from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime, timedelta
from app.database import db
from app.dependencies import get_current_user
from app.models.schemas import JudgmentCreate, JudgmentResponse, JudgmentListResponse, SuspectResponse, PaginatedResponse
from app.services.github_service import GitHubService
from app.services.gemini_service import GeminiService
from app.utils.exceptions import ForbiddenException
import random
import string

router = APIRouter()

@router.post("", response_model=JudgmentResponse)
async def create_judgment(
    judgment_in: JudgmentCreate,
    current_user = Depends(get_current_user)
):
    # Generate Case Number
    year = datetime.now().year
    # 3 groups of 4 digits
    nums = [str(random.randint(1000, 9999)) for _ in range(3)]
    case_number = f"{year}-{'-'.join(nums)}"
    
    judgment = await db.judgment.create(
        data={
            "user_id": current_user.id,
            "case_number": case_number,
            "repo_owner": judgment_in.repo_owner,
            "repo_name": judgment_in.repo_name,
            "title": judgment_in.title,
            "description": judgment_in.description,
            "file_path": judgment_in.file_path,
            "period_days": judgment_in.period_days,
            "status": "pending",
        }
    )
    return judgment

@router.get("", response_model=PaginatedResponse[JudgmentListResponse])
async def list_judgments(
    status: str = None,
    page: int = 1,
    per_page: int = 20,
    current_user = Depends(get_current_user)
):
    where = {"user_id": current_user.id}
    if status:
        where["status"] = status
        
    total = await db.judgment.count(where=where)
    judgments = await db.judgment.find_many(
        where=where,
        take=per_page,
        skip=(page - 1) * per_page,
        order={"created_at": "desc"},
        include={"blame": True} # To check has_blame
    )
    
    items = []
    for j in judgments:
        items.append(JudgmentListResponse(
            id=j.id,
            case_number=j.case_number,
            repo_name=j.repo_name,
            title=j.title,
            status=j.status,
            has_blame=bool(j.blame),
            created_at=j.created_at
        ))
        
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page
    )

# Need to import PaginatedResponse here or move it to common
from app.models.schemas import PaginatedResponse

@router.get("/{judgment_id}", response_model=JudgmentResponse)
async def get_judgment(
    judgment_id: str,
    current_user = Depends(get_current_user)
):
    judgment = await db.judgment.find_unique(
        where={"id": judgment_id},
        include={"suspects": True, "blame": True}
    )
    
    if not judgment:
        raise HTTPException(status_code=404, detail="Judgment not found")
        
    if judgment.user_id != current_user.id:
        raise ForbiddenException()
        
    return judgment

@router.post("/{judgment_id}/analyze", response_model=JudgmentResponse)
async def analyze_judgment(
    judgment_id: str,
    current_user = Depends(get_current_user)
):
    judgment = await db.judgment.find_unique(where={"id": judgment_id})
    
    if not judgment:
        raise HTTPException(status_code=404, detail="Judgment not found")
    if judgment.user_id != current_user.id:
        raise ForbiddenException()
    if judgment.status == "completed":
        raise HTTPException(status_code=400, detail="Already analyzed")
        
    # 1. Fetch Commits
    github_service = GitHubService(current_user.access_token)
    since_date = datetime.utcnow() - timedelta(days=judgment.period_days)
    commits_data = await github_service.get_repo_commits(
        owner=judgment.repo_owner,
        repo=judgment.repo_name,
        path=judgment.file_path,
        since=since_date.isoformat()
    )
    
    commits_payload = []
    for c in commits_data['commits']:
        commits_payload.append({
            "sha": c.sha,
            "message": c.message,
            "author": c.author.username,
            "date": c.date.isoformat(),
            "additions": c.additions,
            "deletions": c.deletions
        })
        
    # 2. Gemini Analysis
    gemini_service = GeminiService()
    analysis_result = await gemini_service.analyze_commits({
        "title": judgment.title,
        "description": judgment.description,
        "file_path": judgment.file_path,
        "commits": commits_payload
    })
    
    # 3. Save Suspects
    for s in analysis_result['suspects']:
        # Try to get avatar from commits or GitHub API (simplified here)
        # We can search in commits_data for matching author
        avatar_url = None
        last_commit_msg = None
        last_commit_date = None
        commit_count = 0
        
        for c in commits_data['commits']:
            if c.author.username == s['username']:
                if not avatar_url: avatar_url = c.author.avatar_url
                if not last_commit_msg: 
                    last_commit_msg = c.message
                    last_commit_date = c.date
                commit_count += 1
                
        await db.suspect.create(
            data={
                "judgment_id": judgment.id,
                "username": s['username'],
                "avatar_url": avatar_url,
                "responsibility": s['responsibility'],
                "reason": s['reason'],
                "commit_count": commit_count,
                "last_commit_msg": last_commit_msg,
                "last_commit_date": last_commit_date
            }
        )
        
    # 4. Update Judgment
    updated_judgment = await db.judgment.update(
        where={"id": judgment.id},
        data={"status": "completed"},
        include={"suspects": True, "blame": True}
    )
    
    return updated_judgment

@router.delete("/{judgment_id}")
async def delete_judgment(
    judgment_id: str,
    current_user = Depends(get_current_user)
):
    judgment = await db.judgment.find_unique(where={"id": judgment_id})
    if not judgment:
        raise HTTPException(status_code=404, detail="Judgment not found")
    if judgment.user_id != current_user.id:
        raise ForbiddenException()
        
    await db.judgment.delete(where={"id": judgment_id})
    return {"message": "Deleted successfully"}

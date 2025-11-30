# backend/app/routers/blame.py
from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import BlameRequest, BlameResponse, FileBlameRequest
from app.services.blame_analyzer import BlameAnalyzer

router = APIRouter()

@router.post("/analyze", response_model=BlameResponse)
async def analyze_blame(
    request: BlameRequest,
    analyzer: BlameAnalyzer = Depends()
):
    """파일의 git blame 분석 및 책임자 판단"""
    try:
        return await analyzer.analyze(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.post("/analyze-url", response_model=BlameResponse)
async def analyze_blame_from_url(
    request: FileBlameRequest,
    analyzer: BlameAnalyzer = Depends()
):
    """GitHub 파일 URL을 받아 blame + 커밋 히스토리 기반 책임자 판단"""
    try:
        return await analyzer.analyze_from_url(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.post("/generate-message")
async def generate_blame_message(
    suspect: str,
    intensity: str,  # "mild", "medium", "spicy"
    analyzer: BlameAnalyzer = Depends()
):
    """Blame 메시지 생성"""
    message = await analyzer.generate_message(suspect, intensity)
    return {"message": message}

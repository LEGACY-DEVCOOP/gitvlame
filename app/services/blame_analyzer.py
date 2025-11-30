# backend/app/services/blame_analyzer.py
import json
from datetime import datetime, timezone
from app.services.github_service import GitHubService
from app.services.gemini_service import GeminiService
from app.models.schemas import BlameRequest, BlameResponse, Suspect, Commit, FileBlameRequest


class BlameAnalyzer:
    def __init__(self):
        self.github_service = GitHubService()
        self.claude_service = GeminiService()

    async def analyze(self, request: BlameRequest) -> BlameResponse:
        """전체 blame 분석 프로세스"""

        # 1. repo 정보 파싱
        owner, repo = self._parse_repo(request.repo)

        # 2. GitHub에서 blame 데이터 가져오기
        blame_data = await self.github_service.get_blame_data(
            owner, repo, request.file_path
        )

        # 3. Claude에게 분석 요청
        analysis_result = await self.claude_service.analyze_blame(
            blame_data,
            request.error_description
        )

        # 4. JSON 파싱
        result = json.loads(analysis_result)

        # 5. Response 모델로 변환
        suspects = [Suspect(**s) for s in result["suspects"]]

        return BlameResponse(
            suspects=suspects,
            timeline=[],  # TODO: 커밋 타임라인 구현
            blame_message=result.get("analysis", "")
        )

    async def analyze_from_url(self, request: FileBlameRequest) -> BlameResponse:
        """파일 URL 기반 blame + 커밋 히스토리 분석"""
        owner, repo, branch, file_path = self.github_service.parse_file_url(request.file_url)

        blame_data = await self.github_service.get_blame_data(owner, repo, file_path, branch)
        commit_history = await self.github_service.get_commit_history(
            owner, repo, branch, file_path, request.commit_limit
        )
        contributors = await self.github_service.get_contributors(owner, repo)

        analysis_result = await self.claude_service.analyze_blame(
            blame_data,
            request.error_description,
            commit_history=commit_history,
            contributors=contributors,
            file_url=request.file_url,
        )

        parsed = json.loads(analysis_result)
        suspects = [Suspect(**s) for s in parsed["suspects"]]
        timeline = self._build_timeline(commit_history)

        return BlameResponse(
            suspects=suspects,
            timeline=timeline,
            blame_message=parsed.get("analysis", "")
        )

    async def generate_message(self, suspect: str, intensity: str) -> str:
        """Blame 메시지 생성"""
        context = {
            "commit": "결제 로직 수정",
            "file": "src/api/payment.ts",
            "error": "TypeError"
        }

        message = await self.claude_service.generate_blame_message(
            suspect, intensity, context
        )

        return message

    def _build_timeline(self, commit_history: list) -> list[Commit]:
        """GitHub commit API 응답을 Commit 모델 리스트로 변환"""
        timeline = []
        for commit in commit_history or []:
            commit_info = commit.get("commit", {}) or {}
            author_info = commit_info.get("author") or {}
            raw_date = author_info.get("date")

            parsed_date = datetime.now(timezone.utc)
            if raw_date:
                try:
                    parsed_date = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                except ValueError:
                    pass

            timeline.append(
                Commit(
                    sha=commit.get("sha", ""),
                    author=author_info.get("name") or (commit.get("author") or {}).get("login", "unknown"),
                    message=commit_info.get("message", ""),
                    date=parsed_date,
                )
            )
        return timeline

    def _parse_repo(self, repo_field: str) -> tuple[str, str]:
        """
        owner/repo 문자열 또는 https://github.com/owner/repo 형태 모두 지원
        """
        value = repo_field.strip()
        if "github.com" in value:
            parts = value.split("github.com/", 1)[-1].split("/")
        else:
            parts = value.split("/")

        if len(parts) >= 2 and parts[0] and parts[1]:
            return parts[0], parts[1]

        raise ValueError("repo는 'owner/repo' 또는 GitHub URL 형식이어야 합니다.")

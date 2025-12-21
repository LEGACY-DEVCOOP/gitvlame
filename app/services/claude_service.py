from anthropic import Anthropic
import json
import asyncio
from app.config import settings
from app.utils.exceptions import ClaudeAPIException

class ClaudeService:
    def __init__(self):
        self.client = Anthropic(api_key=settings.CLAUDE_API_KEY)

    async def analyze_commits(self, params: dict) -> dict:
        prompt = f"""
        당신은 Git 커밋 히스토리를 분석하여 버그/장애의 책임자를 판단하는 AI입니다.

        [사건 정보]
        제목: {params['title']}
        에러 내용: {params['description']}
        관련 파일: {params['file_path']}

        [커밋 히스토리]
        {json.dumps(params['commits'], indent=2, ensure_ascii=False)}

        위 정보를 분석하여 각 개발자의 책임 비율을 판단해주세요.

        판단 기준:
        1. 해당 파일/기능의 마지막 수정자 (가장 높은 책임)
        2. 에러와 관련된 코드의 작성자
        3. 최근 커밋일수록 책임 비율 높음
        4. 커밋 메시지와 에러 내용의 연관성

        반드시 다음 JSON 형식으로만 응답하세요 (다른 텍스트 없이):
        {{
          "suspects": [
            {{
              "username": "개발자명",
              "responsibility": 책임비율(0-100 정수),
              "reason": "책임 사유 (한국어, 1-2문장)"
            }}
          ]
        }}

        주의:
        - 책임 비율의 합은 반드시 100이어야 합니다
        - 최소 1명, 최대 5명까지 선정
        - responsibility가 높은 순으로 정렬
        """

        retries = 2
        for attempt in range(retries + 1):
            try:
                response = await asyncio.to_thread(
                    self.client.messages.create,
                    model="claude-3-haiku-20240307",
                    max_tokens=2000,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                text = response.content[0].text
                if not text:
                    raise ValueError("Empty response from Claude")

                # Extract JSON from response (might have extra text)
                text = text.strip()

                # Try to find JSON in the response
                if text.startswith("```json"):
                    text = text.split("```json")[1].split("```")[0].strip()
                elif text.startswith("```"):
                    text = text.split("```")[1].split("```")[0].strip()

                return json.loads(text)

            except Exception as e:
                if attempt == retries:
                    raise ClaudeAPIException(f"Claude Analysis Failed: {str(e)}")
                await asyncio.sleep(1)

    async def generate_blame_message(self, params: dict, intensity: str) -> list:
        prompt = f"""
        다음 상황에 맞는 Blame 메시지를 정확히 3개의 짧은 문장으로 작성해주세요.

        프로젝트: {params['repo_name']}
        사건: {params['title']}
        범인: {params['target_username']}
        책임도: {params['responsibility']}%
        관련 커밋: {params['last_commit_msg']}
        책임 사유: {params['reason']}

        강도: {intensity}
        - mild (순한맛): 정중하고 부드럽게 ("확인 부탁드려요~", "시간 되실 때 봐주세요")
        - medium (중간맛): 유머러스하게 ("커피 한 잔 사주세요 ☕", "다음엔 테스트 코드 좀...")
        - spicy (매운맛): 직설적이고 재미있게 ("야 이거 누가 짠 거야", "책임지세요 선배님")

        반드시 다음 JSON 형식으로만 응답하세요:
        ["문장1", "문장2", "문장3 (마지막에 이모지 포함)"]

        예시:
        ["hjy080530님 확인 부탁드려요.", "신택스 에러가 발생했습니다.", "시간 되실 때 봐주세요~ 🙏"]
        """

        try:
            response = await asyncio.to_thread(
                self.client.messages.create,
                model="claude-3-haiku-20240307",
                max_tokens=300,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            text = response.content[0].text.strip()

            # Extract JSON from response
            if text.startswith("```json"):
                text = text.split("```json")[1].split("```")[0].strip()
            elif text.startswith("```"):
                text = text.split("```")[1].split("```")[0].strip()

            return json.loads(text)

        except Exception as e:
            raise ClaudeAPIException(f"Claude Message Generation Failed: {str(e)}")

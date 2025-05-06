import logging
from typing import List, Optional
import google.generativeai as genai

from .base_processor import BaseProcessor
# 여기에 사용할 생성형 AI 라이브러리 import (예: from google.generativeai import GenerativeModel)

class AiProcessor(BaseProcessor):
    """생성형 AI를 사용하여 텍스트에서 "도파민 포인트"를 추출하는 클래스"""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"): # 기본 모델 이름 변경
        """AI 프로세서 초기화
        Args:
            api_key (Optional[str]): Google AI API 키
            model_name (str): 사용할 Gemini 모델 이름
        """
        self.api_key = api_key
        self.model_name = model_name
        self.model = self._initialize_model() # 모델 초기화 호출
        # logging.info(f"AI Processor 초기화 완료 (모델: {self.model_name})") # _initialize_model 내부 로깅으로 대체

    def _initialize_model(self):
        """Google Generative AI 모델 클라이언트를 초기화합니다."""
        if not self.api_key:
            logging.warning("AI API 키가 제공되지 않았습니다. AI 기능이 제한됩니다.")
            return None
        try:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model_name)
            logging.info(f"Google Generative AI 모델({self.model_name}) 초기화 완료.")
            return model
        except Exception as e:
            logging.error(f"Google Generative AI 모델 ({self.model_name}) 초기화 실패: {e}", exc_info=True)
            return None

    def process(self, data: dict) -> dict:
        """단일 기사 데이터를 받아 도파민 포인트를 추출하여 반환합니다.
           BaseProcessor의 process 메서드를 구체화합니다.
        """
        title = data.get('title', '')
        content = data.get('summary', '') # 요약이나 본문 사용
        link = data.get('link', '')

        dopamine_points = self.extract_dopamine_points(title, content)

        return {
            'title': title,
            'link': link,
            'dopamine_points': dopamine_points
        }

    def extract_dopamine_points(self, title: str, content: str) -> List[str]:
        """기사 제목과 내용을 바탕으로 도파민 포인트를 추출합니다.

        Args:
            title (str): 기사 제목
            content (str): 기사 내용 (요약 또는 본문)

        Returns:
            List[str]: 추출된 도파민 포인트 문자열 리스트
        """
        if not title and not content:
            logging.warning("도파민 포인트를 추출할 제목이나 내용이 없습니다.")
            return []

        if not self.model:
            logging.error("AI 모델이 초기화되지 않아 도파민 포인트를 추출할 수 없습니다.")
            return ["AI 모델 오류로 추출 실패"]

        prompt = self._build_prompt(title, content)
        logging.debug(f"AI 프롬프트 생성:\n{prompt}")

        try:
            # Gemini API 호출
            response = self.model.generate_content(prompt)
            # 로깅 메시지를 별도로 생성
            log_message = f"AI 응답 수신:\n{response.text}"
            logging.debug(log_message) # 생성된 메시지로 로깅
            # 결과 파싱
            points = self._parse_response(response.text)
            return points
            # logging.warning("AI 모델 호출 로직이 구현되지 않았습니다. 임시 결과를 반환합니다.")
            # return ["예시 도파민 포인트 1", "예시 도파민 포인트 2"] # 임시 반환값 제거

        except Exception as e:
            logging.error(f"AI 모델({self.model_name}) 호출 중 오류 발생: {e}", exc_info=True)
            # API 관련 특정 오류 처리 추가 가능 (예: google.api_core.exceptions.PermissionDenied)
            return [f"AI 처리 중 오류 발생: {e}"]

    def _build_prompt(self, title: str, content: str) -> str:
        """AI 모델에 전달할 프롬프트를 생성합니다."""
        # 사용자 요구사항에 맞춰 프롬프트 상세화 필요
        prompt = f"""다음 뉴스 기사의 제목과 내용을 분석하여, 독자의 흥미를 유발하고 계속 주목하게 만들 수 있는 핵심적인 '도파민 포인트'를 정확히 2가지 추출해 주세요.

각 포인트는 기사의 핵심 갈등, 궁금증, 또는 놀라운 사실을 간결하게 요약해야 합니다.

결과는 간결하고 흥미를 유발하는 방식으로 표현해 주세요. 예를 들어, 다음과 같은 스타일을 참고할 수 있습니다:
"백종원 대표의 방송 활동 중단 선언: '기업 경영 집중' 및 논란 수습 의지 표명 vs. '방송 갑질' 의혹 등 외부 비판 의식한 결정?"

아래 형식에 맞춰 도파민 포인트를 작성해주세요.

제목: {title}

내용 요약:
{content[:1500]}...

도파민 포인트:
"""
        return prompt

    def _parse_response(self, response_text: str) -> List[str]:
        """AI 모델의 응답 텍스트를 파싱하여 도파민 포인트 리스트로 변환합니다."""
        points = []
        lines = response_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            # 번호(1., 2.)나 하이픈(-)으로 시작하는 라인 처리 개선
            if line and (line.startswith(tuple(f"{i}." for i in range(1, 10))) or line.startswith('-')):
                # "1. " 또는 "- " 다음의 내용을 추출
                point = line.split(maxsplit=1)[-1] if len(line.split(maxsplit=1)) > 1 else ""
                if point:
                    points.append(point)
            elif line: # 번호 없이 내용만 있는 경우도 고려 (모델 응답 스타일에 따라)
                # 필요하다면 이 부분 로직 추가/수정
                 points.append(line)

        # Gemini가 마크다운 형식을 사용할 경우 처리 (예: **포인트**) - 필요시 추가
        points = [p.replace('**', '') for p in points]

        if not points:
            logging.warning(f"AI 응답에서 유효한 포인트를 파싱하지 못했습니다. 원본 응답: {response_text}")
            return ["추출된 포인트 없음"]

        return points 
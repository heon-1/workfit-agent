import logging
from typing import List, Dict

from .base_formatter import BaseFormatter

class DefaultFormatter(BaseFormatter):
    """처리된 데이터를 지정된 텍스트 형식으로 포맷하는 클래스"""
    def format(self, data: List[Dict]) -> str:
        """처리된 기사 데이터 리스트를 입력받아 요구사항 형식의 문자열로 변환합니다.

        Args:
            data (List[Dict]): 각 기사 정보 (title, link, dopamine_points)를 담은 딕셔너리 리스트

        Returns:
            str: 포맷팅된 전체 결과 문자열
        """
        formatted_output = ""
        if not data:
            logging.warning("포맷할 데이터가 없습니다.")
            return ""

        for i, item in enumerate(data):
            title = item.get('title', '제목 없음')
            link = item.get('link', '링크 없음')
            dopamine_points = item.get('dopamine_points', ["포인트 정보 없음"])

            formatted_output += f"{i+1:02d}. '{title}'\n{link}\n\n"
            formatted_output += "도파민 포인트\n"
            if dopamine_points:
                for j, point in enumerate(dopamine_points):
                    formatted_output += f"{j+1}. {point}\n"
            else:
                formatted_output += "- 추출된 포인트 없음\n"
            formatted_output += "\n"

        logging.info(f"총 {len(data)}개 항목에 대한 포맷팅 완료")
        return formatted_output.strip() 
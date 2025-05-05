import logging

from .base_sender import BaseSender

class ConsoleSender(BaseSender):
    """결과를 콘솔에 출력하는 클래스"""
    def send(self, content: str):
        """주어진 콘텐츠를 표준 출력(콘솔)에 출력합니다.

        Args:
            content (str): 출력할 문자열 콘텐츠
        """
        try:
            print("--- 최종 결과 --- ")
            print(content)
            print("-----------------")
            logging.info("결과를 콘솔에 성공적으로 출력했습니다.")
        except Exception as e:
            logging.error(f"콘솔 출력 중 오류 발생: {e}", exc_info=True) 
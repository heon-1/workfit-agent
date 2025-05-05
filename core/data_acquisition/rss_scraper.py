import feedparser
import logging
from typing import List, Dict

from .base_scraper import BaseScraper

class RssScraper(BaseScraper):
    """RSS 피드에서 기사를 스크랩하는 클래스"""
    def scrape(self, url: str) -> List[Dict]:
        """주어진 RSS 피드 URL에서 기사 목록을 파싱하여 반환합니다.

        Args:
            url (str): 파싱할 RSS 피드의 URL

        Returns:
            List[Dict]: 각 기사의 제목(title)과 링크(link)를 담은 딕셔너리 리스트
                       파싱 중 오류 발생 시 빈 리스트 반환
        """
        articles = []
        try:
            feed = feedparser.parse(url)
            if feed.bozo:
                logging.warning(f"RSS 피드 파싱 중 문제 발생 (bozo): {url}, 이유: {feed.bozo_exception}")
                # bozo가 true라도 entries가 있을 수 있으므로 계속 진행

            for entry in feed.entries:
                article = {
                    'title': entry.get('title', '제목 없음'),
                    'link': entry.get('link', ''),
                    # 필요시 다른 필드 추가 (published, summary 등)
                    'summary': entry.get('summary', '')
                }
                if article['link']: # 링크가 없는 항목은 제외 (선택 사항)
                    articles.append(article)

        except Exception as e:
            logging.error(f"RSS 피드({url}) 처리 중 오류 발생: {e}", exc_info=True)
            return [] # 오류 발생 시 빈 리스트 반환

        return articles 
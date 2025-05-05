import feedparser
import logging
from typing import List, Dict
import ssl
from .base_scraper import BaseScraper

# 경고: SSL 검증 비활성화 (보안 위험!)
# 이 코드는 개발 환경에서 다른 해결 방법이 없을 때 임시로만 사용해야 합니다.
# 연합 뉴스 버전
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Python 버전이 낮아 해당 속성이 없을 경우
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context
    logging.warning("*****************************************************")
    logging.warning("경고: 전역 SSL 인증서 검증이 비활성화되었습니다! 보안에 매우 취약한 상태입니다.")
    logging.warning("*****************************************************")

class RssScraper(BaseScraper):
    """RSS 피드에서 기사를 스크랩하는 클래스"""
    def scrape(self, url: str) -> List[Dict]:
        """주어진 RSS 피드 URL에서 기사 목록을 파싱하여 반환합니다.

        Args:
            url (str): 파싱할 RSS 피드의 URL

        Returns:
            List[Dict]: 각 기사의 제목(title), 링크(link), 요약(summary)을 담은 딕셔너리 리스트
                       파싱 중 오류 발생 시 빈 리스트 반환
        """
        logging.info(f"'{url}'에서 RSS 피드 스크래핑 시작...")
        articles = []
        try:
            feed = feedparser.parse(url)
            logging.debug(f"'{url}' 피드 파싱 완료. 상태: {feed.status if hasattr(feed, 'status') else 'N/A'}, 인코딩: {feed.encoding if hasattr(feed, 'encoding') else 'N/A'}, 버전: {feed.version if hasattr(feed, 'version') else 'N/A'}")

            if feed.bozo:
                # bozo가 1이면 파싱 중 문제가 있었음을 의미 (예: 잘못된 형식)
                # bozo_exception은 문제의 원인을 담고 있음
                logging.warning(f"RSS 피드 파싱 중 잠재적 문제 발생 (bozo=1): {url}. 이유: {feed.bozo_exception}")
                # bozo가 true라도 entries가 있을 수 있으므로 계속 진행

            if not feed.entries:
                logging.warning(f"'{url}' 피드에서 항목(entries)을 찾을 수 없습니다.")
                return []

            logging.info(f"'{url}' 피드에서 {len(feed.entries)}개의 항목 발견.")

            for i, entry in enumerate(feed.entries):
                title = entry.get('title', '제목 없음')
                link = entry.get('link', '')
                summary = entry.get('summary', '') # 요약 정보 추출
                published = entry.get('published', '') # 발행일 정보 추출 (선택적)
                # published_parsed = entry.get('published_parsed', None) # 파싱된 시간 구조체 (선택적)

                logging.debug(f"항목 {i+1}/{len(feed.entries)} 처리 중: 제목='{title}', 링크='{link}'")

                if not link:
                    logging.warning(f"항목 '{title}'에 링크가 없어 건너<0xEB><0x9C><0x91>니다.")
                    continue # 링크가 없는 항목은 제외

                article = {
                    'title': title,
                    'link': link,
                    'summary': summary,
                    'published': published, # 발행일 추가
                    # 'published_parsed': published_parsed # 필요시 파싱된 시간 추가
                    'source_url': url # 출처 URL 추가
                }
                articles.append(article)
                logging.debug(f"기사 '{title}' 추가 완료.")
                print(f"스크랩된 기사: {article}") # 스크랩된 기사 정보 출력

        except ssl.SSLCertVerificationError as e:
             logging.error(f"SSL 인증서 검증 오류 발생 ({url}): {e}. 전역 SSL 검증 비활성화 상태일 수 있습니다.", exc_info=False) # 상세 스택 트레이스는 제외
             return []
        except Exception as e:
            # 일반적인 예외 처리 (네트워크 오류, 파싱 오류 등 포함)
            logging.error(f"RSS 피드({url}) 처리 중 예상치 못한 오류 발생: {e}", exc_info=True)
            return [] # 오류 발생 시 빈 리스트 반환

        logging.info(f"'{url}' 스크래핑 완료. 총 {len(articles)}개의 유효한 기사 수집.")
        return articles
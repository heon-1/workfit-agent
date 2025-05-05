import logging

from configs.settings import load_config
from core.data_acquisition.rss_scraper import RssScraper
from core.processing.ai_processor import AiProcessor
from core.formatting.default_formatter import DefaultFormatter
from core.delivery.console_sender import ConsoleSender
from utils.logger import setup_logging
from utils.database import initialize_db, save_article # DB 함수 임포트

def main():
    """메인 실행 함수"""
    # 설정 로드
    config = load_config()
    setup_logging()
    initialize_db() # 프로그램 시작 시 DB 및 테이블 초기화

    logging.info("자동 마케팅 프로세스 시작")

    try:
        # 1. 데이터 수집 (RSS)
        rss_urls = config.get('rss_feeds', [])
        if not rss_urls:
            logging.warning("설정 파일 또는 .env 파일에 RSS 피드 URL(RSS_FEED_n)이 없습니다.")
            return

        scraper = RssScraper()
        articles = []
        for url in rss_urls:
            try:
                logging.info(f"{url} 에서 기사 수집 중...")
                fetched_articles = scraper.scrape(url)
                articles.extend(fetched_articles)
                logging.info(f"기사 {len(fetched_articles)}건 수집 완료")
            except Exception as e:
                logging.error(f"{url} 스크래핑 중 오류 발생: {e}", exc_info=True)

        if not articles:
            logging.info("수집된 기사가 없습니다.")
            return

        # 2. 데이터 처리 (AI 도파민 포인트 추출) 및 저장
        ai_config = config.get('ai', {})
        api_key = ai_config.get('api_key')
        model_name = ai_config.get('model_name')

        processed_articles_for_output = [] # 최종 출력을 위한 리스트

        if not api_key:
            logging.error("AI API 키가 설정되지 않아 AI 처리를 건너뛸 수 없습니다.")
            # AI 처리 없이 DB 저장 시도 (선택적: 요약만 저장 등)
            # for article in articles:
            #     save_article(article) # dopamine_points 없이 저장 (필요시 save_article 수정)
            processed_articles_for_output = articles # 원본 데이터를 출력
        else:
            processor = AiProcessor(api_key=api_key, model_name=model_name)
            for article in articles:
                try:
                    processed_article = processor.process(article)
                    # DB에 저장 시도
                    save_successful = save_article(processed_article)
                    # DB에 새로 저장된 기사만 출력 리스트에 추가 (선택 사항)
                    # if save_successful:
                    #    processed_articles_for_output.append(processed_article)
                    processed_articles_for_output.append(processed_article) # 모든 처리 결과를 출력 (중복 포함)

                    logging.debug(f"'{article['title']}' 처리 및 저장 시도 완료")
                except Exception as e:
                    logging.error(f"'{article['title']}' 처리 또는 저장 중 오류 발생: {e}", exc_info=True)
                    error_result = {
                        'title': article['title'],
                        'link': article['link'],
                        'summary': article.get('summary', ''),
                        'dopamine_points': [f"처리/저장 오류: {e}"]
                    }
                    processed_articles_for_output.append(error_result)

        # 3. 결과 포맷팅 (출력할 데이터 기준)
        formatter = DefaultFormatter()
        formatted_output = formatter.format(processed_articles_for_output)
        logging.info("데이터 포맷팅 완료")

        # 4. 결과 전송 (콘솔 출력)
        sender = ConsoleSender()
        sender.send(formatted_output)
        logging.info("결과 전송 완료")

    except Exception as e:
        logging.critical(f"메인 프로세스 실행 중 심각한 오류 발생: {e}", exc_info=True)
    finally:
        logging.info("자동 마케팅 프로세스 종료")

if __name__ == "__main__":
    main() 
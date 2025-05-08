import logging
import os # os 모듈 추가

from configs.settings import load_config
from core.data_acquisition.rss_scraper import RssScraper
from core.processing.ai_processor import AiProcessor
from core.processing.image_generator import ImageGenerator # ImageGenerator 임포트
from core.formatting.default_formatter import DefaultFormatter
from core.delivery.console_sender import ConsoleSender
from utils.logger import setup_logging
from utils.database import initialize_db, save_article, get_articles_without_gen_image, update_article_gen_image # DB 함수 임포트

GENERATED_IMAGES_DIR = "generated_images" # 생성된 이미지 저장 디렉토리

def ensure_dir_exists(directory_path: str):
    """주어진 경로의 디렉토리가 없으면 생성합니다."""
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path)
            logging.info(f"디렉토리 생성: {directory_path}")
        except OSError as e:
            logging.error(f"디렉토리 생성 실패 ({directory_path}): {e}", exc_info=True)
            # 디렉토리 생성 실패 시 예외를 다시 발생시키거나, 프로그램 흐름을 조정할 수 있음
            raise # 일단은 예외를 다시 발생시켜 문제 인지를 명확히 함

def process_missing_images(config: dict):
    """gen_image가 없는 기사에 대해 이미지를 생성하고 DB를 업데이트합니다."""
    logging.info("--- 누락된 이미지 생성 프로세스 시작 ---")
    ai_config = config.get('ai', {})
    api_key = ai_config.get('api_key')
    # ImageGenerator는 자체적으로 모델명을 가지고 있으므로, config에서 가져올 필요는 없음
    # image_model_name = ai_config.get('image_model_name') # 필요시 설정에서 모델명 오버라이드 가능

    if not api_key:
        logging.error("AI API 키가 설정되지 않아 이미지 생성을 건너뛸 수 없습니다.")
        return

    try:
        ensure_dir_exists(GENERATED_IMAGES_DIR) # 이미지 저장 디렉토리 확인/생성
    except Exception:
        logging.error(f"{GENERATED_IMAGES_DIR} 디렉토리 준비 실패. 이미지 생성을 진행할 수 없습니다.")
        return
        
    image_generator = ImageGenerator(api_key=api_key)
    # image_generator = ImageGenerator(api_key=api_key, image_model_name=image_model_name) # 모델명 오버라이드 시

    articles_to_process = get_articles_without_gen_image(limit=config.get('image_processing_limit', 5)) # 한 번에 처리할 이미지 수
    if not articles_to_process:
        logging.info("이미지를 생성할 대상 기사가 없습니다.")
        return

    logging.info(f"{len(articles_to_process)}건의 기사에 대해 이미지 생성을 시도합니다.")

    for article in articles_to_process:
        article_id = article.get('id')
        title = article.get('title')
        link = article.get('link') # 로그용

        if not article_id or not title:
            logging.warning(f"이미지 생성을 위한 ID 또는 제목이 누락된 기사 데이터: {article}")
            continue

        # 이미지 파일명 생성 (예: article_123.png)
        # 링크에서 파일명으로 부적합한 문자 제거 또는 해시 사용 고려 가능
        # 간단하게 ID 기반으로 파일명 생성
        image_filename = f"article_img_{article_id}.png"
        output_image_path = os.path.join(GENERATED_IMAGES_DIR, image_filename)

        logging.info(f"기사 ID {article_id} ('{title}') 이미지 생성 시도 -> {output_image_path}")
        
        # 이미지 생성 주제는 기사 제목을 사용 (또는 요약 등)
        subject_prompt = title 
        # subject_prompt = article.get('summary', title) # 요약이 있으면 요약 사용

        try:
            success = image_generator.generate_halftone_image(subject_prompt, output_image_path)
            if success:
                logging.info(f"기사 ID {article_id} 이미지 생성 성공: {output_image_path}")
                # DB에 이미지 경로 업데이트
                update_success = update_article_gen_image(article_id, output_image_path)
                if not update_success:
                    logging.error(f"기사 ID {article_id}의 gen_image DB 업데이트 실패.")
            else:
                logging.error(f"기사 ID {article_id} ('{title}') 이미지 생성 실패.")
        except Exception as e:
            logging.error(f"기사 ID {article_id} ('{title}') 이미지 생성 중 예외 발생: {e}", exc_info=True)
    
    logging.info("--- 누락된 이미지 생성 프로세스 완료 ---")



def main():
    """메인 실행 함수"""
    # 설정 로드
    config_data = load_config() # 변수명 변경 (config는 dict)
    setup_logging()
    initialize_db() # 프로그램 시작 시 DB 및 테이블 초기화

    logging.info("자동 마케팅 프로세스 시작")

    try:
        # 1. 데이터 수집 (RSS)
        rss_urls = config_data.get('rss_feeds', [])
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
        ai_config = config_data.get('ai', {})
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

        # --- 추가: 누락된 이미지 생성 프로세스 호출 ---
        if config_data.get('enable_image_generation', True): # 설정에서 이미지 생성 기능 활성화 여부 확인
            process_missing_images(config_data)
        else:
            logging.info("이미지 생성 기능이 비활성화되어 있습니다 (config: enable_image_generation).")

    except Exception as e:
        logging.critical(f"메인 프로세스 실행 중 심각한 오류 발생: {e}", exc_info=True)
    finally:
        logging.info("자동 마케팅 프로세스 종료")

if __name__ == "__main__":
    main() 
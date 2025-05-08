import logging
import os
import argparse # 명령줄 인자 처리를 위해 추가

from configs.settings import load_config
from core.processing.image_generator import ImageGenerator
from core.processing.ai_processor import AiProcessor # AiProcessor 임포트
from utils.database import initialize_db, get_articles_without_gen_image, update_article_gen_image
from utils.logger import setup_logging
# from google import genai # 이 임포트는 더 이상 필요하지 않음

GENERATED_IMAGES_DIR = "generated_images"  # 생성된 이미지 저장 디렉토리

def ensure_dir_exists(directory_path: str):
    """주어진 경로의 디렉토리가 없으면 생성합니다."""
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path)
            logging.info(f"디렉토리 생성: {directory_path}")
        except OSError as e:
            logging.error(f"디렉토리 생성 실패 ({directory_path}): {e}", exc_info=True)
            raise

def batch_generate_missing_images(config: dict, limit: int):
    """gen_image가 없는 기사에 대해 이미지를 생성하고 DB를 업데이트합니다."""
    logging.info("--- 일괄 이미지 생성 프로세스 시작 ---")
    ai_config = config.get('ai', {})
    api_key = ai_config.get('api_key')

    # AiProcessor 초기화 (키워드 추출용)
    # AiProcessor는 자체적으로 모델명을 가지므로, text 모델 설정 사용
    text_model_name = ai_config.get('model_name') # 또는 기본값 사용
    ai_processor = AiProcessor(api_key=api_key, model_name=text_model_name)
    if not ai_processor.model: # AiProcessor 초기화 성공 여부 확인
        logging.error("AiProcessor 초기화에 실패하여 키워드 추출을 진행할 수 없습니다.")
        # 이미지 생성은 키워드 없이 진행하거나 중단할 수 있음 - 여기서는 중단하지 않고 원본 제목 사용
        # return

    # ImageGenerator 초기화 (Vertex AI 또는 genai.Client 방식)
    image_generator = ImageGenerator()

    # ImageGenerator가 성공적으로 초기화되었는지 확인 (client 속성 확인)
    if not image_generator.client:
        logging.error("ImageGenerator 초기화에 실패하여 이미지 생성을 진행할 수 없습니다.")
        return
        
    try:
        ensure_dir_exists(GENERATED_IMAGES_DIR)
    except Exception:
        logging.error(f"{GENERATED_IMAGES_DIR} 디렉토리 준비 실패.")
        return

    articles_to_process = get_articles_without_gen_image(limit=limit)
    if not articles_to_process:
        logging.info("이미지를 생성할 대상 기사가 없습니다.")
        return

    logging.info(f"{len(articles_to_process)}건의 기사에 대해 이미지 생성을 시도합니다 (최대 {limit}건).")

    for article in articles_to_process:
        article_id = article.get('id')
        title = article.get('title')

        if not article_id or not title:
            logging.warning(f"ID 또는 제목 누락 데이터: {article}")
            continue

        # LLM으로 이미지 생성용 키워드 추출
        subject_prompt = title # 기본값은 원본 제목
        if ai_processor.model: # AiProcessor가 성공적으로 초기화된 경우에만 시도
            try:
                keywords = ai_processor.extract_image_keywords(title)
                if keywords:
                    # 추출된 키워드를 이미지 프롬프트로 사용 (쉼표와 공백으로 연결)
                    subject_prompt = ", ".join(keywords)
                    logging.info(f"키워드 기반 이미지 프롬프트 사용: '{subject_prompt}'")
                else:
                    logging.warning(f"'{title}'에 대한 이미지 키워드를 추출하지 못했습니다. 원본 제목을 사용합니다.")
            except Exception as keyword_e:
                logging.error(f"'{title}' 키워드 추출 중 예외 발생: {keyword_e}. 원본 제목 사용.")
        else:
             logging.warning("AiProcessor가 초기화되지 않아 원본 제목을 이미지 프롬프트로 사용합니다.")

        image_filename = f"article_img_{article_id}.png"
        output_image_path = os.path.join(GENERATED_IMAGES_DIR, image_filename)

        logging.info(f"기사 ID {article_id} ('{title}') 이미지 생성 시도 -> {output_image_path}")
        
        # 생성된 subject_prompt 사용
        try:
            success = image_generator.generate_halftone_image(subject_prompt, output_image_path)
            if success:
                logging.info(f"기사 ID {article_id} 이미지 생성 성공: {output_image_path}")
                update_success = update_article_gen_image(article_id, output_image_path)
                if not update_success:
                    logging.error(f"기사 ID {article_id}의 gen_image DB 업데이트 실패.")
            else:
                logging.error(f"기사 ID {article_id} ('{title}') 이미지 생성 실패.")
        except Exception as e:
            logging.error(f"기사 ID {article_id} ('{title}') 이미지 생성 중 예외 발생: {e}", exc_info=True)
    
    logging.info("--- 일괄 이미지 생성 프로세스 완료 ---")

if __name__ == "__main__":
    setup_logging()
    
    parser = argparse.ArgumentParser(description="DB에서 gen_image가 없는 기사에 대해 이미지를 일괄 생성합니다.")
    parser.add_argument(
        "--limit", 
        type=int, 
        help="한 번에 처리할 최대 기사 수. 설정 파일의 image_processing_limit보다 우선 적용됩니다."
    )
    args = parser.parse_args()

    config_data = load_config()
    initialize_db() # DB 파일 및 테이블이 준비되었는지 확인/초기화

    # 명령줄 인자로 limit이 주어지면 그 값을 사용, 아니면 설정 파일 값 사용, 둘 다 없으면 기본값 5 사용
    processing_limit = args.limit if args.limit is not None else config_data.get('image_processing_limit', 5)

    try:
        batch_generate_missing_images(config_data, limit=processing_limit)
    except Exception as e:
        logging.critical(f"일괄 이미지 생성 스크립트 실행 중 심각한 오류 발생: {e}", exc_info=True) 
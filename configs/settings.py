import logging
import os
from dotenv import load_dotenv
from typing import Dict, Any, List

def load_config(env_path: str = '.env') -> Dict[str, Any]:
    """환경 변수 파일(.env)을 로드하여 설정을 구성합니다.

    .env 파일이나 시스템 환경 변수에서 설정을 읽어옵니다.
    값이 없으면 코드 내 정의된 기본값을 사용합니다.

    Args:
        env_path (str): .env 파일 경로

    Returns:
        Dict[str, Any]: 로드된 설정 딕셔너리
    """
    config: Dict[str, Any] = {}

    # 1. .env 파일 로드 (환경 변수 설정)
    try:
        # load_dotenv는 기존 환경 변수를 덮어쓰지 않음 (시스템 환경 변수 우선)
        # .env 파일의 값을 우선하려면 override=True 사용 가능
        load_dotenv(dotenv_path=env_path)
        logging.info(f".env 파일 로드 시도: {env_path}")
    except Exception as e:
        logging.warning(f".env 파일 ({env_path}) 로드 중 오류 발생: {e}")
    # RSS 피드 목록 처리
    config['rss_feeds'] = []
    i = 1
    while True:
        feed_url = os.getenv(f'RSS_FEED_{i}')
        if feed_url:
            config['rss_feeds'].append(feed_url)
            i += 1
        else:
            break
    if config['rss_feeds']:
        logging.info(f"환경 변수에서 {len(config['rss_feeds'])}개의 RSS 피드 URL을 로드했습니다.")
    else:
        logging.warning("환경 변수에 RSS 피드 URL(RSS_FEED_n)이 설정되지 않았습니다.")

    # AI 설정
    config['ai'] = {}
    config['ai']['api_key'] = os.getenv('GEMINI_API_KEY')
    config['ai']['model_name'] = os.getenv('GEMINI_MODEL_NAME', "gemini-2.5-flash-preview-04-17")

    if config['ai']['api_key']:
        logging.info("환경 변수에서 Gemini API 키를 로드했습니다.")
    else:
        logging.warning("환경 변수에 Gemini API 키(GEMINI_API_KEY)가 설정되지 않았습니다.")
    logging.info(f"AI 모델: {config['ai']['model_name']}")

    # Slack 설정
    slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if slack_webhook_url:
        config['delivery'] = {'slack': {'webhook_url': slack_webhook_url}}
        logging.info("환경 변수에서 Slack Webhook URL을 로드했습니다.")

    # 데이터베이스 파일명 설정 (필요하다면)
    config['database'] = {}
    config['database']['file_name'] = os.getenv('DATABASE_FILE_NAME', 'automkt.db') # 기본값 설정
    logging.info(f"데이터베이스 파일명: {config['database']['file_name']}")

    # 필요한 다른 설정들도 유사하게 환경 변수에서 읽거나 기본값 설정

    return config

# 예시: 기본 설정 로드
# loaded_config = load_config()
# print(loaded_config) 
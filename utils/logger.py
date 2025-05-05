import logging
import sys
import yaml
from logging.config import dictConfig

DEFAULT_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
        },
        # 'file': {
        #     'level': 'DEBUG',
        #     'formatter': 'standard',
        #     'class': 'logging.FileHandler',
        #     'filename': 'app.log', # 설정 파일에서 관리하는 것이 좋음
        #     'mode': 'a',
        # },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console'], # 기본 핸들러 설정
            'level': 'DEBUG',
            'propagate': True
        },
        # '__main__': { # main 모듈 로거 설정 예시
        #     'handlers': ['console', 'file'],
        #     'level': 'INFO',
        #     'propagate': False
        # },
    }
}

def setup_logging(config_path: str = 'configs/logging_config.yaml'):
    """로깅 설정을 로드하고 적용합니다.

    Args:
        config_path (str): 로깅 설정 파일 경로. 파일이 없으면 기본 설정을 사용합니다.
    """
    try:
        with open(config_path, 'rt') as f:
            logging_config = yaml.safe_load(f.read())
        dictConfig(logging_config)
        logging.info(f"로깅 설정 로드 완료: {config_path}")
    except FileNotFoundError:
        logging.warning(f"로깅 설정 파일({config_path})을 찾을 수 없습니다. 기본 설정을 사용합니다.")
        dictConfig(DEFAULT_LOGGING_CONFIG)
    except Exception as e:
        logging.error(f"로깅 설정 중 오류 발생: {e}", exc_info=True)
        # 오류 발생 시에도 기본 로깅은 동작하도록
        logging.basicConfig(level=logging.INFO)
        logging.warning("기본 로깅 설정으로 대체합니다.")

# setup_logging() 호출은 main.py에서 수행 
import logging

# 사용자 정의 예외 클래스 (필요시)
class DataAcquisitionError(Exception):
    """데이터 수집 중 발생한 오류"""
    pass

class ProcessingError(Exception):
    """데이터 처리 중 발생한 오류"""
    pass

class DeliveryError(Exception):
    """결과 전송 중 발생한 오류"""
    pass

# 간단한 에러 처리 함수 예시
def log_error(message: str, error: Exception, level: int = logging.ERROR):
    """오류를 로깅하는 간단한 함수"""
    logging.log(level, f"{message}: {error}", exc_info=True)

# 필요에 따라 더 복잡한 에러 처리 로직 추가 가능
# (예: 특정 에러 발생 시 재시도, 알림 발송 등) 
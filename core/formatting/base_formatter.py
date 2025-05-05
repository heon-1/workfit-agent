from abc import ABC, abstractmethod

class BaseFormatter(ABC):
    @abstractmethod
    def format(self, data):
        """데이터를 특정 형식으로 포맷합니다."""
        pass 
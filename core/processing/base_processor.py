from abc import ABC, abstractmethod

class BaseProcessor(ABC):
    @abstractmethod
    def process(self, data):
        """입력 데이터를 처리합니다."""
        pass 
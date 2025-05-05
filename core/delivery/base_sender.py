from abc import ABC, abstractmethod

class BaseSender(ABC):
    @abstractmethod
    def send(self, content):
        """콘텐츠를 지정된 대상으로 전송합니다."""
        pass 
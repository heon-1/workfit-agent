from abc import ABC, abstractmethod

class BaseScraper(ABC):
    @abstractmethod
    def scrape(self, source: str):
        """지정된 소스에서 데이터를 스크랩합니다."""
        pass 
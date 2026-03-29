from abc import ABC, abstractmethod
from datetime import datetime
from sqlalchemy.orm import Session
from backend.db.models import ScrapeCheckpoint


class BaseScraper(ABC):
    def __init__(self, db_session: Session):
        self.db = db_session

    @abstractmethod
    def scrape(self) -> list[dict]:
        pass

    def save_checkpoint(self, platform: str, source_key: str, last_id: str, last_timestamp: datetime = None):
        checkpoint = self.db.query(ScrapeCheckpoint).filter_by(
            platform=platform, source_key=source_key
        ).first()
        if checkpoint:
            checkpoint.last_id = last_id
            checkpoint.last_timestamp = last_timestamp
        else:
            checkpoint = ScrapeCheckpoint(
                platform=platform,
                source_key=source_key,
                last_id=last_id,
                last_timestamp=last_timestamp,
            )
            self.db.add(checkpoint)
        self.db.commit()

    def get_checkpoint(self, platform: str, source_key: str) -> str | None:
        checkpoint = self.db.query(ScrapeCheckpoint).filter_by(
            platform=platform, source_key=source_key
        ).first()
        return checkpoint.last_id if checkpoint else None

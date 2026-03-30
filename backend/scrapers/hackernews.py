import hashlib
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from backend.db.models import RawPost
from backend.scrapers.base import BaseScraper

PLATFORM = "hackernews"
HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
CHECKPOINT_KEY = "newstories"
INCLUDE_PREFIXES = ("Ask HN", "Show HN", "Tell HN")


class HNScraper(BaseScraper):
    def __init__(self, db_session: Session):
        super().__init__(db_session)
        self.client = httpx.Client(timeout=10)

    def fetch_item(self, item_id: int) -> dict | None:
        resp = self.client.get(f"{HN_API_BASE}/item/{item_id}.json")
        if resp.status_code == 200:
            return resp.json()
        return None

    def scrape(self) -> list[dict]:
        resp = self.client.get(f"{HN_API_BASE}/newstories.json")
        resp.raise_for_status()
        story_ids: list[int] = resp.json()

        last_id = self.get_checkpoint(PLATFORM, CHECKPOINT_KEY)
        last_id = int(last_id) if last_id else None

        scraped = []
        newest_id = None

        for story_id in story_ids:
            if last_id and story_id <= last_id:
                break

            item = self.fetch_item(story_id)
            if not item or item.get("type") != "story" or item.get("dead") or item.get("deleted"):
                continue

            title = item.get("title", "")
            num_comments = item.get("descendants", 0)

            qualifies = (
                any(title.startswith(prefix) for prefix in INCLUDE_PREFIXES)
                or num_comments >= 5
            )
            if not qualifies:
                continue

            raw_post = self._store_story(item)
            scraped.append({"id": raw_post.id, "platform": PLATFORM, "hn_id": story_id})

            if newest_id is None:
                newest_id = story_id

            kids = item.get("kids", [])
            scraped.extend(self._scrape_comments(kids[:10], raw_post.source_url))

        if newest_id:
            self.save_checkpoint(PLATFORM, CHECKPOINT_KEY, str(newest_id))

        return scraped

    def _store_story(self, item: dict) -> RawPost:
        author_hash = (
            hashlib.sha256(item["by"].encode()).hexdigest() if item.get("by") else None
        )
        raw_post = RawPost(
            platform=PLATFORM,
            source_url=item.get("url") or f"https://news.ycombinator.com/item?id={item['id']}",
            author_hash=author_hash,
            title=item.get("title", "")[:512],
            body=item.get("text"),
            upvotes=item.get("score", 0),
            comment_count=item.get("descendants", 0),
            created_at=datetime.fromtimestamp(item["time"], tz=timezone.utc),
        )
        self.db.add(raw_post)
        self.db.commit()
        self.db.refresh(raw_post)
        return raw_post

    def _scrape_comments(self, comment_ids: list[int], parent_url: str) -> list[dict]:
        results = []
        for comment_id in comment_ids:
            item = self.fetch_item(comment_id)
            if not item or item.get("deleted") or item.get("dead") or not item.get("text"):
                continue

            author_hash = (
                hashlib.sha256(item["by"].encode()).hexdigest() if item.get("by") else None
            )
            raw_post = RawPost(
                platform=PLATFORM,
                source_url=f"https://news.ycombinator.com/item?id={item['id']}",
                author_hash=author_hash,
                title=None,
                body=item.get("text"),
                upvotes=item.get("score", 0),
                comment_count=0,
                created_at=datetime.fromtimestamp(item["time"], tz=timezone.utc),
            )
            self.db.add(raw_post)
            results.append({"platform": PLATFORM, "type": "comment", "hn_id": comment_id})

        self.db.commit()
        return results

    def close(self):
        self.client.close()

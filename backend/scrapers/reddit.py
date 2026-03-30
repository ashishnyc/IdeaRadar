import hashlib
from datetime import datetime, timezone

import praw
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db.models import RawPost
from backend.scrapers.base import BaseScraper

PLATFORM = "reddit"

SUBREDDITS = [
    "entrepreneur",
    "SaaS",
    "startups",
    "smallbusiness",
    "Entrepreneur",
    "indiehackers",
    "webdev",
    "AskReddit",
    "productivity",
    "technology",
]


class RedditScraper(BaseScraper):
    def __init__(self, db_session: Session):
        super().__init__(db_session)
        self.client = praw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT,
        )

    def scrape(self) -> list[dict]:
        scraped = []
        for subreddit_name in SUBREDDITS:
            subreddit = self.client.subreddit(subreddit_name)
            last_id = self.get_checkpoint(PLATFORM, subreddit_name)
            new_posts = []

            for submission in subreddit.new(limit=50):
                if last_id and submission.id == last_id:
                    break
                new_posts.append(submission)

            for submission in new_posts:
                post = self._store_post(submission, subreddit_name)
                scraped.append(post)

                if submission.comment_count > 5:
                    scraped.extend(self._scrape_comments(submission))

            if new_posts:
                self.save_checkpoint(
                    PLATFORM,
                    subreddit_name,
                    new_posts[0].id,
                    datetime.fromtimestamp(new_posts[0].created_utc, tz=timezone.utc),
                )

        return scraped

    def _store_post(self, submission, subreddit_name: str) -> dict:
        author_hash = (
            hashlib.sha256(str(submission.author).encode()).hexdigest()
            if submission.author
            else None
        )
        raw_post = RawPost(
            platform=PLATFORM,
            source_url=f"https://reddit.com{submission.permalink}",
            author_hash=author_hash,
            title=submission.title[:512],
            body=submission.selftext or None,
            upvotes=submission.score,
            comment_count=submission.num_comments,
            created_at=datetime.fromtimestamp(submission.created_utc, tz=timezone.utc),
        )
        self.db.add(raw_post)
        self.db.commit()
        self.db.refresh(raw_post)
        return {"id": raw_post.id, "platform": PLATFORM, "source": subreddit_name}

    def _scrape_comments(self, submission) -> list[dict]:
        results = []
        submission.comments.replace_more(limit=0)
        for comment in submission.comments.list():
            if not comment.body or comment.body in ("[deleted]", "[removed]"):
                continue
            author_hash = (
                hashlib.sha256(str(comment.author).encode()).hexdigest()
                if comment.author
                else None
            )
            raw_post = RawPost(
                platform=PLATFORM,
                source_url=f"https://reddit.com{comment.permalink}",
                author_hash=author_hash,
                title=None,
                body=comment.body,
                upvotes=comment.score,
                comment_count=0,
                created_at=datetime.fromtimestamp(comment.created_utc, tz=timezone.utc),
            )
            self.db.add(raw_post)
            results.append({"platform": PLATFORM, "type": "comment"})
        self.db.commit()
        return results

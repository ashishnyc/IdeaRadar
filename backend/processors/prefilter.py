import re

from backend.db.models import RawPost
from backend.processors.language_detector import is_english

_SPAM_PATTERNS = re.compile(
    r"(buy now|click here|free money|crypto|bitcoin|nft|binance|airdrop"
    r"|follow me|dm me|t\.me/|discord\.gg/|check my profile"
    r"|100x|moon|pump|get rich)",
    re.IGNORECASE,
)

MIN_BODY_LENGTH = 20


def should_process(raw_post: RawPost) -> bool:
    text = raw_post.body or raw_post.title or ""

    if len(text.strip()) < MIN_BODY_LENGTH:
        return False

    if not is_english(text):
        return False

    if _SPAM_PATTERNS.search(text):
        return False

    return True

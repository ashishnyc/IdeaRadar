import re
import unicodedata

from bs4 import BeautifulSoup

_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_MARKDOWN_RE = re.compile(r"[*_~`>#\-]+")
_WHITESPACE_RE = re.compile(r"\s+")


def clean_text(raw_text: str) -> str:
    if not raw_text:
        return ""

    # Strip HTML
    text = BeautifulSoup(raw_text, "html.parser").get_text(separator=" ")

    # Remove URLs
    text = _URL_RE.sub(" ", text)

    # Strip markdown formatting characters
    text = _MARKDOWN_RE.sub(" ", text)

    # Remove emoji and non-ASCII symbols
    text = "".join(
        ch for ch in text
        if not unicodedata.category(ch).startswith("So")
    )

    # Normalize whitespace
    text = _WHITESPACE_RE.sub(" ", text).strip()

    return text

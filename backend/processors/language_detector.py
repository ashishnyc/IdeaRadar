from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Ensure consistent results
DetectorFactory.seed = 0


def detect_language(text: str) -> str | None:
    try:
        return detect(text)
    except LangDetectException:
        return None


def is_english(text: str) -> bool:
    if not text or len(text) < 20:
        return False
    lang = detect_language(text)
    return lang == "en"

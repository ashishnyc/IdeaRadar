import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    API_PORT: int = int(os.getenv("API_PORT", 53847))
    DASHBOARD_PORT: int = int(os.getenv("DASHBOARD_PORT", 47291))

    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/idearadar")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1")

    REDDIT_CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET", "")
    REDDIT_USER_AGENT: str = os.getenv("REDDIT_USER_AGENT", "IdeaRadar/1.0")

    ALERT_EMAIL: str = os.getenv("ALERT_EMAIL", "")
    ALERT_SCORE_THRESHOLD: float = float(os.getenv("ALERT_SCORE_THRESHOLD", 0.75))


settings = Settings()

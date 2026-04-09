from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    anthropic_api_key: str = "sk-placeholder"
    claude_model: str = "claude-sonnet-4-6"
    max_research_rounds: int = 3

settings = Settings()

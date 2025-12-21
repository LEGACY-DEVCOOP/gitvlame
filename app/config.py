from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_REDIRECT_URI: str
    CLAUDE_API_KEY: str
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SECRET_KEY: str
    FRONTEND_URL: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

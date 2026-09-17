from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/medikiosk.db"
    jwt_secret: str = "medikiosk-local-development-secret-change-me"
    jwt_access_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 7
    redis_url: str = "redis://localhost:6381/0"
    minio_endpoint: str = "localhost:9002"
    minio_access_key: str = "medikiosk"
    minio_secret_key: str = "medikiosk-demo-secret"
    minio_bucket_documents: str = "medical-documents"
    minio_bucket_generated: str = "generated-files"
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002"
    max_upload_bytes: int = 10 * 1024 * 1024
    asr_provider: str = "mock"
    ocr_provider: str = "mock"
    llm_provider: str = "mock"
    abdm_mode: str = "mock"
    his_mode: str = "mock"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def upload_dir(self) -> Path:
        location = Path("uploads")
        location.mkdir(parents=True, exist_ok=True)
        return location


settings = Settings()


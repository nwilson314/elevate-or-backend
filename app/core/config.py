import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    database_url: str = "postgresql://surgery_user:surgery_password@localhost:5432/surgery_db"
    jwt_secret_key: str = "CHANGE_THIS_TO_SOMETHING_SECURE"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60 * 24  # 24 hours default

    class Config:
        env_file = ".env"

settings = Settings()
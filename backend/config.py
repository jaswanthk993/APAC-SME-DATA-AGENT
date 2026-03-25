"""Application configuration with fail-fast validation."""

import os
import sys
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Google Cloud
    GOOGLE_API_KEY: str = Field(..., description="Gemini API Key")
    GCP_PROJECT_ID: str = Field(default="", description="GCP Project ID")

    # AlloyDB / PostgreSQL
    DB_HOST: str = Field(..., description="Database host")
    DB_PORT: int = Field(default=5432, description="Database port")
    DB_NAME: str = Field(default="sme_data", description="Database name")
    DB_USER: str = Field(default="postgres", description="Database user")
    DB_PASSWORD: str = Field(..., description="Database password")

    # Application
    APP_PORT: int = Field(default=8080, description="Application port")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def async_database_url(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


def get_settings() -> Settings:
    """Load and validate settings. Fail fast if required vars are missing."""
    try:
        return Settings()
    except Exception as e:
        print(f"\n❌ CONFIGURATION ERROR: {e}")
        print("Please ensure all required environment variables are set.")
        print("Copy .env.example to .env and fill in your values.\n")
        sys.exit(1)


settings = get_settings()

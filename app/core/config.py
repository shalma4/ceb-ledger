from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "CEB-Ledger"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./ceb_ledger.db"

    model_config = ConfigDict(case_sensitive=True)


settings = Settings()

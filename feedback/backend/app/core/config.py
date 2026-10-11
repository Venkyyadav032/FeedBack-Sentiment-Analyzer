import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "FeedbackSense AI"
    APP_ENV: str = "development"
    SECRET_KEY: str = "feedbacksense_secret_key_change_in_production_2026"
    API_PORT: int = 8000
    API_HOST: str = "127.0.0.1"
    
    # CORS Origins
    CORS_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000,http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000,null"
    
    # MySQL Database Config
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "root"
    MYSQL_DB: str = "feedbacksense_db"
    
    # Fallback
    ENABLE_SQLITE_FALLBACK: bool = True
    SQLITE_DB_PATH: str = "./feedbacksense.db"
    
    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        
    @property
    def mysql_url(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"

    @property
    def sqlite_url(self) -> str:
        return f"sqlite:///{self.SQLITE_DB_PATH}"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

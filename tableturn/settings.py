"""One settings object, read once at start-up. Nothing is hard-coded.
Every field here has a default; the environment can change it."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./tableturn.db"
    default_quote_minutes: int = 40  # the wait every party is quoted
    seed_dir: str = "seed"
    host: str = "0.0.0.0"  # bind every interface
    port: int = Field(default=8080, ge=1, le=65535)
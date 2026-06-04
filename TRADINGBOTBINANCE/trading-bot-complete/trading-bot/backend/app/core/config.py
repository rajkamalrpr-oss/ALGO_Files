"""
app/core/config.py — Application configuration via pydantic-settings.
All values can be overridden by environment variables or a .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Binance ──────────────────────────────────────────────────────────────
    binance_api_key: str = ""
    binance_api_secret: str = ""
    binance_testnet: bool = True
    binance_base_url: str = "https://testnet.binancefuture.com"

    # ── MongoDB ───────────────────────────────────────────────────────────────
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db: str = "trading_bot"

    # ── App ───────────────────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "DEBUG"


settings = Settings()

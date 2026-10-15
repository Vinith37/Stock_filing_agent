from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration — loaded from .env file"""

    # ── Ollama / Phi-4 Mini ─────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "phi4-mini"
    llm_temperature: float = 0.1
    llm_context_window: int = 8192

    # ── Scraping ────────────────────────────────
    bse_enabled: bool = True
    nse_enabled: bool = True
    scrape_delay_seconds: float = 1.0

    # ── JEV ─────────────────────────────────────
    jev_probability_threshold: float = 0.65
    jev_max_retries: int = 3
    jev_min_data_quality: float = 0.3

    # ── Output ──────────────────────────────────
    excel_output_dir: str = "./data/output"

    # ── Logging ─────────────────────────────────
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_prefix": "AGENT_"}


settings = Settings()

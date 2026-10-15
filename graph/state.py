"""Graph state definition shared across all LangGraph nodes"""

from typing import TypedDict
from datetime import date


class AgentState(TypedDict, total=False):
    """State shared across all LangGraph nodes

    Fields:
        target_date: Date to fetch filings for
        filings: List of raw filing dicts from scraper
        filings_count: Total number of filings fetched
        analyses: List of LLM analysis dicts
        verdicts: List of JEV verdict dicts
        needs_reprocessing: Whether any filing needs re-fetch
        retry_count: Number of feedback loop retries so far
        feedback_filings: Filing IDs flagged for re-fetch
        output_file: Path to the generated Excel report
    """

    # Config
    target_date: date

    # Scraper output
    filings: list[dict]
    filings_count: int

    # LLM output
    analyses: list[dict]

    # JEV output
    verdicts: list[dict]
    needs_reprocessing: bool

    # Feedback control
    retry_count: int
    feedback_filings: list[str]

    # Final output
    output_file: str

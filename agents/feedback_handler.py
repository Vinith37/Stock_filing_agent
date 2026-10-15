"""LangGraph Node & Edge Functions: Feedback Handler

Manages the feedback loop when JEV flags filings for reprocessing.
"""

from loguru import logger
from config.settings import settings


def handle_feedback(state: dict) -> dict:
    """LangGraph Node: Process feedback — identify filings needing re-fetch

    Args:
        state: Current graph state with 'verdicts' and 'retry_count'

    Returns:
        Updated state with incremented retry_count and feedback_filings list
    """
    verdicts = state.get("verdicts", [])
    retry_count = state.get("retry_count", 0)

    # Find filings flagged for reprocessing
    refetch_ids = [
        v["filing_id"]
        for v in verdicts
        if v.get("needs_reprocessing", False)
    ]

    logger.info(
        f"🔁 Feedback: {len(refetch_ids)} filings need re-fetch "
        f"(attempt {retry_count + 1}/{settings.jev_max_retries})"
    )

    for fid in refetch_ids:
        logger.debug(f"  → Re-fetching: {fid}")

    return {
        "retry_count": retry_count + 1,
        "feedback_filings": refetch_ids,
    }


def route_after_jev(state: dict) -> str:
    """Conditional edge: Does JEV need re-processing?

    Returns:
        'feedback' if any filing needs reprocessing, 'output' otherwise
    """
    if state.get("needs_reprocessing", False):
        return "feedback"
    return "output"


def check_retry_limit(state: dict) -> str:
    """Conditional edge: Have we exceeded the maximum retry count?

    Returns:
        'retry' to go back to scraper, 'give_up' to proceed to output
    """
    retry_count = state.get("retry_count", 0)

    if retry_count >= settings.jev_max_retries:
        logger.warning(
            f"🔁 Max retries ({settings.jev_max_retries}) reached — "
            f"proceeding to output with current results"
        )
        return "give_up"

    return "retry"

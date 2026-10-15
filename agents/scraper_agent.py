"""LangGraph Node: Scraper Agent — fetches daily filings from BSE & NSE"""

from datetime import date
from loguru import logger
from scrapers.bse_scraper import BSEScraper
from scrapers.nse_scraper import NSEScraper
from scrapers.document_parser import DocumentParser
from config.settings import settings


# Initialize scrapers (reused across invocations)
_bse = BSEScraper()
_nse = NSEScraper()
_parser = DocumentParser()


def scrape_exchange_filings(state: dict) -> dict:
    """LangGraph Node: Fetch and parse daily filings from BSE & NSE

    This node:
    1. Fetches corporate announcements from BSE and NSE for the target date
    2. Enriches filings with full document text (PDF/HTML parsing)
    3. Returns the list of filings for LLM analysis

    Args:
        state: Current graph state with optional 'target_date'

    Returns:
        Updated state with 'filings' and 'filings_count'
    """
    target_date = state.get("target_date", date.today())
    feedback_filings = state.get("feedback_filings", [])

    logger.info(f"📥 Scraping filings for {target_date}")

    all_filings = []

    # Fetch from BSE
    if settings.bse_enabled:
        try:
            bse_filings = _bse.fetch_daily_filings(target_date)
            all_filings.extend(bse_filings)
        except Exception as e:
            logger.error(f"BSE scraper failed: {e}")

    # Fetch from NSE
    if settings.nse_enabled:
        try:
            nse_filings = _nse.fetch_daily_filings(target_date)
            all_filings.extend(nse_filings)
        except Exception as e:
            logger.error(f"NSE scraper failed: {e}")

    # If this is a feedback retry, only re-process flagged filings
    if feedback_filings:
        all_filings = [f for f in all_filings if f.id in feedback_filings]
        logger.info(f"📥 Feedback retry: re-processing {len(all_filings)} filings")

    # Enrich with document text (PDF/HTML parsing)
    enriched = []
    for filing in all_filings:
        if filing.document_url and len(filing.raw_text) < 100:
            logger.debug(f"  Parsing document for {filing.company_name}...")
            doc_text = _parser.parse_document(filing.document_url)
            if doc_text:
                filing.raw_text = doc_text
            else:
                # Fallback to subject line
                filing.raw_text = filing.subject

        enriched.append(filing.model_dump())

    logger.info(
        f"📥 Total filings scraped: {len(enriched)} "
        f"(BSE: {sum(1 for f in enriched if f['source'] == 'BSE')}, "
        f"NSE: {sum(1 for f in enriched if f['source'] == 'NSE')})"
    )

    return {
        "filings": enriched,
        "filings_count": len(enriched),
        "retry_count": state.get("retry_count", 0),
    }

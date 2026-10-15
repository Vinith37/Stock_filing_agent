"""BSE/NSE Exchange Filings Analysis Agent

Entry point for running the daily filing analysis pipeline.
Uses LangGraph to orchestrate: Scraper → Phi-4 Mini → JEV → Excel

Usage:
    # Run for today
    python main.py

    # Run for a specific date
    python main.py --date 2026-10-14

    # Run the scheduler (daily at 4 PM)
    python main.py --schedule
"""

import asyncio
import argparse
from datetime import date, datetime
from loguru import logger
from pathlib import Path

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logger.add(
    "logs/agent_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
)


async def run_daily_analysis(target_date: date | None = None):
    """Execute the full filing analysis pipeline

    Args:
        target_date: Date to analyze filings for (defaults to today)

    Returns:
        Final graph state with all results
    """
    # Import here to avoid circular imports during graph compilation
    from graph.workflow import app
    from graph.state import AgentState

    target_date = target_date or date.today()

    logger.info("=" * 60)
    logger.info(f"🚀 Starting daily analysis for {target_date}")
    logger.info("=" * 60)

    # Initial state
    initial_state: AgentState = {
        "target_date": target_date,
        "filings": [],
        "analyses": [],
        "verdicts": [],
        "retry_count": 0,
        "needs_reprocessing": False,
        "feedback_filings": [],
    }

    # Run the LangGraph workflow
    try:
        result = app.invoke(initial_state)
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        raise

    # Report results
    output_file = result.get("output_file", "N/A")
    verdicts = result.get("verdicts", [])
    yes_count = sum(1 for v in verdicts if v.get("verdict") == "YES")
    no_count = len(verdicts) - yes_count

    logger.info("=" * 60)
    logger.info("✅ Analysis complete!")
    logger.info(f"   📊 Filings processed: {len(verdicts)}")
    logger.info(f"   ✅ YES verdicts: {yes_count}")
    logger.info(f"   ❌ NO verdicts: {no_count}")
    logger.info(f"   📁 Output: {output_file}")
    logger.info("=" * 60)

    return result


def run_scheduler():
    """Run the agent on a daily schedule at 4:00 PM IST"""
    import schedule
    import time

    def daily_job():
        logger.info("⏰ Scheduled run triggered")
        asyncio.run(run_daily_analysis(date.today()))

    # Schedule for 4:00 PM IST (after market close at 3:30 PM)
    schedule.every().day.at("16:00").do(daily_job)

    logger.info("📅 Scheduler started — running daily at 4:00 PM IST")
    logger.info("   Press Ctrl+C to stop")

    while True:
        schedule.run_pending()
        time.sleep(60)


def main():
    parser = argparse.ArgumentParser(
        description="BSE/NSE Exchange Filings Analysis Agent"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Target date in YYYY-MM-DD format (default: today)",
        default=None,
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run on a daily schedule at 4:00 PM IST",
    )

    args = parser.parse_args()

    if args.schedule:
        run_scheduler()
    else:
        target_date = (
            datetime.strptime(args.date, "%Y-%m-%d").date()
            if args.date
            else date.today()
        )
        asyncio.run(run_daily_analysis(target_date))


if __name__ == "__main__":
    main()

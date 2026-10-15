"""NSE India corporate announcements scraper"""

import httpx
import time
from datetime import datetime, date
from loguru import logger
from models.filing import RawFiling, ExchangeSource
from config.settings import settings


class NSEScraper:
    """Fetch corporate announcements from NSE India (nseindia.com)"""

    BASE_URL = "https://www.nseindia.com/api"
    ANNOUNCEMENTS_URL = f"{BASE_URL}/corporate-announcements"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        # Don't request brotli — let httpx handle decompression
        "Accept-Encoding": "gzip, deflate",
    }

    def __init__(self):
        self.client = httpx.Client(
            headers=self.HEADERS,
            timeout=30.0,
            follow_redirects=True,
        )
        self._init_session()

    def _init_session(self):
        """NSE requires cookies from homepage visit before API calls"""
        try:
            # Visit homepage to get session cookies
            resp = self.client.get("https://www.nseindia.com")
            logger.info(f"NSE: Session initialized (status={resp.status_code})")
        except Exception as e:
            logger.warning(f"NSE session init failed: {e}")

    def fetch_daily_filings(
        self, target_date: date | None = None
    ) -> list[RawFiling]:
        """Fetch all corporate announcements for a given date"""
        target_date = target_date or date.today()
        dt_str = target_date.strftime("%d-%m-%Y")

        logger.info(f"NSE: Fetching filings for {target_date}")

        params = {
            "index": "equities",
            "from_date": dt_str,
            "to_date": dt_str,
        }

        try:
            response = self.client.get(
                self.ANNOUNCEMENTS_URL, params=params
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"NSE HTTP error: {e.response.status_code}")
            # Try re-initializing session if 403
            if e.response.status_code == 403:
                logger.info("NSE: Re-initializing session...")
                self._init_session()
            return []
        except Exception as e:
            logger.error(f"NSE fetch failed: {e}")
            return []

        filings = []
        items = data if isinstance(data, list) else data.get("data", [])

        for item in items:
            try:
                # Parse date
                date_str = item.get("an_dt", "")
                try:
                    filing_date = datetime.strptime(
                        date_str, "%d-%b-%Y %H:%M:%S"
                    )
                except ValueError:
                    filing_date = datetime.combine(
                        target_date, datetime.min.time()
                    )

                filing = RawFiling(
                    id=f"NSE-{item.get('an_dt', '')}-{item.get('symbol', '')}",
                    source=ExchangeSource.NSE,
                    company_name=item.get("desc", "Unknown"),
                    company_code=item.get("symbol", ""),
                    isin=item.get("isin", ""),
                    filing_type=item.get("smIndustry", "Other"),
                    subject=item.get("attchmntText", ""),
                    filing_date=filing_date,
                    raw_text=item.get("attchmntText", ""),
                    document_url=item.get("attchmntFile", ""),
                    metadata={
                        "industry": item.get("smIndustry"),
                        "exchange_sub": item.get("exchdisstime"),
                    },
                )
                filings.append(filing)

            except Exception as e:
                logger.warning(f"NSE: Skipping malformed filing: {e}")
                continue

            time.sleep(settings.scrape_delay_seconds * 0.1)

        logger.info(f"NSE: Fetched {len(filings)} filings")
        return filings

    def close(self):
        """Close the HTTP client"""
        self.client.close()

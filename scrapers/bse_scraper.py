"""BSE India corporate announcements scraper"""

import httpx
import time
from datetime import datetime, date
from loguru import logger
from models.filing import RawFiling, ExchangeSource
from config.settings import settings


class BSEScraper:
    """Fetch corporate announcements from BSE India (bseindia.com)"""

    BASE_URL = "https://api.bseindia.com/BseIndiaAPI/api"
    ANNOUNCEMENTS_URL = f"{BASE_URL}/AnnGetData/w"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.bseindia.com/",
        "Origin": "https://www.bseindia.com",
    }

    def __init__(self):
        self.client = httpx.Client(
            headers=self.HEADERS,
            timeout=30.0,
            follow_redirects=True,
        )
        self._init_session()

    def _init_session(self):
        """BSE requires cookies — visit homepage first to get session"""
        try:
            self.client.get("https://www.bseindia.com/")
            logger.info("BSE: Session initialized with cookies")
        except Exception as e:
            logger.warning(f"BSE session init failed: {e}")

    def fetch_daily_filings(
        self, target_date: date | None = None
    ) -> list[RawFiling]:
        """Fetch all corporate announcements for a given date"""
        target_date = target_date or date.today()
        dt_str = target_date.strftime("%Y%m%d")

        logger.info(f"BSE: Fetching filings for {target_date}")

        params = {
            "strCat": "-1",  # All categories
            "strPrevDate": dt_str,
            "strScrip": "",
            "strSearch": "P",
            "strGet498": "Y",
            "strType": "C",
            "pageno": "1",
        }

        try:
            response = self.client.get(
                self.ANNOUNCEMENTS_URL, params=params
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"BSE HTTP error: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"BSE fetch failed: {e}")
            return []

        filings = []
        table_data = data.get("Table", [])

        for item in table_data:
            try:
                # Parse date — BSE returns various date formats
                date_str = item.get("NEWS_DT", "")
                try:
                    filing_date = datetime.strptime(
                        date_str, "%Y-%m-%dT%H:%M:%S"
                    )
                except ValueError:
                    filing_date = datetime.combine(
                        target_date, datetime.min.time()
                    )

                filing = RawFiling(
                    id=f"BSE-{item.get('NEWSID', '')}",
                    source=ExchangeSource.BSE,
                    company_name=item.get("SLONGNAME", "Unknown"),
                    company_code=str(item.get("SCRIP_CD", "")),
                    filing_type=item.get("CATEGORYNAME", "Other"),
                    subject=item.get("NEWSSUB", ""),
                    filing_date=filing_date,
                    raw_text=item.get("NEWSSUB", ""),
                    document_url=item.get("ATTACHMENTNAME", ""),
                    metadata={
                        "category": item.get("CATEGORYNAME"),
                        "subcategory": item.get("SUBCATNAME"),
                        "criticality": item.get("CRITICALITY"),
                    },
                )
                filings.append(filing)

            except Exception as e:
                logger.warning(f"BSE: Skipping malformed filing: {e}")
                continue

            # Respect rate limits
            time.sleep(settings.scrape_delay_seconds * 0.1)

        logger.info(f"BSE: Fetched {len(filings)} filings")
        return filings

    def close(self):
        """Close the HTTP client"""
        self.client.close()

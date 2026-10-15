"""Data models for raw exchange filings from BSE/NSE"""

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ExchangeSource(str, Enum):
    BSE = "BSE"
    NSE = "NSE"


class FilingType(str, Enum):
    FINANCIAL_RESULTS = "Financial Results"
    BOARD_MEETING = "Board Meeting"
    SHAREHOLDING = "Shareholding Pattern"
    INSIDER_TRADING = "Insider Trading"
    CORPORATE_ACTION = "Corporate Action"
    AGM_EGM = "AGM/EGM"
    REGULATORY = "Regulatory"
    OTHER = "Other"


class RawFiling(BaseModel):
    """Raw filing fetched from BSE/NSE"""

    id: str = Field(description="Unique filing identifier")
    source: ExchangeSource
    company_name: str
    company_code: str  # BSE scrip code or NSE symbol
    isin: str = ""
    filing_type: str  # Raw type from exchange
    subject: str  # Filing headline
    filing_date: datetime
    raw_text: str  # Extracted document content
    document_url: str = ""  # Link to original PDF/document
    metadata: dict = {}

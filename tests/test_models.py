"""Tests for data models"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from models.filing import RawFiling, ExchangeSource
from models.analysis import FilingAnalysis, FinancialMetrics
from models.verdict import JEVVerdict


class TestRawFiling:
    def test_create_bse_filing(self):
        filing = RawFiling(
            id="BSE-12345",
            source=ExchangeSource.BSE,
            company_name="Reliance Industries Ltd",
            company_code="500325",
            filing_type="Financial Results",
            subject="Q2 FY25 Results",
            filing_date=datetime(2026, 10, 14),
            raw_text="Revenue increased 12% YoY...",
        )
        assert filing.source == ExchangeSource.BSE
        assert filing.company_code == "500325"

    def test_create_nse_filing(self):
        filing = RawFiling(
            id="NSE-2026-10-14-TCS",
            source=ExchangeSource.NSE,
            company_name="Tata Consultancy Services",
            company_code="TCS",
            isin="INE467B01029",
            filing_type="Board Meeting",
            subject="Board Meeting Outcome",
            filing_date=datetime(2026, 10, 14),
            raw_text="The Board approved dividend...",
        )
        assert filing.source == ExchangeSource.NSE
        assert filing.isin == "INE467B01029"


class TestFilingAnalysis:
    def test_create_analysis(self):
        analysis = FilingAnalysis(
            filing_id="BSE-12345",
            category="Financial Results",
            sentiment="bullish",
            impact_score=8,
            key_metrics=FinancialMetrics(
                revenue="₹4,500 Cr",
                net_profit="₹320 Cr",
                eps="₹15.6",
            ),
            risk_flags=[],
            summary="Strong quarterly results with revenue growth.",
            data_quality=0.9,
        )
        assert analysis.sentiment == "bullish"
        assert analysis.impact_score == 8
        assert analysis.key_metrics.revenue == "₹4,500 Cr"


class TestJEVVerdict:
    def test_yes_verdict(self):
        verdict = JEVVerdict(
            filing_id="BSE-12345",
            company_name="Reliance Industries",
            probability=0.82,
            verdict="YES",
            confidence_factors=["Bullish sentiment (+0.25)"],
            risk_level="LOW",
        )
        assert verdict.verdict == "YES"
        assert verdict.probability > 0.65

    def test_no_verdict_with_reprocessing(self):
        verdict = JEVVerdict(
            filing_id="NSE-12345",
            company_name="HDFC Bank",
            probability=0.0,
            verdict="NO",
            needs_reprocessing=True,
            feedback_notes="Re-fetch needed",
        )
        assert verdict.needs_reprocessing is True

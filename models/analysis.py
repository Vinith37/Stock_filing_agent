"""Structured output schema for Phi-4 Mini filing analysis"""

from pydantic import BaseModel, Field


class FinancialMetrics(BaseModel):
    """Extracted financial metrics from a filing"""

    revenue: str = ""
    net_profit: str = ""
    eps: str = ""
    yoy_growth: str = ""
    debt_equity: str = ""
    dividend: str = ""
    other_metrics: dict = {}


class FilingAnalysis(BaseModel):
    """Structured output from Phi-4 Mini analysis"""

    filing_id: str = Field(default="", description="Filing identifier")
    category: str = Field(
        description="Filing category: Financial Results, Board Meeting, "
        "Insider Trading, Corporate Action, Regulatory, Other"
    )
    sentiment: str = Field(description="bullish, bearish, or neutral")
    impact_score: int = Field(
        description="Market impact score 1-10", ge=1, le=10
    )
    key_metrics: FinancialMetrics = Field(default_factory=FinancialMetrics)
    risk_flags: list[str] = Field(
        default_factory=list, description="Identified risk indicators"
    )
    summary: str = Field(description="2-3 sentence filing summary")
    data_quality: float = Field(
        description="Quality of source data 0.0-1.0", ge=0.0, le=1.0
    )

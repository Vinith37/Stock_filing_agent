"""JEV (Journal Entry Verification) verdict schema"""

from pydantic import BaseModel, Field


class JEVVerdict(BaseModel):
    """Journal Entry Verification output — the final decision on a filing"""

    filing_id: str
    company_name: str

    # Core outputs
    probability: float = Field(
        ge=0.0, le=1.0, description="Confidence score 0-1"
    )
    verdict: str = Field(description="YES or NO")

    # Supporting factors
    confidence_factors: list[str] = Field(default_factory=list)
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH
    historical_match: bool = True  # Consistent with past filings?
    data_quality: float = 1.0

    # Feedback signals
    needs_reprocessing: bool = False
    feedback_notes: str = ""

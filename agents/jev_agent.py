"""LangGraph Node: JEV Agent — Journal Entry Verification

Scores each filing analysis with a weighted probability and produces
a YES/NO verdict based on a configurable threshold.
"""

from loguru import logger
from models.verdict import JEVVerdict
from config.settings import settings


# ── Scoring Weights ───────────────────────────
WEIGHTS = {
    "sentiment_signal": 0.25,
    "impact_score": 0.25,
    "data_quality": 0.20,
    "risk_penalty": 0.15,
    "category_relevance": 0.15,
}

# Categories that are more market-relevant
HIGH_RELEVANCE_CATEGORIES = {
    "Financial Results",
    "Board Meeting",
    "Insider Trading",
    "Corporate Action",
}


def calculate_probability(analysis: dict) -> tuple[float, list[str]]:
    """Calculate JEV probability score from LLM analysis

    Uses a weighted scoring model across 5 dimensions:
    - Sentiment signal (0.25): bullish > bearish > neutral
    - Impact score (0.25): normalized 1-10 score
    - Data quality (0.20): source data completeness
    - Risk penalty (0.15): fewer flags = higher score
    - Category relevance (0.15): market-moving categories score higher

    Args:
        analysis: Dictionary from LLM analyzer output

    Returns:
        Tuple of (probability float 0-1, list of explanation factors)
    """
    factors = []
    score = 0.0

    # 1. Sentiment signal (weight: 0.25)
    sentiment = analysis.get("sentiment", "neutral")
    if sentiment == "bullish":
        score += 0.25
        factors.append("Bullish sentiment detected (+0.25)")
    elif sentiment == "bearish":
        score += 0.20
        factors.append("Bearish sentiment — potential short signal (+0.20)")
    else:
        score += 0.10
        factors.append("Neutral sentiment (+0.10)")

    # 2. Impact score (weight: 0.25)
    impact = analysis.get("impact_score", 1)
    impact_contribution = (impact / 10) * 0.25
    score += impact_contribution
    factors.append(f"Impact score {impact}/10 (+{impact_contribution:.3f})")

    # 3. Data quality (weight: 0.20)
    quality = analysis.get("data_quality", 0.5)
    quality_contribution = quality * 0.20
    score += quality_contribution
    factors.append(f"Data quality {quality:.1f} (+{quality_contribution:.3f})")

    # 4. Risk penalty (weight: 0.15)
    risk_flags = analysis.get("risk_flags", [])
    if len(risk_flags) == 0:
        score += 0.15
        factors.append("No risk flags (+0.150)")
    elif len(risk_flags) <= 2:
        score += 0.08
        factors.append(
            f"{len(risk_flags)} risk flag(s) — minor penalty (+0.080)"
        )
    else:
        score += 0.0
        factors.append(
            f"{len(risk_flags)} risk flags — significant penalty (+0.000)"
        )

    # 5. Category relevance (weight: 0.15)
    category = analysis.get("category", "Other")
    if category in HIGH_RELEVANCE_CATEGORIES:
        score += 0.15
        factors.append(f"High-relevance category: {category} (+0.150)")
    else:
        score += 0.05
        factors.append(f"Low-relevance category: {category} (+0.050)")

    return round(min(score, 1.0), 3), factors


def journal_entry_verification(state: dict) -> dict:
    """LangGraph Node: JEV — score and verdict each analysis

    For each LLM analysis result, this node:
    1. Checks data quality (flags for re-fetch if < 0.3)
    2. Calculates weighted probability score
    3. Applies YES/NO verdict threshold
    4. Determines risk level

    Args:
        state: Current graph state with 'analyses' and 'filings'

    Returns:
        Updated state with 'verdicts' and 'needs_reprocessing' flag
    """
    analyses = state.get("analyses", [])
    filings = state.get("filings", [])
    threshold = settings.jev_probability_threshold

    verdicts = []
    needs_feedback = False

    logger.info(
        f"⚖️  JEV: Evaluating {len(analyses)} analyses "
        f"(threshold={threshold})"
    )

    for analysis in analyses:
        # Find matching filing for context
        filing = next(
            (f for f in filings if f.get("id") == analysis.get("filing_id")),
            {},
        )

        # Check if data quality is too low — needs re-fetch
        data_quality = analysis.get("data_quality", 0.5)

        if data_quality < settings.jev_min_data_quality:
            verdict = JEVVerdict(
                filing_id=analysis.get("filing_id", ""),
                company_name=filing.get("company_name", "Unknown"),
                probability=0.0,
                verdict="NO",
                confidence_factors=["Data quality too low for reliable analysis"],
                risk_level="HIGH",
                data_quality=data_quality,
                needs_reprocessing=True,
                feedback_notes=(
                    f"Re-fetch needed: quality={data_quality:.2f} "
                    f"< threshold={settings.jev_min_data_quality}"
                ),
            )
            needs_feedback = True
        else:
            # Calculate probability score
            probability, factors = calculate_probability(analysis)

            # Apply verdict threshold
            verdict_str = "YES" if probability >= threshold else "NO"

            # Determine risk level from flags
            risk_flags = analysis.get("risk_flags", [])
            if len(risk_flags) > 2:
                risk_level = "HIGH"
            elif len(risk_flags) > 0:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

            verdict = JEVVerdict(
                filing_id=analysis.get("filing_id", ""),
                company_name=filing.get("company_name", "Unknown"),
                probability=probability,
                verdict=verdict_str,
                confidence_factors=factors,
                risk_level=risk_level,
                data_quality=data_quality,
                needs_reprocessing=False,
                feedback_notes="",
            )

        verdicts.append(verdict.model_dump())
        logger.info(
            f"  {verdict.company_name}: P={verdict.probability:.3f} → "
            f"{verdict.verdict} | Risk={verdict.risk_level}"
        )

    # Summary
    yes_count = sum(1 for v in verdicts if v["verdict"] == "YES")
    no_count = sum(1 for v in verdicts if v["verdict"] == "NO")
    logger.info(f"⚖️  JEV Summary: {yes_count} YES, {no_count} NO")

    return {
        "verdicts": verdicts,
        "needs_reprocessing": needs_feedback,
    }

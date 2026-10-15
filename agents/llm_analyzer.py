"""LangGraph Node: LLM Analyzer — processes filings through Phi-4 Mini"""

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger
from models.analysis import FilingAnalysis
from config.prompts import (
    FILING_ANALYSIS_SYSTEM_PROMPT,
    FILING_ANALYSIS_USER_PROMPT,
)
from config.settings import settings


def _get_llm() -> ChatOllama:
    """Create and return the Phi-4 Mini LLM instance"""
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=settings.llm_temperature,
        num_ctx=settings.llm_context_window,
    )


def analyze_with_phi4(state: dict) -> dict:
    """LangGraph Node: Analyze each filing with Phi-4 Mini

    For each filing, this node:
    1. Formats the filing data into a structured prompt
    2. Calls Phi-4 Mini via Ollama with structured output
    3. Returns classification, sentiment, metrics, risk flags, and summary

    Args:
        state: Current graph state with 'filings' list

    Returns:
        Updated state with 'analyses' list
    """
    filings = state.get("filings", [])
    analyses = []

    if not filings:
        logger.warning("🧠 No filings to analyze")
        return {"analyses": []}

    logger.info(f"🧠 Analyzing {len(filings)} filings with Phi-4 Mini...")

    # Initialize LLM with structured output
    llm = _get_llm()
    structured_llm = llm.with_structured_output(FilingAnalysis)

    for i, filing in enumerate(filings):
        try:
            # Truncate raw text to fit context window comfortably
            raw_text = filing.get("raw_text", "")[:6000]

            # Build the analysis prompt
            user_prompt = FILING_ANALYSIS_USER_PROMPT.format(
                source=filing.get("source", "Unknown"),
                company_name=filing.get("company_name", "Unknown"),
                company_code=filing.get("company_code", ""),
                filing_type=filing.get("filing_type", "Other"),
                filing_date=filing.get("filing_date", ""),
                subject=filing.get("subject", ""),
                raw_text=raw_text,
            )

            # Call Phi-4 Mini with structured output
            result: FilingAnalysis = structured_llm.invoke([
                SystemMessage(content=FILING_ANALYSIS_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ])

            # Attach filing ID
            result.filing_id = filing.get("id", "")
            analyses.append(result.model_dump())

            logger.info(
                f"  [{i + 1}/{len(filings)}] {filing.get('company_name', '?')}: "
                f"{result.sentiment} | impact={result.impact_score} | "
                f"quality={result.data_quality:.1f}"
            )

        except Exception as e:
            logger.error(
                f"  [{i + 1}/{len(filings)}] FAILED: "
                f"{filing.get('company_name', '?')} — {e}"
            )
            # Create a fallback analysis for failed items
            analyses.append({
                "filing_id": filing.get("id", ""),
                "category": "Other",
                "sentiment": "neutral",
                "impact_score": 1,
                "key_metrics": {
                    "revenue": "",
                    "net_profit": "",
                    "eps": "",
                    "yoy_growth": "",
                    "debt_equity": "",
                    "dividend": "",
                    "other_metrics": {},
                },
                "risk_flags": [],
                "summary": f"Analysis failed: {str(e)[:100]}",
                "data_quality": 0.0,
            })

    logger.info(
        f"🧠 Analysis complete: {len(analyses)} filings processed, "
        f"{sum(1 for a in analyses if a.get('data_quality', 0) > 0)} successful"
    )

    return {"analyses": analyses}

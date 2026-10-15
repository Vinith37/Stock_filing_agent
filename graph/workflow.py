"""LangGraph workflow definition — wires all nodes and edges together"""

from langgraph.graph import StateGraph, START, END
from graph.state import AgentState
from agents.scraper_agent import scrape_exchange_filings
from agents.llm_analyzer import analyze_with_phi4
from agents.jev_agent import journal_entry_verification
from agents.feedback_handler import (
    handle_feedback,
    route_after_jev,
    check_retry_limit,
)
from output.excel_writer import write_to_excel


def build_workflow() -> StateGraph:
    """Build and compile the full LangGraph workflow

    Graph structure:
        START → scraper → analyzer → jev → [output | feedback]
        feedback → [retry → scraper | give_up → output]
        output → END

    Returns:
        Compiled LangGraph StateGraph
    """
    graph = StateGraph(AgentState)

    # ── Add Nodes ──────────────────────────────
    graph.add_node("scraper", scrape_exchange_filings)
    graph.add_node("analyzer", analyze_with_phi4)
    graph.add_node("jev", journal_entry_verification)
    graph.add_node("feedback", handle_feedback)
    graph.add_node("excel_writer", write_to_excel)

    # ── Linear Edges ───────────────────────────
    graph.add_edge(START, "scraper")
    graph.add_edge("scraper", "analyzer")
    graph.add_edge("analyzer", "jev")

    # ── Conditional Edge: JEV → output or feedback ──
    graph.add_conditional_edges(
        "jev",
        route_after_jev,
        {
            "feedback": "feedback",
            "output": "excel_writer",
        },
    )

    # ── Conditional Edge: Feedback → retry or give up ──
    graph.add_conditional_edges(
        "feedback",
        check_retry_limit,
        {
            "retry": "scraper",
            "give_up": "excel_writer",
        },
    )

    # ── Terminal Edge ──────────────────────────
    graph.add_edge("excel_writer", END)

    return graph.compile()


# Compile the workflow once at module level
app = build_workflow()

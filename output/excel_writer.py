"""LangGraph Node: Excel Writer — writes JEV results to a formatted Excel file"""

from datetime import date
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from loguru import logger
from config.settings import settings


# ── Styling Constants ─────────────────────────
HEADER_FILL = PatternFill(start_color="1a365d", fill_type="solid")
HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
YES_FILL = PatternFill(start_color="c6f6d5", fill_type="solid")
NO_FILL = PatternFill(start_color="fed7d7", fill_type="solid")
HIGH_RISK_FILL = PatternFill(start_color="fff5f5", fill_type="solid")
THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)

# Column definitions: (header_name, column_width)
COLUMNS = [
    ("Date", 14),
    ("Company", 30),
    ("Symbol", 12),
    ("Source", 8),
    ("Category", 20),
    ("Sentiment", 12),
    ("Impact", 8),
    ("JEV Probability", 16),
    ("JEV Verdict", 12),
    ("Risk Level", 12),
    ("Risk Flags", 30),
    ("Summary", 50),
    ("Confidence Factors", 40),
    ("Document URL", 30),
]


def write_to_excel(state: dict) -> dict:
    """LangGraph Node: Write all JEV results to a formatted Excel file

    Creates an Excel workbook with:
    - Main sheet with all filing analyses and verdicts
    - Summary sheet with aggregate statistics
    - Color-coded YES/NO verdicts and risk levels

    Args:
        state: Current graph state with 'verdicts', 'analyses', 'filings'

    Returns:
        Updated state with 'output_file' path
    """
    verdicts = state.get("verdicts", [])
    analyses = state.get("analyses", [])
    filings = state.get("filings", [])

    # Create output directory
    output_dir = Path(settings.excel_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with date
    target_date = state.get("target_date", date.today())
    filename = f"jev_results_{target_date.isoformat()}.xlsx"
    filepath = output_dir / filename

    logger.info(f"📊 Writing {len(verdicts)} results to Excel...")

    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "JEV Analysis"

    # ── Write Headers ─────────────────────────
    for col_idx, (header, width) in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = THIN_BORDER
        ws.column_dimensions[cell.column_letter].width = width

    # Freeze header row
    ws.freeze_panes = "A2"

    # ── Write Data Rows ───────────────────────
    for row_idx, verdict in enumerate(verdicts, start=2):
        # Find matching analysis and filing
        analysis = next(
            (a for a in analyses if a.get("filing_id") == verdict.get("filing_id")),
            {},
        )
        filing = next(
            (f for f in filings if f.get("id") == verdict.get("filing_id")),
            {},
        )

        # Build row data
        row_data = [
            target_date.isoformat(),
            verdict.get("company_name", ""),
            filing.get("company_code", ""),
            filing.get("source", ""),
            analysis.get("category", ""),
            analysis.get("sentiment", ""),
            analysis.get("impact_score", ""),
            verdict.get("probability", 0),
            verdict.get("verdict", ""),
            verdict.get("risk_level", ""),
            ", ".join(analysis.get("risk_flags", [])),
            analysis.get("summary", ""),
            " | ".join(verdict.get("confidence_factors", [])),
            filing.get("document_url", ""),
        ]

        for col_idx, value in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = THIN_BORDER
            cell.alignment = Alignment(wrap_text=True, vertical="top")

        # Color-code verdict cell (column 9)
        verdict_cell = ws.cell(row=row_idx, column=9)
        if verdict.get("verdict") == "YES":
            verdict_cell.fill = YES_FILL
            verdict_cell.font = Font(bold=True, color="276749")
        else:
            verdict_cell.fill = NO_FILL
            verdict_cell.font = Font(bold=True, color="9b2c2c")

        # Highlight high-risk rows
        if verdict.get("risk_level") == "HIGH":
            risk_cell = ws.cell(row=row_idx, column=10)
            risk_cell.fill = HIGH_RISK_FILL
            risk_cell.font = Font(bold=True, color="c53030")

    # ── Add Summary Sheet ─────────────────────
    _add_summary_sheet(wb, verdicts, analyses, target_date)

    # Save workbook
    wb.save(filepath)
    logger.info(f"📊 Excel saved: {filepath}")

    return {"output_file": str(filepath)}


def _add_summary_sheet(
    wb: openpyxl.Workbook,
    verdicts: list[dict],
    analyses: list[dict],
    target_date: date,
):
    """Add a summary statistics sheet to the workbook"""
    ws = wb.create_sheet("Summary")

    total = len(verdicts)
    yes_count = sum(1 for v in verdicts if v.get("verdict") == "YES")
    no_count = total - yes_count
    avg_prob = (
        sum(v.get("probability", 0) for v in verdicts) / max(total, 1)
    )
    high_risk = sum(
        1 for v in verdicts if v.get("risk_level") == "HIGH"
    )
    bullish = sum(
        1 for a in analyses if a.get("sentiment") == "bullish"
    )
    bearish = sum(
        1 for a in analyses if a.get("sentiment") == "bearish"
    )

    summary_data = [
        ("Metric", "Value"),
        ("Report Date", target_date.isoformat()),
        ("Total Filings Analyzed", total),
        ("YES Verdicts", yes_count),
        ("NO Verdicts", no_count),
        ("YES Rate", f"{(yes_count / max(total, 1) * 100):.1f}%"),
        ("Average Probability", f"{avg_prob:.3f}"),
        ("High Risk Count", high_risk),
        ("Bullish Signals", bullish),
        ("Bearish Signals", bearish),
        ("Neutral Signals", total - bullish - bearish),
    ]

    for row_idx, (metric, value) in enumerate(summary_data, start=1):
        metric_cell = ws.cell(row=row_idx, column=1, value=metric)
        value_cell = ws.cell(row=row_idx, column=2, value=value)

        if row_idx == 1:
            metric_cell.font = Font(bold=True, size=12)
            value_cell.font = Font(bold=True, size=12)
            metric_cell.fill = HEADER_FILL
            metric_cell.font = HEADER_FONT
            value_cell.fill = HEADER_FILL
            value_cell.font = HEADER_FONT
        else:
            metric_cell.font = Font(size=11)

        metric_cell.border = THIN_BORDER
        value_cell.border = THIN_BORDER

    ws.column_dimensions["A"].width = 25
    ws.column_dimensions["B"].width = 20

# 📊 BSE/NSE Exchange Filings Analysis Agent

> AI-powered daily analysis of Indian stock exchange filings using **Phi-4 Mini** (3.8B) + **LangGraph**

## Architecture

```
BSE/NSE → Scraper Agent → Phi-4 Mini (Ollama) → JEV Agent → Excel Report
                ↑                                    |
                └──────── Feedback Loop ─────────────┘
```

## Quick Start

### 1. Install Ollama & Phi-4 Mini

```bash
brew install ollama
ollama serve &
ollama pull phi4-mini
```

### 2. Set Up Python Environment

```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate
uv sync

# Or using pip
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3. Run the Agent

```bash
# Analyze today's filings
python main.py

# Analyze a specific date
python main.py --date 2026-10-14

# Run on daily schedule (4 PM IST)
python main.py --schedule
```

## Project Structure

```
stock-filing-agent/
├── main.py                  # Entry point
├── config/                  # Settings & prompts
├── models/                  # Pydantic data schemas
├── scrapers/                # BSE & NSE scrapers
├── agents/                  # LangGraph nodes
├── graph/                   # Workflow orchestration
├── output/                  # Excel writer
├── tests/                   # Unit tests
└── data/output/             # Generated Excel reports
```

## Configuration

All settings are configurable via `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_OLLAMA_MODEL` | `phi4-mini` | Ollama model name |
| `AGENT_JEV_PROBABILITY_THRESHOLD` | `0.65` | YES/NO verdict threshold |
| `AGENT_JEV_MAX_RETRIES` | `3` | Max feedback loop retries |
| `AGENT_EXCEL_OUTPUT_DIR` | `./data/output` | Output directory |

## Running Tests

```bash
python -m pytest tests/ -v
```

## Hardware Requirements

- **Mac M1 8GB RAM** ✅ (Phi-4 Mini uses ~2.5 GB)
- **Python 3.11+**
- **Ollama** with `phi4-mini` model pulled

## License

Private — for personal use only.

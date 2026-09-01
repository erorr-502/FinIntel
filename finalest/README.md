# FININTEL — The AI Market Daily

FININTEL is a hackathon-ready, explainable multi-agent financial intelligence prototype for retail investors. The interface intentionally mixes a **Wall Street newspaper** feel in Light mode with a **navy terminal / fintech** feel in Dark mode while keeping the same layout and readable contrast.

## What the app demonstrates

- Three independent market dimensions: **price momentum, volume anomaly and sentiment**.
- Parallel specialist reasoning: **Technical, Volume, Sentiment, Fundamental/RAG, Risk and Skeptic**.
- A **Behavioral Guard** that detects FOMO, panic selling, social proof and performance-chasing behavior.
- A simple local **RAG-style filing retriever**. Fundamental claims always show the synthetic source ID and source text.
- **Profile-aware outputs**. Conservative, Moderate and Aggressive profiles use different portfolio-concentration limits.
- **Graceful degradation**. Missing feed, missing filing and conflicting-signal demos reduce confidence instead of crashing the pipeline.
- **Persistent JSONL performance logs** with latency, confidence and portfolio-concentration metrics.
- Working internal navigation for Front Page, Markets, Investigations, Filings, AI Desk, Portfolio, Watchlist, Scenario Lab, Performance, Archive and Settings.
- Search shortcuts for stocks and internal topics.

> All market prices and filings in this repository are simulated/synthetic for the 24-hour hackathon demo. FININTEL does not execute trades and is not financial advice.

## Run on Windows / VS Code

1. Extract the ZIP completely.
2. Open the extracted folder in VS Code.
3. Choose **Terminal → New Terminal**.
4. Run these commands one at a time:

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit normally opens `http://localhost:8501` automatically.

You can also double-click `start_windows.bat` after extracting the folder.

### Important

Do **not** run the project with `python app.py` or VS Code's normal **Run Python File** button. This is a Streamlit application and must be started with:

```powershell
python -m streamlit run app.py
```

## Files you should understand before judging

| File | What it does |
|---|---|
| `app.py` | UI, Light/Dark themes, navigation, forms, graphs and demo pages |
| `engine.py` | Runs the specialist agents in parallel and synthesizes their structured outputs |
| `rag.py` | Retrieves matching synthetic filing chunks |
| `profiles.py` | Stores the three risk profiles and concentration limits |
| `performance_log.py` | Saves and reloads analysis metrics in JSONL format |
| `data/market.csv` | Simulated market snapshot |
| `data/disclosures.json` | Synthetic regulatory / earnings evidence |
| `data/session_log.jsonl` | Persistent analysis log created by the app |
| `docs/ARCHITECTURE.md` | System architecture and decision logic |
| `docs/DEMO_SCRIPT.md` | Short judge demo flow |
| `docs/JUDGE_CHEATSHEET.md` | Simple explanation + likely judge questions |

## Best demo order

1. Show the Light newspaper interface, then switch to Dark mode.
2. Select `RELIANCE` and choose a Moderate investor profile.
3. Enter holdings and press **Analyse Stock with All Agents**.
4. Open **Investigations** and show the reasoning trace + Safety layer.
5. Open **Filings** and show that the Fundamental Agent is grounded in a visible source.
6. Open **Portfolio** and show the same market input under three different risk profiles.
7. Turn on a missing-feed or conflicting-signal simulation and rerun.
8. Open **Performance** to show persistent metrics.

The key line for judges is: **“FININTEL is an auditable research pipeline, not a black-box stock tip.”**

# FININTEL Architecture

## One-line flow

**Simulated market data + synthetic filings + user profile + portfolio + behavior → parallel specialist agents → transparent weighted synthesis → Behavioral Guard → Safety / Uncertainty → explainable dashboard + persistent metrics.**

## Specialist agents

Every specialist returns the same structured contract:

```text
name
signal
score          (-1 to +1)
confidence     (0 to 1)
reasoning
metrics
```

### 1. Technical Agent
Uses the momentum index and daily price movement. This is the first market-signal dimension.

### 2. Volume Agent
Compares current volume with the normal baseline. This is the second market-signal dimension.

### 3. Sentiment Agent
Classifies the normalized news/social sentiment feed. This is the third market-signal dimension.

### 4. Fundamental Agent / RAG
Retrieves the most relevant synthetic filing chunks before making a fundamental classification. If evidence is unavailable, the agent returns `UNAVAILABLE` instead of inventing a claim.

### 5. Risk Agent
Uses market volatility plus the user's current and projected portfolio concentration. Conservative, Moderate and Aggressive profiles have different concentration limits.

### 6. Skeptic Agent
Looks for reasons the consensus could be wrong: elevated volatility, unusual volume, crowded sentiment and explicit cross-agent disagreement.

## Behavioral Guard

The Behavioral Guard is a personalization / safety layer rather than a market-data agent. It checks user-selected behaviors for:

- panic selling / loss aversion
- FOMO / recency bias
- social proof
- performance chasing
- decision uncertainty

It never changes raw market facts. It can reduce confidence when the user's decision context is risky.

## Synthesis

Available specialist scores are combined with fixed, visible weights:

- Technical: 22%
- Volume: 13%
- Sentiment: 15%
- Fundamental/RAG: 30%
- Risk: 20%

The weights are renormalized if one source is unavailable. The Skeptic Agent does not secretly reverse the signal; it reduces confidence when it finds strong downside concerns.

## Safety / uncertainty

Confidence is reduced when:

- agents disagree,
- market data is missing,
- filing evidence is missing,
- the Skeptic Agent finds downside concerns,
- the portfolio violates the selected profile limit,
- behavioral-bias signals are strong.

The interface shows these reasons explicitly.

## Persistence

Each deliberate analysis writes one JSON object to `data/session_log.jsonl`. The Performance and Archive pages read this file back, so the metrics survive Streamlit reruns and app restarts.

## Why this design is easy to defend

The LLM is not required for the core logic. The hackathon prototype remains deterministic and auditable. A production version can swap the simulated data feed, retrieval method or natural-language explanation layer without replacing the structured agent contracts or synthesis logic.

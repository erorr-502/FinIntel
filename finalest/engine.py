"""FININTEL multi-agent analysis engine.

The engine is intentionally small and deterministic so a hackathon team can explain
all of it. Every specialist returns the same structured contract:
name, signal, confidence, score and reasoning.

Scores are normalized to [-1, +1]. Positive means supportive evidence; negative
means cautionary evidence. Risk and skeptic outputs can reduce the final confidence.
"""

from __future__ import annotations

import concurrent.futures
import statistics
import time
from pathlib import Path

import pandas as pd

from rag import retrieve


DATA = Path(__file__).parent / "data" / "market.csv"


def load_market_data() -> pd.DataFrame:
    """Load the bundled synthetic market snapshot."""
    return pd.read_csv(DATA)


def market_row(symbol: str, snapshot: dict | None = None) -> dict:
    """Use a refreshed UI snapshot when supplied; otherwise read the CSV row."""
    if snapshot:
        return dict(snapshot)
    frame = load_market_data()
    row = frame.query("symbol == @symbol")
    if row.empty:
        raise ValueError(f"Unknown symbol: {symbol}")
    return row.iloc[0].to_dict()


def _bounded(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def technical_agent(symbol: str, snapshot: dict | None = None, missing: bool = False, conflict: bool = False) -> dict:
    """Dimension 1: classify price momentum and daily movement."""
    if missing:
        return {
            "name": "Technical Agent",
            "signal": "UNAVAILABLE",
            "confidence": 0.0,
            "score": 0.0,
            "reasoning": "Market feed is unavailable, so no momentum claim is produced.",
            "metrics": {},
        }

    row = market_row(symbol, snapshot)
    momentum_score = _bounded((float(row["momentum"]) - 50.0) / 35.0)
    change_score = _bounded(float(row["day_change"]) / 5.0)
    score = _bounded(0.65 * momentum_score + 0.35 * change_score)
    if conflict:
        score = -abs(score or 0.35)

    signal = "BULLISH" if score > 0.25 else ("BEARISH" if score < -0.25 else "NEUTRAL")
    confidence = min(0.94, 0.58 + abs(score) * 0.32)
    return {
        "name": "Technical Agent",
        "signal": signal,
        "confidence": confidence,
        "score": score,
        "reasoning": (
            f"Momentum index is {row['momentum']:.1f}/100 and the day move is "
            f"{row['day_change']:+.2f}%."
        ),
        "metrics": {"momentum": float(row["momentum"]), "day_change": float(row["day_change"])},
    }


def volume_agent(symbol: str, snapshot: dict | None = None, missing: bool = False) -> dict:
    """Dimension 2: classify the volume anomaly versus normal activity."""
    if missing:
        return {
            "name": "Volume Agent",
            "signal": "UNAVAILABLE",
            "confidence": 0.0,
            "score": 0.0,
            "reasoning": "Market feed is unavailable, so volume cannot be compared with baseline.",
            "metrics": {},
        }

    row = market_row(symbol, snapshot)
    ratio = float(row["volume_anomaly"])
    score = _bounded((ratio - 1.0) / 1.0)
    signal = "HIGH ACTIVITY" if ratio >= 1.5 else ("LOW ACTIVITY" if ratio <= 0.7 else "NORMAL")
    confidence = min(0.92, 0.60 + min(abs(ratio - 1.0), 1.0) * 0.28)
    return {
        "name": "Volume Agent",
        "signal": signal,
        "confidence": confidence,
        "score": score,
        "reasoning": f"Trading volume is {ratio:.2f}× the normal baseline.",
        "metrics": {"volume_ratio": ratio},
    }


def sentiment_agent(symbol: str, snapshot: dict | None = None, missing: bool = False, conflict: bool = False) -> dict:
    """Dimension 3: classify the normalized sentiment feed."""
    if missing:
        return {
            "name": "Sentiment Agent",
            "signal": "UNAVAILABLE",
            "confidence": 0.0,
            "score": 0.0,
            "reasoning": "Sentiment feed is unavailable; the synthesis will continue without it.",
            "metrics": {},
        }

    row = market_row(symbol, snapshot)
    sentiment = _bounded(float(row["sentiment"]))
    if conflict:
        sentiment = -sentiment if sentiment != 0 else -0.35
    signal = "POSITIVE" if sentiment > 0.30 else ("NEGATIVE" if sentiment < -0.30 else "NEUTRAL")
    confidence = min(0.90, 0.58 + abs(sentiment) * 0.30)
    return {
        "name": "Sentiment Agent",
        "signal": signal,
        "confidence": confidence,
        "score": sentiment,
        "reasoning": f"Normalized news/social sentiment score is {sentiment:+.2f} on a -1 to +1 scale.",
        "metrics": {"sentiment": sentiment},
    }


def fundamental_agent(symbol: str, missing: bool = False, conflict: bool = False) -> tuple[dict, list[dict]]:
    """RAG-grounded fundamentals: every claim is tied to bundled disclosure evidence."""
    if missing:
        return ({
            "name": "Fundamental Agent",
            "signal": "UNAVAILABLE",
            "confidence": 0.0,
            "score": 0.0,
            "reasoning": "The filing corpus was intentionally made unavailable for this demo run.",
            "metrics": {},
        }, [])

    evidence = retrieve(symbol, "revenue margin growth risk uncertainty guidance debt outlook", top_k=2)
    if not evidence:
        return ({
            "name": "Fundamental Agent",
            "signal": "UNAVAILABLE",
            "confidence": 0.0,
            "score": 0.0,
            "reasoning": "No matching disclosure was retrieved; FININTEL refuses to invent a filing claim.",
            "metrics": {},
        }, [])

    text = " ".join(item["text"].lower() for item in evidence)
    positive_terms = ["growth", "stable", "steady", "expansion", "improving", "resilient", "strong", "higher"]
    negative_terms = ["risk", "pressure", "uncertainty", "sensitivity", "decline", "weak", "lower", "volatile"]
    positive = sum(text.count(term) for term in positive_terms)
    negative = sum(text.count(term) for term in negative_terms)
    denominator = max(positive + negative, 1)
    score = _bounded((positive - negative) / denominator)
    if conflict:
        score = abs(score or 0.35)

    signal = "POSITIVE" if score > 0.18 else ("NEGATIVE" if score < -0.18 else "MIXED")
    confidence = min(0.90, 0.62 + abs(score) * 0.24)
    return ({
        "name": "Fundamental Agent",
        "signal": signal,
        "confidence": confidence,
        "score": score,
        "reasoning": (
            f"RAG retrieved {len(evidence)} filing chunk(s): {positive} supportive indicator(s) "
            f"and {negative} risk indicator(s)."
        ),
        "metrics": {"positive_terms": positive, "risk_terms": negative, "sources": len(evidence)},
    }, evidence)


def risk_agent(symbol: str, profile: dict, portfolio: dict, snapshot: dict | None = None) -> tuple[dict, float]:
    """Personalize risk using profile concentration limit plus market volatility."""
    row = market_row(symbol, snapshot)
    portfolio_value = max(float(portfolio.get("value", 0)), 0.0)
    selected_holding = max(float(portfolio.get("selected_holding", 0)), 0.0)
    new_investment = max(float(portfolio.get("new_investment", 0)), 0.0)

    concentration = (selected_holding / portfolio_value * 100) if portfolio_value else 0.0
    projected_total = portfolio_value + new_investment
    projected_concentration = ((selected_holding + new_investment) / projected_total * 100) if projected_total else 0.0
    limit = float(profile["max_concentration"])
    volatility = float(row["volatility"])

    concentration_pressure = max(concentration, projected_concentration) / max(limit, 1.0)
    if concentration_pressure > 1.0 or volatility >= 0.32:
        signal, score = "HIGH RISK", -0.90
    elif concentration_pressure > 0.75 or volatility >= 0.20:
        signal, score = "MODERATE RISK", -0.35
    else:
        signal, score = "LOW RISK", 0.55

    return ({
        "name": "Risk Agent",
        "signal": signal,
        "confidence": 0.90,
        "score": score,
        "reasoning": (
            f"Current concentration is {concentration:.1f}% and would become {projected_concentration:.1f}% "
            f"after the planned investment; the {profile['risk_label'].lower()}-risk profile limit is {limit:.0f}%."
        ),
        "metrics": {
            "concentration": concentration,
            "projected_concentration": projected_concentration,
            "profile_limit": limit,
            "volatility": volatility,
        },
    }, concentration)


def skeptic_agent(symbol: str, snapshot: dict | None = None, conflict: bool = False) -> dict:
    """Challenge optimistic evidence and explicitly surface contradictions."""
    row = market_row(symbol, snapshot)
    warnings: list[str] = []
    if float(row["volatility"]) > 0.28:
        warnings.append("elevated volatility")
    if float(row["volume_anomaly"]) > 1.50:
        warnings.append("unusual volume")
    if abs(float(row["sentiment"])) > 0.65:
        warnings.append("crowded sentiment")
    if conflict:
        warnings.append("explicit cross-agent disagreement")

    signal = "SKEPTICAL" if len(warnings) >= 2 else ("WATCH" if warnings else "CLEAR")
    score = -0.65 if len(warnings) >= 2 else (-0.20 if warnings else 0.20)
    return {
        "name": "Skeptic Agent",
        "signal": signal,
        "confidence": 0.82 if warnings else 0.68,
        "score": score,
        "reasoning": (
            "Challenges the consensus using downside checks: " + ", ".join(warnings) + "."
            if warnings else
            "No major contradiction was found in the current snapshot, but uncertainty remains."
        ),
        "metrics": {"warnings": len(warnings)},
    }


def behavioral_guard(profile: dict, behavior: dict) -> dict:
    """Behavioral profiling layer required by the PS; it modifies confidence, not market facts."""
    reaction = behavior.get("reaction", "Review data before acting")
    decision_style = behavior.get("decision_style", "Research before deciding")

    warnings = []
    if reaction == "Sell quickly when prices fall":
        warnings.append("loss-aversion / panic-selling risk")
    elif reaction == "Buy more immediately after a rise":
        warnings.append("recency / FOMO risk")
    elif reaction == "I am unsure what I would do":
        warnings.append("decision uncertainty")

    if decision_style == "Follow social-media tips":
        warnings.append("social-proof bias")
    elif decision_style == "Choose what recently performed best":
        warnings.append("performance-chasing bias")

    if len(warnings) >= 2:
        status, factor = "HIGH BIAS RISK", 0.78
    elif warnings:
        status, factor = "WATCH", 0.90
    else:
        status, factor = "DISCIPLINED", 1.00

    return {
        "name": "Behavioral Guard",
        "status": status,
        "confidence_factor": factor,
        "reasoning": (
            "Detected " + " and ".join(warnings) + "."
            if warnings else "No major behavioral warning was selected."
        ) + f" Interpretation is calibrated for a {profile['risk_label'].lower()}-risk profile.",
    }


def _stance_from_score(score: float) -> tuple[str, str]:
    if score >= 0.45:
        return "RESEARCH POSITIVE", "CONSIDER / VERIFY"
    if score >= 0.12:
        return "MIXED-POSITIVE", "HOLD / WATCH"
    if score > -0.12:
        return "MIXED", "WAIT / REVIEW"
    if score > -0.45:
        return "CAUTIOUS", "CAUTION"
    return "NEGATIVE", "AVOID / REVIEW"


def build_advisory(stance: str, final_signal: str, confidence: float, risk: dict, behavior: dict, profile: dict, question: str) -> dict:
    """Convert the synthesis into an explainable, non-execution advisory."""
    if risk["signal"] == "HIGH RISK":
        headline = "Portfolio risk is the main constraint"
        action = "Review concentration before adding exposure; the market signal does not override your risk limit."
    elif behavior["status"] == "HIGH BIAS RISK":
        headline = "Slow down the decision"
        action = "Use the evidence trace and predefined risk rules before reacting to price or social signals."
    elif stance == "RESEARCH POSITIVE":
        headline = "Supportive evidence, but verify before acting"
        action = "Review the cited filing, uncertainty note and portfolio impact before any real-world decision."
    elif stance in {"MIXED-POSITIVE", "MIXED"}:
        headline = "Evidence is mixed"
        action = "Keep the asset on watch and wait for stronger agreement across independent signals."
    else:
        headline = "Caution dominates the current evidence"
        action = "Investigate the negative signals and avoid relying on a single market move."

    return {
        "headline": headline,
        "action": action,
        "final_signal": final_signal,
        "confidence": confidence,
        "profile_note": (
            f"Personalized for {profile['goal'].lower()} with a maximum single-position "
            f"concentration of {profile['max_concentration']}%."
        ),
        "question": question.strip() or "What does the current evidence mean for this portfolio?",
    }


def run_analysis(
    symbol: str,
    profile: dict,
    missing_feed: bool = False,
    conflict: bool = False,
    snapshot: dict | None = None,
    portfolio: dict | None = None,
    behavior: dict | None = None,
    question: str = "",
    missing_filing: bool = False,
) -> dict:
    """Run independent specialists in parallel and synthesize a profile-aware result."""
    start = time.perf_counter()
    portfolio = portfolio or {"value": 100000, "selected_holding": 0, "new_investment": 0}
    behavior = behavior or {
        "reaction": "Review data before acting",
        "decision_style": "Research before deciding",
    }

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            "technical": executor.submit(technical_agent, symbol, snapshot, missing_feed, conflict),
            "volume": executor.submit(volume_agent, symbol, snapshot, missing_feed),
            "sentiment": executor.submit(sentiment_agent, symbol, snapshot, missing_feed, conflict),
            "fundamental": executor.submit(fundamental_agent, symbol, missing_filing, conflict),
            "risk": executor.submit(risk_agent, symbol, profile, portfolio, snapshot),
            "skeptic": executor.submit(skeptic_agent, symbol, snapshot, conflict),
        }
        technical = futures["technical"].result()
        volume = futures["volume"].result()
        sentiment = futures["sentiment"].result()
        fundamental, evidence = futures["fundamental"].result()
        risk, concentration = futures["risk"].result()
        skeptic = futures["skeptic"].result()

    behavioral = behavioral_guard(profile, behavior)
    agents = [technical, volume, sentiment, fundamental, risk, skeptic]

    weights = {
        "Technical Agent": 0.22,
        "Volume Agent": 0.13,
        "Sentiment Agent": 0.15,
        "Fundamental Agent": 0.30,
        "Risk Agent": 0.20,
    }
    usable = [a for a in agents if a["name"] in weights and a["signal"] != "UNAVAILABLE"]
    weight_total = sum(weights[a["name"]] for a in usable)

    if not usable or weight_total == 0:
        raw_score = 0.0
        stance, final_signal = "INSUFFICIENT DATA", "PAUSE / VERIFY"
    else:
        raw_score = sum(weights[a["name"]] * float(a["score"]) for a in usable) / weight_total
        stance, final_signal = _stance_from_score(raw_score)

    directional = [a["score"] for a in usable if abs(float(a["score"])) >= 0.25 and a["name"] != "Risk Agent"]
    has_positive = any(v > 0 for v in directional)
    has_negative = any(v < 0 for v in directional)
    conflict_detected = conflict or (has_positive and has_negative)

    available_confidences = [float(a["confidence"]) for a in usable]
    confidence = statistics.mean(available_confidences) if available_confidences else 0.25
    confidence *= 0.80 + 0.20 * min(abs(raw_score) + 0.25, 1.0)
    confidence *= behavioral["confidence_factor"]
    if skeptic["signal"] == "SKEPTICAL":
        confidence *= 0.88
    if conflict_detected:
        confidence *= 0.78
    if missing_feed:
        confidence *= 0.75
    if missing_filing or not evidence:
        confidence *= 0.82
    if risk["signal"] == "HIGH RISK":
        confidence = min(confidence, 0.62)
        if final_signal == "CONSIDER / VERIFY":
            final_signal = "HOLD / REVIEW RISK"
            stance = "RISK-CONSTRAINED POSITIVE"
    confidence = max(0.20, min(0.94, confidence))

    row = market_row(symbol, snapshot)
    market_dimensions = {
        "price_momentum": {
            "label": technical["signal"],
            "value": float(row["momentum"]),
            "explanation": technical["reasoning"],
        },
        "volume_anomaly": {
            "label": volume["signal"],
            "value": float(row["volume_anomaly"]),
            "explanation": volume["reasoning"],
        },
        "sentiment": {
            "label": sentiment["signal"],
            "value": float(row["sentiment"]),
            "explanation": sentiment["reasoning"],
        },
    }

    trace = [
        f"Ingested the simulated market snapshot for {symbol}.",
        "Dispatched Technical, Volume, Sentiment, Fundamental/RAG, Risk and Skeptic specialists in parallel.",
        (
            f"Retrieved {len(evidence)} cited disclosure chunk(s) for the Fundamental Agent."
            if evidence else
            "No filing evidence was available, so the Fundamental Agent was marked unavailable."
        ),
        f"Applied the {profile['risk_label'].lower()}-risk profile and portfolio concentration rules.",
        f"Applied Behavioral Guard status: {behavioral['status']}.",
        "Combined available structured agent scores with transparent fixed weights.",
    ]
    if conflict_detected:
        trace.append("Detected conflicting directional signals and reduced synthesis confidence.")
    if missing_feed:
        trace.append("Market feed degradation was detected; market-derived agents abstained.")
    if missing_filing:
        trace.append("Filing degradation was detected; no uncited fundamental claim was generated.")
    trace.append("Ran the Skeptic and Safety checks before exposing the final research signal.")

    uncertainty_reasons = []
    if conflict_detected:
        uncertainty_reasons.append("independent signals disagree")
    if missing_feed:
        uncertainty_reasons.append("market feed is incomplete")
    if missing_filing or not evidence:
        uncertainty_reasons.append("filing evidence is unavailable")
    if skeptic["signal"] == "SKEPTICAL":
        uncertainty_reasons.append("the Skeptic Agent found downside concerns")
    if behavioral["status"] in {"WATCH", "HIGH BIAS RISK"}:
        uncertainty_reasons.append("behavioral bias may influence the decision")
    if risk["signal"] == "HIGH RISK":
        uncertainty_reasons.append("portfolio concentration exceeds the selected profile limit")
    if not uncertainty_reasons:
        uncertainty_reasons.append("normal market uncertainty remains")

    safety = {
        "name": "Safety / Uncertainty Layer",
        "status": "CAUTION" if len(uncertainty_reasons) >= 2 else "MONITORED",
        "uncertainty": max(6, round((1.0 - confidence) * 100)),
        "reasoning": "; ".join(uncertainty_reasons).capitalize() + ".",
    }

    advisory = build_advisory(stance, final_signal, confidence, risk, behavioral, profile, question)

    contributions = []
    for agent in usable:
        weight = weights[agent["name"]]
        contributions.append({
            "agent": agent["name"],
            "weight": weight,
            "score": float(agent["score"]),
            "weighted_score": float(agent["score"]) * weight,
        })

    return {
        "asset": symbol,
        "stance": stance,
        "final_signal": final_signal,
        "confidence": confidence,
        "latency_ms": (time.perf_counter() - start) * 1000.0,
        "signal_score": round((raw_score + 1.0) * 50.0, 1),
        "raw_score": raw_score,
        "summary": (
            "FININTEL combines three independent market dimensions, cited filing evidence, "
            "portfolio risk, behavioral context and a skeptical challenge before synthesis."
        ),
        "agents": agents,
        "behavioral": behavioral,
        "market_dimensions": market_dimensions,
        "evidence": evidence,
        "trace": trace,
        "conflict_detected": conflict_detected,
        "agent_contributions": contributions,
        "portfolio": {
            "value": float(portfolio.get("value", 0)),
            "selected_holding": float(portfolio.get("selected_holding", 0)),
            "new_investment": float(portfolio.get("new_investment", 0)),
            "concentration": round(concentration, 1),
            "projected_concentration": round(risk["metrics"]["projected_concentration"], 1),
            "risk_flag": "REVIEW" if risk["signal"] == "HIGH RISK" else "OK",
        },
        "advisory": advisory,
        "safety": safety,
        "safety_note": (
            "Educational research output only. FININTEL does not execute trades and is not financial advice. "
            "The bundled market data and disclosures are simulated/synthetic for the hackathon demo."
        ),
    }

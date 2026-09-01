# FININTEL — Multi-Agent Financial Intelligence System

FININTEL is a multi-agent AI-based financial intelligence platform built for **HackVerse: Into the Web — Sprint 1**.

The goal of FININTEL is to help retail investors understand market information in a simpler and more explainable way.

Instead of showing only stock prices or charts, FININTEL combines multiple independent analysis agents, user risk information, financial documents, and market signals to generate a final investment insight with clear reasoning.

> This project is an educational hackathon prototype and does not provide real financial advice.

---

## Problem Statement

Retail investors have access to a large amount of financial information such as:

- Market price data
- Trading volume
- Financial filings
- Earnings information
- Market sentiment
- Portfolio information

However, understanding all this information together can be difficult.

FININTEL attempts to bridge this gap by using multiple specialized agents that analyze different parts of the market independently and combine their results into one explainable insight.

---

## What FININTEL Does

A user can:

- Select a stock to investigate
- View market signals and trends
- Analyse technical momentum
- Detect unusual trading volume
- Understand market sentiment
- Retrieve information from financial documents
- View portfolio concentration and risk
- Receive a combined AI-generated market signal
- See the reasoning behind the final result
- View the evidence used by the system
- Test failure scenarios to understand how the system behaves when data is missing

---

## Multi-Agent Architecture

FININTEL uses multiple specialized agents instead of relying on one model for everything.

### Technical Agent

Analyses price movement and momentum.

It helps answer:

> Is the stock showing bullish, bearish or neutral technical behaviour?

### Volume Agent

Looks for abnormal trading activity by comparing current volume with normal trading volume.

It helps identify whether there is unusual market participation.

### Sentiment Agent

Analyses the available sentiment signal and determines whether the current sentiment is:

- Positive
- Neutral
- Negative

### Fundamental Agent

Retrieves relevant information from the financial filing corpus before making a classification.

The agent only analyses information that is present in the retrieved evidence.

This reduces unsupported or hallucinated financial claims.

### Synthesis Layer

The outputs of all agents are combined into one final market intelligence result.

The final result includes:

- Overall signal
- Confidence
- Agent contributions
- Explanation
- Risk adjustments

---

## Retrieval-Augmented Analysis

FININTEL includes a lightweight retrieval system for financial documents.

The process is:

`User Query`

↓

`Retrieve Relevant Filing Information`

↓

`Select the Most Relevant Evidence`

↓

`Fundamental Analysis`

↓

`Source Attribution`

The retrieved evidence is shown to the user so that the reasoning can be checked instead of treating the AI output as a black box.

---

## Personalised Risk Analysis

The same stock should not necessarily produce the same conclusion for every investor.

FININTEL considers information such as:

- Risk profile
- Existing portfolio
- Portfolio concentration
- Investment behaviour

For example, a stock may look positive from a market perspective but still receive a caution signal if the investor already has too much exposure to that stock.

---

## Explainable AI

One of the main goals of FININTEL is explainability.

Instead of displaying only:

`BUY`

or

`SELL`

the system shows:

- Which agents were positive
- Which agents were cautious
- Confidence of each analysis
- Evidence used
- Portfolio risk
- Final reasoning

This makes it easier for the user to understand **why** the system produced a particular result.

---

## Graceful Failure Handling

Real financial systems may sometimes have incomplete information.

FININTEL includes demo controls that allow us to simulate situations such as:

- Missing market data
- Missing financial filing
- Conflicting signals

Instead of crashing or generating unsupported information, the system continues using the available data and reduces the confidence of the final result when required.

---

## User Interface

FININTEL uses a financial newspaper + Wall Street inspired interface.

The design includes:

- Newspaper-style light mode
- Wall Street-inspired dark mode
- Responsive sidebar navigation
- Market overview
- AI agent cards
- Portfolio and risk information
- Evidence and sources
- Market trends
- Performance information
- Regulatory filing retrieval
- Scenario testing

Both themes are designed to keep text, controls and important information clearly visible.

---

## Light and Dark Mode

FININTEL supports two visual themes.

### Light Mode

Inspired by traditional financial newspapers and Wall Street publications.

### Dark Mode

Inspired by modern financial terminals and trading dashboards.

The user can switch between both themes directly from the interface.

---

## Technology Used

### Frontend / Interface

- Streamlit
- HTML
- CSS

### Backend

- Python

### Data Processing

- Pandas

### AI Architecture

- Multi-agent architecture
- Structured agent outputs
- Synthesis layer

### Document Intelligence

- Retrieval-Augmented Generation concepts
- Financial document retrieval
- Source-grounded analysis

### Data

For the hackathon prototype, market data and financial filing information are simulated/synthetic.

This allows us to demonstrate the complete architecture without depending on unstable or paid financial APIs.

---

## Project Structure

```text
FININTEL/
│
├── app.py
│
├── engine.py
├── rag.py
├── profiles.py
├── performance_log.py
│
├── data/
│   ├── market data
│   ├── user profiles
│   └── session logs
│
├── documents/
│   └── synthetic financial filings
│
├── assets/
│   └── UI images and design assets
│
├── requirements.txt
└── README.md

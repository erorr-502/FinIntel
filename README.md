# FININTEL — Multi-Agent Financial Intelligence System

**AI investigates. You invest intelligently.**

FININTEL is an explainable multi-agent financial intelligence platform developed for **HackVerse: Into the Web — Sprint 1**, organized by the **IEEE Robotics & Automation Society, VIT Chennai Student Chapter**.

The project is based on:

> **PS-01 — Multi-Agent Autonomous Financial Intelligence System for Retail Investors**

FININTEL combines market signals, financial documents, investor risk profiles and multiple specialised agents to generate understandable and explainable financial insights.

Instead of only showing stock charts or predictions, FININTEL focuses on:

**What is happening, why is it happening, and what does it mean for this particular investor?**

---
## Team Data Divas

- Juee Mahale
- Pranjali Joshi
- Sagnika Mukherjee
- Garima Choudhari

---

## The Problem

Retail investors already have access to stock prices, trading volumes, market sentiment, corporate filings and portfolio data.

The main difficulty is understanding all this information together and converting it into a useful, personalised and explainable insight.

FININTEL connects these different signals using a coordinated **multi-agent intelligence system**.

---

## Features

- Technical, Volume, Sentiment and Fundamental Agents
- Multi-agent synthesis
- Price momentum and volume analysis
- Market sentiment analysis
- Portfolio and risk analysis
- RAG-based financial document retrieval
- Source-backed fundamental analysis
- Personalised insights for different risk profiles
- Confidence-based final signals
- Failure handling for missing or conflicting data
- Performance tracking
- Light and Dark mode
- Newspaper + Wall Street inspired UI

---

## Multi-Agent Architecture

Different agents independently analyse different parts of the same stock before their results are combined.

```text
                    USER
                     │
                     ▼
          Stock + Investor Profile
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   TECHNICAL       VOLUME      SENTIMENT
     AGENT          AGENT        AGENT
        │            │            │
        └────────────┼────────────┘
                     │
                     ▼
              FUNDAMENTAL AGENT
              + Financial Evidence
                     │
                     ▼
              Investor Risk/Profile
                     │
                     ▼
               SYNTHESIS LAYER
                     │
                     ▼
            FINAL MARKET INSIGHT
                     │
            Explanation + Sources

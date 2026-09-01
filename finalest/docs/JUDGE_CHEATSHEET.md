# FININTEL Judge Cheatsheet — Simple Explanation

## What is our project?

FININTEL helps a retail investor understand **what is happening in a stock and what it means for their own portfolio**. Instead of one AI giving one answer, different agents look at different evidence and then a synthesis layer combines them.

## Why multi-agent?

A real financial decision is not only about price. One agent can be optimistic while another sees risk. Keeping them separate makes disagreement visible and easier to explain.

## What does each agent do?

- **Technical Agent:** checks price momentum and daily price movement.
- **Volume Agent:** checks whether trading activity is unusually high or low.
- **Sentiment Agent:** checks the simulated news/social sentiment score.
- **Fundamental Agent:** retrieves filing evidence and checks whether it looks supportive or risky.
- **Risk Agent:** checks volatility and whether this stock is too large a part of the user's portfolio.
- **Skeptic Agent:** actively tries to challenge the positive story.

## What is RAG here?

RAG means **retrieve first, answer using that evidence second**. Our Fundamental Agent searches the bundled filing corpus and shows the source ID and exact retrieved text. If there is no source, it returns `UNAVAILABLE`.

## How is it personalized?

The Risk Agent uses different concentration limits:

- Conservative: 15%
- Moderate: 35%
- Aggressive: 45%

So the same stock can be acceptable for one profile and too concentrated for another.

## How do we handle failures?

We do not let the app crash or invent missing facts. A missing market feed makes market agents abstain. A missing filing makes the Fundamental Agent abstain. The remaining agents still run and final confidence is reduced.

## What are the logged metrics?

Each analysis persists at least these metrics:

1. response latency,
2. final confidence,
3. portfolio concentration.

We also save signal score, profile, final stance, conflict status and safety status.

## Why is the UI newspaper themed?

The product is about turning a noisy stream of market information into a readable daily intelligence brief. The newspaper metaphor makes the system feel like a research desk, while Dark mode keeps the terminal / Wall Street feel.

## Is the data real?

No. The hackathon build uses simulated market data and synthetic filing text on purpose. This lets us demonstrate the complete architecture safely without depending on unstable paid APIs during judging.

## Is this financial advice?

No. It is an educational research prototype. It does not execute trades, and the final signal is always accompanied by uncertainty, evidence and risk context.

## What would we change for production?

We would replace the simulated feed with licensed/live data, replace the simple local retriever with a production vector database, add authentication and secure user storage, and add stronger evaluation/backtesting. The agent contracts and explainable synthesis can remain the same.

# Idea — follow-up to Prospect Theory: An Analysis of Decision under Risk (psychology)

Anchor paper: Prospect Theory: An Analysis of Decision under Risk (Kahneman D et al., 1979; DOI 10.2307/1914185, https://doi.org/10.2307/1914185).

Research question: Do current open-weight LLMs (qwen-2.5 family, scaled across 1B-72B) reproduce the certainty-equivalent shifts predicted by Prospect Theory when prompted as decision-makers on the original Kahneman-Tversky lottery battery?

Hypothesis: Larger LLMs exhibit human-like risk aversion for gains + risk seeking for losses; the reflection effect's strength increases monotonically with model size on the original lottery set.

Methods: Implement the K-T lottery battery as a prompt template; run 100 trials per lottery per model with temperature sweep; fit per-model Prospect-Theory parameters via MLE; bootstrap CIs.

Feasibility: implementable with free-model LLM panels + publicly available data; no paid services or proprietary compute required.

---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Influence of Emotional Contagion on Collective Decision-Making in Online Forums

**Field**: psychology

## Research question

Does the emotional tone of early contributions in online forums bias subsequent participants and thereby affect the quality and efficiency of collective decisions?

## Motivation

Collective decisions in online communities (e.g., product recommendations, policy discussions) shape real‑world outcomes, yet the role of affective dynamics in these settings is poorly understood. While emotion contagion is well‑documented in face‑to‑face groups, its impact on the convergence, diversity, and accuracy of crowd‑sourced judgments online remains a gap. Clarifying this relationship can inform platform design and moderation policies to promote more rational collective intelligence.

## Related work

- [Collective emotions online and their influence on community life (2011)](http://arxiv.org/abs/1107.2647v1) — Shows that emotional expressions in e‑communities correlate with community engagement and cohesion.  
- [An agent-based model for emotion contagion and competition in online social media (2017)](http://arxiv.org/abs/1706.02676v1) — Provides a computational framework for how emotions spread and compete on social platforms, useful for hypothesizing mechanisms in forums.  
- [Network analysis reveals open forums and echo chambers in social media discussions of climate change (2015)](https://doi.org/10.1016/j.gloenvcha.2015.03.006) — Demonstrates how structural features of online discussions relate to opinion polarization, offering metrics for decision quality (e.g., echo‑chamber detection).

## Expected results

We anticipate finding that threads seeded with strongly positive (or negative) sentiment produce faster consensus but lower opinion diversity, and that such sentiment bias reduces the predictive accuracy of collective judgments compared to neutral‑seeded threads. Confirmation will be measured by (1) a statistically significant correlation between early‑post sentiment scores and later‑post sentiment alignment, and (2) a drop in decision‑quality metrics (e.g., agreement‑to‑ground‑truth error) for high‑contagion threads, assessed via mixed‑effects regression (p < 0.05).

## Methodology sketch

- **Data acquisition**  
  - Download Reddit comment archives (Pushshift API) for a set of subreddits with clear decision‑making outcomes (e.g., r/AskScience, r/ProductReviews).  
  - Download Stack Exchange data dumps for sites that host voting‑based decisions (e.g., Politics.SE, Seasoned Advice).  
- **Thread selection**  
  - Identify discussion threads that contain a clearly defined “decision point” (e.g., a question asking for a recommendation, a poll, or a problem‑solving request).  
  - Extract the first N = 3 top‑level posts as “seed posts”.  
- **Emotion measurement**  
  - Apply VADER sentiment analysis (NLTK) to compute a compound sentiment score for each post.  
  - Compute an “emotional contagion index” as the Pearson correlation between seed‑post sentiment and the sentiment trajectory of subsequent replies over the first 20 comments.  
- **Decision‑quality metrics**  
  - **Agreement**: proportion of later comments that align with the majority vote or accepted answer.  
  - **Diversity**: Shannon entropy of sentiment and topical keywords across all replies.  
  - **Predictive accuracy**: compare the collective judgment (e.g., majority‑vote outcome) against an external ground truth where available (e.g., product performance benchmarks, expert‑verified facts).  
- **Statistical modeling**  
  - Fit mixed‑effects linear models with thread‑level random intercepts: decision‑quality ~ seed sentiment + contagion index + control variables (thread length, topic popularity).  
  - Test significance of contagion coefficients using Wald tests (α = 0.05).  
- **Robustness checks**  
  - Repeat analysis with alternative sentiment tools (TextBlob, pretrained BERT‑based sentiment model) to ensure results are not tool‑specific.  
  - Perform a lagged analysis to rule out reverse causality (i.e., later sentiment driving early sentiment).  
- **Reproducibility**  
  - All code will be written in Python (≥3.9) using only CPU‑friendly libraries (pandas, scikit‑learn, statsmodels).  
  - Scripts will be containerized with a lightweight Docker image (<1 GB) to run within the 7 GB RAM, 2‑core GitHub Actions environment, and each analysis step will be limited to ≤30 min wall‑clock time.

## Duplicate-check

- Reviewed existing ideas: (none provided).  
- Closest match: (no comparable entry found).  
- Verdict: **NOT a duplicate**.

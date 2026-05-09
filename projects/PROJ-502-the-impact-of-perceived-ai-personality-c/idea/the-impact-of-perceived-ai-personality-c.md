---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Perceived AI Personality Consistency on User Trust

**Field**: psychology

## Research question

Does perceived personality consistency in AI chatbots predict user trust levels across multiple interaction sessions?

## Motivation

Establishing whether personality consistency drives trust is critical for designing reliable conversational AI systems, yet existing work focuses primarily on personality *type* rather than *stability* over time. If consistency matters, inconsistent AI responses could erode user trust even when individual responses are appropriate, creating a design gap in current AI-human interaction guidelines.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using the following terms: "AI personality consistency trust," "chatbot personality stability user trust," "conversational agent consistency reliability," and "LLM personality trait user trust." We also broadened to "explainability trust AI systems" and "AI-generated content trust perceptions" to capture tangentially related work on trust mechanisms in AI. The literature search returned 2 results total, neither of which directly addresses personality consistency as a predictor of trust in conversational agents.

### What is known

- [Preliminary Quantitative Study on Explainability and Trust in AI Systems](http://arxiv.org/abs/2510.15769v1) — Establishes that explainability mechanisms influence trust in high-stakes AI deployments, but does not examine personality consistency as a trust factor.
- [Examining the Impact of Label Detail and Content Stakes on User Perceptions of AI-Generated Images on Social Media](http://arxiv.org/abs/2510.19024v1) — Documents how transparency labels affect trust in AI-generated content, but focuses on visual media rather than conversational agents.

### What is NOT known

No published work has measured whether consistency in an AI's personality expression (as opposed to transparency or explainability) predicts user trust in conversational settings. Existing trust literature conflates personality *type* with personality *stability*, leaving the independent effect of consistency unquantified.

### Why this gap matters

Conversational AI developers lack evidence-based guidance on whether maintaining consistent personality traits across sessions improves long-term user engagement. If consistency drives trust, inconsistent chatbot behavior could undermine adoption in healthcare, education, and customer service applications where reliability is critical.

### How this project addresses the gap

This project measures personality consistency using linguistic style analysis across conversation sessions and correlates it with user trust indicators from public chatbot datasets. The methodology directly quantifies the previously unmeasured relationship between consistency and trust, producing the first empirical evidence on this mechanism.

## Expected results

We expect to find a positive correlation between personality consistency scores and user trust indicators, with consistency explaining at least 15% of variance in trust measures. A null result (no significant correlation) would be equally informative, suggesting that personality stability may be less critical than other factors like response accuracy or transparency.

## Methodology sketch

- Download public chatbot conversation dataset (e.g., DailyDialog or OpenSubtitles with AI-chatbot labels from HuggingFace Datasets: `huggingface.co/datasets/DailyDialog`)
- Extract conversation sessions per user (≥3 interactions required for consistency measurement)
- Apply pre-trained sentiment analysis model (`distilbert-base-uncased` via HuggingFace Transformers) to each response
- Compute personality consistency score: variance of sentiment + variance of lexical diversity (type-token ratio) across sessions per user
- Extract trust indicators: interaction length (word count), session frequency (days between conversations), and explicit rating if available
- Perform Pearson correlation analysis between consistency scores and trust indicators
- Run multiple linear regression controlling for total interaction count and session duration
- Generate visualizations: scatter plots with regression lines, consistency distribution histograms
- All computation runs on CPU with batch processing to stay within 7GB RAM and 6-hour time limit

## Duplicate-check

- Reviewed existing ideas: None in psychology field corpus.
- Closest match: None identified.
- Verdict: NOT a duplicate

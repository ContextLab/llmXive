---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Linguistic Accommodation on Perceived Empathy in AI Assistants

**Field**: psychology

## Research question

Does linguistic accommodation in AI assistant responses influence users' perceptions of the AI's empathy and rapport?

## Motivation

Linguistic accommodation—the unconscious mirroring of speech patterns—has been shown to foster rapport in human-human interactions. However, it remains unclear whether this mechanism generalizes to human-AI interactions, where users may have different expectations of authenticity and emotional connection. Understanding this relationship could inform the design of emotionally intelligent AI systems for therapeutic, educational, and customer-support applications.

## Literature gap analysis

### What we searched

Searched Semantic Scholar/arXiv for terms including "linguistic accommodation AI," "speech accommodation chatbot," "perceived empathy AI assistant," and "human-AI rapport linguistic style." Results were sparse, with only one directly relevant paper identified.

### What is known

- [Psychological Factors Influencing University Students Trust in AI-Based Learning Assistants (2025)](http://arxiv.org/abs/2512.17390v1) — This work examines trust factors in AI learning assistants but does not specifically address linguistic accommodation or its relationship to perceived empathy.

### What is NOT known

No published work has directly measured linguistic accommodation metrics (e.g., lexical overlap, syntactic similarity) in human-AI conversations and correlated them with user ratings of perceived empathy. Existing studies focus on trust or technical performance rather than the specific mechanism of accommodation as a driver of rapport in AI contexts.

### Why this gap matters

This gap matters for developers of emotionally supportive AI systems (e.g., mental health chatbots, tutoring assistants) who need evidence-based guidance on whether stylistic mirroring enhances or undermines user trust. Clarifying this relationship could improve AI design for high-stakes emotional interactions.

### How this project addresses the gap

This project will quantify linguistic accommodation in public human-AI conversation datasets and statistically test its correlation with empathy ratings, providing the first empirical evidence on this specific mechanism in human-AI contexts.

## Expected results

We expect to observe a modest positive correlation between accommodation metrics and perceived empathy ratings, though the effect may be weaker than in human-human interactions due to user awareness of AI identity. A null result would suggest accommodation is less relevant for AI rapport, which would also be publishable as a boundary condition on accommodation theory.

## Methodology sketch

- Download DailyDialog and other public human-AI dialogue datasets (e.g., from HuggingFace Datasets repository)
- Preprocess transcripts to extract AI assistant responses and corresponding user turns
- Compute accommodation metrics: lexical overlap (Jaccard similarity), syntactic similarity (POS tag sequence overlap), and prosodic proxies (sentence length variance)
- Extract or infer user empathy/helpfulness ratings from dataset annotations or survey metadata where available
- Perform correlation analysis (Pearson/Spearman) between accommodation scores and empathy ratings
- Run regression models controlling for conversation length, topic, and user demographics
- Generate visualizations (scatter plots, effect size distributions) for interpretation
- Validate robustness via bootstrap resampling (1000 iterations)

## Duplicate-check

- Reviewed existing ideas: None in corpus (initial flesh-out).
- Closest match: N/A (first iteration).
- Verdict: NOT a duplicate

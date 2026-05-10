---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Linguistic Complexity on Trust in AI-Generated Text

**Field**: psychology

## Research question

Does linguistic complexity in AI-generated text (e.g., sentence structure, lexical diversity) predict readers' trust ratings when the source is explicitly identified as AI-generated?

## Motivation

As AI-generated text becomes ubiquitous, understanding which linguistic features drive or undermine trust is critical for ethical AI deployment. While prior work examines trust in AI explanations or visual AI content, few studies isolate linguistic complexity as a predictor of trust in text, even when users know the source is artificial.

## Literature gap analysis

### What we searched

Searched Semantic Scholar/arXiv/OpenAlex using queries: (1) "linguistic complexity trust AI text" and (2) "AI-generated text readability trust psychology". Retrieved 6 papers, mostly on AI images, explanations, or general linguistic characteristics.

### What is known

- [Linguistic Characteristics of AI-Generated Text: A Survey (2025)](http://arxiv.org/abs/2510.05136v1) — Documents linguistic patterns in LLM output but does not test trust outcomes.
- [Exploring Effectiveness of Explanations for Appropriate Trust: Lessons from Cognitive Psychology (2022)](http://arxiv.org/abs/2210.03737v1) — Establishes that AI explanations influence trust, but focuses on transparency rather than linguistic style.
- [Examining the Impact of Label Detail and Content Stakes on User Perceptions of AI-Generated Images on Social Media (2025)](http://arxiv.org/abs/2510.19024v1) — Shows labeling affects trust in AI images, suggesting disclosure matters, but does not address text complexity.

### What is NOT known

No published work has measured whether objective linguistic complexity metrics (readability scores, lexical density) correlate with trust ratings for AI-generated text when users are explicitly aware of the AI source. The interaction between cognitive fluency cues and source awareness remains untested.

### Why this gap matters

Filling this gap enables AI designers to optimize text style for appropriate trust calibration—avoiding both over-trust in overly fluent content and unnecessary skepticism of complex but accurate AI output. This has direct implications for education, healthcare communication, and news dissemination.

### How this project addresses the gap

The methodology generates AI text samples with controlled linguistic complexity, collects trust ratings from participants, and tests for correlation between complexity metrics and trust scores while controlling for source awareness.

## Expected results

We expect a non-linear relationship where moderate linguistic complexity maximizes trust, while both very low (overly simple) and very high (overly dense) complexity reduce trust. This would be confirmed by a significant quadratic regression term (complexity²) in predicting trust ratings.

## Methodology sketch

- Download public text corpora (e.g., Wikipedia articles, news datasets) from HuggingFace Datasets (https://huggingface.co/datasets/wikipedia)
- Generate AI text samples using open LLMs via local inference (e.g., Gemma-2B) with prompt variations controlling output length and style
- Compute linguistic complexity metrics using Python packages: Flesch-Kincaid readability, lexical diversity (MTLD), sentence length (NLTK)
- Recruit participants via Prolific or similar platform (target N=100) for trust rating task
- Present participants with AI-labeled text samples and collect 5-point Likert trust ratings
- Run linear regression with complexity metrics as predictors and trust as outcome
- Apply quadratic terms to test for non-linear (inverted-U) relationships
- Bootstrap confidence intervals (1000 resamples) to assess robustness

## Duplicate-check

- Reviewed existing ideas: None provided in input (no existing_idea_paths).
- Closest match: None identified.
- Verdict: NOT a duplicate

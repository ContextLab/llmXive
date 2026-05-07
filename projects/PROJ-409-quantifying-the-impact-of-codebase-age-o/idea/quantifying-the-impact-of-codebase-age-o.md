---
field: computer science
submitter: google.gemma-3-27b-it
---

# Quantifying the Impact of Codebase Age on LLM Code Understanding

**Field**: Computer Science

## Research question

How does the median commit age of a software repository correlate with the perplexity and function-completion accuracy of Large Language Models on code tasks?

## Motivation

Large Language Models (LLMs) are increasingly deployed to assist with legacy code maintenance, yet their performance on older, "technical debt"-rich codebases is poorly characterized. If LLM performance degrades significantly with codebase age, this creates a critical risk for automated refactoring and documentation tools targeting long-lived systems. This project addresses the gap between general code-generation benchmarks and the specific temporal dynamics of real-world software evolution.

## Literature gap analysis

### What we searched

We queried Semantic Scholar, arXiv, and OpenAlex using terms such as "LLM code quality temporal," "legacy code language model performance," and "software age code understanding." The search returned general papers on CodeLLMs but yielded no direct studies measuring the correlation between repository commit history age and model inference metrics.

### What is known

- [CodeBERT: A Pre-Trained Model for Programming and Natural Languages](https://arxiv.org/abs/2002.08155) — Establishes the baseline capability of transformer models on code representation and retrieval tasks.
- [Evaluating Large Language Models Trained on Code](https://arxiv.org/abs/2107.03374) — Demonstrates human-level performance on code completion but focuses on standardized benchmarks rather than temporal code properties.

### What is NOT known

There is no published work quantifying how the *temporal age* of code (e.g., median commit date) specifically impacts LLM perplexity or accuracy. Existing benchmarks (e.g., HumanEval, MBPP) use static, curated code snippets that do not reflect the evolution or aging process of production repositories.

### Why this gap matters

Software engineering teams rely on LLMs for refactoring legacy systems; if models systematically underperform on older code, this could lead to incorrect modifications in critical infrastructure. Understanding this gap is essential for setting realistic expectations for AI-assisted maintenance and for developing age-aware adaptation strategies.

### How this project addresses the gap

This project will explicitly calculate repository age metrics from git history and correlate them with model perplexity and completion accuracy on a subset of public repositories. By linking git metadata directly to inference outcomes, we produce the first empirical evidence of age-dependent performance degradation.

## Expected results

We expect to observe a moderate negative correlation between codebase age and LLM performance, where older codebases yield higher perplexity and lower completion accuracy. A null result (no correlation) would be equally significant, suggesting that modern LLMs generalize well across temporal code styles.

## Methodology sketch

- Download 5 open-source Python repositories from GitHub with varying median commit ages (e.g., 2015–2023).
- Extract 200 function-level code snippets per repository using a static parser to ensure consistent size.
- Compute "code age" for each snippet based on the median commit date of the containing file.
- Run a quantized small-scale CodeLLM (e.g., CodeGen-350M) on the CPU to calculate perplexity for each snippet.
- Measure completion accuracy by comparing model output against the original function body (token-level match).
- Perform Spearman rank correlation analysis between median snippet age and model perplexity/accuracy.
- Validate results with a secondary test using a different small model architecture (e.g., TinyLlama) to ensure robustness.
- Ensure all inference runs complete within 6 hours on a 2-core CPU by limiting total samples to 1,000.

## Duplicate-check

- Reviewed existing ideas: None found in local corpus.
- Closest match: None (general LLM code evaluation papers exist, but none focus on temporal age).
- Verdict: NOT a duplicate

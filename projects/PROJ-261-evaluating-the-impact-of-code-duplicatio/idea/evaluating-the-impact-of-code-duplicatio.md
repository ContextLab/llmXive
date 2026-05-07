---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Impact of Code Duplication on LLM Code Understanding

**Field**: Computer Science

## Research question

How does the local density of syntactic code clones correlate with the perplexity and bug-detection accuracy of pre-trained language models on open-source Python code?

## Motivation

Code duplication is a well-documented liability for human maintainability, yet its influence on Large Language Model (LLM) robustness remains unquantified. Since LLMs are trained on GitHub corpora rich in copy-pasted code, understanding whether this redundancy aids memorization or degrades generalization is critical for assessing training data quality. This gap matters for developers relying on AI tools to refactor or debug systems where duplication is prevalent.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv for terms including "code duplication LLM performance," "impact of code clones on language models," "redundancy in code training data," and "training data optimization for code generation." The search returned multiple studies on using LLMs *for* clone detection and general data quality optimization, but no studies specifically isolating code duplication density as a variable affecting model comprehension or prediction metrics.

### What is known

- [Rewriting Pre-Training Data Boosts LLM Performance in Math and Code (2025)](https://arxiv.org/abs/2505.02881) — Establishes that pre-training data quality fundamentally limits LLM performance in program synthesis, though it does not isolate duplication density.
- [On the Effectiveness of Training Data Optimization for LLM-based Code Generation: An Empirical Study (2025)](https://arxiv.org/abs/2512.24570) — Confirms that high-quality code datasets drive generation progress, but focuses on selection rather than structural redundancy metrics.
- [Code Clone Detection Techniques Based on Large Language Models (2025)](https://ieeexplore.ieee.org/document/10918947/) — Demonstrates LLMs are effective at *detecting* clones, establishing the problem's relevance but not its impact on model understanding.

### What is NOT known

There is no published work quantifying the relationship between structural clone density and downstream model metrics such as perplexity or bug detection error rates. It remains unclear whether LLMs treat duplicated code as a signal for pattern reinforcement or as noise that degrades generalization.

### Why this gap matters

If duplication systematically biases model predictions, refactoring strategies for "AI-readiness" may need to prioritize code uniqueness over human readability. Filling this gap would provide empirical evidence for whether reducing duplication improves the reliability of LLM-assisted software engineering tools.

### How this project addresses the gap

This project will compute clone density metrics on a public Python corpus and measure the resulting perplexity and task accuracy of a pre-trained model. By correlating these two independent measurements, we will produce the first evidence linking code redundancy directly to LLM understanding performance.

## Expected results

We expect to find a non-linear correlation where moderate duplication reduces perplexity (easier prediction) but high duplication increases bug detection errors (overfitting to patterns). Confirmation will require a statistically significant correlation coefficient (p < 0.05) across a stratified sample of code segments.

## Methodology sketch

- Download a subset of the `codeparrot/github-code` dataset from HuggingFace (Python files only, limited to 500MB to fit GHA RAM).
- Run a lightweight AST-based clone detector to assign a "duplication density" score to each code segment.
- Load `Salesforce/codegen-350M-mono` in 8-bit quantization for CPU inference to stay within 7GB RAM limits.
- Compute perplexity for each segment and run bug detection on a held-out subset using the `humaneval` evaluation suite.
- Calculate Spearman’s rank correlation between duplication density and model performance metrics.
- Visualize the relationship using scatter plots with regression lines generated via `matplotlib`.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: None identified.
- Verdict: NOT a duplicate

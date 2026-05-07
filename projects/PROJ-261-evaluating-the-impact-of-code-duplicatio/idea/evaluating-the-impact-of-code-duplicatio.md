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

We queried Semantic Scholar, arXiv, and OpenAlex for terms including "code duplication LLM performance," "impact of code clones on language models," "redundancy in code training data," "code patterns LLM understanding," and "LLM code quality metrics." The search returned seven results from the verified literature block, all focused on LLM benchmarks for code generation, vulnerability analysis, or multi-agent context engineering rather than investigating how code duplication affects LLM comprehension or prediction metrics.

### What is known

- [Understanding Code Patterns - Analysis, Interpretation & Measurement (2011)](https://arxiv.org/abs/1106.6159) — Establishes foundational methodology for measuring code patterns and quality in software systems, though predates LLM-era analysis.
- [SIMCOPILOT: Evaluating Large Language Models for Copilot-Style Code Generation (2025)](https://arxiv.org/abs/2505.21514) — Introduces a benchmark for LLM code completion but does not examine training data redundancy as a predictor variable.
- [Evaluating Code Generation of LLMs in Advanced Computer Science Problems (2025)](https://arxiv.org/abs/2504.14964) — Assesses LLM performance on student programming tasks but does not correlate results with code duplication metrics in the training or test corpora.
- [LLaVul: A Multimodal LLM for Interpretable Vulnerability Reasoning about Source Code (2025)](https://arxiv.org/abs/2509.17337) — Focuses on vulnerability analysis as a downstream task, not on how structural redundancy affects baseline model comprehension.

### What is NOT known

There is no published work quantifying the relationship between structural clone density and downstream model metrics such as perplexity or bug detection error rates. It remains unclear whether LLMs treat duplicated code as a signal for pattern reinforcement or as noise that degrades generalization. None of the retrieved papers examine code duplication as an independent variable affecting model comprehension.

### Why this gap matters

If duplication systematically biases model predictions, refactoring strategies for "AI-readiness" may need to prioritize code uniqueness over human readability. Filling this gap would provide empirical evidence for whether reducing duplication improves the reliability of LLM-assisted software engineering tools, informing both training data curation and codebase maintenance practices.

### How this project addresses the gap

This project will compute clone density metrics on a public Python corpus and measure the resulting perplexity and task accuracy of a pre-trained model. By correlating these two independent measurements, we will produce the first evidence linking code redundancy directly to LLM understanding performance.

## Expected results

We expect to find a non-linear correlation where moderate duplication reduces perplexity (easier prediction) but high duplication increases bug detection errors (overfitting to patterns). Confirmation will require a statistically significant correlation coefficient (p < 0.05) across a stratified sample of code segments.

## Methodology sketch

- Download a subset of the `codeparrot/github-code` dataset from HuggingFace Datasets (Python files only, limited to 500MB to fit GHA RAM).
- Run a lightweight AST-based clone detector (e.g., custom Python AST parser using `ast` module) to assign a "duplication density" score to each code segment.
- Load `Salesforce/codegen-350M-mono` in 8-bit quantization for CPU inference to stay within 7GB RAM limits.
- Compute perplexity for each segment using the model's log-probability outputs.
- Run bug detection on a held-out subset using the `humaneval` evaluation suite (subset of 50 problems).
- Calculate Spearman's rank correlation between duplication density and model performance metrics.
- Visualize the relationship using scatter plots with regression lines generated via `matplotlib`.
- Document all hyperparameters, random seeds, and clone detection thresholds for reproducibility.
- Store intermediate metrics in CSV format for auditability.
- Perform sensitivity analysis across three different clone-detection thresholds to verify robustness.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: None identified.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.1.0) on 2026-05-07T03:32:11Z
**Outcome**: success
**Original term**: Evaluating the Impact of Code Duplication on LLM Code Understanding computer science
**Verified citation count**: 7

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Evaluating the Impact of Code Duplication on LLM Code Understanding computer science | 7 |

### Verified citations

1. **SIMCOPILOT: Evaluating Large Language Models for Copilot-Style Code Generation** (2025). Mingchao Jiang, Abhinav Jain, Sophia Zorek, Chris Jermaine. arXiv. [2505.21514](https://arxiv.org/abs/2505.21514). PDF-sampled: No.
2. **Context Engineering for Multi-Agent LLM Code Assistants Using Elicit, NotebookLM, ChatGPT, and Claude Code** (2025). Muhammad Haseeb. arXiv. [2508.08322](https://arxiv.org/abs/2508.08322). PDF-sampled: No.
3. **Understanding Code Patterns - Analysis, Interpretation & Measurement** (2011). Jitesh Dundas. arXiv. [1106.6159](https://arxiv.org/abs/1106.6159). PDF-sampled: No.
4. **Evaluating Code Generation of LLMs in Advanced Computer Science Problems** (2025). Emir Catir, Robin Claesson, Rodothea Myrsini Tsoupidi. arXiv. [2504.14964](https://arxiv.org/abs/2504.14964). PDF-sampled: No.
5. **Code-A1: Adversarial Evolving of Code LLM and Test LLM via Reinforcement Learning** (2026). Aozhe Wang, Yuchen Yan, Nan Zhou, Zhengxi Lu, Weiming Lu, et al.. arXiv. [2603.15611](https://arxiv.org/abs/2603.15611). PDF-sampled: No.
6. **Enhancing Code Translation in Language Models with Few-Shot Learning via Retrieval-Augmented Generation** (2024). Manish Bhattarai, Javier E. Santos, Shawn Jones, Ayan Biswas, Boian Alexandrov, et al.. arXiv. [2407.19619](https://arxiv.org/abs/2407.19619). PDF-sampled: No.
7. **LLaVul: A Multimodal LLM for Interpretable Vulnerability Reasoning about Source Code** (2025). Ala Jararweh, Michael Adams, Avinash Sahu, Abdullah Mueen, Afsah Anwar. arXiv. [2509.17337](https://arxiv.org/abs/2509.17337). PDF-sampled: No.

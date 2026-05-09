---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Impact of Code Generation Models on Code Review Quality with LLM-Assisted Metrics

**Field**: computer science

## Research question

How do LLM-assisted code quality metrics differ between human-written and LLM-generated code samples, and what does this imply for the sensitivity of code review standards?

## Motivation

As LLMs increasingly generate production code, reviewers may lack the specific criteria to detect subtle artifacts unique to machine-generated patterns. Existing evaluation focuses on correctness (execution) rather than maintainability or review friction. Understanding these metric differences helps calibrate review processes to ensure code quality standards are maintained regardless of origin.

## Literature gap analysis

### What we searched

Searches were conducted on Semantic Scholar and arXiv using queries: "LLM code generation review quality", "automated code review metrics", and "human vs AI code complexity". Sources queried included Semantic Scholar and arXiv. The search returned 8 results, but few directly address the intersection of *code origin* and *review process metrics*.

### What is known

- [Gendered Prompting and LLM Code Review: How Gender Cues in the Prompt Shape Code Quality and Evaluation (2026)](http://arxiv.org/abs/2603.24359v1) — Establishes that LLMs are embedded in programming workflows including automated code review, though focus is on prompt cues rather than generation origin.
- [Execution-based Evaluation for Data Science Code Generation Models (2022)](http://arxiv.org/abs/2211.09374v1) — Demonstrates that execution-based metrics are standard for evaluating generation correctness, but do not capture review-specific friction.
- [ReCode: Robustness Evaluation of Code Generation Models (2022)](http://arxiv.org/abs/2212.10264v1) — Shows that code generation models can be brittle, suggesting potential variability in code quality that might affect review.
- [SIMCOPILOT: Evaluating Large Language Models for Copilot-Style Code Generation (2025)](http://arxiv.org/abs/2505.21514v1) — Provides benchmarks for interactive coding assistance, focusing on completion tasks rather than review outcomes.

### What is NOT known

No published work has directly compared LLM-assisted static analysis metrics (e.g., complexity, potential bugs) across matched human and LLM-generated code samples to predict review effort. Existing literature focuses on whether code *runs*, not whether it is *reviewed differently*.

### Why this gap matters

If LLM-generated code passes execution tests but exhibits distinct structural artifacts, reviewers may miss maintainability issues. Filling this gap enables the creation of review checklists specifically tuned for AI-assisted development, preventing technical debt accumulation.

### How this project addresses the gap

The methodology applies lightweight LLM-based analysis to both human and LLM code datasets, quantifying metric distributions and statistically testing for differences that would correlate with review effort. This produces the first comparative profile of "review-readiness" between the two code origins.

## Expected results

We expect LLM-generated code to show lower execution failure rates but higher complexity or style inconsistency scores compared to human code. A statistically significant difference in these LLM-assisted metrics would confirm that current review standards may need adjustment for AI-generated artifacts.

## Methodology sketch

- Download human-written code dataset (e.g., `CodeSearchNet` via HuggingFace Datasets).
- Download LLM-generated code dataset (e.g., `HumanEval` or `MBPP` via HuggingFace Datasets).
- Filter datasets to ensure comparable function sizes and languages (e.g., Python only).
- Run a lightweight quantized local LLM (e.g., `TinyLlama-1.1B` or similar CPU-optimized model) on each code snippet to extract complexity and potential bug scores.
- Aggregate scores per dataset to form metric distributions.
- Apply Mann-Whitney U test to compare metric distributions between human and LLM groups.
- Visualize differences using boxplots to highlight where review friction might arise.
- Map metric deviations to specific review guideline recommendations.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: N/A.
- Verdict: NOT a duplicate.

---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Impact of Code Generation on Code Review Quality with LLM Assistance

**Field**: computer science

## Research question

How does LLM-assisted code review affect the detection rate and severity classification of bugs in LLM-generated code compared to human-only review?

## Motivation

LLM-generated code is increasingly integrated into software development workflows, but downstream quality assurance practices remain uncertain. This research addresses the gap in understanding whether LLM assistance in code review improves bug detection or introduces systematic blind spots that could compromise software reliability.

## Literature gap analysis

### What we searched

Searched Semantic Scholar and arXiv for queries: (1) "LLM code review quality bug detection" and (2) "automated code review large language model evaluation". Queried sources included Semantic Scholar API and arXiv.org. Retrieved 7 results total.

### What is known

- [Gendered Prompting and LLM Code Review: How Gender Cues in the Prompt Shape Code Quality and Evaluation (2026)](http://arxiv.org/abs/2603.24359v1) — Establishes that prompt characteristics influence LLM-assisted code review outcomes, suggesting review quality is sensitive to input framing.
- [SIMCOPILOT: Evaluating Large Language Models for Copilot-Style Code Generation (2025)](http://arxiv.org/abs/2505.21514v1) — Provides a benchmark framework for evaluating LLM code generation performance, though not focused on downstream review processes.
- [Evaluating Code Generation of LLMs in Advanced Computer Science Problems (2025)](http://arxiv.org/abs/2504.14964v1) — Documents LLM usage patterns in programming education and code generation evaluation, but does not examine code review quality.

### What is NOT known

No published work has measured the bug detection rate difference between LLM-assisted and human-only code review on the same codebase. There is also no systematic analysis of whether LLMs systematically miss certain severity classes of bugs (e.g., security vulnerabilities vs. style issues) in generated code.

### Why this gap matters

Software engineering teams adopting LLM tools need evidence on whether LLM-assisted review improves or degrades quality assurance. Filling this gap would enable informed decisions about integrating LLMs into CI/CD pipelines and establish benchmarks for automated review tool effectiveness.

### How this project addresses the gap

This project will extract paired code review data from public GitHub repositories, apply standardized LLM review prompts to identify bugs, and compare detection rates and severity classifications against human review annotations. The methodology directly produces the missing comparative evidence on review quality outcomes.

## Expected results

We expect to observe either (1) LLM-assisted review detects more bugs overall but with different severity distribution, or (2) LLM assistance provides no significant improvement over human-only review. Either outcome is publishable as it informs practical adoption decisions and reveals whether LLM review adds complementary value or redundancy.

## Methodology sketch

- **Data source**: GitHub API to extract pull requests with code review comments and linked bug reports from 3-5 active open-source projects (e.g., `microsoft/vscode`, `pytorch/pytorch`, `tensorflow/tensorflow`). Target: 200-500 reviewed PRs with bug labels.
- **Code extraction**: Use `gh` CLI or GitHub REST API to download PR diffs, review comments, and issue tracker data (bugs/closed issues linked to PRs).
- **LLM review simulation**: Run open-source LLM (e.g., CodeLlama-7B or StarCoder2-3B via HuggingFace) on each PR diff to generate bug reports; use standardized prompt with explicit severity categories (critical, major, minor, style).
- **Human review baseline**: Extract existing human review comments and bug labels from GitHub issues; annotate each bug with severity using a standardized rubric.
- **Alignment**: Match LLM-detected bugs to human-annotated bugs using code location (file + line range) and bug description similarity (cosine similarity on embedding).
- **Statistical analysis**: Compute precision, recall, and F1-score for bug detection; use McNemar's test to compare detection rates between LLM and human review; chi-square test for severity distribution differences.
- **Resource constraints**: Process PRs in batches of 50 to stay within 7GB RAM; limit LLM inference to 300ms per PR using quantized model; total runtime target: 4-5 hours on GHA 2-CPU runner.

## Duplicate-check

- Reviewed existing ideas: None provided in input corpus.
- Closest match: N/A (no corpus available for comparison).
- Verdict: NOT a duplicate

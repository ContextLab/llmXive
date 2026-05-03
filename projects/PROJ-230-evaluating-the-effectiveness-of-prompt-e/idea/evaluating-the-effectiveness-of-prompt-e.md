---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Effectiveness of Prompt Engineering for LLM-Based Code Translation

**Field**: computer science

## Research question

How do different prompt engineering strategies (instruction detail, few-shot examples, code style specifications) affect the functional correctness and code quality of LLM-based code translation from Python to JavaScript?

## Motivation

Code translation is a critical task for software maintenance and interoperability, yet LLM performance varies dramatically with prompt design. This study addresses the gap between theoretical LLM capabilities and practical deployment by identifying which prompt patterns consistently produce functionally correct translations, reducing migration risks for developers.

## Related work

- [Enhancing Code Translation in Language Models with Few-Shot Learning via Retrieval-Augmented Generation (2024)](http://arxiv.org/abs/2407.19619v1) — Directly addresses code translation improvements through few-shot prompting and RAG techniques.
- [TDD Governance for Multi-Agent Code Generation via Prompt Engineering (2026)](http://arxiv.org/abs/2604.26615v1) — Examines prompt engineering's role in ensuring code generation discipline and test-driven workflows.
- [A survey on large language model based autonomous agents (2024)](https://doi.org/10.1007/s11704-024-40231-1) — Provides context on LLM agent reliability and prompt sensitivity in software tasks.

## Expected results

We expect few-shot prompts with style specifications to achieve significantly higher functional correctness rates (p < 0.05 via chi-square test) compared to zero-shot baselines. We will measure translation success by unit test pass rates across 200+ code snippets, with evidence requiring 95% confidence intervals on correctness metrics.

## Methodology sketch

- **Dataset acquisition**: Download Python-to-JavaScript translation pairs from HuggingFace CodeTrans dataset (https://huggingface.co/datasets/codeparrot/code-trans-py-js) and BigCode evaluation suite (https://huggingface.co/datasets/bigcode/evaluation); target N ≥ 200 pairs.
- **Prompt design**: Create 4 prompt conditions: (1) zero-shot basic, (2) zero-shot with style specs, (3) few-shot (3 examples), (4) few-shot + style specs.
- **LLM selection**: Use accessible models via API (e.g., CodeLlama-7B via HuggingFace Inference API) to stay within GHA resource limits; no local fine-tuning.
- **Translation execution**: Run each prompt condition on all code snippets; store outputs with deterministic seeds.
- **Functional correctness**: Execute translated JavaScript against original Python unit tests (adapted via pytest-js bridge); record pass/fail per snippet.
- **Code quality metrics**: Compute cyclomatic complexity (using radon library for Python, eslint complexity for JS) and lines of code per translation.
- **Statistical analysis**: Apply chi-square tests for correctness rate differences; ANOVA for quality metric comparisons across prompt conditions.
- **Reproducibility**: Log all prompts, model versions, and test results in a version-controlled CSV; generate summary figures via matplotlib.

## Duplicate-check

- Reviewed existing ideas: None provided (existing_idea_paths empty).
- Closest match: N/A — no prior fleshed-out ideas in corpus.
- Verdict: NOT a duplicate

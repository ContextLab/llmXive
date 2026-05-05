---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Impact of LLM-Generated Code on Code Coverage

**Field**: computer science

## Research question

How does code coverage differ between LLM-generated code and human-written code for equivalent programming tasks, and which code structures or problem types exhibit the largest coverage gaps?

## Motivation

As LLMs become mainstream in software development, understanding their impact on software quality metrics is critical. Code coverage is a foundational testability metric, yet no systematic study has quantified whether LLM-generated code achieves comparable coverage to human-written solutions. This research addresses that gap to inform best practices for AI-assisted development pipelines.

## Related work

- [HumanEval: Benchmarking LLMs on Code Generation](https://huggingface.co/datasets/openai/human-eval) — Foundational benchmark for LLM code generation performance on Python functions.
- [MBPP: Mostly Basic Python Programming](https://github.com/google-research/google-research/tree/master/mbpp) — Dataset of 974 Python programming tasks with test cases for evaluating code generation.
- [CodeSearchNet: Code and Text Retrieval](https://github.com/github/CodeSearchNet) — Large-scale corpus for studying code understanding and retrieval with coverage annotations.
- [APPS: Benchmark for Programming Problems](https://github.com/hendrycks/apps) — Collection of competitive programming problems for evaluating code generation at scale.
- [Pytest-Cov Documentation](https://pytest-cov.readthedocs.io/) — Standard Python coverage tool for measuring line, branch, and statement coverage.

## Expected results

We expect LLM-generated code to achieve 10-25% lower branch coverage than human-written baselines on average, with larger gaps on edge-case-heavy problems. Coverage will be measurable via pytest-cov with statistical significance (p<0.05) across ≥100 problems. Results will identify specific problem categories (e.g., boundary conditions, error handling) where LLMs systematically underperform.

## Methodology sketch

- **Data acquisition**: Download MBPP dataset (974 Python tasks) from GitHub via `wget`; download HumanEval test suite from HuggingFace Datasets.
- **Code generation**: Query OpenAI API (GPT-4) or use open-source alternative (CodeLlama-7B via HuggingFace) to generate one solution per task; store outputs in structured JSON.
- **Test suite preparation**: Use existing test cases from MBPP/HumanEval; augment with additional boundary-case tests where available.
- **Coverage instrumentation**: Install pytest-cov; run each generated solution against its test suite with `pytest --cov` to collect line/branch coverage metrics.
- **Human baseline collection**: Sample 200 problems with known human solutions from APACS or CodeSearchNet for comparison.
- **Statistical analysis**: Compute mean coverage difference between LLM and human code; apply paired t-test (α=0.05) for significance; calculate effect size (Cohen's d).
- **Stratified analysis**: Group results by problem difficulty (easy/medium/hard) and code pattern (loops, conditionals, recursion) to identify underperformance patterns.
- **Visualization**: Generate bar charts and box plots comparing coverage distributions using matplotlib/seaborn.
- **Reproducibility**: Save all generated code, coverage reports, and analysis scripts to a version-controlled repository for audit.

## Duplicate-check

- Reviewed existing ideas: None available (no existing_idea_paths provided).
- Closest match: N/A
- Verdict: NOT a duplicate

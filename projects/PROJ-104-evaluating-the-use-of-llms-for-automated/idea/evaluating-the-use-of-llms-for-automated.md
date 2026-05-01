---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Use of LLMs for Automated Documentation Generation from Code Commits

**Field**: computer science

## Research question

Can large language models generate accurate, complete, and clear documentation updates directly from code commit messages, and how does their performance compare to human-written documentation baselines?

## Motivation

Keeping software documentation synchronized with code changes is a persistent challenge in software engineering, often leading to outdated or missing documentation that reduces maintainability. This research addresses the gap in evaluating LLMs specifically for commit-to-documentation translation, a task distinct from general code generation or summarization. Demonstrating feasibility could reduce developer overhead and improve long-term project sustainability.

## Related work

- [The Programmer's Assistant: Conversational Interaction with a Large Language Model for Software Development](https://doi.org/10.1145/3581641.3584037) — Demonstrates LLMs can assist developers in software tasks including documentation, providing a foundation for commit-to-doc generation.
- [Integrating Code Metrics into Automated Documentation Generation for Computational Notebooks](http://arxiv.org/abs/2602.08133v1) — Addresses automated documentation generation for code artifacts, though focused on notebooks rather than commit-based updates.
- [Evaluating Code Generation of LLMs in Advanced Computer Science Problems](http://arxiv.org/abs/2504.14964v1) — Provides evaluation methodology for LLM code-related tasks that can be adapted for documentation quality assessment.
- ["Which LLM should I use?": Evaluating LLMs for tasks performed by Undergraduate Computer Science Students](http://arxiv.org/abs/2402.01687v2) — Offers comparative framework for evaluating multiple LLMs on software development tasks.

## Expected results

We expect LLM-generated documentation to achieve moderate-to-high semantic similarity with human-written baselines on accuracy and completeness metrics, with clarity scores varying by model. A paired t-test comparing LLM vs. baseline documentation quality scores should reveal whether differences are statistically significant (p<0.05). We anticipate that smaller models will underperform compared to larger models but may still be viable for lightweight documentation tasks.

## Methodology sketch

- Download commit-message and documentation pairs from 10 popular open-source repositories on GitHub (e.g., from GitHub Archive or direct `git clone` of repos like pandas, scikit-learn, requests) using `wget` or `curl` with explicit commit hashes.
- Extract commit messages and corresponding documentation changes using GitHub's API or `git log --format=%B` combined with `git diff` to identify documentation file modifications.
- Select 3 open-source LLMs available on HuggingFace Datasets (e.g., `google/gemma-2b`, `microsoft/phi-2`, `meta-llama/Llama-2-7b-hf`) that can run within 7GB RAM constraints.
- Prompt each LLM with 200 randomly sampled commit messages using a standardized template (commit message → expected doc update format).
- Generate documentation outputs for each commit-message pair across all 3 models.
- Score generated documentation using 3 criteria: accuracy (matches commit intent), completeness (covers all changes), clarity (readability score via `pyssim` or similar).
- Collect human-written documentation from the same commits as ground truth baseline for comparison.
- Apply paired t-test to compare LLM-generated scores vs. human baseline scores for each quality criterion.
- Visualize results with bar charts (model comparison) and box plots (score distributions) using matplotlib.
- Compute statistical significance (p-value) and effect size (Cohen's d) for all pairwise comparisons.

## Duplicate-check

- Reviewed existing ideas: N/A (no existing fleshed-out ideas provided in input).
- Closest match: N/A (no corpus provided for comparison).
- Verdict: NOT a duplicate

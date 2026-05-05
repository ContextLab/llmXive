---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Impact of Code Generation on Code Review Quality Using LLMs

**Field**: computer science

## Research question

Does the use of LLM-generated code significantly alter code review metrics (comment density, resolution time, defect density) compared to human-written code in public repositories?

## Motivation

Large language models are increasingly integrated into software development workflows, yet their downstream impact on quality assurance processes remains under-explored. Understanding whether LLM code accelerates or burdens the review process is critical for adapting team workflows and maintaining software quality standards.

## Related work

- [Evaluating Code Generation of LLMs in Advanced Computer Science Problems (2025)](http://arxiv.org/abs/2504.14964v1) — Establishes baseline performance metrics for LLMs in generating code for advanced problems.
- [SIMCOPILOT: Evaluating Large Language Models for Copilot-Style Code Generation (2025)](http://arxiv.org/abs/2505.21514v1) — Introduces a benchmark for interactive, copilot-style coding assistants relevant to workflow integration.
- [EVOR: Evolving Retrieval for Code Generation (2024)](http://arxiv.org/abs/2402.12317v2) — Discusses retrieval-augmented generation pipelines which may influence the quality of generated code snippets.
- [Large Language Models in Computer Science Education: A Systematic Literature Review (2024)](http://arxiv.org/abs/2410.16349v1) — Provides context on LLM adoption rates and educational impacts in computer science domains.

## Expected results

We expect to observe a statistically significant difference in review comment density, with LLM-generated code initially attracting more comments due to unfamiliar patterns. However, we anticipate that resolution time may decrease over time as reviewers adapt to LLM-specific code styles, provided the underlying logic remains sound.

## Methodology sketch

- **Data Acquisition**: Download pull request metadata and code diffs from a public GitHub repository using the GitHub API endpoint `https://api.github.com/repos/psf/requests/pulls` (limit to last 200 PRs to fit within GHA storage limits).
- **Data Filtering**: Parse JSON responses to separate PRs containing LLM-generated content (identified by specific commit message patterns or bot signatures) from human-authored PRs.
- **Feature Extraction**: Calculate review metrics per PR including comment count, time-to-merge, and number of review cycles using Python `pandas`.
- **Quality Proxy**: Use a pre-trained code quality model (e.g., `bert-base` via HuggingFace `transformers` library on CPU) to score code complexity and similarity to known bug patterns.
- **Statistical Analysis**: Perform independent two-sample t-tests to compare review metrics between the LLM and human groups using `scipy.stats`.
- **Visualization**: Generate boxplots and histograms of review metrics using `matplotlib` to visualize distribution differences.
- **Resource Management**: Process data in batches of 50 PRs to ensure memory usage stays under 7 GB RAM on the GitHub Actions runner.
- **Execution Environment**: Run the analysis pipeline within a single 6-hour GitHub Actions job using a Python 3.9 environment.
- **Reproducibility**: Save all intermediate CSV artifacts and statistical outputs as job artifacts for verification.
- **Validation**: Cross-check a random 10% sample of LLM classifications manually to ensure labeling accuracy.

## Duplicate-check

- Reviewed existing ideas: None in current context.
- Closest match: N/A (similarity sketch: N/A).
- Verdict: NOT a duplicate

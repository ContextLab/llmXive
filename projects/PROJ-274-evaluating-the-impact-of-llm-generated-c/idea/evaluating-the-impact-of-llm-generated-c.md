---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Impact of LLM-Generated Code Documentation on Developer Onboarding

**Field**: computer science

## Research question

How does LLM-generated code documentation compare to human-written documentation (or no documentation) in reducing onboarding time and effort for new developers working on open-source codebases?

## Motivation

As LLMs become ubiquitous in software development workflows, understanding their practical impact on team productivity is critical. While LLM-generated documentation promises efficiency gains, there is limited empirical evidence on whether it actually improves developer onboarding outcomes compared to traditional documentation practices.

## Related work

- [Using an LLM to Help With Code Understanding (2024)](https://doi.org/10.1145/3597503.3639187) — Demonstrates that LLMs can assist with code comprehension, though focused on individual understanding rather than team onboarding workflows.
- [Large Language Models in Computer Science Education: A Systematic Literature Review (2024)](http://arxiv.org/abs/2410.16349v1) — Reviews LLM applications in CS education, providing context for how LLMs affect learner comprehension in technical domains.
- [Evaluating Code Generation of LLMs in Advanced Computer Science Problems (2025)](http://arxiv.org/abs/2504.14964v1) — Examines LLM performance on programming tasks, relevant for benchmarking code understanding capabilities.
- [AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation (2023)](https://doi.org/10.48550/arxiv.2308.08155) — Provides framework context for LLM-based developer tools, though not directly focused on documentation quality.

## Expected results

We expect LLM-generated documentation to reduce initial code comprehension time by 15-30% compared to no documentation, but potentially show no significant difference or slight degradation compared to high-quality human documentation. Effectiveness will be measured via task completion time, question frequency, and subjective helpfulness ratings, with statistical significance determined at p<0.05.

## Methodology sketch

- Select 3-5 small-to-medium open-source projects (100-500 files) from GitHub with existing human documentation
- Generate documentation for each project using a state-of-the-art LLM (e.g., via HuggingFace API or local Gemma model)
- Recruit 15-20 volunteer CS students for a controlled onboarding study (IRB approval required)
- Randomly assign participants to one of three conditions: LLM docs, human docs, or no docs
- Measure time to complete standardized onboarding tasks (e.g., fix a bug, add a feature, explain architecture)
- Track number of clarification questions asked during the onboarding session
- Collect subjective ratings of documentation helpfulness via Likert-scale survey
- Perform ANOVA to compare means across conditions, with post-hoc Tukey tests for pairwise comparisons
- All data collection and analysis will use lightweight Python/R scripts runnable within 6 hours on standard CPU

## Duplicate-check

- Reviewed existing ideas: N/A (first fleshed-out idea in this pipeline)
- Closest match: None identified
- Verdict: NOT a duplicate

---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load

**Field**: computer science

## Research question

How does the use of LLM-based code completion tools affect developer cognitive load in professional software development workflows, as measured by code review complexity and iteration patterns?

## Motivation

While LLM-powered code completion tools promise to increase developer productivity, their impact on cognitive load remains unclear. Understanding whether these tools reduce or increase mental effort is critical for both tool design and adoption decisions, especially given evidence that over-reliance may introduce hidden costs in code quality and developer learning.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using the following search strings: (1) "LLM code completion cognitive load" (2) "AI code generators developer productivity" (3) "code review complexity LLM assistance". The search returned 4 results, of which only 2 are defensibly on-topic for measuring cognitive load in professional development contexts.

### What is known

- [Using an LLM to Help With Code Understanding (2024)](https://doi.org/10.1145/3597503.3639187) — Establishes that code understanding is challenging in complex development environments and LLMs can assist with code comprehension, though it does not quantify cognitive load metrics.
- [Studying the effect of AI Code Generators on Supporting Novice Learners in Introductory Programming (2023)](https://doi.org/10.1145/3544548.3580919) — Demonstrates that AI code generators can impact learning outcomes for novice programmers, with potential negative effects from over-reliance, but focuses on educational settings rather than professional workflows.

### What is NOT known

No published work has measured cognitive load proxies (such as code review comment length, merge iteration counts, or revert frequency) in professional software development contexts where LLM code completion is actively used. Existing studies either focus on code understanding tasks in isolation or on novice learners rather than experienced developers in production environments.

### Why this gap matters

Software engineering teams adopting LLM tools need empirical evidence about whether these tools reduce or increase hidden cognitive costs. Filling this gap would enable evidence-based decisions about tool integration, training requirements, and code review process adjustments to maintain code quality while leveraging AI assistance.

### How this project addresses the gap

This project will analyze public GitHub pull request metadata from projects with documented LLM integration to compute correlation between code completion tool usage and established cognitive load proxies (review comment length, iteration cycles, revert frequency). The methodology directly measures the previously-unavailable evidence on professional workflow impacts.

## Expected results

We expect to observe either (1) a negative correlation between LLM code completion usage and cognitive load proxies, indicating reduced mental effort, or (2) a positive correlation, indicating increased evaluation burden. Either outcome would be informative: the former validates tool adoption, while the latter suggests a need for improved tool design or developer training. Statistical significance will be assessed using regression models with project-level controls.

## Methodology sketch

- Download GitHub Pull Request metadata from selected repositories (using GitHub API with public rate limits, targeting ~50 projects with documented LLM tool usage)
- Extract code review metrics: comment length (characters), iteration count (PR update cycles), and revert frequency from pull request history
- Identify LLM tool usage via repository configuration files (e.g., `.cursorrules`, `copilot` configuration, or explicit mentions in project documentation)
- Compute per-project LLM adoption score as a binary indicator (tool present vs. absent)
- Apply linear regression with project size (lines of code), team size (contributor count), and domain complexity as control variables
- Test the null hypothesis that LLM usage has no effect on cognitive load proxies using t-tests on regression coefficients
- Generate summary statistics and visualization of effect sizes with 95% confidence intervals
- Validate results through sensitivity analysis on different project subsets (e.g., by programming language, repository age)

## Duplicate-check

- Reviewed existing ideas: [none provided in input].
- Closest match: N/A (no existing fleshed-out ideas provided for comparison).
- Verdict: NOT a duplicate

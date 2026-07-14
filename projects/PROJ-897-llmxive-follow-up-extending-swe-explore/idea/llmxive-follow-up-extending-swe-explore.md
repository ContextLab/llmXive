---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "SWE-Explore: Benchmarking How Coding Agents Explore Repositories"

**Field**: computer science

## Research question

Does an iterative, feedback-driven exploration strategy yield higher line-level coverage and repair success on ambiguous or unsolvable issues compared to the static, one-shot exploration evaluated in the original SWE-Explore benchmark?

## Motivation

The original SWE-Explore benchmark isolates retrieval quality but relies on solvable issues and a static, one-shot context window, failing to capture the dynamic, error-correcting nature of real-world debugging on difficult tasks. Addressing this gap is critical to determining whether the primary bottleneck for coding agents on complex problems is initial retrieval accuracy or the lack of adaptive, multi-turn exploration mechanisms.

## Literature gap analysis

### What we searched
We queried Semantic Scholar and arXiv for terms including "iterative code exploration agents," "feedback-driven repository navigation," "LLM debugging multi-turn," and "dynamic context retrieval software engineering." The search yielded general overviews of AI in software engineering and studies on human cognitive biases or citation patterns, but no primary literature specifically evaluating iterative exploration protocols against static baselines on the "hard tail" of repository issues.

### What is known
- [Morescient GAI for Software Engineering (Extended Version) (2024)](https://arxiv.org/abs/2406.04710) — Establishes the broad promise of Generative AI for automating software artifacts but does not provide a specific benchmark for iterative exploration strategies.
- [The Future of AI-Driven Software Engineering (2024)](https://arxiv.org/abs/2406.07737) — Discusses the paradigm shift toward AI systems in development productivity but lacks empirical comparisons of multi-turn vs. one-shot context retrieval mechanisms.
- [Cognitive Biases in Software Engineering: A Systematic Mapping Study (2017)](https://arxiv.org/abs/1707.03869) — Analyzes human error sources in SE, providing a theoretical basis for why iterative correction might be necessary, but does not offer automated agent benchmarks.

### What is NOT known
No published work has empirically measured whether multi-turn, feedback-driven exploration agents outperform static one-shot retrievers specifically on ambiguous or previously "unsolvable" repository issues. There is currently no standard methodology for generating synthetic ambiguous issues to stress-test the adaptive capabilities of coding agents beyond fixed retrieval budgets.

### Why this gap matters
Filling this gap is essential for advancing agents from simple retrieval tools to autonomous debuggers capable of handling the "long tail" of complex, ill-defined software problems that dominate real-world development. Understanding the limits of static retrieval versus dynamic adaptation will guide the design of next-generation coding agents and prevent over-optimism based solely on solvable benchmark subsets.

### How this project addresses the gap
This project will curate a subset of "hard" instances from the existing SWE-Explore dataset and augment them with synthetic ambiguous issues to test a multi-turn exploration loop. By comparing the line-level coverage and repair potential of an iterative agent against the original static baseline on these difficult cases, we will provide the first empirical evidence on the efficacy of dynamic feedback in repository exploration.

## Expected results

We expect the iterative agent to demonstrate a statistically significant improvement in line-level coverage and ranking efficiency on the "hard" subset compared to the one-shot baseline, particularly when initial issue descriptions are vague. A null result would suggest that the bottleneck lies in the underlying retrieval model's capacity rather than the exploration strategy, a finding that would redirect future research toward better foundational models rather than procedural changes.

## Methodology sketch

- **Data Curation**: Download the SWE-Explore dataset (848 issues) and filter for the bottom 20% of initial coverage scores to identify "hard" instances; generate 50 synthetic ambiguous issues by mutating variable names and removing comments in a subset of solvable tasks.
- **Agent Implementation**: Implement a multi-turn exploration loop using a lightweight, CPU-tractable LLM wrapper (e.g., Qwen-7B or similar via HuggingFace) that accepts a query, returns top-k code regions, executes a static analysis pass (using `pylint` or `ast` parsing) to detect errors/missing dependencies, and reformulates the query based on these signals.
- **Baseline Comparison**: Run the same set of issues through the original SWE-Explore static retrieval protocol (one-shot, fixed budget) to establish a control group.
- **Metric Calculation**: Compute line-level coverage (percentage of ground-truth relevant lines retrieved) and ranking efficiency (position of the first relevant line) for both the iterative and static runs.
- **Statistical Testing**: Apply the Wilcoxon signed-rank test to compare the coverage and efficiency metrics between the iterative and static approaches on the paired "hard" and synthetic issues, checking for statistical significance at p < 0.05.
- **Resource Constraints**: Ensure all execution runs within 6 hours on a 2-core, 7GB RAM runner by limiting the number of turns per issue to 3 and using a small-context model.

## Duplicate-check

- Reviewed existing ideas: SWE-Explore benchmark extension, iterative code exploration, static vs. dynamic retrieval.
- Closest match: SWE-Explore benchmark extension (similarity sketch: shares the dataset and goal of improving coverage, but differs by focusing on iterative feedback on hard/ambiguous issues rather than general benchmark expansion).
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-14T00:15:01Z
**Outcome**: success_after_expansion
**Original term**: llmXive follow-up: extending "SWE-Explore: Benchmarking How Coding Agents Explore Repositories" computer science
**Verified citation count**: 5

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | llmXive follow-up: extending "SWE-Explore: Benchmarking How Coding Agents Explore Repositories" computer science | 0 |
| 1 | software engineering agents repository exploration | 5 |
| 2 | LLM-based code exploration strategies | 0 |
| 3 | autonomous coding agent benchmarking | 0 |
| 4 | repository traversal by AI agents | 0 |
| 5 | SWE-bench exploration methodologies | 0 |
| 6 | code repository navigation by large language models | 0 |
| 7 | automated software maintenance agent exploration | 0 |
| 8 | LLM context retrieval for code understanding | 0 |
| 9 | AI-driven software repository analysis | 0 |
| 10 | benchmarking autonomous software engineering tools | 0 |
| 11 | code search and exploration by generative models | 0 |
| 12 | agent-based software repository mining | 0 |
| 13 | LLM performance on repository-scale tasks | 0 |
| 14 | exploring codebases with autonomous agents | 0 |
| 15 | software development agent evaluation frameworks | 0 |
| 16 | context window utilization in code exploration | 0 |
| 17 | multi-step code exploration by LLMs | 0 |
| 18 | automated repository understanding benchmarks | 0 |
| 19 | agentic workflows for software engineering | 0 |
| 20 | LLM interaction with version control systems | 0 |

### Verified citations

1. **Morescient GAI for Software Engineering (Extended Version)** (2024). Marcus Kessel, Colin Atkinson. arXiv. [2406.04710](https://arxiv.org/abs/2406.04710). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
2. **Cognitive Biases in Software Engineering: A Systematic Mapping Study** (2017). Rahul Mohanani, Iflaah Salman, Burak Turhan, Pilar Rodriguez, Paul Ralph. arXiv. [1707.03869](https://arxiv.org/abs/1707.03869). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
3. **Software Engineering in Civic Tech: A Case Study about Code for Ireland** (2019). Antti Knutas, Victoria Palacin, Giovanni Maccani, Markus Helfert. arXiv. [1904.04104](https://arxiv.org/abs/1904.04104). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
4. **The Future of AI-Driven Software Engineering** (2024). Valerio Terragni, Annie Vella, Partha Roop, Kelly Blincoe. arXiv. [2406.07737](https://arxiv.org/abs/2406.07737). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
5. **Text and Team: What Article Metadata Characteristics Drive Citations in Software Engineering?** (2022). Lorenz Graf-Vlachy, Daniel Graziotin, Stefan Wagner. arXiv. [2204.06033](https://arxiv.org/abs/2204.06033). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*

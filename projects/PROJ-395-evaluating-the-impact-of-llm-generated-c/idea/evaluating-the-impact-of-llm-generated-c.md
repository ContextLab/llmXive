---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Impact of LLM-Generated Code on Memory Usage

**Field**: computer science

## Research question

Do LLM-generated code solutions for algorithmic tasks exhibit systematically different memory consumption patterns compared to human-written equivalents, and do specific code characteristics (e.g., variable naming patterns, control flow complexity, library usage) correlate with these differences?

## Motivation

Resource-constrained deployment environments (edge devices, serverless functions, embedded systems) require predictable memory footprints. If LLM-generated code systematically consumes more or less memory than human-written code, this has practical implications for deployment decisions, cost estimation, and sustainability metrics. Understanding whether the gap exists and what code features drive it would enable better LLM prompting strategies and resource-aware code generation pipelines.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using three distinct search strings: (1) "LLM generated code memory usage" (2) "code generation efficiency memory consumption" and (3) "large language models runtime resource footprint." The queries returned approximately 15-20 total results across both sources, with most papers focusing on LLM performance in educational contexts, correctness benchmarks, or code quality metrics rather than runtime resource consumption.

### What is known

- [Evaluating Code Generation of LLMs in Advanced Computer Science Problems (2025)](http://arxiv.org/abs/2504.14964v1) — Establishes that LLMs are widely used by students for code generation in CS education, documenting adoption patterns but not runtime resource metrics.
- [Large Language Models in Computer Science Education: A Systematic Literature Review (2024)](http://arxiv.org/abs/2410.16349v1) — Reviews LLM applications in CS education broadly, covering correctness and pedagogical outcomes but omitting memory or computational efficiency analysis.

### What is NOT known

No published work has measured the memory footprint of LLM-generated code solutions compared to human-written baselines on standardized algorithmic benchmarks. Existing evaluations focus exclusively on functional correctness, code style, or pass rates, leaving runtime resource consumption as an unexplored dimension of code quality.

### Why this gap matters

Software deployment in resource-constrained environments (IoT devices, serverless functions, mobile applications) requires predictable memory budgets. Without evidence on whether LLM-generated code meets these constraints, organizations risk deploying code that exceeds memory limits at runtime, causing failures or inflated cloud costs. Filling this gap would enable evidence-based decisions about when LLM-generated code is suitable for production use.

### How this project addresses the gap

This project will measure peak and steady-state memory consumption of LLM-generated versus human-written code solutions on standardized algorithmic tasks. By profiling execution on identical inputs and hardware, we will produce the first comparative dataset linking code generation source (LLM vs human) to memory footprint, enabling practitioners to assess deployment risks.

## Expected results

We expect to find measurable differences in memory consumption between LLM-generated and human-written code, with either higher or lower usage depending on LLM architecture and prompt design. A statistically significant difference (p < 0.05, effect size d > 0.5) on a sample of N ≥ 50 code pairs would provide sufficient evidence to support deployment guidelines; a null result would similarly be informative by confirming LLM code meets memory expectations.

## Methodology sketch

- Download HumanEval or MBPP benchmark datasets from HuggingFace Datasets (public, no authentication required)
- Extract human-written reference solutions from the benchmark (ground truth)
- Generate LLM code solutions using CodeLlama-7B or StarCoder (via HuggingFace Transformers, single-GPU-free inference)
- Create a profiling harness using Python's `memory_profiler` and `tracemalloc` modules
- Execute each code solution on identical test inputs from the benchmark
- Record peak memory usage, steady-state memory, and allocation patterns for each execution
- Compute paired differences (LLM memory minus human memory) for each problem-solution pair
- Apply Wilcoxon signed-rank test to assess whether memory differences are systematically positive or negative
- Perform regression analysis to identify code features (lines of code, loop depth, library imports) that predict memory usage
- Generate summary statistics and visualizations (box plots, scatter plots) for the final report

## Duplicate-check

- Reviewed existing ideas: N/A (first iteration in this field)
- Closest match: None identified in corpus
- Verdict: NOT a duplicate

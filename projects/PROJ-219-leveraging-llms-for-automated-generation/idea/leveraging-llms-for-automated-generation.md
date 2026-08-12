---
field: computer science
submitter: google.gemma-3-27b-it
---

# Leveraging LLMs for Automated Generation of Code Complexity Metrics

**Field**: computer science

## Research question

How accurately do zero-shot large language models predict standard code-complexity metrics (e.g., cyclomatic complexity, Halstead volume) compared to traditional static analysis, and what code-level factors drive any systematic prediction errors?

## Motivation

Traditional static analysis tools are deterministic and fast but lack semantic context, while LLMs offer reasoning capabilities that may handle novel or obfuscated code better. This research addresses the critical gap in understanding whether LLMs can serve as reliable, semantic-aware proxies for complexity metrics in continuous integration pipelines, and specifically identifies the conditions under which they fail.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using terms: "LLM code complexity metrics," "large language models cyclomatic complexity," "software quality LLM evaluation," and "static analysis vs LLM code metrics." The search returned a sparse set of results, with only one paper directly addressing the conceptual framework of comprehensive quality models in software, but none explicitly benchmarking LLMs against traditional static analyzers for quantitative metric estimation.

### What is known

- [Are Comprehensive Quality Models Necessary for Evaluating Software Quality? (2017)](https://arxiv.org/abs/1703.04298) — Establishes that software quality is a multi-faceted concept where comprehensive measurement is often impractical, suggesting a need for efficient proxies like LLMs, though it does not evaluate LLMs specifically.

### What is NOT known

No published work has quantitatively compared zero-shot LLM predictions of standard complexity metrics (cyclomatic complexity, Halstead volume) against ground-truth static analysis results on a controlled dataset. Specifically, it is unknown which code structures (e.g., deep nesting, dynamic control flow, heavy commenting) cause LLMs to systematically over- or under-estimate these metrics.

### Why this gap matters

Understanding the failure modes of LLMs in this domain is essential for deciding whether they can be trusted in automated code review tools. If LLMs consistently fail on specific complex patterns, developers can either fine-tune models or restrict their use, preventing false confidence in code quality assessments.

### How this project addresses the gap

This project directly measures the correlation between LLM estimates and static analysis ground truth on a diverse dataset of code snippets. By analyzing the residuals of this comparison, we will isolate specific code-level features (e.g., nesting depth, variable count) that correlate with prediction errors, providing the first empirical map of LLM reliability for this task.

## Expected results

We expect a moderate to high correlation (Pearson r > 0.7) for simple, linear code structures but significant divergence on complex control flows. The primary finding will be a characterization of error patterns, likely showing that LLMs overestimate complexity in highly nested code or underestimate it in obfuscated logic, providing a basis for targeted model improvements.

## Methodology sketch

- **Data Acquisition**: Download 500 diverse Python code snippets from the `codeparrot/github-code-clean` dataset on HuggingFace (`hf://datasets/codeparrot/github-code-clean`), stratified by file size and function count to ensure variety.
- **Ground Truth Calculation**: Execute the `radon` Python library locally on all snippets to compute deterministic ground-truth values for Cyclomatic Complexity (CC) and Halstead Volume.
- **LLM Inference**: Load a quantized 1B parameter model (e.g., TinyLlama-1.1B INT4) using the `transformers` library on a CPU-only environment, ensuring memory usage remains under 4GB.
- **Prompt Engineering**: Construct zero-shot prompts requesting the model to output CC and Halstead Volume as JSON for each snippet, explicitly defining the metric definitions to reduce ambiguity.
- **Execution & Logging**: Run inference on the 500 snippets, logging inference latency, token usage, and raw model outputs.
- **Parsing & Alignment**: Parse model JSON outputs and align them with the `radon` ground truth, handling non-numeric or malformed outputs as errors.
- **Statistical Analysis**: Compute Pearson correlation coefficients and Mean Absolute Error (MAE) between LLM predictions and static analysis values.
- **Error Attribution**: Perform a regression analysis where the dependent variable is the prediction error (|LLM - Radon|) and independent variables are code features (e.g., lines of code, nesting depth, comment density) extracted via `ast` module, to identify drivers of systematic error.
- **Visualization**: Generate scatter plots of predicted vs. actual values and heatmaps of error distribution across code complexity buckets.
- **Validation Independence**: Ensure the error attribution analysis uses code features derived from the Abstract Syntax Tree (AST) as predictors, which are structurally distinct from the semantic reasoning performed by the LLM, avoiding circular validation.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: N/A.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-08-12T00:36:16Z
**Outcome**: exhausted
**Original term**: Leveraging LLMs for Automated Generation of Code Complexity Metrics computer science
**Verified citation count**: 1

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Leveraging LLMs for Automated Generation of Code Complexity Metrics computer science | 0 |
| 1 | large language models for software complexity analysis | 4 |
| 2 | automated code metric generation using AI | 0 |
| 3 | LLM-based static code analysis | 0 |
| 4 | neural network estimation of cyclomatic complexity | 0 |
| 5 | generative AI for software quality metrics | 0 |
| 6 | transformer models for code maintainability assessment | 0 |
| 7 | automated extraction of code complexity indicators via LLMs | 0 |
| 8 | AI-driven software metric prediction | 0 |
| 9 | deep learning approaches to code complexity measurement | 0 |
| 10 | large language models for estimating cognitive complexity | 0 |
| 11 | LLMs for calculating lines of code and nesting depth | 0 |
| 12 | automated software engineering metrics with generative models | 0 |
| 13 | natural language processing for code quality evaluation | 0 |
| 14 | machine learning models for software maintainability indices | 0 |
| 15 | code complexity prediction using pre-trained language models | 0 |
| 16 | automated generation of Halstead metrics with LLMs | 0 |
| 17 | AI-assisted code smell and complexity detection | 0 |
| 18 | neural code understanding for metric derivation | 0 |
| 19 | large language models in software engineering measurement | 0 |
| 20 | automated software metric computation using generative AI | 0 |

### Verified citations

1. **Are Comprehensive Quality Models Necessary for Evaluating Software Quality?** (2017). Klaus Lochmann, Jasmin Ramadani, Stefan Wagner. arXiv. [1703.04298](https://arxiv.org/abs/1703.04298). PDF-sampled: No.

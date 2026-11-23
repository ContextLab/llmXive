---
field: computer science
submitter: google.gemma-3-27b-it
---

# Leveraging LLMs for Automated Generation of Code Complexity Metrics

**Field**: computer science

## Research question

To what extent does the semantic representation of code in large language models diverge from the syntactic definition of complexity metrics, and which structural code patterns specifically cause this divergence?

## Motivation

Traditional static analysis tools calculate complexity (e.g., cyclomatic complexity) based on strict syntactic rules, ignoring semantic intent, while LLMs reason about code semantics. This research addresses the critical gap in understanding whether LLMs' semantic "understanding" aligns with or systematically deviates from established syntactic metrics, and identifies specific code structures where this divergence creates reliability risks for automated code review.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using terms: "LLM code complexity metrics," "large language models cyclomatic complexity," "semantic vs syntactic code metrics," and "LLM estimation of software quality." The search returned a sparse set of results directly relevant to the specific comparison of LLM semantic representations against standard syntactic complexity metrics. Most results focused on code generation, general quality assessment in other media (images/video), or broad information system quality, rather than the specific mechanistic divergence between LLM reasoning and static analysis.

### What is known

- [Are Comprehensive Quality Models Necessary for Evaluating Software Quality?](https://arxiv.org/abs/1703.04298) — Establishes that software quality is multi-faceted and that comprehensive measurement is often impractical, suggesting a need for efficient proxies, though it predates the specific application of LLMs for metric estimation.

### What is NOT known

No published work has quantitatively compared the *semantic* estimates of complexity produced by zero-shot LLMs against the *syntactic* ground truth of standard metrics (e.g., Cyclomatic Complexity, Halstead Volume) to map the specific structural patterns where they diverge. It remains unknown whether LLMs perceive "complexity" in ways that are orthogonal to, or merely noisy versions of, traditional static analysis definitions.

### Why this gap matters

Understanding the nature of this divergence is essential for deploying LLMs in continuous integration pipelines. If LLMs consistently "misinterpret" complexity due to semantic reasoning (e.g., ignoring a complex loop because the logic is simple), relying on them could lead to false security or missed refactoring opportunities. Filling this gap provides a principled basis for when to trust LLMs versus traditional tools.

### How this project addresses the gap

This project directly measures the correlation and residuals between LLM-generated complexity estimates and static analysis ground truth on a diverse dataset. By regressing these residuals against specific syntactic features (nesting depth, control flow density, variable usage), we will empirically map the structural conditions that trigger semantic-syntactic divergence.

## Expected results

We expect a moderate correlation for linear code but significant divergence in cases involving complex control flow or obfuscated logic. The primary finding will be a characterization of error patterns, likely showing that LLMs systematically underestimate complexity in highly nested but semantically simple code, or overestimate it in complex but well-abstracted logic, providing a basis for targeted model calibration.

## Methodology sketch

- **Data Acquisition**: Download 500 diverse Python code snippets from the `codeparrot/github-code-clean` dataset on HuggingFace (`hf://datasets/codeparrot/github-code-clean`), stratified by file size and function count.
- **Ground Truth Calculation**: Execute the `radon` Python library locally on all snippets to compute deterministic ground-truth values for Cyclomatic Complexity (CC) and Halstead Volume.
- **Code Feature Extraction**: Use the Python `ast` module to extract syntactic features (nesting depth, number of branches, variable count) that are independent of the LLM's semantic processing.
- **LLM Inference**: Load a quantized 1B parameter model (e.g., TinyLlama-1.1B INT4) using the `transformers` library on a CPU-only environment, ensuring memory usage remains under 4GB.
- **Prompt Engineering**: Construct zero-shot prompts requesting the model to output CC and Halstead Volume as JSON, explicitly defining the metric definitions to minimize ambiguity.
- **Execution & Logging**: Run inference on the 500 snippets, logging inference latency, token usage, and raw model outputs.
- **Parsing & Alignment**: Parse model JSON outputs and align them with the `radon` ground truth, handling non-numeric or malformed outputs as errors.
- **Statistical Analysis**: Compute Pearson correlation coefficients and Mean Absolute Error (MAE) between LLM predictions and static analysis values.
- **Error Attribution**: Perform a regression analysis where the dependent variable is the prediction error (|LLM - Radon|) and independent variables are the extracted syntactic features (nesting depth, branch count), ensuring these predictors are structurally distinct from the LLM's internal semantic representation.
- **Visualization**: Generate scatter plots of predicted vs. actual values and heatmaps of error distribution across code complexity buckets.
- **Validation Independence**: Ensure the error attribution analysis relies on syntactic features derived from the Abstract Syntax Tree (AST) as predictors, which are mathematically distinct from the semantic reasoning performed by the LLM, avoiding circular validation.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: N/A.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-09-01T12:29:33Z
**Outcome**: success_after_expansion
**Original term**: Leveraging LLMs for Automated Generation of Code Complexity Metrics computer science
**Verified citation count**: 8

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Leveraging LLMs for Automated Generation of Code Complexity Metrics computer science | 0 |
| 1 | LLM-based code quality assessment | 5 |
| 2 | automated software complexity estimation using language models | 0 |
| 3 | large language models for static code analysis | 0 |
| 4 | neural network prediction of cyclomatic complexity | 0 |
| 5 | generative AI for software metric computation | 0 |
| 6 | code complexity measurement with transformer models | 0 |
| 7 | AI-driven software maintainability evaluation | 0 |
| 8 | natural language processing for code metric extraction | 0 |
| 9 | fine-tuned LLMs for source code analysis | 0 |
| 10 | automated derivation of Halstead metrics using LLMs | 0 |
| 11 | machine learning approaches to code complexity prediction | 0 |
| 12 | LLMs for estimating cognitive complexity | 0 |
| 13 | deep learning models for software engineering metrics | 0 |
| 14 | automated code smell detection via large language models | 0 |
| 15 | semantic code analysis for complexity scoring | 0 |
| 16 | zero-shot code metric generation with foundation models | 0 |
| 17 | comparing LLM outputs to traditional complexity tools | 0 |
| 18 | LLM-assisted software refactoring based on complexity | 0 |
| 19 | predicting code maintainability with generative AI | 0 |
| 20 | automated generation of software engineering KPIs using LLMs | 0 |

### Verified citations

1. **The Future of Scientific Publishing: Automated Article Generation** (2024). Jeremy R. Harper. arXiv. [2404.17586](https://arxiv.org/abs/2404.17586). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
2. **Context Engineering for Multi-Agent LLM Code Assistants Using Elicit, NotebookLM, ChatGPT, and Claude Code** (2025). Muhammad Haseeb. arXiv. [2508.08322](https://arxiv.org/abs/2508.08322). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
3. **EVOR: Evolving Retrieval for Code Generation** (2024). Hongjin Su, Shuyang Jiang, Yuhang Lai, Haoyuan Wu, Boao Shi, et al.. arXiv. [2402.12317](https://arxiv.org/abs/2402.12317). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
4. **Scale Guided Hypernetwork for Blind Super-Resolution Image Quality Assessment** (2023). Jun Fu. arXiv. [2306.02398](https://arxiv.org/abs/2306.02398). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
5. **Enhancing Blind Video Quality Assessment with Rich Quality-aware Features** (2024). Wei Sun, Linhan Cao, Jun Jia, Zhichao Zhang, Zicheng Zhang, et al.. arXiv. [2405.08745](https://arxiv.org/abs/2405.08745). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
6. **AIS 2024 Challenge on Video Quality Assessment of User-Generated Content: Methods and Results** (2024). Marcos V. Conde, Saman Zadtootaghaj, Nabajeet Barman, Radu Timofte, Chenlong He, et al.. arXiv. [2404.16205](https://arxiv.org/abs/2404.16205). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
7. **Towards an Assessment-oriented Model for External Information System Quality Characterization** (2013). Abir Elmir, Badr Elmir, Bouchaib Bounabat. arXiv. [1310.8111](https://arxiv.org/abs/1310.8111). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
8. **LEIQ-Assessor: Multi-dimensional Quality Assessment of Low-light Enhanced Images via Multi-task Learning** (2026). Wei Sun, Yanwei Jiang, Dandan Zhu, Jinqiu Sang, Jikai Xu, et al.. arXiv. [2606.29752](https://arxiv.org/abs/2606.29752). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*

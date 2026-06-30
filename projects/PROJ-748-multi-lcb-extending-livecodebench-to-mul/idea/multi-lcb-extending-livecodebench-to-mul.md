---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/348
paper_authors:
  - Maria Ivanova
  - Pavel Zadorozhny
  - Rodion Levichev
  - Ivan Petrov
  - Adamenko Pavel
  - Ivan Lopatin
  - Alexey Kutalev
  - Dmitrii Babaev
---

# Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages

**Field**: computer science

## Research question

How does the performance ranking of large language models on code-generation tasks vary across different programming languages, and to what extent does performance in Python serve as a reliable proxy for performance in non-Python languages?

## Motivation

Current evaluations of code-generating LLMs are heavily biased toward Python, despite the prevalence of other languages in industry and competitive programming. This reliance creates a risk that models optimized for Python syntax may fail to generalize to other environments, yet there is insufficient empirical evidence to determine if Python performance is a robust predictor of cross-language capability. Addressing this gap is critical for establishing fair, multi-language benchmarks that prevent "Python overfitting" and accurately reflect a model's true versatility.

## Literature gap analysis

### What we searched
We queried Semantic Scholar and arXiv using the following terms: "LiveCodeBench multi-language extension," "LLM code generation cross-language performance," "Python vs non-Python LLM benchmarking," and "multilingual code generation evaluation." We specifically looked for studies comparing model rankings across diverse syntaxes (e.g., C++, Java, Python) and analyses of data contamination in competitive programming datasets.

### What is known
- [Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages (2026)](https://arxiv.org/abs/2606.20517) — This paper introduces a dataset extending LiveCodeBench to 12 programming languages, providing initial evidence that Python performance does not always correlate perfectly with other languages, though it notes specific statistical inconsistencies in its own methodology regarding sampling and confidence intervals.
- [Cross-Lingual Pitfalls: Automatic Probing Cross-Lingual Weakness of Multilingual Large Language Models (2025)](https://arxiv.org/abs/2505.18673) — This work establishes that while LLMs show remarkable success in natural language processing, their cross-lingual consistency is fragile; the authors propose methods to automatically probe these weaknesses, a technique that could be adapted for code generation to identify specific language-dependent failure modes.

### What is NOT known
The existing literature lacks a rigorous, statistically powered analysis of the *magnitude* of the correlation between Python and non-Python performance across a wide spectrum of models, specifically controlling for data contamination and temperature sensitivity. Furthermore, there is no standardized framework for evaluating whether "Python overfitting" is a systematic bias in top-tier models or an artifact of the specific benchmarks used in prior studies.

### Why this gap matters
Without quantifying the reliability of Python as a proxy, the community risks deploying models that appear competent in Python-centric evaluations but fail in production environments dominated by C++, Java, or Go. Filling this gap will enable the creation of more robust, language-agnostic evaluation metrics, guiding better model selection for multi-language software engineering tasks and preventing the misallocation of compute resources toward models with narrow language capabilities.

### How this project addresses the gap
This project will re-evaluate the Multi-LCB dataset using a rigorous statistical framework (paired t-tests with multiple comparison corrections) to quantify the correlation between Python and non-Python pass rates. By explicitly controlling for temperature variations and model versioning, we will produce a definitive ranking of models that distinguishes between general code-generation capability and Python-specific optimization, directly addressing the statistical and contamination concerns raised in prior work.

## Expected results

We expect to find a moderate-to-strong correlation between Python and other languages for top-tier models, but with significant outliers where Python performance overestimates capability in lower-level languages (e.g., C++). The statistical analysis will likely reveal that temperature sensitivity varies by language, suggesting that single-temperature benchmarks are insufficient for cross-language comparison. These findings will be confirmed by a significant p-value in the correlation test and a distinct clustering of models in a multi-dimensional performance space that separates "generalists" from "Python-specialists."

## Methodology sketch

- **Data Acquisition**: Download the Multi-LCB dataset (12 languages, 1,055 tasks each) from the Hugging Face repository linked in the source paper, ensuring version pinning via the provided commit hash or Zenodo snapshot.
- **Preprocessing**: Parse the JSON schema to extract problem statements, test cases, and reference solutions; convert all STDIN/STDOUT test cases into a unified execution format using a Docker-based sandbox environment.
- **Execution**: Run the target LLMs (e.g., Qwen, GPT-OSS, CodeLlama) on the dataset using a fixed temperature (0.2) and a broader range (0.6, 1.0) for sensitivity analysis, executing each task 10 times to estimate variance.
- **Metric Calculation**: Compute Pass@1, Pass@5, and Pass@10 for each model-language pair, calculating mean and standard deviation; apply Bonferroni correction to account for the 288 comparisons (24 models × 12 languages).
- **Statistical Analysis**: Perform Pearson correlation analysis between Python pass rates and non-Python pass rates; conduct paired t-tests (or Wilcoxon signed-rank tests for non-normal distributions) to compare model performance across languages.
- **Contamination Check**: Verify task release dates against model training cutoffs; exclude any tasks released after a model's cutoff date to ensure a contamination-free evaluation subset.
- **Visualization**: Generate radar charts and boxplots with clearly labeled axes, units (%), and legends to visualize performance distributions and correlations; create heatmaps showing error types by language.
- **Validation**: Compare results against the original Multi-LCB paper's summary statistics to identify discrepancies; re-run a subset of tasks with manual inspection to verify the "no major inconsistencies" claim in the conversion pipeline.
- **Reporting**: Compile results into a reproducible report including the full statistical model, effect sizes, and confidence intervals, ensuring all figures meet publication standards for resolution and labeling.

## Duplicate-check

- Reviewed existing ideas: Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages.
- Closest match: Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages (similarity sketch: identical title and core research question).
- Verdict: duplicate of Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-30T12:58:22Z
**Outcome**: exhausted
**Original term**: Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages computer science
**Verified citation count**: 2

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages computer science | 0 |
| 1 | cross-lingual code generation benchmarks | 5 |
| 2 | multilingual code evaluation datasets | 0 |
| 3 | LiveCodeBench extension to non-Python languages | 0 |
| 4 | programming language agnostic coding benchmarks | 0 |
| 5 | comparative analysis of LLMs across multiple programming languages | 0 |
| 6 | code generation performance in diverse syntax environments | 0 |
| 7 | multilingual software engineering datasets for large language models | 0 |
| 8 | cross-language code synthesis evaluation | 0 |
| 9 | benchmarking LLMs on Java, C++, and JavaScript code generation | 0 |
| 10 | generalization of code benchmarks beyond Python | 0 |
| 11 | multilingual code understanding and generation metrics | 0 |
| 12 | heterogeneous programming language code datasets | 0 |
| 13 | evaluating LLMs on polyglot coding tasks | 0 |
| 14 | LiveCodeBench multi-language adaptation | 0 |
| 15 | code generation benchmarks for low-resource programming languages | 0 |
| 16 | cross-lingual transfer in code generation models | 0 |
| 17 | standardized evaluation for multilingual code assistants | 0 |
| 18 | dataset construction for multilingual code generation | 0 |
| 19 | performance variance of code LLMs across language families | 0 |
| 20 | expanding code benchmarks to include C++ and Java | 0 |

### Verified citations

1. **Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages** (2026). Maria Ivanova, Pavel Zadorozhny, Rodion Levichev, Ivan Petrov, Adamenko Pavel, et al.. arXiv. [2606.20517](https://arxiv.org/abs/2606.20517). PDF-sampled: No.
2. **Cross-Lingual Pitfalls: Automatic Probing Cross-Lingual Weakness of Multilingual Large Language Models** (2025). Zixiang Xu, Yanbo Wang, Yue Huang, Xiuying Chen, Jieyu Zhao, et al.. arXiv. [2505.18673](https://arxiv.org/abs/2505.18673). PDF-sampled: No.

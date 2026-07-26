# Research: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code

## Overview

This research investigates whether structural (AST depth, complexity) and semantic (taint API frequency, embedding similarity) features of code snippets predict the accuracy of Large Language Models (LLMs) in identifying security vulnerabilities. The study compares zero-shot LLM performance against static analyzer baselines (Bandit, cppcheck) across Python, C, and JavaScript. **Crucially, the analysis is framed as measuring predictive associations, not causal mechanisms.**

## Dataset Strategy

The study utilizes three open, programmatic datasets verified for direct download via Hugging Face `datasets` library. No access-gated data is used.

| Language | Dataset Source | Verified URL | Usage |
|:--- |:--- |:--- |:--- |
| **Python** | VulDeePecker | ` | Primary source for Python snippets (vulnerable/safe). |
| **C/C++** | BigVul | ` | Primary source for C/C++ snippets. **Note**: Replaces NIST Juliet due to lack of verified raw code URLs. |
| **JavaScript** | BigVul / JS HF | ` | Primary source for JS snippets. |

**Dataset Strategy Rationale**:
- **Feasibility**: All selected URLs are direct `.parquet` downloads via `datasets.load_dataset` or `hf_hub_download`. No authentication is required.
- **Gap Handling**: The spec mentions "NIST Juliet" for C, but the verified dataset block lacks a direct NIST C-code snippet source. To avoid fabrication (Constitution Principle II), the plan substitutes **BigVul** for C/C++ analysis. The study scope is explicitly adjusted to "LLM effectiveness on BigVul C/C++" rather than NIST Juliet.
- **Sampling**: Stratified sampling by language and vulnerability type (if labels exist) will be applied to reach a representative sample cap.

**Power Analysis & Sampling**:
Before inference, the plan will verify sample sizes per language.
- **Protocol**: G*Power parameters (alpha=0.05, power=0.80, effect size=0.2) will be used to calculate minimum sample sizes.
- **Fallback**: If the C-subset is too small (<100 samples), the study will report "underpowered for C" and exclude C from cross-language regression, focusing on Python/JS.

## Model & Method Selection

### LLM Inference (CPU-First)
- **Model**: `microsoft/Phi-3-mini-4k-instruct` or `stabilityai/stable-code-3b` (quantized to 4-bit if RAM permits, otherwise default float16).
- **Rationale**: These models are small enough to fit in standard CPU memory. Larger models (e.g., CodeLlama-7B) would exceed RAM limits or require the GPU escape hatch, which is reserved for embedding models if necessary.
- **Quantization**: `bitsandbytes` 4-bit quantization if available for CPU; otherwise, default precision with batch size = 1.
- **Context Window**: Truncation to the model's maximum context length for snippets exceeding limits.

### Embedding Model
- **Model**: `sentence-transformers/all-MiniLM-L6-v2` (CPU-tractable, ~80MB).
- **Rationale**: Provides semantic similarity scores to known vulnerable patterns without requiring a GPU.

### Static Analyzers
- **Python**: `bandit` (CLI).
- **C**: `cppcheck` (CLI).

### Reference Set Construction (FR-004)
- **Source**: A curated subset of 500 known vulnerable snippets from the **BigVul train split** (excluding the test split used for evaluation).
- **Usage**: These snippets are embedded using `all-MiniLM-L6-v2` to create a fixed reference set for computing cosine similarity scores. This ensures independence from the test set while using verified data.

## Statistical Methodology

1. **Descriptive Statistics**: Precision, Recall, F1, ROC-AUC per language and vulnerability category.
2. **Correlation Analysis**: **Point-Biserial correlation** (not Pearson) between features (AST depth, complexity, etc.) and `is_correct` (binary).
 - **Multiple Comparison Correction**: Benjamini-Hochberg procedure applied to the family of tests for each language/category to control FDR.
 - **Collinearity Check**: Variance Inflation Factors (VIF) will be calculated. If `taint_api_count` has VIF > 5 (indicating it is a proxy for the label), it will be excluded from the primary regression to avoid trivial results.
3. **Regression**: Logistic Regression (GLM with logit link) predicting `is_correct` from features + `language` (categorical) + **`source_dataset`** (categorical).
 - **Metric**: Adjusted R² (Nagelkerke) and coefficient p-values.
 - **Interpretation**: Coefficients indicate **predictive association**, not causal mechanisms.
4. **Baseline Comparison**: McNemar's test comparing LLM predictions vs. Static Analyzer predictions on the same samples.
 - **Static Analyzer Output Mapping**: 'unknown' or 'no issue' from static analyzers are mapped to 'safe' (0) for the binary pairing. Samples with non-binary outputs are counted separately.
5. **Sensitivity Analysis (FR-011)**:
 - **Protocol**: A secondary rule-based classifier (using a distinct set of regex patterns not used in the primary datasets) will be run on a subset (n=100) to generate 'pseudo-ground-truth' labels.
 - **Purpose**: To assess the impact of potential ground-truth label noise on the calculated metrics.

## Validation Strategy

- **Circular Validation Warning**: The analysis acknowledges that `is_correct` is defined by the dataset label. The regression may predict the *dataset's labeling bias* rather than LLM capability. The FR-011 sensitivity analysis is elevated to a primary validation check to mitigate this.
- **Baseline Independence Check**: The plan will verify that the ground truth labels in BigVul/VulDeePecker were not derived solely from the specific rules of Bandit/cppcheck. If overlap is detected (e.g., BigVul labels based on static rules), the comparison is flagged as 'potential circularity' and the study will prioritize LLM-only analysis for those specific CWEs.

## Compute Feasibility & Escape Hatch

- **CPU Path**: The primary pipeline runs on CPU.
 - **LLM**: Batch size 1, quantized model.
 - **Embeddings**: `all-MiniLM-L6-v2` (fast on CPU).
 - **Static Analysis**: CLI tools (fast).
 - **Total Time**: Estimated 4.5 hours for [deferred] samples (A per-sample computational budget.).
- **GPU Escape Hatch**: If the embedding model fails to load on CPU or the LLM quantization fails, the execution agent will offload to Kaggle GPU.
 - **Scaled Down**: Only the embedding step or a small subset of LLM inferences will run on GPU.
 - **No Fabrication**: The plan does not simulate GPU results; it plans for the real scaled-down GPU run if CPU fails.
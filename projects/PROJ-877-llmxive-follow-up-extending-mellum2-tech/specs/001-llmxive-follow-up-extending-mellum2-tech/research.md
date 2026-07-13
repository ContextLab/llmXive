# Research: llmXive follow-up: extending "Mellum2 Technical Report"

## 1. Research Question & Hypothesis

**Primary Question**: Is there a statistically significant correlation between static code complexity metrics (cyclomatic complexity, nesting depth) and the prediction loss (perplexity) of a frozen LLM? Does this relationship exhibit non-linear thresholds where prediction difficulty increases disproportionately?

**Hypotheses**:
- **H1**: There is a positive correlation between static complexity metrics and LLM prediction loss.
- **H2**: The relationship is non-linear, with specific thresholds (e.g., nesting depth > 4) where the slope of the relationship increases significantly.
- **H3**: This relationship holds across different programming languages (Python vs. Java) when controlling for token frequency.

## 2. Dataset Strategy

**Source**: The project utilizes the `codeparrot/github-code` dataset from HuggingFace.
*Note: The `# Verified datasets` block provided in the prompt lists `AdityaMayukhSom/MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score`. This dataset is a **training benchmark for CPU inference** and does not contain the raw code repositories required for static analysis (CodeQL/tree-sitter) or the specific Python/Java repositories needed for the research question. The spec explicitly requires `codeparrot/github-code` (FR-001). Since `codeparrot/github-code` is a standard, well-known HuggingFace dataset but **not** in the provided "Verified datasets" block, we must state the mismatch explicitly.*

**Constraint**: Per the output contract, we cannot invent a URL for `codeparrot/github-code`. However, the research plan **must** use `codeparrot/github-code` to satisfy FR-001 and the research question.
**Resolution**: The plan will proceed with the assumption that `codeparrot/github-code` is accessible via the standard `datasets` library (which is verified for this dataset in general HF usage), but the **specific URL** for the raw parquet files is not in the provided "Verified datasets" block. The implementation will attempt to load via `datasets.load_dataset("codeparrot/github-code", ...)` which is the standard programmatic loader.

**Fallback Methodology**: If `codeparrot/github-code` is inaccessible (network error, rate limit, or missing), the study will be **aborted** and reported as "Data Unavailable". No partial results will be generated, as the research question is dependent on this specific code structure.

**Dataset Selection Rationale**:
- **CodeParrot/github-code**: Contains diverse, real-world Python and Java repositories.
- **Subsetting**: To meet the disk constraint, we will sample a fixed number of repositories (e.g., 500 Python, 500 Java) and limit chunk sizes.
- **Variables**:
  - **Predictors**: Cyclomatic Complexity, Nesting Depth, Repetition Ratio (derived via static analysis).
  - **Outcome**: Per-token loss (log loss), prediction entropy (derived via LLM inference).
  - **Covariates**: Token frequency (n-gram probability), language ID.

**Potential Mismatch**: If the `codeparrot/github-code` dataset lacks sufficient variety in complexity levels (e.g., mostly boilerplate), the study may return a null result. This is an acceptable outcome per the spec (Edge Cases).

## 3. Methodology & Statistical Rigor

### 3.1 Data Pipeline

1.  **Download**: Fetch sampled repos from `codeparrot/github-code`.
2.  **Static Analysis (Independence Guarantee)**:
    - Run **CodeQL** and **tree-sitter** on raw code chunks.
    - **Memory Mitigation**: CodeQL is configured with a per-file limit (max a moderate number of lines). Files exceeding this are skipped and logged to prevent OOM on the 7GB runner.
    - Compute: Cyclomatic Complexity, Nesting Depth, Repetition Ratio.
    - *Constraint*: This step is strictly separated from LLM inference to satisfy Constitution Principle VI.
3.  **LLM Inference**:
    - Load a frozen CPU-optimized model: **`TinyLlama-1.1B-Chat-v1.0`** (selected for feasibility on 2 CPU/7GB RAM).
    - *Note*: Llama-3-8B or Mistral-7B are infeasible on the free tier (requires >16GB RAM for weights).
    - Compute per-token loss and entropy for each chunk.
    - *Constraint*: Must run on CPU only. No 8-bit quantization.
4.  **Normalization (FR-010)**:
    - **Baseline Model**: A pre-trained, fixed-order **5-gram Kneser-Ney smoothed model** trained on a **disjoint** subset of The Stack (non-overlapping with the test set). This model is loaded from a pre-computed binary file to avoid on-the-fly training overhead.
    - **Mathematical Operation**: `normalized_loss = -log(p_llm) - (-log(p_5gram))`.
    - This isolates structural uncertainty by subtracting the baseline n-gram probability from the LLM's probability, avoiding circularity (the baseline is not an LLM).

### 3.2 Statistical Analysis

- **Unit of Analysis & Aggregation**:
  - To avoid pseudoreplication (chunks nested within repos), the primary correlation analysis is performed on **Repository-Level Aggregates**.
  - For each repository, compute the mean of all chunk metrics (complexity, loss, normalized_loss).
  - **Correlation (FR-004)**: Compute Pearson and Spearman correlation coefficients between these **aggregated** means across repositories.
- **Multiple Comparison Correction (FR-008)**:
  - Apply Benjamini-Hochberg (FDR) correction for tests on multiple metrics (Complexity, Depth, Repetition) and multiple languages.
- **Threshold Detection (FR-005)**:
  - Use **Piecewise Regression** (segmented regression) or **Change-Point Detection** (e.g., `ruptures` library) on the aggregated data.
  - Compare models (Linear vs. Piecewise) using AIC/BIC. If AIC difference < 2, prefer linear model.
- **Sensitivity Analysis (FR-006)**:
  - Sweep threshold values (±0.01, ±0.05, ±0.1) around the identified point.
  - Report variation in inconsistency rates.
- **Dataset Perturbation (SC-002)**:
  - To measure threshold stability, perform **Bootstrap Resampling** of repositories (subsampling with replacement).
  - Re-run threshold detection on a substantial number of bootstrap samples.
  - Measure the maximum shift in the identified threshold value across samples (must be ≤ 0.05 units).
- **Significance & Power (FR-007, FR-008)**:
 - **Permutation Test**: Perform block permutations at the **Repository Level** ([deferred] iterations) on the aggregated data to generate a null distribution of correlation coefficients.
  - **Power Analysis**: The study is **compute-constrained**. Sample size is determined by the runtime limit on the free tier.. The study is framed as **exploratory**; we report observed effect sizes and confidence intervals but do not claim "adequate power" based on post-hoc calculations.
  - **Cross-Language Validation (FR-009)**: Compute correlation separately for Python and Java; compare coefficients.
- **Proxy Validation (FR-011)**:
  - **Constraint**: CodeXGLUE does not contain human-labeled complexity ratings.
  - **Strategy**: Correlate static complexity metrics with **CodeBLEU** scores (a code quality proxy) on a representative sample.
  - **Limitation**: We explicitly acknowledge that this validates "complexity-quality correlation" rather than "complexity-reasoning depth" directly, due to the lack of a standard human-labeled complexity benchmark.

### 3.3 Computational Feasibility (CPU-Only)

- **Model**: `TinyLlama-1.1B-Chat-v1.0` on CPU.
  - *Strategy*: Use `transformers` with `torch_dtype=torch.float32`. Expect moderate throughput on CPU cores.
  - *Mitigation*: Strict chunk size limits and repository sampling to ensure total runtime < 6 hours.
- **Static Analysis**: CodeQL memory limits enforced (max 500 lines/file). `tree-sitter` used for faster parsing where possible.
- **Memory**: Process data in batches (streaming) to stay under available RAM limits..

## 4. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Dataset Unavailability** | High | `codeparrot/github-code` not in "Verified datasets" list. | **Abort**: If download fails, report "Data Unavailable" and halt. |
| **CPU Inference Timeouts** | High | 2 CPU cores may be too slow. | Use TinyLlama-1.1B; strict 6h timeout; reduce sample size if needed. |
| **Static Analysis Failure** | Medium | CodeQL/tree-sitter fail on syntax errors. | Skip file, log error, continue (Edge Case handling). |
| **Low Variance in Complexity** | Medium | Dataset too simple. | Detect lack of variance; report null result (Edge Case). |
| **Collinearity** | Medium | Complexity metrics may be correlated. | Report correlation matrix; acknowledge collinearity in interpretation (do not claim independent effects). |

## 5. Decision Log

- **Dataset**: `codeparrot/github-code` selected for diversity. Fallback: Abort if unavailable.
- **Model**: `TinyLlama-1.1B-Chat-v1.0` (CPU) selected for feasibility. 8B models rejected.
- **Analysis**: Repository-Level Aggregation selected as primary method to avoid pseudoreplication.
- **Correction**: Benjamini-Hochberg (FDR) selected for multiple comparisons.
- **Baseline**: Pre-computed 5-gram Kneser-Ney model on disjoint corpus selected for normalization.
- **Validation**: Proxy validation using CodeBLEU selected with explicit limitation statement.
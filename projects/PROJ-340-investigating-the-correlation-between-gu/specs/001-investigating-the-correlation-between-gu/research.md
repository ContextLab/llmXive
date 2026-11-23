# Research: Investigating the Correlation Between Gut Microbiome Composition and Sleep Architecture

## Dataset Strategy

The project requires a dataset containing both **metagenomic sequencing data** (predictors: microbial taxa abundances) and **sleep architecture metrics** (outcomes: REM duration, SWS duration, etc.) for the same subjects.

### Verified Datasets
Based on the provided verified sources, the following datasets were reviewed:

| Dataset Name | Source URL | Suitability |
|--------------|------------|-------------|
| REM (parquet) | ` | **Not Suitable**: Contains phishing URL data, not biological sleep/microbiome data. |
| SWS (zip) | ` | **Not Suitable**: File name suggests "SWS" but content is likely unrelated. |
| VIFs (parquet) | ` | **Not Suitable**: Contains cattle pricing data, not human microbiome/sleep. |
| CPU-only (parquet) | `https://huggingface.co/datasets/AdityaMayukhSom/MixSub-LLaMA-3.2-...` | **Not Suitable**: Contains LLM training scores, not biological data. |
| Human Microbiome Project (HMP2) | ` | **Not Suitable**: Contains metagenomics but lacks concurrent polysomnography data. |
| American Gut Project | ` | **Not Suitable**: Public survey data lacks clinical sleep architecture metrics. |
| Sleep Microbiome Studies (General) | N/A | **Not Suitable**: No single public dataset currently contains both modalities (metagenomics + PSG) for the same subjects. |

### Decision & Rationale
**Critical Gap Identified**: None of the *verified* datasets provided in the input block, nor any known public dataset, contain the required biological variables (gut microbiome counts + sleep architecture) for the same subjects.

**Action Plan**:
1. **Primary Strategy**: The implementation will be designed to accept a **generic CSV/TSV input** as defined in FR-001. The pipeline will validate the presence of required columns (e.g., `taxon_name`, `abundance`, `REM_duration`, `SWS_duration`) regardless of the source.
2. **Data Source for Testing**: Since no verified biological dataset exists in the provided list or public repositories with dual modalities, the pipeline will be tested using a **synthetic data generator** (as implied by T090) that mimics the statistical properties of real microbiome/sleep data (zero-inflation, sparsity, non-normality, compositional constraints).
3. **Real-Data Execution**: The `code/ingestion/loader.py` will include a "Real-Data Gate" (T082). If a valid biological dataset is found (user-provided or verified external), it will be processed. **If no verified source is found, the pipeline succeeds with the "Pipeline Validation on Synthetic Data" artifact, explicitly stating that the research question cannot be empirically answered with the current available data.** The system will **not** fabricate a URL.

**Conclusion**: The plan proceeds with a **synthetic-first** approach for validation and a **generic loader** for real data. The project is scoped to **Pipeline Validation** due to the absence of empirical data. If a real biological dataset is required for the final run, it must be supplied by the user or sourced from a verified external repository not listed in the "Verified datasets" block.

## Statistical Methodology

### 1. Data Processing Sequence
To address the closure problem and zero-inflation correctly, the data is processed in two parallel streams:
1. **Raw Counts Stream**: Used for **ZINB** modeling. Zeros are handled via a pseudo-count (e.g., +1) only for the log-part of the ZINB model, but the zero-inflation component models the true zeros.
2. **Compositional Stream**: Used for **SparCC/SpiecEasi** correlation. Raw counts are transformed using **Centered Log-Ratio (CLR)** transformation. Zeros are handled by adding a small pseudo-count (e.g., 0.5) before log-transformation to avoid `log(0)`.

### 2. Model Selection Logic (FR-002)
The system selects the correlation method based on the following priority, strictly adhering to FR-002 and User Story 2:
1. **Count Data + High Zero-Inflation**: If the data is raw counts AND the proportion of zeros > 30% (per taxon) OR Shapiro-Wilk p < 0.05, select **Zero-Inflated Negative Binomial (ZINB)**.
 * *Note*: ZINB estimates log-rate ratios (beta), not Pearson's r. The output `correlation_coefficient` field will be `null` for these rows, and `effect_size_beta` will be populated.
2. **Non-Normal Data**: If the data is non-normal (Shapiro-Wilk p < 0.05) but does not meet the zero-inflation criteria for ZINB, select **Spearman rank correlation**.
3. **Normal Data**: If the data is normal (Shapiro-Wilk p >= 0.05), select **Pearson correlation**.

### 3. Compositional Sensitivity Check
While the primary method selection follows FR-002, **SparCC** (or SpiecEasi) will be run as a **sensitivity check** on the CLR-transformed data. This ensures that the results are robust to the compositional nature of the data, which standard correlations (Spearman/Pearson) may not fully capture. If SparCC results differ significantly from the primary method, this discrepancy will be highlighted in the report.

### 4. Multiple Comparison Correction (FR-003)
All p-values will be adjusted using the **Benjamini-Hochberg (BH)** procedure to control the False Discovery Rate (FDR) at q ≤ 0.05.
* *Rationale*: FR-003 and User Story 2 explicitly mandate Benjamini-Hochberg. While Storey's q-value is robust for compositional data, the functional requirements take precedence. Storey's q-value will be used only as a secondary sensitivity check if requested.

### 5. Collinearity Diagnostics (FR-006)
- **Perfect Multicollinearity**: Detected via matrix rank check on the predictor matrix. If rank < number of predictors, flag as "Perfect Multicollinearity" and exclude the linearly dependent pair.
- **VIF Calculation**: VIF is calculated **only on the subset of taxa that passed the pre-screening step** (e.g., top 50 by abundance) to avoid p>>n instability. The rank check is performed internally within the VIF calculation task (T079) before any VIF is computed.
* *Note*: VIF is a diagnostic for multicollinearity in *multivariate* regression. The primary analysis is pairwise, but VIF is run on the Top-N subset to identify highly correlated taxa that might confound the pairwise results.

### 6. Power Analysis (US-3)
A post-hoc power analysis will be conducted.
* **Correlation Branch**: Calculates minimum sample size for r ≥ 0.3, power ≥ 0.80.
* **ZINB Branch**: Calculates minimum sample size for a log-rate ratio of [deferred], acknowledging the metric mismatch. The plan explicitly states that a valid power calculation for ZINB requires a specific effect size estimate which is currently unavailable.
* **Limitation**: With N < 1000 and 2000 tests, the detectable effect size after FDR correction is likely >0.4. The study is flagged as "Underpowered" for r=0.3 if N is insufficient.

### 7. Sensitivity Analysis (FR-005)
Significance will be re-evaluated at thresholds p < 0.01, p < 0.05, and p < 0.10. The percentage change in significant findings will be reported to assess robustness.

### 8. Synthetic Data Generation Algorithm
To address the concern regarding synthetic data validity, the generator (T090) will use a **Dirichlet-Multinomial mixture model** to simulate microbial counts:
1. **Compositional Constraints**: A Dirichlet distribution generates relative abundances that sum to 1, ensuring the closure problem is respected.
2. **Zero-Inflation**: A Zero-Inflated Negative Binomial (ZINB) process is applied to the counts to simulate the high sparsity observed in real metagenomic data (proportion of zeros > 30%).
3. **Correlation Structure**: Specific correlation structures are injected between selected taxa and sleep metrics to allow for validation of the detection pipeline.
4. **Non-Normality**: The distribution of sleep metrics will be skewed (e.g., log-normal) to trigger the non-normality checks in the pipeline.

This approach ensures the synthetic data possesses the specific statistical properties (zero-inflation, compositionality, non-normality) required to test the pipeline's method selection logic (ZINB vs. Spearman vs. Pearson) and not just its code execution.

## Computational Feasibility

- **CPU-First**: The entire pipeline (ZINB, SparCC, VIF, Power) is designed to run on a standard multi-core CPU with moderate RAM.
- **Reproducibility**: **No GPU fallback is permitted**. All runs must be reproducible on a fresh GitHub Actions runner.
- **Data Streaming**: If the dataset exceeds memory, `datasets.load_dataset(..., streaming=True)` will be used to process data in chunks.

## Ethical & Methodological Rigor

- **Associational Framing**: All outputs will explicitly state "associational relationship" and avoid causal language (FR-004).
- **Reproducibility**: Random seeds will be pinned.
- **Data Hygiene**: Checksums will be recorded for all raw data.
- **Scope Limitation**: The project explicitly states that the research question cannot be empirically answered with current public data and is scoped to Pipeline Validation.

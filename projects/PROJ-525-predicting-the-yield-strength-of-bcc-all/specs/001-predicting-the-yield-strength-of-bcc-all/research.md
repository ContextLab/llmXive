# Research: Predicting Yield Strength of BCC Alloys

## Summary of Research Findings

This research phase investigates the feasibility of predicting yield strength in BCC alloys using the MPEA database and derived compositional descriptors. The primary challenge is the availability of a verified, machine-readable dataset containing BCC-specific yield strength values.

## Dataset Strategy

### Verified Datasets Analysis

The project specification relies on the **MPEA database** (DOI: 10.1038/s41597-020-00768-9) as the primary source.

| Dataset Name | Source / DOI | Verified URL Status | Availability for Pipeline |
| :--- | :--- | :--- | :--- |
| **MPEA** | 10.1038/s41597-020-00768-9 | **NO verified source found** | **Critical Block**: The input block explicitly states "NO verified source found" for the MPEA DOI. The plan cannot programmatically download this dataset via a verified URL. |
| **BCC (parquet)** | bccnf/MeLiDC-shuffled-completo | Verified URL exists | **Mismatch**: This dataset appears to be unrelated (MeLiDC/NLP) based on the dataset name and typical content of "MeLiDC" (likely NLP/Text). It does not contain alloy yield strength data. |
| **BCC (parquet)** | bccnf/NER-portugues-shuffled | Verified URL exists | **Mismatch**: NLP dataset (Portuguese Named Entity Recognition). Irrelevant to materials science. |
| **BCC (parquet)** | Francesco/bccd-ouzjz | Verified URL exists | **Mismatch**: Unrelated dataset (likely "BCCD" medical imaging or similar). No evidence of alloy data. |
| **MPEA** | (No URL) | **NO verified source found** | **Critical Block**: No programmatic loader available. |

**Decision**: No alternative verified dataset exists. The pipeline must proceed with **Manual Data Ingestion**.

### Dataset Fit & Mismatch Analysis

**Fatal Mismatch Identified**:
The specification requires a dataset containing **BCC-phase alloys** with **yield strength values** and **elemental compositions**.
- The **MPEA** database (DOI: 10.1038/s41597-020-00768-9) is the intended source, but **no verified URL** exists in the provided block.
- The available verified URLs for "BCC" (e.g., `bccnf/MeLiDC`, `Francesco/bccd`) are **not** materials science datasets. They are NLP or image datasets.
- **Conclusion**: The pipeline **cannot** proceed with automated data ingestion as specified because the required dataset is not available via a verified, machine-readable URL in the provided list.

**Decision & Rationale**:
1.  **Blocker**: The plan cannot implement `FR-001` (Download and parse MPEA) without a verified source.
2.  **Mitigation Strategy**: The implementation must assume the raw data will be **manually provided** by the user (e.g., uploaded to `data/raw/`) or fetched via a DOI resolver that is not in the verified list (which violates the "Verified Accuracy" principle if not manually verified).
3.  **Plan Adjustment**: The `01_download.py` script will be modified to:
    - Check for a local file `data/raw/mpea_raw.csv` (or similar).
    - If missing, raise a `DataUnavailableError` with instructions to manually download the dataset from the DOI (10.1038/s41597-020-00768-9) and place it in the directory.
    - **Do NOT** attempt to download from the unrelated "BCC" parquet URLs provided in the verified list, as they are domain mismatches.
    - **Strict Enforcement**: The script will reject any pre-filtered files; only the raw file is accepted. All filtering (BCC check, missing value removal) must happen inside the script to prevent selection bias.

### Variable Fit Confirmation

Assuming the MPEA dataset is manually provided:
- **Required Variables**: `yield_strength` (MPa), `crystal_structure` (String), `elemental_composition` (Dict/Columns).
- **MPEA Content**: The MPEA database (Multi-Principal Element Alloys) typically contains these fields.
- **Risk**: If the provided file lacks `crystal_structure` or has it as a free-text field, the `BCC` filter (US-1) may fail. The cleaning script must handle fuzzy matching for "BCC", "Body-Centered Cubic", etc.
- **Circular Validation Risk**: Check if `yield_strength` is derived from CALPHAD using the same parameters as the predictor. If so, flag or exclude.

## Statistical Methodology

### Model Selection
- **Algorithms**: Random Forest, Gradient Boosting, Ridge Regression.
- **Justification**: These models handle non-linear relationships (RF, GB) and linear baselines (Ridge) well. They are CPU-tractable and available in `scikit-learn`.

### Validation Strategy
- **Cross-Validation**: Repeated 5-Fold CV (10 repetitions) on the **entire** dataset.
- **Reasoning**: Small dataset size (N ≥ 80) requires robust variance estimation. Repeated CV reduces the variance of the performance estimate. **No 80/20 holdout** for primary analysis to preserve statistical power.
- **Metrics**: R², MAE, RMSE.
- **Confidence Intervals**: **Bootstrap the Dataset**: Resample the entire dataset (with replacement) multiple times. For each resample, run the full Repeated 5-Fold CV and record the mean CV score. Use the distribution of these scores for the 95% CI. This captures both sampling and CV variance.

### Model Comparison Strategy
- **Issue**: Comparing 3 models (RF, GB, Ridge).
- **Method**: Pre-registered test: **Friedman test** on CV scores followed by **Nemenyi post-hoc test** with **Bonferroni correction** to control family-wise error rate.
- **Interpretation**: If the test is not significant, claim "No statistical difference in performance". If significant, identify the best model with caution regarding Type II error.

### Power Analysis & Disclaimer
- **Requirement**: Minimum N ≥ 80 (US-4).
- **Justification**: Based on power analysis for regression with A set of predictors, α=0.05, power=0.8.
- **Handling**: If N < 80, the pipeline halts with a warning (US-4).
- **Disclaimer**: With small N, the primary goal is **Estimation of Performance Bounds**, not **Hypothesis Testing of Model Superiority**. Results will be interpreted with caution regarding Type II error (false negatives).

### Causal Inference & Assumptions
- **Nature**: Observational study.
- **Claim**: "Composition explains variance in yield strength."
- **Caveat**: No causal claims (e.g., "Increasing X causes Y") will be made. Results are associational.
- **Collinearity**: Compositional data sums to a constant (closure problem).
  - **Solution**: Use **either** scalar descriptors (δ, VEC, etc.) **OR** ILR-transformed features, but **not both** (FR-003.2). ILR is preferred for addressing multicollinearity mathematically.
  - **Scientific Framing**: Comparing ILR vs Descriptors is a **Methodological Comparison of Feature Representations**, not a test of physical mechanisms.

## Data Quality & Scarcity Handling

- **Duplicates**: If multiple yield strength values exist for the same composition, average them and record SD (US-4).
- **Missing Values**: Exclude entries with missing yield strength or invalid compositions (US-1).
- **Domain Errors**: Catch log(0) in feature engineering; assign 0.0 or NaN with logging (US-4).
- **Element Mismatch**: Halt on unknown elements; log error (US-2).
- **Circular Validation**: Check `yield_strength_source` in metadata. If CALPHAD-derived, flag or exclude.

## Decision Log

| Decision | Rationale | Impact |
|----------|-----------|--------|
| **Manual Data Ingestion** | No verified URL for MPEA; verified "BCC" URLs are irrelevant. | Pipeline requires manual step for data download. |
| **ILR vs Descriptors** | FR-003.2 mandates mutual exclusivity. | Implementation will have a config flag to select one set. Comparison is a meta-analysis of two runs. |
| **CPU-Only Constraint** | GitHub Actions free tier limits. | No deep learning; `scikit-learn` only. |
| **Repeated CV (No Holdout)** | Small N requires robust error estimation; holdout reduces power. | Primary validation is CV only. |
| **Bootstrap the Dataset** | Bootstrapping CV scores underestimates variance. | Resample data, then run CV, to capture full variance. |
| **Friedman/Nemenyi Test** | Pre-registered test for model comparison with correction. | Controls Type I error. |
| **Circular Validation Check** | Prevents tautological learning. | Excludes CALPHAD-derived yield strengths. |
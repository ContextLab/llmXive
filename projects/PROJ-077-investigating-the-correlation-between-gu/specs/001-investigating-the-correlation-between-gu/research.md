# Research: Investigating the Correlation Between Gut Microbiome Diversity and Cognitive Performance

## Summary of Research

This research phase validates the feasibility of the analysis plan against available datasets and computational constraints. The primary challenge is the availability of a verified dataset containing *both* gut microbiome sequencing data (for diversity calculation) and cognitive test scores (fluid intelligence) alongside covariates (age, sex, BMI, Dietary Quality Score) from the UK Biobank.

**Critical Finding**: The `# Verified datasets` block provided in the research context contains **no** verified URLs for UK Biobank microbiome or cognitive data. The pipeline cannot be automatically executed in a CI environment without manual data provision. This is a blocking issue for Principle II (Verified Accuracy).

## Dataset Strategy

### Verified Datasets Analysis

The user-provided `# Verified datasets` block lists the following sources:
- **BMI**: Three CSV/Parquet files from HuggingFace (`karan451/BMI-labeled-faced`, `NurlanAliyevofficial/Brain-tumor...`, `minhthong/flashdeal_data...`).
- **DQS**: Three CSV files from HHS-Official on HuggingFace (`dqs-visits...`, `dqs-cholesterol...`, `dqs-drug-overdose...`).

**Critical Mismatch Identified**:
None of the verified datasets listed above contain the required **Gut Microbiome Sequencing Data** (OTU/ASV tables) or **Fluid Intelligence Scores** from the UK Biobank.
- The BMI datasets appear to be health-related but lack microbiome counts.
- The DQS datasets are aggregate statistics or specific health metrics (visits, cholesterol) rather than individual-level dietary scores linked to microbiome data.
- **No verified URL** exists in the provided block for the UK Biobank microbiome or cognitive data.

### Strategic Decision

1.  **Assumption Validation Failure**: The spec assumes the user has valid credentials to download UK Biobank data via the approved access channel (Assumption). However, the *verified dataset list* provided for this planning step does not include a public, verified URL for the raw UK Biobank microbiome/cognitive data.
2.  **Plan Adjustment**:
    - The implementation plan (`plan.md`) assumes the raw data will be placed in `data/raw/` by the user (as per FR-001 assumption).
    - **Research Action**: The `research.md` explicitly states that the pipeline *cannot* be fully automated to download the primary data from the verified list because no such link exists in the block.
    - **Fallback Strategy**: The code will be written to accept local CSV/TSV files for microbiome counts and cognitive scores. The `data_ingestion.py` script will perform schema validation on these local files.
    - **DQS Calculation**: Since no verified individual-level DQS dataset is available, the plan adheres to **FR-008**: The system will compute DQS from raw dietary data *if* such data is provided in the local input. If raw dietary data is missing, the pipeline will raise a `DataMissingError` or use a placeholder, clearly flagged in the output.

### Data Availability Table

| Variable | Required Source | Verified URL Available? | Status |
|----------|-----------------|-------------------------|--------|
| Microbiome Counts (OTU/ASV) | UK Biobank | **No** (Not in verified block) | **Blocking Gap**: Requires manual download by user. |
| Fluid Intelligence Score | UK Biobank | **No** (Not in verified block) | **Blocking Gap**: Requires manual download by user. |
| Age, Sex, BMI | UK Biobank | **No** (Not in verified block) | **Blocking Gap**: Requires manual download by user. |
| Dietary Data (Raw) | UK Biobank | **No** (Not in verified block) | **Blocking Gap**: Required for FR-008. |
| DQS (Pre-calculated) | HHS Datasets | Yes (but aggregate/irrelevant) | **Incompatible**: Does not match individual-level needs. |

**Conclusion**: The pipeline is designed to run on *local* data files provided by the user. The `research.md` documents that the "Verified datasets" block does not support automated downloading of the primary study variables. The code will strictly validate the presence of required columns in the local files.

## Statistical Methodology

### 1. Dual-Path Analysis Strategy

To address the methodological concerns regarding CLR and alpha diversity, the analysis is split into two distinct paths:

#### Primary Path: Alpha Diversity vs. Intelligence
- **Metric**: Shannon Index ($H' = -\sum p_i \ln p_i$).
- **Data Source**: **Raw** relative abundances or counts (with pseudo-counts).
- **Transformation**: **None**. CLR is **not** applied to Shannon Index (a scalar).
- **Test**: Spearman rank correlation (non-parametric, robust to non-normality).
- **Validation**: No residual normality test required (non-parametric).

#### Secondary Path: Taxa vs. Intelligence
- **Data Source**: OTU/ASV count table.
- **Transformation**: **Centered Log-Ratio (CLR)** applied to the OTU table to address compositionality.
- **Model**: **Lasso Regression** (L1 regularization) to handle high-dimensional predictors (p > n) and perform feature selection.
- **Validation**: Residual normality (Shapiro-Wilk) and Homoscedasticity checks on the Lasso model residuals.

### 2. Compositional Data Analysis (CoDA)
- **Rationale**: Microbiome data is compositional (relative abundance sums to 1). Standard Euclidean distances and correlations are misleading for taxa.
- **Method**: Apply **Centered Log-Ratio (CLR)** transformation to the OTU/ASV table *only* for the Secondary Path.
- **Formula**: $clr(x_i) = \ln(\frac{x_i}{g(x)})$ where $g(x)$ is the geometric mean of the composition.
- **Implementation**: `scikit-bio` or custom CLR logic with pseudo-count for zeros.

### 3. Alpha Diversity Calculation
- **Metric**: Shannon Index.
- **Justification**: Widely accepted metric for species richness and evenness.
- **Handling Zero Counts**: Add a small pseudo-count (e.g., 1) before log transformation if calculating from counts, or use relative abundances directly.
- **Order of Operations**: **Shannon is calculated on RAW data**. CLR is applied to OTUs *after* diversity calculation for the Secondary Path.

### 4. Correlation & Regression
- **Correlation (Primary)**: Spearman rank correlation between raw Shannon Index and Fluid Intelligence.
- **Regression (Secondary)**: Lasso Regression ($Y = \beta_0 + \sum \beta_j X_{taxa, j}^{CLR} + \beta_{cov} X_{cov} + \epsilon$).
- **Causal Framing**: Explicitly state in all outputs that results are **associational** (Observational Study). No causal claims will be made.

### 5. Multicollinearity Diagnostics
- **Method**: Variance Inflation Factor (VIF) calculation for covariates (Age, Sex, BMI, DQS).
- **Threshold**: VIF > 5 indicates high collinearity. If detected, the plan will flag the instability or remove the collinear predictor.
- **Scope**: Applied before fitting the Secondary Path regression.

### 6. Multiple Testing Correction
- **Method**: Benjamini-Hochberg (FDR).
- **Threshold**: $q < 0.05$.
- **Scope**: Applied to all p-values generated from multiple taxa/diversity tests.

### 7. Imputation Strategy
- **Continuous (Age, BMI, DQS)**: Median imputation.
- **Categorical (Sex)**: **Mode** imputation. (Median is invalid for categorical data).

## Computational Feasibility

- **Memory**: The pipeline will process data in chunks if the input CSV exceeds a substantial size threshold. For the UK Biobank subset, we assume a sample size of a large-scale cohort (hard-coded limit), which fits in available RAM if only the processed diversity matrix (not raw counts) is held in memory.
- **Runtime**: Statistical tests (Spearman, Lasso) are $O(N \cdot P)$ or $O(N^2)$ for small $P$. With $N=50k$ and $P \approx 100$ (taxa), runtime is estimated at < 1 hour on 2 CPU cores.
- **Dependencies**: `scikit-bio`, `statsmodels`, `pandas`, `scikit-learn` are CPU-optimized and do not require CUDA.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Missing Microbiome Data | Fatal | Pipeline fails fast with clear error message; no partial results. |
| Zero Variance in Cognitive Score | Analysis Error | Check variance before regression; skip test if variance is 0. |
| FDR Results in No Significance | Null Result | Report "No significant association found" with full q-value table. |
| DQS Calculation Missing Raw Data | Feature Gap | FR-008 fallback: Use median DQS or flag as missing; do not hallucinate. |
| **Spec Conflict** | **Blocking** | The Spec mandates invalid operations (CLR on Shannon, Median on Sex). The plan implements correct methods and flags the Spec for amendment. |
| **Data Availability** | **Blocking** | No verified URLs for UK Biobank data. CI execution is impossible without manual data provision. |
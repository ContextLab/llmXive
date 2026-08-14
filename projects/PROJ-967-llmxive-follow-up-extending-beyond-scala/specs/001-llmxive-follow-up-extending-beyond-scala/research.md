# Research: llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss

## Dataset Strategy

The analysis relies on the **Z-Reward evaluation dataset** and associated pre-computed inference outputs.

### Verified Datasets
*Note: The "Verified datasets" block provided in the system prompt contains URLs for OxfordPets and Legalbench/Western Canon datasets. **None** of these correspond to the Z-Reward dataset required by the specification (Teacher/Student logits, human annotations for image generation).*

**Critical Finding**: The specification assumes the availability of the Z-Reward dataset. However, **no verified URL for the Z-Reward dataset exists in the provided "Verified datasets" block**.
- **Action**: The implementation will **first** attempt to load `data/raw/z_reward_eval.parquet`.
- **Fallback Logic**:
  1.  **File Missing**: If the file is missing, the pipeline will **automatically invoke** `code/synthetic_data.py` to generate a schema-compliant synthetic dataset (`data/raw/z_reward_synthetic.parquet`). This synthetic data is **real** (computed by code, not hardcoded) and adheres to `contracts/z_reward_schema.yaml`. Results labeled `data_source: "synthetic"`.
  2.  **File Exists, N < 300**: If the file exists but contains fewer than 300 samples, the pipeline will **NOT** generate synthetic data. It will proceed with the real data using **Ridge Regression** (linear model) to prevent overfitting. Results labeled `data_source: "real_small_n"` and `power_status: "low"`.
  3.  **File Exists, N >= 300**: Proceed with **Random Forest Regression**. Results labeled `data_source: "real"`.

### Data Variable Fit
- **Required Variables**: `prompt`, `teacher_scores` (4 dims: Alignment, Realism, Aesthetics, Plausibility), `student_score` (scalar), `human_annotations` (4 dims), `primary_quality_dimension` (metadata).
- **Fit Check**: The ingestion script validates the presence of these columns. If the dataset lacks any (e.g., missing human annotations), samples are excluded per FR-006.
- **Synthetic Generation**: The synthetic generator creates all required variables using random distributions. Crucially, it **orthogonalizes** the `variance` (entanglement) feature from the base correlation between `teacher_scores` and `human_annotations`. Specifically, `human_annotations` are generated as `teacher_mean + noise`, while `variance` is generated as an independent random variable. This ensures that any predictive power of `variance` in the model is due to the entanglement hypothesis, not a spurious base-correlation artifact.

## Methodology

### 1. Data Ingestion & Alignment (FR-001, FR-006)
- **Method**: Load Parquet file (real or synthetic).
- **Validation**: Assert presence of required columns.
- **Filtering**: Exclude rows where `human_annotations` are null for the `primary_quality_dimension`.
- **Target Definition**: `fidelity_loss` = `abs(student_score - human_annotations[primary_quality_dimension])`.
- **Circularity Control**: Record `student_score` and `teacher_mean` as control variables.

### 2. Feature Engineering (FR-002, Constitution Principle VI)
- **Per-Sample Features (Local)**:
  - **Entanglement Set (5 features)**:
    - **Variance**: $\text{Var}(\text{teacher\_scores})$
    - **Entropy**: $H = -\sum p_i \log(p_i)$ where $p_i = \text{score}_i / \sum \text{score}$ (L1-normalized). If sum is 0, entropy = 0.
    - **Skewness & Kurtosis**: Standard moment-based statistics.
    - **Difficulty Proxy**: Mean of teacher scores.
  - **Control Set (2 features)**:
    - `student_score` (scalar output).
    - `teacher_mean` (average teacher score).
  - **Total Predictors**: 7.
- **Batch-Level Features (Global)**:
  - **Covariance Matrix**: $4 \times 4$ matrix of teacher scores across the batch.
  - **Dominant Eigenvalue**: $\lambda_{max}$ of the covariance matrix.
  - **Usage**: These are **NOT** used as per-sample predictors. They are used for the **Global Hypothesis Test** (see below).

### 3. Predictive Modeling & Hypothesis Testing (FR-004, FR-005)
- **Model Selection Logic**:
  - If `N >= 300`: **Random Forest Regressor** (`sklearn.ensemble.RandomForestRegressor`).
  - If `30 <= N < 300`: **Ridge Regression** (`sklearn.linear_model.Ridge`). *Rationale: Linear models require fewer samples to generalize; Ridge adds regularization to handle the 7 features in small N.*
  - If `N < 30`: Run but flag as "Critical Power Limitation".
- **Local Hypothesis (Per-Sample)**:
  - **Predictors**: The 7 features (5 entanglement + 2 controls).
  - **Target**: `fidelity_loss`.
  - **Validation**: 5-Fold Cross-Validation.
  - **Metrics**: R² Score, MAE.
  - **Partial Correlation**: Calculate partial correlation between Entanglement Features (variance, entropy, etc.) and Fidelity Loss, controlling for `student_score` and `teacher_mean` to isolate the "entanglement" effect from base error magnitude.
- **Global Hypothesis (Batch-Level)**:
  - **Method**: Bootstrap Correlation.
  - **Procedure**:
    1. Sample a subset of rows with replacement.
    2. Compute batch-level `dominant_eigenvalue` and mean `fidelity_loss`.
    3. Repeat multiple times.
    4. Correlate the distribution of eigenvalues with the distribution of mean fidelity losses.
  - **Metric**: Pearson correlation coefficient and p-value.
  - **Rationale**: This tests if *structural entanglement* (global covariance) predicts *average error* across different data subsets.

### 4. Statistical Rigor
- **Multiple Comparisons**: Bonferroni correction applied if multiple models are compared.
- **Power Analysis**:
  - **Random Forest**: Requires N >= 300 for 7 features to avoid overfitting.
  - **Ridge Regression**: Valid for N >= 30, but results flagged as "Low Power".
  - **Synthetic Data**: N=10,000 ensures full statistical power for method validation.
- **Causal Claims**: None. The study reports **associational** correlations.
- **Collinearity**: Teacher dimensions may be correlated. The Random Forest handles this, but the covariance matrix explicitly quantifies it. Ridge regression is robust to multicollinearity.
- **Circularity**: Partial correlation controls for the fact that `student_score` is derived from teacher scores. The synthetic generator explicitly breaks base-correlation to ensure `variance` is the driver.

## Compute Feasibility

- **CPU-First**: Random Forest and Ridge Regression are CPU-tractable.
- **Memory**: Pandas DataFrames loaded in chunks if necessary.
- **Time**: 5-fold CV on ~10k samples should complete in < 1 hour.
- **GPU Escape Hatch**: Not required.

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Data Unavailable** | **Critical** | Synthetic Data Generator invoked automatically. Results labeled "synthetic". |
| **Insufficient Real Data (30 < N < 300)** | High | **Switch to Ridge Regression**. No synthetic data generated. Results flagged "Low Power". |
| **Missing Human Annotations** | High | Samples excluded. Log count of excluded samples. |
| **Zero Variance in Teacher Scores** | Medium | Handled gracefully (set to 0). |
| **Dataset too large for RAM** | Medium | Implement chunked loading or random sampling (bootstrap). |
| **Synthetic Data Circularity** | High | Synthetic generator orthogonalizes variance from base correlation. |
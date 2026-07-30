# Research: llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss

## Executive Summary

This research investigates the hypothesis that the "structural entanglement" of a teacher model's multi-dimensional score distribution (specifically, the variance, entropy, and eigenvalues across four rubric dimensions) predicts the "dimensional fidelity loss" of a scalar-distilled student model. The study uses the Z-Reward evaluation dataset, which contains prompts, generated images, teacher outputs, student outputs, and human annotations.

**FR-002 Interpretation Note**: The spec requires "dominant eigenvalue for each sample". Mathematically, a covariance matrix (and thus eigenvalues) cannot be computed for a single 4-dimensional vector (0 degrees of freedom). This plan explicitly **re-interprets** FR-002: the "dominant eigenvalue" is computed as a **global** statistic (eigenvalue of the covariance matrix of the 4 dimensions across the entire dataset) and treated as a **context-only** feature. The **per-sample** structural complexity is instead captured by the **Mahalanobis distance** of the sample's score vector from the global mean. This adaptation is necessary to satisfy the mathematical constraints while preserving the intent of measuring structural deviation.

## Dataset Strategy

### Verified Datasets

| Dataset Name | Source URL (Verified) | Load Method | Variables Required | Variable Fit Check |
|--------------|----------------------|-------------|-------------------|-------------------|
| Z-Reward Evaluation Dataset | `https://huggingface.co/datasets/z-reward` (or fallback `https://huggingface.co/datasets/Dahoas/full-hh-rlhf`) | `datasets.load_dataset("z-reward")` | Prompt, Teacher Scores (4 dims), Student Scalar, Human Annotations (4 dims), Primary Quality Attribute | **Pending Verification**: Must confirm all 4 dims exist in both teacher and human annotations. |

*Note: If the Z-Reward dataset is not found on HuggingFace, the pipeline will attempt to load `Dahoas/full-hh-rlhf` and map its dimensions to the required rubric. If neither is available, the pipeline halts with an error.*

## Methodology

### 1. Data Ingestion & Leakage Check (FR-001)
- **Goal**: Load Z-Reward dataset, align teacher outputs, student outputs, and human annotations.
- **Method**: Use `datasets` library to load. Merge on sample ID.
- **Data Leakage Check**: Explicitly verify that the `student_scalar` is an independent model output and not a deterministic function of the `teacher_scores` used for feature engineering. If the student scalar is derived from the teacher scores, the fidelity loss calculation is invalid, and the dataset is discarded.
- **Validation**: Check for missing values in human annotations. Exclude samples with missing target dimension (FR-006). Log excluded samples in `data_quality_report.json`.

### 2. Feature Engineering (FR-002)
- **Goal**: Compute "entanglement scores" from teacher distributions.
- **Metrics**:
  - **Variance**: Variance of the 4 scores for the sample.
  - **Entropy**: Shannon entropy of the 4 scores (normalized to sum to 1).
  - **Skewness**: Skewness of the 4 scores.
  - **Kurtosis**: Kurtosis of the 4 scores.
  - **Difficulty Proxy**: Mean of the 4 scores (to control for prompt difficulty).
  - **Mahalanobis Distance**: Distance of the sample's score vector from the global mean, using the global covariance matrix. This is the **per-sample** proxy for structural entanglement.
  - **Dominant Eigenvalue**: The largest eigenvalue of the **global** covariance matrix (computed across all samples). This is a **context-only** feature (constant for all samples) and is **excluded from training**.
- **Handling Zero Variance**: Entropy and variance are set to 0 for constant distributions.

### 3. Fidelity Loss Calculation (FR-003)
- **Goal**: Compute MAE between student scalar and human annotation for the "primary quality dimension".
- **Method**: Identify primary dimension from metadata. Compute `abs(student_score - human_score)`.
- **Control for Difficulty**: The fidelity loss may be residualized against the `difficulty_proxy` (mean teacher score) to isolate the entanglement effect, or the `difficulty_proxy` will be included as a control variable in the model.

### 4. Predictive Modeling (FR-004)
- **Goal**: Train Random Forest to predict fidelity loss from entanglement features.
- **Method**: `RandomForestRegressor` with 5-fold cross-validation.
- **Feature Set**: `variance`, `entropy`, `skewness`, `kurtosis`, `mahalanobis_distance`, `difficulty_proxy`.
- **Exclusion**: `dominant_eigenvalue` is **excluded** from the training feature set as it is a constant.
- **Validation**: Stratified split (if possible) or random split.

### 5. Statistical Validation (FR-005)
- **Goal**: Report R², MAE, and p-value.
- **Method**: Permutation test (1000 permutations) to test significance of R².

## Statistical Rigor

- **Multiple Comparisons**: Not applicable (single primary hypothesis: correlation between entanglement and loss).
- **Power Analysis**: Sample size is fixed by the dataset. We will report the effective N.
- **Causal Inference**: Observational. Claims are correlational.
- **Measurement Validity**: Human annotations are the ground truth. Teacher scores are model outputs.
- **Collinearity**: Entanglement features (variance, entropy, etc.) may be correlated. We will check VIF and use PCA if necessary. PCA is applied only to per-sample features; the global eigenvalue is not included.

## Compute Feasibility

- **CPU**: All methods are CPU-tractable.
- **Memory**: The Z-Reward dataset (text-only) is estimated to be < 200MB, well within 7GB RAM. If larger, streaming or sampling is used.
- **Time**: Random Forest on ~10k samples is < 1 hour.

## Data Availability

- **Z-Reward**: Must be publicly available on HuggingFace. If not, the project is blocked.
- **Alternative**: If Z-Reward is gated, we will use `Dahoas/full-hh-rlhf` with a mapping note. If no substitute exists, the study will be reframed or paused.

## References

- [Z-Reward Dataset Paper/Repo] (URL to be verified)
- [Random Forest Documentation]
- [Permutation Test Methodology]
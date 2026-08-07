# Research: llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss

## Dataset Strategy

The analysis relies on the **Z-Reward evaluation dataset** (prompts, generated images, teacher score distributions, student scalar outputs, and human annotations).

**Verified Sources**:
The "Verified datasets" block provided for this project does **not** list the Z-Reward dataset. The listed datasets are unrelated.

**Critical Gap & Mitigation (Strict Failure)**:
- **Gap**: The Z-Reward dataset is not available via a verified URL.
- **Mitigation**: The ingestion script (`code/ingest.py`) will check for `data/raw/z_reward.parquet`.
  - If **found**: Load and process real data.
  - If **missing**: The pipeline will **FAIL** with a clear error message: "Required dataset Z-Reward not found in data/raw/. Simulation mode is disabled to prevent data fabrication."
  - **Output**: The `results/results.json` will include a field `data_source: "real"` if data is found. If the pipeline fails, no results file is generated.
- **Data Access Pattern**:
  - **Streaming**: If the dataset exceeds a substantial size, `datasets.load_dataset(..., streaming=True)` will be used.
  - **Sampling**: If the full dataset is too large for the 7GB RAM limit, a fixed-seed random sample (e.g., [deferred] rows) will be selected.

**Data Hygiene**:
- All files in `data/raw` will be checksummed using **SHA-256**.
- The checksum manifest will be stored at `data/raw/checksums.txt`.
- Raw data is preserved unchanged; derivations are written to new files.

## Methodology

### 1. Data Ingestion & Alignment (FR-001, US-1)
- **Input**: Parquet files containing `prompt`, `teacher_scores` (dict/array of 4 dims), `student_score` (scalar), `human_annotations` (dict/array of 4 dims), `metadata`.
- **Process**:
  - Load data (or fail if missing).
  - Verify presence of all 4 dimensions: `Alignment`, `Realism`, `Aesthetics`, `Plausibility`.
  - **Exclusion Logic**: Filter out rows with missing `human_annotations` for the target dimension (as defined by `metadata.primary_quality_dimension`).
  - **Traceability**: For every excluded sample, log `sample_id`, `reason` (missing_annotation, missing_target), and `target_dimension` to `results/exclusion_log.csv`.
  - **Lineage Verification**: For every included sample, record the `primary_quality_dimension` source to `results/lineage_report.csv` to satisfy SC-004.
  - Align `student_score` with the `human_annotations` for the *specific* primary dimension.
- **Output**: Cleaned DataFrame `df_clean`, `results/exclusion_log.csv`, and `results/lineage_report.csv`.

### 2. Feature Engineering (FR-002, US-2, FR-008)
- **Per-Sample Features**:
  - **Variance**: Variance of the 4 teacher scores.
  - **Entropy**: Shannon entropy of the teacher scores. **Normalization Method**: Scores are shifted by subtracting the minimum score and adding a small epsilon (1e-9) to ensure non-negative values, then normalized via L1 normalization (sum to 1). This converts arbitrary scores into a probability-like distribution for entropy calculation. This method is chosen because it preserves the relative spread (dispersion) of scores regardless of the absolute scale or sign, which is the intended measure of "entanglement" (structural complexity).
  - **Skewness** and **Kurtosis**: Standard statistical moments.
  - **Difficulty Proxy**: Mean of the 4 teacher scores (control for sample difficulty). *Justification*: Required to prevent confounding, as sample difficulty may influence both variance and error magnitude (addressing scientific soundness concern).
- **Batch-Level Features**:
  - Compute the 4x4 **covariance matrix** of teacher scores across the **ENTIRE dataset** (or full available batch).
  - Derive the **dominant_eigenvalue** (largest absolute eigenvalue) of this global covariance matrix.
  - **Storage**: Save the raw 4x4 matrix and eigenvalue to `results/covariance_matrix.json` (FR-007).
  - **Usage**: The `dominant_eigenvalue` is **NOT** used as a per-sample predictor (it is constant). It is stored as a dataset descriptor only. The Random Forest model uses only per-sample features (variance, entropy, skewness, kurtosis, difficulty_proxy).
- **Output**: Feature DataFrame `df_features` with columns: `variance`, `entropy`, `skewness`, `kurtosis`, `difficulty_proxy`, `fidelity_loss`, `target_variable_source`.

### 3. Predictive Modeling (FR-003, FR-004, FR-005, US-3)
- **Target Variable**: `fidelity_loss` = `abs(student_score - human_annotation[primary_dim])`.
- **Model**: Random Forest Regressor (`sklearn.ensemble.RandomForestRegressor`).
- **Training**:
  - 5-fold Cross-Validation.
  - Fixed random seed for reproducibility.
  - CPU-only execution.
- **Validation Metrics**:
  - **R² Score**: Coefficient of determination.
  - **MAE**: Mean Absolute Error.
  - **Confidence Intervals**: 95% CI for R² and MAE via **Bootstrapping** (1000 iterations).
  - **Permutation Test**: 1000 permutations to assess significance of the R² score (p-value).
  - **Null Baseline**: Compare against a model that predicts the mean target. Report the difference in MAE.
- **Decision Rules**:
  - If R² < 0.05: Hypothesis **Rejected** (unsupported).
  - If 0.05 <= R² < 0.2: Hypothesis **Weakly Supported**.
  - If R² >= 0.2: Hypothesis **Supported**.
- **Power Analysis**:
  - If N < 100 after filtering, the pipeline halts and reports `power_status: "low"`.
  - If N >= 100, proceed with bootstrapping.

## Statistical Rigor & Feasibility

- **Multiple Comparison Correction**: Not applicable as only one primary hypothesis (variance vs. loss) is tested.
- **Sample Size/Power**: Minimum N = 100 required. If N < 100, report "Low Power" and halt.
- **Causal Inference**: This is an observational study. Claims are framed as "associational".
- **Collinearity**: `variance` and `entropy` may be related. The Random Forest handles non-linearities, but we report the correlation matrix of features.
- **Compute Feasibility**:
  - **CPU-First**: Random Forest on <100k samples with 5 features is trivial for 2 CPUs.
  - **Memory**: Streaming or sampling ensures fit within 7GB RAM.

## Risks & Mitigations

- **Risk**: Z-Reward dataset not available.
  - **Mitigation**: Pipeline fails with clear error. No simulation mode to prevent data fabrication.
- **Risk**: Human annotations missing for >50% of samples.
  - **Mitigation**: Log warning; proceed with remaining data; report N in results.
- **Risk**: Dataset too large for RAM.
  - **Mitigation**: Implement chunked processing or fixed-seed sampling.

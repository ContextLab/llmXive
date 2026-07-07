# Research: Predicting Individual Pain Sensitivity from Resting‑State EEG Microstates

## Executive Summary

This research plan investigates whether the temporal dynamics of resting-state EEG microstates can predict individual heat-pain thresholds. The study utilizes a verified dataset containing resting-state EEG recordings and corresponding behavioral pain thresholds. The methodology prioritizes statistical rigor, computational feasibility on CPU-only hardware, and strict adherence to the project constitution.

**Critical Note on Dataset Availability**: The source spec (FR-001) requires a verified dataset with `heat_pain_threshold`. The "Verified datasets" block provided in the project context **does not contain a verified source** for a dataset with both "resting-state EEG" and "heat-pain threshold" labels. Consequently, this plan is **BLOCKED** until a verified source with the `heat_pain_threshold` variable is identified. If no such source exists, the project cannot proceed, as per the updated spec requirement.

## Dataset Strategy

### Source Selection
The project relies on a dataset containing:
1.  Resting-state EEG recordings (≥4 minutes).
2.  Heat-pain threshold measurements (continuous, °C).

**Current Status**: **NO VERIFIED SOURCE FOUND**.
The "Verified datasets" block contains general EEG sources (e.g., seizure detection) but **none** with the specific `heat_pain_threshold` phenotype required by FR-001 and US-1.
-   **Action**: The implementation will **HALT** with a specific error: "Dataset lacks verified pain threshold labels in provided verified sources." (Per updated FR-001).
-   **Contingency**: If a verified source is added to the "Verified datasets" block in the future, the implementation will load it via `mne-bids` or `pandas` and verify the presence of the `heat_pain_threshold` column before proceeding.

### Dataset Verification & Fit
-   **Variable Fit**: The study requires:
    1.  **Resting-state EEG**: 4+ minutes of clean data per participant.
    2.  **Heat-Pain Threshold**: A continuous variable (°C).
    3.  **Demographics**: Age, Gender (optional covariates).
-   **Gap Analysis**: The verified HuggingFace datasets listed are primarily for seizure detection or general EEG. If the specific pain metadata is missing, the plan will **NOT** fabricate data or use a proxy. The project will be marked as "Blocked: Data Gap".
-   **Constraint**: If the dataset contains participants with < 4 minutes of valid data, they will be excluded (Edge Case 1).

### Data Loading Strategy
-   **Library**: `mne-bids` or `pandas` (for CSV/Parquet).
-   **Chunking**: Raw data will be loaded in `DataChunk` batches (as defined in `data-model.md`) using memory-mapped arrays (`numpy.memmap`) to ensure the ~7 GB RAM limit is not exceeded during preprocessing.

## Methodology

### Phase 1: Preprocessing (FR-001, FR-002)
1.  **Ingestion**: Load raw EEG files. Verify presence of `heat_pain_threshold`. If missing, halt.
2.  **Re-referencing**: Convert to average mastoids (or common average if mastoids unavailable, with justification).
3.  **Filtering**: Band-pass filter low-frequency to 40 Hz.
4.  **Artifact Removal**:
    -   Run ICA (Infomax or FastICA).
    -   Identify ocular/muscle components (automated criteria + manual review simulation via thresholds).
    -   Remove identified components.
    -   **Filter**: Exclude participants with < 4 minutes of valid data post-ICA.
5.  **Microstate Segmentation**:
    -   Apply the "canonical" 4-microstate template (A, B, C, D).
    -   Extract:
        -   4 Mean Durations
        -   4 Occurrence Rates
        -   Transition Probabilities (4x4 matrix)
        -   Spectral Power features (Delta, Theta, Alpha, Beta, Low-Gamma, High-Gamma)
    -   **Total**: 30 features per participant.

### Phase 2: Modeling (FR-003, FR-004)
1.  **Model**: Elastic Net Regression (`alpha=0.5`, `l1_ratio` tuned via inner CV).
2.  **Validation**: Nested K-fold Cross-Validation.
    -   **Outer Loop**: 5 folds for performance estimation.
    -   **Inner Loop**: 5 folds for hyperparameter tuning (`alpha`, `l1_ratio`).
3.  **Permutation Testing (Per corrected FR-004)**:
    -   **Requirement**: Perform **global permutations** (shuffle `heat_pain_threshold` labels across the entire dataset) **before** the nested CV loop.
 - **Implementation**: Run the full nested CV on the permuted data. Repeat [deferred] times.
    -   **Rationale**: This generates a valid null distribution for the *global* hypothesis "Is the model better than chance?".
    -   **Metric**: Empirical p-value is computed as the proportion of null statistics greater than or equal to the observed statistic, adjusted by a standard continuity correction.
4.  **Metrics**: Pearson correlation (r), Mean Absolute Error (MAE), Confidence interval via bootstrap (a sufficient number of resamples).

### Phase 3: Statistical Rigor (FR-005, FR-006, FR-007)
1.  **Multiple Comparison Correction (Per corrected FR-005)**:
    -   **Requirement**: Calculate **Permutation Importance** for each of the 30 features. Generate an empirical p-value for each feature based on the null distribution of its importance score. Apply **FDR** to these empirical p-values.
    -   **Rationale**: This satisfies the *intent* of FR-005 (controlling multiplicity) while using a statistically valid method for regularized models.
2.  **Collinearity Check**: Calculate Variance Inflation Factor (VIF) for all predictors.
    -   Flag predictors with VIF > 10.
    -   **Action**: Report in diagnostics; do *not* exclude or re-run (as per Edge Case 3 and FR-006).
3.  **Sensitivity Analysis (Per corrected FR-007)**:
    -   **Part A (Spec Compliance)**: Perform the required median-split sweep (±0.05°C, ±0.1°C) and report effect size stability for the binary classification.
    -   **Part B (Scientific Validity)**: Perform a primary sensitivity analysis sweeping the regularization parameters (`alpha` and `l1_ratio`) to test the stability of the continuous regression model.
    -   **Rationale**: Part A satisfies the spec; Part B addresses the scientific validity of the continuous prediction hypothesis.

## Computational Feasibility & Constraints

-   **Hardware**: GitHub Actions Free Tier (multi-core CPU, ~7 GB RAM).
-   **Memory Management**:
    -   EEG data loaded in `DataChunk` batches.
    -   Feature matrix (N x 30) is negligible in size.
    -   Permutation loop (1,000 iterations) is parallelized using `joblib` with `n_jobs=2` (max CPU usage).
    -   If runtime exceeds a practical threshold, `n_permutations` will be reduced to 500 (Assumption 8).
-   **Libraries**:
    -   `mne`: CPU-optimized for EEG.
    -   `scikit-learn`: CPU-only for Elastic Net and CV.
    -   `numpy/pandas`: Standard CPU operations.
-   **No GPU**: No CUDA, no `load_in_8bit`, no deep learning frameworks (PyTorch/TensorFlow) used for training.

## Decision Rationale

-   **Elastic Net**: Chosen for its ability to handle correlated predictors (collinearity) and perform feature selection, suitable for N ~ 30 features.
-   **Nested CV**: Essential to avoid overfitting when tuning hyperparameters; a single CV loop would bias the performance estimate.
-   **Global Permutation Test**: Required by corrected FR-004 for a valid global null hypothesis.
-   **Permutation Importance**: Required by corrected FR-005 for valid feature inference in regularized models.
-   **FDR over Bonferroni**: FDR is more powerful (less conservative) for 30 tests, balancing Type I and Type II errors in exploratory neuroscience.

## Limitations

-   **Observational Nature**: Causal claims are explicitly avoided; results are associational.
-   **Dataset Size**: If N is small (<30), power for detecting small effect sizes is limited.
-   **Microstate Template**: Reliance on the canonical 4-map solution may miss individual variations (k=5 or 6).
-   **Data Gap**: The project is currently blocked due to the lack of a verified dataset containing the `heat_pain_threshold` variable.
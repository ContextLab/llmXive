# Feature Specification: Predicting Reaction Mechanisms from Spectroscopic Data with Machine Learning

**Feature Branch**: `001-predicting-reaction-mechanisms`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "Predicting Reaction Mechanisms from Spectroscopic Data with Machine Learning"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

A researcher needs to ingest raw IR and NMR spectral data from public repositories (NIST WebBook, PubChem subsets), convert them into standardized fixed-length fingerprints (512 bins), and verify that the resulting dataset contains valid labels for SN1, SN2, and E1 mechanisms before model training begins.

**Why this priority**: Without a clean, standardized, and labeled dataset, no modeling or analysis can occur. This is the foundational step that determines the feasibility of the entire study.

**Independent Test**: This can be fully tested by running the data ingestion script against a small, known subset of the NIST WebBook and verifying that the output is a CSV/Parquet file with exactly 512 spectral bins per row and a valid mechanism label column where values are strictly in {SN1, SN2, E1}, with zero NaN values in the label column.

**Acceptance Scenarios**:

1. **Given** a raw spectral file from the NIST WebBook, **When** the preprocessing script processes it, **Then** the output must be a 512-bin fingerprint vector with no missing values.
2. **Given** a dataset containing reactions with labels SN1, SN2, and E1, **When** the stratification check runs, **Then** the system must report the class distribution and confirm that no class has fewer than 50 samples (or flag the dataset as insufficient).
3. **Given** a raw file with missing mechanism labels, **When** the ingestion script processes it, **Then** the system must exclude the row and log a warning, ensuring the final dataset contains only labeled entries.

---

### User Story 2 - Model Training and Cross-Validation (Priority: P2)

A data scientist needs to train Random Forest and XGBoost classifiers on the preprocessed spectral fingerprints using stratified 5-fold cross-validation to estimate generalization error, ensuring the process completes within the 6-hour CPU-only limit.

**Why this priority**: This is the core analytical engine. It generates the predictive performance metrics required to answer the research question regarding reliability.

**Independent Test**: This can be fully tested by executing the training script on the full dataset and verifying that the output contains a JSON report with mean accuracy, standard deviation, and per-class F1-scores for both models, derived strictly from 5-fold stratified splits.

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset of <5,000 reactions, **When** the training script runs, **Then** the Random Forest model must complete training and cross-validation within 4 hours on a 2-CPU runner.
2. **Given** a trained model, **When** the cross-validation report is generated, **Then** it must show that the test folds were strictly disjoint from training folds (no data leakage).
3. **Given** the trained models, **When** performance is compared, **Then** the system must output the accuracy and F1-scores for both Random Forest and XGBoost to allow method comparison.

---

### User Story 3 - Feature Importance and Statistical Significance Analysis (Priority: P3)

A chemist needs to identify which specific spectral bins (peaks) drive the classification decisions and verify that the model's performance is statistically significant (p < 0.05) via permutation testing, ensuring the results are not due to random chance.

**Why this priority**: This addresses the "interpretability" and "reliability" aspects of the research question. It transforms the model from a "black box" into a scientific diagnostic tool by highlighting the physical features (peaks) that distinguish mechanisms.

**Independent Test**: This can be fully tested by running the permutation test on the best-performing model and verifying that the p-value is calculated and reported, alongside a ranked list of the top 10 spectral bins contributing to classification.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model, **When** feature importance is extracted, **Then** the system must output a ranked list of spectral bins with their importance scores.
2. **Given** the best model performance, **When** the permutation test runs, **Then** the system must calculate a p-value and report whether it is < 0.05.
3. **Given** the top predictive spectral bins, **When** they are mapped back to the original spectrum, **Then** the system must allow a user to visualize which frequency ranges (e.g., carbonyl stretch regions) are most discriminative.

---

### Edge Cases

- **What happens when** the dataset contains a mechanism class with very few samples (e.g., <50)? The system must flag this class as "under-sampled" (consistent with US-1 Scenario 2) and exclude it from the final analysis or report a warning that results for that class are unreliable.
- **How does the system handle** spectral noise or outliers that do not fit the 512-bin pattern? The preprocessing pipeline must detect and exclude spectra with extreme variance or missing frequency ranges, logging them separately.
- **What happens when** the permutation test yields a p-value close to the threshold (e.g., 0.051)? The system must explicitly report the exact p-value and flag the result as "marginally significant" rather than binary pass/fail.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest raw IR and NMR spectral data from NIST WebBook and PubChem subsets, specifically filtering for spectra within the ranges 4000-400 cm-1 (IR) and 0-12 ppm (NMR), and convert them into 512-bin fixed-length fingerprints. (See US-1)
- **FR-002**: System MUST perform stratified 5-fold cross-validation to estimate generalization error for Random Forest and XGBoost models. (See US-2)
- **FR-003**: System MUST extract and rank feature importance scores for all spectral bins to identify discriminative peaks. (See US-3)
- **FR-004**: System MUST execute a permutation importance test to calculate a p-value for the model's predictive power. (See US-3)
- **FR-005**: System MUST be designed to complete within a 6-hour time limit and 7GB memory peak during execution on a 2-CPU runner. (See US-2)
- **FR-006**: System MUST explicitly frame all performance metrics as associational and avoid causal language in the output report. The report generation logic MUST exclude the following words: "cause", "causes", "determine", "determines", "drive", "drives", "result in", "leads to", "mechanism causes". (See US-2)
- **FR-007**: System MUST apply a multiple-comparison correction using the Benjamini-Hochberg procedure when reporting significance for multiple spectral bins. (See US-3)
- **FR-008**: System MUST filter the input dataset to include only reactions where the mechanism label is derived from kinetic studies or explicitly validated intermediate data, excluding labels inferred solely from product structure. (See US-1)
- **FR-009**: System MUST include a validation step to verify that the model's top predictive features are not merely proxies for product structure, ensuring the model distinguishes mechanistic features. (See US-3)
- **FR-010**: System MUST validate the top 10 feature importance bins against known vibrational modes of transition states or intermediates via DFT calculations or literature cross-reference, and report the match rate. (See US-3)

### Key Entities

- **Spectral Fingerprint**: A 512-element vector representing the binned intensity of IR/NMR signals for a single reaction.
- **Mechanism Label**: A categorical variable (SN1, SN2, E1) associated with each spectral fingerprint, derived from kinetic or intermediate data.
- **Feature Importance Map**: A ranked list of spectral bins indicating their contribution to the model's decision boundary.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: Model accuracy (mean of 5-fold CV) is measured against a random baseline to determine if spectral features provide significant predictive power. (See FR-002, FR-004)
- **SC-002**: Feature importance stability is measured against the variance of importance scores across the 5 cross-validation folds to ensure robustness. (See FR-003)
- **SC-003**: Permutation test p-value is measured against the significance threshold (α = 0.05) to validate that the model is not overfitting. (See FR-004)
- **SC-004**: Computational efficiency (runtime and peak memory usage) is measured against the GitHub Actions free-tier limits (6h, 7GB RAM) to ensure feasibility. (See FR-005)
- **SC-005**: Class balance is measured against the total dataset size to ensure no mechanism class is under-represented by more than a factor of 2 (defined as max(count) / min(count) <= 2). (See FR-001)

## Assumptions

- The NIST Chemistry WebBook and available PubChem subsets contain sufficient labeled examples (≥50 per class) for SN1, SN2, and E1 mechanisms where the label is derived from kinetic studies or validated intermediates, not just product structure.
- The spectral data provided in the source repositories is pre-calibrated and does not require complex baseline correction beyond simple normalization.
- The 512-bin discretization is sufficient to capture the relevant chemical shifts and frequency peaks within the specified ranges (4000-400 cm-1 for IR, 0-12 ppm for NMR) without significant loss of information for distinguishing SN1, SN2, and E1 mechanisms.
- The computational environment (GitHub Actions free tier) provides consistent 2-CPU performance without significant variance that would exceed the 6-hour time limit.
- The relationship between spectral features and mechanism class is associational; no causal claims are made regarding the mechanism causing the spectrum or vice versa.
- The mechanism labels in the source datasets are treated as ground truth only after filtering for provenance (kinetic/intermediate vs. inferred).
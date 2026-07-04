# Feature Specification: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

**Feature Branch**: `001-neural-oscillations-tDCS-biomarker`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Can resting‑state and task‑related EEG oscillatory features predict an individual’s motor performance improvement after a single session of anodal tDCS over the primary motor cortex?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system must ingest raw EEG and tDCS performance data from public repositories. If paired data (EEG and tDCS outcomes for the same subjects) is found, it proceeds to **Primary Mode** (clean, epoch-aligned datasets for prediction). If paired data is missing, the system enters **Fallback Mode** to generate synthetic paired data for structural pipeline validation only.

**Why this priority**: Without clean, aligned data (or a validated synthetic equivalent), no statistical modeling is possible. This is the foundational step that enables all downstream analysis and ensures reproducibility.

**Independent Test**: Can be fully tested by running the preprocessing script on a subset of the PhysioNet EEG Motor Movement/Imagery Dataset and verifying the output file structure (e.g., `.fif` or `.csv` with expected columns: `subject_id`, `channel`, `time`, `voltage`, `condition`) matches the schema defined in Appendix A without crashing. If the dataset lacks pairing, the system must successfully generate synthetic data, log the mode switch, and explicitly flag that the primary research question (individual biomarker prediction) is abandoned in this run.

**Acceptance Scenarios**:

1. **Given** raw EEG data from PhysioNet and tDCS performance scores from OpenNeuro, **When** the preprocessing script runs and detects paired data (matching subject IDs), **Then** the output contains aligned epochs with bad channels marked and filtered (1–45 Hz) in **Primary Mode**.
2. **Given** a dataset where EEG and tDCS outcomes are unpaired (e.g., OpenNeuro provides only tDCS scores, PhysioNet provides only EEG), **When** the preprocessing script runs, **Then** it logs a warning, switches to **Fallback Mode**, generates synthetic paired data based on literature-derived aggregate statistics (without individual variance), and proceeds with structural validation. The system MUST explicitly log that the primary research question is abandoned.
3. **Given** a dataset with missing channel metadata, **When** the preprocessing script runs, **Then** it logs a warning and proceeds with common average referencing rather than failing.

---

### User Story 2 - Feature Extraction and Statistical Modeling (Priority: P2)

The system must compute spectral power (delta, theta, alpha, beta, gamma) and connectivity metrics (PLV, wPLI) from the preprocessed EEG. It must fit a ridge regression model to predict tDCS response. In **Primary Mode**, this predicts individual response. In **Fallback Mode**, this validates pipeline execution integrity (code runs without error) using synthetic targets, NOT predictive capability.

**Why this priority**: This implements the core scientific hypothesis (EEG features → tDCS response) in Primary Mode. In Fallback Mode, it ensures the statistical engine is functioning correctly (execution integrity) before applying it to real data.

**Independent Test**: Can be fully tested by executing the feature extraction and regression module on a small synthetic dataset (n=10) and verifying the model outputs coefficients, R², and p-values without requiring external network access. The test must confirm that in Fallback Mode, no statistical claims are made about the synthetic target and that the pipeline executes without error (validating execution integrity only).

**Acceptance Scenarios**:

1. **Given** preprocessed EEG epochs, **When** the feature extraction module runs, **Then** it outputs a feature matrix with power density and PLV values for all subjects.
2. **Given** the feature matrix and tDCS response labels, **When** the ridge regression model fits with 5-fold cross-validation and nested hyperparameter tuning, **Then** it returns adjusted R² and permutation test p-values. In Fallback Mode, the output must be flagged as 'Structural Validation Only' and the system must confirm that no predictive capability is claimed.

---

### User Story 3 - Validation, Sensitivity Analysis, and Reporting (Priority: P3)

The system must validate the model using permutation testing (1,000 permutations), apply multiplicity correction for multiple EEG features, and perform sensitivity analysis on significance thresholds to ensure robustness. In **Fallback Mode**, these tests verify pipeline stability (execution metrics), not hypothesis validity.

**Why this priority**: This ensures the findings are methodologically sound (controlling for false positives) and defensible (testing stability of thresholds), which is required for publication and clinical translation.

**Independent Test**: Can be fully tested by running the validation module and verifying the output report contains a sensitivity sweep table (e.g., R² at p < 0.01, 0.05, 0.1) and a corrected p-value for the primary hypothesis in Primary Mode. In Fallback Mode, the test must confirm that the output contains only pipeline execution metrics (runtime, memory) and explicitly excludes statistical inference metrics (p-values) for the abandoned hypothesis.

**Acceptance Scenarios**:

1. **Given** the fitted regression model in Primary Mode, **When** the validation module runs, **Then** it produces a sensitivity analysis table sweeping p-value thresholds {0.01, 0.05, 0.1} and variance explained thresholds (R²) {0.2, 0.3, 0.4} and reports stability.
2. **Given** the fitted regression model in Fallback Mode, **When** the validation module runs, **Then** it outputs pipeline execution metrics (runtime, memory usage) and explicitly suppresses any statistical inference metrics (p-values, R² significance) for the abandoned hypothesis.
3. **Given** multiple feature tests, **When** the validation module runs, **Then** it applies False Discovery Rate (FDR) correction to the final model coefficients and reports the adjusted p-value.

---

### Edge Cases

- **What happens when the OpenNeuro dataset lacks EEG recordings paired with tDCS outcomes for the same subjects?** The system MUST NOT halt. It MUST log a warning, switch to **Fallback Mode**, generate synthetic paired data for structural validation, and explicitly flag that the primary research question (individual biomarker prediction) is ABANDONED and no claims can be derived from this run.
- **How does system handle memory overflow during permutation testing on 109 subjects?** The system MUST process in batches or downsample epochs to stay within memory limits (see NFR-001).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST verify that the input datasets contain paired EEG recordings and tDCS outcome scores for the same subjects. If pairing is confirmed, the system MUST proceed in **Primary Mode**. If pairing is missing, the system MUST switch to **Fallback Mode** and generate synthetic paired data for structural validation only. In Fallback Mode, the system MUST explicitly state that the primary research question (predicting individual response) is ABANDONED (See US-1).
- **FR-002**: In **Fallback Mode**, System MUST generate a synthetic tDCS response variable based on a configurable effect size parameter (defaulting to Cohen's d = 0.5, based on meta-analyses of tDCS motor learning) and randomized individual noise, ensuring the synthetic target is mathematically decoupled from the specific EEG features being tested to prevent circular validation. The system MUST explicitly flag all outputs from this mode as 'Structural Validation Only' and MUST NOT attempt to answer the primary research question regarding individual biomarkers, as the synthetic target lacks biological correlation (See US-1, US-2).
- **FR-003**: System MUST band-pass filter EEG data between low-frequency and 45 Hz and re-reference to common average before feature extraction (See US-1).
- **FR-004**: System MUST compute spectral power density for delta, theta, alpha, beta, and gamma bands using Welch's method (See US-2).
- **FR-005**: System MUST fit a multivariate linear regression with L regularization (ridge) using 5-fold cross-validation and nested hyperparameter tuning (inner loop for alpha selection, outer loop for evaluation) to predict tDCS response percentage change. In **Fallback Mode**, this step is strictly for validating the regression pipeline and must not produce statistical inferences (See US-2).
- **FR-006**: System MUST apply False Discovery Rate (FDR) correction to the p-values of the final multivariate model coefficients when testing multiple EEG features to control family-wise error (See US-3).
- **FR-007**: System MUST perform sensitivity analysis sweeping the significance threshold (p) over a configurable set and the variance explained threshold (R²) over a configurable set. The system MUST define 'justified stability' as the primary finding (p < 0.05) holding across at least out of 3 tested thresholds, or report the specific threshold range where significance is lost (See US-3).

### Non-Functional Requirements

- **NFR-001**: System MUST execute all computations on CPU-only infrastructure with a maximum runtime within a feasible operational window. and ≤7 GB RAM usage across all User Stories (See US-1, US-2, US-3).

### Key Entities *(include if feature involves data)*

- **EEG Epoch**: Represents a 2-second window of filtered EEG data with associated subject ID and condition (rest/task).
- **tDCS Response**: Represents the percentage change in motor task score (pre vs. post) for a specific subject.
- **Feature Vector**: Represents the aggregated spectral and connectivity metrics for one subject.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data integrity is measured against the raw dataset checksums and subject count consistency (See US-1).
- **SC-002**: In **Primary Mode**, model predictive performance is measured against the observed adjusted R² and permutation test p-value. Success is defined as achieving a p-value < 0.05 in the permutation test against a null model (See US-2).
- **SC-002-FB**: In **Fallback Mode**, model performance is measured against the synthetic target. Success is defined as achieving an R² ≈ 0.0 (±0.05) to confirm the synthetic target is decoupled from EEG features (See US-2).
- **SC-003**: Computational feasibility is measured against the -hour runtime limit and Standard GitHub Actions runners provide a constrained RAM limit.

Research Question: How can memory-efficient algorithms be developed for large-scale graph processing?
Method: Comparative analysis of algorithmic complexity and resource utilization across distributed and single-node implementations.
References: Smith et al. (2023), DOI:10.1234/example (See NFR-001).
- **SC-004**: Threshold stability is measured against the variance of the binary significance outcome (0 or 1) across the sensitivity sweep {0.01, 0.05, 0.1}. Success is defined as variance ≤ 0.05 or no change in significance status (See US-3).

## Assumptions

- The OpenNeuro dataset contains tDCS motor scores and the PhysioNet dataset contains EEG data, but explicit pairing of these two datasets for the same subjects is rare; if pairing is missing, the system defaults to Fallback Mode for structural validation only, acknowledging that individual prediction is impossible in this mode and the primary research question is abandoned.
- The PhysioNet EEG Motor Movement/Imagery Dataset provides sufficient resting-state baseline data if OpenNeuro EEG is unavailable for baseline comparison.
- All required Python libraries (MNE, scikit-learn, numpy, pandas) are available in the GitHub Actions environment without requiring CUDA or GPU drivers.
- The dataset size for the target cohort fits within the 7 GB RAM constraint after epoching and filtering; if not, subsampling of epochs will be applied.
- The tDCS response metric (percentage change) is normalized and does not require imputation for missing pre/post scores.
- No external API calls are required during the analysis phase; all data is downloaded and processed locally within the runner.
- Synthetic data generated in Fallback Mode uses randomized individual noise and a configurable effect size (default Cohen's d = 0.5) to ensure it does not validate the specific EEG-tDCS hypothesis.
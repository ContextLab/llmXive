# Feature Specification: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

**Feature Branch**: `001-neural-oscillations-tDCS-biomarker`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Can resting‑state and task‑related EEG oscillatory features predict an individual’s motor performance improvement after a single session of anodal tDCS over the primary motor cortex?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system must ingest raw EEG and tDCS performance data from public repositories, apply standard preprocessing (filtering, re-referencing, artifact rejection), and output clean, epoch-aligned datasets ready for feature extraction.

**Why this priority**: Without clean, aligned data, no statistical modeling is possible. This is the foundational step that enables all downstream analysis and ensures reproducibility across different data sources.

**Independent Test**: Can be fully tested by running the preprocessing script on a subset of the PhysioNet EEG Motor Movement/Imagery Dataset and verifying the output file structure (e.g., `.fif` or `.csv` with expected columns) matches the schema without crashing.

**Acceptance Scenarios**:

1. **Given** raw EEG data from PhysioNet and tDCS performance scores from OpenNeuro, **When** the preprocessing script runs, **Then** the output contains aligned epochs with bad channels marked and filtered (1–45 Hz).
2. **Given** a dataset with missing channel metadata, **When** the preprocessing script runs, **Then** it logs a warning and proceeds with common average referencing rather than failing.

---

### User Story 2 - Feature Extraction and Statistical Modeling (Priority: P2)

The system must compute spectral power (delta, theta, alpha, beta, gamma) and connectivity metrics (PLV, wPLI) from the preprocessed EEG, then fit a ridge regression model to predict tDCS response (percentage change in motor score) using these features.

**Why this priority**: This implements the core scientific hypothesis (EEG features → tDCS response). It delivers the primary research output (the model coefficients and significance).

**Independent Test**: Can be fully tested by executing the feature extraction and regression module on a small synthetic dataset (n=10) and verifying the model outputs coefficients, R², and p-values without requiring external network access.

**Acceptance Scenarios**:

1. **Given** preprocessed EEG epochs, **When** the feature extraction module runs, **Then** it outputs a feature matrix with power density and PLV values for all subjects.
2. **Given** the feature matrix and tDCS response labels, **When** the ridge regression model fits, **Then** it returns adjusted R² and permutation test p-values.

---

### User Story 3 - Validation, Sensitivity Analysis, and Reporting (Priority: P3)

The system must validate the model using permutation testing (1,000 permutations), apply multiplicity correction for multiple EEG features, and perform sensitivity analysis on significance thresholds to ensure robustness.

**Why this priority**: This ensures the findings are methodologically sound (controlling for false positives) and defensible (testing stability of thresholds), which is required for publication and clinical translation.

**Independent Test**: Can be fully tested by running the validation module and verifying the output report contains a sensitivity sweep table (e.g., R² at p < 0.01, 0.05, 0.1) and a corrected p-value for the primary hypothesis.

**Acceptance Scenarios**:

1. **Given** the fitted regression model, **When** the validation module runs, **Then** it produces a sensitivity analysis table sweeping p-value thresholds {0.01, 0.05, 0.1} and reports stability.
2. **Given** multiple feature tests, **When** the validation module runs, **Then** it applies False Discovery Rate (FDR) correction and reports the adjusted p-value.

---

### Edge Cases

- What happens when the OpenNeuro dataset lacks EEG recordings paired with tDCS outcomes for the same subjects? (System must flag `[NEEDS CLARIFICATION]` and halt individual prediction).
- How does system handle memory overflow during permutation testing on 109 subjects? (System must process in batches or downsample epochs).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST verify that the input datasets contain paired EEG recordings and tDCS outcome scores for the same subjects, otherwise it MUST halt and emit `[NEEDS CLARIFICATION: Does OpenNeuro ds001734 contain concurrent EEG recordings paired with tDCS outcomes for the same subjects?]` (See US-1)
- **FR-002**: System MUST band-pass filter EEG data between 1–45 Hz and re-reference to common average before feature extraction (See US-1)
- **FR-003**: System MUST compute spectral power density for delta, theta, alpha, beta, and gamma bands using Welch's method (See US-2)
- **FR-004**: System MUST fit a multivariate linear regression with L2 regularization (ridge) to predict tDCS response percentage change (See US-2)
- **FR-005**: System MUST apply False Discovery Rate (FDR) correction when testing multiple EEG features to control family-wise error (See US-3)
- **FR-006**: System MUST perform sensitivity analysis sweeping the significance threshold (p) over {0.01, 0.05, 0.1} and the effect size threshold (R²) over {0.2, 0.3, 0.4} to justify stability (See US-3)
- **FR-007**: System MUST execute all computations on CPU-only infrastructure with a maximum runtime of 6 hours and ≤7 GB RAM usage (See US-3)

### Key Entities *(include if feature involves data)*

- **EEG Epoch**: Represents a 2-second window of filtered EEG data with associated subject ID and condition (rest/task).
- **tDCS Response**: Represents the percentage change in motor task score (pre vs. post) for a specific subject.
- **Feature Vector**: Represents the aggregated spectral and connectivity metrics for one subject.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data integrity is measured against the raw dataset checksums and subject count consistency (See US-1)
- **SC-002**: Model predictive performance is measured against the adjusted R² threshold (≥ 0.3) and permutation test p-value (< 0.05) (See US-2)
- **SC-003**: Computational feasibility is measured against the 6-hour runtime limit and 7 GB RAM limit on standard GitHub Actions runners (See US-3)
- **SC-004**: Threshold stability is measured against the variance in significance rates across the sensitivity sweep {0.01, 0.05, 0.1} (See US-3)

## Assumptions

- The OpenNeuro dataset contains both pre/post tDCS motor scores and EEG data for the same participants, or a valid mapping exists to pair them.
- The PhysioNet EEG Motor Movement/Imagery Dataset provides sufficient resting-state baseline data if OpenNeuro EEG is unavailable for baseline comparison.
- All required Python libraries (MNE, scikit-learn, numpy, pandas) are available in the GitHub Actions environment without requiring CUDA or GPU drivers.
- The dataset size for the target cohort fits within the 7 GB RAM constraint after epoching and filtering; if not, subsampling of epochs will be applied.
- The tDCS response metric (percentage change) is normalized and does not require imputation for missing pre/post scores.
- No external API calls are required during the analysis phase; all data is downloaded and processed locally within the runner.

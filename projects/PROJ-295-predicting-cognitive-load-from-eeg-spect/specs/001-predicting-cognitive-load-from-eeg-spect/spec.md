# Feature Specification: Predicting Cognitive Load from EEG Spectral Power Changes During Naturalistic Viewing

**Feature Branch**: `001-predict-cognitive-load-eeg`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting Cognitive Load from EEG Spectral Power Changes During Naturalistic Viewing"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system must successfully download, clean, and prepare the OpenNeuro EEG dataset for analysis, ensuring that EEG data is artifact-free and aligned with behavioral logs within the 7GB RAM constraint.

**Why this priority**: Without clean, aligned data, no feature extraction or modeling can occur. This is the foundational step; if the data pipeline fails or exceeds memory limits, the entire research project halts.

**Independent Test**: Can be fully tested by executing the data loading and ICA artifact removal script on the target runner and verifying that the output contains clean epochs with matching behavioral timestamps, while monitoring memory usage to ensure it stays under 7GB.

**Acceptance Scenarios**:

1. **Given** the OpenNeuro ds000246 dataset is available, **When** the preprocessing script runs with MNE-Python settings (1–45 Hz bandpass, 250 Hz downsampling), **Then** the output EEG epochs are free of line noise and eye-blink artifacts, and memory usage peaks at ≤ 6.5 GB under full dataset load.
2. **Given** raw EEG and behavioral logs, **When** the alignment process runs, **Then** every EEG epoch has a corresponding cognitive load proxy label (gaze variance) with a timestamp mismatch of ≤ 100ms.
3. **Given** the target dataset exceeds available RAM, **When** the script attempts to load the full data, **Then** it automatically switches to a chunked loading strategy or subsampling method to prevent out-of-memory errors, logging the action taken.

---

### User Story 2 - Feature Extraction and Label Generation (Priority: P2)

The system must compute spectral power features (theta and alpha bands) for each channel and generate a continuous cognitive load label based on gaze fixation stability for every trial.

**Why this priority**: This step transforms raw signals into the specific variables required for the hypothesis test. It validates the "Dataset-variable fit" by confirming that the necessary spectral bands and behavioral proxies are extractable.

**Independent Test**: Can be fully tested by running the feature extraction module on a subset of clean epochs and verifying that the resulting feature matrix contains valid theta/alpha power ratios and that the label distribution is non-trivial (not all zeros).

**Acceptance Scenarios**:

1. **Given** clean EEG epochs, **When** Welch's method is applied to compute Power Spectral Density, **Then** the system extracts mean power for the theta and alpha bands for all channels, producing a feature matrix with dimensions [n_epochs, n_channels * 2].
2. **Given** aligned behavioral logs, **When** the label generation logic runs, **Then** a continuous cognitive load score is derived from gaze variance for each epoch, with a normalized range via min-max scaling per subject.
3. **Given** the extracted features, **When** the system checks for missing values, **Then** it identifies and flags any epochs with > 5% missing sensor data for exclusion, ensuring the final dataset is complete for regression.

---

### User Story 3 - Model Training and Statistical Validation (Priority: P3)

The system must train a Ridge Regression model to predict cognitive load from spectral features and validate performance against a permutation baseline using a subject-wise split, ensuring results are statistically significant.

**Why this priority**: This is the core research question answer. It tests the "Inference framing" and "Predictor collinearity" constraints by ensuring the model is evaluated correctly and findings are framed as associational.

**Independent Test**: Can be fully tested by running the training and evaluation script on the held-out test set and verifying that the reported R² and RMSE values are calculated correctly and that the model outperforms the baseline.

**Acceptance Scenarios**:

1. **Given** the feature matrix and labels, **When** the Ridge Regression model is trained with subject-wise 5-fold cross-validation, **Then** the optimal regularization alpha is selected, and the model is evaluated on a held-out test set comprising a portion of subjects.
2. **Given** the test set predictions, **When** performance metrics are computed, **Then** the system reports a Pearson correlation (r) and Root Mean Squared Error (RMSE), and confirms if the test R² exceeds a predefined threshold for sufficient evidence.
3. **Given** multiple hypothesis tests (e.g., per-channel or per-band), **When** the analysis completes, **Then** a multiple-comparison correction (e.g., Bonferroni or FDR) is applied, and the corrected p-values are reported to control family-wise error.

### Edge Cases

- What happens if the OpenNeuro dataset is missing the specific behavioral log file required for gaze variance calculation? The system must halt with a clear error message identifying the missing file rather than proceeding with null labels.
- How does the system handle subjects with excessive artifacts (e.g., > 50% of epochs rejected by ICA)? The system must exclude these subjects from the final analysis and log the exclusion count to prevent biased results.
- What happens if the theta/alpha ratio calculation results in a division by zero (e.g., near-zero alpha power)? The system must add a small epsilon to the denominator to ensure numerical stability.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and preprocess the OpenNeuro dataset., applying a 1–45 Hz bandpass filter, downsampling to 250 Hz, and removing 50/60 Hz line noise (See US-1).
- **FR-002**: System MUST apply Independent Component Analysis (ICA) to remove eye-blink artifacts and retain only clean epochs for analysis (See US-1).
- **FR-003**: System MUST compute Power Spectral Density (PSD) using Welch's method and extract log-transformed relative power for theta (4–7 Hz) and alpha (8–12 Hz) bands per channel (See US-2).
- **FR-004**: System MUST derive a continuous cognitive load proxy label from gaze fixation stability (variance) aligned to each EEG epoch (See US-2).
- **FR-005**: System MUST train a Ridge Regression model using [deferred] of subjects for training and tune the regularization alpha via subject-wise 5-fold cross-validation (See US-3).
- **FR-006**: System MUST evaluate model performance using Pearson correlation and RMSE on a [deferred] held-out test set and compare against a mean-baseline predictor (See US-3).
- **FR-007**: System MUST apply a multiple-comparison correction (e.g., Bonferroni) to all statistical tests involving multiple channels or bands to control family-wise error (See US-3).
- **FR-008**: System MUST perform a sensitivity analysis on the proxy validity by varying the gaze variance calculation window and reporting the impact on model R² (See US-3).

### Key Entities

- **EEG Epoch**: A time-locked segment of EEG data associated with a specific video stimulus and behavioral event.
- **Cognitive Load Proxy**: A continuous numerical value derived from gaze variance representing the estimated mental effort for a given epoch.
- **Spectral Feature Vector**: A vector containing the log-transformed relative power values for theta and alpha bands across all EEG channels for a single epoch.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Model performance (R²) is measured against the pre-defined threshold to determine if the EEG spectral features reliably predict the gaze fixation stability proxy (See US-3).
- **SC-002**: Computational feasibility is measured against the GitHub Actions free-tier limits (≤ 7 GB RAM, ≤ 6 hours runtime) to ensure the analysis is reproducible on standard CI infrastructure (See US-1).
- **SC-003**: Statistical validity is measured by the application of multiple-comparison correction, ensuring that the family-wise error rate is controlled at α = 0.05 across all tested hypotheses (See US-3).
- **SC-004**: Data quality is measured by the percentage of epochs retained after ICA artifact removal, ensuring that at least 70% of the original epochs are available for analysis, consistent with community standards for sufficient statistical power in EEG studies (See US-1).
- **SC-005**: Measurement validity is measured by the successful extraction of theta/alpha power ratios, confirming that the selected frequency bands contain non-zero, stable power values across subjects (See US-2).

## Assumptions

- The OpenNeuro ds000246 dataset contains both the raw EEG recordings and the synchronized behavioral logs (gaze data) required to derive the cognitive load proxy.
- The "cognitive load" derived from gaze fixation stability is a valid and accepted proxy for mental effort in naturalistic viewing paradigms, as supported by the related work cited, acknowledging that it is a proxy rather than an absolute ground truth.
- The Ridge Regression model with L2 regularization is sufficient to handle potential collinearity among EEG channels without requiring more complex, GPU-accelerated deep learning architectures.
- The sufficiency of the sample size to detect a moderate effect size (R² ≥ 0.2) is a hypothesis to be tested via power analysis during the research phase, rather than a pre-existing fact, given the constraints of a CPU-only environment.
- The 1–45 Hz frequency range is sufficient to capture the relevant theta and alpha spectral power changes associated with cognitive load, ignoring higher frequency bands (gamma) which may be more susceptible to noise.
- The computational complexity of the ICA and Welch's PSD methods on the downsampled (250 Hz) data will not exceed the 6-hour runtime limit of the GitHub Actions runner.
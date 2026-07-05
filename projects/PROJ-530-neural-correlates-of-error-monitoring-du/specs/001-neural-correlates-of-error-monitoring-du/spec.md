# Feature Specification: Neural Correlates of Error Monitoring During Simulated Navigation

**Feature Branch**: `001-neural-correlates-error-monitoring`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Neural Correlates of Error Monitoring During Simulated Navigation"

## User Scenarios & Testing

### User Story 1 - Primary Analysis: MFN Amplitude vs. Error Magnitude (Priority: P1)

The system must ingest the Navigation Error Corpus EEG dataset, preprocess the signals to isolate Medial Frontal Negativity (MFN) components, and compute the correlation between MFN amplitude and continuous directional error magnitude.

**Why this priority**: This is the core research question. Without establishing the primary relationship between neural signals and behavioral error metrics, the project fails its scientific objective.

**Independent Test**: The pipeline can be tested by running the preprocessing and regression script on a subset of the data (e.g., 5 participants) and verifying that a correlation coefficient and p-value are outputted without runtime errors.

**Acceptance Scenarios**:

1. **Given** the raw EEG and trajectory data from the Navigation Error Corpus, **When** the system executes the preprocessing and regression pipeline, **Then** it outputs a valid mixed-effects model summary (or a GAM summary if linearity is rejected) regardless of the significance of the result.
2. **Given** a valid dataset with at least 10 participants, **When** the system calculates the angular deviation for each error event, **Then** it successfully maps these continuous values to the corresponding EEG epochs time-locked to the error.
3. **Given** the full dataset, **When** the analysis completes, **Then** the system generates a scatter plot visualizing MFN amplitude (y-axis) against error magnitude in degrees (x-axis) with the regression line overlay.

---

### User Story 2 - Methodological Robustness: Sensitivity Analysis on Thresholds (Priority: P2)

The system must perform a sensitivity analysis by sweeping the decision cutoff for "valid error events" (e.g., minimum angular deviation) across a defined range to ensure the primary finding is not an artifact of a single arbitrary threshold. Note: Error magnitude is calculated for ALL events; the threshold only filters events for the robustness check to avoid truncation bias.

**Why this priority**: Methodological soundness requires demonstrating that results are robust to parameter choices. This prevents the "threshold introduced without justification" rejection by the methodology panel.

**Independent Test**: The system can be tested by running the sensitivity sweep script and verifying that it produces a table or plot showing how the correlation coefficient and p-value change across the swept thresholds.

**Acceptance Scenarios**:

1. **Given** the primary analysis results, **When** the system sweeps the minimum angular deviation threshold over the set {5, 10, 15, 20} degrees, **Then** it outputs a summary table listing the correlation coefficient and p-value for each threshold.
2. **Given** a specific threshold sweep, **When** the analysis runs, **Then** it reports the variation in the headline false-positive rate (or significance status) across the swept values.
3. **Given** the sensitivity analysis output, **When** a user reviews the results, **Then** they can confirm that the primary finding (significant correlation) holds (p-value < 0.05) across at least 3 of the 4 tested thresholds.

---

### User Story 3 - Validation: Collinearity and Multiplicity Checks (Priority: P3)

The system must calculate Variance Inflation Factors (VIF) to check for predictor collinearity if multiple behavioral metrics are used, and apply a multiple-comparison correction (e.g., Bonferroni or FDR) if multiple EEG electrodes or frequency bands are tested simultaneously.

**Why this priority**: The methodology panel requires explicit handling of statistical assumptions (collinearity) and error rates (multiplicity) to ensure the inference framing is valid and not overstated.

**Independent Test**: The system can be tested by intentionally adding a redundant predictor (e.g., error magnitude in radians vs. degrees) and verifying that the VIF diagnostic flag is raised, or by running the correction script on a multi-electrode test case.

**Acceptance Scenarios**:

1. **Given** a model with multiple behavioral predictors, **When** the system calculates VIF, **Then** it reports a VIF value < 5 for all predictors, or flags a collinearity warning if VIF ≥ 5.
2. **Given** results from testing MFN amplitude across 5 medial frontal electrodes, **When** the system applies family-wise error correction, **Then** it outputs the adjusted p-values and indicates which results remain significant.
3. **Given** the final results, **When** the system generates the report, **Then** the report contains the exact phrase "associational" in the Conclusion section.

### Edge Cases

- What happens if the trajectory data for a specific error event is missing or corrupted? The system must skip that event and log a warning, ensuring the analysis proceeds with valid data rather than crashing.
- How does the system handle participants with fewer than 10 error events? The system must exclude these participants from the mixed-effects model to ensure statistical power, logging the exclusion count.
- What if the MFN window (200-400ms) overlaps with a muscle artifact? The system must rely on the ICA artifact removal step; if ICA fails to remove the component, the epoch must be flagged and excluded from the final amplitude calculation.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and cache the Navigation Error Corpus dataset (Zenodo record) without requiring user authentication, ensuring the full dataset is available for analysis. (See US-1)
- **FR-002**: System MUST apply a bandpass filter (1 Hz to 40 Hz) and a 60 Hz notch filter to raw EEG data, followed by Independent Component Analysis (ICA) to remove ocular and muscular artifacts. (See US-1)
- **FR-003**: System MUST calculate directional error magnitude for each error event as the angular deviation (in degrees) between the participant's heading and the optimal path at the moment of error onset. (See US-1)
- **FR-004**: System MUST extract the peak (most negative) MFN amplitude from the 200-400ms post-error window at electrodes FCz, Cz, and Fz, baseline-corrected to the pre-error period. (See US-1)
- **FR-005**: System MUST fit a linear mixed-effects model with MFN amplitude as the outcome, error magnitude as a fixed effect, and participant ID as a random intercept; if a non-linearity test (e.g., GAM smooth term p < 0.05) rejects linearity, the system MUST fall back to a Generalized Additive Model (GAM). (See US-1)
- **FR-006**: System MUST execute a sensitivity analysis sweeping the minimum error magnitude threshold over the set {5, 10, 15, 20} degrees and report the resulting correlation coefficients. (See US-2)
- **FR-007**: System MUST calculate Variance Inflation Factors (VIF) for all behavioral predictors and flag any predictor with VIF ≥ 5 as collinear. (See US-3)
- **FR-008**: System MUST apply a multiple-comparison correction (e.g., Bonferroni) to p-values if multiple electrodes or frequency bands are tested simultaneously. (See US-3)

### Key Entities

- **EEG Epoch**: A time-locked segment of EEG data (-200ms to 800ms) surrounding an error event, containing amplitude values across channels and time.
- **Error Event**: A behavioral instance where the participant deviates from the optimal path, characterized by a timestamp and a calculated directional error magnitude.
- **Participant**: A unique subject in the dataset, associated with a set of EEG epochs and error events, used as a random intercept in the statistical model.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient (r) between MFN amplitude and error magnitude is measured against the hypothesis of a positive association (r > 0) using the Navigation Error Corpus dataset. (See US-1)
- **SC-002**: The stability of the primary finding is measured against the sensitivity analysis sweep (thresholds 5, 10, 15, 20 degrees) to ensure the correlation remains significant (p-value < 0.05 after Bonferroni correction) across the range. (See US-2)
- **SC-003**: The validity of the model assumptions is measured against the Variance Inflation Factor (VIF) diagnostic, requiring VIF < 5 for all predictors. (See US-3)
- **SC-004**: The family-wise error rate is measured against the uncorrected p-values to ensure the final reported significance holds (adjusted p-value < 0.05) after multiple-comparison correction. (See US-3)
- **SC-005**: The computational feasibility is measured against the GitHub Actions free-tier constraints (≤6h runtime, ≤7GB RAM) by ensuring the full analysis completes within these limits on the full available dataset. (See US-1)

## Assumptions

- The Navigation Error Corpus dataset (Zenodo record) contains synchronized EEG and behavioral trajectory data for a cohort of participants, with sufficient quality for ICA artifact removal.
- The "optimal path" for each navigation task is explicitly defined in the dataset's metadata or can be derived deterministically from the maze structure provided in the corpus.
- The EEG signal quality is sufficient to resolve the MFN component (200-400ms post-error window) after standard ICA preprocessing; no participants have such severe artifacts that they must be entirely excluded.
- The analysis will be performed on a CPU-only environment; therefore, the method avoids GPU-accelerated deep learning or 8-bit quantization, relying instead on classical statistics (statsmodels) and standard signal processing (MNE-Python).
- The "directional error magnitude" is calculated as the absolute angular deviation in degrees, and this metric is the primary behavioral predictor of interest as defined in the research question.
- The sample size (N=47) is estimated to provide sufficient statistical power (≥80%) to detect a moderate effect size (r ≈ 0.3) at α = 0.05, conditional on an intra-class correlation (ICC) < 0.5, as estimated by G*Power prior to data collection.
- MFN amplitude is expected to scale linearly with prediction error magnitude (Holroyd & Coles,); if this assumption is rejected by the data (non-linearity test p < 0.05), the Generalized Additive Model (GAM) fallback defined in FR-005 will be used.
- Error magnitude is calculated for ALL events to avoid truncation bias; the sensitivity analysis thresholds in FR-006 are applied only as a robustness filter for the regression, not for the initial calculation of the predictor variable.
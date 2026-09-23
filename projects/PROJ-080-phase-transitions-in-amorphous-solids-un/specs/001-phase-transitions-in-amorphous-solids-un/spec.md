# Feature Specification: Phase Transitions in Amorphous Solids Under Shear Stress

**Feature Branch**: `001-phase-transitions-amorphous-solids`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Phase Transitions in Amorphous Solids Under Shear Stress"

## User Scenarios & Testing

### User Story 1 - Precursor Detection Pipeline (Priority: P1)

The researcher needs to ingest raw molecular dynamics trajectory data, compute non-affine displacement ($D^2_{min}$) and local shear strain metrics, and identify the precise timestep of macroscopic yielding to establish the ground truth for the transition.

**Why this priority**: Without a robust, automated pipeline to extract the predictor variables ($D^2_{min}$) and the target variable (yielding onset), no statistical analysis can occur. This is the foundational data preparation step.

**Independent Test**: Can be fully tested by processing a single, small, held-out trajectory file (e.g., ≤ 10,000 steps) and verifying the output contains a CSV with computed $D^2_{min}$ values per particle and a flagged index for the stress-drop yielding point.

**Acceptance Scenarios**:

1. **Given** a valid trajectory file in the input directory, **When** the preprocessing script runs, **Then** it outputs a structured CSV containing per-particle $D^2_{min}$ values and a global stress-strain curve with the yielding timestep explicitly marked.
2. **Given** a trajectory where the stress drop is ambiguous (no sharp peak), **When** the script runs, **Then** it flags the dataset as "indeterminate" and logs a warning, preventing downstream analysis from proceeding on invalid data.

---

### User Story 2 - Statistical Correlation Analysis (Priority: P2)

The researcher needs to compare the distribution of $D^2_{min}$ values between brittle and ductile trajectories to determine if there is a statistically significant difference in structural precursors prior to yielding.

**Why this priority**: This addresses the core research question: "What are the precursory structural signatures?" It moves from data extraction to scientific inference.

**Independent Test**: Can be fully tested by running the analysis script on two pre-labeled datasets (one brittle, one ductile) and verifying the output includes a Kolmogorov-Smirnov test statistic and p-value.

**Acceptance Scenarios**:

1. **Given** two distinct trajectory datasets labeled as "brittle" and "ductile", **When** the statistical analysis module executes, **Then** it outputs a report containing the KS-test statistic, p-value, and a visual overlay of the $D^2_{min}$ distribution histograms (aggregated by shear band to account for spatial correlation).
2. **Given** a dataset where the sample size is insufficient for the KS-test (n < 30), **When** the module executes, **Then** it halts and reports a "Power Limitation" warning, noting that the p-value is unreliable. This threshold (n=30) is required to achieve statistical power ≥ 0.8 for detecting medium effect sizes (Cohen's d ≈ 0.5) at α=0.05.

---

### User Story 3 - Predictive Threshold Validation (Priority: P3)

The researcher needs to validate a specific threshold of $D^2_{min}$ that predicts time-to-failure with a measurable accuracy, including a sensitivity analysis to ensure the threshold is not arbitrary.

**Why this priority**: This addresses the "can these signatures be used to predict" part of the research question, moving from correlation to prediction.

**Independent Test**: Can be fully tested by applying the derived threshold to the 20% held-out validation set and verifying the False Positive and False Negative rates are reported against the time-to-failure metric.

**Acceptance Scenarios**:

1. **Given** a derived threshold value for $D^2_{min}$, **When** applied to the held-out validation set, **Then** the system outputs a confusion matrix and calculates the False Positive Rate (FPR) and False Negative Rate (FNR) relative to the time-to-failure event.
2. **Given** a decision threshold, **When** the sensitivity analysis runs, **Then** the system sweeps the threshold across a range (e.g., $\pm 0.05$) and outputs a table showing how FPR and FNR vary with the threshold change.

### Edge Cases

- What happens when the trajectory data is corrupted or incomplete (missing frames)?
- How does the system handle trajectories where the stress-strain curve shows multiple yielding events (complex plasticity)?
- What if the computed $D^2_{min}$ values are NaN or infinite due to numerical instability in the neighbor list?

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute non-affine displacement ($D^2_{min}$) for every particle in the trajectory using a CPU-optimized implementation of the Falk-Langer algorithm. (See US-1)
- **FR-002**: System MUST identify the yielding onset point by detecting the first significant stress drop (defined as a decrease > 5% in global shear stress relative to the local maximum stress immediately preceding the drop, occurring over 50 timesteps). This threshold aligns with community standards for macroscopic yielding in amorphous solids (See US-1).
- **FR-003**: System MUST perform a two-sample Kolmogorov-Smirnov test to compare $D^2_{min}$ distributions between brittle and ductile trajectory groups, explicitly framing the result as an associational finding. The input to the test MUST be $D^2_{min}$ values aggregated to the shear-band level (mean per connected cluster of high-displacement particles) to account for spatial autocorrelation. (See US-2)
- **FR-004**: System MUST implement a sensitivity analysis that sweeps the prediction threshold for $D^2_{min}$ over a range of $\{ \text{threshold} - 0.05, \text{threshold}, \text{threshold} + 0.05 \}$ and reports the variation in False Positive and False Negative rates. The prediction target MUST be the "time-to-failure" (timesteps until complete structural collapse) to ensure non-trivial validation. (See US-3)
- **FR-005**: System MUST enforce a multiple-comparison correction (e.g., Bonferroni) if more than one hypothesis test is performed across different strain rates or temperatures within a single analysis run to control the family-wise error rate. (See US-2)
- **FR-006**: System MUST reject any input trajectory where the particle count exceeds 100,000 particles to ensure the dataset fits within the memory constraint of the CI runner (7GB RAM) and guarantees reproducibility. (See US-1)

### Key Entities

- **Trajectory**: A sequence of particle coordinates and simulation box dimensions over time, representing the state of the amorphous solid.
- **Precursor Metric**: A derived scalar value (e.g., $D^2_{min}$, local strain) computed for specific particles or regions at a specific timestep.
- **Yielding Event**: A specific timestep identified by a macroscopic stress drop, marking the transition from elastic to plastic behavior.
- **Validation Set**: A subset of trajectories (≤ 20% of total) held out from the training/clustering phase to test predictive accuracy.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The predictive accuracy (F-score) of the $D^2_{min}$ threshold model is measured against the held-out validation set labels. (See US-3)
- **SC-002**: The statistical significance (p-value) of the difference in $D^2_{min}$ distributions between brittle and ductile regimes is measured against the standard alpha level of 0.05. (See US-2)
- **SC-003**: The sensitivity of the prediction threshold is measured by the change in False Positive Rate across the specified threshold sweep range. (See US-3)
- **SC-004**: The computational runtime of the full analysis pipeline is measured against the time limit of the GitHub Actions `ubuntu-latest` runner (6 hours). (See US-1)
- **SC-005**: The memory footprint of the data processing step is measured against the RAM limit of the `ubuntu-latest` runner (7 GB). (See US-1)

## Assumptions

- The public molecular dynamics repositories (HuggingFace `amorphous-silicon-shear-trajectories`, Zenodo) contain the necessary particle coordinates and box dimensions to compute $D^2_{min}$ and shear strain.
- The amorphous solid systems simulated are limited to ≤ 100,000 particles to fit within the 7GB RAM constraint of the CI environment.
- The "brittle" and "ductile" labels for trajectories are pre-defined in the metadata of the source datasets or are derived from global mechanical response metrics (e.g., total strain at failure) rather than the stress-drop shape, to avoid circular validation.
- The analysis will be performed in double precision to maintain numerical stability, as single precision may introduce noise in $D^2_{min}$ calculations.
- The GitHub Actions free-tier runner provides sufficient disk space to store temporary trajectory files and output artifacts without external storage.
- The `amorphous-silicon-shear-trajectories` dataset does not contain missing frames that would break the temporal continuity required for strain calculation.
- Spatial autocorrelation in $D^2_{min}$ data is significant, necessitating aggregation to shear bands before statistical testing.
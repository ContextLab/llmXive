# Research Plan & Methodology

## Objective
To investigate the neural correlates of predictive error signals (MMN) during tactile discrimination learning and their relationship to behavioral accuracy.

## Methodological Corrections (Plan Phase 0.5)

This section documents deviations from the initial specification to align with the final analysis plan.

### 1. Statistical Model Update (FR-006)
- **Original**: Non-specified or generic modeling.
- **Revised**: The primary statistical model is now a **Gaussian Linear Mixed-Effects (LME)** model.
- **Formula**: `MMN_Amplitude ~ Accuracy + Learning_Phase + (1|Subject)`
- **Rationale**: Gaussian LME provides a robust framework for handling repeated measures and inter-subject variability in continuous neural data.

### 2. Lagged Alignment (FR-005, User Story 2)
- **Original**: Direct alignment of MMN and accuracy within the same block.
- **Revised**: Implementation of **Lagged Alignment**.
- **Method**:
 - Calculate MMN amplitude over a **preceding 50-trial window** (t-50 to t-10).
 - Align this neural metric to the **subsequent multi-trial accuracy block** (t to t+n).
- **Rationale**: This approach tests the hypothesis that the neural prediction error signal in a preceding window drives learning and accuracy in the subsequent block, rather than being a concurrent correlate.

### 3. Exclusion of Underpowered Subjects
- **Criteria**: Subjects with <20 subjects in the total cohort or blocks with <10 valid trials.
- **Handling**: These subjects/blocks are explicitly excluded from the primary GLMM input data.
- **Documentation**: Excluded subject IDs are written to `data/excluded_subjects.csv` and logged in `data/validation_report.json`.
- **Rationale**: Ensures statistical power and model stability by removing noise from insufficient data points.

### 4. Data Handling
- **Streaming**: All data ingestion uses streaming buffers to maintain peak RAM ≤ 7 GB.
- **Checksums**: Checksum utilities are used for data hygiene (FR-009).
- **Permutation**: Permutation tests (n=1000) include logic to verify sufficiency based on dataset size.

## Analysis Pipeline Overview

1. **Ingestion**: Fetch datasets, validate variables (`stimulus_type`, `response_correctness`).
2. **Preprocessing**: Filter (-40 Hz), ICA, interpolate, epoch (-200ms to 500ms).
3. **Alignment**: Compute MMN, apply Lagged Alignment (50-trial window), handle missing logs.
4. **Modeling**: Fit Gaussian LME, apply FDR correction, run permutation test.
5. **Validation**: Sensitivity analysis, robustness checks.

## Expected Outcomes
- Identification of significant predictive relationships between MMN amplitude and subsequent behavioral accuracy.
- Robust statistical evidence supporting the role of predictive error signals in tactile learning.
- A reproducible pipeline for analyzing similar EEG datasets.

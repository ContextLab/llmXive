# Project Specification: Neural Correlates of Predictive Error Signals During Tactile Discrimination Learning

## Overview
This project investigates the neural correlates of predictive error signals in the context of tactile discrimination learning. We utilize EEG data to measure mismatch negativity (MMN) and align it with behavioral accuracy metrics.

## Functional Requirements

### FR-001: Dataset Discovery
The system must search for and identify relevant datasets containing tactile, somatosensory, or odd-ball experimental paradigms.

### FR-002: Preprocessing
Raw EEG data must be bandpass filtered (1-40 Hz), subjected to ICA for artifact removal, and bad channels interpolated.

### FR-003: Epoching
Data must be epoched from -200ms to 500ms relative to stimulus onset, separated by standard and deviant stimulus types.

### FR-004: MMN Calculation
MMN amplitude must be calculated as the mean difference wave (Deviant - Standard) within the 150–250ms time window at electrodes CP3, CP4, C3, and C4.

### FR-005: Behavioral Alignment (UPDATED)
Behavioral accuracy must be aligned with neural data using **Lagged Alignment**.
- **Method**: The MMN amplitude is calculated over a preceding 50-trial window (t-50 to t-10) and aligned to the subsequent multi-trial accuracy block (t to t+n).
- **Exclusion**: Subjects identified as "underpowered" (fewer than 20 valid subjects in the cohort or insufficient trials per block) must be explicitly excluded from the primary GLMM input data.
- **Fallback**: If behavioral logs are missing, the system defaults to "Stimulus-Driven" analysis mode.

### FR-006: Statistical Modeling (UPDATED)
The primary statistical model is a **Gaussian Linear Mixed-Effects Model (LME)**.
- **Formula**: `MMN_Amplitude ~ Accuracy + Learning_Phase + (1 | Subject)`
- **Correction**: Multiple comparisons across electrodes must be corrected using the Benjamini-Hochberg (FDR) procedure.
- **Validation**: A permutation test (n=1000) must be performed to validate significance.

### FR-007: Permutation Test
A permutation test with 1000 shuffles is required to validate the significance of the LME coefficients. The system must check for p-value stability or adjust n based on dataset size.

### FR-008: Multiple Comparison Correction
Apply FDR (Benjamini-Hochberg) correction to p-values derived from electrode-specific analyses.

### FR-009: Resource Constraints
The pipeline must operate within 7 GB RAM and run on multi-core CPU without GPU acceleration. Raw files must be deleted post-processing.

### FR-010: Sensitivity Analysis
Perform sensitivity analysis by sweeping the time window ±10ms (e.g., 140–240ms, 160–260ms).

### FR-011: Missing Data Handling
Log warnings for missing metadata and skip affected datasets rather than crashing.

### FR-012: Analysis Mode Selection
Automatically determine analysis mode ("Error-Signal" or "Stimulus-Driven") based on the availability of `stimulus_type` and `response_correctness` variables.

## User Stories

### US1: Data Ingestion and Preprocessing
**As a** researcher,
**I want** to download, preprocess, and epoch EEG data,
**So that** I have a clean dataset with labeled epochs for analysis.
**Acceptance Criteria**:
- Data downloaded from OpenNeuro/HF.
- Preprocessing includes filtering, ICA, and interpolation.
- Epoching success rate ≥ 95%.
- Underpowered subjects flagged and excluded from primary analysis.

### US2: MMN Amplitude and Behavioral Alignment
**As a** researcher,
**I want** to compute MMN amplitudes and align them with behavioral accuracy using Lagged Alignment,
**So that** I can correlate neural predictive errors with learning performance.
**Acceptance Criteria**:
- MMN calculated at CP3, CP4, C3, C4 (150–250ms).
- **Lagged Alignment** applied: 50-trial source window mapped to subsequent accuracy block.
- Underpowered subjects explicitly excluded from the aligned dataset.
- Output `data/aligned_data.csv` contains time-series of MMN and accuracy.

### US3: Statistical Modeling and Validation
**As a** researcher,
**I want** to fit a Gaussian LME model and validate it with permutation tests,
**So that** I can make statistically robust claims about the relationship between MMN and accuracy.
**Acceptance Criteria**:
- Model: `MMN_Amplitude ~ Accuracy + Learning_Phase + (1 | Subject)`.
- FDR correction applied.
- Permutation test (n=1000) executed and reported.
- Sensitivity analysis performed.

## Version History
- v1.0: Initial draft.
- v1.1: Updated FR-005 and US2 to reflect "Lagged Alignment" (50-trial window) and exclusion of underpowered subjects. Updated FR-006 to specify "Gaussian LME".

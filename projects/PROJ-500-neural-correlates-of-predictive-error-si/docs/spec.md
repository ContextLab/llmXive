# Project Specification: Neural Correlates of Predictive Error Signals During Tactile Discrimination Learning

## Overview
This project investigates the neural correlates of predictive error signals (MMN) during tactile discrimination learning. The study utilizes EEG data to analyze the relationship between neural responses and behavioral accuracy.

## Functional Requirements

### FR-001: Dataset Discovery
The system must automatically discover and download relevant datasets from OpenNeuro or HuggingFace containing tactile, somatosensory, or odd-ball paradigms.

### FR-002: Preprocessing
Data must be preprocessed with a -40 Hz bandpass filter, ICA artifact removal, and bad channel interpolation.

### FR-003: Epoching
Data must be epoched from -200ms to 500ms relative to stimulus onset, separating standard and deviant stimuli.

### FR-004: MMN Calculation
MMN amplitude must be calculated as the mean difference wave between deviant and standard responses in the 150–250ms window at electrodes CP3, CP4, C3, and C4.

### FR-005: Behavioral Alignment (UPDATED)
Behavioral accuracy must be aligned with neural data using **Lagged Alignment**.
- **Method**: Calculate MMN amplitude over a preceding 50-trial window (t-50 to t-10) and align it to the subsequent multi-trial accuracy block (t to t+n).
- **Exclusion**: Subjects with insufficient power (defined as <20 valid subjects in the cohort or <10 valid trials per block) must be excluded from the primary GLMM input.
- **Fallback**: If behavioral logs are missing, the system defaults to "Stimulus-Driven" mode (using P=0.8 probability) as defined in FR-011.

### FR-006: Statistical Modeling (UPDATED)
The primary statistical model must be a **Gaussian Linear Mixed-Effects (LME)** model.
- **Formula**: `MMN_Amplitude ~ Accuracy + Learning_Phase + (1|Subject)`
- **Correction**: Apply FDR (Benjamini-Hochberg) correction for multiple comparisons across electrodes.
- **Validation**: Perform a permutation test (n=1000) to validate significance, with logic to check sufficiency of n based on dataset size.

### FR-007: Permutation Test
Implement a permutation test with 1000 shuffles to validate the significance of the LME model coefficients.

### FR-008: Multiple Comparison Correction
Use FDR (Benjamini-Hochberg) to correct p-values across the tested electrodes (CP3, CP4, C3, C4).

### FR-009: Data Hygiene & Resource Constraints
- Implement streaming buffers to ensure peak RAM usage does not exceed 7 GB.
- Delete raw files post-processing.
- Implement checksum utilities for data integrity.

### FR-010: Sensitivity Analysis
Perform sensitivity analysis by sweeping the time window ±10ms (140–240ms, 160–260ms) to ensure robustness of findings.

### FR-011: Analysis Mode Branching
The pipeline must detect missing behavioral logs and automatically switch `analysis_mode` to "Stimulus-Driven" if data is unavailable, otherwise default to "Error-Signal".

### FR-012: Variable Validation
The system must verify the presence of `stimulus_type` and `response_correctness` in dataset metadata before proceeding.

## User Stories

### User Story 1: Data Ingestion and Preprocessing
**As a** researcher, **I want** to automatically download, preprocess, and epoch EEG data so that I have a clean dataset ready for analysis.
**Acceptance Criteria**:
- Datasets are fetched from OpenNeuro/HF.
- Filtering, ICA, and interpolation are applied.
- Epochs are generated with ≥95% success rate.
- Underpowered subjects (<20 subjects in cohort) are flagged and excluded from GLMM input.

### User Story 2: MMN Amplitude and Behavioral Alignment
**As a** researcher, **I want** to compute MMN amplitude and align it with behavioral accuracy using Lagged Alignment so that I can analyze the predictive nature of the neural signal.
**Acceptance Criteria**:
- MMN is calculated at CP3, CP4, C3, C4 (150–250ms).
- **Lagged Alignment** is applied: MMN from a 50-trial window (t-50 to t-10) aligns to the accuracy block (t to t+n).
- Underpowered subjects are explicitly excluded from the primary GLMM input.
- Missing behavioral logs trigger "Stimulus-Driven" fallback.
- Output: `data/aligned_data.csv` and `data/interim_lagged_mmns.csv`.

### User Story 3: Statistical Modeling and Validation
**As a** researcher, **I want** to fit a Gaussian LME model and validate results with permutation tests so that I can draw statistically robust conclusions.
**Acceptance Criteria**:
- Model: `MMN_Amplitude ~ Accuracy + Learning_Phase + (1|Subject)`.
- FDR correction applied.
- Permutation test (n=1000) performed with sufficiency check.
- Sensitivity analysis performed.
- Output: `analysis/results/model_output.json`.

## Constraints
- Hardware: Multi-core CPU, ≤7 GB RAM, no GPU.
- Runtime: Full pipeline ≤6 hours.
- No 8-bit/4-bit quantization.

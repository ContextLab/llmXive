# Research Plan: Neural Correlates of Predictive Error Signals

## Overview
This project investigates the neural correlates of predictive error signals during tactile discrimination learning using EEG data.

## Methodological Corrections (Plan Phase 0.5)

The original specification has been updated to align with the following methodological corrections:

### 1. Statistical Model Update (Gaussian LME)
- **Previous:** Generic LME specification.
- **Current:** **Gaussian Linear Mixed-Effects Model**.
- **Formula:** `MMN_Amplitude ~ Accuracy + Learning_Phase + (1|Subject)`
- **Rationale:** The Gaussian assumption is appropriate for the continuous MMN amplitude metric after artifact rejection.

### 2. Alignment Strategy (Lagged Alignment)
- **Previous:** Simultaneous alignment of neural and behavioral metrics.
- **Current:** **Lagged Alignment** using a 50-trial window.
- **Mechanism:** Neural metrics (MMN) are calculated over a preceding window (t-50 to t-10) to predict the behavioral outcome in the subsequent block (t to t+n). This accounts for the latency of learning effects.

### 3. Exclusion of Underpowered Subjects
- **Protocol:** Subjects or clusters with insufficient power (e.g., <20 subjects in a group or <10 valid trials per block) are explicitly excluded from the primary GLMM input data.
- **Documentation:** Excluded subjects are logged to `data/excluded_subjects.csv` and reported in `data/validation_report.json` but are not dropped from the raw dataset.

## Data Pipeline
1. **Ingestion:** Fetch from OpenNeuro/HF.
2. **Preprocessing:** Filter (-40 Hz), ICA, Epoching.
3. **Alignment:** Compute MMN over 50-trial lag window, align to behavioral block.
4. **Modeling:** Fit Gaussian LME with FDR correction and permutation testing.

## References
- Plan Document: `specs/001-neural-correlates-tactile-learning/plan.md` (Phase 0.5)
- Specification: `spec.md` (Amended)

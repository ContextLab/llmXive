# Implementation Plan: Investigating the Relationship Between Neural Synchrony and Attention Switching Costs

**Branch**: `001-investigating-neural-synchrony-attention-switching` | **Date**: 2024-05-22 | **Spec**: `specs/001-investigating-neural-synchrony-attention-switching/spec.md`

## Summary

This project implements a CPU-tractable pipeline to investigate the relationship between pre-stimulus frontoparietal neural synchrony (measured via wPLI/PLV in theta and gamma bands) and attention switching costs (RT difference) using task-switching EEG data. The approach involves a dynamic search for a verified OpenNeuro dataset containing 'switch/stay' trials, preprocessing it with strict memory constraints (bandpass low-frequency range, ICA artifact removal), computing synchrony metrics on scalp-level proxies for DLPFC/Parietal regions, and performing permutation-based correlation analyses with multiple-comparison corrections. All findings will be framed as associational.

**Critical Constraint**: The project **MUST** halt with a formal "Data Gap Report" if NO verified task-switching dataset is found in the OpenNeuro repository. The pipeline does not rely on a single hardcoded dataset ID (e.g., ds004173) but queries the OpenNeuro API for any dataset matching the required schema. This ensures the methodology is robust to dataset deprecation.

## Technical Context

**Language/Version**: Python 3.x

The specific value to remove/generalize: '3.x'

Rewritten passage:
Python 3.x

The specific value to remove/generalize: '3.x'

Rewritten passage:  
**Primary Dependencies**: `mne` (EEG processing), `numpy`, `scipy`, `pandas`, `statsmodels`, `scikit-learn`, `pyyaml`, `openneuro-py`, `bids`  
**Storage**: Local temporary directory for raw data; `data/` for derived artifacts (epochs, metrics).  
**Testing**: `pytest` (unit tests for signal processing, integration tests for pipeline).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM, no GPU).  
**Project Type**: Computational Neuroscience Analysis Pipeline  
**Performance Goals**: Peak RSS ≤ 6.5 GB; Total runtime ≤ 6 hours for full dataset.  
**Constraints**: CPU-only; no CUDA; sequential subject processing to fit RAM; strict epoching windows.  
**Scale/Scope**: Processing a cohort of subjects; generating synchrony matrices and behavioral metrics.

> **Dataset Fit Note**: The spec requires a task-switching dataset. The plan implements a dynamic search via the `openneuro` Python client to find ANY dataset with 'task-switching' events. If no such dataset exists in the public repository, the project halts with a documented "Data Gap Report" rather than crashing. This is the only valid path under the "Verified Accuracy" constitution, as using unverified data is forbidden.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Status | Notes |
|-----------|---|---|
| **I. Reproducibility** | **PASS** | Plan mandates pinned seeds, isolated virtualenv, and raw data caching. |
| **II. Verified Accuracy** | **PASS** | Plan restricts dataset citations to the "Verified datasets" block. It actively queries OpenNeuro for valid task-switching data. If none is found, it produces a "Data Gap Report" (a valid research artifact) rather than using unverified proxies. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming for raw data and derived artifacts; no in-place modification. |
| **IV. Single Source of Truth** | **PASS** | Final metrics will be generated programmatically; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | A script `code/update_state_hashes.py` will be generated/verified in Phase 0. Artifacts will carry content hashes; state file updated on changes. |
| **VI. Neural Signal Processing Consistency** | **PASS** | Plan strictly adheres to a low-frequency cutoff within the standard bandpass range, /ms epoching, and wPLI/PLV metrics. Sensitivity analysis for windows is included. |
| **VII. Computational Resource Adherence** | **PASS** | Plan enforces sequential processing, memory limit checks, and CPU-only libraries. |

## Project Structure

### Documentation (this feature)

```text
specs/001-investigating-the-relationship-between-n/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-498-investigating-the-relationship-between-n/
├── data/
│   ├── raw/             # Downloaded OpenNeuro data (checksummed)
│   ├── processed/       # Cleaned epochs, ICA components
│   ├── metrics/         # Synchrony matrices, behavioral costs
│   └── trial_level/     # Per-trial synchrony and RT data
├── code/
│   ├── __init__.py
│   ├── config.py        # Paths, seeds, hyperparameters
│   ├── download.py      # Data fetching logic (OpenNeuro API search)
│   ├── preprocess.py    # Filtering, ICA, epoching
│   ├── synchrony.py     # PLV/wPLI calculation
│   ├── analysis.py      # Correlation, permutation tests, LME
│   ├── update_state_hashes.py # Generates/verifies hashes for state file
│   └── main.py          # Pipeline orchestrator
├── tests/
│   ├── unit/            # Synthetic signal tests
│   └── integration/     # End-to-end pipeline tests
├── requirements.txt     # Pinned dependencies
└── README.md            # Project overview
```

**Structure Decision**: Single-project structure selected to minimize overhead and ensure all analysis steps (download -> preprocess -> analyze) are tightly coupled in a single execution flow, suitable for CI/CD.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|---|---|
| **Sensitivity Analysis (FR-007)** | Required to validate robustness of pre-stimulus window. | Single window analysis risks false positives if the chosen window is arbitrary. |
| **Linear Mixed-Effects (LME) Model (FR-009)** | Required for trial-level granularity. | Simple correlation ignores within-subject trial variability and reduces statistical power. |
| **Permutation Testing (FR-005)** | Required for non-parametric significance without distributional assumptions. | Parametric t-tests assume normality which may not hold for small N or skewed RT distributions. |
| **Dynamic Dataset Search** | Required to handle dataset deprecation (methodology-f4c72735). | Hardcoding a single dataset ID risks project failure if that dataset is removed or invalid. |
| **Data Gap Report** | Required to handle the case where no valid dataset exists. | Halting with a silent error is not a valid research outcome; a formal report is needed. |

## Implementation Phases

### Phase 0: Setup & Validation
1. **Environment**: Create virtualenv, install `requirements.txt`.
2. **Script Generation**: Generate `code/update_state_hashes.py` if missing (or verify it exists).
3. **Dataset Search**: Query OpenNeuro API for datasets containing 'task-switching' events.
   - **If Found**: Select the first valid dataset (e.g., ds004173 or alternative).
   - **If Not Found**: Generate `data_gap_report.json` (schema defined in contracts), log error, and halt with status `data_gap_unverifiable`.
   - **Validation**: Ensure selected dataset contains 'switch/stay' labels and RT data.
     - **If Invalid**: Log error, halt.
     - **If Valid**: Proceed.

### Phase 1: Preprocessing (FR-002, FR-006)
1. **Download**: Fetch raw data to `data/raw/`.
2. **Filter**: Bandpass lower than a frequency threshold appropriate for the target signal characteristics..
3. **ICA**: Remove components with kurtosis > 5 or spectral peak > 30 Hz.
4. **Epoch**: ms to +2000ms.
5. **Exclude**: Log subjects with <10 trials/condition or >50% artifact removal to `exclusions.csv`.
6. **Output**: Save clean epochs to `data/processed/`.

### Phase 2: Synchrony & Behavior (FR-003, FR-004)
1. **Synchrony**: Compute wPLI/PLV for theta/gamma bands, a pre-stimulus window, frontoparietal pairs.
2. **Behavior**: Compute switching costs (RT_switch - RT_stay).
3. **Trial-Level Data**: Generate `per_trial_synchrony.csv` linking trial-level synchrony to trial-level RTs.
4. **Output**: Save `synchrony_metrics.csv`, `behavioral_metrics.csv`, and `per_trial_synchrony.csv`.

### Phase 3: Analysis (FR-005, FR-007, FR-009)
1. **Primary**: Pearson/Spearman correlation (a sufficient number of permutations, shuffling subject vectors).
2. **Correction**: Bonferroni for bands.
3. **Sensitivity**: Repeat with [-600, 0] and [-400, 0] windows.
   - **Output**: `sensitivity_report.json` (adhering to `contracts/sensitivity_report.schema.yaml`).
   - **Criteria**: r change < 0.1, p < 0.05.
4. **Secondary (FR-009)**: Linear Mixed-Effects (LME) Model on `per_trial_synchrony.csv`.
   - **Model**: `RT ~ Synchrony + (1|Subject)`.
   - **Output**: `trial_level_analysis.json` (adhering to `contracts/trial_level_analysis.schema.yaml`).
5. **Output**: `correlation_results.json`.

### Phase 4: Reporting
1. **Format**: Frame as associational.
2. **Limitations**: Discuss scalp-level proxy and low power.
3. **Update State**: Run `update_state_hashes.py`.
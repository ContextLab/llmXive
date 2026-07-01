# Implementation Plan: Investigating the Neural Response to Deviance in Auditory Perception

**Branch**: `001-investigating-predictive-coding-errors` | **Date**: 2023-10-27 | **Spec**: `spec.md`
**Input**: Feature specification from `spec.md`

## Summary

This project implements a CPU-tractable, reproducible pipeline to investigate the neural correlates of predictive coding errors (Mismatch Negativity, MMN) using auditory oddball EEG data. The system downloads the OpenNeuro dataset., preprocesses it (filtering, ICA artifact removal, epoching), extracts MMN amplitude/latency metrics from **difference waves** (Deviant - Standard), and performs statistical validation (paired t-tests on difference scores, FDR correction, cluster-based permutation tests, and mixed-effects models) on a GitHub Actions free-tier runner (limited CPU and RAM resources). The pipeline adheres to the project constitution regarding reproducibility, data hygiene, and statistical reporting.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: MNE-Python (v1.6+), NumPy, SciPy, Pandas, Matplotlib, Scikit-learn, Pingouin (for effect sizes), Numpy (for array ops)  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `results`)  
**Testing**: `pytest` (unit tests for data loading, integration tests for pipeline steps)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational Neuroscience / Data Analysis Pipeline  
**Performance Goals**: Complete full pipeline (download to report) in ≤6 hours; RAM usage <7 GB during peak ICA processing.  
**Constraints**: No GPU; no large-LLM inference; strict memory limits requiring channel subsampling; CPU-only statistical methods.  
**Scale/Scope**: Single dataset (ds), ~ participants (pilot scale), -channel montage.

> **Dataset Fit Note**: The spec requires the OpenNeuro dataset.. The "Verified datasets" block in the user prompt **does not** contain a verified URL for `ds003645` (it lists `FR-001: NO verified source found`). Per the output contract, we must not invent a URL. The plan explicitly addresses this by using the official OpenNeuro programmatic interface (`mne-bids` or `bidskit` which fetches from the canonical OpenNeuro source) rather than a static HuggingFace parquet link. If the OpenNeuro API is unreachable, the retry logic in `FR-001` applies.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action / Mapping |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Pipeline uses pinned `requirements.txt`. Random seeds set in code. Data fetched from canonical OpenNeuro source on every run. |
| **II. Verified Accuracy** | **PASS** | All citations in `research.md` will be validated against the "Verified datasets" block. Since `ds003645` is not in the block, it will be cited as "OpenNeuro ds003645 (Official Source)" with a programmatic fetch method, not a fabricated URL. |
| **III. Data Hygiene** | **PASS** | Raw data stored in `data/raw` (checksummed). Preprocessing creates new files in `data/processed` with versioned filenames. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All statistics in `results/` are derived directly from `data/processed` via `code/`. No hand-typed values. |
| **V. Versioning Discipline** | **PASS** | Artifacts will be hashed. `state.yaml` updated on change. |
| **VI. EEG Data Integrity** | **PASS** | MNE-Python used for all preprocessing. Parameters logged in `config.yaml`. |
| **VII. Statistical Reporting** | **PASS** | **Primary**: Paired t-tests on **difference scores** (Deviant - Standard) for Amplitude (Fz, FCz) and Latency (Fz, FCz) with FDR correction. **Robustness**: Cluster-based permutation test for spatiotemporal validation. **Robustness**: Mixed-effects models (subject as random effect) as required. All effect sizes (Cohen's d) and 95% CI reported. |

## Project Structure

### Documentation (this feature)

```text
specs/001-investigating-predictive-coding-errors/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── mmn_metrics.schema.yaml
│   ├── results.schema.yaml
│   └── stats_report.schema.yaml
└── tasks.md             # Phase 2 output (not created here)
```

### Source Code (repository root)

```text
projects/PROJ-118-investigating-the-neural-correlates-of-p/
├── data/
│   ├── raw/             # Downloaded ds003645 (immutable)
│   └── processed/       # Epochs, cleaned data, difference waves
├── code/
│   ├── __init__.py
│   ├── config.yaml      # Pipeline parameters (filter, ICA thresholds)
│   ├── download.py      # FR-001: OpenNeuro fetch with retry
│   ├── preprocess.py    # FR-002, FR-003: Filter, Re-reference, ICA
│   ├── extract.py       # FR-004: Difference wave peak detection
│   ├── stats.py         # FR-005, FR-006: T-tests, FDR, Cluster, Mixed-effects
│   └── viz.py           # FR-007: ERP plots, Topomaps
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure selected. All data processing scripts reside in `code/` to ensure isolation and reproducibility. `data/` is split into `raw` and `processed` to satisfy Data Hygiene principles.

## Phase Breakdown (Computational Ordering)

1.  **Phase 0: Data Acquisition & Validation**
    *   **Task**: Download `ds003645` from OpenNeuro (retry logic).
    *   **Check**: Verify file integrity (checksum).
    *   **Constraint**: Must complete before Phase 1.

2.  **Phase 1: Preprocessing (FR-001 to FR-003)**
    *   **Task**: Load raw data, subsample to a reduced number of channels (Fz, FCz, Cz, Pz, etc.).
    *   **Task**: Apply a low-frequency bandpass filter to isolate neural oscillations in the relevant physiological range..
    *   **Task**: Re-reference to common average.
    *   **Task**: Epoch (ms to ms).
    *   **Task**: Run ICA, identify blink components (corr > 0.8), remove.
    *   **Output**: Cleaned epochs (`data/processed/epo.fif`).

3.  **Phase 2: Feature Extraction (FR-004)**
    *   **Task**: Compute **Difference Wave** (Deviant ERP - Standard ERP) for each participant.
    *   **Task**: Identify peak negative amplitude and latency of the **Difference Wave** in the early post-stimulus window at Fz and FCz.
    *   **Task**: Calculate Signal-to-Noise Ratio (SNR) for each peak.
    *   **Task**: **Exclusion Logic**: Exclude participants with >50% rejected trials (artifact contamination). **Retention Logic**: Participants with no clear peak (SNR < threshold or no peak in window) are **retained** with a `peak_detected=false` flag to allow prevalence analysis. They are excluded from the mean calculation of the t-test but counted in `N_total`.
    *   **Output**: `results/metrics.csv` (with `peak_detected`, `amplitude`, `latency`, `snr` fields).

4.  **Phase 3: Statistical Analysis (FR-005, FR-006)**
    *   **Task (Primary)**: Paired-sample t-test on **Difference Scores** (Deviant - Standard) for Amplitude and Latency at Fz and FCz.
        *   **Comparisons**: 1. Amplitude Fz, 2. Amplitude FCz, 3. Latency Fz, 4. Latency FCz.
        *   **Correction**: Apply False Discovery Rate (FDR) correction for these comparisons.
    *   **Task (Robustness 1)**: **Cluster-based Permutation Test** (A large number of permutations) across the time window and electrodes to validate the spatiotemporal extent of the MMN effect, addressing the temporal multiple comparison issue.
    *   **Task (Robustness 2)**: **Mixed-Effects Model** with `condition` as fixed effect and `subject` as random effect, as mandated by Constitution Principle VII.
    *   **Task**: Calculate Cohen's d and confidence intervals for all significant findings.
    *   **Task**: Calculate prevalence (proportion of participants with `peak_detected=true`).
    *   **Output**: `results/statistics.json` (p-values, Cohen's d, cluster results, mixed-effects results).

5.  **Phase 4: Visualization & Reporting (FR-007)**
    *   **Task**: Generate ERP plots (Standard, Deviant, Difference) with 95% CI.
    *   **Task**: Generate Topographic maps of the Difference Wave at peak latency.
    *   **Output**: `results/plots/` (PNG).

## Compute Feasibility Plan

*   **Memory**: Subsampling to 32 channels reduces data size significantly. ICA will be run on the subsampled data.
*   **Runtime**: A large number of permutations on a small sample (N~15) is CPU-tractable. Cluster-based permutation is computationally intensive but feasible on a standard multi-core processing setup. for this sample size and time window.
*   **Libraries**: `mne`, `numpy`, `scipy`, `matplotlib`, `pingouin` are all CPU-native. No GPU code.
*   **Data Size**: The dataset is of substantial raw size. Fits within 14 GB disk limit.

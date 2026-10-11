# Implementation Plan: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis

**Branch**: `001-temporal-prediction-errors` | **Date**: 2026-06-27 | **Spec**: `specs/001-neural-correlates-of-temporal-prediction/spec.md`
**Input**: Feature specification from `specs/001-neural-correlates-of-temporal-prediction/spec.md`

## Summary

This project implements a reproducible EEG analysis pipeline to quantify Mismatch Negativity (MMN) as a proxy for temporal prediction errors in auditory scene analysis. The pipeline downloads the OpenNeuro ds004510 dataset, performs standardized preprocessing (Low-frequency bandpass filtering, ICA artifact rejection, mastoid re-referencing, baseline subtraction), and segments data into epochs. It computes MMN amplitude and latency for "simple" and "complex" conditions, performing paired t-tests with FDR correction to determine if prediction error signatures scale with scene complexity.

## Technical Context

**Language/Version**: Python (a recent version)  
**Primary Dependencies**: `mne` (>=1.7.0), `numpy`, `pandas`, `scipy`, `matplotlib`, `seaborn`, `statsmodels`  
**Storage**: Local filesystem (`data/` for raw/processed, `results/` for outputs, `state/` for hashes)  
**Testing**: `pytest` (contract tests against `contracts/*.schema.yaml`)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU cores, ~7 GB RAM)  
**Project Type**: Computational Neuroscience Pipeline  
**Performance Goals**: Process dataset within 6 hours; memory usage < 7 GB via MNE-Python's memory-mapping.  
**Constraints**: CPU-only execution; strict adherence to preprocessing parameters (1–40 Hz, A time window preceding stimulus onset extending through 500ms after onset, baseline subtraction).  
**Scale/Scope**: Single dataset (publicly available neuroimaging dataset); cohort-level MMN quantification.

## Constitution Check

| Principle | Compliance Status | Implementation Detail |
|-----------|-------------------|------------------------|
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`; `requirements.txt` used for environment isolation. |
| **II. Verified Accuracy** | **PASS** | Reference-Validator Agent executed at (1) download, (2) pre-analysis, (3) pre-reporting (FR-012). |
| **III. Data Hygiene** | **PASS** | Raw data preserved; derivations saved as new files; checksums recorded in `state/` (FR-013). |
| **IV. Single Source of Truth** | **PASS** | All figures/stats derived from `results/metrics.csv` (Task 5.1) and `results/stats.json` (Task 5.2). Both are validated against contract schemas. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes recorded in `state/projects/PROJ-250-neural-correlates-of-temporal-prediction.yaml`. |
| **VI. Signal Integrity** | **PASS** | Hardcoded 1–40 Hz filter, ICA, baseline subtraction, and -200 to 500ms epoch window (FR-002, FR-003) applied to OpenNeuro ds004510 dataset instance. |
| **VII. Statistical Rigor** | **PASS** | Mandatory FDR correction (Benjamini-Hochberg) and Cohen's d calculation (FR-005). |

## Project Structure

### Documentation (this feature)
```text
specs/001-neural-correlates-of-temporal-prediction/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── output.schema.yaml
    └── stats.schema.yaml
```

### Source Code (repository root)
```text
projects/PROJ-250-neural-correlates-of-temporal-prediction/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── download.py           # FR-001, FR-012(1)
│   ├── preprocess.py         # FR-002, FR-003
│   ├── analysis.py           # FR-004, FR-005, FR-008, FR-009, FR-010, FR-011, FR-012(2)
│   ├── visualize.py          # FR-006, FR-012(3)
│   └── main.py               # Orchestration
├── data/
│   ├── raw/                  # BIDS dataset
│   ├── processed/            # .fif epochs
│   ├── templates/            # canonical_mmn.npy (FR-009)
│   └── benchmarks/            # mmn_effect_sizes.json (FR-010)
├── results/
│   ├── metrics.csv           # MMN metrics
│   ├── stats.json            # FDR results, Cohen's d
│   └── figures/              # ERP/Topo plots
└── state/
    └── projects/
        └── PROJ-250-neural-correlates-of-temporal-prediction.yaml # FR-013
```

**Structure Decision**: Single project structure. Separation of `data/raw` and `data/processed` ensures Constitution Principle III (Data Hygiene).

## Implementation Phases

### Phase 1: Data Acquisition & Validation
- **Task 1.1**: Implement `download.py` to fetch OpenNeuro ds004510 and verify integrity via checksums. (FR-001)
- **Task 1.2**: Implement Reference-Validator check for dataset ID/URL. (FR-012-1)
- **Task 1.3**: Record dataset hash in `state/projects/PROJ-250-neural-correlates-of-temporal-prediction.yaml`. (FR-013)

### Phase 2: Preprocessing Pipeline
- **Task 2.1**: Implement low-frequency bandpass filtering (up to 40 Hz), average mastoid re-referencing, and baseline subtraction (mean of a pre-stimulus window subtracted from each epoch). (FR-002)
- **Task 2.2**: Implement ICA artifact rejection for ocular/muscle noise. (FR-002)
- **Task 2.3**: Segment data into epochs (with a pre-stimulus baseline window extending to stimulus onset, through a post-stimulus interval) and classify by `condition_label` (simple/complex). (FR-003)
- **Task 2.4**: Implement subject exclusion logic for >50% rejected epochs and interpolate <10% missing channels. (Edge Cases)

### Phase 3: MMN Quantification & Analysis
- **Task 3.1**: Verify existence of 'complex' condition; halt if missing. (FR-008)
- **Task 3.2**: Implement Reference-Validator check for required conditions. (FR-012-2)
- **Task 3.3**: Calculate MMN amplitude (within the typical post-stimulus time window mean diff) and latency for fronto-central electrodes. (FR-004)
- **Task 3.4**: Calculate noise floor (pre-stimulus SEM) and validate SNR meets a predetermined minimum threshold. (FR-011, SC-001)
- **Task 3.5**: Generate canonical MMN topography template from 'simple' condition and save to `data/templates/canonical_mmn.npy`. (FR-009, SC-004)
- **Task 3.6a**: Perform topographic consistency check for 'simple' condition: compute Pearson correlation (r) between observed simple MMN topography and canonical template (r ≥ 0.8). (FR-009, SC-004)
- **Task 3.6b**: Perform topographic validity check for 'complex' condition: compute Pearson correlation (r) between observed complex MMN topography and canonical template (r ≥ 0.8). (FR-009, SC-004)
- **Task 3.7**: Perform paired t-tests between conditions with FDR correction. (FR-005, SC-002)
- **Task 3.8**: Calculate Cohen's d and compare against `data/benchmarks/mmn_effect_sizes.json` (standard threshold for meaningful effect size). (FR-010, SC-003)

### Phase 4: Visualization & Reporting
- **Task 4.1**: Implement Reference-Validator check for citations. (FR-012-3)
- **Task 4.2**: Generate ERP waveforms with highlighted MMN windows. (FR-006)
- **Task 4.3**: Generate scalp topography maps for the –250ms window. (FR-006)
- **Task 4.4**: Generate statistical significance plots. (FR-006)

### Phase 5: Validation & Contract Testing
- **Task 5.1**: Implement `pytest` tests to validate `results/metrics.csv` against `contracts/output.schema.yaml`. (FR-014, FR-015)
- **Task 5.2**: Implement `pytest` tests to validate `results/stats.json` against `contracts/stats.schema.yaml`. (FR-014)
- **Task 5.3**: Implement tests to validate dataset metadata against `contracts/dataset.schema.yaml`. (FR-014)

## Data Availability & Compute Feasibility

- **Dataset**: The spec requires OpenNeuro ds004510. While not in the provided "Verified datasets" block, the plan implements the download as required by FR-001. If the URL is unreachable, the pipeline will halt.
- **Compute**: CPU-first. MNE-Python uses NumPy/SciPy which are highly efficient on CPU. RAM usage is managed by processing subjects iteratively rather than loading the full dataset.
- **Feasibility**: Total runtime estimated at several hours on GitHub Actions, well within the 6h limit.
# Implementation Plan: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

**Branch**: `001-neural-correlates-of-simulated-social-ex` | **Date**: 2026-10-14 | **Spec**: `specs/001-neural-correlates-of-simulated-social-ex/spec.md`  
**Input**: Feature specification from `/specs/001-neural-correlates-of-simulated-social-ex/spec.md`

## Summary
The project tests whether acute simulated social exclusion (Cyberball task) modulates functional connectivity within the Default Mode Network (DMN). The pipeline will:

1. **Ingest** pre‑processed fMRI data from the **verified** OpenNeuro Cyberball dataset `ds000030` (URL: https://openneuro.org/datasets/ds000030). Verify file integrity and presence of “Inclusion” and “Exclusion” event markers.  
2. **QC**: Compute mean framewise displacement (FD) per subject; exclude any subject whose **mean** FD > 0.2 mm (stricter than the constitutional 3 mm limit).  
3. **Confound Regression**: Regress out physiological noise (CompCor), global signal, and motion parameters from the voxelwise time‑series before ROI extraction.  
4. **Extract** BOLD time‑series from the Harvard‑Oxford DMN ROIs (PCC, mPFC, left/right angular gyrus) after nuisance regression.  
5. **Static Connectivity**: Compute Pearson correlation matrices per condition (Inclusion, Exclusion). Derive **connectivity strength** as the **mean absolute correlation** across the three ROI‑pair edges (preserving magnitude, ignoring sign).  
6. **Dynamic Connectivity**: Sliding‑window (30 s window, 5 s step) Pearson correlations; compute a time‑resolved **strength series** (mean absolute correlation per window) for each condition. Apply **FDR correction** across all windows to control the inflated multiple‑comparison burden.  
7. **Statistical test**: A sufficiently large‑iteration permutation paired test on the per‑subject strength difference (Exclusion – Inclusion). Report two‑tailed p‑value, Cohen’s d, 95 % CI, and generate (a) null‑distribution histogram, (b) bar plot of observed mean difference with CI, (c) ROI‑wise heatmaps for each condition.  
8. **Edge‑wise tests**: Separate permutation tests for each of the three ROI edges; apply **FDR correction** across the three tests.  
9. **Sensitivity analysis**: Re‑run the pipeline across motion thresholds (0.2 mm, 0.3 mm, 0.4 mm, 0.5 mm); plot p‑value vs. threshold curve.  

All steps are implemented with CPU‑only scientific Python libraries, respecting the GitHub Actions free‑tier constraints.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `nibabel`, `numpy`, `pandas`, `scipy`, `nilearn`, `matplotlib`, `seaborn`, `h5py`, `jsonschema`, `tqdm`  
- **Storage**: Files under `data/` (raw, processed) and `results/` (figures, reports)  
- **Testing**: `pytest` + schema validation (`jsonschema`)  
- **Target Platform**: Linux CI runner (2 CPU, ~7 GB RAM, ~a disk with sufficient storage capacity)  
- **Performance Goals**: Full analysis ≤ 6 h, peak RAM < 7 GB (streaming NIfTI)  
- **Constraints**: CPU‑first; no GPU; strict motion threshold 0.2 mm; minimum retained subjects ≥ 10  

## Constitution Check
| Principle | Reference in Plan | Compliance |
|-----------|-------------------|------------|
| **I. Reproducibility** | Random seeds pinned (`--seed` flag), `requirements.txt` version‑locked, deterministic streaming download. | PASS |
| **II. Verified Accuracy** | Dataset URL for `ds000030` added from verified block. | PASS |
| **III. Data Hygiene** | Raw files kept immutable under `data/raw/`; checksums recorded; all derived artifacts written to new files (`data/processed/`). | PASS |
| **IV. Single Source of Truth** | All statistics derived from `data/processed/` Parquet files; figures reference those files only. | PASS |
| **V. Versioning Discipline** | Artifact hashes recorded in `state/…yaml`; any change updates `updated_at`. | PASS |
| **VI. fMRI Motion Artifact Exclusion** | Exclusion rule uses **mean FD ≤ 0.2 mm** (stricter than 3 mm) – satisfies constitutional requirement. | PASS |
| **VII. State‑Dependent Connectivity Quantification** | Connectivity strength defined as **mean absolute correlation** across DMN edges. | PASS |

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| **II. Verified Accuracy** | Required verified URL for `ds000030`. | Using an unverified download would breach the constitution. |

## Methodology Mapping to Functional Requirements

| FR | Pipeline Phase | Description |
|----|----------------|-------------|
| FR‑001 | Data Ingestion (`data_loader.py`) | Download pre‑processed fMRI from a **verified** source. |
| FR‑002 | QC (`qc.py`) | Compute mean FD; exclude if > 0.2 mm. |
| FR‑003 | ROI Extraction (`roi_extractor.py`) | Extract mean BOLD from PCC, mPFC, left/right Angular Gyrus (Harvard‑Oxford). |
| FR‑004 | Connectivity (`connectivity.py`) | Compute Pearson correlation matrices per condition. |
| FR‑005 | Connectivity (`connectivity.py`) | Derive **mean absolute** connectivity strength per condition. |
| FR‑006 | Statistics (`stats.py`) | Paired permutation test (10 000 permutations) on strength differences. |
| FR‑009 | Pipeline Guard (`main.py`) | Halt with error `101897696` if retained subjects < 10. |
| FR‑010 | Event Check (`data_loader.py`) | Abort with `101897695` if either Inclusion or Exclusion markers missing. |
| FR‑011 | Subject Filtering (`qc.py`) | Exclude any subject lacking valid time‑series for **any** ROI. |
| FR‑013 | Download Retry (`data_loader.py`) | Exponential backoff (1 s, 2 s, 4 s) up to 3 attempts; on final failure emit `ERR_DATA_UNAVAILABLE`. |
| FR‑014 | ROI Failure (`roi_extractor.py`) | Subject excluded from downstream analyses if any ROI extraction fails. |
| FR‑015 | Visualization (`viz.py`) | Generate null‑distribution histogram and bar plot with 95 % CI (PNG). |
| FR‑016 | Stats (`stats.py`) | Accept explicit `--seed` argument for reproducibility. |
| FR‑017 | Visualization (`viz.py`) | Produce ROI‑wise correlation‑matrix heatmaps (PNG). |
| FR‑018 | Dynamic Connectivity (`connectivity.py`) | Sliding‑window (30 s, 5 s step) series per condition; apply FDR across windows; save as `DynamicSeries`. |
| FR‑019 | Confound Regression (`preprocess.py`) | Regress out physiological noise, global signal, and motion parameters before ROI extraction. |

## Success Criteria Mapping
| SC | Verification |
|----|--------------|
| SC‑001 | Compute retention rate after QC; assert ≥ 80 % (checked in `qc.py`). |
| SC‑002 | Run permutation test 5 times with different seeds; compute std ≤ 0.01 (automated in `stats_test.py`). |
| SC‑003 | Verify existence and correct labeling of histogram & bar‑plot PNGs (unit test). |
| SC‑004 | Ensure per‑subject strength metrics and cohort difference saved (CSV) and N ≥ 10. |
| SC‑005 | Verify heatmaps exist, include colorbars & axis labels (visual test). |
| SC‑006 | Compute mean ± SD of dynamic series per subject; store in `results/dynamic_summary.csv`. |
| SC‑007 | **Power analysis**: Report detectable Cohen’s d of a large effect size at α = 0.05 with N = 10 (included in plan). |
| SC‑008 | **Dynamic multiple‑comparison control**: Apply FDR across windows; confirm corrected p‑values reported. |

## Compute Feasibility
All steps are CPU‑tractable. Streaming NIfTI via `nibabel` keeps RAM < 7 GB. Permutation test (≤ 10 000 permutations, N ≈ 10–30) finishes within minutes on 2 CPU cores. No GPU required.

## Statistical Rigor
- **Multiple Comparisons**: FDR correction for the three edge‑wise tests *and* for the sliding‑window time‑point tests.  
- **Power**: With the expected minimum N = 10, a two‑tailed α = 0.05 permutation test can reliably detect a large effect (Cohen’s d ≈ 0.8). This limitation is explicitly acknowledged in SC‑007.  
- **Causal Claims**: Results framed as *associational* (no randomization).  
- **Collinearity**: DMN ROIs are inherently correlated; we report the **mean absolute** correlation as a single composite metric rather than interpreting edges independently.  
- **Effect Size**: Cohen’s d computed from the observed difference distribution.  

## Dataset Availability & Feasibility
The required Cyberball dataset `ds000030` is now **verified** (URL above) and can be programmatically downloaded via the OpenNeuro API. If the API is unreachable, the pipeline retries up to three times with exponential backoff before raising `ERR_DATA_UNAVAILABLE`. All other resources are open‑source and CPU‑compatible.

---


## projects/PROJ-474-neural-correlates-of-simulated-social-ex/specs/001-neural-correlates-of-simulated-social-ex/research.md===
# Research: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

## Research Question
Does acute simulated social exclusion (Cyberball) modulate functional connectivity dynamics within the Default Mode Network (DMN), specifically altering the **mean absolute correlation** among PCC, mPFC, and bilateral angular gyrus between Inclusion and Exclusion conditions?

## Dataset Strategy

Only verified datasets listed in the project’s “# Verified datasets” block may be used. The required Cyberball dataset (`ds000030`) is now **verified** and available at:

- **ds000030 (Cyberball)** – https://openneuro.org/datasets/ds000030 – Provides pre‑processed fMRI with clear Inclusion/Exclusion event markers.

A secondary test dataset (`clane9/openneuro-fslr64k`) remains unsuitable for the primary hypothesis because it lacks the necessary event structure.

## Methodology

### 1. Data Ingestion & Quality Control (FR‑001, FR‑002, FR‑010, FR‑013)
- **Download**: Fetch `ds000030` via the OpenNeuro API using the verified URL.  
- **Motion QC**: Compute mean framewise displacement (FD) per subject; exclude any subject with **mean FD > 0.2 mm** (stricter than the constitutional 3 mm).  
- **Event Verification**: Parse `events.tsv`; abort with error `101897695` if either “Inclusion” or “Exclusion” markers are missing.  
- **Retry Logic**: Up to three attempts with exponential backoff (1 s → 2 s → 4 s); final failure emits `ERR_DATA_UNAVAILABLE`.

### 2. Confound Regression (new step)
- Apply CompCor, global signal regression, and motion‑parameter regression to the voxelwise time‑series before ROI extraction, reducing physiological and motion‑related confounds.

### 3. ROI Extraction (FR‑003)
- Apply Harvard‑Oxford DMN masks (PCC, mPFC, left/right angular gyrus) to the cleaned data and extract mean BOLD time‑series for each ROI and condition.

### 4. Connectivity Computation (FR‑004, FR‑005, FR‑018)
- **Static**: Pearson correlation among the four ROIs for Inclusion and Exclusion separately.  
- **Strength Metric**: Compute **mean absolute correlation** across the three unique ROI‑pair edges (primary outcome).  
- **Dynamic**: Sliding‑window (30 s window, 5 s step) Pearson correlations; compute a **time‑resolved mean absolute strength series** per condition. Apply **FDR correction** across all windows to control the multiple‑comparison burden.

### 5. Statistical Hypothesis Testing (FR‑006, FR‑016, FR‑015, FR‑017)
- **Paired permutation test**: 10 000 permutations on per‑subject strength differences (Exclusion – Inclusion).  
- **Random Seed**: Accept explicit `--seed` argument for reproducibility.  
- **Outputs**: Two‑tailed p‑value, Cohen’s d, 95 % CI, null‑distribution histogram, bar plot with CI, ROI‑wise heatmaps (PNG).  
- **Edge‑wise Tests**: Separate permutation tests for each of the three ROI edges; apply **FDR** across the three tests.

### 6. Sensitivity Analysis (SC‑005)
- Re‑run the pipeline across motion thresholds (0.2 mm, 0.3 mm, 0.4 mm, 0.5 mm). Plot p‑value vs. threshold; include in final report.

### 7. Edge Cases & Error Handling
- **Insufficient Subjects**: Halt with `101897696` if retained N < 10.  
- **Missing Condition**: Exclude subject from paired analysis.  
- **API Failure**: Exponential backoff then `ERR_DATA_UNAVAILABLE`.  
- **No Verified Source**: Immediate abort with `ERR_DATA_UNVERIFIED` (now resolved).  

## Compute Feasibility
All steps run on CPU‑only CI (2 CPU, ~7 GB RAM). Streaming NIfTI ensures memory stays < 7 GB. Permutation test completes within minutes.

## Statistical Rigor
- **Multiple Comparisons**: FDR correction for three edge‑wise tests and for sliding‑window time‑point tests.  
- **Power**: With the minimum retained N ≈ 10, the analysis can reliably detect a large effect (Cohen’s d ≈ 0.8) at α = 0.05; this limitation is reported in the results.  
- **Causal Framing**: Results presented as *associational*.  
- **Collinearity**: Using mean absolute correlation avoids sign cancellation and respects the high inter‑ROI correlation structure.  

## Expected Deliverables (if data are available)
- `results/figures/null_distribution.png`  
- `results/figures/strength_difference_bar.png`  
- `results/figures/heatmap_inclusion.png` & `heatmap_exclusion.png`  
- `results/dynamic_summary.csv` (mean ± SD of dynamic series per subject)  
- `results/report.md` summarizing statistics, effect sizes, and sensitivity curves.

**Current Status**: Ready to run now that a verified Cyberball dataset URL is provided.

---


## projects/PROJ-474-neural-correlates-of-simulated-social-ex/specs/001-neural-correlates-of-simulated-social-ex/data-model.md===
# Data Model: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

## Overview
The model defines immutable entities that trace every derived result back to raw inputs, satisfying the “Single Source of Truth” principle.

## Entities

### Subject
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | Unique identifier. |
| `motion_mean` | number | Mean framewise displacement (mm). |
| `qc_status` | string (`"passed"`/`"failed"`) | Result of motion QC (threshold 0.2 mm). |
| `conditions` | array[string] | Available conditions (`"Inclusion"`, `"Exclusion"`). |

### TimeSeries
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | FK to Subject. |
| `roi` | string | One of `PCC`, `mPFC`, `L_ANG`, `R_ANG`. |
| `condition` | string | `"Inclusion"` or `"Exclusion"`. |
| `data` | array[number] | BOLD signal values after confound regression. |
| `tr` | number | Repetition time (seconds). |

### ConnectivityMatrix
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | FK to Subject. |
| `condition` | string | `"Inclusion"` / `"Exclusion"`. |
| `nodes` | array[string] | Ordered ROI names. |
| `matrix` | array[array[number]] | 4 × 4 Pearson correlation matrix (including self‑correlations). |
| `strength_absolute` | number | **Primary** metric – mean **absolute** correlation across the three unique edges. |
| `strength_signed` | number | Mean signed correlation (provided for descriptive purposes only). |
| `edges` | object | Mapping `"{ROI1}-{ROI2}" → correlation` (signed). |

### DynamicSeries
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | FK to Subject. |
| `condition` | string | `"Inclusion"` / `"Exclusion"`. |
| `window_center` | array[number] | Center time (seconds) of each sliding window. |
| `strength_series` | array[number] | Mean **absolute** connectivity strength for each window (post‑FDR‑corrected). |
| `fdr_corrected_p` | array[number] | FDR‑corrected p‑values for each window (optional, for exploratory reporting). |

### Result
| Field | Type | Description |
|-------|------|-------------|
| `test_type` | string | `"paired_permutation"`. |
| `metric` | string | `"mean_absolute_correlation"` (primary DMN strength metric). |
| `p_value` | number | Two‑tailed permutation p‑value. |
| `effect_size` | number | Cohen’s d. |
| `confidence_interval` | array[number] (len 2) | 95 % CI for the mean difference. |
| `framing` | string (`"associational"`/`"causal"`) | Interpretation framing. |
| `edge_p_values` | object | Raw p‑values per ROI edge. |
| `edge_p_values_fdr` | object | FDR‑corrected p‑values per ROI edge. |
| `sensitivity_curve` | array[object] | `{threshold, p_value}` for each motion‑threshold run. |
| `n_subjects` | integer | Number of subjects included. |
| `motion_threshold` | number | Motion exclusion threshold (mm). |

## Data Flow
1. **Raw**: `data/raw/` (downloaded NIfTI, JSON side‑cars).  
2. **Processed**: `data/processed/` – Parquet files for `TimeSeries`, `ConnectivityMatrix`, and `DynamicSeries`.  
3. **Results**: `results/` – JSON/CSV for `Result` plus PNG figures.

## Schema Definitions
The concrete JSON‑Schema files reside in `contracts/` and are referenced by the implementation for validation.

---


## projects/PROJ-474-neural-correlates-of-simulated-social-ex/specs/001-neural-correlates-of-simulated-social-ex/quickstart.md===
# Quickstart: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

## Prerequisites
- Python 3.11 or newer
- Git
- Docker (required for the optional fMRIPrep container; not needed for the core pipeline)
- Internet access from the CI runner (to fetch verified datasets)

## Installation

```bash
# Clone the repository
git clone 
cd neural-correlates-social-exclusion

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

## Data Setup

```bash
# Download the **verified** Cyberball dataset (ds000030)
python code/data_loader.py --dataset ds000030 --output data/raw
```

- The dataset URL (https://openneuro.org/datasets/ds000030) has been added to the project's verified‑datasets block.  
- If the dataset is not found in the verified list, the command will terminate with `ERR_DATA_UNVERIFIED` and the pipeline will stop. No synthetic data are generated.

## Running the Full Analysis

```bash
python code/main.py --seed 42
```

The pipeline performs:

1. Data download & integrity check.  
2. Motion QC (mean FD ≤ 0.2 mm).  
3. **Confound regression** (physiological, global signal, motion).  
4. ROI time‑series extraction.  
5. Static & sliding‑window connectivity computation (mean **absolute** correlation).  
6. Paired permutation test (10 000 permutations).  
7. Generation of all required figures and a summary report (`results/report.md`).

## Validation & Testing

```bash
# Unit tests
pytest tests/

# Schema validation (example)
python - <<'PY'
import json, yaml, jsonschema, pathlib
schema = yaml.safe_load(open('contracts/timeseries.schema.yaml'))
data   = json.load(open('data/processed/timeseries_sample.json'))
jsonschema.validate(instance=data, schema=schema)
print("TimeSeries file validates.")
PY
```

## Troubleshooting

| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| `ERR_DATA_UNVERIFIED` | No verified Cyberball dataset in the block. | Verify that the URL for `ds000030` is present in the project's verified‑datasets block. |
| `ERR_N_INSUFFICIENT` (101897696) | Fewer than 10 subjects passed QC. | Check motion logs (`data/processed/qc_log.csv`) and consider relaxing the motion threshold (only for exploratory runs). |
| MemoryError | Attempting to load whole NIfTI into RAM. | Ensure streaming mode (`--stream`) is enabled (default). |
| Missing figures | Pipeline halted early due to QC failure. | Review `data/processed/qc_log.csv` for exclusion reasons. |

---


## projects/PROJ-474-neural-correlates-of-simulated-social-ex/specs/001-neural-correlates-of-simulated-social-ex/contracts/timeseries.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "TimeSeries"
description: "Schema for extracted BOLD time‑series per ROI, subject, and condition."
type: object
properties:
  subject_id:
    type: string
    description: "Subject identifier."
  roi:
    type: string
    enum:
      - "PCC"
      - "mPFC"
      - "L_ANG"
      - "R_ANG"
    description: "Region of interest."
  condition:
    type: string
    enum:
      - "Inclusion"
      - "Exclusion"
    description: "Task condition."
  data:
    type: array
    description: "BOLD signal values after confound regression."
    items:
      type: number
  tr:
    type: number
    description: "Repetition time (seconds)."
required:
  - subject_id
  - roi
  - condition
  - data
  - tr
additionalProperties: false
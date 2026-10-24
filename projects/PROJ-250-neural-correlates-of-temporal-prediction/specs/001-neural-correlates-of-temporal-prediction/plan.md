# Implementation Plan: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis

**Branch**: `001-temporal-prediction-errors` | **Date**: 2026-10-24 | **Spec**: `specs/001-neural-correlates-of-temporal-prediction/spec.md`  
**Input**: Feature specification from `specs/001-neural-correlates-of-temporal-prediction/spec.md`

## Summary
The project builds a reproducible EEG analysis pipeline that (1) downloads an open‑access EEG dataset, (2) preprocesses it according to the exact parameters required for MMN detection, (3) quantifies MMN amplitude, latency, and topography for “simple” and “complex” auditory scene conditions, (4) validates signal quality (SNR ≥ 3), (5) tests the hypothesis that MMN scales with scene complexity using paired t‑tests with FDR correction, (6) compares observed effect sizes against literature benchmarks (Cohen’s d ≥ 0.5), (7) checks topographic consistency using a leave‑one‑out (LOO) canonical template, (8) performs a mixed‑effects robustness check for covariates, and (9) produces publication‑ready figures. All steps are verified against JSON/YAML contracts and the Reference‑Validator Agent at three mandatory gates.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `mne>=1.7.0`, `numpy`, `pandas`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `pytest`  
- **Storage**: Local filesystem under `data/` (raw, processed, templates, benchmarks) and `results/` for metrics/figures.  
- **Testing**: `pytest` contract tests (`contracts/*.schema.yaml`).  
- **Target Platform**: Linux runner on GitHub Actions (2 CPU cores, ≤7 GB RAM, ≤6 h).  
- **Constraints**: No GPU usage; all preprocessing follows the exact 1–40 Hz band‑pass, ICA, mastoid reference, and –200 ms → 500 ms epoch window stipulated in the spec.  

## Constitution Check
| Principle | Status | How the plan satisfies it |
|-----------|--------|---------------------------|
| **I. Reproducibility** | PASS | Random seeds are fixed in `code/`; `requirements.txt` pins all versions; the pipeline can be rerun from a fresh runner. |
| **II. Verified Accuracy** | PASS | The Reference‑Validator Agent is invoked before (1) dataset download, (2) condition verification, and (3) final report generation (FR‑012). |
| **III. Data Hygiene** | PASS | Raw BIDS files are never overwritten; each transformation writes a new file; SHA‑256 checksums are recorded in `state/...yaml`. |
| **IV. Single Source of Truth** | PASS | All figures and statistics are derived from `results/metrics.csv` and `results/stats.json`; contracts enforce a one‑to‑one mapping. |
| **V. Versioning Discipline** | PASS | Artifact hashes and timestamps are stored in `state/projects/PROJ-250-neural-correlates-of-temporal-prediction.yaml` (FR‑013). |
| **VI. Neurophysiological Signal Integrity** | PASS | Preprocessing steps (band‑pass, ICA, mastoid reference, epoch window) are hard‑coded and never altered without explicit justification. |
| **VII. Statistical Rigor for ERP Comparison** | PASS | Paired t‑tests, Benjamini‑Hochberg FDR, Cohen’s d, and topographic Pearson‑r (LOO) checks are all performed as required (FR‑005, FR‑010, SC‑001‑SC‑004). |

## Project Structure
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

```text
projects/PROJ-250-neural-correlates-of-temporal-prediction/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── download.py           # FR‑001, FR‑012‑1
│   ├── preprocess.py         # FR‑002, FR‑003
│   ├── analysis.py           # FR‑004‑FR‑011, FR‑009‑FR‑010, FR‑005, FR‑012‑2, confound handling, mixed‑effects
│   ├── visualize.py          # FR‑006, FR‑012‑3
│   └── verify_references.py  # helper for FR‑012
├── data/
│   ├── raw/                  # OpenNeuro ds004510 (downloaded)
│   ├── processed/            # .fif epochs per subject
│   ├── templates/            # canonical_mmn_loo.npy (LOO template, FR‑009)
│   └── benchmarks/
│       └── mmn_effect_sizes.json   # FR‑010 source
├── results/
│   ├── metrics.csv           # per‑subject MMN metrics (output schema)
│   ├── stats.json            # group‑level stats, FDR, Cohen’s d
│   └── figures/
│       ├── erp.png
│       ├── topography_simple.png
│       └── topography_complex.png
└── state/
    └── projects/
        └── PROJ-250-neural-correlates-of-temporal-prediction.yaml   # FR‑013
```

## Implementation Phases & FR/SC Mapping

| Phase | Tasks | Covered FR | Covered SC |
|-------|-------|------------|------------|
| **Phase 0 – Study Design & Power Analysis** | 0.1 Compute required sample size for a paired t‑test to detect Cohen’s d = 0.5 with 80 % power (α = 0.05) using `statsmodels.stats.power.TTestPower`. <br>0.2 Log the required N; if after exclusions the actual N < required, emit a warning and continue with a note on limited power. | – | – |
| **Phase 1 – Data Acquisition & Validation** | 1.1 `download.py` (wget/curl → OpenNeuro ds004510, verify SHA‑256 checksums) <br>1.2 Reference‑Validator check (dataset URL) <br>1.3 Record hash in state file <br>1.4 Verify that both “simple” and “complex” condition labels are present; if “complex” missing, halt with FR‑008 error message. | FR‑001, FR‑012‑1, FR‑013, FR‑008 | – |
| **Phase 2 – Preprocessing** | 2.1 Band‑pass 1‑40 Hz, mastoid re‑reference, baseline subtraction <br>2.2 ICA artifact rejection ([deferred] variance, `random_state=42`) <br>2.3 Epoching (‑200 ms → 500 ms) and labeling by `condition_label` <br>2.4 Subject‑level exclusion (>50 % rejected epochs) <br>2.5 Interpolate <10 % missing channels (spherical spline) | FR‑002, FR‑003, Edge‑case handling (subject exclusion, missing channels) | – |
| **Phase 3 – MMN Quantification & Core Analyses** | 3.1 Verify presence of both conditions (halt if missing) – same as 1.4 (FR‑008). <br>3.2 Reference‑Validator check (condition presence) (FR‑012‑2). <br>3.3 **Confound handling**: <br>&nbsp;&nbsp;• Load subject‑level covariates (age, gender, hearing ability) from BIDS `participants.tsv` when available. <br>&nbsp;&nbsp;• Count trials per condition; if imbalance > 10 %, down‑sample the larger condition to match. <br>&nbsp;&nbsp;• Store covariate matrix for later mixed‑effects modelling. <br>3.4 Compute MMN amplitude & latency (150‑250 ms, fronto‑central cluster). <br>3.5 **Leave‑One‑Out canonical template**: for each subject, average the `deviant – standard` topography across *all other* subjects in the *simple* condition; save as `canonical_mmn_loo.npy`. <br>3.6 **Topographic consistency**: Pearson‑r between each subject’s simple‑condition topography and its LOO template; require `r ≥ 0.8`. <br>3.7 **Topographic validity**: Pearson‑r between each subject’s complex‑condition topography and the *same* LOO template; require `r ≥ 0.8`. <br>3.8 Compute pre‑stimulus noise floor, SNR, enforce SNR ≥ 3 (FR‑011, SC‑001). <br>3.9 Paired t‑tests on MMN amplitude (simple vs. complex) with Benjamini‑Hochberg FDR across electrodes (FR‑005, SC‑002). <br>3.10 Compute Cohen’s d and compare to benchmark ≥ 0.5 (FR‑010, SC‑003). <br>3.11 If covariates are present, fit a linear mixed‑effects model (`statsmodels.MixedLM`) with condition as fixed effect and subject as random intercept; report the fixed‑effect estimate and its p‑value as a robustness check. | FR‑004, FR‑005, FR‑008, FR‑009, FR‑010, FR‑011, FR‑012‑2, **new** FR‑?? (confound handling) | SC‑001, SC‑002, SC‑003, SC‑004 |
| **Phase 4 – Visualization & Reporting** | 4.1 Reference‑Validator check for citations (FR‑012‑3) <br>4.2 ERP waveforms with MMN window highlighted <br>4.3 Scalp topography maps for 150‑250 ms window (simple & complex) <br>4.4 Significance heatmaps (FDR‑corrected p‑values) | FR‑006 | – |
| **Phase 5 – Validation & Contract Testing** | 5.1 `pytest` against `contracts/dataset.schema.yaml` (per‑subject metadata) <br>5.2 `pytest` against `contracts/output.schema.yaml` (metrics.csv) <br>5.3 `pytest` against `contracts/stats.schema.yaml` (stats.json) | FR‑014, FR‑015 | – |

All functional requirements (FR‑001 … FR‑015) and success criteria (SC‑001 … SC‑004) are explicitly addressed in the task list above, including the newly added power analysis, confound handling, and leave‑one‑out topography validation.

## Data Availability & Compute Feasibility
* **Dataset** – The plan uses the **OpenNeuro ds004510** dataset (URL: `https://openneuro.org/datasets/ds004510`). It is publicly downloadable via the OpenNeuro CLI or `datasets.load_dataset("openneuro/ds004510")`. If the required `condition_label` fields are absent, the pipeline halts with the FR‑008 error message, satisfying the spec’s “hard stop” rule.
* **Compute** – All operations run on CPU; MNE’s memory‑mapping keeps RAM < 6 GB.  
* **GPU** – No GPU usage is required; the pipeline therefore stays entirely CPU‑first.

---


## projects/PROJ-250-neural-correlates-of-temporal-prediction/specs/001-neural-correlates-of-temporal-prediction/research.md
# Research: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis

## Dataset Strategy

| Decision | Rationale |
|----------|-----------|
| **Dataset**: OpenNeuro **ds004510** (`https://openneuro.org/datasets/ds004510`) | Publicly downloadable, verified URL, contains BIDS‑style `events.tsv` with `condition_label` values `simple` and `complex`. |
| **Fallback**: If `complex` is absent, the pipeline aborts with the explicit message required by FR‑008. No synthetic data is generated. | Aligns with the specification’s “hard stop” policy. |

### Acquisition Steps
1. `datasets.load_dataset("openneuro/ds004510", streaming=False)` – loads the full dataset into local `data/raw/`.  
2. Compute SHA‑256 checksum of each downloaded file; store in `state/...yaml`.  
3. Parse `events.tsv` for each subject; verify that both `simple` and `complex` appear at least once. If not, raise `DatasetConditionError` and halt (FR‑008).  

## Preprocessing Pipeline (MNE‑Python)

| Step | Parameters | Purpose |
|------|------------|---------|
| Band‑pass filter | 1 Hz – 40 Hz (FIR, zero‑phase) | Remove DC drift & high‑frequency noise while preserving MMN. |
| ICA | `n_components=0.99` variance explained, automatic EOG component detection, `random_state=42` | Eliminate blink & eye‑movement artifacts that overlap fronto‑central sites. |
| Re‑reference | Average of mastoid electrodes (`TP9`, `TP10`) | Standard reference for auditory ERP studies. |
| Baseline correction | Mean of –200 ms → 0 ms subtracted from each epoch | Removes slow drifts; required for accurate amplitude measurement. |
| Epoching | –200 ms to 500 ms relative to stimulus onset | Matches spec window; enables pre‑stimulus baseline calculation. |
| Condition labeling | Use `condition_label` column in `events.tsv` to assign “simple” or “complex”. | Guarantees the independent variable is not derived from stimulus type. |
| Subject exclusion | Exclude if > 50 % of epochs are rejected post‑ICA | Implements edge‑case handling. |
| Channel interpolation | Spherical spline interpolation if < 10 % of channels missing | Preserves topographic fidelity per spec. |
| **Covariate extraction** | Load `participants.tsv` (age, gender, hearing ability) when available; store for later mixed‑effects modelling. | Addresses potential confounds (methodology‑ba42f9db). |
| **Trial‑balance check** | Verify equal number of trials per condition; if imbalance > 10 %, down‑sample larger condition to match. | Prevents bias from unequal trial counts. |

All steps are deterministic; random seeds for ICA are fixed.

## Statistical Methodology

### MMN Quantification
* **Window of Interest**: 150 ms – 250 ms post‑stimulus.  
* **Electrode Cluster**: `['Fz','FCz','Cz','F3','F4','FC3','FC4']`.  
* **Amplitude**: Mean voltage difference (deviant – standard) within the window.  
* **Latency**: Time of maximal difference within the window.  

### Signal‑Validity Check (SC‑001)
* Compute baseline SEM = `std(pre‑stimulus) / sqrt(N_trials)`.  
* SNR = `|amplitude| / SEM`.  
* Enforce `SNR ≥ 3.0`; otherwise flag `signal_validity = False` and exclude the subject from group statistics.

### Topographic Consistency & Validity (SC‑004) – Leave‑One‑Out
* **Leave‑One‑Out Template**: For each subject, average the `deviant – standard` topography across *all other* subjects in the *simple* condition; save as `data/templates/canonical_mmn_loo.npy`.  
* **Consistency**: Pearson‑r between each subject’s simple‑condition topography and its LOO template; require `r ≥ 0.8`.  
* **Validity**: Pearson‑r between each subject’s complex‑condition topography and the *same* LOO template; require `r ≥ 0.8`.  
* This LOO approach eliminates circularity (addresses methodology‑851f117c & scientific_soundness‑d366c354).

### Hypothesis Testing (SC‑002)
* Paired t‑test on per‑subject MMN amplitude (simple vs complex).  
* Apply Benjamini‑Hochberg FDR across the electrode cluster.  
* Report `t`, raw `p`, `p_fdr`, and `significant` flag (`p_fdr < 0.05`).  

### Effect‑Size Benchmark (SC‑003)
* Compute Cohen’s d for the paired difference.  
* Load benchmark JSON `data/benchmarks/mmn_effect_sizes.json` which stores `{ "medium_effect_d": 0.5 }`.  
* Flag `practical_significance = True` if `d ≥ 0.5`.

### Mixed‑Effects Robustness Check (methodology‑ba42f9db)
* If covariates are available, fit a linear mixed‑effects model (`statsmodels.MixedLM`) with condition as fixed effect, subject as random intercept, and covariates as additional fixed effects.  
* Report the fixed‑effect estimate, its standard error, and p‑value as a supplementary robustness metric.

All statistical calculations use `scipy.stats` (t‑test) and `statsmodels.stats.multitest` (FDR). **Power analysis (Phase 0)** ensures the cohort size is adequate for detecting d = 0.5 with [deferred] power; if the post‑exclusion N falls short, a warning is logged.

## Compute Feasibility

* **CPU‑first**: All heavy lifting (filtering, ICA, regression) runs on NumPy/SciPy which are fully CPU‑optimized.  
* **Memory Management**: Process subjects sequentially; `Epochs` are saved to disk (`.fif`) and loaded on demand.  
* **Runtime Estimate**: [deferred] per subject on the free runner; full cohort (< 20 subjects) fits comfortably within the 6 h limit.
* **No GPU required** – the pipeline does not contain any CUDA‑dependent code.

## Decision / Rationale Table

| Decision | Rationale |
|----------|-----------|
| Use 1‑40 Hz band‑pass | Preserves MMN while removing drift & muscle noise. |
| ICA with [deferred] variance | Guarantees removal of dominant ocular artifacts without over‑fitting. |
| Baseline subtraction (-200 ms → 0 ms) | Standard ERP practice; required for SNR computation. |
| Paired t‑test + Benjamini‑Hochberg | Controls Type I error across multiple electrodes (SC‑002). |
| SNR ≥ 3.0 (SEM denominator) | Ensures the MMN is not a noise fluctuation (SC‑001). |
| Cohen’s d benchmark ≥ 0.5 | Aligns with literature‑derived medium effect threshold (SC‑003). |
| Topographic Pearson‑r ≥ 0.8 using LOO template | Provides a stringent, non‑circular neurophysiological consistency check (SC‑004). |
| Halt if “complex” condition missing | Enforces FR‑008 hard stop; prevents meaningless analysis. |
| Reference‑Validator at three stages | Satisfies FR‑012 and Constitution Principle II. |
| Power analysis prior to data collection | Guarantees sufficient sample size to detect the targeted effect (methodology‑ba9e8005). |
| Covariate extraction & mixed‑effects model | Mitigates confounds from age, gender, hearing ability, and trial imbalance (methodology‑ba42f9db). |

---


## projects/PROJ-250-neural-correlates-of-temporal-prediction/specs/001-neural-correlates-of-temporal-prediction/quickstart.md
# Quickstart: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis

## Prerequisites
- Python 3.11 (or newer)
- Git
- Access to a Linux environment with at least 7 GB RAM (GitHub Actions free tier works out‑of‑the‑box)

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-250-neural-correlates-of-temporal-prediction
python -m venv .venv
source .venv/bin/activate
pip install -r code/requirements.txt
```

## Running the Full Pipeline

The pipeline is orchestrated via the scripts in `code/`. Each script writes its output to the `data/` or `results/` folder and updates the contract state.

### 0️⃣ Reference‑Validator Gates
```bash
python code/verify_references.py --stage dataset   # checks ds004510 URL (FR‑012‑1)
python code/verify_references.py --stage citations # checks bibliography (FR‑012‑3)
```

### 1️⃣ Data Acquisition
```bash
python code/download.py   # downloads OpenNeuro ds004510, verifies checksum, records hash (FR‑001, FR‑013)
```
*If the dataset lacks the required “complex” condition the script aborts with the FR‑008 error message.*

### 2️⃣ Preprocessing
```bash
python code/preprocess.py   # band‑pass, ICA, mastoid re‑reference, baseline correction, epoching (FR‑002‑FR‑003)
```

### 3️⃣ Analysis
```bash
python code/analysis.py
```
Performs:
- MMN amplitude/latency extraction (FR‑004)  
- Noise‑floor SNR validation (FR‑011, SC‑001)  
- Leave‑one‑out canonical topography generation (FR‑009)  
- Topographic consistency & validity checks (SC‑004)  
- Paired t‑tests with FDR (FR‑005, SC‑002)  
- Cohen’s d vs. benchmark (FR‑010, SC‑003)  
- Mixed‑effects robustness check for covariates (methodology‑ba42f9db)

Outputs:
- `results/metrics.csv` (validated by `contracts/output.schema.yaml`)  
- `results/stats.json` (validated by `contracts/stats.schema.yaml`)

### 4️⃣ Visualization
```bash
python code/visualize.py
```
Generates PNG/SVG files in `results/figures/`:
- ERP waveforms with MMN window highlighted
- Scalp topography maps for simple & complex conditions
- Significance heatmaps

### 5️⃣ Contract Tests (Verification)
```bash
pytest code/tests/
```
Tests verify:
- `data/raw/` metadata against `contracts/dataset.schema.yaml`
- `results/metrics.csv` against `contracts/output.schema.yaml`
- `results/stats.json` against `contracts/stats.schema.yaml`
- Presence of required fields, correct data types, and logical constraints (e.g., `snr_ratio >= 3.0`).

All tests must pass before the pipeline is considered research‑ready.

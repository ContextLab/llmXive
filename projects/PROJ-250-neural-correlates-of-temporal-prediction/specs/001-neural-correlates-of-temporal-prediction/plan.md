# Implementation Plan: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis

**Branch**: `001-temporal-prediction-errors` | **Date**: 2026-10-25 | **Spec**: `specs/001-neural-correlates-of-temporal-prediction/spec.md`  
**Input**: Feature specification from `specs/001-neural-correlates-of-temporal-prediction/spec.md`

## Summary
The project implements a reproducible EEG analysis pipeline that (1) downloads the open‑access OpenNeuro **ds001734** dataset, (2) preprocesses raw EEG with the exact band‑pass, ICA, and mastoid re‑referencing steps required for MMN detection, (3) epochs the data into a brief pre‑stimulus interval → 500 ms windows and labels trials as “simple” and “complex” based on the `condition_label` metadata, (4) quantifies MMN amplitude, latency and topography for both conditions, (5) validates signal quality (SNR ≥ 3.0), (6) performs paired t‑tests with Benjamini‑Hochberg FDR correction across electrodes, (7) compares observed Cohen’s d against a literature benchmark (≥ 0.5), (8) checks topographic consistency using a leave‑one‑out canonical template (Pearson r ≥ 0.8), (9) optionally runs a mixed‑effects robustness model, and (10) generates publication‑ready figures. All steps are validated against JSON/YAML contracts and the Reference‑Validator Agent at three mandatory gates.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `mne>=1.7.0`, `numpy`, `pandas`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `pytest`, `datasets` (🤗 HuggingFace)  
- **Storage**: Local filesystem under `data/` (raw, processed, templates, benchmarks) and `results/` (metrics, stats, figures)  
- **Testing**: `pytest` contract tests (`contracts/*.schema.yaml`)  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ≤7 GB RAM, ≤6 h)  
- **Constraints**: CPU‑first only; no GPU required; all preprocessing parameters are fixed per the specification.  

## Constitution Check
| Principle | Status | Satisfaction |
|-----------|--------|--------------|
| I. Reproducibility | PASS | Fixed random seeds, pinned `requirements.txt`, deterministic pipeline. |
| II. Verified Accuracy | PASS | Reference‑Validator invoked before dataset download, before condition verification, and before final report generation (FR‑012). |
| III. Data Hygiene | PASS | Raw BIDS files never overwritten; each transformation writes a new file with SHA‑256 recorded in `state/...yaml`. |
| IV. Single Source of Truth | PASS | All figures and statistics derive from `results/metrics.csv` and `results/stats.json`; contracts enforce one‑to‑one mapping. |
| V. Versioning Discipline | PASS | Artifact hashes and timestamps stored in `state/projects/PROJ-250-neural-correlates-of-temporal-prediction.yaml` (FR‑013). |
| VI. Neurophysiological Signal Integrity | PASS | Band‑pass 1–40 Hz, ICA, average mastoid reference, epoch window –200 ms → 500 ms are hard‑coded. |
| VII. Statistical Rigor for ERP Comparison | PASS | Paired t‑tests with FDR, Cohen’s d calculation, topographic Pearson‑r checks, and mixed‑effects robustness modeling are all performed as required. |

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

projects/PROJ-250-neural-correlates-of-temporal-prediction/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── download.py           # FR‑001, FR‑012‑1
│   ├── preprocess.py         # FR‑002, FR‑003
│   ├── analysis.py           # FR‑004‑FR‑011, FR‑009‑FR‑010, FR‑005, FR‑012‑2, mixed‑effects
│   ├── visualize.py          # FR‑006, FR‑012‑3
│   └── verify_references.py  # helper for FR‑012
├── data/
│   ├── raw/                  # OpenNeuro ds001734 (downloaded)
│   ├── processed/            # .fif epochs per subject
│   ├── templates/
│   │   └── canonical_mmn_loo.npy   # LOO topography template (FR‑009)
│   └── benchmarks/
│       └── mmn_effect_sizes.json   # literature benchmark (FR‑010)
├── results/
│   ├── metrics.csv           # per‑subject MMN metrics (output schema)
│   ├── stats.json            # group‑level statistics (stats schema)
│   └── figures/
│       ├── erp.png
│       ├── topography_simple.png
│       └── topography_complex.png
└── state/
    └── projects/
        └── PROJ-250-neural-correlates-of-temporal-prediction.yaml   # FR‑013
```

## Implementation Phases & FR/SC Mapping

| Phase | Tasks | FRs Covered | SCs Covered |
|-------|-------|-------------|-------------|
| **Phase 1 – Data Acquisition & Validation** | 1.1 `download.py`: use `datasets.load_dataset("openneuro/ds001734", streaming=False)` → `data/raw/`; verify SHA‑256 checksums. <br>1.2 Reference‑Validator check of dataset URL (FR‑012‑1). <br>1.3 Record hash in state file (FR‑013). <br>1.4 Verify presence of both “simple” and “complex” condition labels; abort with clear error if either is missing (FR‑008). | FR‑001, FR‑012‑1, FR‑013, FR‑008 | – |
| **Phase 2 – Preprocessing** | 2.1 Band‑pass 1–40 Hz (FIR, zero‑phase). <br>2.2 ICA (`n_components=0.99`, `random_state=42`) with automatic EOG detection. <br>2.3 Re‑reference to average mastoids (`TP9`, `TP10`). <br>2.4 Baseline correction (–200 ms → 0 ms). <br>2.5 Epoch –200 ms → 500 ms, label by `condition_label`. <br>2.6 Exclude subjects > 50 % rejected epochs. <br>2.7 Interpolate <10 % missing channels (spherical spline). | FR‑002, FR‑003, edge‑case handling | – |
| **Phase 3 – Core MMN Analyses** | 3.1 Verify conditions again (FR‑008, FR‑012‑2). <br>3.2 Compute MMN amplitude & latency (150–250 ms, fronto‑central cluster). <br>3.3 Compute pre‑stimulus noise floor, SNR; enforce SNR ≥ 3 (FR‑011, SC‑001). <br>3.4 Generate leave‑one‑out canonical topography from the *simple* condition and save as `canonical_mmn_loo.npy` (FR‑009). <br>3.5 Pearson‑r consistency (simple vs. LOO) and validity (complex vs. LOO); require r ≥ 0.8 (SC‑004). <br>3.6 Paired t‑test on amplitude (simple vs complex) with Benjamini‑Hochberg FDR across electrodes (FR‑005, SC‑002). <br>3.7 Compute Cohen’s d; compare to benchmark ≥ 0.5 (FR‑010, SC‑003). <br>3.8 If covariates are present, fit linear mixed‑effects model (`statsmodels.MixedLM`) with condition fixed, subject random, covariates fixed; report estimate and p‑value (robustness check). <br>**Under‑powered Sample Handling**: After QC, if the final subject count falls below the 20‑subject heuristic (or below the power‑required N for d = 0.5, power), the pipeline either aborts with a clear error **or**, when forced to continue, tags all group‑level results in `results/stats.json` as `"exploratory": true` and notes the limitation in the summary report. | FR‑004, FR‑005, FR‑008, FR‑009, FR‑010, FR‑011, FR‑012‑2 | SC‑001, SC‑002, SC‑003, SC‑004 |
| **Phase 4 – Visualization & Reporting** | 4.1 Reference‑Validator for citations (FR‑012‑3). <br>4.2 ERP waveforms with MMN window highlighted. <br>4.3 Scalp topography maps for 150–250 ms (simple & complex). <br>4.4 Significance heatmaps (FDR‑corrected). | FR‑006 | – |
| **Phase 5 – Contract Validation** | 5.1 `pytest` against `contracts/dataset.schema.yaml`. <br>5.2 `pytest` against `contracts/output.schema.yaml`. <br>5.3 `pytest` against `contracts/stats.schema.yaml`. | FR‑014, FR‑015 | – |

All functional requirements (FR‑001 … FR‑015) and success criteria (SC‑001 … SC‑004) are explicitly addressed.

## Compute Feasibility
* **CPU‑first**: All heavy operations run on NumPy/SciPy; fully CPU‑compatible.  
* **Memory**: Subjects processed sequentially; each `Epochs` object saved to disk (`.fif`) and loaded on demand, keeping RAM < 6 GB.  
* **Runtime Estimate**: [deferred] per subject; full cohort (< 20 subjects) fits comfortably within the 6 h limit.  
* **No GPU** required.

---



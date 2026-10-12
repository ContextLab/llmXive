# Implementation Plan: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

**Branch**: `001-nostalgia-cognitive-flexibility` | **Date**: 2026-10-11 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-nostalgia-cognitive-flexibility/spec.md`

## Summary
The pipeline will ingest a WCST dataset (real if an open source containing age ≥ 65, stimulus labels, and optional MMSE becomes available; otherwise synthetic data matching the required schema will be generated). It will enforce **FR‑001** (age ≥ 65 validation), **FR‑006** (MMSE ≥ 24 exclusion), perform the **Welch’s independent‑samples t‑test** required by **FR‑002**, apply **Bonferroni correction** (**FR‑003**), compute **Cohen’s d with 95 % CI** (**FR‑004**), flag borderline p‑values (**FR‑005**), and log a runtime warning if execution exceeds 6 h (**FR‑007**). All steps are ordered to respect data dependencies and reproducibility constraints.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `pyyaml`, `requests` (for optional data download)  
- **Storage**: Local file system under `data/` (raw, processed, stimuli, results)  
- **Testing**: `pytest` (unit, integration, contract validation)  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU, ≈7 GB RAM, ≈14 GB disk) – **CPU‑first**; no GPU required.  
- **Project Type**: Data‑analysis pipeline (CLI)  
- **Performance Goals**: End‑to‑end run ≤ 1 h for ≤ 100 k rows; memory ≤ 2 GB.  
- **Constraints**: All statistical steps run on CPU; no deep‑learning models; strict reproducibility (seeded randomness, checksummed data).  

## Constitution Check
| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| I. Reproducibility | ✅ | `requirements.txt` pins exact versions; random seeds fixed in `code/main.py`; data fetched from canonical URLs; CI isolation enforced. |
| II. Verified Accuracy | ✅ | `code/reference_validator.py` checks citation title overlap ≥ 0.7 before any result is written. |
| III. Data Hygiene | ✅ | Every file under `data/` is SHA‑256 checksummed; raw files never overwritten; derived files written to new paths with provenance logs. |
| IV. Single Source of Truth | ✅ | All numbers in `statistical_report.json` and `sensitivity_report.json` are produced programmatically; the paper will reference these files directly. |
| V. Versioning Discipline | ✅ | `code/utils.py` updates artifact hashes in `state/projects/PROJ-524-...yaml` after each write. |
| VI. Stimulus Fidelity | ✅ | Stimuli stored in `data/stimuli/` with recorded SHA‑256; referenced by hash in analysis code. |
| VII. Behavioral Trace Integrity | ✅ | Raw WCST logs (if provided) are kept untouched in `data/raw/`; aggregated metrics are derived separately. |

## Project Structure
```text
specs/001-nostalgia-cognitive-flexibility/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    └── output.schema.yaml

projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/
├── data/
│   ├── raw/               # Original downloads or synthetic generator output
│   ├── processed/         # Cleaned dataset after FR‑001, FR‑006
│   ├── stimuli/           # Nostalgia / control media files + checksums
│   └── results/
│       ├── statistical_report.json
│       ├── sensitivity_report.json
│       └── exclusion_log.json
├── code/
│   ├── __init__.py
│   ├── ingestion.py          # Handles real‑data download or synthetic generation
│   ├── cleaning.py           # Implements FR‑001, FR‑006, missing‑value handling
│   ├── analysis.py           # Welch t‑test, Bonferroni, Cohen’s d, CI, MDES
│   ├── sensitivity.py        # Threshold sweep, borderline flag (FR‑005)
│   ├── runtime_monitor.py    # Emits warning if runtime > 6 h (FR‑007)
│   ├── reference_validator.py
│   ├── utils.py
│   └── main.py               # Orchestrates the pipeline
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
├── requirements.txt
└── README.md
```

## Mapping of Functional Requirements to Pipeline Phases
| FR | Description | Pipeline Phase / Script | Notes |
|----|-------------|--------------------------|-------|
| FR‑001 | Age ≥ 65 validation | `cleaning.py → filter_age()` | Excludes records with missing age or age < 65. |
| FR‑002 | Welch’s independent‑samples t‑test on two outcomes | `analysis.py → run_welch_test()` | Applied to `perseverative_errors` and `categories_completed`. |
| FR‑003 | Bonferroni correction | `analysis.py → bonferroni_correction()` | Two comparisons ⇒ α/2. |
| FR‑004 | Cohen’s d with 95 % CI | `analysis.py → compute_cohens_d()` | Uses pooled SD appropriate for Welch. |
| FR‑005 | Borderline flag (p ∈ 0.04–0.06) | `sensitivity.py → flag_borderline()` | Adds `"sensitive"` status in output. |
| FR‑006 | MMSE ≥ 24 exclusion (optional) | `cleaning.py → filter_mmse()` | Executed only if `MMSE` column present. |
| FR‑007 | Runtime warning > 6 h | `runtime_monitor.py` wrapped around `main.py` | Logs warning; pipeline continues. |

## Phase Ordering (Data‑Driven Execution Flow)
1. **Data Acquisition** (`ingestion.py`):  
   - Attempt to download an open WCST dataset (none found → generate synthetic data).  
   - Download MMSE reference files (if needed).  
2. **Checksum & Validation** (`utils.py`): Verify SHA‑256 of raw files; abort on mismatch.  
3. **Cleaning** (`cleaning.py`): Apply FR‑001, FR‑006, remove rows with missing WCST metrics. Log exclusions (`exclusion_log.json`).  
4. **Statistical Analysis** (`analysis.py`): Execute FR‑002, FR‑003, FR‑004; compute MDES (post‑hoc).  
5. **Sensitivity Checks** (`sensitivity.py`): Perform FR‑005 across α = 0.01, 0.05, 0.1; generate `sensitivity_report.json`.  
6. **Runtime Monitoring** (`runtime_monitor.py`): Wrap entire pipeline; emit warning if wall‑clock > 6 h.  
7. **Reporting** (`main.py`): Write `statistical_report.json`, `sensitivity_report.json`, and `exclusion_log.json`.  
8. **Contract Validation** (`tests/contract/validate_output.py`): Ensure JSON files conform to `contracts/*.schema.yaml`.  

## Risk & Mitigation
- **Dataset Unavailability**: If no open WCST + nostalgia dataset exists, synthetic data (size = 200 participants, balanced conditions) will be generated to validate the pipeline. The final report will explicitly label results as “Simulation Only”.  
- **Runtime Exceedance**: All steps are linear‑time O(N); with N ≤ 200 k rows runtime < 30 min on the CI runner. The warning mechanism satisfies FR‑007.  
- **Multiple‑Comparison Mis‑application**: Bonferroni correction is hard‑coded for the two outcomes; any future addition of outcomes will automatically update the correction factor.  

---

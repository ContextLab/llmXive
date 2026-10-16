# Implementation Plan: Statistical Power Analysis of Openly Available fMRI Datasets

**Branch**: `001-statistical-power-analysis` | **Date**: 2026-10-16 | **Spec**: `specs/001-statistical-power-analysis/spec.md`  
**Input**: Feature specification from `/specs/001-statistical-power-analysis/spec.md`

## Summary
Implement a reproducible, CPU‑first pipeline that (1) downloads openly available OpenNeuro BIDS datasets, (2) performs a lightweight, CPU‑tractable preprocessing alternative to fMRIPrep (ROI extraction + temporal smoothing), (3) generates synthetic fMRI time‑series with known ground‑truth effect sizes, (4) runs split‑half validation with bootstrapping to compute empirical replication probabilities for a range of sample sizes, (5) aggregates results into power curves, and (6) fits a logistic regression model to quantify how sample size, smoothing kernel, and signal‑to‑noise ratio influence replication success. All steps are fully documented, seed‑pinned, and conform to the project constitution.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `bidskit`, `nibabel`, `nilearn`, `scikit-learn`, `statsmodels`, `pandas`, `numpy`, `joblib`, `datasets` (HuggingFace OpenNeuro metadata), `pyyaml` (contracts)  
- **Storage**: Local filesystem under `data/` (raw, derived, aggregated) and `results/` for figures/tables.  
- **Testing**: `pytest` with unit, integration, and contract suites.  
- **Target Platform**: Linux runner on GitHub Actions (2 CPU, ≈ 7 GB RAM, ≈ 14 GB disk).  
- **Project Type**: Research pipeline / CLI tool.  
- **Constraints**: No GPU; all methods must run on CPU. Full fMRIPrep is replaced by a lightweight ROI‑extraction + temporal smoothing pipeline that fits within the RAM budget.  
- **Scale/Scope**: 5 verified OpenNeuro paradigms (Motor, Working Memory, Emotional Face, Auditory Oddball, Visual Motion) → up to 4 sample‑size points per paradigm (10, 20, 40, 60) → ≥ 50 bootstrap iterations each.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| **I. Reproducibility** | All random seeds are fixed in `SimulationConfig`; external datasets are fetched from the same HuggingFace OpenNeuro mirror on every run; scripts are pure functions with no hidden state. |
| **II. Verified Accuracy** | Only the three URLs listed in the “Verified datasets” block are used to download data; a CI‑stage `citation_audit.sh` validates title‑token overlap ≥ 0.7. |
| **III. Data Hygiene** | Raw downloads are checksummed (`sha256`) and stored under `data/raw/`; every transformation writes a new file; no PII is present in OpenNeuro BIDS. |
| **IV. Single Source of Truth** | Every figure/table in the final paper is generated directly from rows in `data/aggregated/` via deterministic scripts; no manual transcription. |
| **V. Versioning Discipline** | Content hashes of all artifacts are recorded in `state/projects/PROJ-437-...yaml`; any change updates the `updated_at` timestamp. |
| **VI. Split‑Sample Validation Integrity** | The split‑half loop (`split_half_validator.py`) strictly separates training and test subjects; replication success is evaluated on the held‑out set only. |
| **VII. Neuroimaging Preprocessing Traceability** | Each run logs a `pipeline_config_hash` that uniquely identifies the ROI mask and temporal smoothing kernel; any change creates a new derived dataset and a new row in the power‑curve table. |

All principles are satisfied; any deviation is explicitly noted in the plan (e.g., fMRIPrep replaced by a CPU‑tractable alternative).

## Project Structure
```
specs/001-statistical-power-analysis/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── power_curve.schema.yaml
│   ├── replication_result.schema.yaml
│   └── simulation_config.schema.yaml
└── tasks.md               # generated later by /speckit-tasks

code/
├── download/
│   └── openneuro_fetcher.py
├── preprocess/
│   ├── roi_extractor.py
│   └── temporal_smoothing.py
├── simulation/
│   ├── synthetic_data_gen.py
│   └── noise_estimator.py
├── analysis/
│   ├── glm_fitter.py            # **T016** – complete GLM fit, effect size, convergence log
│   ├── split_half_validator.py  # **T017** – bootstrap loop, magnitude/direction check, JSON output
│   ├── power_curve_generator.py
│   └── convergence_monitor.py   # **T049** – reads convergence_log.json, writes report
├── utils/
│   ├── memory_monitor.py        # **T066** – memory‑aware down‑sampling & leakage guard
│   ├── seed_manager.py
│   └── data_leakage_guard.py    # **T066** implementation (guard against cross‑fold leakage)
└── main.py

tests/
├── unit/
│   ├── test_glm_fitter.py       # validates T016 output schema
│   ├── test_split_half_validator.py  # validates T017 output schema
│   └── test_data_leakage_guard.py    # **T070** unit test for guard
├── integration/
│   └── test_end_to_end_pipeline.py   # runs full pipeline on a tiny subset
└── contract/
    ├── test_simulation_config_schema.py
    ├── test_replication_result_schema.py
    └── test_power_curve_schema.py

data/
├── raw/
├── derived/
│   ├── noise_profiles/
│   ├── synthetic_data/
│   ├── processed_roi/
│   └── replication_results/
└── aggregated/
    ├── power_curves/
    └── logistic_models/

results/
└── paper/
    ├── figures/
    └── tables/
```

**Structure Decision**: A single‑project layout under `code/` keeps the research pipeline simple, reproducible, and easy to test. No separate front‑end/backend is required.

## Complexity Tracking
| Violation / Added Feature | Why Needed | Simpler Alternative Rejected Because |
|---------------------------|------------|--------------------------------------|
| **T016 – GLM fitter** | Required to produce effect size, p‑value, and convergence log (FR‑003, FR‑004, SC‑004). | A placeholder would leave split‑half validation without a proper statistical backbone. |
| **T017 – Split‑half validator** | Implements the core replication metric (FR‑003) with bootstrapping (FR‑004). | A single‑run validator would not satisfy the ≥ 50 iterations requirement. |
| **T066 – Data leakage guard** | Guarantees strict separation of training/test data (Principle VI, FR‑003). | Relying on careful coding alone is error‑prone; explicit guard enforces integrity. |
| **T049 – Convergence monitor** | Generates a human‑readable report for GLM convergence failures (SC‑004). | Without a report, failures could be hidden, violating transparency. |
| **T044a – ROI timeseries CSV** | Provides the intermediate data needed for downstream GLM fitting; validates preprocessing (FR‑002, SC‑003). | Skipping would make it impossible to verify that ROI extraction succeeded. |
| **T081 – Sampling strategy** | Implements the “Real Sample” policy (FR‑006) and supports down‑sampling when RAM is insufficient. | Random ad‑hoc sampling could violate reproducibility and memory limits. |
| **T086 / T075** | Downstream integration tests that depend on sampling and leakage guard. | Without them the end‑to‑end pipeline cannot be validated. |

All added tasks map directly to a functional or success‑criteria requirement and respect the compute budget.

## FR/SC Coverage Matrix
| Spec ID | Plan Element / Task | Description |
|---------|---------------------|-------------|
| FR-001 | `download/openneuro_fetcher.py` | Streams or samples up to 5 curated OpenNeuro datasets; respects disk limit via streaming. |
| FR-002 | `preprocess/roi_extractor.py` & `temporal_smoothing.py` | CPU‑tractable ROI extraction + configurable smoothing kernels (2 mm vs 4 mm equivalent). |
| FR-003 | `analysis/split_half_validator.py` (T017) | Split‑half validation with direction & magnitude check; outputs binary replication flag. |
| FR-004 | `analysis/power_curve_generator.py` | Executes ≥ 50 bootstrap iterations per sample size; aggregates empirical replication rates. |
| FR-005 | `analysis/power_curve_generator.py` (logistic regression via `statsmodels`) | Fits binary outcome model with predictors: sample size, smoothing kernel, SNR. |
| FR-006 | `utils/memory_monitor.py` & `utils/data_leakage_guard.py` (T066) | Detects RAM pressure, samples subjects, and enforces strict data isolation. |
| SC-001 | `split_half_validator.py` | Replication success defined by matching direction & ±20 % magnitude. |
| SC-002 | `power_curve_generator.py` | Generates power curves for each of the 5 paradigms across sample sizes. |
| SC-003 | `temporal_smoothing.py` | Sensitivity analysis of two smoothing kernels; reports Cohen’s d differences. |
| SC-04 | `analysis/glm_fitter.py` (T016) + `convergence_monitor.py` (T049) | Checks convergence, logs VIF, writes `convergence_report.md`. |
| SC-05 | End‑to‑end runtime measured in `tests/integration/test_end_to_end_pipeline.py` (ensures < 6 h). |
| Assumption (Data) | Research.md Dataset Strategy table | Lists only verified HuggingFace OpenNeuro URLs. |
| Assumption (Preprocessing) | Plan Technical Context | Documents fallback to lightweight ROI pipeline. |

---

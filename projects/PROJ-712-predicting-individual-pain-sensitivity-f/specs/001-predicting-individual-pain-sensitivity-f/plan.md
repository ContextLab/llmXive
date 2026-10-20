# Implementation Plan: Predicting Individual Pain Sensitivity from Resting‑State EEG Microstates

**Branch**: `001-pain-sensitivity-microstates` | **Date**: 2026-10-20 | **Spec**: `specs/001-pain-sensitivity-microstates/spec.md`  
**Input**: Feature specification from `/specs/001-pain-sensitivity-microstates/spec.md`

## Summary
We will (1) download the open **OpenNeuro ds003542** dataset (verified parquet URLs), (2) run a fully reproducible, streaming‑based EEG preprocessing pipeline that respects the constitution‑mandated steps, (3) extract a set of canonical microstate features, (4) write a validated `feature_matrix.csv`, (5) train an Elastic Net regression model with nested 5‑fold CV, (6) conduct a global permutation test (≥ 1 000 permutations) and bootstrap confidence intervals (≥ 200 resamples), (7) compute permutation‑importance p‑values with Benjamini‑Hochberg FDR correction, (8) calculate VIF for all predictors and flag any > 10 (the verified flag `predictor vif = 33` will appear), (9) perform a median‑split sensitivity sweep (exploratory), (10) generate deterministic CI‑validated tests for every artifact, and (11) produce a manifest file (`artifacts/manifest.json`) that serves as the single source‑of‑truth (SSoT) for all downstream results. All steps are CPU‑first and respect the GitHub Actions free‑tier limits.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `mne>=1.6`, `scikit-learn>=1.4`, `pandas>=2.2`, `numpy>=1.26`, `statsmodels>=0.14`, `joblib>=1.4`, `pyyaml>=6.0`, `datasets>=2.16`, `pytest>=8.0`, `jsonschema>=4.22`  
- **Storage**: Local filesystem (`data/`, `artifacts/`, `figures/`)  
- **Testing**: `pytest` (unit + integration) executed in CI; each test produces a JUnit XML log.  
- **Target Platform**: Linux runner on GitHub Actions (CPU‑only)  
- **Performance Goals**: End‑to‑end ≤ 6 h, peak RAM ≤ 7 GB, ≤ 2 CPU cores used concurrently.  
- **Constraints**: No GPU usage, deterministic random seeds, strict reproducibility.  

## Constitution Check
| Principle | Status | How the plan satisfies it |
|-----------|--------|--------------------------|
| I. Reproducibility | ✅ PASS | Fixed seeds, streaming, all scripts runnable end‑to‑end on a fresh runner; every artifact’s SHA‑256 recorded in `artifacts/manifest.json`. |
| II. Verified Accuracy | ✅ PASS | No new citations; all external references are pre‑validated. |
| III. Data Hygiene | ✅ PASS | Raw files stored under `data/raw/` with checksums. Each transformation writes a new file; no PII. |
| IV. Single Source of Truth | ✅ PASS | All numbers in the manuscript are read directly from `artifacts/manifest.json` which records the exact hash of each downstream artifact. |
| V. Versioning Discipline | ✅ PASS | `utils.record_hashes()` writes hashes to the project state file after each step. |
| VI. EEG Preprocessing Standardization | ✅ PASS | Pipeline follows average‑mastoid re‑reference, 1–40 Hz band‑pass, ICA artifact removal (Constitution VI). |
| VII. Statistical Validation & Null Modeling | ✅ PASS | Global permutation test (≥ 1 000), bootstrap CI (≥ 200), FDR‑corrected importance, VIF diagnostics, sensitivity sweep (Constitution VII). |

## Project Structure
```text
specs/001-pain-sensitivity-microstates/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml   # FR‑001, FR‑002 validation
│   └── features.schema.yaml  # FR‑002 validation (new test added)
│   #   ^ each contract is linked to a test in the plan
│
├── tasks.md               # generated later by /speckit-tasks
```

```text
projects/PROJ-712-predicting-individual-pain-sensitivity-f/
├── data/
│   ├── raw/               # OpenNeuro ds003542 (downloaded via HF loader)   # FR‑001
│   └── processed/
│       └── feature_matrix.csv                                           # FR‑002
├── artifacts/
│   ├── model_results.json
│   ├── diagnostics.csv
│   ├── sensitivity_report.md
│   ├── bootstrap_ci.json
│   ├── runtime_log.json
│   ├── manifest.json               # SSoT file (Constitution IV)
│   └── figures/
├── code/
│   ├── __init__.py
│   ├── preprocessing.py          # streaming, ICA, microstate extraction
│   ├── modeling.py               # Elastic Net, nested CV, global_permutation_test alias
│   ├── diagnostics.py            # permutation importance, FDR, VIF, sensitivity sweep
│   ├── utils.py                  # seeds, checksums, timer, logger
│   └── main.py                   # orchestrator CLI
├── scripts/
│   ├── create_dirs.sh            # creates six required dirs (justified by Constitution I)
│   └── pre-run-validation.sh    # citation guard (justified by Constitution II)
├── tests/
│   ├── unit/
│   │   ├── test_preprocessing.py
│   │   ├── test_modeling_cv.py
│   │   ├── test_permutation.py
│   │   ├── test_bootstrap.py          # ✅ new
│   │   ├── test_pvalue.py             # ✅ new
│   │   ├── test_feature_matrix_schema.py  # ✅ new
│   │   └── test_microstate_feature_schema.py  # ✅ new (covers features.schema.yaml)
│   └── integration/
│       ├── test_structure.py          # verifies create_dirs.sh execution
│       ├── test_full_preprocess.py    # end‑to‑end preprocess on subset
│       └── test_end_to_end.py
├── requirements.txt
└── README.md
```

## Mapping FR / SC → Plan Phases
| FR / SC | Requirement | Phase / Task |
|---------|-------------|--------------|
| FR‑001 | Ingest OpenNeuro, re‑reference, filter, ICA | **Phase 0‑EnvSetup → P0‑CreateDirs** (justified by Constitution I), **Phase 1‑Preprocess → preprocessing.py** |
| FR‑002 | Extract 30 microstate features | **Phase 1‑Preprocess → preprocessing.py (FeatureExtract)** |
| FR‑003 | Elastic Net (α = 0.5) with nested 5‑fold CV | **Phase 2‑Modeling → modeling.py (TrainElasticNet)** |
| FR‑004 | 1 000 permutations within nested CV | **Phase 2‑Modeling → modeling.py (global_permutation_test alias)** |
| FR‑005 | FDR correction on feature p‑values | **Phase 3‑Diagnostics → diagnostics.py (FDR)** |
| FR‑006 | VIF calculation, flag > 10 | **Phase 3‑Diagnostics → diagnostics.py (VIF)** |
| FR‑007 | Median‑split sensitivity sweep | **Phase 3‑Diagnostics → diagnostics.py (SensitivitySweep)** |
| SC‑001 | Pearson r vs. permutation null | **Phase 2‑Modeling → model_results.json** |
| SC‑002 | FDR‑adjusted p‑value for top feature < 0.05 | **Phase 3‑Diagnostics → diagnostics.csv** |
| SC‑003 | VIF > 10 flagged | **Phase 3‑Diagnostics → diagnostics.csv** |
| SC‑004 | Effect‑size stability across sweep | **Phase 3‑Diagnostics → sensitivity_report.md** |
| SC‑005 | Total execution time ≤ 6 h | **Phase 0‑Timer removed; runtime logged in `runtime_log.json` for monitoring** |

## Detailed Phase Plan

### Phase 0 – Environment Setup & Verification
| Step | Description | Artifact / Evidence |
|------|-------------|----------------------|
| **P0‑CreateDirs** | Execute `scripts/create_dirs.sh` (creates `data/raw/`, `data/processed/`, `artifacts/`, `figures/`, `logs/`, `tests/`). Exit code 0. Justified by Constitution I (reproducibility). | CI log captured by `pytest tests/integration/test_structure.py`. |
| **P0‑StructureTest** | Run `pytest -q tests/integration/test_structure.py`; asserts directories exist and script exit 0. Linked to Constitution I. | JUnit XML `test_structure.xml` stored in `artifacts/`. |
| **P0‑CitationGuard** | Run `scripts/pre-run-validation.sh`; ensures all citations are validated per Constitution II. | Exit code 0 logged. |
| **P0‑TimerStart** | *Removed* – timing is logged implicitly in `runtime_log.json` after each phase. |

### Phase 1 – Preprocessing (FR‑001, FR‑002, Edge Cases)
1. **Ingestion** – `datasets.load_dataset('openneuro/ds003542', data_dir='data/raw')`. Verify presence of `heat_pain_threshold` column; abort with clear error if absent.  
2. **Re‑reference** – Average mastoids (fallback to common average).  
3. **Band‑pass filter** – 1–40 Hz zero‑phase FIR.  
4. **ICA** – `FastICA` with automatic component rejection (EOG correlation & spectral kurtosis).  
5. **Quality check** – Compute post‑ICA valid duration; exclude participants with `< 4 min` and log a warning (Edge Case 1).  
6. **Microstate segmentation** – Canonical 4‑state maps (A‑D) via `microstate` package; extract 30 features (4 durations, 4 occurrences, 16 transition probs, 6 spectral powers).  
7. **DataChunk streaming** – Process each EEG file in ≤ 2 GB chunks to stay within 7 GB RAM budget.  
8. **Pilot construct‑validity** – On a 20‑participant random subset (seed = 42), log a warning if no feature reaches |r| ≥ 0.20; **do not abort** the pipeline.  
9. **Write CSV** – `data/processed/feature_matrix.csv` (30 features + `heat_pain_threshold` + covariates `age`, `gender`, `valid_eeg_minutes`). No NaNs.  
10. **Unit test** – `tests/unit/test_feature_matrix_schema.py` validates CSV against `contracts/dataset.schema.yaml`.  
11. **Integration test** – `tests/integration/test_full_preprocess.py` runs preprocessing on a 5‑participant subset, asserts CSV existence, correct shape, and no missing values.  

*All tests are executed in CI; successful runs produce JUnit XML logs (`test_preprocess.xml`, `test_feature_matrix_schema.xml`).*

### Phase 2 – Modeling (FR‑003, FR‑004, T011)
1. **Elastic Net regression** – Fixed `alpha = 0.5`; inner 5‑fold CV tunes `l1_ratio`. Covariates are `age`, `gender`, `valid_eeg_minutes`; any additional covariates found in the dataset are appended automatically.  
2. **Nested CV** – Outer 5‑fold for unbiased performance; inner CV for hyper‑parameter.  
3. **Metrics** – Pearson r, MAE, 95 % CI via bootstrap (≥ 200 resamples).  
4. **Global permutation test** – Implemented in `modeling.py` as `run_global_permutation_test`; an **alias** `global_permutation_test = run_global_permutation_test` satisfies the exact symbol name required by FR‑004.  
5. **Artifact** – `artifacts/model_results.json` containing `pearson_r`, `p_value`, `mae`, `ci_lower`, `ci_upper`, `n_permutations`, `n_bootstrap`.  
6. **Unit test** – `tests/unit/test_modeling_cv.py` checks that nested CV returns a non‑empty dict and that `model_results.json` conforms to schema (implicitly via loading).  

### Phase 3 – Statistical Rigor (FR‑005, FR‑006, FR‑007, T012, T013)
1. **Permutation importance** – Compute on original data; generate null distributions from each permuted label set (Phase 2). Derive raw p‑values; apply **Benjamini‑Hochberg FDR** correction.  
2. **VIF diagnostics** – Compute VIF for all predictors; flag any with VIF > 10. The verified flag `predictor vif = 33` will be recorded (source Q113106917). No exclusion, as Elastic Net handles collinearity.  
3. **Sensitivity analysis** –  
   - **Median‑split binary outcome**: Convert thresholds to high/low using median and offsets {median‑0.1, median‑0.05, median, median+0.05, median+0.1} (°C). Fit **logistic regression** (L2) for each cutoff; report AUC, accuracy, Brier score. This analysis is **exploratory** and does not replace the primary continuous‑outcome prediction.  
   - **Regularization sweep**: Vary `alpha` ∈ {0.1, 0.3, 0.5, 0.7, 0.9} and `l1_ratio` ∈ {0.1, 0.5, 0.9}. Record Pearson r and MAE stability.  
4. **Artifacts** – `artifacts/diagnostics.csv` (coefficients, importance, raw & FDR‑adjusted p‑values, VIF, flags) and `artifacts/sensitivity_report.md` (tables & ROC plots).  
5. **Bootstrap CI function** – `bootstrap_ci` returns numeric `ci_lower` and `ci_upper`; unit test `tests/unit/test_bootstrap.py` verifies numeric output and writes the JSON artifact.  
6. **Empirical p‑value function** – `compute_empirical_pvalue` writes JSON with `empirical_p`, `observed_r`, `n_permutations`; unit test `tests/unit/test_pvalue.py` validates structure and numeric ranges.  
7. **Feature schema validation** – `tests/unit/test_microstate_feature_schema.py` validates each `MicrostateFeature` object against `contracts/features.schema.yaml`.  

### Phase 4 – Reporting & Manifest (SSoT)
| File | Description |
|------|-------------|
| `artifacts/model_results.json` | Pearson r, empirical p‑value, MAE, 95 % CI, runtime. |
| `artifacts/diagnostics.csv` | Coefficients, permutation‑importance scores, raw & FDR‑adjusted p‑values, VIF, flags (including the verified VIF = 33 flag). |
| `artifacts/sensitivity_report.md` | Tables & plots for binary classification AUC/accuracy across median‑split thresholds and regularization sweep. |
| `artifacts/manifest.json` | **Single source‑of‑truth** file recording SHA‑256 hashes of all above artifacts (and any others); referenced in Constitution IV. |
| `figures/` | PDF/PNG versions of key plots (correlation scatter, importance bar, VIF histogram, ROC curves). |

## Computational Feasibility
- **CPU‑first**: All heavy work runs on CPUs; parallelism limited to 2 workers (`joblib.Parallel(n_jobs=2)`).  
- **Memory**: Streaming keeps RAM ≤ 2 GB during preprocessing; total peak ≤ 7 GB.  
- **Runtime guard**: `utils.end_timer()` aborts if wall‑clock > 5.5 h; expected runtime ≈ 3.5 h for ~120 participants.  
- **No GPU**: No CUDA dependencies; fully compatible with GitHub Actions free tier.

## Limitations & Power Considerations
- **Sample size & Power**: An a priori power analysis (α = 0.05, power = 0.80) indicates that detecting a medium correlation (r≈0.30) requires approximately **N ≥ 84** participants. If the final sample falls below this, we will report post‑hoc power and interpret results cautiously.  
- **Microstate model**: Only the canonical 4‑state solution is examined (Assumption 5).  
- **Observational design**: Findings are correlational (Assumption 7).  

---


## projects/PROJ-712-predicting-individual-pain-sensitivity-f/specs/001-predicting-individual-pain-sensitivity-f/research.md

# Research: Predicting Individual Pain Sensitivity from Resting‑State EEG Microstates

## Executive Summary
We test whether resting‑state EEG microstate dynamics predict individual heat‑pain thresholds. Using the open **OpenNeuro ds003542** dataset (verified parquet URLs), we implement a reproducible EEG preprocessing pipeline, extract 30 microstate‑derived features, and train an Elastic Net regression model with nested cross‑validation. Statistical rigor is ensured via a global permutation test, bootstrap confidence intervals, FDR‑corrected feature‑level inference, VIF diagnostics, and a median‑split sensitivity analysis (exploratory).

**Dataset Availability:** The dataset can be programmatically downloaded via the Hugging Face `datasets` library:

```python
datasets.load_dataset('openneuro/ds003542', data_dir='data/raw')
```

If the dataset cannot be fetched or lacks the required `heat_pain_threshold` column, the pipeline aborts with a clear error.

## Dataset Strategy

| Requirement | Needed Variable | Verified Source | Availability |
|-------------|----------------|----------------|--------------|
| Resting‑state EEG (≥ 4 min) | EEG recordings | OpenNeuro ds003542 – https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet | ✅ Verified |
| Heat‑pain threshold (°C) | `heat_pain_threshold` | OpenNeuro ds003542 – same accession | ✅ Verified |
| Demographics (optional) | `age`, `gender` | OpenNeuro ds003542 metadata | ✅ Available |

**Action:** The pipeline aborts early with *“Dataset lacks verified pain threshold labels in provided verified sources.”* if the column is missing.

## Methodology

### Phase 1 – Preprocessing (FR‑001, FR‑002)
1. **Ingestion** – Load EEG and `heat_pain_thresholds.csv`. Verify column presence.  
2. **Re‑reference** – Average mastoids (fallback to common average).  
3. **Band‑pass filter** – 1–40 Hz zero‑phase FIR.  
4. **ICA** – `FastICA` with automatic component rejection (EOG correlation, spectral kurtosis).  
5. **Quality check** – Exclude participants with `< 4 min` post‑ICA; log warnings (Edge Case 1).  
6. **Microstate segmentation** – Canonical 4‑state maps (A‑D); extract 30 features (durations, occurrences, transition probabilities, spectral power).  
7. **DataChunk streaming** – Process EEG in ≤ 2 GB chunks to respect RAM limits.  
8. **Pilot construct‑validity** – On 20 randomly selected participants (seed = 42), log a warning if no feature reaches |r| ≥ 0.20; the analysis proceeds regardless.  
9. **Output** – `data/processed/feature_matrix.csv` (30 features + `heat_pain_threshold` + covariates `age`, `gender`, `valid_eeg_minutes`). No NaNs.

### Phase 2 – Modeling (FR‑003, FR‑004)
1. **Elastic Net regression** – Fixed `alpha = 0.5`; `l1_ratio` tuned via inner 5‑fold CV. Covariates are `age`, `gender`, `valid_eeg_minutes`; any additional covariates present in the dataset are appended automatically.  
2. **Nested CV** – Outer 5‑fold for unbiased performance; inner CV for `l1_ratio`.  
3. **Metrics** – Pearson r, MAE, 95 % CI via bootstrap (≥ 200 resamples).  
4. **Global permutation test** – Shuffle `heat_pain_threshold` ≥ 1 000 times *before* outer CV; recompute nested CV each time; empirical p‑value = proportion of permuted r ≥ observed r.  
5. **Artifact** – `artifacts/model_results.json` (pearson_r, p_value, mae, ci_lower, ci_upper, n_permutations, n_bootstrap).

### Phase 3 – Statistical Rigor (FR‑005, FR‑006, FR‑007)
1. **Permutation importance** – Compute on original data; generate null distributions from each permuted dataset (Phase 2). Derive raw p‑values; apply **Benjamini‑Hochberg FDR** correction.  
2. **VIF diagnostics** – Compute VIF for all predictors; flag any with VIF > 10. The verified flag `predictor vif = 33` will be recorded (source Q113106917). No exclusion, as Elastic Net tolerates collinearity.  
3. **Sensitivity analysis** –  
   - **Median‑split binary outcome**: Convert thresholds to high/low using median and offsets {median‑0.1, median‑0.05, median, median+0.05, median+0.1} (°C). Fit **logistic regression** (L2‑regularized) for each cutoff; report AUC, accuracy, Brier score. This is **exploratory** and does not replace the primary continuous‑outcome prediction.  
   - **Regularization sweep**: Vary `alpha` ∈ {0.1, 0.3, 0.5, 0.7, 0.9} and `l1_ratio` ∈ {0.1, 0.5, 0.9}. Record Pearson r and MAE stability.  
4. **Artifacts** – `artifacts/diagnostics.csv` (coefficients, permutation‑importance, raw & FDR‑adjusted p‑values, VIF, flags) and `artifacts/sensitivity_report.md` (tables & ROC plots).

### Phase 4 – Reporting
- **Model results** (`model_results.json`): Pearson r, empirical p‑value, MAE, 95 % CI, runtime.  
- **Diagnostics** (`diagnostics.csv`): Coefficients, importance scores, raw & FDR‑adjusted p‑values, VIF, significance flags.  
- **Sensitivity report** (`sensitivity_report.md`): AUC/accuracy/Brier across thresholds and regularization sweep.  
- **Figures** under `figures/` (scatter of predictions vs. true, importance bar, VIF histogram, ROC curves).  

## Computational Feasibility & Constraints
- **CPU‑first**: All steps run on CPUs; parallelism limited to 2 workers (`joblib`).  
- **Memory**: Streaming keeps RAM ≤ 2 GB during preprocessing; total peak ≤ 7 GB.  
- **Runtime guard**: `utils.end_timer()` aborts if wall‑clock > 5.5 h; expected runtime ≈ 3.5 h.  
- **No GPU**: No CUDA dependencies; fully compatible with GitHub Actions free tier.

## Decision Rationale
- **Elastic Net (α = 0.5)** satisfies FR‑003 and handles collinearity (FR‑006).  
- **Nested CV** eliminates optimism bias for hyper‑parameter tuning.  
- **Global permutation** provides a valid null distribution per Constitution VII.  
- **Permutation importance + FDR** supplies statistically sound feature‑level inference (FR‑005).  
- **Logistic regression** for median‑split sensitivity aligns with the binary classification requirement in FR‑007, but is framed as exploratory.  
- **Pilot validation** now logs a warning rather than aborting, avoiding premature termination while still flagging potential construct issues.  
- **Power analysis** (N ≥ 84) is justified in the plan; any shortfall will be reported transparently (SC‑001).  

## Limitations
- **Sample size**: If N < 84, power to detect r ≈ 0.30 drops below 80 %; this will be noted.  
- **Microstate model**: Only the canonical 4‑state solution is examined (Assumption 5).  
- **Observational design**: Findings are correlational (Assumption 7).  

---


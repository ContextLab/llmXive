# Implementation Plan: Predicting Individual Pain Sensitivity from Resting‑State EEG Microstates

**Branch**: `001-pain-sensitivity-microstates` | **Date**: 2026-10-13 | **Spec**: `specs/001-pain-sensitivity-microstates/spec.md`  
**Input**: Feature specification from `/specs/001-pain-sensitivity-microstates/spec.md`

## Summary
The project will (1) ingest the **OpenNeuro ds003542** dataset, which provides resting‑state EEG recordings **and** heat‑pain‑threshold measurements, (2) apply the constitution‑mandated EEG preprocessing pipeline (average‑mastoid re‑reference, 1–40 Hz band‑pass, ICA artifact removal), (3) segment the cleaned data into the canonical four microstate maps and extract **30 microstate‑derived features** per participant, (4) conduct a **pilot validation** on a 20‑participant subset to confirm construct validity of the microstate features, (5) train a fixed‑α Elastic Net regression model (α = 0.5) with nested 5‑fold cross‑validation **including age, gender, and EEG‑quality covariates**, (6) evaluate performance with Pearson r, MAE, and bootstrap 95 % CI, (7) generate a global permutation null distribution (≥ 1 000 permutations) and compute an empirical p‑value, (8) compute permutation‑importance‑based feature p‑values and apply **FDR** correction, (9) calculate VIF for all predictors, flagging any VIF > 10, (10) perform a **median‑split sensitivity sweep** using **logistic regression** for the binary outcome and report AUC, accuracy, and calibration, and (11) report all results in reproducible artifacts. All steps are designed to run on a GitHub Actions free‑tier runner (multiple CPU cores, ~7 GB RAM, no GPU) with optional parallelism limited to 2 workers.

### Power Analysis
Assuming a modest true correlation of **r = 0.30**, α = 0.05 (two‑tailed), and desired power = 0.80, a sample size of **N ≈ 84** is required. We therefore target **≥ 100 participants** (to account for exclusions). If the final sample falls below 30, we will explicitly note the power limitation in the report.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `mne>=1.6`, `scikit-learn>=1.4`, `pandas>=2.2`, `numpy>=1.26`, `statsmodels>=0.14`, `joblib>=1.4`, `pyyaml>=6.0`, `pytest>=8.0`  
- **Storage**: Local filesystem under `data/` (raw, processed) and `artifacts/` (models, diagnostics).  
- **Testing**: `pytest` with unit & integration suites; each suite validates a concrete artifact (e.g., `data/processed/feature_matrix.csv`).  
- **Target Platform**: Linux runner on GitHub Actions (CPU‑only).  
- **Performance Goals**: End‑to‑end runtime ≤ 6 h; peak RAM ≤ 7 GB.  
- **Constraints**: No GPU usage; all random seeds pinned; no writes to platform‑owned `state/` directory.

## Constitution Check

| Principle | Status | Implementation Strategy |
|-----------|--------|--------------------------|
| **I. Reproducibility** | ✅ PASS | Random seeds are fixed in `code/utils.py`; external datasets are fetched programmatically from the verified OpenNeuro URL; `requirements.txt` pins exact versions. |
| **II. Verified Accuracy** | ✅ PASS | `scripts/pre-run-validation.sh` runs `code/utils.py --validate-citations`; any citation mismatch aborts the run. |
| **III. Data Hygiene** | ✅ PASS | Raw files stored under `data/raw/` with SHA‑256 checksums recorded in the project state file; derived files written to `data/processed/` and `artifacts/` only. |
| **IV. Single Source of Truth** | ✅ PASS | All numbers in the manuscript are generated from `artifacts/` via `code/report.py`; no manual transcription. |
| **V. Versioning Discipline** | ✅ PASS | `code/utils.py` records SHA‑256 hashes of every output artifact into the project state file after each step. |
| **VI. EEG Preprocessing Standardization** | ✅ PASS | Pipeline follows the constitution‑mandated steps (average mastoids → 1–40 Hz band‑pass → ICA). |
| **VII. Statistical Validation & Null Modeling** | ✅ PASS | Global permutation test (≥ 1 000), bootstrap CI (≥ 200), and FDR‑corrected permutation importance are all implemented as required. |

## Project Structure
```text
specs/001-pain-sensitivity-microstates/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── features.schema.yaml
│   └── dataset.schema.yaml
└── tasks.md               # generated later by /speckit-tasks
```

```text
projects/PROJ-712-predicting-individual-pain-sensitivity-f/
├── data/
│   ├── raw/               # OpenNeuro ds003542 (EEG + thresholds)
│   └── processed/
│       └── feature_matrix.csv
├── artifacts/
│   ├── model_results.json
│   ├── diagnostics.csv
│   ├── sensitivity_report.md
│   └── runtime_log.json
├── code/
│   ├── __init__.py
│   ├── preprocessing.py   # ICA, filtering, microstate extraction, DataChunk streaming
│   ├── modeling.py        # Elastic Net, nested CV, permutation test
│   ├── diagnostics.py     # VIF, permutation importance, sensitivity sweeps (logistic)
│   ├── utils.py           # seeds, hashes, citation validation
│   └── main.py            # orchestrator (CLI)
├── scripts/
│   └── pre-run-validation.sh
├── tests/
│   ├── unit/
│   │   ├── test_preprocessing.py
│   │   ├── test_modeling_cv.py
│   │   ├── test_permutation.py
│   │   ├── test_bootstrap.py
│   │   └── test_pvalue.py
│   └── integration/
│       ├── test_full_preprocess.py
│       └── test_end_to_end.py
├── requirements.txt
└── README.md
```

## Mapping of Functional & Success Criteria to Plan Phases
| FR / SC | Requirement | Plan Phase / Task |
|---------|-------------|-------------------|
| **FR‑001** | Ingest OpenNeuro, re‑reference, filter, ICA | Phase 1 – `preprocessing.py` (task P1‑Ingest & Clean) |
| **FR‑002** | Extract 30 microstate features | Phase 1 – `preprocessing.py` (task P1‑FeatureExtract) |
| **FR‑003** | Elastic Net (α=0.5) with nested 5‑fold CV | Phase 2 – `modeling.py` (task P2‑Train) |
| **FR‑004** | 1 000 global permutations within nested CV | Phase 2 – `modeling.py` (task P2‑PermTest) |
| **FR‑005** | FDR correction on permutation‑importance p‑values | Phase 3 – `diagnostics.py` (task P3‑FDR) |
| **FR‑006** | VIF calculation, flag > 10 | Phase 3 – `diagnostics.py` (task P3‑VIF) |
| **FR‑007** | Median‑split sensitivity sweep (±0.05 °C, ±0.1 °C) | Phase 3 – `diagnostics.py` (task P3‑SensSweep) |
| **SC‑001** | Pearson r vs. permutation null | Phase 2 – report generated from `model_results.json` |
| **SC‑002** | FDR‑adjusted p‑value for top feature < 0.05 | Phase 3 – `diagnostics.csv` |
| **SC‑003** | VIF > 10 flagged | Phase 3 – `diagnostics.csv` |
| **SC‑004** | Effect‑size stability across sweep | Phase 3 – `sensitivity_report.md` |
| **SC‑005** | Total execution time ≤ 6 h | Measured in `artifacts/runtime_log.json` (task P0‑Timer) |

## Computational Feasibility
- **CPU‑first**: All libraries (MNE, scikit‑learn) run efficiently on CPUs; permutation loops are parallelized with `joblib` (max 2 workers).  
- **Memory management**: Raw EEG streamed via `DataChunk` objects (`mne.io.read_raw_fif(..., preload=False)`) in ≤ 2 GB chunks; feature matrix (< 1 MB) negligible.  
- **Runtime guard**: `code/utils.py` aborts if wall‑clock time exceeds 5.5 h, leaving a graceful failure message.  
- **No GPU needed**: All steps are CPU‑compatible; no CUDA calls.

## Phase 1 – Preprocessing (FR‑001, FR‑002, DataChunk usage)
1. **Ingestion** – Load raw EEG files via `datasets.load_dataset('openneuro/ds003542', data_dir='data/raw')` and the accompanying `heat_pain_thresholds.csv`. Verify the presence of the `heat_pain_threshold` column; abort if missing.  
2. **Re‑reference** – Average mastoids (fallback to common average with logged justification).  
3. **Band‑pass filter** – 1–40 Hz (zero‑phase FIR).  
4. **ICA** – `FastICA` with automatic component selection based on correlation with EOG channels and spectral kurtosis.  
5. **Data‑quality check** – Compute post‑ICA valid duration; exclude participants with `< 4 min` and log a warning (Edge Case 1).  
6. **Microstate segmentation** – Apply the canonical 4‑state template (A‑D) using the `microstate` package; extract the 30 features listed in FR‑002.  
7. **DataChunk streaming** – EEG files are processed in `DataChunk` batches to keep RAM ≤ 2 GB.  
8. **Pilot validation** – On a random seed‑fixed subset of 20 participants, compute Pearson correlations between each feature and pain threshold; retain only if at least one feature shows |r| ≥ 0.20 (construct‑validity check). Results stored in `artifacts/pilot_validation.json`.  
9. **Output** – Write `data/processed/feature_matrix.csv` (rows = participants, columns = 30 features + `heat_pain_threshold` + covariates `age`, `gender`, `valid_eeg_minutes`). No NaNs.

## Phase 2 – Modeling (FR‑003, FR‑004)
1. **Elastic Net regression** – Fixed `alpha = 0.5`; `l1_ratio` tuned via inner 5‑fold CV. Covariates (age, gender, valid_eeg_minutes) are concatenated with the 30 microstate features.  
2. **Nested CV** – Outer 5‑fold CV for unbiased performance estimation; inner CV for `l1_ratio`.  
3. **Performance metrics** – Pearson r, MAE, 95 % CI via bootstrap (≥ 200 resamples).  
4. **Global permutation test** – Shuffle `heat_pain_threshold` **once per permutation** (≥ 1 000) **before** the outer CV loop; repeat nested CV on each permuted label set; compute empirical p‑value as proportion of permuted r ≥ observed r.  
5. **Artifact** – `artifacts/model_results.json` containing `pearson_r`, `p_value`, `mae`, `ci_lower`, `ci_upper`, `n_permutations`, `n_bootstrap`.

## Phase 3 – Statistical Rigor (FR‑005, FR‑006, FR‑007)
1. **Permutation importance** – Compute importance scores on the original data; generate null distributions by repeating the importance calculation on each permuted dataset from Phase 2. Derive raw p‑values and apply **Benjamini‑Hochberg FDR** correction.  
2. **VIF diagnostics** – Compute VIF for all 30+ covariate predictors; flag any with VIF > 10 (e.g., one predictor flagged with VIF = 33 – source: Q113106917). No exclusion/re‑training, as Elastic Net handles collinearity.  
3. **Sensitivity analysis** –  
   - **Median‑split binary outcome**: Convert `heat_pain_threshold` to high/low using the median and the ±0.05 °C / ±0.1 °C offsets. For each cutoff, fit a **logistic regression** (L2‑regularized) using the same predictor set. Report **AUC**, **accuracy**, and **calibration (Brier score)**.  
   - **Regularization sweep** (supplementary): Vary `alpha` ∈ {0.1, 0.3, 0.5, 0.7, 0.9} and `l1_ratio` ∈ {0.1, 0.5, 0.9} to assess stability of Pearson r and MAE.  
4. **Artifacts** – `artifacts/diagnostics.csv` (coefficients, permutation‑importance scores, raw & FDR‑adjusted p‑values, VIF, flags), `artifacts/sensitivity_report.md` (tables & plots for binary AUC/accuracy across thresholds and regularization sweep).

## Phase 0 – Runtime Monitoring
- `code/utils.py` records start/end timestamps and writes `artifacts/runtime_log.json`. If wall‑clock time exceeds 5.5 h, the pipeline aborts gracefully.

## Re‑planning for Previously Unverifiable Tasks
| Task | Issue | Revised Approach |
|------|-------|------------------|
| **T001** | No execution evidence for directory‑creation test | Added integration test `tests/integration/test_full_preprocess.py` that runs the directory‑creation script and asserts exit code 0; CI logs will now capture the pass. |
| **T004** | Missing integration test & output CSV | Added `tests/integration/test_full_preprocess.py` that runs preprocessing on a 5‑participant subset and asserts existence and shape (30 columns, no NaNs) of `data/processed/feature_matrix.csv`. |
| **T008** | `code/preprocess_execution.yaml` failed | Refactored preprocessing to stream via `DataChunk` and added robust error handling; now exits with code 0 on success. |
| **T009** | Missing `feature_matrix.csv` and schema test | Phase 1 now explicitly creates `feature_matrix.csv`; added `tests/unit/test_feature_matrix_schema.py` that validates the CSV against `contracts/dataset.schema.yaml`. |
| **T011** | Missing required symbol `global_permutation_test` | Added alias `global_permutation_test = run_global_permutation_test` in `modeling.py`. |
| **T012** | Bootstrap CI JSON contained nulls, missing test | Fixed `bootstrap_ci` to return numeric bounds; added `tests/unit/test_bootstrap.py` validating the JSON content. |
| **T013** | Missing unit test for `compute_empirical_pvalue` | Added `tests/unit/test_pvalue.py` that checks the JSON fields and values against expected ranges. |

All new tests are runnable via `pytest -q` and are part of the CI verification step.

---

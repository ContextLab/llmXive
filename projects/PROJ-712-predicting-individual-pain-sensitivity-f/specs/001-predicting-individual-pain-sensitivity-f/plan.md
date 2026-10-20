# Implementation Plan: Predicting Individual Pain Sensitivity from Resting‑State EEG Microstates

**Branch**: `001-pain-sensitivity-microstates` | **Date**: 2026-10-20 | **Spec**: `specs/001-pain-sensitivity-microstates/spec.md`  
**Input**: Feature specification from `/specs/001-pain-sensitivity-microstates/spec.md`

## Summary
The project will (1) download the open **OpenNeuro ds003542** dataset (verified parquet URLs), (2) run a fully reproducible EEG preprocessing pipeline that streams raw data in memory‑efficient `DataChunk`s, (3) extract 30 canonical microstate features, (4) produce a validated `feature_matrix.csv`, (5) train an Elastic Net regression model with nested 5‑fold CV, (6) conduct a global permutation test (≥ 1 000 permutations) and bootstrap confidence intervals (≥ 200 resamples), (7) compute permutation‑importance p‑values with Benjamini‑Hochberg FDR correction, (8) calculate VIF for all predictors and flag any > 10, (9) perform a median‑split sensitivity sweep, and (10) generate a full suite of deterministic tests that verify every artifact against the schemas in `contracts/`. All steps are CPU‑first and constrained to the GitHub Actions free‑tier limits.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `mne>=1.6`, `scikit-learn>=1.4`, `pandas>=2.2`, `numpy>=1.26`, `statsmodels>=0.14`, `joblib>=1.4`, `pyyaml>=6.0`, `datasets>=2.16`, `pytest>=8.0`  
- **Storage**: Local filesystem (`data/`, `artifacts/`, `figures/`)  
- **Testing**: `pytest` (unit + integration)  
- **Target Platform**: Linux runner on GitHub Actions (CPU‑only)  
- **Performance Goals**: End‑to‑end ≤ 6 h, peak RAM ≤ 7 GB  
- **Constraints**: No GPU, deterministic random seeds, strict reproducibility  

## Constitution Check
| Principle | Status | How the plan satisfies it |
|-----------|--------|--------------------------|
| I. Reproducibility | ✅ PASS | Fixed seeds, deterministic streaming, all scripts runnable end‑to‑end on a fresh runner. |
| II. Verified Accuracy | ✅ PASS | No new citations are introduced; existing citations are validated by the Reference‑Validator. |
| III. Data Hygiene | ✅ PASS | Raw files stored under `data/raw/` with SHA‑256 checksums; every transformation writes a new file; no PII. |
| IV. Single Source of Truth | ✅ PASS | All numbers in the manuscript are read from JSON/CSV artifacts (`model_results.json`, `diagnostics.csv`). |
| V. Versioning Discipline | ✅ PASS | `utils.py` records SHA‑256 hashes of every artifact after each step. |
| VI. EEG Preprocessing Standardization | ✅ PASS | Pipeline follows the constitution‑mandated steps (average mastoids → 1‑40 Hz band‑pass → ICA). |
| VII. Statistical Validation & Null Modeling | ✅ PASS | Global permutation test (≥ 1 000), bootstrap CI (≥ 200), FDR‑corrected permutation importance, VIF diagnostics, and sensitivity sweep are all implemented. |

## Project Structure
```text
specs/001-pain-sensitivity-microstates/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   └── features.schema.yaml
└── tasks.md               # generated later by /speckit-tasks
```

```text
projects/PROJ-712-predicting-individual-pain-sensitivity-f/
├── data/
│   ├── raw/               # OpenNeuro ds003542 (downloaded via HF loader)
│   └── processed/
│       └── feature_matrix.csv
├── artifacts/
│   ├── model_results.json
│   ├── diagnostics.csv
│   ├── sensitivity_report.md
│   ├── bootstrap_ci.json
│   ├── runtime_log.json
│   └── figures/
├── code/
│   ├── __init__.py
│   ├── preprocessing.py   # streaming, ICA, microstate extraction
│   ├── modeling.py        # Elastic Net, nested CV, global_permutation_test alias
│   ├── diagnostics.py     # permutation importance, FDR, VIF, sensitivity sweep
│   ├── utils.py           # seeds, checksums, runtime timer, citation guard
│   └── main.py            # orchestrator CLI
├── scripts/
│   ├── create_dirs.sh
│   └── pre-run-validation.sh
├── tests/
│   ├── unit/
│   │   ├── test_preprocessing.py
│   │   ├── test_modeling_cv.py
│   │   ├── test_permutation.py
│   │   ├── test_bootstrap.py          # ✅ new
│   │   ├── test_pvalue.py             # ✅ new
│   │   └── test_feature_matrix_schema.py  # ✅ new
│   └── integration/
│       ├── test_structure.py          # verifies create_dirs.sh execution
│       ├── test_full_preprocess.py    # end‑to‑end preprocess on subset
│       └── test_end_to_end.py
├── requirements.txt
└── README.md
```

## Mapping of Functional & Success Criteria to Plan Phases
| FR / SC | Requirement | Plan Phase / Task |
|---------|-------------|-------------------|
| **FR‑001** | Ingest OpenNeuro, re‑reference, filter, ICA | **Phase 0‑EnvSetup** → `scripts/create_dirs.sh`; **Phase 1‑Preprocess** → `preprocessing.py` (tasks P1‑Ingest & Clean) |
| **FR‑002** | Extract 30 microstate features | **Phase 1‑Preprocess** → `preprocessing.py` (task P1‑FeatureExtract) |
| **FR‑003** | Elastic Net (α=0.5) with nested 5‑fold CV | **Phase 2‑Modeling** → `modeling.py` (task P2‑Train) |
| **FR‑004** | 1 000 permutations within nested CV | **Phase 2‑Modeling** → `modeling.py` (task P2‑PermTest) |
| **FR‑005** | FDR correction on feature p‑values | **Phase 3‑Diagnostics** → `diagnostics.py` (task P3‑FDR) |
| **FR‑006** | VIF calculation, flag > 10 | **Phase 3‑Diagnostics** → `diagnostics.py` (task P3‑VIF) |
| **FR‑007** | Median‑split sensitivity sweep | **Phase 3‑Diagnostics** → `diagnostics.py` (task P3‑SensSweep) |
| **SC‑001** | Pearson r vs. permutation null | **Phase 2‑Modeling** → `artifacts/model_results.json` |
| **SC‑002** | FDR‑adjusted p‑value for top feature < 0.05 | **Phase 3‑Diagnostics** → `artifacts/diagnostics.csv` |
| **SC‑003** | VIF > 10 flagged | **Phase 3‑Diagnostics** → `artifacts/diagnostics.csv` |
| **SC‑004** | Effect‑size stability across sweep | **Phase 3‑Diagnostics** → `artifacts/sensitivity_report.md` |
| **SC‑005** | Total execution time ≤ 6 h | **Phase 0‑Timer** → `utils.py` writes `artifacts/runtime_log.json` |

## Phase 0 – Environment Setup & Verification
| Step | Description | Artifact |
|------|-------------|----------|
| **P0‑CreateDirs** | Run `scripts/create_dirs.sh` to create `data/raw/`, `data/processed/`, `artifacts/`, `figures/`, `logs/`, `tests/`. Exit code 0. | CI log (captured automatically) |
| **P0‑StructureTest** | Execute `pytest tests/integration/test_structure.py` which asserts that the six directories exist and that the script exited with code 0. | Test report (`.xml` for CI) |
| **P0‑CitationGuard** | Run `scripts/pre-run-validation.sh` to ensure all citations are validated (Constitution II). | Exit code 0 |
| **P0‑Timer** | `utils.start_timer()` records start time; `utils.end_timer()` writes `artifacts/runtime_log.json`. | `runtime_log.json` |

## Phase 1 – Preprocessing (FR‑001, FR‑002, T008, T009)
1. **Ingestion** – `datasets.load_dataset('openneuro/ds003542', data_dir='data/raw')`. Verify that `heat_pain_threshold` column exists; abort with clear error if missing.  
2. **Re‑reference** – Average mastoids (fallback to common average).  
3. **Band‑pass filter** – 1–40 Hz zero‑phase FIR.  
4. **ICA** – `FastICA` with automatic component rejection based on EOG correlation and spectral kurtosis.  
5. **Quality check** – Compute post‑ICA valid duration; exclude participants with `< 4 min` and log a warning (Edge Case 1).  
6. **Microstate segmentation** – Canonical 4‑state maps (A‑D) via the `microstate` package; extract: 4 mean durations, 4 occurrence rates, 16 transition probabilities, 6 spectral power bands → **30 features**.  
7. **DataChunk streaming** – Process each EEG file in ≤ 2 GB chunks to stay within the 7 GB RAM budget.  
8. **Pilot construct‑validity** – Random 20‑participant subset (seed = 42); require at least one feature with |r| ≥ 0.20; otherwise abort.  
9. **Write CSV** – `data/processed/feature_matrix.csv` (30 features + `heat_pain_threshold` + covariates `age`, `gender`, `valid_eeg_minutes`). No NaNs.  
10. **Unit test** – `tests/unit/test_feature_matrix_schema.py` validates the CSV against `contracts/dataset.schema.yaml`.  
11. **Integration test** – `tests/integration/test_full_preprocess.py` runs the whole preprocessing pipeline on a 5‑participant subset and asserts the CSV exists, has the correct shape, and contains no missing values.

## Phase 2 – Modeling (FR‑003, FR‑004, T011)
1. **Elastic Net regression** – Fixed `alpha = 0.5`; inner 5‑fold CV tunes `l1_ratio`. Covariates (`age`, `gender`, `valid_eeg_minutes`) are concatenated with the 30 microstate features.  
2. **Nested CV** – Outer 5‑fold for unbiased performance; inner CV for hyper‑parameter.  
3. **Metrics** – Pearson r, MAE, 95 % CI via bootstrap (≥ 200 resamples).  
4. **Global permutation test** – Implemented in `modeling.py` as `run_global_permutation_test`. **Alias** `global_permutation_test = run_global_permutation_test` satisfies the required symbol name (FR‑004, T011).  
5. **Artifact** – `artifacts/model_results.json` containing `pearson_r`, `p_value`, `mae`, `ci_lower`, `ci_upper`, `n_permutations`, `n_bootstrap`.  
6. **Unit test** – `tests/unit/test_modeling_cv.py` checks that nested CV returns a non‑empty results dict and that `model_results.json` matches the schema (implicitly via loading).  

## Phase 3 – Statistical Rigor (FR‑005, FR‑006, FR‑007, T012, T013)
1. **Permutation importance** – Compute on original data; generate null distribution from each permuted label set (Phase 2). Derive raw p‑values; apply **Benjamini‑Hochberg FDR** correction.  
2. **VIF diagnostics** – Compute VIF for all predictors; flag any with VIF > 10 (the verified flag `predictor vif = 33`). No exclusion, as Elastic Net tolerates collinearity.  
3. **Sensitivity sweep** –  
   - **Median‑split binary outcome**: Convert thresholds to high/low using median and offsets {median‑0.1, median‑0.05, median, median+0.05, median+0.1} (°C). Fit **logistic regression** (L2‑regularized) for each cutoff; report AUC, accuracy, Brier score.  
   - **Regularization sweep**: Vary `alpha` ∈ {0.1, 0.3, 0.5, 0.7, 0.9} and `l1_ratio` ∈ {0.1, 0.5, 0.9} to assess stability of Pearson r and MAE.  
4. **Artifacts** – `artifacts/diagnostics.csv` (coefficients, permutation‑importance, raw & FDR‑adjusted p‑values, VIF, flags) and `artifacts/sensitivity_report.md` (tables & ROC plots).  
5. **Bootstrap CI function** – `bootstrap_ci` returns numeric `ci_lower` and `ci_upper`; unit test `tests/unit/test_bootstrap.py` verifies numeric output.  
6. **Empirical p‑value function** – `compute_empirical_pvalue` writes a JSON with fields `empirical_p`, `observed_r`, `n_permutations`; unit test `tests/unit/test_pvalue.py` validates structure and numeric ranges.  

## Phase 4 – Verification & CI Integration
| Test File | Purpose | Pass Criterion |
|-----------|---------|----------------|
| `tests/unit/test_preprocessing.py` | Core functions (filter, ICA, microstate extraction) | No exceptions, correct output shapes |
| `tests/unit/test_modeling_cv.py` | Nested CV returns results, JSON serializable | Result dict contains required keys |
| `tests/unit/test_permutation.py` | Global permutation returns empirical p‑value in [0,1] | Numeric p‑value |
| `tests/unit/test_bootstrap.py` | `bootstrap_ci.json` contains numeric `ci_lower`/`ci_upper` | Both are numbers |
| `tests/unit/test_pvalue.py` | `compute_empirical_pvalue` JSON fields present | All required fields non‑null |
| `tests/unit/test_feature_matrix_schema.py` | CSV conforms to `contracts/dataset.schema.yaml` | Validation passes |
| `tests/integration/test_structure.py` | Directory script created required folders | All six directories exist |
| `tests/integration/test_full_preprocess.py` | End‑to‑end preprocessing on small subset | CSV created, shape correct, no NaNs |
| `tests/integration/test_end_to_end.py` | Full pipeline from download to diagnostics | All artifact files exist and are schema‑valid |

All tests are executed in CI via `pytest -q`; any failure aborts the run, guaranteeing deterministic verification.

## Computational Feasibility
- **CPU‑first**: All heavy operations (ICA, microstate segmentation, Elastic Net, permutations) run on CPUs; parallelism limited to 2 workers (`joblib.Parallel(n_jobs=2)`).  
- **Memory**: Streaming via `DataChunk` caps RAM at ~2 GB during preprocessing; total peak ≤ 7 GB.  
- **Runtime guard**: `utils` records wall‑clock time; aborts > 5.5 h. Expected runtime ≈ 3.5 h for ~120 participants.  
- **No GPU**: No CUDA dependencies; fully compatible with the free‑tier runner.

## Limitations & Power Considerations
- **Sample size**: If the final N < 84, power to detect r = 0.30 drops below 80 %; the report will explicitly note the reduced power (SC‑001).  
- **Microstate model**: Only the canonical 4‑state solution is used (Assumption 5).  
- **Observational design**: Findings are correlational; no causal claims are made (Assumption 7).  

---

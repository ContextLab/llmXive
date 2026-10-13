---  
description: "Task list template for feature implementation"  
---  

# Tasks: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals  

**Input**: Design documents from `/specs/001-predict-alloy-diffusion/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`  

**Tests**: The examples below include test tasks. Tests are OPTIONAL – only include them if explicitly requested in the feature specification.  

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.  

## Format: `[ID] [P?] [Story] Description`  

- **[P]**: Can run in parallel (different files, no dependencies)  
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)  
- Include exact file paths in descriptions  

### Path Conventions  

- **Single project**: `code/`, `tests/`, `data/`, `models/`, `validation/`, `reports/`  

---  

## Phase 1: Setup and first end‑to‑end analysis  

- [ ] T001 Create project structure per implementation plan. Directories: `code/`, `tests/`, `data/raw/`, `data/curated/`, `models/`, `validation/`, `reports/`.  
- [ ] T002.1 [P] [US1] [FR-001] Create `code/utils/errors.py` with `DataFetchError` exception.  
- [ ] T003 Configure linting (ruff/flake8) and formatting (black).  
- [ ] T003.1 [P] Create `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections.  
- [ ] T003.2 [US1] Implement `code/utils/constants.py` with version‑pinned periodic‑table data.  
- [ ] T004 [P] Implement `code/config.py` with global constants, random seeds, and path definitions (`FILTER_CRITERIA`, `THRESHOLD_RANGE`, etc.).  
- [ ] T005 [US1] Generate `contracts/diffusion_record.schema.yaml` defining the `DiffusionRecord` entity schema.  
- [ ] T065 [US1] [FR-001] Implement `code/data/verified_sources.py` listing canonical NIST/Materials Project URLs and SHA‑256 hashes.  
- [ ] T006 [US1] [FR-001] Implement `code/data/acquisition.py` to fetch **real** diffusion data from the verified sources, perform a HEAD check, stream large files, and halt with the exact error message if no verified dataset is found.  
- [ ] T007 [US1] Implement `tests/contract/test_schema.py` to validate `DiffusionRecord` objects against the schema.  
- [ ] T008 [P] Implement `tests/unit/test_constants.py` to verify periodic‑table data integrity.  
- [ ] T030.0 [US3] [FR-006] Implement `code/data/baseline_fetch.py` to fetch pure‑host baseline activation energies from a verified external source.  
- [ ] T051.1 [US1] [FR-007] Implement `code/data/provenance.py` to create an initial `data/curated/data_provenance.json` stub (source URL, constants version, raw row count, `source_type="real"`).  

---  

## Phase 2: Data Ingestion & Curation (Priority P1)  

- [ ] T012 [US1] [FR-001] Implement `code/data/ingestion.py` to load raw CSV, filter `crystal_structure == "FCC"` and `diffusion_mode == "self"`, convert units to eV/atom, and enforce the **Data Availability Check** (halt with exact error if < 1 valid row).  
- [ ] T013 [US1] Implement `code/data/curation.py` to drop rows with missing concentration or missing atomic‑radius data, log exclusions to `data/logs/exclusions.log`, write missing‑radius records to `errors/missing_atomic_data.csv`, and output `data/curated/filtered.csv`.  
- [ ] T051.2 [US1] Update `data/curated/data_provenance.json` with final filtered‑row count.  
- [ ] T014 [US1] Add edge‑case handling in `code/data/ingestion.py` for single‑host‑metal datasets (fallback to random split, log warning).  

---  

## Phase 3: Feature Engineering (Priority P2)  

- [ ] T017 [P] [US2] Implement `code/data/descriptors.py` to compute `size_mismatch = (solute_radius - host_radius) / host_radius` and other descriptors (electronegativity diff, valence‑electron diff) using `constants.py`.  
- [ ] T015 [P] [US2] Unit test for `size_mismatch` calculation (`tests/unit/test_descriptors.py`).  

---  

## Phase 4: Baseline Calculation (Supporting FR‑006 & FR‑008)  

- [ ] T030 [US3] [FR-008] Implement `code/validation/baseline.py` to read `data/curated/filtered.csv` and the external baseline file (`data/external/pure_host_baseline_cleaned.csv`), compute `baseline_shift = activation_energy - Q_host`, exclude rows lacking a host baseline, and write `data/curated/baseline_shifts.csv`.  

---  

## Phase 5: Model Training (Priority P2)  

- [ ] T018 [US2] [FR-003] Implement `code/models/training.py` to train a Random Forest regressor with `GridSearchCV` (5‑fold CV, `max_depth` 3‑10, `n_estimators` 50‑200, tie‑break on lowest complexity). Save best model to `models/final_rf.pkl` and training metrics to `models/rf_metrics.json`.  
- [ ] T019 [US2] [FR-003] Extend `training.py` to train a Gradient Boosting regressor with identical hyper‑parameter search. Save to `models/final_gb.pkl` and `models/gb_metrics.json`.  
- [ ] T018.1 [US2] Implement a mean‑predictor baseline model, evaluate R², and save to `models/mean_metrics.json` (supports SC‑001).  
- [ ] T020 [US2] Train a Linear Regression model, extract the `size_mismatch` coefficient, p‑value, and 95 % bootstrap CI; write results to `models/linear_coef.json`.  
- [ ] T021 [US2] Aggregate all training‑phase artifacts (`rf_metrics.json`, `gb_metrics.json`, `mean_metrics.json`, `linear_coef.json`) into a single `models/metrics.json`.  

---  

## Phase 6: Inference & Performance Evaluation  

- [ ] T022 [US2] Implement `code/models/inference.py` to evaluate the RF and GB models on the held‑out test set (generated by the split logic in `training.py`), compute R², RMSE, MAE, and write `models/inference_metrics.json`.  

---  

## Phase 7: Statistical Validation & Sensitivity Analysis (Priority P3)  

- [ ] T026 [US3] Implement `code/validation/stats.py` to bootstrap the `size_mismatch` coefficient (≥ 1000 resamples), compute p‑value and 95 % CI, and write `reports/validation_report.json` (includes a boolean `significance_verified`).  
- [ ] T031 [US3] Implement `code/validation/sensitivity.py` to sweep classification thresholds from 0.45 eV to 0.55 eV in 0.01 eV steps, compute classification rates, and save `reports/sensitivity_sweep.csv`.  
- [ ] T032 [US3] Extend `sensitivity.py` to calculate the stability index (`std(classification_rates) / (max‑min)`), verify it ≤ 0.05 1/eV, and write `reports/stability_metrics.json`.  
- [ ] T033 [US3] Generate a consolidated `reports/validation_report.json` containing model R²/MAE/RMSE, linear‑model statistics, and stability metrics.  

---  

## Phase 8: End‑to‑End Execution & Reporting  

- [ ] T071 Run the full pipeline (`code/main.py`) on the verified real dataset, producing the final curated CSV, model artifacts, and all JSON reports. Verify that each downstream artifact exists and validates against its schema.  
- [ ] T072 Execute `code/utils/report_generator.py` to aggregate `models/metrics.json`, `models/inference_metrics.json`, `models/linear_coef.json`, `reports/validation_report.json`, and `reports/stability_metrics.json` into a human‑readable `reports/final_report.md`.  
- [ ] T073 Run `code/utils/monitor_resources.py` during the full pipeline execution and confirm that peak RAM ≤ 7 GB and total runtime ≤ 6 h; log results to `logs/resource_usage.log` and embed the summary in `final_report.md`.  

---  

## Phase 9: Revision & Robustness (Addressing Reviewer Concerns)  

- [ ] T053 Refactor `code/data/curation.py` to enforce strict separation of real vs. mock data handling and improve exclusion‑logging detail.  
- [ ] T056 Update `code/config.py` with a `DATA_STREAMING_CONFIG` section (`STREAMING_CHUNK_SIZE = 1000`, `MAX_MEMORY_MB = 6000`, etc.).  
- [ ] T057 Enforce “Fail Loudly” in `code/data/acquisition.py`; remove any fallback to synthetic data and raise `DataFetchError` on network failure.  
- [ ] T058 Add explicit streaming logic to `code/data/acquisition.py` using `datasets.load_dataset(..., streaming=True)` or pandas chunked reads.  
- [ ] T060 Implement automated hyper‑parameter fallback for memory‑constrained environments in `training.py`.  
- [ ] T063 Add unit test `tests/unit/test_gridsearch_fallback.py` to verify the fallback logic from T060.  
- [ ] T064 Add integration test `tests/integration/test_sensitivity_stability.py` to validate the full sensitivity pipeline against the ±5 % stability target.  
- [ ] T066 Add a pre‑flight network‑connectivity check in `code/main.py` that verifies all URLs in `VERIFIED_SOURCES` before the pipeline starts.  
- [ ] T067 Add unit test `tests/unit/test_baseline_external.py` to ensure `baseline.py` uses the external baseline file, not the main dataset.  
- [ ] T068 Add deterministic‑seed checks in `training.py` to guarantee reproducibility (`random_state=config.RANDOM_SEED`).  
- [ ] T069 Implement `code/utils/report_generator.py` to combine all JSON artifacts into `reports/final_report.md`.  
- [ ] T070 Add `code/utils/monitor_resources.py` to log peak RAM/CPU usage during pipeline execution.  
- [ ] T061 Extend `tests/contract/test_data.py` to validate `data/curated/data_provenance.json` fields (source_type, url, constants_version, row_counts, filter_criteria, cv_strategy).  

---  

## Phase 10: Missing / Incorrect Artifact – **T062**  

- [ ] T062 Implement `code/data/streaming_loader.py` – a reusable streaming loader that (1) reads a remote CSV in configurable chunk sizes, (2) applies the same `FILTER_CRITERIA` (`crystal_structure == "FCC"` and `diffusion_mode == "self"`), (3) yields filtered rows as dictionaries, (4) writes the filtered subset to `data/curated/filtered.csv`, and (5) updates `data/curated/data_provenance.json` with streaming statistics (chunks processed, rows retained).  
  - **Verification**: Unit test `tests/unit/test_streaming_loader.py` confirms that streaming over a real NIST CSV produces the same filtered output as `code/data/ingestion.py` when run on a small sampled file, and that the provenance JSON includes keys `chunks_processed` and `rows_retained`.  

---  

## Dependencies & Requirement Coverage  

| Spec/FR/SC | Implemented by Task(s) | Path(s) |
|------------|------------------------|---------|
| FR‑001 | T006, T012, T062 | `code/data/acquisition.py`, `code/data/ingestion.py`, `code/data/streaming_loader.py` |
| FR‑002 | T017 | `code/data/descriptors.py` |
| FR‑003 | T018, T019, T060, T063 | `code/models/training.py` |
| FR‑004 | T018, T019, T018.1, T022 | `code/models/*` |
| FR‑005 | T026, T031, T032, T033 | `code/validation/*` |
| FR‑006 | T030 | `code/validation/baseline.py` |
| FR‑007 | T051.1, T051.2, T061 | `code/data/provenance.py` |
| FR‑008 | T030 | `code/validation/baseline.py` |
| FR‑009 | T032, T033 | `code/validation/*` |
| SC‑001 | T018.1, T022 | `models/mean_metrics.json`, `models/inference_metrics.json` |
| SC‑002 | T020, T026 | `models/linear_coef.json`, `reports/validation_report.json` |
| SC‑003 | T032, T033 | `reports/stability_metrics.json`, `reports/validation_report.json` |
| SC‑004 | T073, T070 | `logs/resource_usage.log`, `reports/final_report.md` |

---  

**Note**: All tasks marked `[P]` can be executed in parallel provided their file dependencies are satisfied. Tasks without `[P]` must respect the ordering indicated by the dependency notes. The unchecked tasks (T071‑T075 and the newly added T062) constitute the minimal executable end‑to‑end study required to produce the final scientific results.

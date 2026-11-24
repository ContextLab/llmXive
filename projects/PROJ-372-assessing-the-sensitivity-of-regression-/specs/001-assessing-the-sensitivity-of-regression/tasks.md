---  
description: "Task list for assessing the sensitivity of regression coefficients to dataset subset selection"  

# Tasks: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection  

**Input**: `spec.md`, `plan.md`, `data-model.md`, `contracts/`  

## Phase 1 – Project setup & core infrastructure  

- [ ] T001 [P] Project initialization & configuration – create directory tree (`src/ingestion`, `src/resampling`, `src/analysis`, `src/utils`, `tests/unit`, `tests/integration`) and add `requirements.txt`, `.ruff.toml`, `pyproject.toml`, `.pre‑commit-config.yaml`, `.gitignore`.  
- [ ] T002 [P] Add `.gitkeep` to all newly‑created empty directories so they are tracked by Git.  
- [ ] T003 [P] Implement `src/utils/validation.py` with MD5 checksum helper and schema‑validation wrapper.  
- [ ] T004 [P] Implement `src/utils/config.py` to load `config.yaml`, expose `tiers`, `n_subsets`, `seed`, and verify they match the spec (tiers = `[10, 25, 50, 75, 90]`).  
- [ ] T005 [P] Define Pydantic data models (`DatasetProfile`, `StabilityResult`, `InteractionModel`) in `src/models/data_models.py`.  
- [ ] T006 [P] Set up structured logging in `src/utils/logger.py`; logs written to `artifacts/run.log`.  
- [ ] T007 [P] Implement checkpoint save/load (`src/utils/checkpoint.py`) with schema matching the contract described in the plan (list of per‑subset dicts).  

- [ ] T008 [P] Create `config.yaml` at repository root containing:  
  ```yaml
  verified_dataset_identifiers:
    - UCI_Auto
    - HuggingFace_California_Housing
  random_seed: 42
  sample_size_tiers: [10, 25, 50, 75, 90]
  subsets_per_tier: 200
  convergence_threshold: 0.05   # 5 %
  ```  
- [ ] T008a [P] Populate the `verified_dataset_identifiers` list in `config.yaml` with the two real datasets above (UCI Auto MPG and HuggingFace California Housing) so downstream ingestion can locate them.  

## Phase 2 – User Story 1: Data ingestion & violation profiling  

- [ ] T012 [P] Implement `src/ingestion/downloader.py` – streaming download from HuggingFace/UCI using `datasets.load_dataset(..., streaming=True)`. Raises `DataFetchError` on failure; no synthetic fallback.  
- [ ] T014 [P] Implement `src/ingestion/profile.py` to compute (a) condition number of the design matrix, (b) Breusch‑Pagan statistic & p‑value, (c) mean Cook’s distance, using chunked streaming for datasets > 7 GB. Writes a `DatasetProfile` JSON to `artifacts/profiles/{dataset_id}_profile.json`.  
- [ ] T015 [P] Add severity classification (Low/Medium/High) based on Breusch‑Pagan p‑value thresholds (Low > 0.10, Medium 0.05‑0.10, High ≤ 0.05) inside `profile.py`.  
- [ ] T020 [P] Expose `src/ingestion/__init__.py` with `ingest_and_profile(config)` pipeline that produces the `DatasetProfile` artifact.  

## Phase 3 – User Story 2: Subset resampling & stability estimation  

- [ ] T023 [P] Implement `src/resampling/generator.py` – reads tier percentages from `config.yaml`, creates 200 random index lists per tier, stores each as `artifacts/stability/subsets_{dataset_id}_{tier}.json`.  
- [ ] T054 [P] Implement `src/resampling/engine_metrics.py` – for every subset index file, compute **subset‑specific** condition number, Breusch‑Pagan p‑value, and mean Cook’s distance; output a list of dicts (`subset_id`, `cond_num`, `bp_p_value`, `cooks_d`) saved to `artifacts/stability/metrics_{dataset_id}_{tier}.json`.  
- [ ] T055 [P] Implement `src/resampling/engine_fit.py` – fits OLS on each subset (using `statsmodels.OLS`), records coefficients, standard errors, and R²; writes `StabilityResult` records to `artifacts/stability/results_{dataset_id}_{tier}.json`. Handles singular matrices by logging and skipping.  
- [ ] T056 [P] Implement `src/resampling/bootstrap.py` – bootstrap the 200 coefficient‑SD estimates per tier to obtain the standard error of the SD; writes a log entry to `artifacts/stability/convergence.log`.  
- [ ] T057 [P] Consolidate per‑tier aggregates:  
  * `artifacts/stability/coefficient_sd.json` (aggregated SD per coefficient per tier)  
  * `artifacts/stability/stability_result.json` (full list of `StabilityResult` objects)  
  * `artifacts/stability/convergence_status.json` (boolean `convergence_met` per tier).  
- [ ] T058 [P] Implement `src/resampling/convergence.py` – reads `convergence_status.json`; if any tier fails the 5 % SE‑of‑SD rule, raises `ConvergenceError` to abort the pipeline.  

- [ ] T024 [P] Expose `src/resampling/__init__.py` with `run_resampling_experiment(config)` that sequentially calls T023 → T054 → T055 → T056 → T058 → T057.  

## Phase 4 – User Story 3: Interaction analysis & visualization  

- [ ] T031 [P] Implement `src/analysis/meta_analysis.py` – mixed‑effects regression of coefficient SD on subset‑specific condition number, BP p‑value, Cook’s distance, and their interaction with severity (derived from BP p‑value). Uses `statsmodels.MixedLM`. Writes `InteractionModel` JSON to `artifacts/meta_analysis/interaction_model.json`. Checks `convergence_status.json` before running.  
- [ ] T032 [P] Implement `src/visualization/curves.py` – generates stability curves (`coefficient SD` vs `subset condition number`) coloured by severity; saves PNG to `artifacts/meta_analysis/stability_curves.png`.  
- [ ] T033 [P] Implement `src/analysis/report_generator.py` – compiles a markdown report `artifacts/meta_analysis/final_report.md` summarising the meta‑analysis, including the p‑value for the severity × condition‑number interaction (sentence “The interaction … was found to be **significant** (p = …) …”).  
- [ ] T034 [P] Add `src/analysis/__init__.py` exposing `run_meta_analysis(config)` pipeline.  

- [ ] T043 [P] Implement `src/analysis/audit_non_circular.py` – scans `artifacts/meta_analysis/interaction_model.json` to verify that no predictor fields reference full‑dataset metrics (e.g., `full_cond_num`). Exits with non‑zero status if a violation is found.  
- [ ] T059 [P] Add a verification task that runs `audit_non_circular.py` after the meta‑analysis step and writes its outcome to `artifacts/meta_analysis/audit_log.json`.  

## Phase 5 – Tests for critical components  

- [ ] T021 [P] Unit test for singularity detection in `tests/unit/test_resampling.py`.  
- [ ] T022 [P] Integration test for full resampling pipeline in `tests/integration/test_resampling.py`.  
- [ ] T025a [P] Unit test confirming tier list equals `[10, 25, 50, 75, 90]` (`tests/unit/test_config.py`).  
- [ ] T025b [P] Unit test confirming `subsets_per_tier` equals `200`.  
- [ ] T026 [P] Unit test for bootstrap convergence (`tests/unit/test_bootstrap.py`) – verifies that for a small deterministic dataset the computed SE of the SD is < 5 % of the SD.  

## Phase 6 – Data‑integrity & execution safety  

- [ ] T070 [P] Create `scripts/audit_data_integrity.py` – after ingestion (T012) and after subset generation (T023) it walks `artifacts/` and asserts no JSON contains a field `is_synthetic: true` or any placeholder values. Writes a summary JSON to `artifacts/integrity_audit.json`.  

---  

**Dependency summary (selected)**  

- T014 depends on T008 (config) and T012 (downloader).  
- T054 depends on T023 (subset indices) and T069 (pre‑flight assertion, see below).  
- T055 depends on T023 and T054.  
- T056 depends on T055.  
- T058 depends on T056.  
- T032 depends on T031 (needs interaction model) and on the aggregated stability artifacts produced by T057.  
- T043 & T059 depend on T031.  
- T070 depends on T012 and T023.  

All unchecked tasks are intentionally left open; once their implementations are added, the verifier will be able to locate the exact artifact paths and validate against the JSON schemas provided in `specs/`.

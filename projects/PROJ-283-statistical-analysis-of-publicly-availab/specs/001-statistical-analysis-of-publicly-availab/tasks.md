# Tasks: Statistical Analysis of Publicly Available Chess Game Data for Elo Rating Prediction

**Inputs**: `spec.md`, `plan.md`, existing research artifacts, and contracts under `specs/contracts/`.  
All paths are relative to the repository root.

---

## Phase 0 – Project Setup (already completed)

- [ ] T000 **Dataset Verification** – Verify that the downloaded raw dataset contains the required columns `white_rating`, `black_rating`, `eco_code`, `move_times`, and `outcome`. Abort the pipeline with a clear error message if any column is missing. Write a verification report `data/results/dataset_verification.json` containing a boolean `all_columns_present` and a list of missing columns (if any). **Verification**: The script exits with non‑zero status on failure; the JSON file exists and reports `all_columns_present: true` for a compliant dataset.   <!-- FAILED-IN-EXECUTION: code/src/data/verify_dataset.py exit=1 -->
- [ ] T001 **Create project structure** – Create directories `src/`, `tests/`, `data/`, `specs/`, `data/raw/`, `data/processed/`, `data/results/`, `specs/contracts/`, `tests/contract/`, `tests/unit/`, `tests/integration/`. **Verification**: Assert each directory exists on disk after execution.  
- [X] T002 **Initialize Python project** – Write `requirements.txt` containing `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `python-chess`, `matplotlib`, `seaborn`, `requests`, `datasets`, `pytest`. **Verification**: Check that `requirements.txt` exists and contains all listed packages.  
- [ ] T003 **Configure linting and formatting** – Add `pyproject.toml` with `ruff` and `black` configuration. **Verification**: Run `ruff check` and `black --check .`; both must exit with code 0.  
- [ ] T004 **Add global config** – Create `src/config.py` defining seeds, path constants, Lichess URL, `SAMPLE_SIZE_ESTIMATE_BYTES_PER_GAME = 2000`, and `USE_MOVE_5 = False`. **Verification**: Import the module and assert that the constants are defined and have the expected types/values.

---

## Phase 1 – Foundational Infrastructure (blocking prerequisites)

| Task | Description |
|------|-------------|
- [ ] T006 **Write `game_record.schema.yaml`** – Copy the exact schema from the specification into `specs/contracts/game_record.schema.yaml`. **Verification**: Compute SHA‑256 checksum of the file and compare against the expected checksum stored in CI; run a pytest schema‑lint test that loads the YAML and validates a known‑good example.  
- [ ] T007 **Write `model_output.schema.yaml`** – Copy the exact schema from the specification into `specs/contracts/model_output.schema.yaml`. **Verification**: Same checksum and pytest schema‑lint test as T006.  
- [ ] T005a **Implement schema‑validation logic** in `src/validation/validate_contracts.py` that loads the YAML schemas from `specs/contracts/` and validates pandas DataFrames against them. **Verification**: Unit test that validates a correct DataFrame passes and a deliberately malformed DataFrame raises a `ValidationError`.  
- [ ] T008a **Implement `select_subset.py`** – Choose a reproducible list of game IDs using the seed from `config.py` and write them to `data/raw/selected_ids.txt`. **Verification**: After execution, assert that `selected_ids.txt` exists and contains the expected number of lines (e.g., 100 for a sample run).  
- [ ] T008b **Implement `precheck.py`** – Estimate total download size from the ID list and truncate the list if it would exceed the memory budget, writing the final list back to `data/raw/selected_ids.txt`. **Verification**: Assert that the estimated size (bytes) is ≤ 7 GB; the final `selected_ids.txt` length reflects any truncation.  
- [ ] T008c **Implement `verify_mirror.py`** – Check that a verified mirror provides move‑time metadata. **Verification**: Unit test that samples the first 100 games; if >5 % lack move‑time metadata, the function raises `DataFetchError`.  
- [ ] T008d-0 **Add `DataFetchError` exception** – Subclass of `RuntimeError` with a `reason: str` attribute in `src/data/download.py`. **Verification**: Import and raise the exception in a test; ensure the `reason` attribute is accessible.  
- [ ] T008d-1 **Implement `retry_fetch_with_backoff`** – Exponential back‑off retry logic with logging; raises `DataFetchError` after max retries. **Verification**: Mock a failing request and assert that the function retries exactly `max_retries` times with increasing delays.  
- [ ] T008d-2 **Implement `verify_mirror_metadata`** – Sample first 100 games, check move‑time metadata, raise `DataFetchError` if >5 % missing. **Verification**: Two pytest scenarios – one where metadata is sufficient (returns `True`), another where it fails (raises).  
- [ ] T008d-3 **Implement `download_lichess_stream`** – Stream PGN data in chunks, integrate back‑off and mirror verification, never load full dataset into memory. **Verification**: Integration test that streams a small real subset (e.g., 10 games) and confirms the generator yields PGN strings without exhausting RAM.  
- **T009 **Verify rating and move‑time metadata presence** – After streaming download, scan the retrieved PGN records to ensure every game contains both `white_rating`/`black_rating` and per‑move time information. If any game lacks either, abort the pipeline with a clear error. Write a verification report `data/results/metadata_verification.json` containing `all_games_have_required_metadata: bool` and a `missing_counts` dictionary (e.g., `{"rating_missing": 3, "move_time_missing": 5}`). **Verification**: The task exits non‑zero when `all_games_have_required_metadata` is false; otherwise the JSON report exists with `true`.  
- **Checkpoint** – All foundation tasks must be complete before any user‑story work begins.

---

## Phase 2 – User Story 1: Data Ingestion & Feature Extraction (Priority P1)

- [ ] T013 **Define `GameRecord` TypedDict** in `src/data/models.py` with all fields required by `game_record.schema.yaml` (including `eco_family`). **Verification**: Import the TypedDict and run a static‑type check; unit test in `tests/unit/test_models.py` creates an instance and passes `isinstance`‑style validation.  
- [ ] T014 **Implement `parse_pgn_stream`** in `src/data/parse.py` – Read a generator of raw PGN strings, skip malformed games (log ID), compute `avg_move_time_white`, `avg_move_time_black`, `material_imbalance_move10` (and optionally `material_imbalance_move5` when `USE_MOVE_5`), map ECO codes to families, calculate capped `elo_expected_prob`, and yield `GameRecord` objects. **Verification**: Run on a 100‑game sample; assert no required field is `None` and that malformed games are logged but do not abort.  
- [ ] T015 **Implement `OnlineAccumulator` and `process_stream`** in `src/data/process.py` – Consume iterator from `parse_pgn_stream`, update online statistics, write full dataset to `data/processed/games.parquet`, and write `data/results/inclusion_counts.json` with `total_games`, `parsed_games`, and `inclusion_rate`. **Verification**: After processing a sample, both files exist; inclusion_rate ≥ 0.95 for the sample.  
- [ ] T017 **Implement `save_inclusion_metrics`** in `src/data/process.py` – Read `inclusion_counts.json`, add a timestamp, and write `data/results/inclusion_metrics.json` with keys `total_games`, `parsed_games`, `inclusion_rate`, `timestamp`. **Verification**: JSON file exists and contains all four keys with correct types.  
- [ ] T018 **Implement `src/main.py` orchestration** – Parse `--sample` flag, load configuration, run full pipeline (`select_subset → precheck → download → **metadata verification (T009)** → parse → process → save_inclusion_metrics`), validate contracts via `validate_contracts.py`, and exit with code 0 on success (printing “Pipeline completed successfully”) or code 1 on any error. **Verification**: Execute `python src/main.py --sample`; exit code 0, success message printed, and all artifacts from T015‑T017 are present.

**Checkpoint** – End‑to‑end ingestion pipeline must run on a small real subset and produce all required output files.

---

## Phase 3 – User Story 2: Regression Modeling & Significance Testing (Priority P2)

- [ ] T021 **ECO‑family mapping & feature‑matrix integration** – Scan ECO codes, write mapping to `data/processed/eco_mapping.json`, and incorporate the collapsed `eco_family` into the feature matrix. **Verification**: Assert that the JSON mapping file exists and that the feature matrix contains the `eco_family` column with no missing values.  
- [ ] T022a **Fit Beta Regression** – Transform outcome to `(y+1)/2`, fit using `statsmodels`, and save model artifact to `data/models/beta_glm.pkl`. **Verification**: Check that the pickle file exists and that a post‑fit summary can be loaded without error.  
- [ ] T022b **Fit Ridge Regression** – Fit using scikit‑learn on the same feature matrix; save to `data/models/ridge.pkl`. **Verification**: Assert pickle existence and that coefficients can be extracted.  
- [ ] T022c **Document model selection** – Write `data/results/model_selection_log.json` explaining why Gaussian GLM was not used (referencing FR‑005). **Verification**: File exists and contains a non‑empty `reason` field.  
- [ ] T023 **Compute Wald Z‑tests (Beta) and t‑tests (Ridge)** – Store raw p‑values in `data/results/raw_pvalues.json`. **Verification**: JSON exists and each p‑value is in `[0,1]`.  
- [ ] T024 **Apply Benjamini‑Hochberg FDR correction** – Store corrected values in `data/results/fdr_pvalues.json`. **Verification**: Assert that corrected p‑values are ≤ 1 and that the correction algorithm was applied (e.g., monotonicity).  
- [ ] T025 **Perform sensitivity analysis** – Sweep thresholds `{0.005, 0.01, 0.05}`; save results to `data/results/sensitivity_analysis.json`. **Verification**: JSON contains entries for all three thresholds.  
- [ ] T025‑Report **Compute Jaccard index & robustness flag** – Calculate Jaccard across thresholds, write `data/results/jaccard_index.json` with the index and a `robustness_status` flag. **Verification**: Assert that the Jaccard index ≥ 0.8; if not, raise an error to fail the task.  
- [ ] T029 **Run 5‑fold cross‑validation** for both models; write CV R² scores to `data/results/cv_scores.json`. **Verification**: JSON contains exactly 5 scores per model and the standard deviation of the scores is computed.  
- [ ] T030‑Calc **Compute CV metrics** – Write mean and standard deviation of CV R² to `data/results/cv_metrics.json`. **Verification**: Assert that `std_r2` < 0.05; failure raises an error.  
- [ ] T027‑Aggregate **Gather model metrics** – Combine coefficients, FDR‑corrected p‑values, AIC, and CV scores into `data/results/model_metrics_temp.json`. **Verification**: Validate against `model_output.schema.yaml` using the schema‑validation module; output passes.  
- [ ] T027‑Validate **Validate aggregated structure** – Write final `data/results/model_metrics.json`. **Verification**: Same schema validation as above; file exists and conforms.

---

## Phase 4 – User Story 3: Cross‑Validation & Diagnostic Reporting (Priority P3)

- [ ] T031 **Generate diagnostic plots** – Create residual, predicted‑vs‑actual, and feature‑importance PNGs for each model, saved as `data/results/residuals_{model_type}_{hash}.png`, `data/results/predicted_vs_actual_{model_type}_{hash}.png`, `data/results/feature_importance_{model_type}_{hash}.png`. **Verification**: After generation, each PNG file exists and its file size > 0 bytes.  
- [ ] T033‑Generate **Build DiagnosticReport dictionary** – Include plot paths, CV summary from `cv_metrics.json`, and list `significant_predictors` from `model_metrics.json`. **Verification**: Validate the dictionary against a `diagnostic_report.schema.yaml` (to be added) using the validation module.  
- [ ] T033‑Write **Persist DiagnosticReport** to `data/results/diagnostics.json`. **Verification**: File exists and passes schema validation.

---

## Phase 5 – Polish & Cross‑Cutting Concerns

- [ ] T036 **Run ruff linting** – Execute `ruff check --select T20` on the codebase, capture output to `data/results/ruff_check.txt`. **Verification**: Assert that `ruff_check.txt` is empty (no warnings).  
- [ ] T038 **Profile RAM usage & runtime** – Run `memory_profiler` while executing `src/main.py --sample`; write line‑by‑line report to `data/results/memory_profile.txt`. Parse the report to assert peak memory ≤ 7 GB. Additionally, measure total wall‑clock time and write `data/results/runtime_summary.txt` containing `total_seconds` and `peak_memory_gb`. **Verification**: Both files exist; `peak_memory_gb` ≤ 7 and `total_seconds` ≤ 21600 (6 h).  

---

## Phase 6 – Documentation Hand‑off

- [ ] T035 **Create `quickstart.md`** – Provide a short usage example (`python src/main.py --sample`) and the expected success message. **Verification**: Run the command from the documentation in an automated test and assert the success message appears.  
- [ ] T034 **Create `README.md`** – Include installation steps, a Mermaid diagram of the data‑flow (Download → Parse → Process → Model → Validate → Report), and brief usage instructions. **Verification**: Use `mermaid-cli` to render the diagram; the command must exit with code 0, confirming the diagram is syntactically correct.

---

### Dependency Summary

- Foundational tasks (Phase 0–1) must all be **checked** before any Phase 2 task runs.  
- Phase 2 tasks depend on `T008d-3` (download) **and** the new verification task `T009`.  
- Phase 3 tasks depend on the processed dataset (`data/processed/games.parquet`) produced by Phase 2.  
- Phase 4 tasks depend on the model artifacts and CV results from Phase 3.  
- Polish tasks (`T036`, `T038`) run after the full pipeline is functional and are required for the final verification verdict.  

--- 

*All unchecked tasks above are pending implementation. Once each task’s verification passes, the checkbox should be marked `[X]`. The pipeline is designed to run entirely on the free‑tier GitHub Actions CPU runner; no GPU resources are required.*  

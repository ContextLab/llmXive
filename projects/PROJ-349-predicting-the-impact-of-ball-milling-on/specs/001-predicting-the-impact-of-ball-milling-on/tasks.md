# Tasks: Predicting the Impact of Ball Milling on Particle Size Distribution

**Input**: `spec.md`, `plan.md`, original research idea, existing artifacts, and any reviewer feedback.  
All paths are relative to the project root.

---

## Phase 0 – Project Setup & Basic Tooling  

| Goal | Run a minimal setup that creates the repository skeleton and verifies the development environment. |
|------|-----------------------------------------------------------------------------------------------|

- [ ] T001 [P] **Create setup script and manifest** – `scripts/setup_manifest.txt`, `scripts/setup.sh` – verifies both files exist and `setup.sh` creates the directories listed in the manifest.  
- [X] T002 [P] **Create `requirements.txt`** – pinned versions of the ten core dependencies. Verification: file exists and lists all required packages.  
- [ ] T002b [P] **Verify `requirements.txt` resolves without conflicts** – run `pip install --dry-run -r requirements.txt` and capture the output. Verification: log shows “Successfully installed …” with no conflict messages.  
- [ ] T003a [P] **Configure linting (flake8)** – create `.flake8` with `max-line-length = 88`. Verification: file exists and contains the setting.  
- [ ] T003b [P] **Configure formatting (black)** – add `pyproject.toml` with a valid black configuration. Verification: file exists and black can read it (`black --check .`).   <!-- FAILED-IN-EXECUTION: code/scripts/check_black.sh exit=127 -->
- [ ] T004 [P] **Initialize Git repository** – run `git init`, add a `.gitignore`, and make an initial commit. Verification: `.git` directory exists and `git log` shows the initial commit.   <!-- FAILED-IN-EXECUTION: code/scripts/init_git_repo.py exit=1 -->

---

## Phase 1 – Core Utilities  

| Goal | Provide deterministic randomness, logging, configuration, and schema validation utilities. |
|------|-------------------------------------------------------------------------------------------|

- [ ] T005 [P] **Seed‑management utility** – `src/utils/seed.py` with `set_seed(seed: int)`. Verification: calling the function sets `random`, `numpy`, and (if available) `torch` seeds.  
- [ ] T006 [P] **Logging infrastructure** – `src/utils/logger.py` exposing `get_logger(name)`. Verification: logger writes messages to stdout with configurable level.  
- [ ] T008 [P] **Custom exception definitions** – `src/utils/exceptions.py` defining `DataIngestionError`, `MissingTimestampError`, `GPRResourceLimitExceeded`, `InsufficientDataError`, `MissingDataError`. Verification: each class exists and can be raised.  
- [ ] T007a [P] **Dataset schema file** – `contracts/dataset.schema.yaml` matching the specification. Verification: file exists and validates against the JSON‑Schema draft‑07 definition.  
- [ ] T007b [P] **Schema‑validation helper** – `src/preprocess/validate_schema.py` with `validate(df)`. Verification: function raises `jsonschema.ValidationError` on mismatched rows.  
- [ ] T009 [P] **Configuration template** – `src/config/config.yaml` containing API endpoints, GPR resource limits, and OCR fallback flags. Verification: file exists with the required keys.  
- [ ] T009b [P] **Configuration loader** – `src/config/settings.py` exposing `load_config()`. Verification: function returns a dictionary with the expected keys.  

---

## Phase 2 – Data Aggregation & Pre‑processing (US‑1)  

| Goal | Acquire real ball‑milling experiments, stream them safely, and produce a validated, analysis‑ready dataset. |
|------|------------------------------------------------------------------------------------------------------------|

- [ ] T012 [P] **Materials Project fetcher** – `src/ingest/materials_project.py`. Verification: function returns a DataFrame with the required columns.  
- [ ] T013 [P] **NIST repository downloader** – `src/ingest/nist_repo.py`. Verification: parses NIST CSV/JSON into a DataFrame.  
- [ ] T013b [P] **arXiv PDF extractor** – `src/ingest/arxiv_extractor.py`. Verification: extracts tables from PDFs and returns a DataFrame.  
- [ ] T020 [P] **Streaming utility** – `src/ingest/streaming_utils.py` providing generator‑based chunked readers for HTTP/CSV/JSON/PDF. Verification: unit test confirms constant memory usage (< 2 GB) on a real subset.  
- [ ] T028a [P] **Integrate streaming with Materials Project & NIST fetchers** – modify `src/ingest/materials_project.py` and `src/ingest/nist_repo.py` to use `streaming_utils`. Verification: integration test shows identical merged output compared to a non‑streaming baseline.  
- [ ] T060 [P] **Validate NIST endpoint** – `src/ingest/nist_repo.py` must contain a reachable URL or raise a clear error. Verification: code contains a valid URL constant or raises `DataIngestionError` with explanatory message.  
- [ ] T061 [P] **“REAL DATA ONLY” comment blocks** – add the header comment to `src/ingest/materials_project.py`, `src/ingest/nist_repo.py`, `src/ingest/arxiv_extractor.py`. Verification: grep finds the comment in each file.  
- [ ] T023 [P] **Real‑data‑only audit** – static scan of `src/ingest/*.py` for any `generate_synthetic_*` or `mock_*` calls. Verification: script exits with code 0 when none are found.  
- [ ] T014c [P] **OCR fallback extraction** – `src/ingest/ocr_extractor.py`. Verification: attempts OCR, logs failures, and never drops the row.  
- [ ] T024 [P] **Streaming + OCR fallback integration** – ensure flagged PSD images are passed to the OCR module within the streaming pipeline. Verification: test `test_streaming_ocr_integration.py` confirms flagged entries are processed (or logged) correctly.  
- [ ] T014a [P] **Image‑detection for PSD curves** – `src/ingest/image_detection.py`. Verification: unit test `test_image_detection.py` correctly identifies image‑based PSD entries.  
- [ ] T014b [P] **Flag unstructured PSD entries** – `src/ingest/flagger.py` writes to `data/flagged_psd.log`. Verification: function creates/updates the log and returns the number of flagged rows.  
- [ ] T015a [P] **Merge & deduplicate** – `src/ingest/merge.py`. Verification: output parquet `data/raw/merged_dataset_temp.parquet` contains unique `experiment_id`s.  
- [ ] T016e [P] **Extract `process_duration` column** – `src/ingest/process_duration_extractor.py`. Verification: column present (may contain NaNs).  
- [ ] T067 [P] **Derive missing `process_duration`** – `src/preprocess/derive_duration.py`. Verification: missing values are filled from timestamps when possible; otherwise flagged as NaN.  
- [ ] T016a [P] **Multiple imputation** – `src/preprocess/impute.py` using `IterativeImputer` (targets excluded). Verification: imputed DataFrame has no NaNs in predictor columns.  
- [ ] T016b [P] **One‑hot encode `material_type`** – `src/preprocess/encode.py` with `drop='first'`. Verification: encoded columns appear, first category omitted.  
- [ ] T016c [P] **Standard‑scale numeric features** – `src/preprocess/scale.py`. Verification: `StandardScaler` defined for all numeric predictors.  
- [ ] T017a [P] **Save processed dataset** – `data/processed/ball_milling_dataset.parquet`. Verification: file exists, passes schema validation.  
- [ ] T044 [P] **Validate source metadata** – verify that `source_name` and `source_id` are non‑empty for every row after merging. Verification: script raises error if any record lacks these fields.  
- [ ] T017b [P] **Size‑gate enforcement** – abort if rows < 150, warn if 150 ≤ rows < 500. Verification: script raises `SystemExit` with the exact message or logs the warning.  
- [ ] T040 [P] **Compute checksums** – generate SHA‑256 checksums for raw and processed data files and write to `data/checksums.sha256`. Verification: checksum file exists and matches file contents.  
- [ ] T041 [P] **Update artifact hash map** – after each artifact creation, update `state/projects/PROJ-349-predicting-the-impact-of-ball-milling-on.yaml` `artifact_hashes` map with new hashes. Verification: yaml file reflects latest hashes.  
- [ ] T042 [P] **Train/test split** – split `data/processed/ball_milling_dataset.parquet` into `data/processed/train.parquet` and `data/processed/test.parquet` (e.g., 80/20 stratified by binned D50). Verification: both files exist and maintain schema.  
- [ ] T043 [P] **Held‑out test evaluation** – run the evaluation pipeline on `data/processed/test.parquet` and store metrics in `results/test_metrics.csv`. Verification: file exists with R², RMSE, MAE for each model.  

---

## Phase 3 – Predictive Modeling & Validation (US‑2)  

| Goal | Train GPR and Random Forest models with nested CV, provide a linear‑regression baseline, and perform statistical testing and power analysis. |
|------|---------------------------------------------------------------------------------------------------------------------------------------------------|

- [ ] T062 [P] **Dynamic bin calculation for stratification** – `src/model/bin_calculator.py` (`calculate_bins(df)`). Verification: unit test confirms correct bin count for various D50 cardinalities.  
- [ ] T063 [P] **Fallback to non‑stratified KFold** – same module adds `fallback_split(df)`. Verification: integration test triggers fallback when unique D50 ≤ 2 and logs the warning.  
- [ ] T028b [P] **Stratified nested CV implementation** – `src/model/nested_cv.py`. Verification: outer folds stratified by binned D50, inner folds 2‑fold; references FR‑009 for GPR fallback.  
- [ ] T029a [P] **GPR training with ARD kernel** – `src/model/train_gpr.py`. Verification: uses nested CV, respects resource limits, returns trained model objects.  
- [ ] T029b [P] **Random Forest training (≤ 1000 trees)** – `src/model/train_rf.py`. Verification: same CV scheme, tree limit enforced.  
- [ ] T068 [P] **Resource monitor for GPR** – `src/model/resource_monitor.py` (context manager). Verification: raises `GPRResourceLimitExceeded` when time > 30 min or RAM > 5 GB (simulated in test).  
- [ ] T071 [P] **Training CLI orchestrator** – `src/cli/train.py`. Verification: `python -m src.cli.train` runs full training pipeline.  
- [ ] T072 [P] **Fallback logic in training CLI** – catches `GPRResourceLimitExceeded` and runs only Random Forest, logging the event. Verification: test forces the exception and checks that RF runs.  
- [ ] T025 [P] **Linear‑regression baseline** – `src/model/baseline_lr.py`. Verification: baseline trained with same nested CV configuration.  
- [ ] T026 [P] **Metrics calculation** – `src/evaluate/metrics.py`. Verification: creates `results/metrics.csv` with R², RMSE, MAE for each model.  
- [ ] T026b [P] **Nested‑CV report** – `src/evaluate/nested_cv_report.py`. Verification: generates a summary CSV/markdown of outer‑fold performance.  
- [ ] T027 [P] **Nadeau & Bengio corrected resampled t‑test** – `src/evaluate/statistical_tests.py`. Verification: unit test `test_nadeau_bengio.py` passes.  
- [ ] T069 [P] **Validation of corrected t‑test** – `tests/unit/test_nadeau_bengio_validation.py`. Verification: compares against known reference values.  
- [ ] T030 [P] **A‑priori power analysis** – `src/evaluate/power_analysis.py` (function `a_priori_power(N)`). Verification: writes `results/power_analysis_result.txt` with the exact MDES string.  
- [ ] T070 [P] **Post‑hoc power analysis for the t‑test** – same module (function `posthoc_power(effect_size, N)`). Verification: writes `results/t_test_power.txt` with the exact power string.  

---

## Phase 4 – Interpretability & Visualization (US‑3)  

| Goal | Produce partial‑dependence plots and a ranked feature‑importance JSON for the trained models. |
|------|-----------------------------------------------------------------------------------------------|

- [ ] T033 [P] **Partial dependence plot generator** – `src/interpret/partial_dependence.py`. Verification: PNG files `results/partial_dependence_<feature>.png` created, total size ≤ 10 MB.  
- [ ] T034 [P] **Feature‑importance exporter** – `src/interpret/feature_importance.py`. Verification: `results/feature_importance.json` contains an ordered list of `{feature, importance}` objects.  
- [ ] T035 [P] **Interpretability CLI** – `src/cli/interpret.py`. Verification: running the CLI produces all PDPs and the JSON file.  

---

## Phase 5 – Reporting & Continuous Integration  

| Goal | Assemble all result artefacts, produce a concise report, and ensure reproducible CI execution. |
|------|-----------------------------------------------------------------------------------------------|

- [ ] T036 [X] **Assemble `results/` folder** – contains `metrics.csv`, `t_test_summary.txt`, all PDP PNGs (≤ 10 MB total), `feature_importance.json`, `associational_disclaimer.txt`, and power‑analysis files. Verification: script asserts size constraints and raises on violation.  
- [ ] T037 [P] **Generate final markdown report** – `src/utils/generate_report.py` writes `results/final_report.md` summarising metrics, power analysis, and disclaimer. Verification: report includes all required sections and links to artefacts.  
- [ ] T038 [P] **GitHub Actions CI workflow** – `.github/workflows/ci.yml` runs the full pipeline, enforces a 6‑hour timeout, and fails on any error. Verification: workflow file exists and contains the required `timeout-minutes` setting.  
- [ ] T039 [X] **Update quickstart documentation** – `quickstart.md` lists dry‑run commands and the full pipeline command. Verification: commands are present and correctly formatted.  

---

## Phase 6 – Final Verification & Dry‑Run Checks  

| Goal | Confirm that every pipeline stage can be executed in a dry‑run mode on CI without touching real data or exceeding resources. |
|------|------------------------------------------------------------------------------------------------------------------------------------|

- [ ] T053 [X] **Synthetic‑fallback audit script** – `scripts/check_synthetic_fallbacks.py`. Verification: script exits with code 0 when no synthetic‑fallback patterns are found.  
- [ ] T054 [X] **Documentation of streaming & minimum‑size policy** – sections added to `README.md` and `quickstart.md`. Verification: headings and content are present.  
- [ ] T055 [X] **Data‑flow dry‑run** – `python src/cli/ingest.py --dry-run`. Verification: completes without error and logs each step.  
- [ ] T056 [P] **Model‑pipeline dry‑run** – `python src/cli/train.py --dry-run --input data/processed/small_sample.parquet`. Verification: completes, logs training flow, and shows any fallback events.  
- [ ] T057 [X] **Interpretability dry‑run** – `python src/cli/interpret.py --dry-run --model results/model_rf.pkl`. Verification: completes and logs plot generation.  
- [ ] T058 [X] **Documentation of dry‑run commands** – `README.md` & `quickstart.md` include the three dry‑run commands above. Verification: commands are listed verbatim.  

---  

*All tasks above are expressed as checklist items with unique IDs, required file paths, and explicit verification steps. Unchecked items indicate work that still needs to be completed or re‑opened due to prior verification failures.*  
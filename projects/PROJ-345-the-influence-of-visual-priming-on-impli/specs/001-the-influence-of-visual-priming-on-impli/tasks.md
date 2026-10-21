---
description: "Task list for feature implementation – The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli"
---

# Tasks: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

**Input**: Design documents from `/specs/001-the-influence-of-visual-priming-on-impli/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

## Phase 1 – Setup and first end‑to‑end analysis  

Goal: Initialise the project, install dependencies, and verify that the logging subsystem creates a real log file.

- [ ] **T001** [P] Create the core data directories (`data/raw`, `data/processed`, `data/primes`, `data/targets`).  
  - **Verification**: `ls data/raw data/processed data/primes data/targets` lists each directory.

- [ ] **T002** [P] Create the code, tests, and state directories (`code/`, `tests/`, `state/`).  
  - **Verification**: `ls code tests state` lists the expected sub‑folders.

- [ ] **T003** [P] Write `requirements.txt` with the pinned package list from the plan and create a virtual environment that installs those requirements.  
  - **Verification**: `cat requirements.txt` contains the exact list; `pip list` shows the pinned versions; `python -c "import pandas"` runs without error.

- [ ] **T004** [P] Configure linting (ruff), formatting (black), and pre‑commit hooks.  
  - **Verification**: `pre‑commit run --all-files` completes with zero failures.

- [ ] **T005** [P] Populate `code/config.py` with paths for all data folders, a random seed, and `PRIMARY_DATASET_URL` (read from `data/verified_sources.json`).  
  - **Verification**: `python -c "from code.config import Config; assert Config.PRIMARY_DATASET_URL"` succeeds.

- [ ] **T006** [P] Implement logging in `code/main.py` using the required format `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`, level INFO, with handlers for `stdout` and `code/logs/pipeline.log`. Execute the script once with a dry‑run flag to generate an initial log entry.  
  - **Verification**: After `python -m code.main --dry-run`, `code/logs/pipeline.log` exists and contains at least one line matching the log‑format regex.

- [ ] **T041** [P] Verify that the logging run from T006 created `code/logs/pipeline.log` and that the file contains the expected header line.  
  - **Verification**: `test -f code/logs/pipeline.log && grep -E "^[0-9]{4}-[0-9]{2}-[0-9]{2} .+ - INFO -" code/logs/pipeline.log` succeeds.

- [ ] **T007** [P] Initialise project state by creating `state/artifact_hashes.json` (empty JSON object) and a minimal `state/project_state.yaml`.  
  - **Verification**: Both files exist and are valid JSON/YAML.

- [ ] **T008** [P] Define base data models (`Trial`, `Participant`, `Stimulus`) in `code/data/models.py`.  
  - **Verification**: Importing each class and instantiating with dummy data raises no exception.

- [ ] **T009** [P] Verify that the ingestion URL in `data/verified_sources.json` is present and matches the URL used in `code/config.py`. Abort with a clear error if the URL is missing or mismatched.  
  - **Verification**: Running `python -c "from code.verified_sources import get_primary_url; from code.config import Config; assert get_primary_url() == Config.PRIMARY_DATASET_URL"` succeeds; a mismatched URL raises `ValueError`.

## Phase 2 – Data ingestion, preprocessing & linkage  

Goal: Download the IAT dataset, validate its schema, extract stimulus metadata, and produce a fully linked trial file.

- [ ] **T010** [P] Load the verified sources (`data/verified_sources.json`) and expose the primary URL via `code/verified_sources.py`.  
  - **Verification**: Importing the module returns the exact URL string.

- [ ] **T011** [P] Download the dataset from `Config.PRIMARY_DATASET_URL` into `data/raw/iat.parquet`; compute its SHA‑256 checksum and record the hash in `state/artifact_hashes.json`.  
  - **Verification**: `data/raw/iat.parquet` exists; `state/artifact_hashes.json` contains an entry with key `"data/raw/iat.parquet"` and a 64‑character hex string.

- [ ] **T012** [P] Perform core‑column validation on the downloaded file (must contain `response_time`, `participant_id`, `stimulus_id`). If any are missing, write `state/linkage_status.json` with `"status": "HALT"` and abort further processing.  
  - **Verification**: When a required column is absent, the JSON file exists, matches `contracts/linkage_status.schema.yaml`, and the pipeline stops.

- [ ] **T013** [P] Extract stimulus metadata (image paths or word tokens) and write `data/processed/metadata_mapping.csv` with columns `trial_id,stimulus_id,type,file_path_or_word,prime_or_target`.  
  - **Verification**: The CSV file contains the expected header row and at least one record per trial.

- [ ] **T014** [P] Detect missing image files, count them, and write `data/processed/missing_images.json` with fields `missing_image_trials` and `missing_image_percentage`.  
  - **Verification**: The JSON file validates against a simple schema and the counts reflect the actual filesystem state.

- [ ] **T015** [P] Apply halt/warn logic for missing images: if > 10 % of trials lack an image, write `state/linkage_status.json` with `"status": "HALT"` and an explanatory message; if ≤ 10 % missing, write `"status": "WARN"` and continue.  
  - **Verification**: The status field reflects the computed percentage and the appropriate message is logged.

- [ ] **T016** [P] Compute the overall linkage metric (linked trials / total trials) and write `data/processed/ingest_metrics.json` (must conform to `contracts/ingest_metrics.schema.yaml`).  
  - **Verification**: The JSON file is non‑empty, all required fields are present, and `linkage_percentage` ≥ `config.LINKAGE_THRESHOLD` when status is `PASS`.

- [ ] **T017** [P] Merge the raw trial data with `metadata_mapping.csv` to create `data/processed/linked_trials.csv`. The file must contain the columns required by `contracts/dataset.schema.yaml` (prime_valence and stimulus_ambiguity may be null at this stage).  
  - **Verification**: The CSV exists, contains ≥ 90 % of the raw trials, and passes schema validation via `pytest -m contract`.

- [ ] **T018** [P] Derive prime‑valence scores for each stimulus using the CPU‑only emotion classifier; write `data/processed/valence_scores.csv` with values in the range [-1, 1].  
  - **Verification**: All rows have a numeric `prime_valence` within the allowed interval; the file validates against a simple schema.

- [ ] **T019** [P] Derive stimulus‑ambiguity scores (WordNet sense‑count for words or texture variance for images) and write `data/processed/ambiguity_scores.csv` with values in [0, 1].  
  - **Verification**: All rows contain a numeric `stimulus_ambiguity` within the allowed interval; schema validation passes.

- [ ] **T020** [P] Merge `valence_scores.csv` and `ambiguity_scores.csv` with `metadata_mapping.csv` (and with `linked_trials.csv`) to produce an enriched `data/processed/linked_trials.csv` that now includes non‑null `prime_valence` and `stimulus_ambiguity` columns.  
  - **Verification**: The updated CSV has no missing values in the two derived columns and validates against `contracts/dataset.schema.yaml`.

- [ ] **T039** [P] Validate that the derived columns `prime_valence` and `stimulus_ambiguity` are present and contain no nulls in the enriched `linked_trials.csv`. Abort with `"status": "HALT"` in `state/linkage_status.json` if any nulls are found.  
  - **Verification**: The task reads the enriched CSV, checks both columns for nulls, writes a pass/fail status, and logs the result.

## Phase 3 – Statistical modelling, diagnostics & validation  

Goal: Check multicollinearity, validate derived scores, ensure sufficient power, run confound diagnostics, and fit the final LME model.

- [ ] **T021** [P] Compute Variance Inflation Factors for all fixed‑effect predictors using the design matrix from `linked_trials.csv` and write `state/vif_flag.json`. If any VIF > 5.0, set `"flagged": true` and `"claim_suppressed": true`.  
  - **Verification**: The JSON file contains the VIF values, the boolean flags, and matches `state/vif_flag.json` schema.

- [ ] **T022** [P] Validate the derived `prime_valence` and `stimulus_ambiguity` scores against external benchmarks (NRC VAD for words, FER‑2013 for images). Store Pearson r, 95 % CI, and a pass/fail flag in `state/score_validation.json`.  
  - **Verification**: The file conforms to `state/score_validation.json` schema and `validation_passed` is true only when both correlations ≥ 0.6.

- [ ] **T023** [P] Perform an a‑priori power analysis (target effect size f = 0.15, α = 0.05, power = 0.80) and write `state/power_check.json`. Halt the pipeline with `"status": "HALT"` in `state/linkage_status.json` if `observed_n` < `required_n`.  
  - **Verification**: The JSON contains `required_n`, `observed_n`, and a boolean `power_achieved`; the halt logic works as described.

- [ ] **T024** [P] Run confound diagnostics (trial‑order autocorrelation, stimulus repetition rate, ICC). Write `state/confound_check.json`; if any severe confound is detected, set `"confound_severe": true` and halt.  
  - **Verification**: The JSON matches its schema and the halt condition triggers when appropriate.

- [ ] **T025** [P] Fit a linear mixed‑effects model with fixed effects `prime_valence`, `stimulus_ambiguity`, and their interaction; random intercept **and** random slope for `prime_valence` per `participant_id`. Use robust SEs and retry up to three optimizers (`lbfgs`, `bfgs`, `powell`). Record attempts and outcomes in `state/model_convergence_metrics.json`. On success, write `state/model_results.json` conforming to `contracts/model_results.schema.yaml`.  
  - **Verification**: `model_convergence_metrics.json` contains `total_attempts`, `successful_runs`, `failed_runs`, and the optimizer list; `model_results.json` includes all required fields.

- [ ] **T026** [P] Apply Benjamini‑Hochberg FDR correction to all raw p‑values and store the corrected values (`p_fdr`) alongside `p_raw` in `state/model_results.json`.  
  - **Verification**: Each fixed‑effect entry now has both `p_raw` and `p_fdr` fields.

- [ ] **T027** [P] Append the associational framing `caution_note` and the limitation `limitation_note` (as required by FR‑003) to `state/model_results.json`.  
  - **Verification**: The two note fields contain the exact strings stipulated in the specification.

- [ ] **T028** [P] Compute bootstrap effect‑size estimates (Cohen’s d and partial η²) with ≥ 1 000 resamples; add the estimates and 95 % CIs to `state/model_results.json` under `effect_sizes`.  
  - **Verification**: Both effect‑size objects contain `estimate`, `ci_lower`, and `ci_upper` and are numeric.

## Phase 4 – Reporting & visualization  

Goal: Produce all required figures, tables, sensitivity analysis, and a final PDF report that reflects either a successful analysis or a data‑gap narrative.

- [ ] **T029** [P] Generate an interaction plot (`reports/interaction_plot.png`) that visualises response‑time differences across prime‑valence conditions.  
  - **Verification**: The PNG file exists and its dimensions are ≥ 600 × 400 px.

- [ ] **T030** [P] Render a coefficient table as an image (`reports/coefficient_table.png`) containing fixed‑effect estimates, SEs, raw and FDR‑corrected p‑values.  
  - **Verification**: The PNG file exists and the text is readable (checked via OCR‑free sanity test).

- [ ] **T031** [P] Perform an α‑sweep sensitivity analysis (α = 0.01, 0.05, 0.10) on the FDR‑corrected results and write `reports/sensitivity_analysis.csv`.  
  - **Verification**: The CSV contains columns `alpha_level, significant_tests, total_tests, conclusion` and three rows.

- [ ] **T032** [P] Assemble all artifacts into `reports/final_report.pdf`. The PDF must contain (a) the interaction plot, (b) the coefficient table image, (c) the sensitivity‑analysis summary, (d) the exact `caution_note` and `limitation_note`, (e) a VIF‑suppression statement when applicable, and (f) an ambiguity‑status paragraph. If `state/linkage_status.json` is `HALT`, the PDF instead contains a data‑gap narrative explaining the reason for halting.  
  - **Verification**: The PDF exists; a text search finds the strings “Interaction Plot”, “Coefficient Table”, “Sensitivity Analysis”, and the two note texts. Schema validation of accompanying JSON metadata passes.

## Phase 5 – Cross‑cutting checks, documentation & end‑to‑end run  

- [ ] **T033** [P] Run contract verification (`pytest -m contract`) to ensure every JSON/YAML artifact conforms to its schema.  
  - **Verification**: Test suite exits with 0 failures.

- [ ] **T034** [P] Update `quickstart.md` with clear installation steps, the command to run the full pipeline on a small subset, and expected artefact locations.  
  - **Verification**: The document contains a runnable example that, when executed on a fresh clone, reproduces the end‑to‑end analysis on ≤ 100 trials.

- [ ] **T035** [P] Execute the full pipeline end‑to‑end on a real subset (≈ 100 trials) and confirm that `reports/final_report.pdf` is produced and passes the checks in T032.  
  - **Verification**: The pipeline completes within the CI time limit, the PDF exists, and all content checks succeed.

- [ ] **T036** [P] Perform a PII scan on all processed outputs using `presidio-analyzer`; write `reports/pii_scan.json` and verify that the `"leaks"` list is empty.  
  - **Verification**: The JSON file matches `contracts/pii_scan.schema.yaml` (if defined) and contains `"leaks": []`.

- [ ] **T037** [P] Add unit tests for edge‑case scenarios identified in the specification (high collinearity, ≤ 10 % missing images, model‑convergence failures). Place them under `tests/unit/`.  
  - **Verification**: `pytest tests/unit/` runs with 0 failures.

- [ ] **T038** [P] Document the streaming helper (`code/data/streaming.py`) that can process datasets > 7 GB in a memory‑efficient way; include a sanity‑check script that creates a synthetic 7.5 GB Parquet file, streams it, and logs memory usage.  
  - **Verification**: The helper runs without exceeding 2 GB RAM (checked via `psutil`), and the log confirms successful streaming.

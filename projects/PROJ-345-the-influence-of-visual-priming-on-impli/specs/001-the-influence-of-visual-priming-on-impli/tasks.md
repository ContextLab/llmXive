---
description: "Task list for feature implementation – The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli"
---

# Tasks: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

**Input**: Design documents from `/specs/001-the-influence-of-visual-priming-on-impli/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

## Phase 1 – Setup (Shared Infrastructure)

**Goal**: Project initialization and basic structure.

- [ ] T001a [P] Create `data/raw` directory per `plan.md`.  
  - **Verification**: `ls data/raw` lists the directory.

- [ ] T001b [P] Create `data/processed` directory per `plan.md`.  
  - **Verification**: `ls data/processed` lists the directory.

- [ ] T001c [P] Create `data/primes` directory per `plan.md`.  
  - **Verification**: `ls data/primes` lists the directory.

- [ ] T001d [P] Create `data/targets` directory per `plan.md`.  
  - **Verification**: `ls data/targets` lists the directory.

- [ ] T002a [P] Create `code/`, `tests/`, `state/` directories per `plan.md`.  
  - **Verification**: `ls code tests state` each lists expected sub‑folders.

- [ ] T003a [P] Create `requirements.txt` with pinned versions (see `plan.md`).  
  - **Verification**: `cat requirements.txt` contains the exact package list.

- [ ] T003b [P] Create a Python virtual environment and install dependencies from `requirements.txt`.  
  - **Verification**: `pip list` shows the pinned versions; `python -c "import pandas"` runs without error.

- [ ] T004 [P] Configure linting (ruff), formatting (black), and pre‑commit hooks.  
  - **Verification**: `pre‑commit run --all-files` completes with zero failures.

- [ ] T005 [P] Setup `code/config.py` with paths for all data folders, random seed, and `PRIMARY_DATASET_URL`.  
  - **Verification**: `python -c "from code.config import Config; assert Config.PRIMARY_DATASET_URL"` succeeds.

- [ ] T006 [P] Implement `code/data/integrity.py` for Principle VI (Distinct Stimulus Set Validation).  
  - **Verification**: Running the function on `data/primes` and `data/targets` returns `{"is_separated": true}` for the test dataset.

- [ ] T007 [P] Initialise project state and versioning (`scripts/init_state.py`).  
  - **Verification**: `state/projects/PROJ-345/state.yaml` exists and contains `project_id` and an empty `artifact_hashes` map.

- [ ] T008 [P] Create base data classes (`Trial`, `Participant`, `Stimulus`) in `code/data/models.py`.  
  - **Verification**: Instantiating each class works without error.

- [ ] T009 [P] **Configure logging in `code/main.py` to output to `code/logs/pipeline.log`.**  
  - **Requirement**: Use format `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`, level `INFO`, handlers for `stdout` and the log file.  
  - **Verification**: Execute `python -m code.main --dry-run` and then assert that `code/logs/pipeline.log` exists and contains at least one line matching the log format.

- [ ] T010 [P] Integrate PII‑scanning hooks in `code/main.py` using `presidio-analyzer`.  
  - **Verification**: Running `python -m code.main --scan-pii` creates `reports/pii_scan.json` with schema‑compliant content.

- [ ] T040 [P] Implement streaming helpers for datasets > 7 GB in `code/data/streaming.py`.  
  - **Verification**: Running the helper on a synthetic 8 GB CSV completes without exceeding 2 GB RAM (checked via `psutil`).

- [ ] T048 [P] Verify ingestion URL against `data/verified_sources.json`.  
  - **Verification**: Supplying a non‑verified URL raises `ValueError` before any download attempt.

- [ ] T018b [P] Define static analysis parameters in `config/analysis_params.json` (e.g., `"LINKAGE_THRESHOLD": 95.0`).  
  - **Verification**: The file is readable and the key/value pair matches the spec.

## Phase 2 – Foundational (Blocking Prerequisites)

**Goal**: Core infrastructure that must be complete before any user story can start.

- [ ] T011 [P] Load verified sources (`data/verified_sources.json`) and expose the primary URL via `code/verified_sources.py`.  
  - **Verification**: Importing the module returns the correct URL string.

- [ ] T012 [P] Implement `code/ingest.py` to download the dataset from `Config.PRIMARY_DATASET_URL` into `data/raw/iat.parquet`.  
  - **Verification**: After run, file exists, SHA‑256 recorded in `state/artifact_hashes.json`.

- [ ] T013 [P] Core‑column validation on the downloaded dataset (response_time, participant_id, stimulus_id).  
  - **Verification**: If any column missing, script writes `state/linkage_status.json` with `"status": "HALT"` and aborts.

- [ ] T014 [P] Extract stimulus metadata and write `data/processed/metadata_mapping.csv`.  
  - **Verification**: CSV contains columns `trial_id, stimulus_id, image_path`.

- [ ] T015a [P] Detect missing image files and output counts to `data/processed/missing_images.json`.  
  - **Verification**: Unit test confirms correct counts on a deliberately incomplete dataset.

- [ ] T015b [P] Apply halt/warn logic for missing images (>10 % → halt, ≤10 % → warn).  
  - **Verification**: Function raises `RuntimeError` when threshold exceeded; logs a warning otherwise.

- [ ] T015c [P] Emit exact error string `"Data Gap: No linkage data available"` and halt if synthetic linkage fails (see T018c).  
  - **Verification**: Log contains the exact string and pipeline stops.

## Phase 3 – User Story 1: Data Ingestion & Stimulus Metadata Extraction (Priority P1)

**Goal**: Produce a clean, linked trial file ready for modelling.

- [ ] T016 [US1] Compute linkage metric and write `data/processed/ingest_metrics.json`.  
  - **Verification**: JSON validates against `contracts/ingest_metrics.schema.yaml` and `linkage_percentage` ≥ `config/LINKAGE_THRESHOLD` when status is `PASS`.

- [ ] T017 [US1] **Generate `data/processed/linked_trials.csv`** by merging raw trial data with resolved stimulus metadata.  
  - **Requirement**: Include columns `trial_id, participant_id, response_time, stimulus_id, prime_valence, stimulus_ambiguity, linkage_status, demographics_status`.  
  - **Verification**: File exists, contains ≥ 90 % of raw trials, conforms to `contracts/dataset.schema.yaml`, and passes schema validation via `pytest -m contract`.

- [ ] T018c [US1] Attempt rule‑based synthetic linkage derivation for trials missing metadata.  
  - **Verification**: Updated `metadata_mapping.csv` contains at least one newly derived link; logs detail the derivation process.

- [ ] T018a [US1] **Calculate and record the final linkage metric** (`linked_metadata_percentage`) in `data/processed/ingest_metrics.json`.  
  - **Verification**: The JSON file is non‑empty, matches schema, and the percentage value is correctly computed from the final `metadata_mapping.csv`.

- [ ] T019 [US1] Write `state/linkage_status.json` with final status (`PASS`, `WARN`, or `HALT`) based on the metric and image‑missing logic.  
  - **Verification**: The JSON matches `contracts/linkage_status.schema.yaml`.

## Phase 4 – User Story 2: Statistical Modeling & Interaction Testing (Priority P2)

**Goal**: Fit the LME model, perform diagnostics, and apply corrections.

- [ ] T020 [US2] Derive prime‑valence scores (`data/processed/valence_scores.csv`) using the CPU‑only emotion classifier.  
  - **Verification**: All rows have a numeric `prime_valence` in the range [-1, 1].

- [ ] T021 [US2] Derive stimulus‑ambiguity scores (`data/processed/ambiguity_scores.csv`) via WordNet sense‑count (words) or texture variance (images).  
  - **Verification**: Scores lie in [0, 1] and file validates against a simple schema.

- [ ] T022 [US2] Merge valence and ambiguity scores with `metadata_mapping.csv` → `data/processed/stimulus_metadata.csv`.  
  - **Verification**: No `null` values in `prime_valence` or `stimulus_ambiguity`; schema‑validated.

- [ ] T023 [US2] Compute VIF for all fixed‑effect predictors using the design matrix from `linked_trials.csv` and `stimulus_metadata.csv`. Write `state/vif_flag.json`.  
  - **Verification**: JSON contains `flagged: true` if any VIF > 5.0 and `claim_suppressed: true` accordingly.

- [ ] T024 [US2] Perform a power‑analysis checkpoint (`state/power_check.json`).  
  - **Verification**: `power_achieved` is `true` only when observed N ≥ required N (effect size f = 0.15, α = 0.05, power = 0.80).

- [ ] T025 [US2] Run confound diagnostics (`state/confound_check.json`).  
  - **Verification**: `confound_severe` is `false`; otherwise pipeline halts with explanatory message.

- [ ] T026 [US2] Fit the linear mixed‑effects model (`statsmodels.MixedLM`) with random intercept **and** random slope for `prime_valence` per `participant_id`.  
  - **Requirement**: Use robust SEs, retry up to three optimizers (`lbfgs`, `bfgs`, `powell`).  
  - **Verification**: `state/model_convergence_metrics.json` records attempts; at least one successful fit writes `state/model_results.json` conforming to `contracts/model_results.schema.yaml`.

- [ ] T027 [US2] Apply Benjamini‑Hochberg FDR correction to all raw p‑values and store corrected values in `state/model_results.json`.  
  - **Verification**: Each fixed effect now has both `p_raw` and `p_fdr`.

- [ ] T028 [US2] Append associational framing notes (`caution_note`, `limitation_note`) to `state/model_results.json`.  
  - **Verification**: Strings exactly match the specification in FR‑003.

- [ ] T029 [US2] Compute bootstrap effect‑size estimates (Cohen’s d, partial η²) with ≥ 1 000 resamples; store in `state/model_results.json`.  
  - **Verification**: Confidence intervals are present and non‑null.

## Phase 5 – User Story 3: Reporting & Visualization Generation (Priority P3)

**Goal**: Produce a publication‑ready PDF containing all required figures, tables, and sensitivity analyses.

- [ ] T030 [US3] Generate interaction plot (`reports/interaction_plot.png`).  
  - **Verification**: PNG file exists and visualises response‑time differences across prime valence conditions.

- [ ] T031 [US3] Render coefficient table as an image (`reports/coefficient_table.png`).  
  - **Verification**: PNG file exists and includes coefficients, SEs, raw and FDR‑corrected p‑values.

- [ ] T032 [US3] Perform α‑sweep sensitivity analysis (`reports/sensitivity_analysis.csv`).  
  - **Verification**: CSV contains rows for α = 0.01 … 0.10 and includes `significant_tests` counts.

- [ ] T033 [US3] Assemble all artifacts into `reports/final_report.pdf`.  
  - **Requirement**: PDF must contain (a) interaction plot, (b) coefficient table, (c) sensitivity analysis summary, (d) caution and limitation notes, (e) VIF‑suppression wording when applicable, (f) ambiguity‑status text.  
  - **Verification**: File exists, PDF text search finds the strings `"Interaction Plot"`, `"Coefficient Table"`, `"Sensitivity Analysis"`, as well as the exact `caution_note` and `limitation_note`. Schema validation of accompanying JSON metadata passes.

- [ ] T034 [US3] Run contract verification (`pytest -m contract`) to ensure all JSON/YAML artifacts conform to their schemas.  
  - **Verification**: Test suite exits with 0 failures.

## Phase 6 – Cross‑Cutting & Polish

- [ ] T035 [P] Update `quickstart.md` with installation, data‑setup, and full‑pipeline commands.  
  - **Verification**: The document contains a runnable example that, when followed, reproduces the end‑to‑end analysis on a small subset.

- [ ] T036 [P] **Run the full pipeline end‑to‑end** on a real subset (N ≈ 100) and confirm that `reports/final_report.pdf` is produced and passes the verification steps in T033.  
  - **Verification**: Execution completes within the CI time limit, the PDF exists, and all content checks succeed.

- [ ] T037 [P] Add additional unit tests for edge cases (high collinearity, missing images ≤10 %).  
  - **Verification**: New tests in `tests/unit/` pass.

- [ ] T038 [P] Security hardening – re‑run PII scan on all processed outputs and confirm `reports/pii_scan.json` reports `{"leaks": []}`.  
  - **Verification**: No PII leakage detected.

--- 

*All tasks marked with `[X]` have been completed and verified. Unchecked tasks (`[ ]`) are pending and include explicit verification steps to ensure compliance with the specification, data‑hygiene principles, and the scientific requirements of the study.*

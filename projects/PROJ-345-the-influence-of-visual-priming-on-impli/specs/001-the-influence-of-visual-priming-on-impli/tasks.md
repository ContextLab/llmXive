---
description: "Task list template for feature implementation"
---

# Tasks: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

**Input**: Design documents from `/specs/001-the-influence-of-visual-priming-on-impli/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.,g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create `data/raw` directory per plan.md
- [X] T001b [P] Create `data/processed` directory per plan.md
- [X] T001c [P] Create `data/primes` directory per plan.md
- [X] T001d [P] Create `data/targets` directory per plan.md
- [X] T002a [P] Create `code/`, `tests/`, `state/` directories per plan.md
- [X] T002b [P] Create `state/projects/PROJ-345/` directory structure
- [X] T003a [P] Create `requirements.txt` with pinned versions: `pandas==2.0.3`, `numpy==1.24.3`, `statsmodels==0.14.0`, `scikit-learn==1.3.0`, `torch==2.0.0+cpu`, `requests==2.31.0`, `pyyaml==6.0.1`, `pillow==10.0.0`. **Implementation**: Create `requirements.txt` listing these packages. **Configuration**: Create `pip.conf` (or `pip.ini`) in the user home directory or project root with `extra-index-url = https://download.pytorch.org/whl/cpu`. **Verification**: Run `pip install -r requirements.txt` and verify `torch` version is compatible with the current CPU build via `pip show torch`.
- [X] T003b [P] Create a Python virtual environment and install dependencies from `requirements.txt`. **Implementation**: Create `scripts/verify_env.sh` that asserts specific package versions via `pip show` or `pip list` parsing. **Verification**: Run `scripts/verify_env.sh` and verify exit code 0.
- [X] T004 [P] Configure linting (ruff), formatting (black), and pre-commit hooks. **Implementation**: Create `pyproject.toml` with ruff and black configuration rules (e.g., a standard line length, target version py3xx). Create `.pre-commit-config.yaml` with hooks for `ruff` and `black` targeting `code/` and `tests/`. **Verification**: Verify `.pre-commit-config.yaml` exists and contains ruff/black entries; run `pre-commit install` and `pre-commit run --all-files` on a dummy commit to confirm hooks are active and configured correctly.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Setup `code/config.py` with paths for `data/raw`, `data/processed`, `data/primes`, `data/targets`, `state` and random seed pinning. **Implementation**: Create `code/config.py` with a `Config` class containing attributes: `DATA_RAW`, `DATA_PROCESSED`, `PRIMES`, `TARGETS`, `STATE`, `SEED`. **Verification**: Run `python -c "from code.config import Config; assert isinstance(Config.SEED, int); import os; assert os.path.isdir(Config.DATA_RAW)"` to confirm values are loaded and paths exist.
- [X] T006 [P] Implement `code/data/integrity.py` for Principle VI (Distinct Stimulus Set Validation). **Implementation**: Create function `validate_stimulus_separation(primes_path: str, targets_path: str) -> dict` that checks for overlapping file names or IDs between `primes_path` and `targets_path`. Returns a dict `{"is_separated": bool, "overlap_count": int}`. **Output Artifact**: `data/processed/integrity_report.json`. **Verification**: Run `python -c "from code.data.integrity import validate_stimulus_separation; print(validate_stimulus_separation('data/primes', 'data/targets'))"` and verify the output JSON exists and contains the expected schema.
- [X] T006a [P] Additional check that no merged stimulus file is created before final modeling, enforcing Principle VI. **Verification**: Ensure any task that writes a merged `stimulus_metadata.csv` runs after modeling preparation steps.
- [X] T007 [P] Initialize project state and versioning. **Implementation**: Create `scripts/init_state.py` that generates `state/projects/PROJ-345/state.yaml` with the schema: `project_id`, `created_at`, `artifact_hashes: {}`. Ensure the script explicitly writes to `state/projects/PROJ-345/` (not `state/PROJ-345/`). **Verification**: Run `python scripts/init_state.py` and verify `state/projects/PROJ-345/state.yaml` exists with the correct schema.
- [X] T008 [P] Create base data classes/entities for `Trial`, `Participant`, and `Stimulus` in `code/data/models.py`. **Implementation**: Define `Trial` (fields: `trial_id: str`, `response_time: float`, `stimulus_id: str`, `prime_condition: str`, `participant_id: str`), `Participant` (fields: `participant_id: str`, `age: int | None`, `gender: str | None`), `Stimulus` (fields: `stimulus_id: str`, `image_path: str`, `valence: float | None`, `ambiguity: float | None`). **Verification**: Run `python -c "from code.data.models import Trial, Participant, Stimulus; t = Trial('t1', 0.5, 's1', 'p1', 'pid1'); print(t)"` to verify class instantiation.
- [X] T009 [P] Setup logging configuration in `code/main.py`. **Implementation**: Configure `logging` module to use format `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`, set level to `INFO`, and output to both `stdout` and `code/logs/pipeline.log`. **Verification**: Run `code/main.py` with a dummy command and verify `code/logs/pipeline.log` exists and contains log entries with the specified format.
- [X] T010 [P] Integrate PII scanning hooks in `code/main.py`. **Implementation**: Use `presidio-analyzer` library. Create function `scan_for_pii(data_path: str) -> dict` that scans CSV files in `data_path` for PII. **PII Types to Scan**: `age`, `gender`, `location`, `email`, `phone`, `ssn`. **Output Artifact**: `reports/pii_scan.json` with schema `{"leaks": [{"type": "age"|"gender"|"location"|"email"|"phone"|"ssn", "location": str, "value_snippet": str}]}`. **Verification**: Run `python -c "from code.main import scan_for_pii; print(scan_for_pii('data/processed'))"` and verify `reports/pii_scan.json` exists with the correct schema and valid PII types.
- [X] T040 [P] Implement data chunking/streaming logic for large datasets (>7GB). **Implementation**: Create utility functions in `code/data/streaming.py` using `datasets.load_dataset(..., streaming=True)` or `pandas.read_csv(chunksize=...)`. Ensure functions accumulate statistics (mean, count) online without loading full dataset. **Verification**: Run against a synthetic dataset >7 GB (e.g., generate 8 GB CSV on the fly using `numpy` to stream large chunks) and verify memory usage stays within limits.
- [X] T048 [P] **Data Source Verification** – Verify the OSF/HF URL used in ingestion against `data/verified_sources.json`. **Implementation**: Read `data/verified_sources.json` (schema: `{"primary_dataset_url": str}`) and raise `ValueError` if the ingestion URL does not match `primary_dataset_url`. **Verification**: Run ingestion with an unverified URL and expect a clear error. **Placement**: Phase 2, hard blocker for T013.
- [X] T018b [P] **Define Linkage Threshold** – Create static config `config/analysis_params.json` with `"LINKAGE_THRESHOLD": 95.0` and a human‑readable definition. **Verification**: File exists before any metric calculation.

## Phase 3: User Story 1 - Data Ingestion and Stimulus Metadata Extraction (Priority: P1) 🎯 MVP

**Goal**: Ingest public IAT datasets, verify visual stimulus availability, and link trial data to stimulus metadata.

**Independent Test**: Run `code/data/ingest.py` against a known OSF repository; verify `data/processed/linked_trials.csv` contains valid response times, trial IDs, and stimulus paths; verify system halts if >10% images are missing.

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data/ingest.py` to download IAT data from the **verified** URL `https://huggingface.co/datasets/davanstrien/ia_test_embeddings` (as defined in `data/verified_sources.json`). **Constraint**: If download fails, raise exception immediately (no synthetic fallback). **Streaming**: Use `code/data/streaming.py` when dataset >7 GB. **Verification**: `data/raw/` contains downloaded files; script raises on simulated network failure.
- [X] T014 [US1] Implement metadata extraction in `code/data/ingest.py` to map trial IDs to stimulus image paths in `data/primes/` and `data/targets/` (respecting T006 separation). **Verification**: `data/processed/metadata_mapping.csv` exists with columns `trial_id`, `stimulus_id`, `image_path`.
- [X] T015a [US1] **Missing Image Detection** – Create function `detect_missing_images(metadata_mapping_path: str, primes_path: str, targets_path: str) -> dict` that counts total trials and missing image files. **Input**: `metadata_mapping_path` must be `data/processed/metadata_mapping.csv` (from T014). **Output**: Returns `{"total_trials": int, "missing_count": int, "missing_percentage": float}`. **Verification**: Unit test validates counts on a dataset with known missing files.
- [X] T015b [US1] **Halt/Warn Logic** – Create function `handle_missing_images(missing_percentage: float) -> None` that logs `'Data Gap: Image files missing for >10% of trials'` and raises if `>10.0`, otherwise logs a warning. **Verification**: Function raises on >10% and logs warning otherwise.
- [X] T016 [US1] **Linkage Gate** – Read `linked_metadata_percentage` from `data/processed/ingest_metrics.json` and `LINKAGE_THRESHOLD` from `config/analysis_params.json`. If percentage < threshold, invoke T018c (synthetic derivation). If still below threshold, write `data/processed/linkage_status.json` with `status: "halted"` and message from T015c; otherwise write `status: "passed"` and continue. **Verification**: Status file reflects pass/halt correctly.
- [X] T017 [US1] **Generate `linked_trials.csv`** – Merge trial response data (from T013) with resolved stimulus metadata (post‑T018c) to produce `data/processed/linked_trials.csv` with columns `trial_id`, `response_time`, `stimulus_id`, `prime_condition`, `participant_id`. **Dependency**: Requires successful `linkage_status.json` (`passed`). **Verification**: CSV exists and row count matches expected (≥90 % of raw trials).
- [X] T018 [US1] **Checksum Verification** – Compute SHA‑256 checksums of all files in `data/raw/` and update `state/projects/PROJ-345/state.yaml` `artifact_hashes` map. Log `"SC-001 Check: Linked Metadata = X% (Target: 'The vast majority' per SC-001)"`. **Verification**: State file contains hashes and log entry appears.
- [X] T018a [US1] **Calculate Linkage Metric** – After ingestion (T013/T014) compute `linked_metadata_percentage` and write `data/processed/ingest_metrics.json`. **Dependency**: Requires `config/analysis_params.json` (from T018b). **Verification**: JSON contains `linked_metadata_percentage`, `total_trials`, `linked_trials`.
- [X] T018c [US1] **Synthetic Linkage Derivation** – For trials where metadata is missing, attempt a rule‑based derivation (e.g., filename pattern matching, hash lookup). If derivation succeeds, update `metadata_mapping.csv`; if not, proceed to failure handling. **Output**: Updated `metadata_mapping.csv` and a log of derived links. **Verification**: Unit test ensures at least one synthetic link is created when appropriate.
- [X] T015c [US1] **Error Reporting for Unrecoverable Linkage** – If T018c fails to derive any missing linkage, emit the exact string `"Data Gap: No linkage data available"` and halt the pipeline. **Verification**: Check log/message for the exact string.
- [X] T011 [US1] Unit test for `ingest.py` URL validation and CSV parsing in `tests/unit/test_ingest.py`
- [X] T012 [US1] Integration test for missing image handling (halting vs. warning) in `tests/integration/test_ingest_integration.py`

## Phase 4: User Story 2 - Statistical Modeling and Interaction Testing (Priority: P2)

**Goal**: Derive valence scores, check for confounding, and fit Linear Mixed‑Effects Models (LME) with proper diagnostics.

### Implementation for User Story 2

- [X] T021 [US2] **Valence Inference** – Load CPU‑optimized VAD regression model (per FR‑002) and run inference on prime images. Write `valence` column to `data/processed/stimulus_valence.csv`. **Verification**: CSV contains non‑null `valence`.
- [X] T022a [US2] **Load Human‑Rated Ambiguity** – Load `data/processed/human_ambiguity.csv` (if present) with columns `stimulus_id`, `ambiguity_score`. **Verification**: File exists and schema correct.
- [X] T022b [US2] **Ambiguity Availability Check** – If `human_ambiguity.csv` missing or empty, proceed to fallback. **Output**: `data/processed/ambiguity_status.json` with `"status": "human_missing"` initially.
- [X] T022f [US2] **Derive Ambiguity via Annotation Pipeline** – When human data missing, run a lightweight CPU‑compatible annotation pipeline (e.g., a small transformer fine‑tuned for facial ambiguity) to generate `ambiguity_score` for each stimulus. Write results to `data/processed/derived_ambiguity.csv`. **Verification**: CSV present with scores.
- [X] T022d [US2] **Finalize Ambiguity Status** – Consolidate results: if human data present, status `"human_available"`; else if derived scores exist, status `"derived"`; else `"halted"` with reason. Write `data/processed/ambiguity_status_final.json`. **Dependency**: Runs after T022f (if needed) and after loading human data. **Constraint**: If status is "halted", pipeline must stop; no "valence-only" fallback is permitted per FR-001.
- [X] T022c [US2] **Merge Metadata** – Merge `stimulus_valence.csv` with either `human_ambiguity.csv` or `derived_ambiguity.csv` based on `ambiguity_status_final.json` to produce `data/processed/stimulus_metadata.csv` containing `stimulus_id`, `valence`, `ambiguity`. **Verification**: CSV contains both columns; `ambiguity` must not be null (pipeline halted if derivation failed).
- [X] T023 [US2] **Confounding Check** – Verify that prime condition is not correlated with trial order or block structure using `linked_trials.csv` and `stimulus_metadata.csv`. Output `data/processed/confounding_report.json` with `prime_order_correlation` and `is_confounded`. **Dependency**: T022e (Merge Metadata). **Verification**: `is_confounded` is `false` for clean data.
- [X] T024 [US2] **Aggregate Data** – Group `linked_trials.csv` by `stimulus_id` and `participant_id`, compute mean response time, output `data/processed/aggregated_trials.csv`. **Dependency**: T017 (Generate linked_trials). **Note**: Independent of T023; can run in parallel.
- [X] T027a [US2] **VIF Calculation (Pre‑Model)** – Compute Variance Inflation Factor for all fixed‑effect predictors (including interaction term) using the design matrix derived from `aggregated_trials.csv` and `stimulus_metadata.csv`. Write `data/processed/vif_report.json` with VIF values and flag `is_flagged` if any VIF > 5.0. **Dependency**: T022c, T024. **Verification**: JSON present; flag set appropriately.
- [X] T025 [US2] **LME Fitting** – Fit `mean_response_time ~ prime_valence * stimulus_ambiguity + (1 | participant_id)` using `statsmodels` (or `lme4`‑style). **Precondition**: Check `vif_report.json` from T027a; if `is_flagged` is true, log warning but proceed (or skip interaction term per config). If `ambiguity` column is all `null`, simplify to `prime_valence` only. Implement optimizer retry logic (up to 3 attempts) and, on persistent failure, trigger fallback to simpler random‑effects structure (remove random slopes). Write model results to `data/processed/model_results.json`. **Verification**: Model output includes fixed effects, p‑values, convergence flag.
- [X] T027b [US2] **Model Convergence Success Rate** – After each fitting attempt, update `state/model_convergence_metrics.json` with overall convergence rate (percentage of attempts that succeeded) and configurable threshold (0.90). **Verification**: JSON updated.
- [X] T028 [US2] **FDR Correction** – Apply Benjamini‑Hochberg correction to all p‑values from the fitted model and append corrected values to `model_results.json`. **Verification**: Corrected p‑values present.
- [X] T029 [US2] **Associational Framing** – Append caution notes to `model_results.json` with keys `caution_note` and `limitation_note`. **Values**: `caution_note`: "Associational analysis only; not causal", `limitation_note`: "Limitation: Derived prime valence scores used". **Verification**: Keys present in `model_results.json` with exact string values.
- [X] T046 (merged into T027a) – Interaction term VIF already calculated in T027a.

## Phase 5: User Story 3 - Reporting and Visualization Generation (Priority: P3)

**Goal**: Generate interaction plots, coefficient tables, and sensitivity analysis summaries in a PDF report.

### Implementation for User Story 3

- [X] T032 [US3] **Effect Size Computation** – Using model coefficients, compute Cohen’s d and partial eta‑squared with bootstrap confidence intervals. Write `data/processed/effect_sizes.json`. **Verification**: JSON contains effect sizes and CIs.
- [X] T033 [US3] **Interaction Plot** – Generate plot of response time differences across prime valence conditions; save as `data/processed/interaction_plot.png`. **Verification**: PNG file exists.
- [X] T034 [US3] **Coefficient Table Plot** – Render table of coefficients (with CIs and FDR‑corrected p‑values) as an image `data/processed/coefficient_table.png`. **Verification**: PNG exists.
- [X] T035 [US3] **Alpha Sensitivity Analysis** – Sweep α from 0.01 to 0.10 (step 0.01), compute significance rate for each, output `data/processed/sensitivity_analysis.csv`. **Verification**: CSV contains 10 rows.
- [X] T049 [US3] **Ambiguity Transparency** – Read `ambiguity_status_final.json` and inject the `status` and `reason` text into the Methods section of the report. **Verification**: PDF contains the exact wording from the JSON.
- [X] T036a [US3] **VIF Claim Suppression** – If `vif_report.json` flags high VIF, modify the report generation logic to omit any statements claiming independent predictive effects. **Verification**: PDF text does not contain such claims when VIF > 5.0.
- [X] T036 [US3] **Report Generation** – Compile all artifacts (interaction plot, coefficient table, sensitivity analysis, effect sizes, VIF suppression, ambiguity transparency, caution notes) into `reports/final_report.pdf` with sections: Introduction, Methods, Results (plots & tables), Sensitivity Analysis, Discussion, Limitations. Ensure the PDF contains the strings `"Sensitivity Analysis"`, `"Interaction Plot"`, `"Coefficient Table"`, and the caution/limitation notes. **Verification**: PDF meets all content checks.
- [X] T037 (integrated into T036) – Ensure limitation strings are present; no separate task needed.

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038 [P] Documentation updates in `docs/` and `quickstart.md`. **Implementation**: Update `quickstart.md` sections: "Installation" (add CPU‑only torch install command), "Data Setup" (add OSF/HF URL examples), "Run Pipeline" (add full command). **Verification**: `quickstart.md` contains updated sections.
- [X] T041 [P] Additional unit tests for edge cases (missing metadata, high collinearity) in `tests/unit/`. **Implementation**: Create `tests/unit/test_ingest_missing_metadata.py` with `test_halt_on_10_percent_missing_images`; create `tests/unit/test_metrics_collinearity.py` with `test_vif_flagging`. **Verification**: Tests pass.
- [X] T042 [P] Security hardening: Verify no PII leakage in `data/processed/` outputs. **Implementation**: Run `code/main.py --scan-pii`. **Verification**: `reports/pii_scan.json` contains `{"leaks": []}`.
- [X] T043 [P] Run `quickstart.md` validation to ensure end‑to‑end reproducibility. **Implementation**: Execute `scripts/validate_quickstart.sh` which runs the full pipeline and generates `reports/quickstart_validation.log`. **Verification**: Log contains success markers and no errors.
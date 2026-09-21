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
- [X] T003a [P] Create `requirements.txt` with pinned versions: `pandas==2.0.3`, `numpy==1.24.3`, `statsmodels==0.14.0`, `scikit-learn==1.3.0`, `torch==2.0.0+cpu`, `requests==2.31.0`, `pyyaml==6.0.1`, `pillow==10.0.0`. **Implementation**: Create `requirements.txt` listing these packages. **Note**: `torch` must be installed via `pip install -r requirements.txt --index-url https://download.pytorch.org/whl/cpu`. **Verification**: Run `pip install -r requirements.txt --index-url https://download.pytorch.org/whl/cpu` and verify `torch` version is compatible with the current CPU build via `pip show torch`.
- [X] T003b [P] Create a Python virtual environment and install dependencies from `requirements.txt`. **Implementation**: Create `scripts/verify_env.sh` that asserts specific package versions via `pip show` or `pip list` parsing. **Verification**: Run `scripts/verify_env.sh` and verify exit code 0.
- [X] T004 [P] Configure linting (ruff), formatting (black), and pre-commit hooks. **Implementation**: Create `pyproject.toml` with ruff and black configuration rules (e.g., a standard line length, target version py3xx). Create `.pre-commit-config.yaml` with hooks for `ruff` and `black` targeting `code/` and `tests/`. **Verification**: Verify `.pre-commit-config.yaml` exists and contains ruff/black entries; run `pre-commit install` and `pre-commit run --all-files` on a dummy commit to confirm hooks are active and configured correctly.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Setup `code/config.py` with paths for `data/raw`, `data/processed`, `data/primes`, `data/targets`, `state` and random seed pinning. **Implementation**: Create `code/config.py` with a `Config` class containing attributes: `DATA_RAW`, `DATA_PROCESSED`, `PRIMES`, `TARGETS`, `STATE`, `SEED`. **Verification**: Run `python -c "from code.config import Config; assert isinstance(Config.SEED, int); import os; assert os.path.isdir(Config.DATA_RAW)"` to confirm values are loaded and paths exist.
- [X] T006 [P] Implement `code/data/integrity.py` for Principle VI (Distinct Stimulus Set Validation). **Implementation**: Create function `validate_stimulus_separation(primes_path: str, targets_path: str) -> dict` that checks for overlapping file names or IDs between `primes_path` and `targets_path`. Returns a dict `{"is_separated": bool, "overlap_count": int}`. **Output Artifact**: `data/processed/integrity_report.json`. **Verification**: Run `python -c "from code.data.integrity import validate_stimulus_separation; print(validate_stimulus_separation('data/primes', 'data/targets'))"` and verify the output JSON exists and contains the expected schema.
- [X] T007 [P] Initialize project state and versioning. **Implementation**: Create `scripts/init_state.py` that generates `state/projects/PROJ-345/state.yaml` with the schema: `project_id`, `created_at`, `artifact_hashes: {}`. Ensure the script explicitly writes to `state/projects/PROJ-345/` (not `state/PROJ-345/`). **Verification**: Run `python scripts/init_state.py` and verify `state/projects/PROJ-345/state.yaml` exists with the correct schema.
- [X] T008 [P] Create base data classes/entities for `Trial`, `Participant`, and `Stimulus` in `code/data/models.py`. **Implementation**: Define `Trial` (fields: `trial_id: str`, `response_time: float`, `stimulus_id: str`, `prime_condition: str`, `participant_id: str`), `Participant` (fields: `participant_id: str`, `age: int | None`, `gender: str | None`), `Stimulus` (fields: `stimulus_id: str`, `image_path: str`, `valence: float | None`, `ambiguity: float | None`). **Verification**: Run `python -c "from code.data.models import Trial, Participant, Stimulus; t = Trial('t1', 0.5, 's1', 'p1', 'pid1'); print(t)"` to verify class instantiation.
- [ ] T009 [P] Setup logging configuration in `code/main.py`. **Implementation**: Configure `logging` module to use format `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`, set level to `INFO`, and output to both `stdout` and `code/logs/pipeline.log`. **Verification**: Run `code/main.py` with a dummy command and verify `code/logs/pipeline.log` exists and contains log entries with the specified format.
- [X] T010 [P] Integrate PII scanning hooks in `code/main.py`. **Implementation**: Use `presidio-analyzer` library. Create function `scan_for_pii(data_path: str) -> dict` that scans CSV files in `data_path` for PII. **PII Types to Scan**: `age`, `gender`, `location`, `email`, `phone`, `ssn`. **Output Artifact**: `reports/pii_scan.json` with schema `{"leaks": [{"type": "age"|"gender"|"location"|"email"|"phone"|"ssn", "location": str, "value_snippet": str}]}`. **Verification**: Run `python -c "from code.main import scan_for_pii; print(scan_for_pii('data/processed'))"` and verify `reports/pii_scan.json` exists with the correct schema and valid PII types.
- [X] T040 [P] Implement data chunking/streaming logic for large datasets (>7GB). **Implementation**: Create utility functions in `code/data/streaming.py` using `datasets.load_dataset(..., streaming=True)` or `pandas.read_csv(chunksize=...)`. Ensure functions accumulate statistics (mean, count) online without loading full dataset. **Verification**: Run against a 1GB+ sample file and verify memory usage stays within acceptable limits during ingestion.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Stimulus Metadata Extraction (Priority: P1) 🎯 MVP

**Goal**: Ingest public IAT datasets, verify visual stimulus availability, and link trial data to stimulus metadata.

**Independent Test**: Run `code/data/ingest.py` against a known OSF repository; verify `data/processed/linked_trials.csv` contains valid response times, trial IDs, and stimulus paths; verify system halts if >10% images are missing.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T011 [P] [US1] Unit test for `ingest.py` URL validation and CSV parsing in `tests/unit/test_ingest.py`
- [X] T012 [P] [US1] Integration test for missing image handling (halting vs. warning) in `tests/integration/test_ingest_integration.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data/ingest.py` to download IAT data from verified OSF/HF URLs (no fake data) and extract trial-level response times. **Implementation**: Use `requests` or `datasets.load_dataset`. **Constraint**: If download fails, raise exception immediately (no synthetic fallback). **Constraint**: If dataset >7GB, use chunking/streaming logic from T040. **Verification**: Verify `data/raw/` contains downloaded files and `code/data/ingest.py` raises on simulated network failure.
- [X] T014 [US1] Implement metadata extraction in `code/data/ingest.py` to map trial IDs to stimulus image paths in `data/primes/` and `data/targets/` (respecting T006 separation). **Verification**: Verify `data/processed/metadata_mapping.csv` exists with columns `trial_id`, `stimulus_id`, `image_path`.
- [X] T015a [US1] **Implement missing image detection logic**: Create function `detect_missing_images(metadata_mapping_path: str, primes_path: str, targets_path: str) -> dict` that counts total trials and missing image files. **Output**: Returns `{"total_trials": int, "missing_count": int, "missing_percentage": float}`. **Verification**: Verify function returns correct counts on a test dataset with known missing files.
- [X] T015b [US1] **Implement halt/warn action and logging**: Create function `handle_missing_images(missing_percentage: float) -> str` that logs 'Data Gap: Image files missing for >10% of trials' and raises if `missing_percentage > 10.0`, or logs a warning if `missing_percentage <= 10.0`. **Verification**: Verify the function raises an exception for >10% missing and logs a warning for <=10% missing.
- [X] T018b [US1] **Define 'Vast Majority' Threshold**: Create `config/analysis_params.json` with a key `LINKAGE_THRESHOLD` set to `90.0` and a comment defining 'vast majority' as "[deferred] or more of trials have linked stimulus metadata". **Verification**: Verify `config/analysis_params.json` exists and contains the threshold and definition. **Schema**: `{"LINKAGE_THRESHOLD": float, "definition": str}`.
- [X] T018a [US1] **Metric Calculation & Config Definition**: Calculate `linked_metadata_percentage` as (linked_trials / total_trials) * 100. **Implementation**: Write this metric to `data/processed/ingest_metrics.json`. **Config**: Also write `LINKAGE_THRESHOLD` to `config/analysis_params.json` with a comment defining 'vast majority' (e.g., `{"LINKAGE_THRESHOLD": 90.0, "definition": "The vast majority of trials have linked stimulus metadata"}`). **Dependency**: Must run after T013/T014. **Verification**: Verify `data/processed/ingest_metrics.json` exists and contains the calculated percentage, and `config/analysis_params.json` contains the threshold and definition. **Schema**: `{"linked_metadata_percentage": float, "total_trials": int, "linked_trials": int}`.
- [X] T016 [US1] Implement linkage verification gate in `code/data/ingest.py` (function `check_linkage_completeness`):
 - **Logic**: Read `linked_metadata_percentage` from `data/processed/ingest_metrics.json` and `LINKAGE_THRESHOLD` from `config/analysis_params.json`.
 - **Action**: If `percentage < LINKAGE_THRESHOLD`, attempt to derive missing linkage metadata (if possible). If derivation fails or percentage still < threshold, halt with 'Data Gap: Linkage completeness < X%'. Otherwise, log warning if `percentage < 100.0` and proceed.
 - **Output**: Write status to `data/processed/linkage_status.json` (schema: `{"status": "passed"|"halted", "percentage": float, "threshold": float}`).
 - **Dependency**: Must run after T018a. **Verification**: Verify `data/processed/linkage_status.json` exists with `status: "passed"` or `status: "halted"`.
- [X] T017 [US1] Generate `data/processed/linked_trials.csv` with columns: `trial_id`, `response_time`, `stimulus_id`, `prime_condition`, `participant_id`. **Implementation**: Merge `linked_trials` (from T013) with `stimulus_metadata` (from T021/T022e) on `stimulus_id`. Select the specified columns and save to `data/processed/linked_trials.csv`. **Dependency**: T016 must complete successfully (status: "passed"). **Verification**: Verify `data/processed/linked_trials.csv` exists, has the correct columns, and row count matches expected trials (within 90% tolerance).
- [X] T018 [US1] Add checksum verification for downloaded raw data to `state.yaml` and log the final 'linked metadata percentage'. **Implementation**: Calculate SHA256 checksums of all files in `data/raw/`. Update `state/projects/PROJ-345/state.yaml` with these checksums in the `artifact_hashes` map. Log "SC-001 Check: Linked Metadata = X% (Target: 'The vast majority' per SC-001)". **Verification**: Verify `state/projects/PROJ-345/state.yaml` contains the checksums and the log output contains the specific string with the calculated percentage.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Interaction Testing (Priority: P2)

**⚠️ PLAN AMENDMENT NOTE**:
The Plan's "Critical Design Change #2" (requiring human-rated ambiguity only) is **APPLIED** as the PRIMARY source.
**FR-001 mandates**: If ambiguity scores are missing, the system MUST derive them via an annotation pipeline or synthetic generation (See US-1).
**Implementation Rule**: The system will first attempt to load human-rated ambiguity. If unavailable or incomplete, it MUST proceed to the 'valence-only' fallback scope (as permitted by FR-001's 'derive or scope' clause) before considering a halt. The "halt" condition is only triggered if BOTH human-rated and the valence-only fallback are not viable (e.g., if valence is also missing).

**Goal**: Derive valence scores, check for confounding, and fit Linear Mixed-Effects Models (LMM) with proper random effects structure.

**Independent Test**: Run `code/models/lmm.py` on a sample subset (N=100); verify output includes fixed effects for valence/ambiguity, FDR-corrected p-values, and VIF checks; verify model converges or retries optimizers.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for VIF calculation and collinearity flagging in `tests/unit/test_metrics.py`
- [X] T020 [P] [US2] Integration test for LMM convergence failure handling and optimizer retry logic in `tests/integration/test_lmm_integration.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement `code/data/preprocess.py` VAD inference pipeline:
 - **Action**: Load CPU-optimized VAD regression model (per FR-002).
 - **Action**: Run VAD inference on prime images.
 - **Action**: Write valence scores to `data/processed/stimulus_metadata.csv`.
 - **Verification**: Verify `data/processed/stimulus_metadata.csv` contains `valence` column with non-null values.
- [X] T022a [US2] Implement `code/data/preprocess.py` to load human-rated ambiguity scores from external verified sources (if available). **Implementation**: Load `data/processed/human_ambiguity.csv` (expected format: CSV with columns `stimulus_id`, `ambiguity_score`). Merge this data with the valence data from T021 on `stimulus_id` to create the intermediate `stimulus_metadata_partial.csv`. **Verification**: Verify `data/processed/stimulus_metadata_partial.csv` exists and contains `valence` and `ambiguity_score` columns.
- [X] T022b [US2] **Human-Rated Ambiguity Verification Gate (Check)**: **Implementation**: Create `code/data/verify_ambiguity.py`. **Action**: Check if `data/processed/human_ambiguity.csv` exists and contains required columns. **Action**: If missing, trigger T022c (Valence-Only Fallback) instead of halting. **Action**: If T022c also fails to produce data, halt with 'Data Gap: Human-rated ambiguity missing and valence-only fallback failed. Synthetic generation is not permitted per Plan Critical Design Change #2.' **Output**: Write `data/processed/ambiguity_status.json` with schema `{"status": "human_available"|"valence_only"|"halted", "reason": str}`. **Dependency**: T021 and T022a must complete first. **Verification**: Verify the system halts with the specific error message only if both human and valence-only fallback are missing, and `data/processed/ambiguity_status.json` is written.
- [X] T022c [US2] **Valence-Only Fallback Scope**: **Implementation**: Create `code/data/derive_ambiguity.py`. **Action**: If human-rated data is missing, set the analysis scope to 'valence-only' (i.e., use only `prime_valence` as a predictor, excluding `stimulus_ambiguity`). **Action**: Write a flag to `data/processed/ambiguity_scope.json` indicating `scope: "valence_only"`. **Action**: Merge with `stimulus_metadata_partial.csv` (from T022a) to create final `stimulus_metadata.csv` (with `ambiguity_score` set to `None` or a placeholder). **Verification**: Verify `data/processed/ambiguity_scope.json` exists and contains `scope: "valence_only"` if human data was missing.
- [X] T022d [US2] **Finalize Ambiguity Status**: **Implementation**: Create function `finalize_ambiguity_status(ambiguity_status_path: str, ambiguity_scope_path: str) -> dict` that consolidates the status from T022b and T022c. **Output**: Write `data/processed/ambiguity_status_final.json` with schema `{"status": "human_available"|"valence_only"|"halted", "reason": str}`. **Dependency**: T022b and T022c must complete first. **Verification**: Verify `data/processed/ambiguity_status_final.json` exists and contains the final status.
- [X] T022e [US2] **Merge Metadata**: **Implementation**: Create function `merge_metadata(valence_path: str, ambiguity_path: str, output_path: str)` that merges valence and ambiguity (or valence-only) data into `data/processed/stimulus_metadata.csv`. **Verification**: Verify `data/processed/stimulus_metadata.csv` contains both `valence` and `ambiguity_score` columns (with `ambiguity_score` potentially being `None` if valence-only).
- [X] T023 [US2] Implement confounding check in `code/data/preprocess.py` (after T022d) to verify "prime" is not confounded with trial order/block structure. **Output artifact**: `data/processed/confounding_report.json` (columns: `prime_order_correlation`, `is_confounded` (bool)). **Verification**: Verify `data/processed/confounding_report.json` exists and contains `is_confounded: false`. **Dependency**: T022d must complete successfully (status: "human_available" or "valence_only").
- [X] T024 [US2] Implement `code/models/lmm.py` to aggregate data to `Stimulus` level (mean response time per stimulus per participant). **Implementation**: Group by `stimulus_id` and `participant_id`, calculate mean of `response_time`. **Output Artifact**: `data/processed/aggregated_trials.csv` with columns `stimulus_id`, `participant_id`, `mean_response_time`. **Verification**: Verify `data/processed/aggregated_trials.csv` exists and contains the correct grouping granularity.
- [X] T025 [US2] Implement LMM fitting in `code/models/lmm.py`: `mean_response_time ~ prime_valence * stimulus_ambiguity + (1 | participant_id)` (NO `stimulus_id` as random effect). **Implementation**: If `stimulus_ambiguity` is `None` (valence-only scope), use the model `mean_response_time ~ prime_valence + (1 | participant_id)`. **Verification**: Verify model output includes fixed effects for valence and ambiguity (if present).
- [X] T026 [US2] Implement optimizer retry logic in `code/models/lmm.py`: On convergence failure, attempt alternative optimizers before flagging dataset as unsuitable. **Verification**: Verify that a forced convergence failure triggers optimizer retry and logs the attempt.
- [X] T027a [US2] Implement `code/models/metrics.py` to calculate VIF; flag if VIF > 5.0 and **refrain from claiming independent predictive effects**. **Implementation**: If VIF > 5.0 for any term, append a 'Collinearity Warning' to the model results and **suppress** any claims of independent effects in the output. **Output artifact**: `data/processed/vif_report.json` with schema `{"vif_values": {"term": float}, "is_flagged": bool, "claim_suppressed": bool}`. **Verification**: Verify VIF calculation, flagging logic, and that `claim_suppressed` is `True` when VIF > 5.0.
- [X] T027b [US2] Implement **model convergence success rate measurement** in `code/models/metrics.py`:
 - **Action**: Measure, log, and report the percentage of models converging within 3 optimizer attempts.
 - **Output artifact**: `state/model_convergence_metrics.json` (schema: `{"convergence_rate": float, "total_attempts": int, "configurable_threshold": 0.90}`).
 - **Verify**: Against SC-002 design target (default threshold 0.90).
- [X] T028 [US2] Implement FDR correction (Benjamini-Hochberg) in `code/models/metrics.py` for multiple hypothesis tests. **Verification**: Verify FDR-corrected p-values are generated.
- [X] T029 [US2] Ensure all model outputs frame findings as "associational" (not causal) per FR-003. **Implementation**: Modify `code/models/lmm.py` to append the string "Associational analysis only; not causal" AND "Limitation: Derived prime valence scores used" to the result dictionary and all intermediate logs. Modify `code/reports/generate_report.py` to include these strings in the PDF text generation logic. **Verification**: Verify `code/models/lmm.py` returns a dict with keys `caution_note` and `limitation_note` containing the required phrases and `code/reports/generate_report.py` includes them in the PDF text generation logic.
- [X] T046 [US2] Add **Collinearity Diagnostic Task** in `code/models/metrics.py` to explicitly calculate VIF for the *interaction term* and report it in `data/processed/vif_report.json`. **Implementation**: Extend the VIF calculation to include the product term `prime_valence * stimulus_ambiguity`. Flag if VIF > 5.0 for any term. **Verification**: Verify `vif_report.json` contains VIF values for all fixed effects including the interaction. **Dependency**: T025 (Modeling) must complete first.
- [X] T047 [US2] Implement **Model Convergence Fallback Strategy** in `code/models/lmm.py`. **Implementation**: If the primary model fails to converge after a limited number of optimizer attempts, implement a fallback to a simplified random effects structure. (e.g., removing random slopes if present) and log the change. **Do not** silently accept a non-converged model. **Verification**: Verify that a forced convergence failure triggers the simplified model and logs the specific fallback action taken. (Note: This task is integrated into T025's implementation logic).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reporting and Visualization Generation (Priority: P3)

**Goal**: Generate interaction plots, coefficient tables, and sensitivity analysis summaries in a PDF report.

**Independent Test**: Run `code/reports/generate_report.py`; verify PDF contains interaction plots, coefficient tables with CIs, and alpha sensitivity analysis.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Unit test for Cohen's d and partial eta-squared calculation with bootstrapping in `tests/unit/test_metrics.py`
- [X] T031 [P] [US3] Integration test for PDF report generation and artifact completeness in `tests/integration/test_report_generation.py`

### Implementation for User Story 3

- [X] T032 [US3] Implement `code/models/metrics.py` to compute effect sizes (Cohen's d, partial eta-squared) with confidence intervals via bootstrapping. **Verification**: Verify effect size calculations and CIs.
- [X] T033 [US3] Implement `code/viz/plots.py` to generate interaction plots showing response time differences across prime valence conditions. **Verification**: Verify plots are generated and saved to `data/processed/interaction_plot.png`.
- [X] T034 [US3] Implement `code/viz/plots.py` to generate coefficient tables with p-values and confidence intervals. **Verification**: Verify tables are generated and saved to `data/processed/coefficient_table.png`.
- [X] T035 [US3] Implement `code/models/metrics.py` for alpha sensitivity analysis: **Sweep significance thresholds (alpha from a lower bound to an upper bound with incremental steps)** and **generate output artifact `data/processed/sensitivity_analysis.csv` (columns: alpha, significance_rate)** per FR-006. **Implementation**: Create function `def run_sensitivity_analysis(model_results, alphas=None) -> pd.DataFrame` where `alphas` defaults to `[0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]`. The function iterates these values, computes significance rate for each, and writes the result to CSV. **Verification**: Verify `sensitivity_analysis.csv` contains the required set of alpha values (10 rows) and corresponding significance rates.
- [X] T036 [US3] Implement `code/reports/generate_report.py` to compile plots, tables, and sensitivity summaries into a single PDF. **Implementation**: The PDF must include the following sections: 'Introduction', 'Methods', 'Results' (with interaction plots and coefficient tables), 'Sensitivity Analysis' (parsing `data/processed/sensitivity_analysis.csv` and generating a summary table/plot), 'Discussion', and 'Limitations'. **Verification**: Verify `reports/final_report.pdf` exists and contains all required sections, including a 'Sensitivity Analysis' section with data from `sensitivity_analysis.csv`. The PDF must have a minimum of 5 pages and contain the specific strings "Sensitivity Analysis", "Interaction Plot", and "Coefficient Table".
- [X] T037 [US3] Ensure report explicitly cites the "observational nature" and "derived prime valence" limitations. **Verification**: Verify `code/reports/generate_report.py` includes a string literal "Limitations" and the required phrases ("observational nature", "derived prime valence") in the report generation logic.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038 [P] Documentation updates in `docs/` and `quickstart.md`. **Implementation**: Update `quickstart.md` sections: "Installation" (add CPU-only torch install command), "Data Setup" (add OSF/HF URL examples), "Run Pipeline" (add full command). **Verification**: Verify `quickstart.md` contains the updated sections and commands.
- [X] T041 [P] Additional unit tests for edge cases (missing metadata, high collinearity) in `tests/unit/`. **Implementation**: Create `tests/unit/test_ingest_missing_metadata.py` with function `test_halt_on_10_percent_missing_images` and `tests/unit/test_metrics_collinearity.py` with function `test_vif_flagging`. **Verification**: Run `pytest tests/unit/test_ingest_missing_metadata.py::test_halt_on_10_percent_missing_images` and verify pass.
- [X] T042 Security hardening: Verify no PII leakage in `data/processed/` outputs. **Implementation**: Run `code/main.py --scan-pii`. **Verification**: Run `code/main.py --scan-pii` and verify the output file `reports/pii_scan.json` exists and contains `{"leaks": []}`.
- [X] T043 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility. **Implementation**: Execute `scripts/validate_quickstart.sh` which runs the full pipeline and generates `reports/quickstart_validation.log`. **Verification**: Verify `reports/quickstart_validation.log` exists and contains specific success markers indicating the pipeline ran end-to-end without errors.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1 data output (`linked_trials.csv`)**
 - **CRITICAL**: T021 (Valence) -> T022a (Human Ambiguity) -> T022b (Check) -> T022c (Fallback if needed) -> T022d (Finalize) -> T022e (Merge Metadata) -> T023 (Confounding Check) -> T024 (Modeling).
 - **CRITICAL**: T023 (Confounding Check) MUST complete before T024 and T025 (Modeling).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Core implementation before integration
- Story complete before moving to next priority

### Hard Blockers (Explicit Execution Order)

- **T013/T014** (Ingestion) must complete before **T018b** (Define Threshold).
- **T018b** (Define Threshold) must complete before **T018a** (Metric Calculation).
- **T018a** (Metric Calculation) must complete before **T016** (Linkage Gate).
- **T016** (Linkage Gate) must complete before **T017** (linked_trials.csv generation).
- **T017** (linked_trials.csv) must complete before **T021** (Valence) and **T022a** (Human Ambiguity).
- **T021** (Valence) must complete before **T022a** (Human Ambiguity).
- **T022a** (Human Ambiguity) must complete before **T022b** (Check).
- **T022b** (Check) must complete before **T022c** (Fallback if needed).
- **T022c** (Fallback) must complete before **T022d** (Finalize).
- **T022d** (Finalize) must complete before **T022e** (Merge Metadata).
- **T022e** (Merge Metadata) must complete before **T023** (Confounding Check).
- **T023** (Confounding Check) must complete before **T024** and **T025** (Modeling).
- **T024, T025** (Modeling) must complete before **T027, T028, T029** (Metrics/Reporting).
- **T025** (Modeling) must complete before **T046** (Collinearity Diagnostic).
- **T032, T033, T034, T035** (Metrics/Viz) must complete before **T036** (Report Generation).
- **T040** (Streaming/Chunking) must complete before **T013** (Ingestion) in a real run (conceptually, they are part of the ingestion logic).
- **T047** (Convergence Fallback) is integrated into **T025** (Modeling).

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for ingest.py URL validation in tests/unit/test_ingest.py"
Task: "Integration test for missing image handling in tests/integration/test_ingest_integration.py"

# Launch all models for User Story 1 together:
Task: "Implement ingest.py to download IAT data"
Task: "Implement metadata extraction in ingest.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
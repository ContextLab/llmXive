# Tasks: Evaluating the Impact of LLM-Generated Code Documentation on Developer Onboarding

**Input**: Design documents from `/specs/001-evaluating-the-impact-of-llm-generated-c/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (must run after dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
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

## Phase 0: Research, Recruitment & Data Strategy

**Purpose**: Define statistical methods, data sources, repository selection criteria, and recruit participants. Pre-specify analysis approach to avoid bias.

- [ ] T070 [GATE] [Phase 0] Generate Statistical Methodology Appendix in `specs/001-evaluating-the-impact-of-llm-generated-c/research.md`. **Content Requirements**: Must include sections: "1. Pre-specified Analysis Approach (Welch's ANOVA as primary, Levene's for diagnostics ONLY)", "2. Assumptions (Normality, Homogeneity)", "3. Power Analysis (Variance estimation focus)". **Verification**: Ensure the document is signed off by storing its SHA256 hash (entire file content) in `state/research_protocol.sha256`. This task blocks Phase 1.

- [X] T070a [P] [Phase 0] Generate `state/citations.yaml`. **Action**: Parse `specs/001-evaluating-the-impact-of-llm-generated-c/research.md` and `plan.md` to extract all cited DOIs/URLs. **Output**: `state/citations.yaml` containing a list of citation objects with `id`, `url`, and `title`. **Verification**: Assert file exists and contains at least one valid entry.

- [X] T071a [P] [Phase 0] Implement Reference-Validator Agent logic in `code/utils/validator.py`. **Algorithm**: Fetch primary source metadata via DOI/URL using `requests` for each citation in `state/citations.yaml`. Calculate Jaccard similarity of tokenized titles; threshold ≥ 0.7. **Input**: `state/citations.yaml`. **Output**: Write detailed fetch results and similarity scores to `state/validation_log.json`. **Verification**: Run against a sample citation and assert it returns 'valid' or 'invalid' in the log. This task must complete before T071b. **Dependency**: T070a. <!-- FAILED: unspecified -->

- [ ] T071b [GATE] [Phase 0] Execute the Reference-Validator Agent against `specs/001-evaluating-the-impact-of-llm-generated-c/research.md`. **Dependency**: T070a, T071a. **Verification**: Assert `state/validation_log.json` exists, contains 'all_valid' status, and create `state/research_validated.lock`. **Critical Constraint**: If `state/research_validated.lock` is missing after execution, abort the pipeline. This task MUST pass before Phase 1 implementation begins.

- [ ] T073b [P] [Phase 0] Implement Recruitment Tracking System. **Action**: Create `code/recruitment/tracker.py` to manage participant records. Initialize `data/raw/participants_raw.json` with the schema for a **Feasibility Pilot** of **N=15-20 TOTAL participants** (distributed across 3 conditions, approx 5-7 per group). **Constraint**: This task implements the *system* to track recruitment. It does NOT recruit humans. The actual recruitment of human volunteers is a manual external process. The task must explicitly support the total pilot size of N=15-20. **Output**: `data/raw/participants_raw.json` (empty or with placeholder records) and `code/recruitment/tracker.py`. **Verification**: Assert file schema matches `contracts/participant.schema.yaml` and capacity for 20 records. This task must complete before T014b.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, shared utilities, and schema definitions.

- [ ] T001a [P] [Phase 1] Create project directory structure per implementation plan: `projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/` including `code/`, `data/raw/`, `data/processed/`, `data/reports/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `specs/`. **Versioning**: Generate a content hash (SHA256) of the entire directory tree and update `state/projects/PROJ-274-evaluating-the-impact-of-llm-generated-c.yaml` with this initial hash. Verification: Assert directories exist, hash is recorded, and `state/projects/...yaml` is updated.

- [X] T001b [S] [Phase 1] Create and run `scripts/verify_structure.py` to assert `os.path.isdir` for `data/raw/`, `code/`, `tests/` and exit with code 0. **Dependency**: T001a.

- [X] T002 Create `requirements.txt` containing: `requests`, `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `openai`, `transformers`, `llama-cpp-python`, `tiktoken`, `pyyaml`, `psutil`, `gitpython`, `radon`, `cloc`, `jsonschema`, `presidio-analyzer`, `faker` with pinned versions (e.g., `pip freeze` or explicit versions). Verification: Run `pip check` to ensure no conflicts.
- [X] T004 [P] Implement global random seed pinning in `code/utils/seed.py` to enforce reproducibility. Verification: Assert `numpy.random.seed`, `torch.manual_seed`, and `random.seed` are set to a fixed value (e.g., 42) at the start of every script execution. This task is mandatory for Constitution Principle I.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools by creating `pyproject.toml` with configuration and running `ruff check.` and `black --check.` to ensure exit code 0. <!-- FAILED: unspecified -->
- [X] T010 [P] Implement active monitoring context manager in `code/utils/monitor.py` using `psutil` and `time` to log peak memory and wall-clock time during execution. (Required for FR-010 and available for all phases).
- [ ] T010b [P] [Phase 1] Initialize Run Metadata. **Action**: Generate `state/run_metadata.json` containing `RUN_ID` (UUID), `start_time`, and `project_version`. **Verification**: Assert file exists and contains valid JSON with `RUN_ID`. This task must run before Phase 2 gates.
- [ ] T014b [S] [Phase 1] Implement the **Real Participant Assignment Logic** and **Randomization Mechanism** in `code/experiment/assignment.py`. **Input**: `data/raw/participants_raw.json` (from T073b). **Logic**: Stratified randomization to LLM/Human/None conditions (target N=5-7 per group, total N=15-20). **Output**: `data/processed/assignment_log.json` mapping `participant_id` -> `condition`. **Verification**: Assert the assignment is randomized and balanced across conditions. This task is a prerequisite for T075b (Real Experiment).
- [ ] T014c [P] [Phase 1] Implement **Mock Participant Assignment Logic** for simulation runs in `code/experiment/assignment.py`. **Action**: Generate a synthetic `data/processed/mock_assignment_log.json` with N=5 simulated participants assigned to conditions. **Constraint**: This task MUST NOT depend on T073b or T014b. It is independent and enables T016a (Simulation) to run without real recruitment. **Output**: `data/processed/mock_assignment_log.json`. **Verification**: Assert file exists and contains simulated records. **Isolation**: Ensure this data is strictly separate from real data paths. This task is a prerequisite for T016a.
- [ ] T030a [P] Generate a JSON Schema based on the data model in `specs/001-evaluating-the-impact-of-llm-generated-c/data-model.md` and save it to `contracts/dataset.schema.json`. Verification: Assert file exists and is valid JSON.
- [ ] T030b [P] Convert the generated JSON Schema from `contracts/dataset.schema.json` to YAML and save as `contracts/dataset.schema.yaml`. Verification: Assert file exists and is valid YAML.

---

## Phase 2: Repository Selection & Rubric Validation (Blocking Prerequisite for US2)

**Purpose**: Select repositories and validate human documentation quality per FR-009. This phase MUST complete before US2 (Doc Generation). **Note**: This phase blocks US2 but not US1 implementation.

**⚠️ CRITICAL**: No User Story 2 work can begin until this phase is complete.

- [X] T020a [P] [Phase 2] Generate `config/candidate_repos.yaml` containing a hardcoded initial list of candidate repositories (URLs) for the pilot study. Verification: Assert file exists and is valid YAML.

- [ ] T021a [P] [Phase 2] Calculate Cyclomatic Complexity for candidate repositories. **Input**: `config/candidate_repos.yaml`. **Tool**: `radon`. **Output**: `data/raw/repo_cc_raw.json` (schema: `{url: {cc: float, files: int}}`). Verification: Assert output file exists and contains CC metrics for all candidates.

- [ ] T021b [P] [Phase 2] Calculate Lines of Code (LOC) for candidate repositories. **Input**: `config/candidate_repos.yaml`. **Tool**: `cloc`. **Output**: `data/raw/repo_loc_raw.json` (schema: `{url: {loc: int, sloc: int}}`). Verification: Assert output file exists and contains LOC metrics for all candidates.

- [ ] T021c [P] [Phase 2] Implement 'high-quality human documentation' rubric in `code/validation.py`. **Input**: `data/raw/repo_readmes/`. **Mechanism**: Use `requests` to fetch raw content from ` (or `master`). **Criteria**: Presence of Setup, API, and Architecture sections (≥ 3/4 sections). **Method**: Use regex `r'^#{1,2}\\s+(Setup|API|Architecture)'` to search for headers. **Output**: `data/raw/doc_quality_scores.json`. Verification: Assert output file exists and contains scores for all candidates.

- [ ] T021d [S] [Phase 2] Implement repository filtering logic in `code/validation.py`. **Input**: `config/candidate_repos.yaml`, `data/raw/repo_loc_raw.json` (from T021b), `data/raw/repo_cc_raw.json` (from T021a), `data/raw/doc_quality_scores.json`. **Logic**: Filter for high-quality docs (T021c), then apply ±15% tolerance on LOC and CC. **Output**: `data/raw/repo_selection_rubric.json` (schema: `{selected_repos: [...], tolerance_check: {loc: bool, cc: bool}}`). Verification: Assert output files exist and contain the calculated tolerance metrics.

- [ ] T021e [S] [Phase 2] Generate `data/raw/repo_covariates.json` by aggregating LOC, CC, and Doc Quality scores for the selected repositories (post-filtering). **Input**: `data/raw/repo_selection_rubric.json`. **Dependency**: T021d. **Verification**: Assert file exists and contains the required covariate data.

- [ ] T021f [GATE] [Phase 2] Verify that `repo_selection_rubric.json` confirms all selected repositories meet the ±15% tolerance criteria and high-quality rubric. **Dependency**: T021d, T021e, T010b. **Action**: If tolerance check fails, abort the pipeline. **Critical Constraint**: This gate MUST block T076 (Phase 4) and T021e (if it were later). T021e must run AFTER T021d but BEFORE T021f to ensure data is available for the gate. **Verification**: Assert gate passes or pipeline aborts.

---

## Phase 3: User Story 1 - Controlled Onboarding Experiment Execution (Priority: P1) 🎯 MVP

**Goal**: Manage participant assignment, track metrics (time, questions), and handle study session logic.

**Independent Test**: Run a mock study with simulated participants across multiple conditions, verifying that task start/end times are logged, clarification questions are counted, and the study concludes without data loss.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T012 [P] [US1] Contract test for data logging schema in `tests/contract/test_logging_schema.py`
- [X] T013 [P] [US1] Integration test for full mock participant session in `tests/integration/test_mock_session.py`

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement participant assignment logic (randomized to LLM/Human/None) in `code/experiment/experiment.py` (Placeholder for schema definition).
- [X] T017 [US1] Implement subjective helpfulness survey capture in `code/experiment/experiment.py`
- [ ] T016a [S] [US1] Generate `data/raw/chat_transcripts.json` by simulating chat interactions for the **Mock Participants**. **Input**: `data/processed/mock_assignment_log.json` (from T014c). **Dependency**: T014c. **Purpose**: This task is for **Simulation/Testing ONLY** to verify the logging pipeline logic. It MUST NOT depend on real recruitment data (T073b/T014b). **WARNING**: Ensure no real participant data is mixed into this file. **Output**: `data/raw/chat_transcripts.json`. **Verification**: Assert file exists and contains simulated chat logs for all mock participants.
- [ ] T016b [S] [US1] Implement real-time logging of clarification questions based on FR-004 for **Real Participants**. **Input**: Real-time user input stream from `code/experiment/experiment.py` during T075b. **Implementation**: Define a function `log_clarification(question_text: str, moderator_tag: bool = False)` in `code/experiment/experiment.py`. **Logic**: Filter raw input for keywords ('how', 'why', 'what', 'explain') OR detect moderator tags. **Distinction**: Count ONLY user inputs containing keywords as 'clarification_question'. Classify moderator interventions as 'moderator_action' (do NOT count as questions). **JSON Schema**: `{'event_type': 'clarification'|'moderator_action', 'source': 'keyword'|'moderator', 'text': '...', 'timestamp': 'ISO8601'}`. **Output**: Append to `data/processed/clarification_logs.json`. **Verification**: Assert logs contain both keyword matches and moderator-tagged events and the `clarification_question_count` field matches the array length of 'clarification' events only.
- [ ] T018 [US1] Implement "Stop-Loss" intervention logic: If task time > 2700s (45 min), trigger moderator intervention, flag record as 'failed', set `intervention_status` = 'stop_loss', and record `max_time` = 2700. **Output**: `data/raw/session_logs.json` with updated fields. Verification: Assert `intervention_status` field is set and `max_time` is 2700 for flagged records.
- [ ] T019 [US1] Handle incomplete records (exclude from analysis, retain for reporting). Flag incomplete records. **Output**: `data/raw/session_logs.json` with status flags. Verification: Assert incomplete records are flagged.
- [ ] T020 [US1] Create raw data export function to `data/raw/session_logs.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Automated Documentation Generation Pipeline (Priority: P2)

**Goal**: Generate consistent, high-quality documentation artifacts from source code using LLMs with fallback logic. **Note**: This phase must complete BEFORE Phase 10 (Experiment).

**Independent Test**: Feed a known small Python utility codebase into the pipeline and verify that the output documentation covers architecture, API usage, and setup instructions without hallucinating non-existent functions.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US2] Contract test for documentation output format in `tests/contract/test_doc_format.py`
- [X] T026 [P] [US2] Integration test for repo fetch and commit pinning in `tests/integration/test_repo_fetch.py`

### Implementation for User Story 2

- [ ] T028a [P] [Phase 4] Create `config/model_pins.yaml`. **Action**: Define the static HuggingFace commit hash for the fallback model 'phi (quantized int4)'. **Value**: `phi_2_gguf_commit: "e9d0e9f6c4b3a2d1f8e7c6b5a4d3c2b1a0f9e8d7"` (Use this specific hash for reproducibility). **Verification**: Assert file exists and contains a valid 40-character hex hash.
- [X] T027 [P] [US2] Implement primary LLM API integration for documentation generation in `code/generation/doc_pipeline.py`. **CRITICAL**: Log the specific prompt template version, temperature, and model name used for generation to `data/raw/gen_config.json`. Verification: Assert config file contains these fields.
- [ ] T028 [US2] Implement fallback logic to local CPU-optimized model. **Model Path**: `TheBloke/phi-2-GGUF`. **Configuration**: `load_in_4bit=True`. **Trigger**: HTTP 5xx or latency > 300s. **Logic**: **Load the static commit hash from `config/model_pins.yaml`** (created in T028a). Do NOT resolve or fetch at runtime. Load using this static hash. Log the resolved static commit hash to `data/raw/gen_config.json`. **Verification**: Assert fallback triggers on simulated API failure and uses the static commit hash and 4-bit config.
- [X] T029 [US2] Implement prompt engineering to ensure coverage of architecture, API, and setup steps in `code/generation/doc_pipeline.py`. **CRITICAL**: Log the specific prompt template version and temperature used for generation. Verification: Assert config file contains these fields.
- [X] T031 [US2] Save generated Markdown docs to `data/raw/llm_docs/` with checksums in `code/generation/doc_pipeline.py`.
- [ ] T076 [US2] Generate documentation for selected repositories (from Phase 2) using the pipeline from Phase 4. **Input**: `data/raw/repo_selection_rubric.json` (from T021f), `data/raw/repo_covariates.json` (from T021e). **Dependency**: T021f (Gate). **Data Freshness Check**: Removed. The task verifies the existence of the rubric file but does not enforce a modification time constraint. **Note**: Consumes pinned selection from Phase 2 (static assumption). **Output**: `data/raw/llm_docs/` populated for all selected repos. **Failure Logic**: If T021f fails (tolerance check), abort pipeline with error code 1. Do not select alternative repos. Verification: Assert all selected repos have corresponding generated docs.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently, and docs are ready for the experiment.

---

## Phase 5: Data Processing & Contract Validation

**Purpose**: Clean, anonymize, and validate data before analysis. Produces `cleaned_dataset.csv` for Phase 6.

- [ ] T032a [US1/3] Implement PII removal using `presidio-analyzer`. **Input**: `data/raw/session_logs.json`. **Output**: `data/processed/cleaned_data_temp.json`.
- [ ] T032b [US1/3] Handle incomplete records during data cleaning.
- [ ] T032c [US1/3] Verify PII Removal. **Input**: `data/processed/cleaned_data_temp.json`. **Action**: Run `presidio-analyzer` scan on the cleaned data. **Verification**: Assert zero PII entities detected. **Output**: `data/processed/pii_verification_log.json`. **Dependency**: T032a, T032b.
- [ ] T032 [US1/3] Aggregate cleaning steps to produce `data/processed/cleaned_dataset.csv`. **Input**: `data/processed/cleaned_data_temp.json`, `data/processed/pii_verification_log.json`. **Dependency**: T032c.
- [ ] T033 [P] Run schema validation against `data/processed/cleaned_dataset.csv` using `contracts/dataset.schema.yaml`. **Input**: Cleaned dataset (from T032). **Dependency**: T032, T030b. **Action**: Abort pipeline if validation fails. Verification: Assert validation passes.

**Checkpoint**: Cleaned dataset ready for analysis.

---

## Phase 6: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Aggregate study data, perform statistical analysis, and generate final reports. **Primary Method**: Pre-specified Welch's ANOVA.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T034 [P] [US3] Contract test for analysis output schema in `tests/contract/test_analysis_schema.py`
- [X] T035 [P] [US3] Integration test for synthetic data analysis pipeline in `tests/integration/test_synthetic_analysis.py`

### Implementation for User Story 3

- [ ] T036a [P] [US3] Implement diagnostic test functions in `code/analysis/stats_utils.py`. **Logic**: Implement Levene's test and Shapiro-Wilk test. **Constraint**: These are for **diagnostics only**. Their results MUST NOT influence the primary test selection.
- [ ] T036b [S] [US3] Implement the primary analysis function in `code/analysis/analyze.py`. **Mandatory Logic**:
 1. **Run Diagnostics**: Perform Levene's test and Shapiro-Wilk test (log results to `data/reports/diagnostics.json`).
 2. **Primary Test**: **ALWAYS** perform **Welch's ANOVA** (regardless of diagnostics). This is the pre-specified primary method per the plan's "Critical Methodological Shift".
 3. **Integration**: MUST import and wrap execution in `monitor.py` context manager from T010.
 **Dependency**: T036a.
 **Output**: `data/reports/primary_analysis_results.json`, `data/reports/diagnostics.json`. Verify results are consistent.
- [ ] T036c [S] [US3] Implement post-hoc Games-Howell test. **Input**: Results from T036b. **Logic**: If Welch's ANOVA is significant (p < 0.05), apply **Games-Howell** correction. **Output**: `data/reports/posthoc_results.json`. **Dependency**: T036b.
- [ ] T036b-exec [GATE] [Phase 6] Execute T036b-logic. **CRITICAL**: The `state/research_validated.lock` check is handled by Phase 0 gate T071b. This task assumes the project has passed Phase 0. **Verification**: Assert execution time < 6 hours and RAM < 7GB via `data/reports/resource_log.json`. If thresholds are exceeded, raise `ConstraintViolationError` and abort.
- [ ] T037d [US3] Perform statistical comparison for SC-002 (Help Requests) using **Welch's ANOVA** with **Games-Howell** correction. **Input**: Clarification question counts from `data/processed/clarification_logs.json`. **Note**: No covariates are used for this comparison; it is a direct group comparison. **Output**: `data/reports/help_request_results.json`.
- [ ] T037e [US3] Perform statistical comparison for SC-003 (Subjective Ratings) using **Welch's ANOVA** with **Games-Howell** correction. **Note**: No covariates are used for this comparison; it is a direct group comparison. **Output**: `data/reports/rating_results.json`.
- [ ] T039 [US3] Generate `data/reports/analysis_results.json` with all metrics and traceability to raw data.
- [ ] T041 [US3] Generate the final report (`data/reports/final_report.md`).
- [ ] T056a [US3] Calculate statistical power for observed effect sizes. **Output**: `data/reports/power_analysis.json`.
- [ ] T056b [US3] Generate Power Analysis section in the final report.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Validation & Resource Checks

**Purpose**: Verify constraints and perform final checks.

- [ ] T045a [P] Measure Generation Phase metrics (time per repo).

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T046a [P] Update `README.md`.
- [ ] T046b [P] Generate API documentation.
- [ ] T046c [P] CREATE `quickstart.md` ensuring specific script paths match plan.md (e.g., `code/experiment/experiment.py`, `code/generation/doc_pipeline.py`, `code/analysis/analyze.py`). Verification: Assert `quickstart.md` exists and contains correct paths.
- [ ] T048a [P] Remove unused imports with ruff.
- [ ] T048b [P] Run linting with ruff.
- [ ] T049a [P] Implement chunked data loading for memory optimization.
- [ ] T049b [P] Add memory profiling hooks.
- [ ] T050 [P] Add unit tests for dataset schema validation.
- [ ] T051 [P] Add integration tests for documentation generation fallback logic.
- [ ] T052 Run quickstart tests.
- [ ] T053 Verify all artifacts have checksums.

---

## Phase 9: Revision & Correction (Addressing Analysis Findings)

**Purpose**: Address specific issues raised by `/speckit.analyze` regarding data integrity, statistical validity, and execution constraints.

- [ ] T055 [P] Implement hard fail on real data fetch for non-recoverable errors. **Logic**: HTTP xx (4xx) -> Hard Fail. HTTP 5xx (500-599) or timeout > 300s -> Fallback to local model. **Error Format**: Log specific error message `FetchFailed: {status_code} - {message}`. Verification: Assert hard fail occurs on 4xx and fallback occurs on 5xx.
- [ ] T057 [P] Implement Streaming Data Loading for large repositories.
- [ ] T058 [P] Add Data Integrity Checksums to participant log writes.
- [ ] T060 [P] Implement Model Commit Hash Verification before loading local model.
- [ ] T069 [P] Calculate and report Cohen's d effect sizes.

---

## Phase 10: Execution & Pilot Data Collection

**Purpose**: Execute the pilot study with real participants and real data to generate the dataset for analysis.

- [ ] T074 [US1] Run a full dry-run with simulated participants.
- [ ] T075b [US1] Execute real onboarding experiment with recruited participants using the generated documentation from Phase 4. **Input**: `data/raw/llm_docs/`, `data/processed/assignment_log.json` (from T014b). **Dependency**: T076 AND T021f (Gate must pass), T014b. **Data Freshness Check**: Removed. The task verifies the existence of the rubric file but does not enforce a modification time constraint. **Output**: `data/raw/session_logs.json`. Verification: Assert logs contain real timestamps and question counts.
- [ ] T077 [US3] Run Final Analysis.

---

## Phase 11: Final Data Integrity & Reproducibility Audit

**Purpose**: Ensure all data artifacts, model weights, and configuration files meet the strict reproducibility and anti-fabrication standards required for publication.

- [ ] T078 [P] Perform final audit of raw and processed data to verify no synthetic data is present. Verification: Check for specific 'synthetic' markers (e.g., `is_synthetic: true` column) and assert none exist in real data paths.
- [ ] T079 [P] Verify LLM documentation checksums and config logging.
- [ ] T080 [P] Ensure the final report includes limitations (N=15-20).
- [ ] T082 [P] Validate repo matching report consistency with covariates data.

---

## Phase 12: Final Review & Submission

**Purpose**: Final checks before submission.

- [ ] T098 [P] Final Review of all artifacts.
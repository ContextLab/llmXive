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

- [ ] T070 [S] [Phase 0] Generate Statistical Methodology Appendix content in `specs/001-evaluating-the-impact-of-llm-generated-c/research.md`. **Content Requirements**: Must include sections: "1. Pre-specified Analysis Approach (Conditional logic: One-Way ANOVA if variances equal, Welch's ANOVA if unequal, Welch-James/Permutation if non-normal & unequal)", "2. Assumptions (Normality, Homogeneity)", "3. Power Analysis (Variance estimation focus for N=15-20)". **Verification**: Ensure the document is created. This task blocks T070a.

- [ ] T070b [S] [Phase 0] Generate SHA256 hash of `research.md` (from T070) and store it in `state/research_protocol.sha256`. **Verification**: Assert file exists and contains a valid 64-character hex string. This task blocks Phase 1.

- [ ] T070a [S] [Phase 0] Generate `state/citations.yaml`. **Action**: Parse `specs/001-evaluating-the-impact-of-llm-generated-c/research.md` (from T070) and `plan.md` to extract all cited DOIs/URLs. **Input**: T070 output. **Output**: `state/citations.yaml` containing a list of citation objects with `id`, `url`, and `title`. **Verification**: Assert file exists and contains at least one valid entry. **Dependency**: T070.

- [ ] T071a [S] [Phase 0] Implement Reference-Validator Agent logic in `code/utils/validator.py`. **Algorithm**: Fetch primary source metadata via DOI/URL using `requests` for each citation in `state/citations.yaml`. Calculate Jaccard similarity of tokenized titles; threshold ≥ 0.7. **Input**: `state/citations.yaml`. **Output**: Write detailed fetch results and similarity scores to `state/validation_log.json`. **Verification**: Run `tests/unit/test_validator.py` against a sample citation and assert it returns 'valid' or 'invalid' in the log. This task must complete before T071b. **Dependency**: T070a.

- [ ] T071b [S] [Phase 0] Execute the Reference-Validator Agent against `specs/001-evaluating-the-impact-of-llm-generated-c/research.md`. **Dependency**: T071a. **Verification**: Assert `state/validation_log.json` exists, contains 'all_valid' status, and create `state/research_validated.lock`. **Critical Constraint**: If `state/research_validated.lock` is missing after execution, abort the pipeline. This task MUST pass before Phase 1 implementation begins.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, shared utilities, schema definitions, and recruitment tracking setup.

- [ ] T001a [P] [Phase 1] Create project directory structure per implementation plan: `projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/` including `code/`, `data/raw/`, `data/processed/`, `data/reports/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `specs/`. **Versioning**: Generate a content hash (SHA256) of the entire directory tree and update `state/projects/PROJ-274-evaluating-the-impact-of-llm-generated-c.yaml` with this initial hash. Verification: Assert directories exist, hash is recorded, and `state/projects/...yaml` is updated.

- [ ] T001b [S] [Phase 1] Create and run `scripts/verify_structure.py` to assert `os.path.isdir` for `data/raw/`, `code/`, `tests/` and exit with code 0. **Dependency**: T001a.

- [ ] T002 [P] Create `requirements.txt` containing: `requests`, `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `openai`, `transformers`, `llama-cpp-python`, `tiktoken`, `pyyaml`, `psutil`, `gitpython`, `radon`, `cloc`, `jsonschema`, `presidio-analyzer`, `faker` with pinned versions (e.g., `pip freeze` or explicit versions). Verification: Run `pip check` to ensure no conflicts.
- [ ] T004 [P] Implement global random seed pinning in `code/utils/seed.py` to enforce reproducibility. Verification: Assert `numpy.random.seed`, `torch.manual_seed`, and `random.seed` are set to a fixed value (e.g., 42) at the start of every script execution. This task is mandatory for Constitution Principle I.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools by creating `pyproject.toml` with configuration and running `ruff check .` and `black --check .` to ensure exit code 0.
- [ ] T010 [P] Implement active monitoring context manager in `code/utils/monitor.py` using `psutil` and `time` to log peak memory and wall-clock time during execution. (Required for FR-010 and available for all phases).
- [ ] T010b [P] [Phase 1] Initialize Run Metadata. **Action**: Generate `state/run_metadata.json` containing `RUN_ID` (UUID), `start_time`, and `project_version`. **Verification**: Assert file exists and contains valid JSON with `RUN_ID`. This task must run before Phase 2 gates.
- [ ] T030a [P] Generate a JSON Schema based on the data model in `specs/001-evaluating-the-impact-of-llm-generated-c/data-model.md` and save it to `contracts/dataset.schema.json`. Verification: Assert file exists and is valid JSON.
- [ ] T030b [P] Convert the generated JSON Schema from `contracts/dataset.schema.json` to YAML and save as `contracts/dataset.schema.yaml`. Verification: Assert file exists and is valid YAML.
- [ ] T030c [P] Generate `contracts/participant.schema.yaml` specifically for the Participant entity (distinct from dataset schema). **Content**: Fields for `participant_id`, `condition`, `demographic_data`, `timestamps`, `question_count`, `completion_status`. **Verification**: Assert file exists and is valid YAML. **Dependency**: T030a.

- [ ] T073b [S] [Phase 1] Implement Recruitment Tracking System. **Action**: Create `code/recruitment/tracker.py` to manage participant records. Initialize `data/raw/participants_raw.json` with the schema for a **Feasibility Pilot** of **N=15-20 TOTAL participants** (distributed across 3 conditions, approx 5-7 per group). **Constraint**: This task implements the *system* to track recruitment. It does NOT recruit humans. The actual recruitment of human volunteers is a manual external process. The task must explicitly support the total pilot size of N=15-20. **Output**: `data/raw/participants_raw.json` (empty or with placeholder records) and `code/recruitment/tracker.py`. **Verification**: Assert file schema matches `contracts/participant.schema.yaml` (from T030c) and capacity for 20 records. This task must complete before T014. **Dependency**: T030c.

- [ ] T014 [S] [Phase 1] Implement the **Participant Assignment Logic** in `code/experiment/assignment.py`. **Action**: Create a unified function `assign_participants(mode='real' | 'mock')` that handles both real and mock assignment.
    - **Real Mode**: Reads `data/raw/participants_raw.json` (from T073b). Extracts participant IDs. Uses stratified randomization (randomized block design) with seed from `code/utils/seed.py` to assign N=15-20 participants to LLM/Human/None conditions (target N=5-7 per group).
    - **Mock Mode**: Generates a synthetic `data/processed/mock_assignment_log.json` with N=5 simulated participants assigned to conditions.
    - **Output**: `data/processed/assignment_log.json` (real) or `data/processed/mock_assignment_log.json` (mock).
    - **Verification**: Assert the assignment is randomized and balanced across conditions. This task is a prerequisite for T016a (Simulation) and T075b (Real Experiment). **Dependency**: T073b (for real mode), T030c (for schema validation).

---

## Phase 2: Repository Selection & Rubric Validation (Blocking Prerequisite for US2)

**Purpose**: Select repositories and validate human documentation quality per FR-009. This phase MUST complete before US2 (Doc Generation). **Note**: This phase blocks US2 but not US1 implementation.

**⚠️ CRITICAL**: No User Story 2 work can begin until this phase is complete.

- [ ] T020a [P] [Phase 2] Generate `config/candidate_repos.yaml` containing a hardcoded initial list of candidate repositories (URLs) for the pilot study. Verification: Assert file exists and is valid YAML.

- [ ] T021a [P] [Phase 2] Calculate Cyclomatic Complexity for candidate repositories. **Input**: `config/candidate_repos.yaml`. **Tool**: `radon`. **Output**: `data/raw/repo_cc_raw.json` (schema: `{url: {cc: float, files: int}}`). Verification: Assert output file exists and contains CC metrics for all candidates.

- [ ] T021b [P] [Phase 2] Calculate Lines of Code (LOC) for candidate repositories. **Input**: `config/candidate_repos.yaml`. **Tool**: `cloc`. **Output**: `data/raw/repo_loc_raw.json` (schema: `{url: {loc: int, sloc: int}}`). Verification: Assert output file exists and contains LOC metrics for all candidates.

- [ ] T021c [P] [Phase 2] Implement 'high-quality human documentation' rubric in `code/validation.py`. **Input**: `data/raw/repo_readmes/`. **Mechanism**: Use `requests` to fetch raw content from `main` (or `master`). **Criteria**: Presence of Setup, API, and Architecture sections (≥ 3/4 sections). **Method**: Use regex `r'^#{1,2}\\s+(Setup|API|Architecture)'` to search for headers. **Output**: `data/raw/doc_quality_scores.json`. Verification: Assert output file exists and contains scores for all candidates.

- [ ] T021d-1 [S] [Phase 2] Load repository metrics. **Input**: `config/candidate_repos.yaml`, `data/raw/repo_loc_raw.json`, `data/raw/repo_cc_raw.json`, `data/raw/doc_quality_scores.json`. **Output**: `data/raw/repo_metrics_combined.json`. **Dependency**: T021a, T021b, T021c.

- [ ] T021d-2 [S] [Phase 2] Implement repository filtering logic. **Input**: `data/raw/repo_metrics_combined.json`. **Logic**: Filter for high-quality docs, then apply ±15% tolerance on LOC and CC. **Output**: `data/raw/repo_selection_rubric.json` (schema: `{selected_repos: [...], tolerance_check: {loc: bool, cc: bool}}`). **Dependency**: T021d-1.

- [ ] T021d-3 [S] [Phase 2] Write filtered repository selection rubric. **Input**: `data/raw/repo_selection_rubric.json`. **Output**: Persist to `data/raw/repo_selection_rubric.json`. **Dependency**: T021d-2.

- [ ] T021e [S] [Phase 2] Generate `data/raw/repo_covariates.json` by aggregating LOC, CC, and Doc Quality scores for the selected repositories (post-filtering). **Input**: `data/raw/repo_selection_rubric.json`. **Dependency**: T021d-3. **Verification**: Assert file exists and contains the required covariate data.

- [ ] T021f [GATE] [Phase 2] Verify that `repo_selection_rubric.json` confirms all selected repositories meet the ±15% tolerance criteria and high-quality rubric. **Dependency**: T021d-3, T021e, T010b. **Action**: If tolerance check fails, abort the pipeline. **Critical Constraint**: This gate MUST block T076 (Phase 4) and T021e (if it were later). T021e must run AFTER T021d-3 but BEFORE T021f to ensure data is available for the gate. **Verification**: Assert gate passes or pipeline aborts.

---

## Phase 3: User Story 1 - Controlled Onboarding Experiment Execution (Priority: P1) 🎯 MVP

**Goal**: Manage participant assignment, track metrics (time, questions), and handle study session logic.

**Independent Test**: Run a mock study with simulated participants across multiple conditions, verifying that task start/end times are logged, clarification questions are counted, and the study concludes without data loss.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T012 [P] [US1] Contract test for data logging schema in `tests/contract/test_logging_schema.py`
- [ ] T013 [P] [US1] Integration test for full mock participant session in `tests/integration/test_mock_session.py`

### Implementation for User Story 1

- [ ] T017 [US1] Implement subjective helpfulness survey capture in `code/experiment/experiment.py`
- [ ] T016a [S] [US1] Generate `data/raw/chat_transcripts.json` by simulating chat interactions for the **Mock Participants**. **Input**: `data/processed/mock_assignment_log.json` (from T014, Mock Mode). **Dependency**: T014. **Purpose**: This task is for **Simulation/Testing ONLY** to verify the logging pipeline logic. It MUST NOT depend on real recruitment data (T073b). **WARNING**: Ensure no real participant data is mixed into this file. **Output**: `data/raw/chat_transcripts.json`. **Verification**: Assert file exists and contains simulated chat logs for all mock participants.
- [ ] T016b [S] [US1] Implement real-time logging of clarification questions based on FR-004 for **Real Participants**. **Input**: Real-time user input stream from `code/experiment/experiment.py` during T075b. **Implementation**: Define a function `log_clarification(question_text: str, moderator_tag: bool = False)` in `code/experiment/experiment.py`. **Logic**: Filter raw input for keywords ('how', 'why', 'what', 'explain') OR detect moderator tags. **Distinction**: Count ONLY user inputs containing keywords as 'clarification_question'. Classify moderator interventions as 'moderator_action' (do NOT count as questions). **JSON Schema**: `{'event_type': 'clarification'|'moderator_action', 'source': 'keyword'|'moderator', 'text': '...', 'timestamp': 'ISO8601'}`. **Output**: Append to `data/processed/clarification_logs.json`. **Verification**: Assert logs contain both keyword matches and moderator-tagged events and the `clarification_question_count` field matches the array length of 'clarification' events only.
- [ ] T018 [US1] Implement "Stop-Loss" intervention logic: If task time > 2700s (45 min), trigger `trigger_stop_loss()` function, flag record as 'failed', set `intervention_status` = 'stop_loss', and record `max_time` = 2700. **Output**: `data/raw/session_logs.json` with updated fields. Verification: Assert `intervention_status` field is set and `max_time` is 2700 for flagged records.
- [ ] T019 [US1] Handle incomplete records (exclude from analysis, retain for reporting). Flag incomplete records. **Output**: `data/raw/session_logs.json` with status flags. Verification: Assert incomplete records are flagged.
- [ ] T020 [US1] Create raw data export function to `data/raw/session_logs.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Automated Documentation Generation Pipeline (Priority: P2)

**Goal**: Generate consistent, high-quality documentation artifacts from source code using LLMs with fallback logic. **Note**: This phase must complete BEFORE Phase 10 (Experiment).

**Independent Test**: Feed a known small Python utility codebase into the pipeline and verify that the output documentation covers architecture, API usage, and setup instructions without hallucinating non-existent functions.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US2] Contract test for documentation output format in `tests/contract/test_doc_format.py`
- [ ] T026 [P] [US2] Integration test for repo fetch and commit pinning in `tests/integration/test_repo_fetch.py`

### Implementation for User Story 2

- [ ] T028a [S] [Phase 4] Create `config/model_pins.yaml`. **Action**: Use `huggingface_hub` to fetch the latest commit hash for `TheBloke/phi-GGUF` and store it in `config/model_pins.yaml`. **Verification**: Assert file exists and contains a valid 40-character hex hash. **Error Handling**: If fetch fails, raise `ConfigError`.
- [ ] T028a-verify [S] [Phase 4] Verify the commit hash in `config/model_pins.yaml` exists on HuggingFace. **Action**: Use `huggingface_hub` to check the commit. **Verification**: Assert the commit exists. **Dependency**: T028a.
- [ ] T027 [P] [US2] Implement primary LLM API integration for documentation generation in `code/generation/doc_pipeline.py`. **CRITICAL**: Log the specific prompt template version, temperature, and model name used for generation to `data/raw/gen_config.json`. Verification: Assert config file contains these fields.
- [ ] T028 [S] [US2] Implement fallback logic to local CPU-optimized model. **Model Path**: `TheBloke/phi-2-GGUF`. **Configuration**: `load_in_4bit=True`. **Trigger**: HTTP 5xx or latency > 300s. **Logic**: **Load the static commit hash from `config/model_pins.yaml`** (created in T028a). **Error Handling**: If the hash is missing or invalid in the config file, raise `ConfigError` and abort. On HTTP 5xx or latency > 300s, retry 3 times with exponential backoff. If still failing, load the local model. **Verification**: Assert fallback triggers on simulated API failure and uses the static commit hash and 4-bit config. **Dependency**: T028a-verify.
- [ ] T029 [US2] Implement prompt engineering to ensure coverage of architecture, API, and setup steps in `code/generation/doc_pipeline.py`. **CRITICAL**: Log the specific prompt template version and temperature used for generation. Verification: Assert config file contains these fields.
- [ ] T031 [US2] Save generated Markdown docs to `data/raw/llm_docs/` with checksums in `code/generation/doc_pipeline.py`.
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

**Goal**: Aggregate study data, perform statistical analysis, and generate final reports. **Primary Method**: Conditional test selection per FR-005.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T034 [P] [US3] Contract test for analysis output schema in `tests/contract/test_analysis_schema.py`
- [ ] T035 [P] [US3] Integration test for synthetic data analysis pipeline in `tests/integration/test_synthetic_analysis.py`

### Implementation for User Story 3

- [ ] T036a-1 [P] [US3] Implement Levene's test function in `code/analysis/stats_utils.py`. **Logic**: Perform Levene's test for homogeneity of variance. **Constraint**: This is for diagnostics only. **Output**: Log p-value to `data/reports/diagnostics.json`.
- [ ] T036a-2 [P] [US3] Implement Shapiro-Wilk test function in `code/analysis/stats_utils.py`. **Logic**: Perform Shapiro-Wilk test for normality. **Constraint**: This is for diagnostics only. **Output**: Log p-value to `data/reports/diagnostics.json`.
- [ ] T036b [S] [US3] Implement the primary analysis function in `code/analysis/analyze.py`. **Mandatory Logic**:
 1. **Run Diagnostics**: Perform Levene's test and Shapiro-Wilk test (log results to `data/reports/diagnostics.json`).
 2. **Primary Test Selection**:
    - If Levene's p >= 0.05 (variances equal): Perform **One-Way ANOVA**.
    - If Levene's p < 0.05 (variances unequal):
        - If Shapiro-Wilk p < 0.05 (non-normal): Perform **Welch-James** or **Permutation Test**.
        - Else: Perform **Welch's ANOVA**.
 3. **Post-hoc**:
    - If One-Way ANOVA significant: Apply **Tukey HSD**.
    - If Welch's ANOVA significant: Apply **Games-Howell**.
    - If Welch-James/Permutation significant: Apply **Permutation-based CI**.
 4. **Integration**: MUST import and wrap execution in `monitor.py` context manager from T010 to measure time and memory.
 **Dependency**: T036a-1, T036a-2.
 **Output**: `data/reports/primary_analysis_results.json`, `data/reports/diagnostics.json`. Verify results are consistent.
- [ ] T036b-exec [GATE] [Phase 6] Execute T036b-logic. **CRITICAL**: The `state/research_validated.lock` check is handled by Phase 0 gate T071b. This task assumes the project has passed Phase 0. **Verification**: Assert execution time < 6 hours and RAM < 7GB via `data/reports/resource_log.json`. This is implemented by wrapping T036b in the `monitor.py` context manager. If thresholds are exceeded, raise `ConstraintViolationError` and abort. **Dependency**: T036b, T071b.
- [ ] T037d [US3] Perform statistical comparison for SC-002 (Help Requests) using **Conditional Test Selection** (Levene's -> ANOVA/Welch/Welch-James) with appropriate post-hoc correction. **Input**: Clarification question counts from `data/processed/clarification_logs.json`. **Note**: No covariates are used for this comparison; it is a direct group comparison. **Output**: `data/reports/help_request_results.json`.
- [ ] T037e [US3] Perform statistical comparison for SC-003 (Subjective Ratings) using **Conditional Test Selection** (Levene's -> ANOVA/Welch/Welch-James) with appropriate post-hoc correction. **Note**: No covariates are used for this comparison; it is a direct group comparison. **Output**: `data/reports/rating_results.json`.
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

- [ ] T055 [P] Implement hard fail on real data fetch for non-recoverable errors. **Logic**: HTTP 4xx -> Raise `FetchFailedError`. HTTP 5xx or timeout > 300s -> Fallback to local model. **Error Format**: Log specific error message `FetchFailed: {status_code} - {message}`. Verification: Assert hard fail occurs on 4xx and fallback occurs on 5xx.
- [ ] T057 [P] Implement Streaming Data Loading for large repositories.
- [ ] T058 [P] Add Data Integrity Checksums to participant log writes.
- [ ] T060 [P] Implement Model Commit Hash Verification before loading local model.
- [ ] T069 [P] Calculate and report Cohen's d effect sizes.

---

## Phase 10: Execution & Pilot Data Collection

**Purpose**: Execute the pilot study with real participants and real data to generate the dataset for analysis.

- [ ] T074 [US1] Run a full dry-run with simulated participants.
- [ ] T075b [US1] Execute real onboarding experiment with recruited participants using the generated documentation from Phase 4. **Input**: `data/raw/llm_docs/`, `data/processed/assignment_log.json` (from T014, Real Mode). **Dependency**: T076 AND T021f (Gate must pass), T014. **Data Freshness Check**: Removed. The task verifies the existence of the rubric file but does not enforce a modification time constraint. **Output**: `data/raw/session_logs.json`. Verification: Assert logs contain real timestamps and question counts.
- [ ] T077 [US3] Run Final Analysis.

---

## Phase 11: Final Data Integrity & Reproducibility Audit

**Purpose**: Ensure all data artifacts, model weights, and configuration files meet the strict reproducibility and anti-fabrication standards required for publication.

- [ ] T078 [P] Perform final audit of raw and processed data to verify no synthetic data is present. Verification: Check for specific 'synthetic' markers (e.g., `is_synthetic: true` column) and assert none exist in real data paths.
- [ ] T079 [P] Verify LLM documentation checksums and config logging.
- [ ] T080 [P] Ensure the final report includes limitations (N=15-20). **Verification**: Assert the string 'Limitations: N=15-20' is present in `data/reports/final_report.md` (specifically in the 'Study Limitations' section).
- [ ] T082 [P] Validate repo matching report consistency with covariates data.

---

## Phase 12: Final Review & Submission

**Purpose**: Final checks before submission.

- [ ] T098 [P] Final Review of all artifacts.

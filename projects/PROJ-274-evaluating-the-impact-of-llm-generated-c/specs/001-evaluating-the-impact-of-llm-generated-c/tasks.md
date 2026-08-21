# Tasks: Evaluating the Impact of LLM-Generated Code Documentation on Developer Onboarding

**Input**: Design documents from `/specs/001-evaluating-llm-generated-c/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
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

## Phase 0: Research & Data Strategy

**Purpose**: Define statistical methods, data sources, and repository selection criteria. Pre-specify analysis approach to avoid bias.

- [ ] T070 [P] [Phase 0] Generate Statistical Methodology Appendix in `specs/001-evaluating-llm-generated-c/research.md` documenting the pre-specified analysis approach (Levene's -> ANOVA/Welch's -> Games-Howell) and assumptions before any data collection. Verification: Ensure the document is signed off and included in the project's `data/` as a pre-registered protocol.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, and shared utilities.

- [X] T001 Create project structure per implementation plan: `projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/` including `code/`, `data/raw/`, `data/processed/`, `data/reports/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `specs/`. Verification: Run a Python script `scripts/verify_structure.py` that asserts `os.path.isdir` for `data/raw/`, `code/`, `tests/` and exits with code 0.
- [X] T002 Create `requirements.txt` containing: `requests`, `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `openai`, `transformers`, `llama-cpp-python`, `tiktoken`, `pyyaml`, `psutil`, `gitpython`, `radon`, `cloc`, `jsonschema`, `presidio-analyzer`, `faker` with pinned versions (e.g., `pip freeze` or explicit versions). Verification: Run `pip check` to ensure no conflicts.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools by creating `pyproject.toml` with configuration and running `ruff check.` and `black --check.` to ensure exit code 0.
- [X] T010 [P] Implement active monitoring context manager in `code/utils/monitor.py` using `psutil` and `time` to log peak memory and wall-clock time during execution. (Required for FR-010 and available for all phases).

---

## Phase 2: Repository Selection & Rubric Validation (Blocking Prerequisite for US2)

**Purpose**: Select repositories and validate human documentation quality per FR-009. This phase MUST complete before US2 (Doc Generation). **Note**: This phase blocks US2 but not US1 implementation.

**⚠️ CRITICAL**: No User Story 2 work can begin until this phase is complete.

- [X] T047 [P] Consolidate validation logic for repository selection and schema validation into `code/validation.py` to ensure a single source of truth for all validation tasks.
- [ ] T021a [P] [US2] Implement Cyclomatic Complexity (CC) collection in `code/validation.py`: Run `radon cc -a -s` for a list of candidate repositories. **Output**: `data/raw/repo_cc_raw.json`. Verification: Assert file exists and contains numeric CC for each candidate repo.
- [ ] T021b [P] [US2] Implement Lines of Code (LOC) collection in `code/validation.py`: Run `cloc --json` for a list of candidate repositories. **Output**: `data/raw/repo_loc_raw.json`. Verification: Assert file exists and contains numeric LOC for each candidate repo.
- [ ] T021c [P] [US2] Implement Documentation Rubric Scoring in `code/validation.py`: Calculate a quantitative "Human Doc Quality Score" based on the presence of Setup, API, and Architecture sections (binary indicator per section, summed). **Input**: Candidate repo list. **Output**: `data/raw/doc_quality_scores.json`. Verification: Assert file contains scores for each repo.
- [ ] T021d [P] [US2] Filter repositories based on documentation quality: Exclude repositories from `data/raw/doc_quality_scores.json` that do not meet the minimum rubric score criteria defined in FR-009. **Output**: `data/raw/repo_selection_rubric_intermediate.json`. Verification: Assert file exists and contains only repos meeting the rubric.
- [ ] T021f [P] [US2] Filter repositories based on metric thresholds: Compare LOC/CC from `data/raw/repo_loc_raw.json` and `data/raw/repo_cc_raw.json` against the median metrics of the initial candidate pool (baseline) and exclude repos failing the ±15% tolerance. **Output**: `data/raw/repo_selection_rubric.json` (final accepted repos) AND `data/raw/repo_matching_report.json`. Verification: Assert file exists and contains accepted repos with matching metrics.
- [ ] T021g [P] [US2] Aggregate LOC, CC, and Doc Quality scores into a single covariate dataset for statistical adjustment (ANCOVA). **Input:** `data/raw/repo_loc_raw.json`, `data/raw/repo_cc_raw.json`, and `data/raw/doc_quality_scores.json`. **Output**: `data/raw/repo_covariates.json`. Verification: Assert file exists and contains normalized/centered covariates for accepted repos.

---

## Phase 3: User Story 1 - Controlled Onboarding Experiment Execution (Priority: P1) 🎯 MVP

**Goal**: Manage participant assignment, track metrics (time, questions), and handle study session logic.

**Independent Test**: Run a mock study with simulated participants across multiple conditions, verifying that task start/end times are logged, clarification questions are counted, and the study concludes without data loss.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T012 [P] [US1] Contract test for data logging schema in `tests/contract/test_logging_schema.py`
- [X] T013 [P] [US1] Integration test for full mock participant session in `tests/integration/test_mock_session.py`

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement participant assignment logic (randomized to LLM/Human/None) in `code/experiment/experiment.py`
- [ ] T016 [US1] Implement real-time logging of clarification questions based on FR-004: filter for keywords (e.g., 'how', 'why') OR moderator tags via the `experiment.py` chat interface. Log timestamp, content, and type (keyword/modeerator-tag). **Simultaneously calculate the count per session**. **Output**: `data/raw/participant_logs.json` with `clarification_questions` array and `clarification_question_count` field. Verification: Assert logs contain both keyword matches and moderator-tagged events, and the count field matches the array length.
- [ ] T017 [US1] Implement subjective helpfulness survey capture in `code/experiment/experiment.py`
- [ ] T018 [US1] Implement "Stop-Loss" intervention logic: If task time > 2700s (45 min), trigger moderator intervention, flag record as 'failed', set `intervention_status` = 'stop_loss', and record `max_time` = 2700. **Output**: `data/raw/participant_logs.json` with updated fields. Verification: Assert `intervention_status` field is set and `max_time` is 2700 for flagged records.
- [ ] T019 [US1] Handle incomplete records (exclude from analysis, retain for reporting). Calculate dropout count. **Output**: `data/raw/participant_logs.json` with status flags.
- [ ] T020 [US1] Create raw data export function to `data/raw/participant_logs.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Automated Documentation Generation Pipeline (Priority: P2)

**Goal**: Generate consistent, high-quality documentation artifacts from source code using LLMs with fallback logic.

**Independent Test**: Feed a known small Python utility codebase into the pipeline and verify that the output documentation covers architecture, API usage, and setup instructions without hallucinating non-existent functions.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US2] Contract test for documentation output format in `tests/contract/test_doc_format.py`
- [X] T026 [P] [US2] Integration test for repo fetch and commit pinning in `tests/integration/test_repo_fetch.py`

### Implementation for User Story 2

- [ ] T027 [P] [US2] Implement primary LLM API integration for documentation generation in `code/generation/doc_pipeline.py`.
- [ ] T028 [US2] Implement fallback logic to local CPU-optimized model ('phi (quantized int4)') if the API fails, pinned to a specific HuggingFace commit hash. Log generation config and checksums.
- [ ] T029 [US2] Implement prompt engineering to ensure coverage of architecture, API, and setup steps in `code/generation/doc_pipeline.py`.
- [ ] T031 [US2] Save generated Markdown docs to `data/raw/llm_docs/` with checksums in `code/generation/doc_pipeline.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: Data Processing & Contract Validation

**Purpose**: Clean, anonymize, and validate data before analysis. Produces `cleaned_dataset.csv` for Phase 6.

- [ ] T030a [P] Generate a JSON Schema based on the data model in `data-model.md` and save it to `data/raw/schema_temp.json`. Verification: Assert file exists and is valid JSON.
- [ ] T030b [P] Convert the generated JSON Schema from `data/raw/schema_temp.json` to YAML and save as `contracts/dataset.schema.yaml`. Verification: Assert file exists and is valid YAML.
- [ ] T033 [P] Run schema validation against `contracts/dataset.schema.yaml`. Abort pipeline if validation fails.
- [ ] T032a [US1/3] Implement PII removal using `presidio-analyzer`.
- [ ] T032b [US1/3] Handle incomplete records during data cleaning.
- [ ] T032 [US1/3] Aggregate cleaning steps to produce `data/processed/cleaned_dataset.csv`.
- [ ] T016b [US1/3] [REMOVED] Task removed. Clarification question counts are now calculated in T016.

**Checkpoint**: Cleaned dataset ready for analysis.

---

## Phase 6: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Aggregate study data, perform statistical analysis, and generate final reports.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T034 [P] [US3] Contract test for analysis output schema in `tests/contract/test_analysis_schema.py`
- [X] T035 [P] [US3] Integration test for synthetic data analysis pipeline in `tests/integration/test_synthetic_analysis.py`

### Implementation for User Story 3

- [ ] T036a [P] Load and center the covariates (LOC, CC, Doc Quality) from `data/raw/repo_covariates.json`. **Output**: `data/processed/centered_covariates.json`, `data/processed/centered_dataset.csv`.
- [ ] T036b [P] Implement the Spec FR-005 Dynamic Decision Tree: Levene's test -> ANOVA/Welch's/Welch-James with appropriate post-hoc tests. **PRIMARY PATH**: Robust Tests (Welch's/Welch-James) are the default to avoid bias. **Output**: `data/reports/primary_analysis_results.json`. Verify results are consistent.
- [ ] T037 [US3] Implement post-hoc tests (Games-Howell). **Output**: `data/reports/posthoc_results.json`.
- [ ] T037d [US3] Perform statistical comparison for SC-002 (Help Requests) using ANCOVA and Games-Howell correction. **Input**: Clarification question counts from `data/raw/participant_logs.json` (T016). **Output**: `data/reports/help_request_results.json`.
- [ ] T037e [US3] Perform statistical comparison for SC-003 (Subjective Ratings) using ANCOVA and Games-Howell correction. **Output**: `data/reports/rating_results.json`.
- [ ] T039 [US3] Generate `data/reports/analysis_results.json` with all metrics and traceability to raw data.
- [ ] T041 [US3] Generate the final report (`data/reports/final_report.md`).
- [ ] T056a [US3] Calculate statistical power for observed effect sizes. **Output**: `data/reports/power_analysis.json`.
- [ ] T056b [US3] Generate Power Analysis section in the final report.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Validation & Resource Checks

**Purpose**: Verify constraints and perform final checks.

- [ ] T044 [P] Verify Analysis Phase execution time < 6 hours and RAM < 7GB using active monitoring (T010).
- [ ] T045a [P] Measure Generation Phase metrics (time per repo).
- [ ] T045b [P] Create Resource Stress Test Script.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T046a [P] Update `README.md`.
- [ ] T046b [P] Generate API documentation.
- [ ] T046c [P] CREATE `quickstart.md` ensuring specific script paths match plan.md (e.g., `code/experiment/experiment.py`, `code/generation/doc_pipeline.py`, `code/analysis/stats_runner.py`). Verification: Assert `quickstart.md` exists and contains correct paths.
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

- [ ] T055 [P] Implement hard fail on real data fetch AND preserve fallback to local model for FR-008 compliance.
- [ ] T057 [P] Implement Streaming Data Loading for large repositories.
- [ ] T058 [P] Add Data Integrity Checksums to participant log writes.
- [ ] T060 [P] Implement Model Commit Hash Verification before loading local model.
- [ ] T069 [P] Calculate and report Cohen's d effect sizes.

---

## Phase 10: Execution & Pilot Data Collection

**Purpose**: Execute the pilot study with real participants and real data to generate the dataset for analysis.

- [ ] T073a [US1] Mock Recruitment: Generate `data/raw/mock_participants.csv` using Faker library with N=15-20 rows. Verification: Assert file exists and contains 15-20 rows with required demographic columns.
- [ ] T074 [US1] Run a full dry-run with simulated participants.
- [ ] T075a [US1] Execute mock onboarding experiment with simulated participants.
- [ ] T076 [US2] Generate documentation for selected repositories.
- [ ] T077 [US3] Run Final Analysis.

---

## Phase 11: Final Data Integrity & Reproducibility Audit

**Purpose**: Ensure all data artifacts, model weights, and configuration files meet the strict reproducibility and anti-fabrication standards required for publication.

- [ ] T078 [P] Perform final audit of raw and processed data to verify no synthetic data is present.
- [ ] T079 [P] Verify LLM documentation checksums and config logging.
- [ ] T080 [P] Ensure the final report includes limitations (N=15-20).
- [ ] T082 [P] Validate repo matching report consistency with covariates data.

---

## Phase 12: Execution Simulation & Resource Stress Testing (Revision Concern: FR-007 & FR-010)

**Purpose**: Validate adherence to resource constraints and the "GPU escape hatch."

- [ ] T087 [P] Create a Resource Stress Test Script.
- [ ] T088 [P] Implement GPU Offload Detection Logic.
- [ ] T089 [P] Add Memory Profiling Hook.
- [ ] T090 [P] Generate Resource Constraint Compliance Report.

---

## Phase 13: Advanced Statistical Robustness & Sensitivity (Revision Concern: FR-005 & Power)

**Purpose**: Validate robustness and address the underpowered nature of the pilot study.

- [ ] T083 [P] Implement Permutation Test for robustness.
- [ ] T084 [P] Generate Bootstrap Confidence Intervals.
- [ ] T085 [P] Run sensitivity analysis with covariate inclusion/exclusion.

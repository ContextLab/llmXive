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

- [ ] T070 [GATE] [Phase 0] Generate Statistical Methodology Appendix in `specs/001-evaluating-llm-docs-impact/research.md` documenting the pre-specified analysis approach (Levene's -> ANOVA/Welch's -> Games-Howell) and assumptions before any data collection. Verification: Ensure the document is signed off by storing its SHA256 hash in `state/research_protocol.sha256`. This task blocks Phase 6.

- [ ] T071a [P] [Phase 0] Implement Reference-Validator Agent logic in `code/utils/validator.py` to check citations against primary sources (URL reachability, title overlap ≥ 0.7) before analysis. Verification: Run against a sample citation and assert it returns 'valid' or 'invalid'. This task must run before Phase 1 implementation begins.

- [ ] T071b [GATE] [Phase 0] Execute the Reference-Validator Agent against the generated `specs/001-evaluating-llm-docs-impact/research.md` file to verify all citations. Verification: Assert the validator returns 'all_valid' and a lock file `state/research_validated.lock` is created. This task MUST pass before Phase 1 implementation begins.

- [ ] T071c [GATE] [Phase 0] Implement the 'Verified Accuracy Gate' logic in `code/utils/gate.py` to block analysis execution if `state/research_validated.lock` is missing or stale. Verification: Attempt to run `code/analysis/stats_runner.py` without the lock and assert it raises a `GateError`. This task ensures Constitution Principle II compliance.

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

- [ ] T020a [P] [Phase 2] Generate `config/candidate_repos.yaml` containing a hardcoded initial list of 10-15 candidate repositories (URLs) for the pilot study. Verification: Assert file exists and is valid YAML.
- [ ] T021 [Prerequisite] [Phase 2] Implement Repository Selection Pipeline in `code/validation.py`:
    1. Read candidate repos from `config/candidate_repos.yaml`.
    2. Run `radon cc -a -s` for each repo (output `data/raw/repo_cc_raw.json`).
    3. Run `cloc --json` for each repo (output `data/raw/repo_loc_raw.json`).
    4. Calculate "Human Doc Quality Score" based on Setup/API/Arch sections (output `data/raw/doc_quality_scores.json`).
    5. Filter repos based on rubric (output `data/raw/repo_selection_rubric_intermediate.json`).
    6. Filter repos based on LOC/CC metrics (±15% tolerance) (output `data/raw/repo_selection_rubric.json` and `data/raw/repo_matching_report.json`).
    7. Aggregate LOC, CC, and Doc Quality scores into `data/raw/repo_covariates.json` for ANCOVA.
    Verification: Assert all output files exist and contain correct data. This task blocks Phase 6.

---

## Phase 3: User Story 1 - Controlled Onboarding Experiment Execution (Priority: P1) 🎯 MVP

**Goal**: Manage participant assignment, track metrics (time, questions), and handle study session logic.

**Independent Test**: Run a mock study with simulated participants across multiple conditions, verifying that task start/end times are logged, clarification questions are counted, and the study concludes without data loss.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T012 [P] [US1] Contract test for data logging schema in `tests/contract/test_logging_schema.py`
- [X] T013 [P] [US1] Integration test for full mock participant session in `tests/integration/test_mock_session.py`

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement participant assignment logic (randomized to LLM/Human/None) in `code/experiment/experiment.py`
- [ ] T016 [US1] Implement real-time logging of clarification questions based on FR-004: filter for keywords (e.g., 'how', 'why', 'what', 'explain') OR moderator tags (specific JSON event type `{'type': 'moderator_tag'}` injected via `experiment.py` chat interface). Log timestamp, content, and type (keyword/modeerator-tag) to `data/raw/participant_logs.json` in an array named `clarification_questions`. **Do NOT calculate the count here**; only log raw events. Verification: Assert logs contain both keyword matches and moderator-tagged events (identified by `type: moderator_tag`) and the array is populated.
- [X] T017 [US1] Implement subjective helpfulness survey capture in `code/experiment/experiment.py`
- [ ] T018 [US1] Implement "Stop-Loss" intervention logic: If task time > 2700s (45 min), trigger moderator intervention, flag record as 'failed', set `intervention_status` = 'stop_loss', and record `max_time` = 2700. **Output**: `data/raw/participant_logs.json` with updated fields. Verification: Assert `intervention_status` field is set and `max_time` is 2700 for flagged records.
- [ ] T019 [US1] Handle incomplete records (exclude from analysis, retain for reporting). **Aggregation**: Calculate `clarification_question_count` by counting items in the `clarification_questions` array from T016. Flag incomplete records. **Output**: `data/raw/participant_logs.json` with status flags and the calculated count field. Verification: Assert `clarification_question_count` matches the length of the `clarification_questions` array and incomplete records are flagged.
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

- [X] T027 [P] [US2] Implement primary LLM API integration for documentation generation in `code/generation/doc_pipeline.py`.
- [ ] T028 [US2] Implement fallback logic to local CPU-optimized model ('microsoft/phi-2', quantized int4) if the API fails (HTTP 5xx or latency > 300s). Pin to HuggingFace commit hash `d5e5263`. Log generation config and checksums. Verification: Assert fallback triggers on simulated API failure and uses the specified commit hash.
- [X] T029 [US2] Implement prompt engineering to ensure coverage of architecture, API, and setup steps in `code/generation/doc_pipeline.py`.
- [X] T031 [US2] Save generated Markdown docs to `data/raw/llm_docs/` with checksums in `code/generation/doc_pipeline.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: Data Processing & Contract Validation

**Purpose**: Clean, anonymize, and validate data before analysis. Produces `cleaned_dataset.csv` for Phase 6.

- [ ] T030a [P] Generate a JSON Schema based on the data model in `specs/001-evaluating-llm-docs-impact/data-model.md` and save it to `data/raw/schema_temp.json`. Verification: Assert file exists and is valid JSON.
- [ ] T030b Convert the generated JSON Schema from `data/raw/schema_temp.json` to YAML and save as `contracts/dataset.schema.yaml`. Verification: Assert file exists and is valid YAML.
- [ ] T033 [P] Run schema validation against `contracts/dataset.schema.yaml`. Abort pipeline if validation fails.
- [ ] T032a [US1/3] Implement PII removal using `presidio-analyzer`.
- [ ] T032b [US1/3] Handle incomplete records during data cleaning.
- [ ] T032 [US1/3] Aggregate cleaning steps to produce `data/processed/cleaned_dataset.csv`.

**Checkpoint**: Cleaned dataset ready for analysis.

---

## Phase 6: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Aggregate study data, perform statistical analysis, and generate final reports.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T034 [P] [US3] Contract test for analysis output schema in `tests/contract/test_analysis_schema.py`
- [X] T035 [P] [US3] Integration test for synthetic data analysis pipeline in `tests/integration/test_synthetic_analysis.py`

### Implementation for User Story 3

- [ ] T036a Load and center the covariates (LOC, CC, Doc Quality) from `data/raw/repo_covariates.json`. **Output**: `data/processed/centered_covariates.json`, `data/processed/centered_dataset.csv`.
- [ ] T036b [P] Implement the Spec FR-005 Dynamic Decision Tree: Levene's test -> ANOVA/Welch's/Welch-James with appropriate post-hoc tests. **PRIMARY PATH**: Robust Tests (Welch's/Welch-James) are the default to avoid bias. **CRITICAL**: This script MUST be wrapped in the `monitor.py` context manager (T010) during execution to log real-time resource usage. **Output**: `data/reports/primary_analysis_results.json`. Verify results are consistent.
- [ ] T036b-exec [GATE] [Phase 6] Execute T036b using the `monitor.py` context manager to verify execution time < 6 hours and RAM < 7GB on the actual data path. **This is the primary gate for FR-007/SC-005**. Verification: Assert `data/reports/resource_log.json` exists and shows compliance. If it fails, abort the pipeline.
- [ ] T037 [US3] Implement post-hoc tests (Games-Howell). **Output**: `data/reports/posthoc_results.json`.
- [ ] T037d [US3] Perform statistical comparison for SC-002 (Help Requests) using ANCOVA and Games-Howell correction. **Input**: Clarification question counts from `data/raw/participant_logs.json` (aggregated in T019). **Output**: `data/reports/help_request_results.json`.
- [ ] T037e [US3] Perform statistical comparison for SC-003 (Subjective Ratings) using ANCOVA and Games-Howell correction. **Output**: `data/reports/rating_results.json`.
- [ ] T039 [US3] Generate `data/reports/analysis_results.json` with all metrics and traceability to raw data.
- [ ] T041 [US3] Generate the final report (`data/reports/final_report.md`).
- [ ] T056a [US3] Calculate statistical power for observed effect sizes. **Output**: `data/reports/power_analysis.json`.
- [ ] T056b [US3] Generate Power Analysis section in the final report.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Validation & Resource Checks

**Purpose**: Verify constraints and perform final checks.

- [ ] T045a [P] Measure Generation Phase metrics (time per repo).
- [ ] T045b [P] [REMOVED] Task merged into T087 (Stress Test).

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

- [ ] T055 [P] Implement hard fail on real data fetch for non-recoverable errors (e.g., 4xx, local model load failure) AND preserve fallback to local model for FR-008 compliance (API 5xx/timeout). Verification: Assert hard fail occurs on 4xx and fallback occurs on 5xx.
- [ ] T057 [P] Implement Streaming Data Loading for large repositories.
- [ ] T058 [P] Add Data Integrity Checksums to participant log writes.
- [ ] T060 [P] Implement Model Commit Hash Verification before loading local model.
- [ ] T069 [P] Calculate and report Cohen's d effect sizes.

---

## Phase 10: Execution & Pilot Data Collection

**Purpose**: Execute the pilot study with real participants and real data to generate the dataset for analysis.

- [ ] T073a [US1] Mock Recruitment: Generate `data/raw/mock_participants.csv` using Faker library. Randomly sample N=18 rows using SEED=42. Verification: Assert file exists and contains exactly 18 rows with required demographic columns.
- [ ] T074 [US1] Run a full dry-run with simulated participants.
- [ ] T075a [US1] Execute mock onboarding experiment with simulated participants.
- [ ] T076 [US2] Generate documentation for selected repositories.
- [ ] T077 [US3] Run Final Analysis.

---

## Phase 11: Final Data Integrity & Reproducibility Audit

**Purpose**: Ensure all data artifacts, model weights, and configuration files meet the strict reproducibility and anti-fabrication standards required for publication.

- [ ] T078 [P] Perform final audit of raw and processed data to verify no synthetic data is present. Verification: Check for specific 'synthetic' markers (e.g., `is_synthetic: true` column) and assert none exist in real data paths.
- [ ] T079 [P] Verify LLM documentation checksums and config logging.
- [ ] T080 [P] Ensure the final report includes limitations (N=15-20).
- [ ] T082 [P] Validate repo matching report consistency with covariates data.

---

## Phase 12: Execution Simulation & Resource Stress Testing (Revision Concern: FR-007 & FR-010)

**Purpose**: Validate adherence to resource constraints and the "GPU escape hatch."

- [ ] T087 [P] Create a Resource Stress Test Script that simulates high-load data processing (synthetic data) to verify system stability under extreme conditions, distinct from the real-data constraint check in T036b-exec. Verification: Assert script runs and reports memory/CPU usage under synthetic load.

---

## Phase 13: Advanced Statistical Robustness & Sensitivity (Revision Concern: FR-005 & Power)

**Purpose**: Validate robustness and address the underpowered nature of the pilot study.

- [ ] T083 [P] Implement Permutation Test for robustness.
- [ ] T084 [P] Generate Bootstrap Confidence Intervals.
- [ ] T085 [P] Run sensitivity analysis with covariate inclusion/exclusion.

---

## Phase 14: Final Review & Submission

**Purpose**: Final checks before submission.

- [ ] T099 [P] [REMOVED] Task moved to Phase 0 (T071b) to ensure pre-analysis validation.
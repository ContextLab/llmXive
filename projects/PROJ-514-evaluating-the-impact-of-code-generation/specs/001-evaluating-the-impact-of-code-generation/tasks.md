# Tasks: Evaluating Code Generation Impact on Code Smell Frequency

**Input**: Design documents from `/specs/001-code-smell-comparison/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are MANDATORY to define interfaces before implementation.

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan: `mkdir -p code/01_data_collection code/02_static_analysis code/03_statistical_analysis code/04_reporting code/utils tests/contract tests/integration tests/unit data/raw/human_samples data/raw/llm_samples data/intermediate data/processed reports specs/001-code-smell-comparison`
- [X] T002 Initialize Python project with `code/requirements.txt`: Pin dependencies to exact versions for reproducibility (e.g., `requests==2.31.0`, `GitPython==3.1.40`, `pandas==2.2.1`, `scipy==1.13.0`, `matplotlib==3.9.0`, `pyyaml==6.0.1`, `pytest==8.2.0`).
- [ ] T003 [P] Configure linting (ruff/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup environment configuration management (`code/utils/config.py` for seeds, paths, timeouts, API keys)
- [X] T005 [P] Implement logging infrastructure (`code/utils/logger.py`) to track commit SHAs, Issue URLs, and API responses
- [ ] T006 [P] Setup data directory structure (`data/raw/human_samples`, `data/raw/llm_samples`, `data/intermediate`, `data/processed`)
- [X] T007 Create base data models (`code/utils/data_models.py`) defining:
 - `class CodeSample`: attributes `source_type`, `repository_id`, `issue_id`, `task_id`, `language`, `file_path`, `function_name`, `is_fresh_commit`.
 - `class SmellMetric`: attributes `sample_id`, `smell_type`, `count`, `threshold_used`, `continuous_metric_value`.
 - `class StatResult`: attributes `smell_type`, `p_value`, `effect_size`, `confidence_interval`, `correction_method`, `test_method_used`.
- [X] T008 Implement syntax validation utility (`code/utils/validators.py`) for Python/Java file integrity checks
- [X] T009 Setup CI environment check for PMD/JRE availability (Dockerfile or CI script to install PMD CLI)

---

## Phase 3: User Story 1 - Data Collection & Sample Preparation (Priority: P1) 🎯 MVP

**Goal**: Collect a balanced dataset of human-written and LLM-generated code samples from multiple repositories (multiple samples per source per repo) to ensure statistical validity and repository-level matching. **Note**: This implements the "Balanced Blocked Design" from plan.md.

**Independent Test**: Verify the existence of `data/raw/human_samples` and `data/raw/llm_samples` containing a representative set of files each, with `data/raw/api_logs.json` logging the source repository, Issue/PR ID, Task ID, and exact commit SHA for every sample.

### Tests for User Story 1 (MANDATORY - Interface Definition)

> **NOTE**: These contract tests define the interface for the implementation. They must be written FIRST to define the expected behavior, even if they fail to import unimplemented modules.

- [X] T010 [US1] Contract test for repository selection logic in `tests/contract/test_repo_selection.py` (Defines interface for T012)
- [X] T011 [US1] Contract test for LLM generation logic in `tests/contract/test_llm_generation.py` (Defines interface for T013)

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/01_data_collection/fetch_human_samples.py`:
 - **Algorithm**: Query GitHub API for 50 public repos with `stars:>100` AND `pushed:>2022-01-01` (ensure active repos with fresh commits) AND `created:<2019-01-01` (ensure 5+ years history).
 - **Freshness Logic**: For each selected repo, use `git log --diff-filter=A --format="%H" -- "*.py" "*.java"` to find commits that *added* functions.
 - **Selection**: Select the **most recent commits per repo** that added a.py or.java file.
 - **Extraction**: Extract the function code from each commit. Save to `data/raw/human_samples/` with metadata JSON sidecars containing `repo_id`, `commit_sha`, `issue_id` (if linked), `issue_url` (full URL), `file_path`, `function_name`.
 - **Constraint**: Total samples collected (3 per repository across 50 repositories) [UNRESOLVED-CLAIM: c_55472511 — status=not_enough_info].
 - **Logging**: Log every sample's `commit_sha`, `repo_id`, and `issue_url` to `data/raw/api_logs.json`.
 - **Traceability**: Ensure `issue_url` is logged to satisfy Constitution Principle II (Verified Accuracy).
- [ ] T012.5 [US1] Implement `code/01_data_collection/export_task_descriptions.py`:
 - **Purpose**: Extract Issue/PR descriptions from the metadata collected in T012 to create a structured task list for LLM generation.
 - **Input**: Read `data/raw/api_logs.json` and `data/raw/human_samples/` metadata.
 - **Output**: Generate `data/intermediate/tasks.json` containing `task_id`, `issue_url`, `description_text`, `language`, `repo_id`.
 - **Dependency**: Must run after T012 completes.
- [X] T013 [US1] Implement `code/01_data_collection/generate_llm_samples.py`:
 - **Task Derivation**: Derive a set of coding tasks from the same Issue/PR descriptions used for human samples (read from `data/intermediate/tasks.json` produced by T012.5).
 - **Generation**: Query HuggingFace Inference API (or similar) with a reasonable timeout and exponential backoff (3 retries).
 - **Sampling**: **Generate 3 samples per task** (Total 150 samples across 50 tasks).
 - **Storage**: Save files to `data/raw/llm_samples/` with metadata JSON sidecars containing `task_id`, `model_id`, `model_version`, `api_endpoint`, `exact_prompt`, `prompt_hash`, `generation_seed`.
 - **Traceability**: Ensure full metadata schema (model_id, version, endpoint, prompt, seed) is logged to satisfy Constitution Principle VI (Code Generation Transparency).
- [X] T014 [US1] Implement `code/01_data_collection/validate_dataset.py`:
 - **Validation**: Run syntax validation on all samples using `code/utils/validators.py`.
 - **Action**: Log and exclude samples failing validation. **Do not impose a hard threshold** (e.g., 95%); simply report the final count of valid samples in the report.
 - **Reporting**: Generate `data/intermediate/validation_report.json` listing excluded samples, reasons, and the final count of valid samples.
 - **Constraint**: If valid count is critically low, flag for manual review, but do not auto-halt based on an arbitrary percentage.
- [X] T015 [US1] Implement `code/01_data_collection/export_manifest.py`:
 - **Manifest**: Generate `data/raw/manifest.csv` with columns: `sample_id`, `source_type`, `repository_id`, `issue_id`, `task_id`, `commit_sha`, `file_path`, `language`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Static Analysis Execution (Priority: P2)

**Goal**: Run CPU-tractable static analysis (PMD/SonarQube CLI) on a representative set of samples to extract metrics for four code smell categories (Long Method, Duplicated Code, Feature Envy, Long Parameter List) within CI limits.

**Independent Test**: Run the analysis pipeline on a subset of samples and verify `data/intermediate/analysis_results.json` contains smell counts for all four categories and a tool-validity flag.

### Tests for User Story 2 (MANDATORY - Interface Definition)

- [ ] T019 [US2] Contract test for PMD CLI wrapper in `tests/contract/test_pmd_wrapper.py`:
 - **Interface**: Define tests for `run_pmd(file_path, ruleset_path)` returning `exit_code` and `stdout`.
 - **Interface**: Define tests for `parse_output(xml_content)` returning a list of `SmellMetric` objects.
 - **Constraint**: Must handle timeout and memory limit errors gracefully.
- [X] T020 [US2] Contract test for parallel analysis execution in `tests/contract/test_static_analysis_interface.py` (Defines interface for T021/T023)

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/02_static_analysis/run_pmd.py`:
 - **Wrapper**: Subprocess wrapper to execute PMD CLI with specific rulesets for `LongMethod`, `DuplicatedCode`, `FeatureEnvy`, `LongParameterList`.
 - **Limits**: Enforce per-process memory limit (≤2 GB) and 2-minute timeout per file [UNRESOLVED-CLAIM: c_8e7768dd — status=not_enough_info].
 - **Error Handling**: Log syntax errors and PMD crashes; exclude from analysis.
 - **Output**: Return raw PMD XML/JSON output.
- [ ] T022 [US2] Implement `code/02_static_analysis/parse_results.py`:
 - **Parser**: Parse PMD XML/JSON output into `data/intermediate/analysis_results.json`.
 - **Dependency**: Must run after T021 completes.
 - **Mapping**: Map smells to `SmellMetric` entities.
- [ ] T022.5 [US2] Implement `code/02_static_analysis/generate_reference_set.py`:
 - **Purpose**: Generate or locate a known "clean" reference set for tool validity testing.
 - **Action**: Create a set of pre-validated clean code files (Python/Java) with known zero smells, or fetch a verified subset from a trusted source.
 - **Output**: Save to `data/raw/reference_set/`.
 - **Dependency**: Must run before T023.
- [ ] T023 [US2] Implement `code/02_static_analysis/tool_validity_check.py`:
 - **Validity**: Run analysis on the "clean" reference set produced by T022.5 (`data/raw/reference_set/`).
 - **Threshold**: Calculate false-positive rate. If >5%, flag tool configuration as invalid in logs.
 - **Traceability**: Explicitly reference **Spec FR-005** for tool validity.
 - **Dependency**: Must run after T022 and T022.5 complete.
 - **Output**: Generate `data/intermediate/tool_validity_status.json` with keys `is_valid` (boolean) and `false_positive_rate` (float).
- [ ] T024 [US2] Implement `code/02_static_analysis/aggregate_metrics.py`:
 - **Aggregation**: Aggregate results into `data/processed/smell_metrics.csv` with columns: `sample_id`, `source_type`, `smell_type`, `count`, `continuous_metric_value` (e.g., cyclomatic complexity).
 - **Dependency**: Must run after T022 and T023 (validity check) complete.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison & Reporting (Priority: P3)

**Goal**: Generate a final report comparing smell frequencies using a Blocked Permutation Test (repository as block), applying Bonferroni correction, and performing sensitivity analysis on the "Long Method" threshold. **Note**: This implements the "Blocked Permutation Test" from plan.md.

**Independent Test**: Generate the final report and verify it contains statistical tables with corrected p-values, effect sizes, box plots, and explicitly uses associational language.

### Tests for User Story 3 (MANDATORY - Interface Definition)

- [ ] T025 [US3] Contract test for permutation test logic in `tests/contract/test_permutation_test_interface.py` (Defines interface for T027)
- [ ] T026 [US3] Contract test for report generation in `tests/contract/test_report_interface.py` (Defines interface for T029)

### Implementation for User Story 3

- [ ] T027 [US3] Implement `code/03_statistical_analysis/compare_distributions.py`:
 - **Method**: Implement Blocked Permutation Test (stratified by repository) per plan.md.
 - **Handling**: Handle zero-inflation and non-normality by using exact permutation counts.
 - **Correction**: Apply **Bonferroni correction for the 4 hypothesis tests** to control family-wise error rate (α ≤ 0.05).
 - **Metrics**: Calculate effect sizes (Cohen's d or equivalent for permutation tests).
 - **Output**: Save results to `data/intermediate/stat_results.json`.
- [ ] T028 [US3] Implement `code/03_statistical_analysis/sensitivity_analysis.py`:
 - **Sweep**: Sweep "Long Method" threshold values across a specific range: **[, 30, 40, 50, 60] lines**.
 - **Comparison**: Compare results against continuous metrics (cyclomatic complexity) to verify stability.
 - **Dependency**: Must run after T027 completes.
 - **Output**: Generate `data/intermediate/sensitivity_analysis_report.json` with threshold vs. p-value tables.
- [ ] T029 [US3] Implement `code/04_reporting/generate_report.py`:
 - **Inputs**: Read from `data/processed/smell_metrics.csv`, `data/intermediate/stat_results.json`, `data/intermediate/sensitivity_analysis_report.json`.
 - **Template**: Use `templates/final_report_template.md`.
 - **Content**: Include Introduction, Methodology (Blocked Permutation Test), Results (Statistical Tables with corrected p-values, effect sizes), Sensitivity Analysis, Conclusion.
 - **Visuals**: Include box plots comparing distributions and continuous metric comparisons.
 - **Language**: Enforce associational language (e.g., "associated with", "correlated with") and exclude causal claims.
 - **Output**: Generate `reports/final_study_report.md`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `specs/001-code-smell-comparison/research.md`
- [ ] T031 Code cleanup and refactoring
- [ ] T032 Performance optimization (ensure total CI job ≤ 2 hours with 20 parallel jobs [UNRESOLVED-CLAIM: c_43add690 — status=not_enough_info])
- [ ] T033 [P] Additional unit tests in `tests/unit/`
- [ ] T034 Run `quickstart.md` validation to ensure reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires valid data from US1
 - **T012.5** depends on T012.
 - **T013** depends on T012.5.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires valid metrics from US2
 - **T022.5** depends on T007 (models).
 - **T023** depends on T022 and T022.5.
 - **T027** depends on T024.

### Within Each User Story

- Tests (T010-T011, T019-T020, T025-T026) define interfaces and must be written before implementation tasks.
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel (if interface defined)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

### Explicit Model Dependencies

- **T007** (Data Models) must complete before:
 - **T014** (Validation)
 - **T021** (PMD Wrapper)
 - **T022** (Parser)
 - **T023** (Validity Check)
 - **T024** (Aggregation)
 - **T027** (Statistics)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (Interface Definition):
Task: "Contract test for repository selection logic in tests/contract/test_repo_selection.py"
Task: "Contract test for LLM generation logic in tests/contract/test_llm_generation.py"

# Launch all models for User Story 1 together:
Task: "Implement fetch_human_samples.py"
Task: "Implement generate_llm_samples.py"
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
- Verify tests fail before implementing (interface definition phase)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Design Note**: This plan implements a **Balanced Blocked Design** with equal allocation instead of the Spec's 1000/50 split to ensure statistical validity, as per `plan.md` section "Updated Sample Size Justification & Deviation".
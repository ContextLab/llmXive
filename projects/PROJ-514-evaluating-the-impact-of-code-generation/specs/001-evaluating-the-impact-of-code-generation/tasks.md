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
- [X] T002 Initialize Python project with `code/requirements.txt`: Pin `requests`, `GitPython`, `pandas`, `scipy`, `matplotlib`, `pyyaml`, `pytest` to latest stable versions (e.g., `pandas>=2.0.0`, `pytest>=7.0.0`).
- [X] T003 [P] Configure linting (ruff/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup environment configuration management (`code/utils/config.py` for seeds, paths, timeouts, API keys)
- [X] T005 [P] Implement logging infrastructure (`code/utils/logger.py`) to track commit SHAs, Issue URLs, and API responses
- [X] T006 [P] Setup data directory structure (`data/raw/human_samples`, `data/raw/llm_samples`, `data/intermediate`, `data/processed`)
- [X] T007 Create base data models (`code/utils/data_models.py`) defining:
 - `class CodeSample`: attributes `source_type`, `repository_id`, `issue_id`, `task_id`, `language`, `file_path`, `function_name`, `is_fresh_commit`.
 - `class SmellMetric`: attributes `sample_id`, `smell_type`, `count`, `threshold_used`, `continuous_metric_value`.
 - `class StatResult`: attributes `smell_type`, `p_value`, `effect_size`, `confidence_interval`, `correction_method`, `test_method_used`.
- [X] T008 Implement syntax validation utility (`code/utils/validators.py`) for Python/Java file integrity checks
- [ ] T009 Setup CI environment check for PMD/JRE availability (Dockerfile or CI script to install PMD CLI)

### Phase 2.5: Spec Deviation & Update Tasks (Critical)

**Purpose**: Formally update the source of truth (`spec.md`) to resolve contradictions between the spec's original requirements and the valid implementation design. **Must complete before Phase 3.**

- [ ] T016 [Spec Update] Update `specs/001-code-smell-comparison/spec.md`:
 - Modify FR-001 text to state target is **150 human samples** (3 per repo × 50 repos) instead of ≥1000.
 - Modify FR-002 text to state target is **150 LLM samples** (3 per repo × 50 repos) instead of ≥50.
 - Modify SC-001 text to state target is **300 total samples** (150/150) instead of 1050.
 - Add "Deviation Log" section citing `plan.md` and `methodology-f30244be`.
- [ ] T017 [Spec Update] Update `specs/001-code-smell-comparison/spec.md`:
 - Mark FR-007 as **REJECTED** in the Functional Requirements list.
 - Add rationale: "Replaced by Balanced Blocked Design to avoid statistical artifacts."
- [ ] T018 [Spec Update] Update `specs/001-code-smell-comparison/spec.md`:
 - Modify US-3 Acceptance Scenario 1 to replace "Shapiro-Wilk → Mann-Whitney U or Welch's t-test" with "**Blocked Permutation Test** (stratified by repository)".
 - Add note referencing `methodology-f30244be`.

**Checkpoint**: Spec and Tasks are now aligned; implementation can proceed without constraint contradictions.

---

## Phase 3: User Story 1 - Data Collection & Sample Preparation (Priority: P1) 🎯 MVP

**Goal**: Collect a balanced dataset of human-written and LLM-generated code samples from multiple repositories (multiple samples per source per repo) to ensure statistical validity and repository-level matching. **Note**: This implements the "Balanced Blocked Design" from plan.md.

**Independent Test**: Verify the existence of `data/raw/human_samples` and `data/raw/llm_samples` containing a representative set of files each, with `data/raw/api_logs.json` logging the source repository, Issue/PR ID, Task ID, and exact commit SHA for every sample.

### Tests for User Story 1 (MANDATORY - Interface Definition)

> **NOTE**: These contract tests define the interface for the implementation. They must be written FIRST to define the expected behavior, even if they fail to import unimplemented modules.

- [ ] T010 [US1] Contract test for repository selection logic in `tests/contract/test_repo_selection.py` (Defines interface for T012)
- [X] T011 [US1] Contract test for LLM generation logic in `tests/contract/test_llm_generation.py` (Defines interface for T013)

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/01_data_collection/fetch_human_samples.py`: <!-- FAILED: unspecified -->
 - Logic to query 50 public GitHub repos (≥100 stars, ≥5 years history).
 - Extract 3 "fresh" functions per repo (total 150) per plan.md "Balanced Blocked Design".
 - Use `git log --diff-filter=A` to find commits introducing functions.
 - Save files to `data/raw/human_samples/` with metadata JSON sidecars.
- [X] T013 [US1] Implement `code/01_data_collection/generate_llm_samples.py`:
 - Logic to derive 50 tasks from the same Issue/PR descriptions used for human samples.
 - Query HuggingFace Inference API (or similar) with a reasonable timeout and exponential backoff (limited retries).
 - Generate 3 samples per task (total 150) per plan.md "Balanced Blocked Design".
 - Save files to `data/raw/llm_samples/` with metadata JSON sidecars.
- [X] T014 [US1] Implement `code/01_data_collection/validate_dataset.py`:
 - Verify ≥95% of 150 samples (≥143 human, ≥143 LLM) are syntactically valid Python/Java.
 - Log failures and exclusion rates.
 - Generate `data/intermediate/validation_report.json` listing excluded samples and reasons.
- [X] T015 [US1] Implement `code/01_data_collection/export_manifest.py`:
 - Generate `data/raw/manifest.csv` linking sample IDs to Source Type, Repo ID, Issue ID, Commit SHA, and File Path.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Static Analysis Execution (Priority: P2)

**Goal**: Run CPU-tractable static analysis (PMD/SonarQube CLI) on a representative set of samples to extract metrics for four code smell categories (Long Method, Duplicated Code, Feature Envy, Long Parameter List) within CI limits.

**Independent Test**: Run the analysis pipeline on a subset of samples and verify `data/intermediate/analysis_results.json` contains smell counts for all four categories and a tool-validity flag.

### Tests for User Story 2 (MANDATORY - Interface Definition)

- [~] T019 [US2] Contract test for PMD CLI wrapper in `tests/contract/test_pmd_wrapper.py` (Defines interface for T020)
- [X] T020 [US2] Contract test for parallel analysis execution in `tests/contract/test_static_analysis_interface.py` (Defines interface for T021/T023)

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/02_static_analysis/run_pmd.py`:
 - Subprocess wrapper to execute PMD CLI with specific rulesets for the 4 target smells.
 - Enforce per-process memory limit (≤2 GB) and 2-minute timeout per file.
 - Handle syntax errors gracefully (log and exclude).
- [ ] T022 [US2] Implement `code/02_static_analysis/parse_results.py`:
 - Parse PMD XML/JSON output into `data/intermediate/analysis_results.json`.
 - **Dependency**: Must run after T021 completes.
 - Map smells to `SmellMetric` entities.
- [X] T023 [US2] Implement `code/02_static_analysis/tool_validity_check.py`:
 - Run analysis on a known "clean" reference set.
 - Calculate false-positive rate; if >5%, flag the tool configuration as invalid in logs.
 - **Dependency**: Must run after T022 completes to ensure results are parsed.
 - Generate `data/intermediate/tool_validity_status.json` with keys `is_valid` (boolean) and `false_positive_rate` (float).
- [X] T024 [US2] Implement `code/02_static_analysis/aggregate_metrics.py`:
 - Aggregate results into `data/processed/smell_metrics.csv` with columns: `sample_id`, `source_type`, `smell_type`, `count`, `continuous_metric_value` (e.g., cyclomatic complexity).
 - **Dependency**: Must run after T022 and T023 (validity check) complete.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison & Reporting (Priority: P3)

**Goal**: Generate a final report comparing smell frequencies using a Blocked Permutation Test (repository as block), applying Bonferroni correction, and performing sensitivity analysis on the "Long Method" threshold. **Note**: This implements the "Blocked Permutation Test" from plan.md.

**Independent Test**: Generate the final report and verify it contains statistical tables with corrected p-values, effect sizes, box plots, and explicitly uses associational language.

### Tests for User Story 3 (MANDATORY - Interface Definition)

- [X] T025 [US3] Contract test for permutation test logic in `tests/contract/test_permutation_test_interface.py` (Defines interface for T026)
- [ ] T026 [US3] Contract test for report generation in `tests/contract/test_report_interface.py` (Defines interface for T028)

### Implementation for User Story 3

- [X] T027 [US3] Implement `code/03_statistical_analysis/compare_distributions.py`:
 - Implement Blocked Permutation Test (stratified by repository) per plan.md.
 - Handle zero-inflation and non-normality.
 - Apply Bonferroni correction for 4 hypothesis tests (family-wise error rate ≤ 0.05).
 - Calculate effect sizes (Cohen's d or equivalent for permutation tests).
- [ ] T028 [US3] Implement `code/03_statistical_analysis/sensitivity_analysis.py`:
 - Sweep "Long Method" threshold values ∈ {100, 150, 200} lines.
 - Compare results against continuous metrics (cyclomatic complexity) to verify stability.
 - **Dependency**: Must run after T027 completes.
 - Log findings on threshold robustness.
- [ ] T029 [US3] Implement `code/04_reporting/generate_report.py`:
 - **Dependency**: Must run after T027 and T028 complete.
 - Generate `reports/final_study_report.md`.
 - Include required sections: Introduction, Methodology (Blocked Permutation Test), Results (Statistical Tables with corrected p-values, effect sizes), Sensitivity Analysis, Conclusion.
 - Include box plots comparing distributions and continuous metric comparisons.
 - Enforce associational language (e.g., "associated with", "correlated with") and exclude causal claims.
 - Include a section explicitly stating the study design as observational.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `specs/001-code-smell-comparison/research.md`
- [ ] T031 Code cleanup and refactoring
- [ ] T032 Performance optimization (ensure total CI job ≤ 2 hours with 20 parallel jobs)
- [ ] T033 [P] Additional unit tests in `tests/unit/`
- [ ] T034 Run `quickstart.md` validation to ensure reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Spec Update (Phase 2.5)**: Depends on Phase 2 completion; MUST complete before Phase 3 implementation to resolve spec contradictions.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires valid data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires valid metrics from US2

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
3. Complete Phase 2.5: Spec Updates (CRITICAL - resolves contradictions)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add Spec Updates (Phase 2.5) → Resolve contradictions
3. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

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
- **Critical Deviation Note**: This plan implements a **Balanced Blocked Design (150/150)** instead of the Spec's 1000/50 split to ensure statistical validity, as per `plan.md` section "Updated Sample Size Justification & Deviation". Tasks T016-T018 formally update the spec to reflect this.
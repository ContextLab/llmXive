---
description: "Task list template for feature implementation"
---

# Tasks: Statistical Analysis of GitHub Issue Resolution Times

**Input**: Design documents from `/specs/001-github-issue-resolution/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/` at repository root
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

- [X] T001a [P] Create code/ directory at repository root
- [X] T001b [P] Create data/ directory at repository root with subdirectories: raw/, processed/, figures/
- [X] T001c [P] Create tests/ directory at repository root with subdirectories: contract/, integration/, unit/
- [X] T001d [P] Create state/ directory at repository root
- [X] T002 Initialize Python 3.11 project with pinned CPU-tractable dependencies in requirements.txt at projects/PROJ-208-statistical-analysis-of-publicly-availab/code/ (requests, pandas, numpy, scipy, statsmodels, pymer4, matplotlib, seaborn, pyyaml)
- [X] T003 [P] Configure linting and formatting tools: create ruff.toml and pyproject.toml config files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create configuration manager in code/utils/config.py (random seeds, paths, thresholds)
- [X] T005 [P] Implement GitHub API client with rate limit handling and exponential backoff in code/utils/api_client.py (FR-001)
- [X] T006 [P] Setup schema validators against contracts/ in code/utils/validators.py (SC-001)
- [X] T027 [P] Create documentation: data-model.md (entity definitions), contracts/ (schema YAML files) per plan.md Phase 1 outputs
- [X] T039 [P] Implement Reference-Validator Agent with checkpoint execution verification at artifact write, Advancement-Evaluator, and research_review→research_accepted transition (Constitution Principle II)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Collection and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically collect closed issue data from multiple GitHub repositories and produce a clean, analysis-ready dataset with computed resolution times.

**Independent Test**: Run collection pipeline on a fixed set of 5 repositories; verify output CSV contains ≥1000 issues with non-missing resolution times and all required feature columns (US1 acceptance scenario 1).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T007 [P] [US1] Contract test for dataset schema in tests/contract/test_dataset_schema.py
- [X] T008 [P] [US1] Integration test for API fetch with rate limit simulation in tests/integration/test_api_fetch.py

### Implementation for User Story 1

- [X] T009 [US1] Implement issue fetcher in code/collect/fetch_issues.py (FR-001, FR-003) with enforcement of ≥100 repository minimum
- [X] T010 [US1] Implement preprocessing script in code/collect/preprocess.py to compute resolution_time_hours and exclude invalid issues (FR-002, FR-003)
- [ ] T011 [US1] Save cleaned dataset to data/processed/cleaned_issues.csv with checksum AND validate ≥95% completeness threshold per SC-001
- [ ] T012 [US1] Add logging for excluded issues (negative resolution time, missing timestamps) to data/logs/preprocessing.log in JSON format (FR-003)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Descriptive Distribution Analysis (Priority: P2)

**Goal**: Generate empirical cumulative distribution plots and fit parametric distribution models (log-normal, Weibull).

**Independent Test**: Run distribution analysis on cleaned dataset; verify ECDF plots generated and fit quality metrics reported.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T013 [P] [US2] Unit test for log-transform handling of zero values in tests/unit/test_transforms.py
- [ ] T014 [P] [US2] Integration test for distribution fitting output format in tests/integration/test_distributions.py

### Implementation for User Story 2

- [ ] T015 [P] [US2] Implement ECDF plot generation in code/analysis/distribution_fitting.py (x-axis log scale) (FR-002)
- [ ] T016 [US2] Fit log-normal and Weibull models using scipy.stats and report KS statistic, p-value, AIC (FR-002)
- [~] T017 [US2] Detect and report extreme outliers (>30 days) with percentage of total dataset (FR-002)
- [ ] T018 [US2] Save figures to data/figures/ and results to data/processed/distribution_metrics.json (SC-002)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Hypothesis Testing and Regression Modeling (Priority: P3)

**Goal**: Execute ANOVA/Kruskal-Wallis tests, apply Holm-Bonferroni correction, and fit linear mixed-effects model.

**Independent Test**: Run hypothesis testing suite; verify p-values with effect sizes and confidence intervals reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US3] Contract test for analysis output schema in tests/contract/test_analysis_schema.py
- [X] T020 [P] [US3] Integration test for mixed-effects model convergence in tests/integration/test_mixed_effects.py

### Implementation for User Story 3

- [X] T021 [P] [US3] Implement Kruskal-Wallis test for programming language groups with Holm-Bonferroni correction in code/analysis/hypothesis_testing.py (FR-004)
- [X] T022 [P] [US3] Fit linear mixed-effects model with random intercepts for repository in code/analysis/mixed_effects_model.py (FR-005)
- [~] T023 [US3] Implement leave-one-repository-out cross-validation for MAE and R² metrics (SC-004)
- [X] T024 [US3] Calculate VIF from full model design matrix, flag collinearity (VIF≥5), and enforce descriptive language for joint relationship (not independent effects) in code/diagnostics/collinearity.py (FR-006)
- [ ] T025 [US3] Perform sensitivity analysis sweeping a range of cutoffs, calculate false-positive/false-negative rates, and report threshold sensitivity (status changes) in code/diagnostics/sensitivity_analysis.py (FR-007)
- [ ] T026 [US3] Enforce "associational" or "correlational" language in all result text generation in code/analysis/results.py (FR-008)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Documentation, Validation & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, constitutional compliance, and final validation

- [ ] T027a [P] Create quickstart.md (end-to-end run instructions) with content requirements and traceability validation criteria (Constitution Principle IV)
- [ ] T028 [P] Code cleanup and refactoring: run ruff check (zero warnings)
- [ ] T042 [P] Achieve pytest coverage ≥80% with coverage report
- [ ] T029 [P] Configure GitHub Actions workflow for CI (standard CPU allocation, sufficient RAM, 6h timeout) AND validate actual runtime stays within ≤6h constraint (FR-009, FR-010)
- [ ] T030 [P] Run quickstart.md validation to ensure end-to-end reproducibility (SC-005)
- [ ] T033 [P] Generate content hashes for all artifacts in data/, code/, state/ (Constitution Principle V)
- [ ] T031 [P] Update state/projects/PROJ-208-statistical-analysis-of-publicly-availab.yaml with artifact hashes and updated_at timestamp (ISO 8601 format) on artifact changes (Constitution Principle V)
- [ ] T032 [P] Validate reproducibility by re-running code/ against data/ on fresh GitHub Actions runner with identical outputs = matching checksums (Constitution Principle I)
- [ ] T034 [P] Enforce reproducibility: verify code re-run produces identical outputs with checksums for data/, code/, state/ artifacts (Constitution Principle I)
- [ ] T035 [P] Validate temporal data integrity: ensure timestamps from GitHub API stored unchanged AND record deterministic timezone script version in code/VERSION.txt (Constitution Principle VI)
- [ ] T036 [P] Validate reproducible feature engineering: verify feature extraction scripts produce identical outputs AND explicitly declare API fields they read (Constitution Principle VII)
- [ ] T037 [P] Validate data hygiene: verify checksums and run Repository-Hygiene Agent for PII scan (Constitution Principle III)
- [ ] T038 [P] Run Repository-Hygiene Agent for PII scan enforcement in CI workflow with checkpoint verification (Constitution Principle III)
- [ ] T040 [P] Validate single-source-of-truth traceability: verify all figures/statistics trace to exactly one data row and code block (Constitution Principle IV)
- [ ] T041 [P] Validate all result text contains "associational" or "correlational" phrases per FR-008

**Checkpoint**: All constitutional principles validated, documentation complete, CI configured

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T027 (data-model.md, contracts/) MUST precede T009-T026 (schema validation and entity definitions)
 - T039 (Reference-Validator Agent) MUST be in Phase 2 to enable checkpoint validation throughout research
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (Phase 3)**: Must complete before US2 and US3 (data dependency)
 - **US2 (Phase 4)**: Requires cleaned dataset from US1 (Phase 3)
 - **US3 (Phase 5)**: Requires cleaned dataset from US1 (Phase 3)
- **Documentation & Validation (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires data output from US1 (Phase 3)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires data output from US1 (Phase 3)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- API Client/Utils before Collection
- Collection before Preprocessing
- Preprocessing before Analysis
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US2 and US3 can start in parallel (if team capacity allows), but both depend on US1 data
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (once data is ready)
- T015 and T016 share code/analysis/distribution_fitting.py; T016 cannot run in parallel with T015 (removed [P] from T016)

### Ordering Notes

- T033 (generate hashes) MUST precede T031 (update state YAML with hashes)
- T027 (data-model.md, contracts/) MUST be in Phase 2 to precede consumer tasks (T009-T026)
- T039 (Reference-Validator Agent) MUST be in Phase 2 to enable checkpoint validation throughout research

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset schema in tests/contract/test_dataset_schema.py"
Task: "Integration test for API fetch with rate limit simulation in tests/integration/test_api_fetch.py"

# Launch implementation for User Story 1:
Task: "Implement issue fetcher in code/collect/fetch_issues.py"
Task: "Implement preprocessing script in code/collect/preprocess.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify ≥1000 issues, valid resolution times, ≥95% completeness)
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Distribution Analysis) [Waits for US1 data from Phase 3]
 - Developer C: User Story 3 (Modeling) [Waits for US1 data from Phase 3]
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
- **Constraint**: All analysis must run on a standard CPU, sufficient memory GitHub Actions runner (no GPU, no 8-bit quantization)
- **Constraint**: Sensitivity analysis must calculate and report false-positive/false-negative rates (FR-007)
- **Constraint**: All result text must include "associational" or "correlational" (FR-008)
- **Constraint**: VIF≥5 must flag collinearity AND describe joint relationship as descriptive (FR-006)
- **Constraint**: Runtime must validate ≤6h completion (FR-009)
- **Constraint**: Dataset completeness must validate ≥95% threshold (SC-001)
- **Constraint**: Repository collection must enforce ≥100 minimum (FR-001)
- **Constitutional Compliance**: All principles must be validated in Phase 6
- **Constitutional Compliance**: Reference-Validator Agent must verify three checkpoints (Principle II)
- **Constitutional Compliance**: Repository-Hygiene Agent must be used for PII scans (Principle III)
- **Constitutional Compliance**: All figures/statistics must trace to single data row and code block (Principle IV)
- **Constitutional Compliance**: updated_at timestamp must update on artifact changes (Principle V)
- **Constitutional Compliance**: Timezone script version must be recorded (Principle VI)
- **Constitutional Compliance**: Feature extraction scripts must declare API fields (Principle VII)
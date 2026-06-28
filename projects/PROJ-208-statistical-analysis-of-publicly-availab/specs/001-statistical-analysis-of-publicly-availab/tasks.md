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

- [ ] T001a [P] Create code/ directory at repository root
- [ ] T001b [P] Create data/ directory at repository root with subdirectories: raw/, processed/, figures/
- [ ] T001c [P] Create tests/ directory at repository root with subdirectories: contract/, integration/, unit/
- [ ] T001d [P] Create state/ directory at repository root
- [ ] T002 Initialize Python 3.11 project with pinned CPU-tractable dependencies in requirements.txt (requests, pandas, numpy, scipy, statsmodels, pymer4, matplotlib, seaborn, pyyaml)
- [ ] T003 [P] Configure linting and formatting tools: create ruff.toml and pyproject.toml config files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create configuration manager in code/utils/config.py (random seeds, paths, thresholds)
- [ ] T005 [P] Implement GitHub API client with rate limit handling and exponential backoff in code/utils/api_client.py (FR-001)
- [ ] T006 [P] Setup schema validators against contracts/ in code/utils/validators.py (SC-001; note: SC-001 uses "GitHub API schema requirements" terminology - flagged for kickback)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Collection and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically collect closed issue data from multiple GitHub repositories and produce a clean, analysis-ready dataset with computed resolution times.

**Independent Test**: Run collection pipeline on a set of fixed repos; verify output CSV contains ≥1000 issues with non-missing resolution times and required feature columns (note: US1 test validates 5 repos but FR-001 requires ≥100 repos - flagged for kickback).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T007 [P] [US1] Contract test for dataset schema in tests/contract/test_dataset_schema.py
- [ ] T008 [P] [US1] Integration test for API fetch with rate limit simulation in tests/integration/test_api_fetch.py

### Implementation for User Story 1

- [ ] T009 [US1] Implement issue fetcher in code/collect/fetch_issues.py (FR-001, FR-003)
- [ ] T010 [US1] Implement preprocessing script in code/collect/preprocess.py to compute resolution_time_hours and exclude invalid issues (FR-002, FR-003)
- [ ] T011 [US1] Save cleaned dataset to data/processed/cleaned_issues.csv with checksum (SC-001)
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

- [ ] T015 [P] [US2] Implement ECDF plot generation in code/analyze/distributions.py (x-axis log scale) (FR-002)
- [ ] T016 [P] [US2] Fit log-normal and Weibull models using scipy.stats and report KS statistic, p-value, AIC (FR-002)
- [ ] T017 [US2] Detect and report extreme outliers (>30 days) with percentage of total dataset (FR-002)
- [ ] T018 [US2] Save figures to data/figures/ and results to data/processed/distribution_metrics.json (SC-002)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Hypothesis Testing and Regression Modeling (Priority: P3)

**Goal**: Execute ANOVA/Kruskal-Wallis tests, apply Holm-Bonferroni correction, and fit linear mixed-effects model.

**Independent Test**: Run hypothesis testing suite; verify p-values with effect sizes and confidence intervals reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US3] Contract test for analysis output schema in tests/contract/test_analysis_schema.py
- [ ] T020 [P] [US3] Integration test for mixed-effects model convergence in tests/integration/test_mixed_effects.py

### Implementation for User Story 3

- [ ] T021 [P] [US3] Implement Kruskal-Wallis test for programming language groups with Holm-Bonferroni correction in code/analyze/hypothesis_tests.py (FR-004)
- [ ] T022 [P] [US3] Fit linear mixed-effects model with random intercepts for repository in code/analyze/mixed_effects.py (FR-005)
- [ ] T023 [US3] Implement leave-one-repository-out cross-validation for MAE and R² metrics (SC-004)
- [ ] T024 [US3] Calculate VIF from full model design matrix and flag collinearity (VIF≥5) in code/analyze/diagnostics.py (FR-006)
- [ ] T025 [US3] Perform sensitivity analysis sweeping cutoffs {0.01, 0.05, 0.1} and report threshold sensitivity (status changes) in code/analyze/diagnostics.py (FR-007; note: spec FR-007 mandates FP/FN rates which is untestable - flagged for kickback)
- [ ] T026 [US3] Enforce "associational" or "correlational" language in all result text generation in code/analyze/results.py (FR-008)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Documentation, Validation & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, constitutional compliance, and final validation

- [ ] T027 [P] Create documentation: quickstart.md (end-to-end run instructions), data-model.md (entity definitions), contracts/ (schema YAML files) per plan.md Phase 1 outputs
- [ ] T028 [P] Code cleanup and refactoring: run ruff check (zero warnings), achieve pytest coverage ≥80%
- [ ] T029 [P] Configure GitHub Actions workflow for CI (2 CPU, 7GB RAM, 6h timeout) (FR-009, FR-010)
- [ ] T030 [P] Run quickstart.md validation to ensure end-to-end reproducibility (SC-005)
- [ ] T031 [P] Update state/ projects YAML with artifact hashes
- [ ] T032 [P] Validate reproducibility by re-running code/ against data/ on fresh GitHub Actions runner (Constitution Principle I)
- [ ] T033 [P] Generate content hashes for all artifacts in data/, code/, state/ (Constitution Principle V)
- [ ] T034 [P] Enforce reproducibility: verify code re-run produces identical outputs with checksums (Constitution Principle I)
- [ ] T035 [P] Validate temporal data integrity: ensure timestamps from GitHub API stored unchanged (Constitution Principle VI)
- [ ] T036 [P] Validate reproducible feature engineering: verify feature extraction scripts produce identical outputs (Constitution Principle VII)
- [ ] T037 [P] Validate data hygiene: verify checksums and PII scan (Constitution Principle III)
- [ ] T038 [P] Generate content hashes for all artifacts in data/, code/, state/, state/ (Constitution Principle V)
- [ ] T039 [P] Run PII scan enforcement in CI workflow (Constitution Principle III)
- [ ] T040 [P] Implement Reference-Validator Agent for citation validation with ≥0.7 title overlap threshold (Constitution Principle II)

**Checkpoint**: All constitutional principles validated, documentation complete, CI configured

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
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
4. **STOP and VALIDATE**: Test User Story 1 independently (verify ≥1000 issues, valid resolution times)
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
- **Constraint**: All analysis must run on 2-CPU, 7GB RAM GitHub Actions runner (no GPU, no 8-bit quantization)
- **Constraint**: Sensitivity analysis must report threshold sensitivity (status changes), not FP/FN rates (spec FR-007 flagged for kickback)
- **Constraint**: All result text must include "associational" or "correlational" (FR-008)
- **Constitutional Compliance**: All principles must be validated in Phase 6
- **Spec Kickback Required**: FR-007 (FP/FN rates untestable), US1 test scope (5 vs 100 repos), SC-001 terminology ("schema requirements")
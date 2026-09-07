# Tasks: Evaluating the Impact of Code Generation on Code Review Time

**Input**: Design documents from `/specs/001-evaluating-llm-code-generation-impact/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create core directories: `mkdir -p code data/tests docs data/raw data/processed`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan):

- [X] T002 [P] Initialize Python project: Create `requirements.txt` with pinned versions: `datasets==2.14.0 scikit-learn==1.3.0 pandas==2.0.3 numpy==1.24.3 scipy==1.11.1 radon==6.0.1 torch==2.0.1 transformers==4.31.0 matplotlib==3.7.2 seaborn==0.12.2 pyyaml==6.0 requests==2.31.0 gitpython==3.1.32 pytest==7.4.0 ruff==0.0.287 black==23.7.0`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `.ruff.toml` and `pyproject.toml` with specified rules.
- [X] T005 [P] Implement `code/utils/config.py` for random seeds, paths, and API credentials
- [X] T006 [P] Setup `code/utils/validators.py` for schema validation and PII scanning
- [X] T007 [P] Create base data models in `code/utils/models.py`:
 - `PullRequest` class with fields: `pr_id`, `repo_id`, `author_type`, `review_duration`, `file_size`, `complexity_score`
 - `CodeSnippet` class with fields: `snippet_id`, `source_commit`, `generation_source`, `complexity_metrics`, `semantic_similarity_score`
- [X] T008 [P] Setup `Dockerfile` for environment replication (CPU-only)
- [X] T013 [P] Implement `code/utils/rate_limiter.py` with exponential backoff strategy (a limited number of retries as per spec Edge Cases) for GitHub API

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Acquire GitHub PR metadata, extract code content, classify code snippets as "LLM-like" or "Human" (Classifier-Based Proxy), AND generate a small "Prompt-Based Cohort" of synthetic code to satisfy FR-008/US-4 (Spec Requirement).

**Note on Methodology**: While Plan.md suggests avoiding synthetic generation due to CPU constraints, Spec FR-008 and US-4 explicitly mandate a "Prompt-Based Cohort". T014b tasks a *scaled-down* generation on the free Kaggle GPU runner (via auto-offload) as a feasibility test. If this fails (timeout/invalid), the project reports the constraint unmet honestly. This preserves the Spec's requirement while adhering to the Constitution's feasibility rules.

**Independent Test**: The pipeline can be executed end-to-end on a single small repository (< 500 PRs) to verify classification works, metadata is extracted correctly, and the dataset fits within the available RAM limit.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for GitHub API response parsing in `tests/contract/test_github_scraper.py`
- [X] T011 [P] [US1] Integration test for classification on CPU in `tests/integration/test_classifier_runner.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/data_acquisition/github_scraper.py` to fetch PR metadata and file content for repos ≥1,000 stars (FR-001)
- [X] T014 [US1] Implement `code/data_acquisition/classifier_runner.py` using CPU-tractable CodeBERT to classify code snippets as "LLM-like" or "Human" (Primary methodology per plan). Output: `data/processed/classified_snippets.parquet`.
- [ ] T014b [US1] [P] **PROMPT-BASED COHORT GENERATION (GPU OFFLOAD)**: Implement `code/data_acquisition/prompt_generator.py` to generate a small synthetic cohort of code snippets using natural language prompts derived from commit messages (FR-008, US-4). **Constraint**: Use a small, quantized model (e.g., CodeLlama-7B) with `device="cuda"` (auto-offload to Kaggle GPU if CPU fails). Strict timeout ≤ 30s/snippet. Limit to a small sample (e.g., a limited number of snippets). **Output**: `data/processed/prompt_cohort.parquet` (if successful) OR `data/processed/generation_failure_log.json` (if timeout/invalid).
- [X] T015 [US1] Implement `code/feature_extraction/complexity.py` to calculate LOC and Cyclomatic Complexity via `radon` (FR-003, FR-009)
- [X] T016 [US1] Implement `code/feature_extraction/timestamps.py` to extract review duration (PR open to first comment/merge) (FR-003)
- [X] T017 [US1] Implement `code/feature_extraction/style_features.py` to compute style metrics required for classification (FR-009)
- [ ] T017b [US1] [P] **DIAGNOSTIC ONLY**: Implement `code/feature_extraction/semantic_similarity.py` to compute semantic similarity scores for every code snippet using CodeBERT embeddings. **NOTE**: These scores are for a Secondary Diagnostic Report only and are explicitly EXCLUDED from matching covariates per Plan. Output: `data/processed/diagnostic_scores.parquet`. **This file is NOT used by the matching algorithm.**
- [ ] T018 [US1] Add error handling for `radon` failures (skip file, log warning, exclude from dataset) (Edge Case)
- [ ] T019 [US1] **SYNTAX VALIDATION**: Implement `code/feature_extraction/syntax_validator.py` to validate the syntax of generated synthetic code (from T014b). **Depends on: T014b**. Must verify ≥ 95% syntax validity (SC-007). If T014b failed, this task must report "Generation Failed - SC-007 Unmet". Output: `data/processed/syntax_validation_report.json`.
- [ ] T020 [US1] Add logic to flag result as "statistically significant" only if p < 0.05 (SC-002)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Propensity Score Matching and Analysis (Priority: P2)

**Goal**: Pair "LLM-like" code commits with "Human" commits using propensity score matching on file size, complexity, and activity (excluding semantic similarity per Plan), then perform statistical testing.

**Independent Test**: The analysis module can be run on a pre-generated static dataset to verify that matching reduces variance in covariates and outputs valid p-values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for matching algorithm balance check in `tests/contract/test_matching.py`
- [X] T021 [P] [US2] Integration test for statistical test selection (t-test vs Mann-Whitney) in `tests/integration/test_statistical_test.py`

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement `code/analysis/matching.py` for propensity score matching using covariates: file size, complexity, activity. **Note**: Semantic similarity scores (from T017b) are computed but EXCLUDED from matching covariates per Plan (to avoid collider bias). **Dependency**: Requires `data/processed/classified_snippets.parquet` from T014. (FR-004)
- [X] T023a [US2] Implement retry logic in `code/analysis/matching.py`: if Standardized Mean Difference (SMD) > 0.1, adjust propensity score model (add interaction terms) and retry up to 3 times.
- [ ] T023b [US2] **FAILURE HANDLING**: Implement logic in `code/analysis/matching.py` to generate `data/processed/matching_failure_report.json` containing SMD values and retry count, and return a failure flag if SMD > 0.1 after 3 retries. **Depends on: T023a**. (FR-004)
- [X] T023c [US2] **PIPELINE GATE CHECK**: Implement `code/main.py` logic (or a dedicated runner script) to check the output of T023b. If `matching_failure_report.json` exists and indicates failure, exit the pipeline with code 1 and log "Matching Failed: SMD > 0.1". This enforces the "halt" requirement of FR-004.
- [X] T024 [US2] Implement `code/analysis/statistical_test.py` to run Shapiro-Wilk, select t-test or Mann-Whitney U, and output p-value/Cohen's d (FR-005)
- [X] T025 [US2] Implement `code/analysis/matching.py` to generate "Covariate Balance Report" listing SMD for all covariates (FR-010)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Perform sensitivity analysis across repository star-count quartiles and generate visualizations.

**Independent Test**: The visualization script can be run on the analysis output to generate the required plots and verify sensitivity sweep.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Contract test for sensitivity analysis stratification in `tests/contract/test_sensitivity.py`
- [X] T028 [P] [US3] Integration test for visualization generation in `tests/integration/test_visualization.py`

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `code/analysis/sensitivity.py` to repeat statistical test across Multiple subsets stratified by star-count quartiles (FR-006)
- [ ] T030 [US3] **SENSITIVITY CONSISTENCY CHECK**: Implement `code/analysis/sensitivity.py` to check if p < 0.05 in ≥ 80% of subsets. **Output**: `data/processed/sensitivity_summary.json` with a "consistent" boolean flag. (SC-005)
- [X] T030b [US3] **PIPELINE GATE CHECK**: Implement `code/main.py` logic to check `sensitivity_summary.json`. If "consistent" is false, exit with code 1 and log "Sensitivity Failed: Consistency < 80%". This enforces SC-005.
- [X] T031 [US3] Implement `code/analysis/visualization.py` to generate box plots and CDF curves comparing review-time distributions (FR-007)
- [ ] T032 [US3] Implement report generation (PDF/HTML) containing p-value, effect size, and visualizations (US-3)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Prompt-Based Cohort Validation (Priority: P2) - **SPEC REQUIREMENT**

**Goal**: Analyze the "Prompt-Based Cohort" (from T014b) as a separate group to compare stylistic properties with "LLM-like" and "Human" code (FR-008, US-4).

**Independent Test**: Verify that the "Prompt-Based" cohort exhibits distinct stylistic features.

**Note on Causal Claims**: The Plan explicitly avoids causal claims. This task performs a *descriptive* comparison of stylistic properties between the "Prompt-Based" (generated from scratch) and "LLM-like" (rewritten) cohorts to test if they are distinct, without asserting causality.

### Implementation for User Story 4

- [ ] T033a [US4] **PROMPT COHORT ANALYSIS**: Implement `code/data_acquisition/cohort_analyzer.py` to segment the `prompt_cohort.parquet` (from T014b) and `classified_snippets.parquet` (from T014) into "Prompt-Based", "LLM-like", and "Human" cohorts. **Depends on: T014b, T014**. Output: `data/processed/cohort_segments.parquet`. **This task compares stylistic properties between cohorts (descriptive) rather than validating a causal claim.**
- [ ] T034 [US4] **PROMPT COHORT MATCHING**: Implement matching logic for the "Prompt-Based" cohort against "Human" code using the same covariates as US2. **Depends on: T033a, T022**. (FR-008 adjusted)

**Checkpoint**: Prompt-based cohort validation complete

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T036 [P] Documentation updates in `docs/` including `quickstart.md`
- [~] T037 Code cleanup and refactoring
- [~] T038 [P] **PERFORMANCE ENFORCEMENT**: Implement runtime measurement and enforcement of the 6-hour constraint (SC-006) in `code/main.py` and `code/utils/config.py`. **Output**: `data/processed/runtime_report.json`.
- [~] T039 [P] Additional unit tests in `tests/unit/`
- [~] T040 Security hardening (PII scan enforcement)
- [ ] T041 Run `quickstart.md` validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T014, T017b)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 analysis output
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Parallel to US2, uses US1 data, depends on US2 matching logic (T022) and T014b output.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, US3, US4 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

### Critical Cross-Phase Dependencies

- **T014b (Phase 3) -> T019 (Phase 3)**: Syntax validation (T019) MUST wait for generation (T014b).
- **T023a (Phase 4) -> T023b (Phase 4)**: Failure report (T023b) MUST wait for retry logic (T023a) to complete and fail.
- **T023b (Phase 4) -> T023c (Phase 4)**: Gate check (T023c) MUST wait for failure report (T023b).
- **T030 (Phase 5) -> T030b (Phase 5)**: Gate check (T030b) MUST wait for summary (T030).
- **T014b (Phase 3) -> T033a (Phase 6) -> T034 (Phase 6)**: Prompt cohort analysis (T033a) and matching (T034) MUST wait for generation (T014b).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for GitHub API response parsing in tests/contract/test_github_scraper.py"
Task: "Integration test for classification on CPU in tests/integration/test_classifier_runner.py"

# Launch all models for User Story 1 together (except T014 which is sequential):
Task: "Implement github_scraper.py in code/data_acquisition/github_scraper.py"
Task: "Implement complexity.py in code/feature_extraction/complexity.py"
Task: "Implement timestamps.py in code/feature_extraction/timestamps.py"
Task: "Implement style_features.py in code/feature_extraction/style_features.py"
Task: "Implement semantic_similarity.py in code/feature_extraction/semantic_similarity.py"
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
- **Critical Constraint**: T014b (Prompt-Based Generation) is restored to satisfy FR-008/US-4. It is a scaled-down GPU feasibility test (a limited set of snippets, 30s timeout). If it fails, the project reports the constraint unmet honestly.
- **Critical Constraint**: T019 (Syntax Validation) depends on T014b.
- **Critical Constraint**: T023b (Failure Handling) depends on T023a and must halt the pipeline (enforced by T023c).
- **Critical Constraint**: T033a/T034 (Prompt Cohort) depend on T014b.
- **Critical Constraint**: Semantic similarity scores (T017b) are computed for diagnostics only and are EXCLUDED from matching covariates per Plan. T022 does NOT require `diagnostic_scores.parquet` to run.
- **Critical Constraint**: T030 (Sensitivity Consistency) is restored to satisfy SC-005 and enforced by T030b.
- **Critical Constraint**: T038 (Performance Enforcement) is moved to Phase N but explicitly tasked to enforce the 6-hour runtime (SC-006).
- **Critical Constraint**: T001b (redundant) has been removed.
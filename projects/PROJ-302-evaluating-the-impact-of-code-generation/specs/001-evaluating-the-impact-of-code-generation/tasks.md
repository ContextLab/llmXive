# Tasks: Evaluating the Impact of Code Generation on Code Review Time

**Input**: Design documents from `/specs/001-evaluating-llm-code-review-impact/`
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

- [ ] T001a [P] Create core directories: `code/`, `data/`, `tests/`, `docs/`
- [ ] T001b [P] Create data subdirectories: `data/raw/`, `data/processed/`
- [ ] T001c [P] Create empty file `data/checksums.yaml`
- [ ] T001d [P] Create code subdirectories: `code/data_acquisition/`, `code/feature_extraction/`, `code/analysis/`, `code/utils/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T002 [P] Initialize Python 3.11 project with `requirements.txt` (pinned `datasets`, `scikit-learn`, `pandas`, `numpy`, `scipy`, `radon`, `torch`, `transformers`, `matplotlib`, `seaborn`, `pyyaml`, `requests`, `gitpython`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [~] T005 [P] Implement `code/utils/config.py` for random seeds, paths, and API credentials
- [~] T006 [P] Setup `code/utils/validators.py` for schema validation and PII scanning
- [~] T007 [P] Create base data models in `code/utils/models.py`:
 - `PullRequest` class with fields: `pr_id`, `repo_id`, `author_type`, `review_duration`, `file_size`, `complexity_score`
 - `CodeSnippet` class with fields: `snippet_id`, `source_commit`, `generation_source`, `complexity_metrics`, `semantic_similarity_score`
- [~] T008 [P] Setup `Dockerfile` for environment replication (CPU-only)
- [~] T013 [P] Implement `code/utils/rate_limiter.py` with exponential backoff strategy (a limited number of retries as per spec Edge Cases) for GitHub API

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Acquire GitHub PR metadata, extract code content, and generate synthetic LLM code snippets (FR-002) using a CPU-tractable model. If generation fails, halt and trigger a spec amendment request.

**Independent Test**: The pipeline can be executed end-to-end on a single small repository (< 500 PRs) to verify generation works, metadata is extracted correctly, and the dataset fits within the available RAM limit.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T010 [P] [US1] Contract test for GitHub API response parsing in `tests/contract/test_github_scraper.py`
- [~] T011 [P] [US1] Integration test for generation on CPU in `tests/integration/test_synthetic_generator.py`

### Implementation for User Story 1

- [~] T012 [P] [US1] Implement `code/data_acquisition/github_scraper.py` to fetch PR metadata and file content for repos ≥1,000 stars (FR-001)
- [~] T014 [US1] Implement `code/data_acquisition/classifier_runner.py` using CPU-tractable CodeBERT to classify code snippets as "LLM-like" or "Human" (for secondary diagnostic purposes only, not primary generation).
- [~] T014b [US1] **MANDATORY GENERATION**: Implement `code/data_acquisition/synthetic_generator.py` to generate synthetic code snippets using a CPU-tractable LLM (CodeLlama) with a -second timeout per snippet (FR-002). **CRITICAL**: If generation fails or exceeds time limit, the task MUST generate `spec_amendment_request.md` detailing the failure and HALT the pipeline. Do NOT silently fall back to classification. Output: `data/processed/generated_snippets.parquet`.
- [~] T015 [US1] Implement `code/feature_extraction/complexity.py` to calculate LOC and Cyclomatic Complexity via `radon` (FR-003, FR-009)
- [~] T016 [US1] Implement `code/feature_extraction/timestamps.py` to extract review duration (PR open to first comment/merge) (FR-003)
- [~] T017 [US1] Implement `code/feature_extraction/style_features.py` to compute style metrics required for classification (FR-009)
- [ ] T017b [US1] [P] **DIAGNOSTIC ONLY**: Implement `code/feature_extraction/semantic_similarity.py` to compute semantic similarity scores for every code snippet using CodeBERT embeddings (FR-009). **NOTE**: These scores are for a Secondary Diagnostic Report only and are explicitly EXCLUDED from matching covariates per Plan. Output: `data/processed/diagnostic_scores.parquet`.
- [ ] T018 [US1] Add error handling for `radon` failures (skip file, log warning, exclude from dataset) (Edge Case)
- [ ] T019 [US1] Add validation to ensure generated snippets (from T014b) are syntactically valid (≥95% success rate check) (SC-007). **Dependency**: T019 depends on T014b output.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Propensity Score Matching and Analysis (Priority: P2)

**Goal**: Pair "LLM-like" code commits with "Human" commits using propensity score matching on file size, complexity, and activity (excluding semantic similarity per Plan), then perform statistical testing.

**Independent Test**: The analysis module can be run on a pre-generated static dataset to verify that matching reduces variance in covariates and outputs valid p-values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Contract test for matching algorithm balance check in `tests/contract/test_matching.py`
- [ ] T021 [P] [US2] Integration test for statistical test selection (t-test vs Mann-Whitney) in `tests/integration/test_statistical_test.py`

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement `code/analysis/matching.py` for propensity score matching using covariates: file size, complexity, activity. **Note**: Semantic similarity scores (from T017b) are computed but EXCLUDED from matching covariates per Plan (to avoid collider bias). **Dependency**: Requires `data/processed/diagnostic_scores.parquet` from T017b to document the exclusion. (FR-004)
- [ ] T022b [US2] Implement logic to generate `data/processed/deviation_report.md` documenting the formal exclusion of semantic similarity from matching covariates (deviation from FR-004/FR-009 intent) per Plan's scientific reasoning. (FR-004 deviation)
- [ ] T023a [US2] Implement retry logic in `code/analysis/matching.py`: if Standardized Mean Difference (SMD) > 0.1, adjust propensity score model (add interaction terms) and retry up to 3 times.
- [ ] T023b [US2] Implement failure handling in `code/analysis/matching.py`: if SMD > 0.1 after 3 retries, generate `data/processed/matching_failure_report.json` containing SMD values and retry count, and halt analysis. (FR-004)
- [ ] T024 [US2] Implement `code/analysis/statistical_test.py` to run Shapiro-Wilk, select t-test or Mann-Whitney U, and output p-value/Cohen's d (FR-005)
- [ ] T025 [US2] Implement `code/analysis/matching.py` to generate "Covariate Balance Report" listing SMD for all covariates (FR-010)
- [ ] T026 [US2] Add logic to flag result as "statistically significant" only if p < 0.05 (SC-002)
- [ ] T034 [US2/US4] Implement matching logic for the Prompt-Based cohort (from T033) using the same covariates as US2. **Dependency**: Requires matching infrastructure from T022/T025. (FR-008 adjusted)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Perform sensitivity analysis across repository star-count quartiles and generate visualizations.

**Independent Test**: The visualization script can be run on the analysis output to generate the required plots and verify sensitivity sweep.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Contract test for sensitivity analysis stratification in `tests/contract/test_sensitivity.py`
- [ ] T028 [P] [US3] Integration test for visualization generation in `tests/integration/test_visualization.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/analysis/sensitivity.py` to repeat statistical test across Multiple subsets stratified by star-count quartiles (FR-006)
- [ ] T030 [US3] Implement `code/analysis/sensitivity.py` to check if p < 0.05 in ≥ 80% of subsets. **Output**: `data/processed/sensitivity_summary.json` with a "consistent" boolean flag. (SC-005)
- [ ] T031 [US3] Implement `code/analysis/visualization.py` to generate box plots and CDF curves comparing review-time distributions (FR-007)
- [ ] T032 [US3] Implement report generation (PDF/HTML) containing p-value, effect size, and visualizations (US-3)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Prompt-Based Cohort Validation (Priority: P2) - **MANDATORY GENERATION**

**Goal**: Generate a "Prompt-Based" cohort of LLM code using natural language prompts derived from commit messages, without access to the original file content, to validate the causal claim (FR-008).

**Independent Test**: Verify that the generated code is syntactically valid and semantically similar to the human originals.

### Implementation for User Story 4

- [ ] T033 [US4] **MANDATORY GENERATION**: Implement `code/data_acquisition/prompt_cohort_generator.py` to generate a "Prompt-Based" cohort of LLM code using natural language prompts derived from commit messages, without access to the original file content (FR-008). **CRITICAL**: If generation fails, the task MUST generate `spec_amendment_request.md` detailing the failure and HALT the pipeline. Do NOT fall back to filtering. Output: `data/processed/prompt_based_cohort.parquet`.
- [ ] T035 [US4] Add validation to ensure prompt-based cohort snippets (from T033) are syntactically valid (FR-008 adjusted)

**Checkpoint**: Prompt-based cohort validation complete

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `docs/` including `quickstart.md`
- [ ] T037 Code cleanup and refactoring
- [ ] T038 Performance optimization across all stories (ensure ≤ 6h runtime)
- [ ] T039 [P] Additional unit tests in `tests/unit/`
- [ ] T040 Security hardening (PII scan enforcement)
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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T014b, T017b)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 analysis output
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Parallel to US2, uses US1 data, depends on US2 matching logic (T022)

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

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for GitHub API response parsing in tests/contract/test_github_scraper.py"
Task: "Integration test for generation on CPU in tests/integration/test_synthetic_generator.py"

# Launch all models for User Story 1 together (except T014b which is sequential):
Task: "Implement github_scraper.py in code/data_acquisition/github_scraper.py"
Task: "Implement classifier_runner.py in code/data_acquisition/classifier_runner.py"
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
- **Critical Constraint**: All LLM/Generation tasks (T014b, T033) MUST be mandatory. If generation fails, the task MUST halt and generate `spec_amendment_request.md`. No silent fallbacks to classification or filtering are permitted.
- **Critical Constraint**: Semantic similarity scores (T017b) are computed for diagnostic purposes only and are EXCLUDED from matching covariates per Plan. This exclusion must be formally documented in `data/processed/deviation_report.md` (T022b).
- **Critical Constraint**: Task T014b and T033 are sequential prerequisites for their respective validation tasks (T019, T035). They are not parallel with their validators.
- **Critical Constraint**: Task T008 and T013 have been merged into a single task T013 in Phase 2 to resolve ordering conflicts.
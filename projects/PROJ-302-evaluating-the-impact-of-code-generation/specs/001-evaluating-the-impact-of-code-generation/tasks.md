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

- [X] T001 Create project structure per implementation plan

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan):

- [X] T002 [P] Initialize Python project: Create `requirements.txt` with pinned versions: `datasets==2.14.0 scikit-learn==1.3.0 pandas==2.0.3 numpy==1.24.3 scipy==1.11.1 radon==6.0.1 torch==2.0.1 transformers==4.31.0 matplotlib==3.7.2 seaborn==0.12.2 pyyaml==6.0 requests==2.31.0 gitpython==3.1.32 pytest==7.4.0 ruff==0.0.287 black==23.7.0 reportlab==4.0.4 jinja2==3.1.2 google-cloud-bigquery==3.11.0 tenacity==8.2.2`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `.ruff.toml` and `pypy.toml` with specified rules.
- [X] T005 [P] Implement `code/utils/config.py` for random seeds, paths, and API credentials
- [X] T006 [P] Setup `code/utils/validators.py` for schema validation and PII scanning
- [X] T007 [P] Create base data models in `code/utils/models.py`:
 - `PullRequest` class with fields: `pr_id`, `repo_id`, `author_type`, `review_duration`, `file_size`, `complexity_score`
 - `CodeSnippet` class with fields: `snippet_id`, `source_commit`, `generation_source`, `complexity_metrics`, `semantic_similarity_score`
- [X] T008 [P] Setup `Dockerfile` for environment replication (CPU-only)
- [X] T013 [P] Implement `code/utils/rate_limiter.py` with exponential backoff strategy (a limited number of retries as per spec Edge Cases)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Acquire GitHub PR metadata, extract code content, generate synthetic LLM code (two distinct cohorts: **Context-Based** and **Prompt-Based**) to satisfy FR-008/US-4, and compute all features.

**Independent Test**: The pipeline can be executed end-to-end on a single small repository (< 500 PRs) to verify generation works, metadata is extracted correctly, and the dataset fits within the available RAM limit.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for GitHub API response parsing in `tests/contract/test_github_scraper.py`
- [X] T011 [P] [US1] Integration test for generation on CPU/GPU in `tests/integration/test_generator.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/data_acquisition/github_scraper.py` to fetch PR metadata and file content for repos ≥1,000 stars (FR-001)
- [X] T014 [US1] Implement `code/data_acquisition/classifier_runner.py` using CPU-tractable CodeBERT to classify code snippets as "LLM-like" or "Human" (Fallback/Secondary). Output: `data/processed/classified_snippets.parquet`. **Verification**: Verify that the output file contains >0 rows and that the 'author_type' column has unique values ['human', 'llm-like'].
- [ ] T014b-GEN [US1] **CONTEXT-BASED GENERATION (GPU ESCAPE HATCH)**: Implement `code/data_acquisition/generator.py` to generate synthetic code snippets using a small/8-bit quantized LLM (e.g., `CodeLlama-7B-8bit` or `4bit`). **Strategy**: Attempt generation on CPU first. If generation time > 60s or fails, trigger a GitHub Actions workflow dispatch to a `runs-on: [self-hosted, gpu]` runner group (defined in T014b-GPU-WORKFLOW) to re-run the generation on a GPU-enabled runner. **Implementation Detail**: Use `requests.post` to `/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches` with payload `{"ref": "main", "inputs": {"snippet_id": "..."}}`. **Crucial**: `workflow_id` must be the workflow filename (e.g., `gpu-generation.yml`). **Input**: Original code + context. **Output**: `data/processed/context_based_snippets.parquet` with `generation_source='llm-context'`. **Timeout**: Enforce ≤30s generation time per snippet on GPU. **Verification**: Verify output contains >0 rows and `generation_source` column has unique values. **Depends on: T012**. (Plan Override: FR-002 CPU limit conditional override - explicitly implements Plan's 'Critical Methodological Override' and FR-002's 30s/60s constraints).
- [ ] T014b-INTENT [US1] **PROMPT PREPARATION**: Implement `code/data_acquisition/prompt_engineering.py` to extract and rewrite commit messages into natural language prompts for the "Prompt-Based" cohort. **Output**: `data/processed/intent_prompts.parquet`. **Constraint**: Must not access original file content. **Output Schema**: Must include a 'prompt' column. **Depends on: T012**.
- [ ] T014b-PROMPT-GEN [US1] **PROMPT-BASED COHORT GENERATION**: Implement `code/data_acquisition/prompt_generator.py` to generate synthetic code snippets using a small/8-bit quantized LLM (e.g., `CodeLlama-7B-8bit` or `4bit`) **without access to original file content**. **Input**: Prompts from `data/processed/intent_prompts.parquet` (T014b-INTENT). **Output**: `data/processed/prompt_based_snippets.parquet` with `generation_source='llm-prompt'`. **Constraint**: Must strictly follow US-4 Acceptance Scenario 1. **Depends on: T012, T014b-INTENT**. (Plan Override: FR-002 CPU limit conditional override - explicitly implements Plan's 'Critical Methodological Override' and FR-002's 30s/60s constraints).
- [ ] T014b-GPU-WORKFLOW [US1] **GPU ESCAPE HATCH WORKFLOW**: Implement `.github/workflows/gpu-generation.yml` to define the GitHub Actions workflow for the GPU offload. **Content**: Define a job that runs on `runs-on: [self-hosted, gpu]` (or equivalent runner group) and triggers the `generator.py` script with `device="cuda"`. **Trigger**: Manual or automatic dispatch from T014b-GEN on failure. **Depends on: T008**.
- [ ] T014b-VAL [US1] **SYNTAX VALIDATION**: Implement `code/data_acquisition/syntax_validator.py` to verify generated code is syntactically valid (≥95% success rate). **Output**: `data/processed/syntax_validation_report.json`. **Verification**: Verify file exists and contains a 'validity_rate' key with value ≥0.95. **Depends on: T014b-GEN, T014b-PROMPT-GEN**. (SC-007)
- [X] T015 [US1] Implement `code/feature_extraction/complexity.py` to calculate LOC and Cyclomatic Complexity via `radon` (FR-003, FR-009)
- [X] T016 [US1] Implement `code/feature_extraction/timestamps.py` to extract review duration (PR open to first comment/merge) (FR-003)
- [X] T017 [US1] Implement `code/feature_extraction/style_features.py` to compute style metrics required for classification (FR-009)
- [ ] T017b-1 [US1] **SEMANTIC SIMILARITY COMPUTATION**: Implement `code/feature_extraction/semantic_similarity.py` to compute semantic similarity scores for every code snippet using CodeBERT embeddings (`microsoft/codebert-base`). **Output**: `data/processed/semantic_scores.parquet`. **Critical Path**: Must complete before Phase 4. **Verification**: Verify file exists and contains scores for all snippets. **Depends on: T012**.
- [ ] T017b-2 [US1] **COVARIATE CONFIGURATION**: Implement `code/feature_extraction/covariate_config.py` to define the covariate set for matching. **Output**: `data/processed/covariate_config.json` listing `['file_size', 'complexity', 'activity']`. **Note**: Explicitly **excludes** 'semantic_similarity' per Plan override. **Depends on: T017b-1**.
- [X] T018 [US1] **ERROR HANDLING FOR RADON FAILURES**: Implement `code/feature_extraction/complexity.py` error handling: 1) On `radon` failure, log `logging.warning("Radon failed for {file}: {error}")` to `logs/radon_errors.log`. 2) Drop the row from the DataFrame. 3) Continue processing. **Output**: `logs/radon_errors.log`. (Edge Case)
- [ ] T014b-WAIVER-LOG [US1] **FR-002 WAIVER LOGGING**: Implement `code/data_acquisition/waiver_logger.py` to generate `data/processed/waiver_log.json`. **Logic**: If T014b-GEN triggers the GPU escape hatch, this script MUST record the event, the specific reason (CPU timeout > 60s), and the timestamp. **Output**: `data/processed/waiver_log.json` with structure `{"waiver_type": "FR-002_CPU_OVERRIDE", "triggered_by": "T014b-GEN", "timestamp": "<ISO8601>", "reason": "CPU generation exceeded 60s limit"}`. **Verification**: Verify file exists and contains the correct waiver structure if GPU was triggered. **Depends on: T014b-GEN**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Propensity Score Matching and Analysis (Priority: P2)

**Goal**: Pair "LLM-generated" code commits with "Human" commits using propensity score matching on file size, complexity, activity (excluding semantic similarity per Plan override), then perform statistical testing.

**Independent Test**: The analysis module can be run on a pre-generated static dataset to verify that matching reduces variance in covariates and outputs valid p-values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for matching algorithm balance check in `tests/contract/test_matching.py`
- [X] T021 [P] [US2] Integration test for statistical test selection (t-test vs Mann-Whitney) in `tests/integration/test_statistical_test.py`

### Implementation for User Story 2

- [ ] T022-1 [US2] **PROPENSITY SCORE MATCHING (EXCLUDING SEMANTIC SIMILARITY)**: Implement `code/analysis/matching.py` for propensity score matching using covariates defined in `data/processed/covariate_config.json` (from T017b-2). **Input Dataset**: `data/processed/merged_features.parquet`. **Columns to Use**: Read from `data/processed/covariate_config.json` (e.g., `['file_size', 'complexity_score', 'activity_level']`). **Constraint**: **Explicitly EXCLUDE** 'semantic_similarity' to avoid 'bad control' bias, per Plan's 'Critical Methodological Override'. **Note**: This overrides Spec FR-004/FR-009. **Bias Check**: Compute causal graph and verify that excluding semantic similarity is valid for "generation from scratch" design. **Depends on: T017b-2, T014b-GEN, T014b-PROMPT-GEN, T014**. (FR-004 adjusted)
- [ ] T022-SPEC-AMEND [US2] **SPEC AMENDMENT FOR METHODOLOGY**: Implement `code/analysis/spec_amender.py` to update `specs/001-evaluating-llm-code-generation-impact/spec.md`. **Content**: Update FR-004 and FR-009 to explicitly state that semantic_similarity is excluded from matching covariates to avoid 'bad control' bias, reflecting the Plan's 'Critical Methodological Override'. **Action**: Modify the spec file directly to ensure the Spec is the Single Source of Truth. **Verification**: Verify spec.md reflects the updated requirement. **Depends on: T022-1**. (Constitution Principle IV)
- [X] T023a [US2] **MATCHING RETRY LOGIC**: Implement `code/analysis/matching.py` logic to: 1) If Standardized Mean Difference (SMD) > 0.1, retry with interaction terms. **Retry Algorithm**: First retry: add (file_size * complexity). Second retry: add (complexity * activity). Third retry: add (file_size * activity). **Output**: Updated matching results. **Depends on: T022-1**. (FR-004)
- [ ] T023b [US2] **MATCHING FAILURE REPORTING & HALT**: Implement `code/analysis/matching.py` logic to: 1) If SMD > 0.1 after multiple retries, generate `data/processed/matching_failure_report.json` containing SMD values and retry count. 2) **HALT the pipeline with `sys.exit(1)`**. **Verification**: Verify `main.py` exits with code 1 when this condition is met. **Depends on: T023a**. (FR-004)
- [X] T024 [US2] Implement `code/analysis/statistical_test.py` to run Shapiro-Wilk, select t-test or Mann-Whitney U, and output p-value/Cohen's d (FR-005)
- [ ] T020-IMP [US2] **SIGNIFICANCE FLAGGING**: Implement `code/analysis/significance.py` with function `check_significance(p_val: float, alpha: float = 0.05) -> bool`. **Logic**: Return `True` if `p_val < alpha`, else `False`. **Output**: `data/processed/significance_flag.json` containing `{"is_significant": <bool>, "p_value": <float>, "alpha": <float>}`. **Depends on: T024**. (SC-002)
- [X] T025 [US2] Implement `code/analysis/matching.py` to generate "Covariate Balance Report" listing SMD for all covariates (FR-010)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Perform sensitivity analysis across repository complexity/size quartiles (replacing star-count) and generate visualizations.

**Independent Test**: The visualization script can be run on the analysis output to generate the required plots and verify sensitivity sweep.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Contract test for sensitivity analysis stratification in `tests/contract/test_sensitivity.py`
- [X] T028 [P] [US3] Integration test for visualization generation in `tests/integration/test_visualization.py`

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `code/analysis/sensitivity.py` to repeat statistical test across multiple distinct subsets stratified by **code complexity and PR size** quartiles (FR-006, Plan override).
- [ ] T030 [US3] **SENSITIVITY CONSISTENCY CHECK**: Implement `code/analysis/sensitivity.py` to check if p < 0.05 in ≥ 80% of subsets. **Input**: `data/processed/merged_features.parquet`. **Method**: Use `pandas.qcut` on columns defined in `data/processed/covariate_config.json` (from T017b-2) for complexity and size. **Constraint**: **Must have at least 5 valid subsets**. **Fallback**: If complexity/size stratification yields <5 subsets, fallback to stratifying by `repository_star_count` (Spec US-3 original requirement). If neither yields ≥5 subsets, **FAIL** with error "Insufficient data for sensitivity analysis (requires ≥5 subsets)". **Output**: `data/processed/sensitivity_summary.json` with a "consistent" boolean flag. **Verification**: Verify JSON file exists and contains a key 'consistent' with a boolean value derived from the logic: (count(p < 0.05) / total_subsets) >= 0.80 AND total_subsets >= 5. (SC-005)
- [X] T030b [US3] **PIPELINE GATE CHECK**: Implement `code/main.py` logic to check `data/processed/sensitivity_summary.json`. If "consistent" is false, exit with code 1 and log "Sensitivity Failed: Consistency < 80%". This enforces SC-005. **Depends on: data/processed/sensitivity_summary.json**.
- [X] T031 [US3] Implement `code/analysis/visualization.py` to generate box plots and CDF curves comparing review-time distributions (FR-007)
- [ ] T032 [US3] **REPORT GENERATION (PDF)**: Implement `code/analysis/report_generator.py` using `reportlab` and `jinja2`. **Input**: `data/processed/analysis_results.json`, `data/processed/visualizations/`. **Output**: `reports/analysis_report.pdf`. **Content**: Sections for p-value, effect size, box plot, CDF, and sensitivity summary. (US-3)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Prompt-Based Cohort Validation (Priority: P2) - **SPEC REQUIREMENT**

**Goal**: Analyze the "Prompt-Based" cohort (from T014b-PROMPT-GEN) and "Context-Based" cohort (from T014b-GEN) as separate groups to validate the causal claim (FR-008, US-4).

**Independent Test**: Verify that the "Prompt-Based" cohort exhibits distinct stylistic properties and is valid for comparison.

### Implementation for User Story 4

- [ ] T033a [US4] **COHORT ANALYSIS**: Implement `code/data_acquisition/cohort_analyzer.py` to segment the `prompt_based_snippets.parquet` (from T014b-PROMPT-GEN) and `context_based_snippets.parquet` (from T014b-GEN) into "llm-prompt", "llm-context", and "human" cohorts. **Depends on: T014b-PROMPT-GEN, T014b-GEN, T014b-VAL, T014**. **Output**: `data/processed/cohort_segments.parquet`. **Verification**: Verify file contains exactly three unique values in 'generation_source' column: 'llm-prompt', 'llm-context', 'human'.
- [ ] T034-MAIN [US4] **COHORT MATCHING (PLAN LOGIC)**: Implement matching logic for the "llm-prompt" and "llm-context" cohorts against "Human" code using the same covariates as US2 (excluding semantic_similarity). **Input**: `data/processed/cohort_segments.parquet`. **Covariates**: `['file_size', 'complexity_score', 'activity_level']` (from `data/processed/covariate_config.json`). **Depends on: T033a, T022-1**. **Output**: `data/processed/llm_cohort_matched_main.parquet`. **Verification**: Verify SMD < 0.1 for all covariates in the output. (FR-008 adjusted)
- [ ] T034-US4-VALID [US4] **COHORT MATCHING (SPEC US-4 VALIDATION)**: Implement matching logic for the "llm-prompt" cohort against "Human" code using the SPEC's US-4 acceptance criteria (including semantic_similarity). **Input**: `data/processed/cohort_segments.parquet`. **Action**: First, merge `data/processed/semantic_scores.parquet` (from T017b-1) into `data/processed/cohort_segments.parquet` to ensure `semantic_similarity_score` column exists. **Covariates**: `['file_size', 'complexity_score', 'activity_level', 'semantic_similarity_score']`. **Depends on: T033a, T017b-1**. **Output**: `data/processed/llm_cohort_matched_spec.parquet`. **Verification**: Verify SMD < 0.1 for all covariates in the output. (FR-008 Spec Compliance)

**Checkpoint**: Prompt-based cohort validation complete

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `docs/` including `quickstart.md`
- [ ] T037 Code cleanup and refactoring
- [ ] T038 [P] **PERFORMANCE ENFORCEMENT**: Implement runtime measurement and enforcement of the -hour constraint (SC-006) in `code/main.py` and `code/utils/config.py`. **Output**: `data/processed/runtime_report.json`.
- [ ] T039 [P] Additional unit tests in `tests/unit/`
- [ ] T040 Security hardening (PII scan enforcement)
- [ ] T041 [P] **QUICKSTART VALIDATION**: Run `python code/quickstart_validator.py`. **Success Criteria**: Exit code 0, no warnings. **Output**: `validation_log.txt`. (Quickstart)
- [ ] T042 [P] [US1] Implement logging for data acquisition failures (API rate limits, invalid repos) in `code/data_acquisition/github_scraper.py`. Rationale: Provides better debugging info for edge cases.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T014b-GEN, T014b-PROMPT-GEN, T017b-1)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 analysis output
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Parallel to US2, uses US1 data, depends on US2 matching logic (T022-1) and T014b-GEN/T014b-PROMPT-GEN output.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority
- **T014b-GEN depends on T012**.
- **T014b-PROMPT-GEN depends on T012, T014b-INTENT**.
- **T017b-1 depends on T012**.
- **T017b-2 depends on T017b-1**.
- **T014b-VAL depends on T014b-GEN, T014b-PROMPT-GEN**.
- **T022-1 depends on T017b-2, T014b-GEN, T014b-PROMPT-GEN, T014**.
- **T022-SPEC-AMEND depends on T022-1**.
- **T023a depends on T022-1**.
- **T023b depends on T023a**.
- **T020-IMP depends on T024**.
- **T033a depends on T014b-PROMPT-GEN, T014b-GEN, T014b-VAL, T014**.
- **T034-MAIN depends on T033a, T022-1**.
- **T034-US4-VALID depends on T033a, T017b-1**.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, US3, US4 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Note**: T014b-GEN, T014b-PROMPT-GEN, T014b-VAL, T017b-1, T017b-2, T022-1, T022-SPEC-AMEND, T023a, T023b, T020-IMP, T033a, T034-MAIN, T034-US4-VALID are **NOT** parallel-safe due to sequential dependencies.

### Critical Cross-Phase Dependencies

- **T017b-1 (Phase 3) -> T022-1 (Phase 4)**: Matching (T022-1) MUST wait for semantic scores (T017b-1) to complete. **Note**: T017b-1 is Critical Path, not [P]. (Clarified: T022-1 uses T017b-1 for exploratory/optional data, but core matching excludes it).
- **T014b-GEN (Phase 3) -> T033a (Phase 6) -> T034-MAIN/T034-US4-VALID (Phase 6)**: Cohort analysis (T033a) and matching (T034) MUST wait for generation (T014b-GEN, T014b-PROMPT-GEN).
- **T014b-GEN (Phase 3) -> T014b-VAL (Phase 3)**: Validation (T014b-VAL) MUST wait for generation (T014b-GEN, T014b-PROMPT-GEN).
- **T022-1 (Phase 4) -> T022-SPEC-AMEND (Phase 4)**: Spec amendment (T022-SPEC-AMEND) MUST wait for matching (T022-1).
- **T023a (Phase 4) -> T023b (Phase 4)**: Failure report (T023b) MUST wait for retry logic (T023a) to complete and fail.
- **T030 (Phase 5) -> T030b (Phase 5)**: Gate check (T030b) MUST wait for summary (T030).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for GitHub API response parsing in tests/contract/test_github_scraper.py"
Task: "Integration test for generation on CPU/GPU in tests/integration/test_generator.py"

# Launch all models for User Story 1 together (except T014b-GEN, T017b-1 which are sequential):
Task: "Implement github_scraper.py in code/data_acquisition/github_scraper.py"
Task: "Implement complexity.py in code/feature_extraction/complexity.py"
Task: "Implement timestamps.py in code/feature_extraction/timestamps.py"
Task: "Implement style_features.py in code/feature_extraction/style_features.py"
# T014b-GEN is Sequential, not [P]
# T017b-1 is Sequential, not [P]
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
- **Critical Constraint**: T014b-GEN (GPU Escape Hatch) now uses conditional GitHub Actions workflow dispatch, not Kaggle.
- **Critical Constraint**: T014b-PROMPT-GEN added to implement distinct 'Prompt-Based' cohort (FR-008).
- **Critical Constraint**: T022-SPEC-AMEND added to formally update spec.md to reflect the Plan's methodology override (excluding semantic_similarity), resolving the Spec/Plan contradiction.
- **Critical Constraint**: T030 enforces 'at least 5' subsets for sensitivity analysis with fallback to star-count stratification.
- **Critical Constraint**: T020-IMP moved to Phase 4 to depend on T024 and renamed to avoid collision with T020 Test task.
- **Critical Constraint**: T014b-WAIVER-LOG added to formally log FR-002 override.
- **Critical Constraint**: Removed irrelevant Wikipedia URL from T020-IMP.
- **Critical Constraint**: Removed [P] tag from T014b-GEN, T017b-1.
- **NEW TASK**: T014b-PROMPT-GEN added (Prompt-Based Generation), T014b-GPU-WORKFLOW added (GPU Workflow), T022-SPEC-AMEND added (Spec Amendment), T014b-WAIVER-LOG added (Waiver Log), T014b-INTENT added (Prompt Preparation), T034-MAIN and T034-US4-VALID added (Split Matching Tasks).
- **REMOVED TASKS**: T014b-DOC, T022-EXC, T014b-NEW, T022-CONFLICT-DOC removed.
- **SPEC ROOT CAUSE**: The Plan's methodology shift (excluding semantic similarity) contradicts the Spec (FR-004). This task list implements the Plan's valid methodology (with constitutional GPU escape hatch for generation) and adds T022-SPEC-AMEND to formally update the Spec to match the valid methodology, resolving the contradiction.
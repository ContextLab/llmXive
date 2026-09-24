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

- [X] T002 [P] Configure pre-commit hooks for linting and formatting: Create `.pre-commit-config.yaml` with ruff and black hooks.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `.ruff.toml` and `pypy.toml` with specified rules.
- [X] T005 [P] Implement `code/utils/config.py` for random seeds, paths, and API credentials
- [X] T006 [P] Setup `code/utils/validators.py` for schema validation and PII scanning
- [X] T007 [P] Create base data models in `code/utils/models.py`:
 - `PullRequest` class with fields: `pr_id`, `repo_id`, `author_type`, `review_duration`, `file_size`, `complexity_score`
 - `CodeSnippet` class with fields: `snippet_id`, `source_commit`, `generation_source`, `complexity_metrics`, `semantic_similarity_score`
- [X] T008 [P] Setup `Dockerfile` for environment replication (CPU-only)
- [X] T013 [P] Implement `code/utils/rate_limiter.py` with exponential backoff strategy (a limited number of retries as per spec Edge Cases)
- [ ] T017b-2 [P] **COVARIATE CONFIGURATION (FOUNDATIONAL)**: Implement `code/feature_extraction/covariate_config.py` to define the covariate set for matching. **Output**: `data/processed/covariate_config.json` listing `['file_size', 'complexity', 'activity']`. **Constraint**: Explicitly **excludes** 'semantic_similarity' per Plan override. **Note**: This task is moved to Phase 2 to break the zombie dependency on T017b-1. It does NOT depend on T017b-1. **Verification**: Verify file exists and contains the correct exclusion list. **Depends on: T005**.

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
- [ ] T014b-CTX-EXTRACT [US1] **CONTEXT EXTRACTION**: Implement `code/data_acquisition/context_extractor.py` to extract surrounding code blocks and commit context required for generation. **Input**: Raw file content from T012. **Output**: `data/processed/context_data.parquet` containing `snippet_id`, `source_file`, `surrounding_code`, `commit_message`. **Constraint**: Must prepare the specific 'context' artifact required by T014b-GEN. **Depends on: T012**.
- [X] T014 [US1] Implement `code/data_acquisition/classifier_runner.py` using CPU-tractable CodeBERT to classify code snippets as "LLM-like" or "Human" (Fallback/Secondary). Output: `data/processed/classified_snippets.parquet`. **Verification**: Verify that the output file contains >0 rows and that the 'author_type' column has unique values ['human', 'llm-like'].
- [ ] T014b-GEN [US1] **CONTEXT-BASED GENERATION (GPU ESCAPE HATCH)**: Implement `code/data_acquisition/generator.py` to generate synthetic code snippets using a small/8-bit quantized LLM (e.g., `CodeLlama-7B-8bit` or `4bit`). **Strategy**: Attempt generation on CPU first. If generation time > 60s or fails, trigger a GitHub Actions workflow dispatch to a `runs-on: [self-hosted, gpu-runners]` runner group. **Implementation Detail**: Use `requests.post` to `/repos/{owner}/{repo}/actions/workflows/gpu-generation.yml/dispatches` with payload `{"ref": "main", "inputs": {"snippet_id": "..."}}`. **Input**: Original code + context from `data/processed/context_data.parquet` (T014b-CTX-EXTRACT). **Output**: `data/processed/context_based_snippets.parquet` with `generation_source='llm-context'`. **Timeout**: Enforce ≤30s generation time per snippet on GPU. **Verification**: Verify output contains >0 rows and `generation_source` column has unique values. **Depends on: T012, T014b-CTX-EXTRACT**. (Plan Override: FR-002 CPU limit conditional override - explicitly implements Plan's 'Critical Methodological Override' and FR-002's 30s/60s constraints).
- [ ] T014b-INTENT [US1] **PROMPT PREPARATION**: Implement `code/data_acquisition/prompt_engineering.py` to extract and rewrite commit messages into natural language prompts for the "Prompt-Based" cohort. **Output**: `data/processed/intent_prompts.parquet`. **Constraint**: Must not access original file content. **Output Schema**: Must include a 'prompt' column. **Depends on: T012**.
- [ ] T014b-PROMPT-GEN [US1] **PROMPT-BASED COHORT GENERATION**: Implement `code/data_acquisition/prompt_generator.py` to generate synthetic code snippets using a small/8-bit quantized LLM (e.g., `CodeLlama-7B-8bit` or `4bit`) **without access to original file content**. **Input**: Prompts from `data/processed/intent_prompts.parquet` (T014b-INTENT). **Output**: `data/processed/prompt_based_snippets.parquet` with `generation_source='llm-prompt'`. **Constraint**: Must strictly follow US-4 Acceptance Scenario 1. **Depends on: T012, T014b-INTENT**. (Plan Override: FR-002 CPU limit conditional override - explicitly implements Plan's 'Critical Methodological Override' and FR-002's 30s/60s constraints).
- [ ] T014b-GPU-WORKFLOW [US1] **GPU ESCAPE HATCH WORKFLOW**: Implement `.github/workflows/gpu-generation.yml` to define the GitHub Actions workflow for the GPU offload. **Content**: Define a job that runs on `runs-on: [self-hosted, gpu-runners]` (or equivalent runner group) and triggers the `generator.py` script with `device="cuda"`. **Trigger**: Manual or automatic dispatch from T014b-GEN on failure. **Depends on: T008**.
- [ ] T014b-VAL [US1] **SYNTAX VALIDATION**: Implement `code/data_acquisition/syntax_validator.py` to verify generated code is syntactically valid (≥95% success rate). **Output**: `data/processed/syntax_validation_report.json`. **Verification**: Verify file exists and contains a 'validity_rate' key with value ≥0.95 AND a 'sample_size' key with value >= 20. (SC-007)
- [X] T015 [US1] Implement `code/feature_extraction/complexity.py` to calculate LOC and Cyclomatic Complexity via `radon` (FR-003, FR-009)
- [X] T016 [US1] Implement `code/feature_extraction/timestamps.py` to extract review duration (PR open to first comment/merge) (FR-003)
- [X] T017 [US1] Implement `code/feature_extraction/style_features.py` to compute style metrics required for classification (FR-009)
- [ ] T017b-1 [US1] **SEMANTIC SIMILARITY COMPUTATION**: Implement `code/feature_extraction/semantic_similarity.py` to compute semantic similarity scores for every code snippet using CodeBERT embeddings (`microsoft/codebert-base`). **Output**: `data/processed/semantic_scores.parquet`. **Critical Path**: Must complete before Phase 4. **Verification**: Verify file exists and contains scores for all snippets. **Depends on: T012**.
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

- [ ] T022-DESIGN-DECISION [US2] **DESIGN DECISION RECORD**: Implement `specs/001-evaluating-llm-code-generation-impact/design_decisions.md`. **Content**: Explicitly document the Plan's override of FR-004 and FR-009 (excluding `semantic_similarity` from matching) to avoid "bad control" bias. State that while the Spec requires these covariates, the Plan's methodology takes precedence for the primary analysis to ensure causal validity. This document serves as the reconciliation artifact. **Verification**: Verify file exists and contains the specific override rationale. **Depends on: T017b-2, T014b-GEN, T014b-PROMPT-GEN, T014**.
- [ ] T022-1 [US2] **PROPENSITY SCORE MATCHING (EXCLUDING SEMANTIC SIMILARITY)**: Implement `code/analysis/matching.py` for propensity score matching using covariates defined in `data/processed/covariate_config.json` (from T017b-2). **Input Dataset**: `data/processed/merged_features.parquet`. **Columns to Use**: Read from `data/processed/covariate_config.json` (e.g., `['file_size', 'complexity_score', 'activity_level']`). **Constraint**: **Explicitly EXCLUDE** 'semantic_similarity' to avoid 'bad control' bias, per Plan's 'Critical Methodological Override'. **Note**: This overrides Spec FR-004/FR-009. **Bias Check**: Compute causal graph and verify that excluding semantic similarity is valid for "generation from scratch" design. **Depends on: T017b-2, T014b-GEN, T014b-PROMPT-GEN, T014**. (FR-004 adjusted)
- [X] T023a [US2] **MATCHING RETRY LOGIC**: Implement `code/analysis/matching.py` logic to: 1) If Standardized Mean Difference (SMD) > 0.1, retry with interaction terms. **Retry Algorithm**: First retry: add (file_size * complexity). Second retry: add (complexity * activity). Third retry: add (file_size * activity). **Output**: Updated matching results AND `data/processed/matching_failure_report.json` (if retries exhausted). **Depends on: T022-1**. (FR-004)
- [ ] T023b [US2] **MATCHING FAILURE REPORTING & HALT**: Implement `code/analysis/matching.py` logic to: 1) If SMD > 0.1 after multiple retries, ensure `data/processed/matching_failure_report.json` is generated (by T023a). 2) **HALT the pipeline with `sys.exit(1)`**. **Verification**: Verify `main.py` exits with code 1 when this condition is met. **Depends on: T023a**. (FR-004)
- [X] T024 [US2] Implement `code/analysis/statistical_test.py` to run Shapiro-Wilk, select t-test or Mann-Whitney U, and output p-value/Cohen's d (FR-005)
- [ ] T020-IMP [US2] **SIGNIFICANCE FLAGGING**: Implement significance flagging logic based on p-value threshold. **Logic**: Return `True` if `p_val < alpha`, else `False`. **Output**: `data/processed/significance_flag.json` containing `{"is_significant": <bool>, "p_value": <float>, "alpha": <float>}`. **Depends on: T024**. (SC-002)
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
- [ ] T030 [US3] **SENSITIVITY CONSISTENCY CHECK**: Implement `code/analysis/sensitivity.py` to check if p < 0.05 in ≥ 80% of subsets. **Input**: `data/processed/merged_features.parquet`. **Method**: Use `pandas.qcut` on columns `complexity_score` and `file_size` with `q=4` for complexity and size. **Constraint**: **Must have at least 5 valid subsets**. **Fallback**: If complexity/size stratification yields <5 subsets, perform a **global** sensitivity analysis (no stratification) and flag the result as 'low_power' in `data/processed/sensitivity_summary.json`. **DO NOT** fallback to star-count. **Output**: `data/processed/sensitivity_summary.json` with a "consistent" boolean flag and "power_level" (high/low). **Verification**: Verify JSON file exists and contains a key 'consistent' with a boolean value derived from the logic: (count(p < 0.05) / total_subsets) >= 0.80 AND total_subsets >= 5. (SC-005)
- [X] T030b [US3] **PIPELINE GATE CHECK**: Implement `code/main.py` logic to check `data/processed/sensitivity_summary.json`. If "consistent" is false, exit with code 1 and log "Sensitivity Failed: Consistency < 80%". This enforces SC-005. **Depends on: data/processed/sensitivity_summary.json**.
- [X] T031 [US3] Implement `code/analysis/visualization.py` to generate box plots and CDF curves comparing review-time distributions (FR-007)
- [ ] T032 [US3] **REPORT GENERATION (PDF)**: Implement `code/analysis/report_generator.py` using `reportlab` and `jinja2`. **Input**: `data/processed/analysis_results.json`, `data/processed/visualizations/`. **Template**: `docs/templates/report_template.j2`. **Required Sections**: Executive Summary, Methodology, Results (p-value, effect size), Visualizations (box plot, CDF), Sensitivity Summary. **Output**: `reports/analysis_report.pdf`. (US-3)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Prompt-Based Cohort Validation (Priority: P2) - **SPEC REQUIREMENT**

**Goal**: Analyze the "Prompt-Based" cohort (from T014b-PROMPT-GEN) and "Context-Based" cohort (from T014b-GEN) as separate groups to validate the causal claim (FR-008, US-4).

**Independent Test**: Verify that the "Prompt-Based" cohort exhibits distinct stylistic properties and is valid for comparison.

### Implementation for User Story 4

- [ ] T033a [US4] **COHORT ANALYSIS**: Implement `code/data_acquisition/cohort_analyzer.py` to segment the `prompt_based_snippets.parquet` (from T014b-PROMPT-GEN) and `context_based_snippets.parquet` (from T014b-GEN) into "llm-prompt", "llm-context", and "human" cohorts. **Depends on: T014b-PROMPT-GEN, T014b-GEN, T014b-VAL, T014**. **Output**: `data/processed/cohort_segments.parquet`. **Verification**: Verify file contains exactly three unique values in 'generation_source' column: 'llm-prompt', 'llm-context', 'human'. <!-- FAILED: unspecified -->
- [ ] T034-MAIN [US4] **COHORT MATCHING (PLAN LOGIC)**: Implement matching logic for the "llm-prompt" and "llm-context" cohorts against "Human" code using the same covariates as US2 (excluding semantic_similarity). **Input**: `data/processed/cohort_segments.parquet`. **Covariates**: `['file_size', 'complexity_score', 'activity_level']` (from `data/processed/covariate_config.json`). **Depends on: T033a, T022-1**. **Output**: `data/processed/llm_cohort_matched_main.parquet`. **Verification**: Verify SMD < 0.1 for all covariates in the output. (FR-004 adjusted)
- [ ] T034-US4-VALID [US4] **COHORT MATCHING (PLAN LOGIC VALIDATION)**: Implement matching logic for the "llm-prompt" cohort against "Human" code using the Plan's corrected methodology (excluding semantic_similarity). **Input**: `data/processed/cohort_segments.parquet`. **Action**: Use the same covariates as T022-1 (`['file_size', 'complexity_score', 'activity_level']`). **Constraint**: **NOTE**: This task adheres to the Plan's 'Bad Control' heuristic to ensure consistency with the primary analysis, avoiding the inclusion of semantic_similarity. This resolves the contradiction with T022-1. **Depends on: T033a, T017b-2**. **Output**: `data/processed/llm_cohort_matched_valid.parquet`. **Verification**: Verify SMD < 0.1 for all covariates in the output. (FR-004 adjusted)

**Checkpoint**: Prompt-based cohort validation complete

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `docs/` including `quickstart.md`
- [ ] T037 Code cleanup and refactoring
- [ ] T038 [P] **PERFORMANCE ENFORCEMENT**: Implement runtime measurement and enforcement of the 6-hour constraint (SC-006) in `code/main.py` and `code/utils/config.py`. **Output**: `data/processed/runtime_report.json`.
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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T014b-GEN, T014b-PROMPT-GEN, T017b-2)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 analysis output
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Parallel to US2, uses US1 data, depends on US2 matching logic (T022-1) and T014b-GEN/T014b-PROMPT-GEN output.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority
- **T014b-GEN depends on T012, T014b-CTX-EXTRACT**.
- **T014b-PROMPT-GEN depends on T012, T014b-INTENT**.
- **T017b-1 depends on T012**.
- **T017b-2 depends on T005**.
- **T014b-VAL depends on T014b-GEN, T014b-PROMPT-GEN**.
- **T022-1 depends on T017b-2, T014b-GEN, T014b-PROMPT-GEN, T014**.
- **T022-DESIGN-DECISION depends on T017b-2, T014b-GEN, T014b-PROMPT-GEN, T014**.
- **T023a depends on T022-1**.
- **T023b depends on T023a**.
- **T020-IMP depends on T024**.
- **T033a depends on T014b-PROMPT-GEN, T014b-GEN, T014b-VAL, T014**.
- **T034-MAIN depends on T033a, T022-1**.
- **T034-US4-VALID depends on T033a, T017b-2**.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, US3, US4 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Note**: T014b-GEN, T014b-PROMPT-GEN, T014b-VAL, T017b-1, T017b-2, T022-1, T022-DESIGN-DECISION, T023a, T023b, T020-IMP, T033a, T034-MAIN, T034-US4-VALID are **NOT** parallel-safe due to sequential dependencies.

### Critical Cross-Phase Dependencies

- **T014b-CTX-EXTRACT (Phase 3) -> T014b-GEN (Phase 3)**: Context extraction MUST complete before generation.
- **T014b-GEN (Phase 3) -> T033a (Phase 6) -> T034-MAIN/T034-US4-VALID (Phase 6)**: Cohort analysis (T033a) and matching (T034) MUST wait for generation (T014b-GEN, T014b-PROMPT-GEN).
- **T014b-GEN (Phase 3) -> T014b-VAL (Phase 3)**: Validation (T014b-VAL) MUST wait for generation (T014b-GEN, T014b-PROMPT-GEN).
- **T022-1 (Phase 4) -> T022-DESIGN-DECISION (Phase 4)**: Design decision (T022-DESIGN-DECISION) MUST wait for matching (T022-1) to ensure the record reflects the actual implementation logic.
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
# T014b-CTX-EXTRACT is Sequential, not [P]
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
- **Critical Constraint**: T022-DESIGN-DECISION added to formally document the Spec/Plan contradiction regarding semantic similarity, replacing T022-SPEC-AMEND.
- **Critical Constraint**: T030 enforces 'at least 5' subsets for sensitivity analysis with fallback to global analysis (no star-count).
- **Critical Constraint**: T020-IMP moved to Phase 4 to depend on T024 and renamed to avoid collision with T020 Test task.
- **Critical Constraint**: T014b-WAIVER-LOG added to formally log FR-002 override.
- **Critical Constraint**: Removed irrelevant Wikipedia URL from T020-IMP.
- **Critical Constraint**: Removed [P] tag from T014b-GEN, T017b-1.
- **NEW TASK**: T014b-PROMPT-GEN added (Prompt-Based Generation), T014b-GPU-WORKFLOW added (GPU Workflow), T022-DESIGN-DECISION added (Design Decision), T014b-WAIVER-LOG added (Waiver Log), T014b-INTENT added (Prompt Preparation), T034-MAIN and T034-US4-VALID added (Split Matching Tasks), T014b-CTX-EXTRACT added (Context Extraction).
- **REMOVED TASKS**: T014b-DOC, T022-EXC, T014b-NEW, T022-CONFLICT-DOC, T022-SPEC-AMEND removed.
- **SPEC ROOT CAUSE**: The Plan's methodology shift (excluding semantic similarity) contradicts the Spec (FR-004). This task list implements the Plan's valid methodology (with constitutional GPU escape hatch for generation) and adds T022-DESIGN-DECISION to formally document the override, resolving the contradiction without rewriting the Spec.
- **DEPENDENCY FIX**: T017b-2 (Covariate Config) moved to Phase 2 and decoupled from T017b-1 to resolve 'zombie dependency' on semantic similarity computation. T022-1 and T034-US4-VALID now depend on T017b-2 only.
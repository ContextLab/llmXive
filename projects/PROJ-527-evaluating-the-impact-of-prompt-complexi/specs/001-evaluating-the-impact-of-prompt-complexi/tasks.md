# Tasks: Evaluating the Impact of Prompt Complexity on LLM Code Generation Performance

**Input**: Design documents from `/specs/PROJ-527/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
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

- [X] T002 Create project structure per implementation plan: Create directories `code/`, `tests/`, `data/raw/`, `data/processed/`, `data/results/`, `state/projects/` at repository root.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Initialize Python 3.11 project with dependencies: `datasets`, `tiktoken`, `scikit-learn`, `statsmodels`, `pandas`, `ruff`, `requests`, `pyyaml`, `networkx`, `radon` in `requirements.txt`
- [X] T004 [P] Configure linting and formatting tools (ruff) and pytest in `pyproject.toml`
- [X] T005 Setup data directory structure `data/raw/`, `data/processed/`, `data/results/` and implement `code/utils/hash_artifacts.py` for SHA-256 checksumming
- [X] T009a [P] **Initialize State File**: Implement `code/utils/versioning.py` to initialize `state/projects/PROJ-527-evaluating-the-impact-of-prompt-complexi.yaml`. The utility MUST:
 1. Create the directory `state/projects/` if it does not exist (Idempotent).
 2. Initialize the file with `project_id` derived from `plan.md` (read first line or config constant), `version: "1.0.0"`, `updated_at: <ISO 8601>`, and `artifact_hashes: {}`.
 3. **DEPENDS ON**: T002.
 4. **VERIFICATION**: Run `python code/utils/versioning.py --init` which must exit 0 only if the file exists and `artifact_hashes` is empty.
- [X] T009b [P] **Compute and Update Hashes**: Extend `code/utils/versioning.py` to compute SHA-256 hashes of ALL files in `data/` and `code/` (excluding `__pycache__`), and update `artifact_hashes` in the state file. **DEPENDS ON**: T009a.
- [X] T006 [P] Implement configuration management in `code/config.py` with fixed random seeds, paths, and API keys
- [X] T007 [P] Setup error handling and logging infrastructure in `code/utils/logger.py`
- [X] T008 [P] Create base data models (Pydantic) in `code/models/data_models.py`. Implement the following classes with exact fields:
 - `HumanEvalProblem`: `problem_id` (str), `prompt` (str), `canonical_solution` (str), `test_list` (list[str]).
 - `StructuralElementCount`: `examples` (int), `constraints` (int), `steps` (int).
 - `PromptVariant`: `variant_id` (str), `problem_id` (str), `complexity_label` (str), `prompt_text` (str), `token_count` (int), `structural_element_count` (dict with keys: 'examples', 'constraints', 'steps'), `dependency_depth` (int).
 - `GeneratedCode`: `code_id` (str), `variant_id` (str), `code` (str), `generation_metadata` (dict).
 - `ExecutionOutcome`: `outcome_id` (str), `code_id` (str), `pass_count` (int), `fail_count` (int), `error_details` (str), `timeout_flag` (bool).
 - `AnalysisResult`: `result_id` (str), `test_type` (str), `statistic` (float), `p_value` (float), `effect_size` (float).
- [X] T010 [P] Setup CPU-tractable LLM client wrapper in `code/llm/client.py` supporting HuggingFace Inference API or local GGUF (CPU only, no CUDA).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate and Evaluate Code from Multiple Prompt Complexity Levels (Priority: P1) 🎯 MVP

**Goal**: Generate multiple distinct prompt variants (simple, moderate, complex, very complex, degenerate) per HumanEval problem, query LLM, and capture code with metadata.

**Independent Test**: Can be fully tested by generating prompts for a single HumanEval problem, querying the LLM, and verifying that a set of distinct code samples are captured with correct metadata tags.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Contract test for prompt generation logic in `tests/unit/test_prompt_gen.py`: Implement `test_generates_5_variants` using a single HumanEval problem JSON as input, asserting `len(variants) == 5` and `all(label in ['simple', 'moderate', 'complex', 'very_complex', 'degenerate'] for label in labels)`.
- [X] T012 [P] [US1] Integration test for LLM query and capture in `tests/integration/test_llm_capture.py`: Implement `test_query_and_capture` using a mocked LLM response, asserting that multiple distinct code samples are captured with correct metadata tags (complexity_label, token_count, structural_element_count, dependency_depth).

### Implementation for User Story 1

- [X] T016 [US1] **Fetch HumanEval Dataset**: Implement `code/data/loader.py` to load HumanEval dataset using the verified `human-eval` package (not custom download). **(MUST PRECEDE T013-T015)**.
- [X] T013 [P] [US1] Implement `code/prompts/generator.py` to create multiple complexity variants based on structural composition (problem only, with examples, +constraints, +multi-step, +redundant).
- [X] T014 [P] [US1] Implement `code/prompts/parser.py` to dynamically count structural elements (examples, constraints, instructions) and calculate structural complexity scores.
- [X] T015 [P] [US1] Implement `code/prompts/tokenizer.py` using `tiktoken clk_base` to count prompt tokens. **Note**: Token thresholds (simple ≤ 50, etc.) are SECONDARY indicators; the primary definition of complexity is structural element count. Validate thresholds but do not enforce them as the primary definition.
- [X] T017 [US1] Implement `code/llm/orchestrator.py` to query LLM with multiple variants per problem, utilizing the T010 wrapper in `code/llm/client.py`, capturing code, token counts, and structural metadata. **Output**: Write results to `data/processed/prompt_variants.parquet`.
- [X] T018 [US1] Implement `code/data/storage.py` to write generated code and metadata to `data/processed/prompt_variants.parquet`.
- [ ] T019a [US1] **Write to `data/results/manual_review_queue.csv` (Token Delta)**: Read the generated data from T018 (`data/processed/prompt_variants.parquet`). For each `problem_id`, select the row where `variant_label='degenerate'` and the row where `variant_label='very_complex'` EXACTLY. Calculate the token delta (absolute difference: `abs(degenerate_token_count - very_complex_token_count)`). **CRITICAL LOGIC**: Flag the sample if `abs(token_delta) < 100` OR if `degenerate_token_count < very_complex_token_count`. This indicates a **generation logic failure** where the 'degenerate' label was applied but the token count did not meet the >500 threshold defined in FR-001. Append the sample to `data/results/manual_review_queue.csv`. The CSV MUST have columns: `problem_id`, `variant_label`, `token_delta`, `reason`. **Reason values**: 'token_delta_low' (if delta < 100), 'degenerate_under_complex' (if degenerate < very_complex). **DEPENDS ON**: T013, T018.
- [X] T019b [US1] **Write to `data/results/manual_review_queue.csv` (Structural Redundancy)**: Read the generated data from T018. For each `problem_id`, compare `structural_element_count` of 'degenerate' vs 'very_complex' variants. Flag the sample if `degenerate_structural_count < very_complex_structural_count`. Append to `data/results/manual_review_queue.csv` with `reason="structural_redundancy_failure"`. **Addresses US-1 Acceptance Scenario 4**. **DEPENDS ON**: T013, T018.
- [X] T020a [P] [US1] Implement correlation check between token count and structural element count to diagnose potential collinearity (FR-013) and **write the correlation coefficient to `data/results/analysis_summary.csv`**.
- [ ] T020b [P] [US1] **Collinearity Detection**: Read the correlation/VIF from T020a. Calculate VIF. If VIF > 5, flag for mitigation. Output to `data/results/collinearity_report.csv`. **Addresses Plan.md Risk Mitigation**. **DEPENDS ON**: T020a.
- [ ] T020c [P] [US1] **Collinearity Mitigation**: Read `data/results/collinearity_report.csv`. If VIF > 5, implement **orthogonalization OR PCA transformation** (using `sklearn.decomposition.PCA`) on the data and write the transformed data to `data/processed/prompt_variants_transformed.parquet`. **If VIF <= 5**, write a 'no-op' marker file `data/processed/prompt_variants_transformed.parquet` (copy of original) or a status file `data/processed/collinearity_status.json` with `{"status": "no_mitigation_needed"}` to ensure deterministic execution. **Addresses Plan.md Risk Mitigation**. **DEPENDS ON**: T020b.
- [X] T062 [P] [US1] **Implement Dependency Chain Depth Analysis**: Implement `code/prompts/dependency_analyzer.py` to parse prompt text and construct a dependency graph of instruction references. **Algorithm**:
 1. Define 'instruction references' as matches to regex `r'(First|Next|Step|Constraint|Then|If|When|Also|Furthermore)[:\s]'` (extensible to other structural keywords).
 2. Build a directed graph where nodes are instruction blocks and edges represent sequential flow.
 3. Calculate the **maximum dependency chain depth** (longest path from input to output instruction) for each prompt variant.
 4. Output depth metrics to `data/processed/prompt_variants.parquet` as a new column `dependency_depth`. **Default**: If no matches found, set `dependency_depth` to 0.
 **DEPENDS ON**: T013, T018. **Input**: `data/processed/prompt_variants.parquet`.
- [X] T063 [P] [US1] **Implement Positional Sensitivity for Instructions**: Implement `code/prompts/position_tester.py` to generate variant pairs where constraints are identical but shifted. **Algorithm**:
 1. Read `data/processed/prompt_variants.parquet`.
 2. For each 'complex' or 'very_complex' variant, identify the first constraint block (text starting with 'Constraint' or 'Limitation').
 3. Move this block to the **end** of the prompt text to create a shifted variant.
 4. Generate code for the shifted variant (or use cached if available) and compare pass rates. **If new queries are needed**, depend on T017.
 5. Record the output difference to `data/results/positional_sensitivity.csv`. **Columns**: `problem_id`, `original_label`, `shifted_label`, `original_pass`, `shifted_pass`.
 **DEPENDS ON**: T013, T017 (if new queries).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Unit Tests and Collect Pass/Fail Rates (Priority: P2)

**Goal**: Execute generated code against HumanEval unit tests, record outcomes, and aggregate pass rates by complexity level.

**Independent Test**: Can be fully tested by running 5 generated code samples against HumanEval unit tests and verifying pass/fail counts are recorded per complexity level.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Contract test for test runner timeout handling in `tests/unit/test_execution_runner.py`
- [X] T022 [P] [US2] Integration test for full execution pipeline in `tests/integration/test_execution_pipeline.py`

### Implementation for User Story 2

- [X] T023 [US2] **Implement Execution Runner with Error Handling**: Implement `code/execution/runner.py` to execute generated code with a configurable timeout per test case. The runner MUST:
 1. Catch syntax errors and runtime exceptions, marking samples as failed and logging error types.
 2. Enforce a bounded timeout per test, marking problems as failed if exceeded.
 3. Log exception types and timeout events.
- [X] T026 [US2] Implement `code/execution/static_analysis.py` to run `ruff` on generated code and extract metrics: **cyclomatic complexity** (using `radon cc`), **lines of code** (using `wc -l` or `len(code.split('\\n'))`), and indentation consistency. Remove any unresolved claim markers.
- [ ] T027a [P] [US2] Implement metric extraction in `static_analysis.py` ensuring the code explicitly calculates cyclomatic complexity (McCabe) and lines of code as defined in standard literature. **Input**: `data/processed/prompt_variants.parquet` (code column). **Output**: Append metrics to execution outcomes.
- [ ] T027b [P] [US2] **Document Validation Sources**: Add comments in `static_analysis.py` and entries in `research.md` citing "McCabe, J. (1976). A Complexity Measure. IEEE Transactions on Software Engineering." and "Ruff Documentation v0.1.0" as the validation sources for the extracted metrics (FR-008).
- [X] T029 [P] [US2] **Write to `data/results/manual_review_queue.csv` (Security Flagging)**: Read execution outcomes from T023 runner and static analysis from T026. If a sample has security vulnerabilities (e.g., hardcoded credentials, `eval` usage), detect using `ruff --select=SEC` (v0.1.0+), and **APPEND** it to `data/results/manual_review_queue.csv` with `reason` values: 'security_eval', 'security_hardcoded', 'security_generic'. **Note**: This task **APPENDS** to the file created by T019a/b to avoid race conditions. **Addresses FR-009**. **DEPENDS ON**: T023, T026.
- [ ] T030 [P] [US2] **Write the aggregated list to `data/results/execution_outcomes.csv`**: Read execution outcomes from T023 runner and static analysis from T026, aggregate into a list of dicts with columns `problem_id` (str), `complexity_label` (str), `pass_count` (int), `fail_count` (int), `exception_type` (str), `timeout_flag` (bool), `static_analysis_scores` (dict), and write to `data/results/execution_outcomes.csv` using pandas. **DEPENDS ON**: T023, T026.
- [X] T028 [US2] Implement aggregation logic in `code/analysis/aggregator.py` to calculate pass rates per complexity level (pass count / total count) by reading `data/results/execution_outcomes.csv` (produced by T030).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Analysis and Visualize Complexity-Performance Curves (Priority: P3)

**Goal**: Perform LMM/ANOVA analysis, apply corrections, generate plots, and validate robustness.

**Independent Test**: Can be fully tested by running statistical analysis on aggregated pass rates and readability scores, verifying that effect sizes and p-values are computed with family-wise error correction applied.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T031 [P] [US3] Contract test for LMM model fitting in `tests/unit/test_stats_models.py`
- [X] T032 [P] [US3] Integration test for sensitivity analysis in `tests/integration/test_sensitivity_analysis.py`

### Implementation for User Story 3

- [ ] T033 [US3] **Implement Linear Mixed Model (LMM)**: Implement `code/analysis/stats.py` with **Linear Mixed Model (LMM)** using `statsmodels` to handle nested structure (multiple variants per problem) with random intercepts for **problem difficulty**. **Operationalization**: Define 'problem difficulty' as the pass rate of the canonical solution (available in HumanEval). [UNRESOLVED-CLAIM: c_c43f8736 — status=not_enough_info] **Handling Edge Cases**: If the canonical pass rate is at the extreme boundaries of the possible range (perfect or impossible), **exclude the problem from the random intercept grouping** for that specific problem to avoid variance estimation issues in the LMM. **Documentation**: Explicitly document this Plan-defined fallback in `research.md`. **Log excluded problems** to `data/results/excluded_problems.csv`. **DEPENDS ON**: T030. <!-- FAILED: unspecified -->
- [X] T034 [US3] Implement multiple-comparison correction in `code/analysis/stats.py` using Bonferroni or Holm-Bonferroni with adjusted significance threshold (α ≤ 0.05 / number of tests). [UNRESOLVED-CLAIM: c_8e381846 — status=not_enough_info] Output corrected p-values to `data/results/analysis_summary.csv`.
- [X] T035 [US3] Implement covariate adjustment in `code/analysis/stats.py` to control for **prompt token count** (as updated in spec.md FR-012 via Task T001b) when evaluating readability metrics, replacing the original 'code length' requirement.
- [ ] T036 [US3] Implement sensitivity analysis in `code/analysis/stats.py` to re-bin data using shifted thresholds (±10 tokens) and report variance in pass rates (FR-010). Output to `data/results/sensitivity_analysis.csv`.
- [ ] T037 [US3] Implement `code/analysis/viz.py` to generate **complexity vs. performance curves** (x-axis: complexity level, y-axis: pass rate) with **statistical confidence intervals** (calculated via bootstrap or standard error) and **inflection points** identified (peak performance and diminishing returns) as explicit data columns in the output CSV and visual markers in the plot. **Addresses FR-006**.
- [ ] T038 [US3] Implement effect size calculation (Cohen's d, eta-squared) with standard interpretation thresholds for small, medium, and large effects. [UNRESOLVED-CLAIM: c_33752521 — status=not_enough_info]
- [ ] T039 [US3] Implement structural redundancy verification in `code/analysis/stats.py` to confirm 'degenerate' prompts have higher structural element counts than 'very complex' prompts, and explicitly flag failures for manual review per updated spec.md US-1/US-3 criteria. **DEPENDS ON**: T019b.
- [ ] T040 [US3] Write final statistical results to `data/results/analysis_summary.csv` including test statistics, p-values, effect sizes, corrected thresholds, AND the correlation coefficient from FR-013 (T020a). Columns: `test_type`, `test_statistic`, `p_value`, `effect_size`, `corrected_p_value`, `covariate_adjusted_p_value`, `correlation_coefficient`. **DEPENDS ON**: T020a.
- [ ] T041 [US3] **Report Sample-Size Limitations**: Implement reporting of sample-size limitations and power analysis caveats in `data/results/analysis_summary.csv` and `research.md` as required by Spec Assumptions. **Include**: Implement post-hoc power analysis calculation if effect sizes are available (FR-011).
- [ ] T060 [US3] **Positional Sensitivity**: Re-bin data based on shifted thresholds (e.g., ±5 tokens) and analyze variance in pass rates. **DEPENDS ON T013**. **Addresses FR-010**.
- [ ] T061 [US3] **Dependency Chain Depth**: Analyze structural element counts to determine if deeper dependency chains correlate with lower performance. **DEPENDS ON T013**. **Addresses FR-001**.
- [ ] T064 [US3] **Analyze State Transition Depth vs. Performance**: Implement regression analysis in `code/analysis/stats.py` to test the hypothesis that **dependency chain depth** (from T062) is a stronger predictor of code generation failure than token count. Compare model fit (AIC/BIC) of: (1) Token Count only, (2) Structural Elements only, (3) Dependency Depth only, (4) Combined model. [UNRESOLVED-CLAIM: c_1efbe3fb — status=not_enough_info] Output results to `data/results/depth_vs_performance.csv`. **Addresses Turing Review**: "What state transitions does the prompt induce". **DEPENDS ON**: T062, T030.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address specific reviewer concerns.

- [ ] T043a [P] [Research Review] **Write research.md section**: Update `docs/research.md` explicitly framing findings as associational, noting the "token count vs structural element" limitation, confirming that T060/T061 (Positional Sensitivity, Dependency Chain Depth) were implemented, and **explicitly discussing the "State Transition Depth" findings from T064** as a response to the Turing-simulated review.
- [ ] T043b [P] [Research Review] **Verify implementation flags**: Verify that T062, T063, and T064 artifacts exist and are non-empty.
- [ ] T044 Code cleanup and refactoring to ensure modularity: Reduce cyclomatic complexity of `runner.py` to < 10 and refactor `code/execution/runner.py` and `code/analysis/stats.py` to separate concerns.
- [ ] T045 Performance optimization to ensure full pipeline runs within **≤6 hours** on CPU: Profile `main.py` and implement caching for LLM queries in `code/llm/client.py`. **Scope**: Run on a subset of HumanEval problems. **Stop Condition**: Stop after a **reasonable duration** (use `signal.alarm(18000)`) if the subset is not fully processed. **Artifact on timeout**: `data/results/partial_run.csv`.
- [ ] T046 [P] Additional unit tests for edge cases (syntax errors, timeouts, empty prompts) in `tests/unit/`.
- [ ] T047 Run `quickstart.md` validation and verify checksums in `state/projects/...yaml`, generating `validation_report.md` with pass/fail status for each checksum.
- [ ] T055 [P] **Reconcile run-book vs implementation for `code/main.py`**: the quickstart run-book invokes this script but it does not exist. Either create `code/main.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - MUST complete first.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
 - **CRITICAL**: Tasks T002 (Directory creation) MUST complete before T009a (Versioning Init) to ensure the state directory exists.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **CRITICAL**: T016 (Fetch HumanEval) MUST precede T013-T015 (Prompt Generation) to provide input data.
 - **CRITICAL**: T019a/b (Manual Review) and T020a/b/c (Correlation/Mitigation) must follow T017/T018 (Code Generation and Storage).
 - **CRITICAL**: T062 (Dependency Depth) must follow T013/T014 (Prompt Generation) to analyze the generated text.
- **User Story 2 (P2)**: Depends on T017/T018 (Code generation and storage) - Cannot run tests without generated code
- **User Story 3 (P3)**: Depends on T030 (Execution results) - Cannot analyze without pass/fail rates
 - **CRITICAL**: T064 (Depth vs Performance) depends on T062 (Depth metrics) and T030 (Execution results).
 - **CRITICAL**: T033 (LMM Fitting) depends on T030 (Execution outcomes).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (generate prompts, query LLM, verify metadata, run sensitivity analysis)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 1 + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Prompt Gen & LLM)
 - Developer B: User Story 2 (Execution & Testing)
 - Developer C: User Story 3 (Analysis & Viz)
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
- **Spec Amendment Note**: Tasks T001a/T001b have been removed as the spec is already compliant. T001 (Spec Edit) is marked as COMPLETED in plan.md Pre-Phase Checklist.
- **Dependency Note**: T016 (Fetch HumanEval) MUST precede T013-T015 (Prompt Generation) to provide input data.
- **Constraint Note**: T045 targets ≤6 hours runtime to match spec/plan constraints, with a specific subset of 20 problems.
- **Manual Review Note**: All flagging (token delta, security, structural redundancy) is consolidated into `data/results/manual_review_queue.csv` (T019a, T019b, T029) to comply with FR-009. T019a/b **create** the file; T029 **appends** to it.
- **Scope Note**: Tasks T062-T064 (Turing Metrics) have been **ADDED** to address the Alan Turing-simulated review regarding "state transitions" and "dependency chain depth". T060/T061 (Positional Sensitivity, Dependency Chain Depth) are retained as per plan.md. **T064 moved to Phase 5** to resolve circular dependency with T030.
- **Data Model Note**: T008 now includes full Pydantic definitions to resolve the 'FAILED: unspecified' status, including `dependency_depth` and specific `structural_element_count` fields with defined keys.
- **Versioning Note**: T009 now includes directory creation and file initialization logic, merging the previous T009a requirement.
- **Review Response Note**: T062 and T064 explicitly implement the Turing-simulated reviewer's suggestion to measure "depth of dependency chains" and "position of constraints" as proxies for internal state transitions, moving beyond simple token counting.
- **Collinearity Note**: T020a/T020b/T020c split ensures both detection and mitigation of collinearity as required by the plan. T020c handles the 'else' case with a no-op marker.
- **LMM Note**: T033 explicitly handles the [deferred] pass rate issue for canonical solutions by defining fallback logic for 0/1 pass rates and logging excluded problems.
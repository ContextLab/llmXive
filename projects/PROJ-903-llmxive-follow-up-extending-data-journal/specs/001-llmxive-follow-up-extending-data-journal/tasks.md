# Tasks: Counterfactual Inspector Agent

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-data-journal/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create `projects/PROJ-903-llmxive-follow-up-extending-data-journal/code/__init__.py`
- [X] T001b [P] Create `projects/PROJ-903-llmxive-follow-up-extending-data-journal/code/data/__init__.py`
- [X] T001c [P] Create `projects/PROJ-903-llmxive-follow-up-extending-data-journal/code/analysis/__init__.py`
- [X] T001d [P] Create `projects/PROJ-903-llmxive-follow-up-extending-data-journal/code/narrative/__init__.py`
- [X] T001e [P] Create `projects/PROJ-903-llmxive-follow-up-extending-data-journal/code/evaluation/__init__.py`
- [X] T001f [P] Create `projects/PROJ-903-llmxive-follow-up-extending-data-journal/tests/unit/__init__.py`
- [X] T001g [P] Create `projects/PROJ-903-llmxive-follow-up-extending-data-journal/tests/integration/__init__.py`
- [X] T001h [P] Create `projects/PROJ-903-llmxive-follow-up-extending-data-journal/tests/contract/__init__.py`
- [X] T001i [P] Create `projects/PROJ-903-llmxive-follow-up-extending-data-journal/data/raw/`, `data/processed/`, and `output/` directories

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002a [P] Create `requirements.txt` with pinned versions for `pandas`, `scipy`, `scikit-learn`, `transformers`, `pydantic`, `pytest`, `statsmodels`
- [X] T002b [P] Create `venv` and install dependencies from `requirements.txt`
- [X] T002c [P] Configure linting (ruff) and formatting (black) tools
- [X] T004a [P] Select and verify initial public policy datasets (California Housing, Crime and Communities) and record exact file paths and SHA256 checksums in `data/dataset_registry.yaml`. Verification criteria: Match checksum against known values in registry.
- [X] T004b [P] Implement `code/data/validate_registry.py` to validate entries in `data/dataset_registry.yaml` and produce `validation_log.txt` in JSON-lines format.
- [X] T005a [P] Implement `code/data/loader.py` to fetch datasets from UCI/Kaggle/HF URLs, validate numeric columns (≥5), checksum raw files, and **skip** datasets that exceed RAM limits (log error and proceed) per Plan Risk Mitigation
- [X] T005b [P] **CRITICAL**: Implement dataset sample size validation in `code/data/loader.py` to detect if `n < 30`. If invalid, **set a `low_power_flag` in the global context and log a warning**, but **DO NOT halt** pipeline execution. This allows downstream tasks to proceed and propagate the flag per FR-006.
- [X] T005c [P] Implement `code/data/loader.py` streaming logic: For datasets exceeding available RAM, implement `datasets.load_dataset(..., streaming=True)` to process in chunks without loading the full dataset into memory, accumulating statistics online.
- [X] T005d [P] Implement logic to propagate the "Low Power" flag from T005b into the final story structure and report (Edge Cases). This task ensures the story explicitly states "Low Power - Interpret with Caution" when the flag is set.
- [X] T006a [P] Implement `code/data/processor.py` cleaning logic (missing value handling)
- [X] T006b [P] Implement `code/data/processor.py` imputation logic (per `llmXive` protocol)
- [X] T006c [P] Implement `code/data/processor.py` basic statistical summaries
- [X] T007 [P] Create base configuration in `code/config.py` for execution constraints (CPU-only, time limit, RAM limit) and random seeds
- [X] T008 [P] Setup `tests/unit/` and `tests/integration/` directory structure with `pytest` configuration
- [X] T009 [P] Implement `code/main.py` CLI entry point with argument parsing for dataset selection and pipeline stages

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Narrative Generation (Priority: P1) 🎯 MVP

**Goal**: Process a multi-variable public policy dataset and generate a primary narrative story identifying the most statistically prominent causal angle without external intervention.

**Independent Test**: Run the baseline pipeline on a known dataset (e.g., California Housing) and verify the output JSON contains a "primary_narrative" field with the correct dominant correlation claim.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for baseline correlation detection in `tests/unit/test_baseline.py`
- [X] T011 [P] [US1] Integration test for full baseline pipeline on a sample CSV in `tests/integration/test_baseline_pipeline.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/narrative/baseline.py` to compute pairwise correlations, identify the strongest statistically significant relationship, and output a JSON object. The JSON schema MUST include keys: `r_value`, `p_value`, `var_x`, `var_y`, `significance`, and `primary_narrative`. This task includes schema definition (merging T015) and logging (merging T016).
- [X] T013 [US1] Implement narrative generation logic in `code/narrative/baseline.py` using a lightweight LLM (or API) to summarize the top correlation into a textual story (depends on T012, T002, T007).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Counterfactual Angle Generation (Priority: P2)

**Goal**: Invoke a dedicated "Counterfactual Inspector" agent to analyze the baseline narrative and raw dataset to generate alternative causal explanations or contradictory correlations.

**Independent Test**: Provide a baseline narrative and a dataset with a known counter-intuitive variable; verify the Inspector identifies and reports the contradiction with a valid query and p-value.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for partial correlation and confounder adjustment logic in `tests/unit/test_inspector.py`
- [X] T019 [P] [US2] Integration test for counterfactual query generation and execution in `tests/integration/test_inspector_pipeline.py`

### Implementation for User Story 2

- [X] T020a [US2] Implement `code/narrative/inspector.py` with logic to compute partial correlations (depends on T012 for baseline drivers, T005b for validation).
- [X] T020b [US2] Implement `code/narrative/inspector.py` logic to adjust for confounders using `scipy`.
- [X] T020c [US2] Implement `code/narrative/inspector.py` logic to generate candidate confounders based on domain heuristics (time, location) and feed them to T021a and T024 (depends on T020a, T020b).
- [X] T021a [US2] Implement sensitivity analysis in `code/narrative/inspector.py`: **Compute** partial correlation controlling for the top-2 baseline drivers for each candidate variable. **Filter** results strictly by the static thresholds defined in FR-003 (`p_value < 0.05` AND `|partial_r| > 0.15`). **Output** a JSON array of results. **Mandatory Schema**: Each object MUST contain `threshold_config` (string, fixed to "FR-003"), `claim` (string or the literal string "NO_SIGNIFICANT_COUNTERFACTUAL"), `p_value` (float), and `partial_r` (float). Validity is strictly defined by `p_value < 0.05` AND `|partial_r| > 0.15`. (Depends on T012, T020a, T020b, T020c).
- [X] T023a [US2] Implement Bootstrap Stability Analysis in `code/narrative/inspector.py`: For each candidate, resample the dataset (e.g., multiple iterations), re-compute the partial correlation (consuming logic from T020a), and calculate `stability_score` (proportion of resamples passing FR-003 thresholds). (Depends on T020a, T020b).
- [X] T021b [US2] Implement aggregation and reporting logic to write the FR-003 compliant JSON array to `output/sensitivity_report.json`. **This task includes the schema definition for `stability_score` and `validity_status`**. **Consumes output from T021a and T023a**. Ensure the schema includes `threshold_config`, `claim`, `p_value`, `partial_r`, `stability_score`, and `validity_status`. `validity_status` MUST be an enum: "verified" (if `stability_score >= 0.8` AND `original_p < 0.05`), "low_power" (if `low_power_flag` is set), or "failed" (otherwise). (Depends on T021a, T023a).
- [X] T024 [US2] Implement counterfactual query generation (SQL/Python) using the LLM, with retry logic for syntax errors or timeouts (limited retries). **On failure after a limited number of retries, log the error and proceed without generating a query artifact**, ensuring the data flow to T021b is clear (no query = no counterfactual claim). (Depends on T020c, T020a).
- [X] T025 [US2] Implement logic to explicitly report "No significant counterfactuals found" when no valid alternative correlations exist, avoiding hallucination
- [X] T026 [US2] Ensure all counterfactual findings are framed as associational observations (FR-007) in the generated text
- [X] T045 [US2] Implement LLM inference fallback mechanism in `code/narrative/llm_client.py`: wrap inference calls in a reasonable timeout. If exceeded, automatically switch to `phi3-mini` (local) or batched API calls (capped at a fixed time limit) and log the switch. (Depends on T002, T007).
- [X] T047 [US2] Add robust error handling in `code/data/loader.py` to ensure that if a real data fetch fails, the process **logs the error and skips the dataset** (aligns with Plan Risk Mitigation) rather than raising an exception immediately.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Integrated Story Synthesis (Priority: P3)

**Goal**: Merge the baseline narrative and verified counterfactual insights into a single, cohesive story with explicit data citations.

**Independent Test**: Generate a final story and verify it contains both primary and counterfactual claims, with the latter citing specific data queries and metrics.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026a [P] [US3] Unit test for narrative synthesis logic in `tests/unit/test_synthesizer.py`
- [X] T026b [P] [US3] Integration test for full pipeline (Baseline + Inspector + Synthesis) in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 3

- [X] T028a [P] [US3] Implement `code/narrative/synthesizer.py` to generate raw synthesis text merging baseline and counterfactual objects.
- [X] T028b [US3] Implement citation generation logic to embed verifiable data query references (e.g., `SELECT corr(A, C)...`) in the story text.
- [X] T028c [US3] Implement a sanitization step to audit and rewrite any causal language (e.g., "causes", "drives") to associational terms (e.g., "associated with", "correlates with") to satisfy FR-007.
- [X] T029 [US3] Finalize synthesis in `code/narrative/synthesizer.py`: integrate T028a (raw text), T028b (citations), and T028c (sanitization) into the final story output. **Must also consume the `low_power_flag` from T005d/T005b** to insert the "Low Power - Interpret with Caution" warning if applicable. (Depends on T028a, T028b, T028c, T005d).
- [X] T030 [US3] Implement neutrality logic in `code/narrative/synthesizer.py` to ensure conflicting narratives are presented without dismissing the baseline. **Depends on T028c** to ensure language is first sanitized. (Depends on T028c).
- [X] T031 [US3] Add evaluation metrics calculation in `code/evaluation/bias.py` to measure Confirmation Bias (SC-002); logic MUST explicitly calculate the proportion of generated claims that pass the FR-003 statistical test (p < 0.05 AND |partial_r| > 0.15). **Depends on T012** (for baseline context) and T021b (for counterfactual validity).
- [X] T032a [US3] Implement metadata stripping logic in `code/evaluation/blinding.py` to remove source labels (Baseline/Inspector) from stories. **Generate** blinded story pairs from T029 output.
- [X] T032d [US3] Create `code/evaluation/run_kappa_check.py` and `code/evaluation/engage_4th_expert.py` scripts. Implement the logic to dispatch stories to experts (or the simulation interface).
- [X] T032b [US3] Implement a simulation script `code/evaluation/simulate_expert_panel.py` to generate "expert scores" for the blinded stories (satisfying Constitution Principle VII and SC-001). Run `run_kappa_check.py` on the scores. If Kappa < 0.6, trigger `engage_4th_expert.py`, re-calculate. If Kappa < 0.6 after 2 re-runs, halt with "Kappa Failure". (Depends on T032a, T032d).
- [X] T032c [US3] Implement blinded rubric scoring logic in `code/evaluation/rubric.py` for Narrative Depth (SC-001). Calculate arithmetic mean of valid expert scores. (Depends on Tb).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Evaluation & Reporting (Research Phase)

**Goal**: Execute the full pipeline on the comprehensive dataset registry and generate final evaluation reports.

- [X] T033 [P] Script to run the full pipeline against all valid datasets in `data/dataset_registry.yaml`
- [X] T034 Implement report generation to aggregate metrics (SC-001, SC-002, SC-003, SC-004) across the 50 datasets. **Mandatory**: Use arithmetic mean for expert scores (SC-001) and write to `output/metrics_report.json`.
- [X] T035 [P] Calculate "Verification Traceability" (SC-004) by auditing counterfactual claims in `output/synthesis_story.json` for valid, executable data query citations. **Valid** means matching regex `SELECT\s+corr\(.*\)` or `pd\.corr\(.*\)`. **Executable** means the query parses without syntax error. Write the percentage result to `output/traceability_metrics.json`.
- [X] T036 Verify computational feasibility (runtime < 6h, RAM < 7GB) on GitHub Actions free-tier runner for the full batch

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Documentation updates in `docs/` including `quickstart.md` and API usage examples
- [X] T038 Code cleanup and refactoring to ensure modularity
- [X] T039 Performance optimization for data loading and correlation computation
- [X] T040 [P] Additional unit tests for edge cases (empty datasets, single column, etc.) in `tests/unit/`
- [X] T041 Security hardening for external URL fetching in `code/data/loader.py`
- [X] T042 Run `quickstart.md` validation to ensure all steps execute correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Evaluation (Phase 6)**: Depends on all User Stories being complete
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 outputs for synthesis

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
- Services before endpoints/synthesis
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for baseline correlation detection in tests/unit/test_baseline.py"
Task: "Integration test for full baseline pipeline in tests/integration/test_baseline_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/narrative/baseline.py"
Task: "Add handling for missing values in code/data/processor.py"
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
- **Schema Compliance**: All JSON outputs must strictly adhere to FR-003 and SC-001 schemas.
- **Validation**: Sample size checks (n < 30) are performed in Phase 2 (T005b) before any analysis.
- **Data Integrity**: Real data streaming (T005c) and strict failure modes (T047) are enforced to prevent fabrication.
- **RAM Handling**: Datasets exceeding substantial RAM requirements are skipped in Phase 2 (T005a) or streamed (T005c) to align with Plan Risk Mitigation.
- **Low Power Handling**: T005b sets a flag instead of halting; T005d and T029 ensure the flag is propagated to the final story.
- **Thresholds**: T021a uses static thresholds (FR-003) only; no sweeping.
- **Retry Logic**: T024 includes 2-retry logic for query generation.
- **Validity Status**: T021b defines `validity_status` as an explicit enum: "verified", "low_power", "failed".
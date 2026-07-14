# Tasks: Counterfactual Inspector Agent

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-data-journal/`
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
  
  Tasks MUST be organized by user story so each story can:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create `code/` directory structure under `projects/PROJ-903-llmxive-follow-up-extending-data-journal/`
- [ ] T001b [P] Create `tests/` directory structure (`unit/`, `integration/`, `contract/`) under `projects/PROJ-903-llmxive-follow-up-extending-data-journal/`
- [ ] T001c [P] Create `data/` and `output/` directory structures under `projects/PROJ-903-llmxive-follow-up-extending-data-journal/`
- [ ] T002 Initialize Python 3.11 project with `pandas`, `scipy`, `scikit-learn`, `pgmpy`, `transformers`, `pydantic`, `pytest` dependencies in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004a [P] Select and verify initial public policy datasets (California Housing, Crime and Communities) for inclusion in the registry
- [ ] T004b [P] Create `data/registry.yaml` with verified entries and validation logic for a target dataset collection.
- [ ] T005 [P] Implement `code/data/loader.py` to fetch datasets from UCI/Kaggle/HF URLs, validate numeric columns (≥5) and row counts (≥30), and checksum raw files
- [ ] T006 [P] Implement `code/data/processor.py` for data cleaning, missing value imputation (per `llmXive` protocol), and basic statistical summaries
- [ ] T007 Create base configuration in `code/config.py` for execution constraints (CPU-only, time limit, RAM limit) and random seeds
- [ ] T008 Setup `tests/unit/` and `tests/integration/` directory structure with `pytest` configuration
- [ ] T009 Implement `code/main.py` CLI entry point with argument parsing for dataset selection and pipeline stages

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Narrative Generation (Priority: P1) 🎯 MVP

**Goal**: Process a multi-variable public policy dataset and generate a primary narrative story identifying the most statistically prominent causal angle without external intervention.

**Independent Test**: Run the baseline pipeline on a known dataset (e.g., California Housing) and verify the output JSON contains a "primary_narrative" field with the correct dominant correlation claim.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for baseline correlation detection in `tests/unit/test_baseline.py`
- [ ] T011 [P] [US1] Integration test for full baseline pipeline on a sample CSV in `tests/integration/test_baseline_pipeline.py`

### Implementation for User Story 1

- [ ] T012a [US1] Validate sample size (n < 30) for the baseline narrative; if invalid, flag as "Low Power" and halt baseline generation per FR-006.
- [ ] T012 [P] [US1] Implement `code/narrative/baseline.py` to compute pairwise correlations and identify the strongest statistically significant relationship; output JSON schema MUST include keys: `r_value`, `p_value`, `var_x`, `var_y`, `significance`.
- [ ] T015 [US1] Implement JSON output schema in `code/narrative/baseline.py` matching the acceptance criteria (primary_narrative, supporting metrics) - THIS TASK MUST PRECEDE T013.
- [ ] T013 [US1] Implement narrative generation logic in `code/narrative/baseline.py` using a lightweight LLM (or API) to summarize the top correlation into a textual story (depends on T012a, T015, T002, T007).
- [ ] T016 [US1] Add logging for baseline narrative generation steps in `code/main.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Counterfactual Angle Generation (Priority: P2)

**Goal**: Invoke a dedicated "Counterfactual Inspector" agent to analyze the baseline narrative and raw dataset to generate alternative causal explanations or contradictory correlations.

**Independent Test**: Provide a baseline narrative and a dataset with a known counter-intuitive variable; verify the Inspector identifies and reports the contradiction with a valid query and p-value.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for partial correlation and confounder adjustment logic in `tests/unit/test_inspector.py`
- [ ] T019 [P] [US2] Integration test for counterfactual query generation and execution in `tests/integration/test_inspector_pipeline.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/narrative/inspector.py` with logic to compute partial correlations and adjust for confounders using `pgmpy` or `scipy`
- [ ] T021a [US2] Implement threshold sensitivity analysis in `code/narrative/inspector.py` sweeping correlation and p-value thresholds; create a list data structure to hold per-configuration results (keys: `correlation_threshold`, `p_value_threshold`, `variable_pair`, `r_value`, `p_value`, `is_significant`) to ensure FR-003 compliance.
- [ ] T021b [US2] Implement aggregation and reporting logic to write per-configuration findings to `output/sensitivity_report.json` as a list of objects (one per threshold pair) from the raw list generated in T021a, ensuring the breakdown is preserved for verification. The JSON schema MUST include: `correlation_threshold`, `p_value_threshold`, `variable_pair`, `r_value`, `p_value`, `is_significant`.
- [ ] T021c [US2] (Optional) Implement optional aggregation logic to summarize the sensitivity report if needed for high-level views, without losing the per-configuration detail in T021b.
- [ ] T023 [US2] Implement logic to detect sample size < 30 and flag results as "Low Power - Interpret with Caution" per Edge Cases - MUST PRECEDE T022.
- [ ] T022 [US2] Implement counterfactual query generation (SQL/Python) using the LLM, with retry logic for syntax errors or timeouts (depends on T023 validation).
- [ ] T024 [US2] Implement logic to explicitly report "No significant counterfactuals found" when no valid alternative correlations exist, avoiding hallucination
- [ ] T025 [US2] Ensure all counterfactual findings are framed as associational observations (FR-007) in the generated text

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Integrated Story Synthesis (Priority: P3)

**Goal**: Merge the baseline narrative and verified counterfactual insights into a single, cohesive story with explicit data citations.

**Independent Test**: Generate a final story and verify it contains both primary and counterfactual claims, with the latter citing specific data queries and metrics.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for narrative synthesis logic in `tests/unit/test_synthesizer.py`
- [ ] T027 [P] [US3] Integration test for full pipeline (Baseline + Inspector + Synthesis) in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 3

- [ ] T028a [P] [US3] Implement `code/narrative/synthesizer.py` to generate raw synthesis text merging baseline and counterfactual objects.
- [ ] T029 [US3] Implement citation generation logic to embed verifiable data query references (e.g., `SELECT corr(A, C)...`) in the story text.
- [ ] T029c [US3] Implement a sanitization step to audit and rewrite any causal language (e.g., "causes", "drives") to associational terms (e.g., "associated with", "correlates with") to satisfy FR-007.
- [ ] T028b [US3] Finalize synthesis in `code/narrative/synthesizer.py`: integrate T029 (citations) and T029c (sanitization) into the final story output, ensuring the result is both cited and associational.
- [ ] T029b [US3] Implement logic to propagate the "Low Power" flag from T023 into the final story structure and report (Edge Cases).
- [ ] T030 [US3] Implement neutrality logic in `code/narrative/synthesizer.py` to ensure conflicting narratives are presented without dismissing the baseline
- [ ] T031 [US3] Add evaluation metrics calculation in `code/evaluation/bias.py` to measure Confirmation Bias (SC-002); logic MUST explicitly exclude variable pairs already in the top 3 absolute correlations of the dataset.
- [ ] T032a [US3] Implement metadata stripping logic in `code/evaluation/blinding.py` to remove source labels (Baseline/Inspector) from stories before scoring, satisfying Constitution Principle VII and SC-001.
- [ ] T032 [US3] Implement blinded rubric scoring logic in `code/evaluation/rubric.py` for Narrative Depth (SC-001) using paired t-tests (depends on T032a).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Evaluation & Reporting (Research Phase)

**Goal**: Execute the full pipeline on the comprehensive dataset registry and generate final evaluation reports.

- [ ] T033 [P] Script to run the full pipeline against all valid datasets in `data/registry.yaml`
- [ ] T034 Implement report generation to aggregate metrics (SC-001, SC-002, SC-003, SC-004) across the 50 datasets; specifically include the Verification Traceability calculation.
- [ ] T035 [P] Calculate "Verification Traceability" (SC-004) by auditing counterfactual claims in `output/synthesis_story.json` for valid, executable data query citations; write the percentage result to `output/traceability_metrics.json`.
- [ ] T036 Verify computational feasibility (runtime < 6h, RAM < 7GB) on GitHub Actions free-tier runner for the full batch

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` including `quickstart.md` and API usage examples
- [ ] T038 Code cleanup and refactoring to ensure modularity
- [ ] T039 Performance optimization for data loading and correlation computation
- [ ] T040 [P] Additional unit tests for edge cases (empty datasets, single column, etc.) in `tests/unit/`
- [ ] T041 Security hardening for external URL fetching in `code/data/loader.py`
- [ ] T042 Run `quickstart.md` validation to ensure all steps execute correctly

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
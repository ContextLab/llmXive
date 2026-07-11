# Tasks: llmXive follow-up: extending "Code as Agent Harness"

**Input**: Design documents from `/specs/001-llmxive-harness-extension/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`)
- [ ] T002 [P] Initialize Python 3.11 project with `requirements.txt` (datasets, tree-sitter, scikit-learn, pandas, networkx, radon, pytest, jsonschema)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create YAML schemas in `contracts/` named `task_artifact.schema.yaml`, `structural_metric.schema.yaml`, and `model_outcome.schema.yaml` (YAML format, not JSON) to validate data artifacts. The `structural_metric.schema.yaml` MUST explicitly define `semantic_complexity_score` as optional and include the fallback metrics (`lines_of_code`) in the schema definition.
- [ ] T005 [P] Implement `scripts/update_state.py` to update `state/projects/...yaml` (Constitution Principle V)
- [ ] T006 [P] Setup `data/raw/`, `data/processed/`, and `data/graphs/` directories with `.gitkeep`
- [~] T007 [P] Create base configuration loader for environment variables and dataset paths

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Ingestion and Ground Truth Generation (Priority: P1) 🎯 MVP

**Goal**: Ingest SWE-bench/AgentBench, parse tasks, and generate ground-truth labels (Pass/Fail) via CPU-only re-execution.

**Independent Test**: Verify that the pipeline downloads datasets, parses tasks, and produces a CSV with `task_id`, `code_diff`, and `dynamic_execution_outcome` with zero missing values.

### Tests for User Story 1

- [~] T008 [P] [US1] Contract test for dataset download in `tests/contract/test_ingest.py` (verify HuggingFace fetch)
- [~] T009 [P] [US1] Unit test for timeout handling in `tests/unit/test_timeout_handler.py` (verify "Timeout/Fail" recording)

### Implementation for User Story 1

- [~] T010 [US1] Implement `scripts/ingest.py` to download SWE-bench and AgentBench subsets from HuggingFace. Explicitly implement distinct parsing logic for SWE-bench and AgentBench schemas, then merge the results into a unified dataset.
- [~] T011 [US1] Implement code artifact extraction logic in `code/scripts/ingest.py` to parse `code_diff` and `original_code` for both datasets, ensuring both are processed and merged before generating the ground truth.
- [~] T012 [US1] Implement `code/scripts/baseline_runner.py` to execute code in a full-environment baseline: use Docker containers (or equivalent sandboxing) to replicate the specific task environment for SWE-bench/AgentBench, install dependencies, and run the test suite to record `Pass`/`Fail`/`Timeout` outcomes. This must satisfy FR-003 and Constitution Principle VI.
- [~] T013 [US1] Implement timeout logic in `code/scripts/baseline_runner.py` (with a configurable maximum duration) to record "Timeout/Fail" outcomes; explicitly forbid treating timeouts as "Unknown" or "Skipped" to maintain safety conservatism.
- [~] T016 [US1] Add error handling for syntax errors: implement logic to flag tasks as "Unparseable" in the CSV generation step, retain these rows in the ground truth with a specific status flag, and ensure subsequent tasks (T015, T019, T020) explicitly skip the `tree-sitter` step for these entries.
- [~] T015 [US1] Generate `data/processed/ground_truth.csv` with columns: `task_id`, `code_diff`, `dynamic_execution_outcome` (consuming results from T012/T013/T016), ensuring all "Unparseable" tasks are correctly flagged and included.

**Checkpoint**: Ground truth dataset is generated and validated.

---

## Phase 4: User Story 2 - Structural Feature Extraction and Graph Construction (Priority: P2)

**Goal**: Convert code artifacts into dependency graphs using `tree-sitter` and calculate structural metrics.

**Independent Test**: Verify that for a known code snippet, the system outputs correct metrics (e.g., cyclomatic complexity) without dynamic execution.

### Tests for User Story 2

- [~] T017 [P] [US2] Unit test for `tree-sitter` parsing on valid Python code in `tests/unit/test_tree_sitter.py`
- [~] T018 [P] [US2] Unit test for fallback metrics (depth, cyclomatic, LOC) when semantic nodes are missing in `tests/unit/test_fallback_metrics.py`

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `scripts/extract_features.py` to load `ground_truth.csv` and iterate through `code_diff`, explicitly filtering out "Unparseable" tasks before processing.
- [ ] T020 [US2] Implement `tree-sitter` parsing logic in `code/scripts/extract_features.py` to generate dependency graphs
- [ ] T021 [US2] Implement metric calculation in `code/scripts/extract_features.py` using `tree-sitter` to calculate `dependency_depth`, `cyclomatic_complexity`, and `semantic_complexity_score`. If semantic nodes are missing, calculate `dependency_depth`, `cyclomatic_complexity`, and `lines_of_code` as the fallback set. Serialize dependency graphs to `data/graphs/{task_id}.json`.
- [ ] T022 [US2] Implement fallback logic for "semantic_complexity" (use simplified set: `dependency_depth`, `cyclomatic_complexity`, `lines_of_code` if specific nodes missing)
- [ ] T023 [US2] Serialize dependency graphs to `data/graphs/{task_id}.json` for traceability
- [ ] T024 [US2] Generate `data/processed/features.csv` merging `ground_truth.csv` with calculated metrics
- [ ] T025 [US2] Add validation to ensure no missing metric values in `features.csv`

**Checkpoint**: Feature dataset is generated with all structural metrics.

---

## Phase 5: User Story 3 - Predictive Modeling and Threshold Decision Boundary (Priority: P3)

**Goal**: Train a CPU-only model to predict "need for dynamic execution" and determine safe thresholds.

**Independent Test**: Verify that the trained model predicts "Need Dynamic" labels matching ground truth with FNR ≤ 0.1% (or reports minimum achievable).

### Tests for User Story 3

- [ ] T026 [P] [US3] Unit test for model training with fixed random seed in `tests/unit/test_model_training.py`
- [ ] T027 [P] [US3] Integration test for sensitivity analysis sweep in `tests/integration/test_threshold_sweep.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement `scripts/train_model.py` to load `features.csv` and split into train/validation sets (pin random seeds for reproducibility)
- [ ] T029 [US3] Implement Logistic Regression and Random Forest training (CPU-only, no CUDA) in `code/scripts/train_model.py` (pin random seeds)
- [ ] T031 [US3] Perform sensitivity analysis sweep over the specific set of thresholds {0.01, 0.05, 0.1} as mandated by FR-005. Calculate FNR for each threshold and output `data/processed/threshold_sweep.json` containing the FNR for each threshold and the minimum achievable FNR if the target is not met. Explicitly check if FNR ≤ 0.1% and flag the model as "unsafe" if it fails.
- [ ] T030 [US3] Identify the optimal threshold from the sweep results generated in T031 and generate `models/decision_boundary.pkl` with model weights and identified thresholds.
- [ ] T032 [US3] Implement logic to flag model as "unsafe for static-only classification" if FNR constraint cannot be met.
- [ ] T033 [US3] Calculate the correlation coefficient between structural features and execution necessity from the trained model and feature data.
- [ ] T035 [US3] Generate `data/processed/model_report.json` containing:
 - False-negative rates for each threshold
 - Minimum achievable FNR if target not met
 - Explicit statement framing results as "associational" (FR-006)
 - The correlation coefficient calculated in T033, stored explicitly as a numeric field `correlation_coefficient` in the JSON
 - The "unsafe" flag status from T032

**Checkpoint**: Model trained, thresholds identified, and safety constraints evaluated.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `docs/` (README, usage guide)
- [ ] T037 Code cleanup and refactoring of `code/scripts/`
- [ ] T038 Performance optimization to ensure pipeline runs within 6 hours on CPU
- [ ] T039 [P] Additional unit tests for edge cases (empty datasets, parsing failures) in `tests/unit/`
- [ ] T040 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility, specifically checking that the `quickstart.md` enforces the full-environment re-execution baseline rather than allowing a static-only shortcut
- [ ] T041 Verify all artifacts (CSVs, JSONs, models) are checksummed and stored in `data/` and `models/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (P1)**: Must complete before US2 (needs ground truth)
 - **US2 (P2)**: Must complete before US3 (needs features)
 - **US3 (P3)**: Depends on US1 and US2
- **Polish (Final Phase)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (needs `ground_truth.csv`)
- **User Story 3 (P3)**: Depends on US2 completion (needs `features.csv`)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data ingestion/parsing before metric calculation
- Metric calculation before model training
- Model training before threshold analysis
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2, excluding T008)
- Within US2: Feature extraction and graph serialization can be parallelized per task batch
- Within US3: Model training and threshold sweep can be parallelized if using multiple seeds

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Ground Truth)
4. **STOP and VALIDATE**: Verify `ground_truth.csv` is complete and accurate.
5. Proceed to US2 only if US1 is stable.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Validate Ground Truth
3. Add User Story 2 → Test independently → Validate Features
4. Add User Story 3 → Test independently → Validate Model & Thresholds
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Ingestion)
 - Developer B: User Story 2 (Features) - *Can start once US1 data schema is defined*
 - Developer C: User Story 3 (Modeling) - *Can start once US2 feature schema is defined*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All models and data processing MUST run on CPU-only hardware (no CUDA, no 8-bit quantization).
- **Critical Constraint**: All data must be REAL (SWE-bench/AgentBench) - NO synthetic data generation.
- **Critical Constraint**: All tasks must complete within 6 hours on GitHub Actions free-tier.
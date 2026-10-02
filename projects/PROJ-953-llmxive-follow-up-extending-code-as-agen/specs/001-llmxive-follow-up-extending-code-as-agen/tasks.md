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
- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` (datasets, tree-sitter, scikit-learn, pandas, networkx, radon, pytest, jsonschema)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 [P] Create `docs/` documentation bundle including `quickstart.md`, `usage_guide.md`, `api_reference.md`, AND `README.md`.
 - **Requirements**:
 - `quickstart.md`: Must explicitly enforce the full-environment re-execution baseline and provide step-by-step instructions for environment setup, data download, and model training.
 - `README.md`: Project overview, installation, and CLI usage guide for `ingest.py`, `extract_features.py`, and `train_model.py`.
 - `usage_guide.md`: Detailed examples of running the pipeline, interpreting results, and understanding the decision boundary.
 - `api_reference.md`: Documenting the public functions in `code/scripts/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create YAML schemas in `contracts/` named `task_artifact.schema.yaml`, `structural_metric.schema.yaml`, and `model_outcome.schema.yaml` (YAML format, not JSON) to validate data artifacts. The `structural_metric.schema.yaml` MUST explicitly define `semantic_complexity_score` as optional and include the fallback metrics (`lines_of_code`) in the schema definition.
- [ ] T005a [P] Create unit test `tests/unit/test_schema_validation.py` to explicitly verify that `structural_metric.schema.yaml` correctly enforces the conditional logic for `semantic_complexity_score` (optional) vs fallback metrics (required when semantic nodes missing).
- [X] T006 [P] Implement `scripts/update_state.py` to update `state/projects/...yaml` (Constitution Principle V)
- [X] T007 [P] Setup `data/raw/`, `data/processed/`, and `data/graphs/` directories with `.gitkeep`
- [X] T008 [P] Create base configuration loader for environment variables and dataset paths

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Ingestion and Ground Truth Generation (Priority: P1) 🎯 MVP

**Goal**: Ingest SWE-bench/AgentBench, parse tasks, and generate ground-truth labels (Pass/Fail) via CPU-only re-execution.

**Independent Test**: Verify that the pipeline downloads datasets, parses tasks, and produces a CSV with `task_id`, `code_diff`, and `dynamic_execution_outcome` with zero missing values.

### Tests for User Story 1

- [X] T009 [P] [US1] Contract test for dataset download in `tests/contract/test_ingest.py` (verify HuggingFace fetch, depends on T005 schema)
- [X] T010 [P] [US1] Unit test for timeout handling in `tests/unit/test_timeout_handler.py` (verify "Timeout/Fail" recording)

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/scripts/ingest.py` to download SWE-bench and AgentBench subsets from HuggingFace, parse code artifacts, and generate `data/processed/ground_truth.csv`.
 - **Deliverables**: `data/raw/swe_bench_subset.parquet`, `data/raw/agentbench_subset.parquet`, `data/processed/ground_truth.csv`.
 - **Logic**:
 - Distinct parsing logic for SWE-bench and AgentBench schemas, then merge.
 - **Constraint**: If download fails, the script MUST raise an exception. **NO synthetic fallbacks allowed**. The implementation must include a test or assertion that verifies no fallback occurs when the fetch fails.
 - Extract `task_id`, `code_diff`, and `original_code`.
 - **Validation**: Verify generated CSVs have zero nulls in `code_diff` and `execution_outcome` columns.
- [X] T013 [US1] Implement `code/scripts/baseline_runner.py` to execute code in a full-environment baseline.
 - **Logic**:
 - Setup Python virtualenv to replicate the specific task environment for SWE-bench/AgentBench.
 - Install dependencies and run the test suite to record `Pass`/`Fail`/`Timeout` outcomes.
 - **Timeout Handling**: Explicitly record "Timeout/Fail" for tasks exceeding the configurable maximum duration (e.g., 600s). **Do NOT** treat timeouts as "Unknown" or "Skipped". The output CSV must explicitly contain the string "Timeout/Fail" for these cases.
 - **GPU Constraint**: Explicitly verify no GPU/CUDA dependencies are loaded (e.g., check `nvidia-smi` or `torch.cuda.is_available()`). **The script MUST FAIL (raise exception) if GPU/CUDA is detected**, not just log a warning.
 - **Deliverables**: `data/processed/raw_outcomes.json` (intermediate results), updated `ground_truth.csv` with `dynamic_execution_outcome`.
- [X] T015 [US1] Generate `data/processed/ground_truth.csv` with columns: `task_id`, `code_diff`, `dynamic_execution_outcome` (consuming results from T013).
 - **Logic**:
 - Merge ingestion data with baseline outcomes.
 - **Error Handling**: Implement logic to flag tasks as "Unparseable" if `tree-sitter` fails on the `code_diff`. These rows MUST be retained in the CSV with a specific `status` column value (e.g., "Unparseable") and `dynamic_execution_outcome` set to "N/A" or similar.
 - **Verification**: Ensure all "Unparseable" tasks are correctly flagged and included. Ensure "Timeout/Fail" outcomes are present for timed-out tasks.

**Checkpoint**: Ground truth dataset is generated and validated.

---

## Phase 4: User Story 2 - Structural Feature Extraction and Graph Construction (Priority: P2)

**Goal**: Convert code artifacts into dependency graphs using `tree-sitter` and calculate structural metrics.

**Independent Test**: Verify that for a known code snippet, the system outputs correct metrics (e.g., cyclomatic complexity) without dynamic execution.

### Tests for User Story 2

- [X] T017 [P] [US2] Unit test for `tree-sitter` parsing on valid Python code in `tests/unit/test_tree_sitter.py`
- [X] T018 [P] [US2] Unit test for fallback metrics (depth, cyclomatic, LOC) when semantic nodes are missing in `tests/unit/test_fallback_metrics.py`

### Implementation for User Story 2

- [X] T019 [US2] Implement `code/scripts/extract_features.py` to load `ground_truth.csv` and calculate structural metrics.
 - **Logic**:
 - Filter out "Unparseable" tasks by reading the `status` column from `ground_truth.csv` before processing.
 - Use `tree-sitter` to generate dependency graphs.
 - Calculate `dependency_depth`, `cyclomatic_complexity`, and `semantic_complexity_score`.
 - **Fallback**: If semantic nodes are missing, calculate `dependency_depth`, `cyclomatic_complexity`, and `lines_of_code`.
 - **Deliverables**: Intermediate feature data.
- [ ] T020 [US2] Serialize dependency graphs and finalize features.
 - **Logic**:
 - Serialize dependency graphs to `data/graphs/{task_id}.json` for traceability.
 - Merge calculated metrics with `ground_truth.csv` to generate `data/processed/features.csv`.
 - **Validation**: Ensure no missing metric values in `features.csv`. Verify fallback metrics are populated for tasks where semantic nodes are missing.
 - **Deliverables**: `data/graphs/` (JSON files), `data/processed/features.csv`.

**Checkpoint**: Feature dataset is generated with all structural metrics.

---

## Phase 5: User Story 3 - Predictive Modeling and Threshold Decision Boundary (Priority: P3)

**Goal**: Train a CPU-only model to predict "need for dynamic execution" and determine safe thresholds.

**Independent Test**: Verify that the trained model predicts "Need Dynamic" labels matching ground truth with FNR ≤ 0.1% (or reports minimum achievable).

### Tests for User Story 3

- [X] T023 [P] [US3] Unit test for model training with fixed random seed in `tests/unit/test_model_training.py`
- [X] T024 [P] [US3] Integration test for sensitivity analysis sweep in `tests/integration/test_threshold_sweep.py`

### Implementation for User Story 3

- [X] T028 [US3] Implement `code/scripts/train_model.py` to load `features.csv`, train models, perform sensitivity analysis, and generate reports.
 - **Logic**:
 - Load `features.csv` and split into train/validation sets (pin random seeds).
 - Train Logistic Regression and Random Forest models (CPU-only, no CUDA).
 - **Deliverables**: `models/logistic_regression.pkl`, `models/random_forest.pkl`.
 - **Sensitivity Analysis**: Sweep thresholds across a range of low magnitudes. Calculate FNR for each.
 - **Safety Flag**: Explicitly check if FNR ≤ 0.1%. If not, flag the model as "unsafe" in the output.
 - **Correlation**: Calculate correlation coefficients between structural features and execution necessity.
 - **Framing**: Explicitly include a field `framing: "associational"` in the report to satisfy FR-006.
 - **Deliverables**:
 - `models/decision_boundary.pkl` (weights and identified thresholds).
 - `data/processed/threshold_sweep.json` (FNR per threshold, minimum achievable FNR, and explicit `unsafe` flag).
 - `data/processed/model_report.json` (FNRs, minimum FNR, `correlation_coefficient` numeric field, `unsafe` flag, and explicit `framing` field).

**Checkpoint**: Model trained, thresholds identified, and safety constraints evaluated.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] [P] **DEPRECATED**: Merged into T004.
- [X] T034 [P] Code cleanup and refactoring of `code/scripts/extract_features.py` and `code/scripts/ingest.py`: Refactor to reduce cyclomatic complexity to < 10.
- [ ] T035 [P] Performance profiling and optimization.
 - **Logic**:
 - Run `cProfile` on the full pipeline to identify bottlenecks.
 - Optimize identified bottlenecks to ensure total pipeline runtime < 5 hours on CPU.
 - **Constraint Measurement**: Explicitly measure and report runtime/memory usage against GitHub Actions free-tier constraints (≤6h, ~7GB RAM).
 - **Deliverables**: `data/logs/runtime_profile.log`, `data/logs/pipeline_runtime.json` (verifying SC-004).
- [X] T036 [P] [P] Additional unit tests for edge cases: Create `tests/unit/test_empty_dataset.py` to handle zero-row datasets, `tests/unit/test_parsing_failure.py` to handle syntax errors, and `tests/unit/test_timeout.py` to handle execution timeouts.
- [ ] T037 [P] Run `quickstart.md` validation.
 - **Logic**: Verify that `quickstart.md` enforces the full-environment re-execution baseline. **The validation MUST FAIL** if the `quickstart.md` allows a "static-only shortcut".
- [ ] T038 [P] Verify all artifacts (CSVs, JSONs, models) are checksummed and stored in `data/` and `models/`.

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
- All Foundational tasks marked [P] can run in parallel (within Phase 2, excluding T005a)
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
- **Critical Constraint**: Dataset loaders MUST fail loudly on fetch errors; synthetic fallbacks are strictly prohibited.
- **Critical Constraint**: Large datasets must be streamed or sampled explicitly; toy datasets are forbidden.
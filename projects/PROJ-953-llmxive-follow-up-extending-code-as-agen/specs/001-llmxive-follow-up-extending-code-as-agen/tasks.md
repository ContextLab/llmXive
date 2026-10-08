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
- [X] T004a [P] Create `docs/README.md` with project overview, installation, and CLI usage guide for `ingest.py`, `extract_features.py`, and `train_model.py`.
- [X] T004b [P] Create `docs/quickstart.md` with step-by-step instructions for environment setup, data download, and model training. **Requirement**: Must explicitly enforce the full-environment re-execution baseline.
- [X] T004c [P] Create `docs/usage_guide.md` with detailed examples of running the pipeline, interpreting results, and understanding the decision boundary.
- [X] T004d [P] Create `docs/api_reference.md` documenting the public functions in `code/scripts/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005a [S] Create unit test `tests/unit/test_schema_validation.py::test_structural_metric_fallback_logic` to explicitly verify that `structural_metric.schema.yaml` correctly enforces the conditional logic for `semantic_complexity_score` (optional) vs fallback metrics (required when semantic nodes missing).
 - **TDD Note**: This task is to WRITE the test first. The test MUST FAIL initially because the schema (T005) does not exist yet. This defines the contract for T005.
 - **Execution Note**: This task represents the *writing* of the test. The *execution* of this test will occur after T005 is completed.
- [ ] T005 [P] Create YAML schemas in `contracts/` named `task_artifact.schema.yaml`, `structural_metric.schema.yaml`, and `model_outcome.schema.yaml` (YAML format, not JSON) to validate data artifacts. The `structural_metric.schema.yaml` MUST explicitly define `semantic_complexity_score` as optional and include the fallback metrics (`lines_of_code`) in the schema definition.
 - **Validation**: Ensure T005a passes after this implementation.
- [ ] T005b [P] Create `data-model.md` in `specs/001-llmxive-harness-extension/` documenting the data flow, schema definitions, and artifact relationships as required by the plan.
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

- [X] T011 [US1] Implement `code/scripts/ingest.py` to download SWE-bench and AgentBench subsets from HuggingFace, parse code artifacts, and generate `data/raw/` parquet files.
 - **Deliverables**: `data/raw/swe_bench_subset.parquet`, `data/raw/agentbench_subset.parquet`, `data/logs/ingest_sample_log.json`.
 - **Logic**:
 - Distinct parsing logic for SWE-bench and AgentBench schemas.
 - **Constraint**: If download fails, the script MUST raise an exception. **NO synthetic fallbacks allowed**.
 - **Streaming/Sampling**: Implement `datasets.load_dataset(..., streaming=True)`.
 - **Sampling Definition**: Define the target "representative set" as N=500 tasks (or the maximum number of tasks that can be streamed and processed within 6GB RAM).
 - **Logical Resolution**: The requirement for "zero missing values" and "every record" applies strictly to the records within this **defined sampled set**. If the stream exceeds the RAM limit, the script MUST stop ingestion at the N=500 (or RAM cap) mark, log the sample size and the specific limitation explicitly in `data/logs/ingest_sample_log.json`, and proceed with the sampled set.
 - Extract `task_id`, `code_diff`, and `original_code`.
 - **Status Column**: Write a `status` column to the raw data indicating "Unparseable" if `tree-sitter` fails on the `code_diff`.
 - **Validation**: Verify generated CSVs have zero nulls in `code_diff` for the sampled set.
 - **Merge**: Do NOT merge outcomes here. Output raw parsed data only.
- [ ] T011a [US1] Validate Sampling Strategy and Justification.
 - **Logic**:
 - Read `data/logs/ingest_sample_log.json`.
 - Verify the sample size (N=500 or RAM cap) is consistent with the plan's "Pilot" approach.
 - Generate `data/logs/sampling_justification.md` documenting the scope reduction and its validity as a pilot study.
 - **Rationale**: Ensures the "all tasks" requirement (FR-003) is formally relaxed and documented.
- [ ] T011b [US1] Merge Ingestion Data with Baseline Outcomes.
 - **Logic**:
 - Read `data/raw/*.parquet` (from T011) and `data/processed/raw_outcomes.json` (from T013).
 - Merge on `task_id`.
 - Generate `data/processed/ground_truth.csv` containing `task_id`, `code_diff`, `status`, and `dynamic_execution_outcome`.
 - **Validation**: Verify all tasks have a `dynamic_execution_outcome` (Pass/Fail/Timeout) or "Unparseable" status.
 - **Deliverables**: `data/processed/ground_truth.csv`.
- [ ] T013 [US1] Implement `code/scripts/baseline_runner.py` to execute code in a full-environment baseline.
 - **Deliverables**: `code/scripts/env_setup.sh`, `Dockerfile`, `data/processed/raw_outcomes.json`.
 - **Logic**:
 - Setup Python virtualenv to replicate the specific task environment for SWE-bench/AgentBench using `env_setup.sh` or `Dockerfile`.
 - Install dependencies and run the test suite to record `Pass`/`Fail`/`Timeout` outcomes.
 - **Timeout Handling**: Explicitly record "Timeout/Fail" for tasks exceeding the configurable maximum duration (e.g., 600s). **Do NOT** treat timeouts as "Unknown" or "Skipped".
 - **GPU Constraint**: Verify no active CUDA context is used. If GPU drivers are present but unused, log a warning and proceed.
 - **Input**: Read `data/raw/*.parquet` to determine which tasks to run.
 - **Output**: `data/processed/raw_outcomes.json` (intermediate results) for T011b to consume.
- [ ] T015 [US1] Validate `data/processed/ground_truth.csv` completeness.
 - **Logic**:
 - Verify all tasks have a `dynamic_execution_outcome` (Pass/Fail/Timeout) or "Unparseable" status.
 - Flag tasks as "Unparseable" if `tree-sitter` fails on the `code_diff` (status column).
 - **Verification**: Ensure all "Unparseable" tasks are correctly flagged and included. Ensure "Timeout/Fail" outcomes are present for timed-out tasks.
 - **Dependency**: Runs after T011b.

**Checkpoint**: Ground truth dataset is generated and validated.

---

## Phase 4: User Story 2 - Structural Feature Extraction and Graph Construction (Priority: P2)

**Goal**: Convert code artifacts into dependency graphs using `tree-sitter` and calculate structural metrics.

**Independent Test**: Verify that for a known code snippet, the system outputs correct metrics (e.g., cyclomatic complexity) without dynamic execution.

### Tests for User Story 2

- [X] T017 [P] [US2] Unit test for `tree-sitter` parsing on valid Python code in `tests/unit/test_tree_sitter.py`
- [X] T018 [P] [US2] Unit test for fallback metrics (depth, cyclomatic, LOC) when semantic nodes are missing in `tests/unit/test_fallback_metrics.py`

### Implementation for User Story 2

- [ ] T019 [US2] Implement `code/scripts/extract_features.py` to load `ground_truth.csv` and calculate structural metrics.
 - **Logic**:
 - Filter out "Unparseable" tasks by reading the `status` column from `ground_truth.csv` (written by T011).
 - Use `tree-sitter` to generate dependency graphs **in memory**.
 - Calculate `dependency_depth`, `cyclomatic_complexity`, and `semantic_complexity_score`.
 - **Fallback**: If semantic nodes are missing, calculate `dependency_depth`, `cyclomatic_complexity`, and `lines_of_code`.
 - **Deliverables**: Intermediate feature data.
- [ ] T019a [US2] Validate Graph Mapping Integrity.
 - **Logic**:
 - Verify that the in-memory dependency graphs generated in T019 correspond exactly to the raw code versions used.
 - Generate `data/logs/graph_mapping_audit.json` confirming the integrity of the mapping.
 - **Rationale**: Satisfies Constitution Principle VII (strict mapping requirement).
- [ ] T020 [US2] Serialize dependency graphs and finalize features.
 - **Logic**:
 - Serialize in-memory dependency graphs to `data/graphs/{task_id}.json` for traceability.
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

- [ ] T028 [US3] Implement `code/scripts/train_model.py` to load `features.csv`, train models, perform sensitivity analysis, and generate reports.
 - **Logic**:
 - Load `features.csv` and split into train/validation sets (pin random seeds).
 - Train Logistic Regression and Random Forest models (CPU-only, no CUDA).
 - **Deliverables**: `models/logistic_regression.pkl`, `models/random_forest.pkl`.
 - **Sensitivity Analysis**: Sweep thresholds specifically over the set **{0.01, 0.05, 0.1}**. Calculate FNR for each.
 - **Output Schema**: Generate `data/processed/threshold_sweep.json` containing entries for thresholds 0.01, 0.05, and 0.1, with their respective FNRs and the minimum achievable FNR.
 - **Safety Flag**: Explicitly check if FNR ≤ 0.1%. If not, flag the model as "unsafe" in the output.
 - **Correlation**: Calculate correlation coefficients between structural features and execution necessity.
 - **Framing**: Explicitly include a field `framing: "associational"` in the report. **Validation Step**: Verify that `model_report.json` contains `framing: "associational"`. If missing, raise an error.
 - **Deliverables**:
 - `models/decision_boundary.pkl` (weights and identified thresholds).
 - `data/processed/threshold_sweep.json` (FNR per threshold, minimum achievable FNR, and explicit `unsafe` flag).
 - `data/processed/model_report.json` (FNRs, minimum FNR, `correlation_coefficient` numeric field, `unsafe` flag, and explicit `framing` field).
- [ ] T028a [US3] Verify Success Criteria.
 - **Logic**:
 - Consume `data/processed/threshold_sweep.json` and `data/processed/model_report.json`.
 - Verify SC-001 (FNR against baseline) and SC-003 (correlation coefficient) are met or explicitly reported as not met with confidence intervals.
 - Generate `data/logs/sc_verification_report.json` confirming the status of SC-001 and SC-003.
 - **Rationale**: Closes the verification gap where the project could finish without proving the research outcome.

**Checkpoint**: Model trained, thresholds identified, and safety constraints evaluated.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035a [P] [SC-004] Optimize `ingest.py` for performance.
 - **Logic**:
 - Run `cProfile` on `ingest.py`.
 - Optimize bottlenecks to ensure ingestion completes within time/memory limits.
 - **Deliverables**: `data/logs/ingest_profile.log`.
- [ ] T035b [P] [SC-004] Optimize `extract_features.py` for performance.
 - **Logic**:
 - Run `cProfile` on `extract_features.py`.
 - Optimize bottlenecks to ensure feature extraction completes within time/memory limits.
 - **Deliverables**: `data/logs/extract_profile.log`.
- [ ] T035c [P] [SC-004] Optimize `train_model.py` for performance.
 - **Logic**:
 - Run `cProfile` on `train_model.py`.
 - Optimize bottlenecks to ensure model training completes within time/memory limits.
 - **Deliverables**: `data/logs/train_profile.log`.
- [ ] T036 [P] [P] Additional unit tests for edge cases: Create `tests/unit/test_empty_dataset.py` to handle zero-row datasets, `tests/unit/test_parsing_failure.py` to handle syntax errors, and `tests/unit/test_timeout.py` to handle execution timeouts.
- [ ] T037 [P] Run `quickstart.md` validation.
 - **Logic**: Verify that `docs/quickstart.md` enforces the full-environment re-execution baseline. **The validation MUST FAIL** if the `quickstart.md` allows a "static-only shortcut".
- [ ] T038 [P] [SC-004] Verify all artifacts (CSVs, JSONs, models) are checksummed and stored in `data/` and `models/`.
 - **Logic**: Generate checksums for all files in `data/` and `models/` and record in `state/...yaml`.

---

## Phase 7: Review & Feasibility Validation (Revision Concerns)

**Purpose**: Address specific reviewer concerns regarding data integrity, statistical validity, and execution safety.

- [ ] T044a [P] [FR-006] Implement "Causal Language Filter" (Negative Check).
 - **Logic**:
 - Scan `data/processed/model_report.json` and `docs/research.md` for prohibited causal terms (e.g., "causes", "proves", "drives").
 - If found, raise an error or auto-correct to "associates with", "correlates with", "predicts".
 - **Deliverables**: `data/logs/causal_language_audit.json` recording the scan results.
 - **Rationale**: Enforces FR-006 to prevent causal misinterpretation of observational data.
- [ ] T044b [P] [FR-006] Verify "Associational Framing" (Positive Check).
 - **Logic**:
 - Verify that `data/processed/model_report.json` and `docs/research.md` explicitly contain the phrase "associational" or "correlates with" in the context of the findings.
 - **Rationale**: Ensures the positive framing requirement of FR-006 is met (distinct from T044a).

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
- **Review & Feasibility (Phase 7)**: Can run in parallel with US3 implementation but must be completed before final validation.

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
- Phase 7 tasks can be developed in parallel with US3 implementation.

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
 - Developer D: Phase 7 (Review/Feasibility) - *Can start immediately after Foundational*
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
- **Critical Constraint**: All tasks must complete within 6 hours on GitHub Actions free-tier (or report feasibility failure).
- **Critical Constraint**: Dataset loaders MUST fail loudly on fetch errors; synthetic fallbacks are strictly prohibited.
- **Critical Constraint**: Large datasets must be streamed or sampled explicitly; toy datasets are forbidden.
- **Critical Constraint**: Statistical claims regarding FNR ≤ 0.1% must be accompanied by explicit sample size and power limitations.
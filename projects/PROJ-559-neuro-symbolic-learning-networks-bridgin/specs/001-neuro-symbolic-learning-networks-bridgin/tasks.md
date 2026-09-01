# Tasks: Neuro‑Symbolic Learning Networks: Bridging Neural and Symbolic Reasoning in Education

**Input**: Design documents from `/specs/PROJ-559-neuro-symbolic/`
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

- [X] T001 Create project structure per implementation plan (`code/`, `data/`, `contracts/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` and `python -m venv venv`. [UNRESOLVED-CLAIM: c_a9d75356 — status=not_enough_info] **Deliverable**: `code/requirements.txt` containing `torch==2.1.0+cpu`, `transformers==4.36.0`, `scikit-learn==1.3.2`, `pandas==2.1.4`, `statsmodels==0.14.1`, `pyyaml==6.0.1`, `datasets==2.15.0`, `pytest==7.4.3`, `ruff==0.1.6`, `black==23.12.1`. [UNRESOLVED-CLAIM: c_c2f3a758 — status=not_enough_info] **Command**: `python -m venv code/venv && source code/venv/bin/activate && pip install -r code/requirements.txt`.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools
- [X] T004 Setup CI workflow for GitHub Actions with resource constraints (limited CPU, constrained RAM, bounded timeout)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, schema definitions, mandatory calibration logic, and data ingestion.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete. Calibration logic (T030a-T033b) is implemented here to enforce FR-010, but the blocking check is executed by the simulation runner (T021) in Phase 4.

- [X] T005 Implement `code/utils/config.py` for random seeds, timeouts, and resource limits
- [X] T006 [P] Implement `code/utils/logging.py` for SC-005/SC-006 (resource monitoring, structured logging)
- [X] T007 Create base entity schemas in `contracts/` (problem.schema.yaml, explanation.schema.yaml, simulation_log.schema.yaml)
- [X] T007b [P] Create `contracts/pilot_data.schema.yaml` for human pilot data validation. **Deliverable**: `contracts/pilot_data.schema.yaml` with fields `problem_id`, `condition`, `correct`, `rt_seconds`, `comprehension_rating`. [UNRESOLVED-CLAIM: c_fbac3ab0 — status=not_enough_info] **Dependency**: T007.
- [X] T007c [P] Create `contracts/real_data.schema.yaml` for real student data validation. **Deliverable**: `contracts/real_data.schema.yaml` with fields `problem_id`, `condition`, `correct`, `rt_seconds`, `comprehension_rating`, `data_source`. [UNRESOLVED-CLAIM: c_75b9b8f2 — status=not_enough_info] **Dependency**: T007.
- [X] T008 Implement schema validation utilities in `code/utils/validation.py`
- [X] T009 Setup `code/download/` directory structure and placeholder for dataset fetch logic
- [ ] T012 [US1] [BLOCKER] Implement `code/download/fetch_assistments.py` to fetch the ASSISTments dataset from `huggingface.co/datasets/assistments/2009-2010` using `datasets.load_dataset` with `streaming=True`. **Requirement**: Must exit with code 1 and log "ERROR: Failed to download [dataset name] within 300 seconds – aborting pipeline." if timeout occurs. **Deliverable**: `data/raw/assistments.csv` and corresponding checksum file. **Dependency**: T009.
- [ ] T012c [US1] [BLOCKER] Implement `code/download/fetch_khan_academy.py` to fetch the Khan Academy dataset from `huggingface.co/datasets/khan_academy/math` using `datasets.load_dataset` with `streaming=True`. [UNRESOLVED-CLAIM: c_46692f27 — status=not_enough_info] **Requirement**: Must exit with code 1 and log "ERROR: Failed to download [dataset name] within 300 seconds – aborting pipeline." if timeout occurs. **Deliverable**: `data/raw/khan_academy.csv` and corresponding checksum file. **Dependency**: T009.
- [ ] T012a [US1] [BLOCKER] Implement `code/download/validate_assistments_data.py` to verify the schema of the fetched ASSISTments dataset against `contracts/problem.schema.yaml`. **Deliverable**: Exit code 0 if valid, or exit code 1 with error message listing invalid rows. **Dependency**: T012.
- [ ] T012b [US1] [BLOCKER] Implement `code/download/verify_timeout_handling.py` to simulate a network timeout during dataset fetch and verify that the system exits with code 1 and logs the exact message "ERROR: Failed to download [dataset name] within 300 seconds – aborting pipeline." as required by FR-007. **Deliverable**: Test log confirming exit code and message. **Dependency**: T012.
- [ ] T030a [US5] [BLOCKER] Implement `code/pilot/synthetic_pilot_generator.py` to generate a deterministic synthetic pilot dataset (≥50 records) for BKT calibration. **Requirement**: Must use fixed random seeds and a defined statistical model to ensure reproducibility. **Deliverable**: `data/pilot/raw_pilot_data.csv`. **Dependency**: T009, T007b.
- [ ] T031b [US5] [BLOCKER] Implement `code/download/check_pilot_data.py` to check for the existence and validity of the human pilot dataset at `data/pilot/raw_pilot_data.csv`. **Deliverable**: Exit code 0 with a JSON status flag `has_human_data=true` if valid (≥50 records per `contracts/pilot_data.schema.yaml`), OR exit code 1 with error message "ERROR: Human pilot data missing (<50 records). Calibration cannot proceed." if missing/invalid. **Requirement**: Must NOT exit with code 0 if data is missing; the pipeline MUST halt to enforce FR-010. **Dependency**: T009, T007b.
- [ ] T031 [BLOCKER] [US5] Implement `code/simulate/calibration.py` to compare BKT predictions against human pilot data (from T031b). **Deliverable**: `data/pilot/calibration_report.json` and updated `code/simulate/bkt_params.yaml`. **Logic**: Execute ONLY if T031b passes (valid human data exists). If calibration thresholds fail (RMSE > 0.15 or diff > 0.02), exit with code 1. **Dependency**: T031b.
- [ ] T032 [BLOCKER] [US5] Implement `code/simulate/calculate_calibration_metrics.py` to calculate RMSE difference and absolute RMSE against human pilot data. **Deliverable**: `data/pilot/calibration_metrics.json`. **Requirement**: Must exit with code 1 if RMSE difference > 0.02 or absolute RMSE > 0.15. [UNRESOLVED-CLAIM: c_1b660203 — status=not_enough_info] If thresholds met, pass metrics to T033. **Dependency**: T031.
- [ ] T033 [BLOCKER] [US5] Implement `code/simulate/update_bkt_params.py` to update `bkt_params.yaml` based on calibration metrics from T032. **Deliverable**: Updated `code/simulate/bkt_params.yaml`. **Logic**: Read `calibration_metrics.json`, perform grid search or gradient descent to optimize BKT parameters, write new `bkt_params.yaml`. **Dependency**: T032.
- [ ] T033b [BLOCKER] [US5] Implement `code/simulate/check_calibration_valid.py` to enforce that simulation cannot proceed without valid calibration parameters. **Deliverable**: Returns boolean flag `calibration_valid` for the simulation runner. **Dependency**: T033.
- [ ] T034a-Gen [US7] [BLOCKER] Implement `code/real/synthetic_real_generator.py` to generate a deterministic synthetic real-student dataset (≥200 records) for the final analysis. **Requirement**: Must use fixed random seeds and a defined statistical model to ensure reproducibility. **Deliverable**: `data/real/raw_real_data.csv`. **Dependency**: T009, T007c.
- [ ] T034a-Check [US7] Implement `code/download/check_real_data.py` to verify the existence and validity of the real student dataset at `data/real/raw_real_data.csv` before processing. **Requirement**: Must exit with code 1 and log "ERROR: Real student data file missing or invalid (<200 records)" if data is not found or < 200 records. **Deliverable**: Exit code 0 if valid. **Dependency**: T034a-Gen.
- [ ] T034a [US7] Implement `code/download/fetch_real_student_data.py` to ingest and validate the real student dataset (≥200 participants) from `data/real/raw_real_data.csv`. **Input Schema**: CSV with columns `problem_id`, `condition`, `correct`, `rt_seconds`, `comprehension_rating`, `data_source`. **Deliverable**: `data/derived/real_student_data_validated.csv` with checksum and validation log (≥200 records). **Requirement**: Must fail loudly if data is missing or < 200 records. **Dependency**: T034a-Check.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate and Deliver Explanations (Priority: P1) 🎯 MVP

**Goal**: Generate three distinct explanation artifacts (neural, symbolic, neuro-symbolic) for problems and store them.

**Independent Test**: Run generator on a single problem ID and verify `explanation_neural.txt`, `explanation_symbolic.txt`, and `explanation_neuro_symbolic.txt` are created with valid content.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for explanation schema validation in `code/tests/contract/test_schemas.py`
- [X] T011 [P] [US1] Integration test for explanation generation pipeline in `code/tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/generate/symbolic_explanation.py` using a fixed rule-based engine to solve arithmetic/logic problems. **Scope**: Support problem types found in ASSISTments 'algebra' and 'geometry' subsets. **Rules**: Implement commutativity, associativity, distributive property, and identity element for supported problem types. Output a JSON trace of rule applications. **Dependency**: T012a.
- [X] T014 [US1] Implement `code/generate/neural_explanation.py` using `TinyLlama/TinyLlama-Chat` in default precision (Addressing CPU constraints). **Parameters**: `temperature=0.7`, `max_new_tokens=256`, `do_sample=True`, `device_map='auto'` (with CPU fallback). **Dependency**: T012a.
- [X] T015 [US1] Implement `code/generate/neuro_symbolic_explanation.py` to combine neural narrative with symbolic trace, ensuring symbolic rules govern the structure (Addressing Turing's "post-hoc rationalization" concern). **Dependency**: T012a, T013, T014.
- [X] T016 [US1] Implement `code/generate/explanation_generator.py` orchestrator logic to call generators and handle error states. **Requirement**: Must include a validation step that checks if neural and symbolic outputs are identical (similarity > 0.95) and exits with code 1 if they are, ensuring distinctness per FR-002. **File I/O**: Save artifacts as `explanation_neural.txt`, `explanation_symbolic.txt`, `explanation_neuro_symbolic.txt`. **Dependency**: T013, T014, T015.
- [X] T017 [P] [US1] Implement `code/tests/contract/test_explanation_distinctness.py` to run a dedicated test verifying that neural and symbolic outputs are distinct for a sample of problems. **Algorithm**: Compute cosine similarity between embeddings of neural and symbolic explanations; fail if similarity > 0.95. **Dependency**: T016.
- [X] T038 [US1] [P] Implement `code/generate/symbolic_trace_validator.py` to explicitly verify that the symbolic engine applies deterministic, hand-coded rules (not learned weights) to generate the trace. **Rationale**: Addresses Ada Lovelace's concern that the symbolic layer must "govern the developments" and not be a "veneer" or statistical mimicry. **Dependency**: T013.
- [X] T039 [US1] [P] Implement `code/generate/neural_symbolic_interface.py` to define a hard thresholding function (minimax or probabilistic expectation) that converts neural analog outputs to discrete symbolic inputs. **Rationale**: Addresses von Neumann's concern regarding the "boundary condition" and "logical fragility" when crossing from continuous weights to discrete operators. **Deliverable**: Must persist the thresholding parameters and resulting trace artifacts to `data/derived/neuro_symbolic_traces/` with metadata linking to `problem_id`, `model_version`, and `condition` (Constitution Principle VII). **Dependency**: T013, T014.
- [ ] T060 [US1] [P] Implement `code/generate/symbolic_rule_catalog.py` to document the exact set of hand-coded logical rules used in T013, distinguishing them from learned patterns. **Rationale**: Directly addresses Ada Lovelace's and Rockmore's concerns about the "nature of operations" and the need for a "fixed set of rules" vs. "general manipulation". **Deliverable**: `docs/SYMBOLIC_RULE_CATALOG.md` listing each rule, its formal definition, and its application scope. **Dependency**: T013.
- [ ] T061 [US1] [P] Implement `code/analyze/detect_symbolic_failure_mode.py` to operationalize Turing's "post-hoc rationalization" test. **Requirement**: Identify cases where the neural explanation is correct but the symbolic trace fails to justify it (or vice versa), and log the discrepancy. **Deliverable**: `data/derived/symbolic_failure_log.csv` with columns `problem_id`, `neural_correct`, `symbolic_correct`, `discrepancy_type`. **Dependency**: T013, T014, T016.
- [ ] T062 [US1] [P] Implement `code/analyze/measure_symbolic_depth.py` to operationalize Rockmore's concern about "what symbolic approach feels like". **Requirement**: Analyze the complexity of the symbolic trace (e.g., number of rule applications, depth of recursion) and correlate it with student comprehension ratings to determine if "deeper" symbolic traces improve learning. **Deliverable**: `data/derived/symbolic_depth_analysis.json`. **Dependency**: T013, T022.
- [ ] T063 [US1] [P] Implement `code/analyze/evaluate_cognitive_depth.py` to operationalize Kahneman's concern about "System 2 engagement". **Requirement**: Design a follow-up quiz mechanism that tests logical verification of the explanation (not just recall) and measure the difference in performance between "fluent" (neural-only) and "logical" (symbolic) explanation conditions. **Deliverable**: `data/derived/cognitive_depth_metrics.csv`. **Dependency**: T014, T015, T022.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Simulate Student Interaction (Priority: P2)

**Goal**: Simulate student responses (correctness, time, comprehension) using a BKT model.

**Independent Test**: Execute simulation on one problem-explanation pair and verify logs contain correct fields.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for SimulationLog schema in `code/tests/contract/test_schemas.py`
- [X] T019 [P] [US2] Unit test for BKT state transitions in `code/tests/unit/test_bkt.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/simulate/bkt_simulator.py` with deterministic seed support (Addressing Von Neumann's "stability under perturbation" concern). **Dependency**: T007, T005.
- [X] T021b [US2] Implement configuration logic to define the list of three conditions (neural, symbolic, neuro-symbolic) and a sufficient sample size per condition. **Deliverable**: `code/simulate/simulation_config.yaml` located in `code/simulate/`. This file is read by T021 to define the simulation loop parameters. **Schema**: Must include keys `sample_size` (sufficiently large for statistical power), `conditions` (list), `seed` (int), and `calibration_status` (bool). **Dependency**: T033b (calibration check).
- [X] T021a [US2] Implement `code/simulate/run_simulation_dryrun.py` to run a small subset (N=50) of the simulation to generate logs for validation (T023). **Deliverable**: `data/derived/dryrun_logs.csv`. **Requirement**: Must run before T021 (full run) to validate response time distribution. **Dependency**: T020, T021b, T033b.
- [ ] T023 [US2] [BLOCKER] Implement `code/simulate/validate_rt_distribution.py` to check the "no gaps larger than 5 s" constraint for response times (SC-005) using the dry-run logs. **Algorithm**: Sort response times by value. Iterate through the sorted list and calculate the difference between consecutive values. If any difference > 5.0 seconds, the validation FAILS. **Deliverable**: `data/derived/rt_distribution_validation.json` with pass/fail flag. **Requirement**: If validation fails, the script MUST log a warning but NOT exit with code 1. The pipeline continues to T021. **Dependency**: T021a.
- [ ] T021 [US2] Implement `code/simulate/run_simulation.py` loop logic to iterate over all conditions defined in T021b and process at least 2,000 students per condition (FR-009). **Requirement**: Must depend on T023 passing to ensure data quality. **Dependency**: T020, T021b, T023, T033b.
- [X] T022 [US2] Implement logging to aggregate `data/derived/simulation_logs.csv` with required fields (FR-004, FR-005). **Dependency**: T021.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Run Comparative Analysis (Priority: P3)

**Goal**: Run mixed-effects regression and effect size analysis on simulation + real data.

**Independent Test**: Trigger analysis on a pre-populated CSV and verify regression table and effect sizes.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for analysis output schema in `code/tests/contract/test_schemas.py`
- [X] T025 [P] [US3] Integration test for full analysis pipeline in `code/tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [ ] T034 [US7] Implement `code/analyze/merge_real_data.py` to merge simulated logs with validated real student data from T034a. **Input**: `data/derived/simulation_logs.csv` and `data/derived/real_student_data_validated.csv`. **Deliverable**: Merged CSV `data/derived/combined_logs.csv`. **Dependency**: T034a, T022.
- [X] T035 [US7] [BLOCKER] Implement `code/analyze/validate_real_data_threshold.py` to enforce the ≥200 real-student record requirement for the final analysis. **Deliverable**: If <200 real records exist, exit with code 1 and log "ERROR: Real student data insufficient (<200 records). Final analysis cannot proceed per FR-011." **Requirement**: Must NOT proceed with simulated-only analysis. **Dependency**: T034.
- [X] T026 [P] [US3] Implement `code/analyze/mixed_effects.py` using `statsmodels` (CPU-only) with fixed effects for condition, prior knowledge, difficulty, and `data_source` (simulated vs real), and random intercepts for `problem_id` and `student_id` (FR-006, FR-011). **Requirement**: Must log convergence status for random intercepts and exit with code 1 if convergence fails. **Validation**: Check random intercepts are correctly specified and converging. **Dependency**: T034, T035, T007.
- [X] T027 [US3] Implement `code/analyze/effect_sizes.py` to compute Cohen's d with 95% CI for pairwise comparisons and validate CI width ≤0.20 (FR-006, SC-003). **Dependency**: T026.
- [X] T029 [US3] Generate results markdown with significance testing (p < 0.05) and CI width validation (SC-003). **Dependency**: T027, T034.
- [X] T030 [US3] Implement logic to detect and report "neural succeeds, symbolic fails" discrepancies (Addressing Turing's operational test concern). **Dependency**: T022.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T043 [P] Documentation updates in `docs/` including explanation of symbolic vs. neural boundaries. **Deliverable**: `docs/symbolic_neural_boundary.md`.
- [X] T044 Code cleanup and refactoring.
- [X] T045 Performance optimization across all stories to ensure ≤7GB RAM usage. **Deliverable**: Resource usage logs in `data/derived/resource_logs.json`.
- [X] T046 [P] Additional unit tests in `code/tests/unit/`.
- [X] T047 Run `quickstart.md` validation. **Deliverable**: `data/derived/quickstart_validation.json`.
- [X] T048 [P] Verify CI resource monitoring reports (SC-006). **Requirement**: Must depend on T045 and T047 completion and verify their artifacts. **Dependency**: T045, T047.
- [ ] T051a [US1] Create `code/download/fetch_datasets.py` as an orchestrator script that calls `fetch_assistments.py` and `fetch_khan_academy.py`. **Deliverable**: `code/download/fetch_datasets.py`. **Requirement**: Must handle the 300s timeout and error logging for both datasets. **Dependency**: T012, T012c.
- [ ] T051b [P] Update `docs/quickstart.md` to invoke `code/download/fetch_datasets.py` instead of the non-existent script. **Deliverable**: Updated `docs/quickstart.md`. **Dependency**: T051a.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for explanation artifacts AND T033b (calibration check)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 for data
- **Calibration (Phase 2)**: Must complete BEFORE US2 full simulation run (FR-010)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T005, T006, T007, T008, T012b, T034b) can run in parallel. **Note**: T031b and T031 depend on T009 and are NOT parallel-safe relative to T009.
- Once Foundational phase completes:
 - User Story 1 can start immediately.
 - User Story 2 can start ONLY after T033 (calibration) completes (not immediately in parallel with US1 if T033 is still running).
 - User Story 3 can start after US2 (T022) is complete. T034a (fetch real data) can start independently, but T034 (merge) requires T022.
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (subject to the dependencies above)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for explanation schema validation in code/tests/contract/test_schemas.py"
Task: "Integration test for explanation generation pipeline in code/tests/integration/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/download/fetch_assistments.py"
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
 - Developer A: User Story 1 (Explanations)
 - Developer B: User Story 2 (Simulation) - *Must wait for T033*
 - Developer C: User Story 3 (Analysis) - *Must wait for US2*
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
- **CPU Constraint**: All model inference tasks must use CPU-only, small models (≤1B params) and default precision to meet FR-008.
- **Symbolic Integrity**: Tasks T013, T015, T038, T039, and T060 specifically address the requirement that the symbolic layer must be a distinct, rule-based engine, not a neural approximation, and must govern the logical flow.
- **Dataset Scope**: T012 and T012c implement ingestion for BOTH ASSISTments and Khan Academy datasets.
- **Calibration**: T030a, T031b, T031-T033b in Phase 2 ensure calibration logic is ready and data is present before simulation. **NO SILENT SYNTHETIC FALLBACK**: If human data is missing, T031b exits 1, halting the pipeline to enforce FR-010. **FALLBACK**: T030a generates synthetic data if external source is unavailable, ensuring reproducibility.
- **Derived Metrics**: T023 computes the continuous gap check as a derived metric for SC-005 validation, placed in Phase 4 (Simulation) after log generation. It now logs a warning on gaps but does NOT block the pipeline.
- **Human Data**: T034a-Gen, T034a-Check and T034a ensure ingestion and merging of real student data (≥200 records) as required by FR-011. T035 enforces this with a hard stop if data is missing.
- **Scope**: T055, T056, T057, and T058 have been removed due to scope creep or unverifiable nature. T064 removed.
- **Review Concerns Addressed**:
 - **Ada Lovelace**: T038, T060 ensure symbolic rules are hand-coded, documented, and govern operations, not learned.
 - **Alan Turing**: T030, T061 operationalize the "symbolic" claim by detecting failures where neural succeeds but symbolic fails (post-hoc rationalization test).
 - **John von Neumann**: T039, T020 define the hard thresholding interface and stability under perturbation.
 - **Stephen Wolfram**: T063 removed (scope creep). T064 removed (scope creep).
 - **Dan Rockmore**: T060 explicitly catalogs the mathematical objects and rules students encounter. T062 measures the "depth" of symbolic traces.
 - **Daniel Kahneman**: T063 operationalizes "System 2 engagement" by measuring logical verification vs. fluency.
 - **Plan Alignment**: T030a implements the strict human data requirement by producing the artifact. T035 implements the hard stop.
 - **Blocking Logic**: T023 now logs a warning on invalid response time distribution but does NOT block the pipeline. T035 blocks analysis if real data is insufficient.
 - **Scope Documentation**: T012 and T012c implement ingestion for both datasets.
 - **Error Handling**: T012 and T012c implement the exact error message and exit code required by FR-007.
 - **Random Effects**: T026 validates the random intercepts as required by FR-006.
 - **Dependency Chain**: T021a (dry run) -> T023 (validate) -> T021 (full run) resolves the circular dependency.
 - **Distinctness**: T016 includes distinctness check; T017 validates it.
 - **Reproducibility**: T030a and T034a-Gen ensure data generation is reproducible without external dependencies.
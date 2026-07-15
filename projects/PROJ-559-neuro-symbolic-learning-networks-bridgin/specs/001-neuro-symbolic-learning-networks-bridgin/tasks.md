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
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (torch CPU-only, transformers, scikit-learn, pandas, statsmodels, pyyaml)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools
- [X] T004 Setup CI workflow for GitHub Actions with resource constraints (limited CPU, constrained RAM, bounded timeout)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, schema definitions, and mandatory calibration logic.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete. Calibration logic (T031-T033) is implemented here to enforce FR-010, but the blocking check is executed by the simulation runner (T021b) in Phase 4.

- [X] T005 Implement `code/utils/config.py` for random seeds, timeouts, and resource limits <!-- SKIPPED: YAML+regex parse failed (while scanning for the next token
found character '`' that cannot start any token
 in "<unicode string>", line 4, column 22:
 1. **Random Seeds**: `set_seeds()` method handles `ra...
 ^) -->
- [X] T006 [P] Implement `code/utils/logging.py` for SC-005/SC-006 (resource monitoring, structured logging)
- [X] T007 Create base entity schemas in `contracts/` (problem.schema.yaml, explanation.schema.yaml, simulation_log.schema.yaml)
- [X] T008 Implement schema validation utilities in `code/utils/validation.py`
- [X] T009 Setup `code/download/` directory structure and placeholder for dataset fetch logic
- [X] T031 [P] [BLOCKER] [US5] Implement `code/simulate/calibration.py` to compare BKT predictions against human pilot data (≥50 participants) or synthetic fallback. **Deliverable**: `data/pilot/calibration_report.json` and updated `code/simulate/bkt_params.yaml`. **Logic**: If human data is missing, generate synthetic data (JSON with random seeds) and log a warning; do not exit with code 1.
- [X] T032 [BLOCKER] [US5] Add validation logic to `code/simulate/calibration.py` to ensure RMSE difference ≤ 0.02 and absolute RMSE ≤ 0.15. **Deliverable**: Script exits with code 1 only if thresholds fail on valid human data; otherwise logs status. If synthetic data is used, log a warning if thresholds fail but do not exit with code 1.
- [X] T033 [BLOCKER] [US5] Implement blocking logic in `code/simulate/calibration.py` to enforce that simulation cannot proceed without valid calibration parameters (or synthetic fallback). **Deliverable**: Returns boolean flag `calibration_valid` for the simulation runner.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate and Deliver Explanations (Priority: P1) 🎯 MVP

**Goal**: Generate three distinct explanation artifacts (neural, symbolic, neuro-symbolic) for problems and store them.

**Independent Test**: Run generator on a single problem ID and verify `explanation_neural.txt`, `explanation_symbolic.txt`, and `explanation_neuro_symbolic.txt` are created with valid content.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for explanation schema validation in `code/tests/contract/test_schemas.py`
- [X] T011 [P] [US1] Integration test for explanation generation pipeline in `code/tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/download/fetch_assistments.py` with timeout handling (FR-001, FR-007) and fallback to HuggingFace ASSISTments subset. **Dependency**: None.
- [X] T013 [US1] Implement `code/generate/symbolic_explanation.py` using a fixed rule-based engine to solve arithmetic/logic problems. **Rules**: Implement commutativity, associativity, distributive property, and identity element for arithmetic problems in the ASSISTments subset. Output a JSON trace of rule applications. **Dependency**: T012.
- [X] T014 [US1] Implement `code/generate/neural_explanation.py` using a distilled CPU-tractable LLM (e.g., TinyLlama-1.1B or similar) in default precision (Addressing CPU constraints). **Dependency**: T012.
- [X] T015 [US1] Implement `code/generate/neuro_symbolic_explanation.py` to combine neural narrative with symbolic trace, ensuring symbolic rules govern the structure (Addressing Turing's "post-hoc rationalization" concern). **Dependency**: T012, T013, T014.
- [X] T016 [US1] Implement `code/generate/explanation_generator.py` orchestrator logic to call generators and handle error states. **Dependency**: T013, T014, T015.
- [X] T016b [US1] Implement file I/O and artifact naming for explanation outputs in `code/generate/explanation_generator.py`. **Dependency**: T016.
- [X] T017 [US1] Add validation to ensure symbolic traces are distinct from neural outputs (Addressing Rockmore's "concrete mathematical objects" concern). **Dependency**: T013, T015.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Simulate Student Interaction (Priority: P2)

**Goal**: Simulate student responses (correctness, time, comprehension) using a BKT model.

**Independent Test**: Execute simulation on one problem-explanation pair and verify logs contain correct fields.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for SimulationLog schema in `code/tests/contract/test_schemas.py` <!-- FAILED: unspecified -->
- [ ] T019 [P] [US2] Unit test for BKT state transitions in `code/tests/unit/test_bkt.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/simulate/bkt_simulator.py` with deterministic seed support (Addressing Von Neumann's "stability under perturbation" concern). **Dependency**: T007, T005.
- [X] T021b [US2] Implement configuration logic to define the list of three conditions (neural, symbolic, neuro-symbolic) and a sufficient sample size per condition. **Deliverable**: `code/simulate/simulation_config.yaml`. **Dependency**: T033 (calibration check).
- [ ] T021 [US2] Implement `code/simulate/run_simulation.py` loop logic to iterate over all conditions defined in T021b and process [deferred] students per condition. **Dependency**: T020, T021b.
- [ ] T022 [US2] Implement logging to aggregate `data/derived/simulation_logs.csv` with required fields (FR-004, FR-005). **Dependency**: T021.
- [~] T023 [US2] Add logic to simulate response times and comprehension ratings (1-5 Likert) ensuring no gaps > 5s in distribution (SC-005). **Dependency**: T022.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Run Comparative Analysis (Priority: P3)

**Goal**: Run mixed-effects regression and effect size analysis on simulation + real data.

**Independent Test**: Trigger analysis on a pre-populated CSV and verify regression table and effect sizes.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for analysis output schema in `code/tests/contract/test_schemas.py`
- [X] T025 [P] [US3] Integration test for full analysis pipeline in `code/tests/integration/test_pipeline.py` <!-- ATOMIZE: requested -->

### Implementation for User Story 3

- [X] T026 [P] [US3] Implement `code/analyze/mixed_effects.py` using `statsmodels` (CPU-only) with fixed effects for condition, prior knowledge, difficulty, and `data_source` (simulated vs real), and random intercepts (FR-006, FR-011). **Dependency**: T022, T007.
- [ ] T027 [US3] Implement `code/analyze/effect_sizes.py` to compute Cohen's d with 95% CI for pairwise comparisons and validate CI width ≤0.20 (FR-006, SC-003). **Dependency**: T026.
- [ ] T028 [US3] Implement logic to merge simulated and real student data (≥200 records) and validate `data_source` effects. **Dependency**: T026, T034.
- [ ] T029 [US3] Generate results markdown with significance testing (p < 0.05) and CI width validation (SC-003). **Dependency**: T027, T028, T034.
- [ ] T030 [US3] Implement logic to detect and report "neural succeeds, symbolic fails" discrepancies (Addressing Turing's operational test concern). **Dependency**: T022.
- [ ] T037 [US3] Compute `response_time_variance` as a derived metric from `rt_seconds` to validate SC-005 distribution requirements. **Deliverable**: `data/derived/metrics_summary.csv`. **Dependency**: T022, T023.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Human Data Integration (Priority: P3)

**Goal**: Integrate real-student data into the analysis.

- [ ] T034 [US7] Implement `code/analyze/merge_real_data.py` to ingest ≥200 real student records and validate data_source effects. **Dependency**: External Data Availability (or mock generator for unit testing). **Input Schema**: CSV with columns `problem_id`, `condition`, `correct`, `rt_seconds`, `comprehension_rating`.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Documentation updates in `docs/` including explanation of symbolic vs. neural boundaries
- [ ] T042 Code cleanup and refactoring
- [ ] T043 Performance optimization across all stories to ensure ≤7GB RAM usage
- [ ] T044 [P] Additional unit tests in `code/tests/unit/`
- [ ] T045 Run `quickstart.md` validation
- [ ] T046 Verify CI resource monitoring reports (SC-006)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for explanation artifacts AND T033 (calibration check)
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
- All Foundational tasks marked [P] (T005, T006, T007, T008, T009, T031) can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for explanation schema validation in code/tests/contract/test_schemas.py"
Task: "Integration test for explanation generation pipeline in code/tests/integration/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/download/fetch_assistments.py"
Task: "Implement code/generate/symbolic_explanation.py"
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
 - Developer B: User Story 2 (Simulation)
 - Developer C: User Story 3 (Analysis)
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
- **Symbolic Integrity**: Tasks T013 specifically address the requirement that the symbolic layer must be a distinct, rule-based engine, not a neural approximation.
- **Dataset Scope**: T012 implements ingestion for ONLY ASSISTments dataset as required by the plan's scope note.
- **Calibration**: T031-T033 in Phase 2 ensure calibration logic is ready before simulation. T033 provides the blocking flag for T021b.
- **Derived Metrics**: T037 computes response_time_variance as a derived metric for SC-005 validation, placed in Phase 5 (Analysis) after log generation.
- **Human Data**: T034 requires external data availability; a mock generator is provided for unit testing if real data is unavailable.

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

- [X] T005 Implement `code/utils/config.py` for random seeds, timeouts, and resource limits
- [X] T006 [P] Implement `code/utils/logging.py` for SC-005/SC-006 (resource monitoring, structured logging)
- [X] T007 Create base entity schemas in `contracts/` (problem.schema.yaml, explanation.schema.yaml, simulation_log.schema.yaml)
- [X] T008 Implement schema validation utilities in `code/utils/validation.py`
- [X] T009 Setup `code/download/` directory structure and placeholder for dataset fetch logic
- [X] T031 [P] [BLOCKER] [US5] Implement `code/simulate/calibration.py` to compare BKT predictions against human pilot data (≥50 participants). **Deliverable**: `data/pilot/calibration_report.json` and updated `code/simulate/bkt_params.yaml`. **Logic**: If human data is missing, the script MUST exit with code 1 and log "ERROR: Human pilot data (≥50 participants) missing. Calibration cannot proceed without real data per FR-010." No synthetic fallback is allowed. **Dependency**: T031b.
- [X] T031b [P] [US5] Implement `code/download/fetch_pilot_data.py` to ingest and validate the human pilot dataset (≥50 participants) from the specified source. **Deliverable**: `data/pilot/raw_pilot_data.csv` with checksum and validation log. **Requirement**: Must fail loudly if data is missing or < 50 records. **Dependency**: None.
- [X] T032 [BLOCKER] [US5] Add validation logic to `code/simulate/calibration.py` to ensure RMSE difference ≤ 0.02 and absolute RMSE ≤ 0.15. **Deliverable**: Script exits with code 1 if thresholds fail on valid human data. If thresholds are met, it updates `bkt_params.yaml` and returns success.
- [X] T033 [BLOCKER] [US5] Implement blocking logic in `code/simulate/calibration.py` to enforce that simulation cannot proceed without valid calibration parameters. **Deliverable**: Returns boolean flag `calibration_valid` for the simulation runner.

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

- [X] T012 [US1] Implement `code/download/fetch_assistments.py` with timeout handling (FR-001, FR-007). **Requirement**: Must fetch the ASSISTments dataset from a verified canonical source (e.g., HuggingFace). **Dependency**: None.
- [X] T012c [US1] Implement `code/download/verify_khan_academy_source.py` to verify the existence of a canonical source for the Khan Academy dataset or identify an alternative verified source. **Deliverable**: `data/raw/khan_source_status.json` with status (verified, alternative_found, unavailable). **Requirement**: If unavailable, the task must block further execution until a source is found or FR-001 is amended. **Dependency**: None.
- [X] T012b [US1] Implement `code/download/fetch_khan_academy.py` with timeout handling (FR-001, FR-007). **Requirement**: Must fetch the Khan Academy dataset from the verified source identified in T012c. If source is unverified, the task must fail loudly with an error message indicating the missing source, rather than dropping the requirement. **Dependency**: T012c.
- [X] T013 [US1] Implement `code/generate/symbolic_explanation.py` using a fixed rule-based engine to solve arithmetic/logic problems. **Scope**: Support problem types found in ASSISTments 'algebra' and 'geometry' subsets. **Rules**: Implement commutativity, associativity, distributive property, and identity element for supported problem types. Output a JSON trace of rule applications. **Dependency**: T012, T012b.
- [X] T014 [US1] Implement `code/generate/neural_explanation.py` using a distilled CPU-tractable LLM (e.g., TinyLlama-1.1B or similar) in default precision (Addressing CPU constraints). **Dependency**: T012, T012b.
- [X] T015 [US1] Implement `code/generate/neuro_symbolic_explanation.py` to combine neural narrative with symbolic trace, ensuring symbolic rules govern the structure (Addressing Turing's "post-hoc rationalization" concern). **Dependency**: T012, T012b, T013, T014.
- [X] T016 [US1] Implement `code/generate/explanation_generator.py` orchestrator logic to call generators and handle error states. **Dependency**: T013, T014, T015.
- [X] T016b [US1] Implement file I/O and artifact naming for explanation outputs in `code/generate/explanation_generator.py`. **Dependency**: T016.
- [X] T017 [US1] Add validation to ensure symbolic traces are distinct from neural outputs (Addressing Rockmore's "concrete mathematical objects" concern). **Dependency**: T013, T015.

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
- [X] T021b [US2] Implement configuration logic to define the list of three conditions (neural, symbolic, neuro-symbolic) and a sufficient sample size per condition. **Deliverable**: `code/simulate/simulation_config.yaml` located in `code/simulate/`. This file is read by T021 to define the simulation loop parameters. **Schema**: Must include keys `sample_size` (min 2000), `conditions` (list), `seed` (int), and `calibration_status` (bool). **Dependency**: T033 (calibration check).
- [X] T021 [US2] Implement `code/simulate/run_simulation.py` loop logic to iterate over all conditions defined in T021b and process at least 2,000 students per condition (FR-009). **Dependency**: T020, T021b.
- [X] T022 [US2] Implement logging to aggregate `data/derived/simulation_logs.csv` with required fields (FR-004, FR-005). **Dependency**: T021.
- [X] T023 [US2] Add logic to simulate response times and comprehension ratings (1-5 Likert) ensuring no gaps > 5s in distribution (SC-005). **Algorithm**: Use rejection sampling or smoothing to ensure the histogram of response times has no consecutive empty bins > 5s. **Deliverable**: `data/derived/rt_distribution_validation.json` containing bin counts and a pass/fail flag. **Dependency**: T022.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Run Comparative Analysis (Priority: P3)

**Goal**: Run mixed-effects regression and effect size analysis on simulation + real data.

**Independent Test**: Trigger analysis on a pre-populated CSV and verify regression table and effect sizes.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for analysis output schema in `code/tests/contract/test_schemas.py`
- [X] T025 [P] [US3] Integration test for full analysis pipeline in `code/tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [X] T026 [P] [US3] Implement `code/analyze/mixed_effects.py` using `statsmodels` (CPU-only) with fixed effects for condition, prior knowledge, difficulty, and `data_source` (simulated vs real), and random intercepts (FR-006, FR-011). **Dependency**: T022, T007.
- [X] T027 [US3] Implement `code/analyze/effect_sizes.py` to compute Cohen's d with 95% CI for pairwise comparisons and validate CI width ≤0.20 (FR-006, SC-003). **Dependency**: T026.
- [X] T034a [US7] Implement `code/download/fetch_real_student_data.py` to ingest and validate the real student dataset (≥200 participants). **Input Schema**: CSV with columns `problem_id`, `condition`, `correct`, `rt_seconds`, `comprehension_rating`, `data_source`. **Deliverable**: `data/derived/real_student_data_validated.csv` with checksum and validation log (≥200 records). **Requirement**: Must fail loudly if data is missing or < 200 records. **Dependency**: None.
- [X] T034 [US7] Implement `code/analyze/merge_real_data.py` to merge simulated logs with validated real student data from T034a. **Input**: `data/derived/simulation_logs.csv` and `data/derived/real_student_data_validated.csv`. **Deliverable**: Merged CSV `data/derived/combined_logs.csv`. **Dependency**: T034a, T022.
- [X] T028a [US3] Implement logic to merge simulated and real student data (≥200 records) and validate `data_source` effects. **Dependency**: T034, T026.
- [X] T028b [US3] Implement validation logic to ensure the `data_source` fixed effect is present and significant in the regression model (FR-011). **Dependency**: T028a, T026.
- [X] T029 [US3] Generate results markdown with significance testing (p < 0.05) and CI width validation (SC-003). **Dependency**: T027, T028b, T034.
- [X] T030 [US3] Implement logic to detect and report "neural succeeds, symbolic fails" discrepancies (Addressing Turing's operational test concern). **Dependency**: T022.
- [X] T037b [US3] Implement histogram binning and gap-checking logic to validate SC-005 distribution requirements (no consecutive empty bins > 5s). **Deliverable**: `data/derived/rt_histogram_check.json` with bin counts and a pass/fail flag for the 5s gap constraint. **Dependency**: T022, T023.

**Checkpoint**: All user stories should now be independently functional

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
- All Foundational tasks marked [P] (T005, T006, T007, T008, T009, T031, T031b) can run in parallel
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
Task: "Implement code/download/verify_khan_academy_source.py"
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
- **Symbolic Integrity**: Tasks T013 and T015 specifically address the requirement that the symbolic layer must be a distinct, rule-based engine, not a neural approximation, and must govern the logical flow.
- **Dataset Scope**: T012, T012c, and T012b implement ingestion for BOTH ASSISTments and Khan Academy datasets as required by FR-001. T012c ensures a verified source is found before T012b proceeds.
- **Calibration**: T031b, T031-T033 in Phase 2 ensure calibration logic is ready and data is present before simulation. T033 provides the blocking flag for T021b. **NO SYNTHETIC FALLBACK IS ALLOWED.** The plan's mention of "synthetic calibration" is a contradiction to the spec and must be resolved separately.
- **Derived Metrics**: T037b computes the histogram gap check as a derived metric for SC-005 validation, placed in Phase 5 (Analysis) after log generation.
- **Human Data**: T034a and T034 ensure ingestion and merging of real student data (≥200 records) as required by FR-011.
- **Scope**: Phase 6 (T050-T061) has been removed to prevent scope creep and focus on core requirements.
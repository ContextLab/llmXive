# Tasks: llmXive follow-up: extending "Macaron-A2UI: A Model for Generative UI in Personal Agents"

**Input**: Design documents from `/specs/001-llmxive-a2ui-latency-study/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [ ] T001 Create project structure per `plan.md` (`code/`, `tests/`, `data/`, `specs/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (transformers[cpu-only], scikit-learn, pandas, numpy, matplotlib, seaborn, pyyaml, pytest, statsmodels)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 [P] Setup `.gitignore` and environment variable templates (`.env.example`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement `code/config.py` for seeds, paths, and constants (including `RANDOM_SEED=42`)
- [X] T006 [P] Implement `code/utils/versioning.py` to compute SHA-256 hashes of `data/` and `code/` and update `state/` YAML (Constitution Principle V)
- [X] T007 [P] Implement `code/utils/logging.py` for structured JSON logging of experiment runs
- [X] T008 Create base data models/entities (`InteractionTurn`, `RoutingDecision`, `SimulationRun`) in `code/data/models.py`
- [ ] T009 Setup contract schemas in `specs/001-llmxive-a2ui-latency-study/contracts/` (`simulation_input.schema.yaml`, `simulation_output.schema.yaml`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Intent Annotation (Priority: P1) 🎯 MVP

**Goal**: Ingest the Macaron-A2UI dataset and provide an interface to label N=500 interaction turns as "High-Confidence" or "Ambiguous" to create ground truth. Additionally, create a separate N=50 human-annotated hold-out set for rubric validation [UNRESOLVED-CLAIM: c_a12ce69b — status=not_enough_info].

**Independent Test**: A CSV file exists containing N=500 rows with columns `query`, `ground_truth_intent`, `complexity_score`, validated by a script checking ≥95% coverage and no missing labels. A separate N=50 hold-out set exists for rubric validation.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/data/ingest.py` with `load_dataset` (Hugging Face) to fetch raw A2UI-Bench data; **no training logic included**; outputs raw CSV
- [X] T012b [US1] Implement `code/data/annotate.py` to provide the **manual annotation interface** for researchers to label N=500 turns (FR-001); outputs labeled CSV
- [X] T013 [US1] Implement validation script `tests/unit/test_annotation_coverage.py` to verify N=500 and valid labels in the output of T012b
- [X] T014 [US1] Add error handling to `code/data/ingest.py` to ensure real data fetch fails loudly (no synthetic fallback) per Data Hygiene rules
- [X] T015 [US1] Implement `code/data/annotate_holdout.py` to create the **N=50 human-annotated hold-out set** for rubric validation (FR-008); **data creation only, no validation logic**

### Tests for User Story 1

- [X] T010 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schemas.py`
- [X] T011 [P] [US1] Unit test for annotation script logic in `tests/unit/test_data_ingest.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Hybrid Routing and Latency Simulation (Priority: P2)

**Goal**: Implement a routing pipeline (DistilBERT CPU classifier) and simulation engine with latency injection, user patience modeling, and fallback generation.

**Independent Test**: A simulation run processes a batch, logs routing decisions, generation time, injected latency, and abandonment events, producing a log where `total_time = gen_time + latency` (or `abandonment_time`).

### Implementation for User Story 2

- [ ] T019 [US2] Train the DistilBERT router on the labeled CSV from **T013**; save model to `code/models/router_model/`
- [X] T020 [US2] Implement `code/models/router.py` with DistilBERT (8-bit quantized) for intent classification (High-Confidence vs. Ambiguous)
- [X] T021 [US2] Implement `code/models/fallback.py` for the deterministic rule-based generator with ontology matching
- [X] T022 [US2] Implement `code/simulation/patience.py` with `sample_patience()` function modeling exponential decay (mean=2s) for user abandonment (FR-003)
- [X] T023 [US2] Implement `code/simulation/rubric.py` to derive and implement the "Human-Agent Alignment" scoring function: `score = 0.4 * intent_match + 0.3 * (1 - latency_penalty) + 0.3 * ui_completeness [UNRESOLVED-CLAIM: c_76d53354 — status=not_enough_info]` (FR-005, SC-002); **must include latency_penalty**
- [X] T024 [US2] Implement `code/simulation/runner.py` with latency injection (sleep/delay) and dependency on **T022** for patience modeling
- [X] T025 [US2] Implement logic in `code/simulation/runner.py` to iterate through **explicit density levels {1, 3, 5, 10}** for deterministic fallback (FR-004, Constitution Principle VII)
- [X] T026 [US2] Implement logic in `code/simulation/runner.py` to handle "Ambiguous" queries: invoke fallback, log "no-match" if no ontology entry, return minimal UI (element)
- [X] T027 [US2] Implement `code/simulation/metrics.py` to calculate alignment scores using the rubric from **T023**; output must include `ui_element_count`
- [ ] T028 [US2] Add validation to ensure `ui_element_count` is logged for every run (1, 3, 5, 10) in the metrics output

### Tests for User Story 2

- [X] T016 [P] [US2] Unit test for router confidence scoring in `tests/unit/test_router.py`
- [X] T017 [P] [US2] Unit test for patience model (exponential decay) in `tests/unit/test_patience_model.py`
- [X] T018 [P] [US2] Integration test for simulation runner in `tests/integration/test_simulation.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Alignment Scoring and Pareto Analysis (Priority: P3)

**Goal**: Calculate metrics, perform statistical tests (FDR/Bonferroni), and generate Pareto frontier plots to identify the latency threshold for fidelity degradation. The alignment score calculation includes `intent_match`, `latency_penalty`, and `ui_completeness`.

**Independent Test**: A report is generated with a Pareto plot and a table of alignment scores per density/latency, identifying the threshold via non-overlapping 95% CIs (p < 0.05).

### Implementation for User Story 3

- [X] T032 [US3] Implement `code/analysis/stats.py` for **Benjamini-Hochberg FDR** multiple-comparison correction on alignment scores (FR-006, SC-004)
- [X] T033 [US3] Implement sensitivity analysis in `code/analysis/sensitivity.py` to sweep router confidence cutoffs across a range of thresholds and report inconsistency rates. (FR-007, SC-005)
- [ ] T034 [US3] Implement `code/analysis/stats.py` to identify the latency threshold where generative baseline CI drops below hybrid model CI (p < 0.05)
- [ ] T035 [US3] Implement `code/analysis/viz.py` to generate the Pareto frontier plot (Alignment vs. Latency)
- [ ] T036 [US3] Implement `code/analysis/viz.py` to plot alignment scores across information density levels (low, medium, high)
- [ ] T037 [US3] Implement `code/analysis/rubric_validation.py` to validate the rubric correlation (r ≥ 0.7) against the N=50 hold-out set from **T015**; **consumes rubric logic from T023 and metrics from T028; explicitly calculate correlation between rubric scores and human scores**
- [ ] T038 [US3] Implement `code/main.py` entry point to orchestrate the full pipeline: Ingest -> Route -> Simulate -> Analyze -> Report
- [ ] T039 [US3] Generate final report containing Pareto plot, threshold table, and inconsistency rate analysis

### Tests for User Story 3

- [ ] T029 [P] [US3] Unit test for statistical correction (FDR/Bonferroni) in `tests/unit/test_stats.py`
- [ ] T030 [P] [US3] Unit test for Pareto frontier calculation in `tests/unit/test_metrics.py`
- [ ] T031 [P] [US3] Unit test for rubric validation against N=50 hold-out set in `tests/unit/test_rubric_validation.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `specs/001-llmxive-a2ui-latency-study/quickstart.md`
- [ ] T041 Code cleanup and refactoring in `code/`
- [ ] T042 Performance optimization: ensure CPU inference < 500ms per query [UNRESOLVED-CLAIM: c_2bcb3a6f — status=not_enough_info] (8-bit quantization check)
- [ ] T043 [P] Additional unit tests for edge cases (e.g., router confidence near boundary) in `tests/unit/`
- [ ] T044 Run `quickstart.md` validation to ensure full reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data (labeled CSV) for training the router
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 simulation logs for analysis

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/contract/test_data_schemas.py"
Task: "Unit test for annotation script logic in tests/unit/test_data_ingest.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/ingest.py with load_dataset and CLI --annotate flag"
Task: "Create annotation interface script code/data/annotate.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (ensure N=500 labeled data exists)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Simulate routing)
4. Add User Story 3 → Test independently → Deploy/Demo (Analyze results)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Routing & Simulation)
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
- **CRITICAL**: Do NOT use synthetic data fallbacks. If real data fetch fails, the task must fail loudly.
- **CRITICAL**: Ensure the router is CPU-optimized (quantized DistilBERT) and the generative model is quantized (quantized DistilGPT) to fit within GitHub Actions constraints.
- **CRITICAL**: Latency injection must be explicit and logged; user patience must be modeled as exponential decay.
- **CRITICAL**: Implement density iteration for {1, 3, 5, 10} to support the minimum viable density study.
- **CRITICAL**: Create N=50 human-annotated hold-out set for rubric validation.
- **CRITICAL**: Ensure sensitivity analysis is performed in the Analysis phase (Phase 5), not the Simulation phase.
- **CRITICAL**: Rubric validation (T037) must explicitly calculate the correlation coefficient (r) against the hold-out set.
- **CRITICAL**: Statistical correction (T032) must use FDR (Benjamini-Hochberg).
- **CRITICAL**: Alignment scoring (T023) must include `latency_penalty` component.
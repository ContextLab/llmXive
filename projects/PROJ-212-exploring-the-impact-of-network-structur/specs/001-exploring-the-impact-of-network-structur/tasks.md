# Tasks: Exploring the Impact of Network Structure on Synchronization in Complex Physical Systems

**Input**: Design documents from `/specs/001-network-synchronization-impact/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are MANDATORY to satisfy the "Independent Test" requirement in the spec.

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-212-exploring-the-impact-of-network-structur/code/`)
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (networkx, scipy, scikit-learn, pandas, matplotlib, datasets)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `config.yaml` for seeding (random seeds), thresholds (r > 0.8, t > 100), and paths
- [ ] T006 [P] Create `src/data_models.py` defining `NetworkGraph`, `SimulationResult`, and `RegressionModel` entities
- [ ] T005 [P] Implement `src/loader.py` with strict real-data fetching (SNAP/Network Repository). Logic: 1) Fetch real data. 2) If real N >= 30, proceed. 3) If 10 <= real N < 30, generate synthetic data to reach N=30 and save to `data/synthetic_fallback_N30.csv`. 4) If real N < 10, stop and output a warning that regression is skipped per FR-004; do NOT generate synthetic data in this case.
- [ ] T007 Setup `src/utils.py` for logging, error handling, and result checksumming
- [X] T008a [P] Setup `pytest` framework configuration in `tests/conftest.py`
- [X] T008b [P] Implement `tests/test_properties.py` with specific hypothesis properties (e.g., 'graph connectivity invariance', 'metric bounds')
- [ ] T009 Create `src/validators.py` for data integrity checks (e.g., disconnected graph detection)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Topological Feature Extraction & Synchronization Simulation (Priority: P1) 🎯 MVP

**Goal**: Compute topological metrics and run Kuramoto simulations to determine critical coupling strength.

**Independent Test**: Load a single known small network (e.g., Barabási-Albert), compute metrics, run simulation, verify output JSON contains valid threshold and metrics.

### Tests for User Story 1 (MANDATORY)

- [ ] T010 [P] [US1] Unit test for `src/topology.py` metrics calculation in `tests/test_topology.py` <!-- FAILED: unspecified -->
- [ ] T011 [P] [US1] Unit test for `src/simulation.py` RK45 integration and threshold detection in `tests/test_simulation.py` <!-- FAILED: unspecified -->
- [X] T012 [P] [US1] Contract test for disconnected graph handling (returns infinity/null) in `tests/test_simulation.py`

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `src/topology.py` to compute degree distribution, clustering coefficient, and average path length (handling disconnected graphs as infinity) using NetworkX
- [ ] T014 [US1] Implement `src/simulation.py` with Kuramoto model (N=200, RK45, K sweep [0, 5] step 0.1) and robustness threshold logic (r > 0.8 for t > 100)
- [ ] T015 [US1] Implement `src/simulation.py` early-exit logic for disconnected graphs (skip K-sweep, return infinity)
- [ ] T016 [US1] Create `main.py` orchestration script to load network, run topology, run simulation, and save `results/sim_results.json`
- [X] T017 [US1] Implement validation for analytical solution check (Ring Graph N=200, K=0.5) within `tests/test_simulation.py`
- [ ] T017b [US1] Implement logic to sort the SNAP dataset list alphabetically by filename, run simulations on the first 5 networks using `src/simulation.py`, and generate `results/verification_report.json` containing the sorted IDs and their threshold values to satisfy SC-003 <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation & Regression Analysis (Priority: P2)

**Goal**: Perform regression analysis to quantify the relationship between topology and synchronization threshold.

**Independent Test**: Feed synthetic CSV of a representative number of rows with pre-calculated features, run regression, verify R², p-values, and coefficients output.

### Tests for User Story 2 (MANDATORY)

- [ ] T018 [P] [US2] Unit test for `src/stats.py` VIF calculation and Ridge fallback logic
- [ ] T019 [P] [US2] Unit test for `src/stats.py` handling of small datasets (<10) with warning generation

### Implementation for User Story 2

- [ ] T020a [P] [US2] Implement `src/stats.py` linear and polynomial regression model fitting functions
- [ ] T020b [P] [US2] Implement `src/stats.py` statistical calculation functions (R², p-values, ANOVA)
- [ ] T020c [P] [US2] Implement `src/stats.py` output generation to produce `results/regression_summary.json` with defined JSON schema
- [ ] T021 [US2] Implement `src/stats.py` VIF check logic: if VIF > 5, flag predictor, remove it, or switch to Ridge Regression; **document the alpha parameter** in config (`alpha: 0.05`) and logs with format "[VIF_ALERT] Alpha={alpha} used for Ridge fallback" as required by FR-006
- [ ] T022 [US2] Implement `src/stats.py` dataset size checks: if N < 10, output descriptive stats + warning; if N >= 10, run full regression
- [ ] T023 [US2] Extend `main.py` logic to aggregate `results/sim_results.json` into `data/processed_metrics.csv` and trigger regression (depends on T016 completion)
- [ ] T024 [US2] Implement null hypothesis testing logic (p < 0.05 required for support) in `src/stats.py`
- [ ] T025 [US2] Ensure `results/regression_summary.json` is generated with model type, coefficients, R², and p-values
- [ ] T028 [P] [US2] Implement `src/stats.py` cross-validation logic: execute **5x5-Fold Cross-Validation** for all datasets (per Plan/Constitution) and report mean R² and std dev
- [ ] T029 [US2] Implement `src/stats.py` instability flagging if CV std dev > 0.1
- [ ] T033 [US2] Implement full pipeline timeout detection logic in `main.py` (after T023 aggregation): track total execution time for all networks; if total time > 6 hours, log 'TIMEOUT' to `results/pipeline_status.json` with JSON structure `{network_id: "aggregate", duration: <seconds>, status: "TIMEOUT"}` to satisfy SC-004

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cross-Validation & Visualization Generation (Priority: P3)

**Goal**: Validate regression model robustness and generate visualizations.

**Independent Test**: Run validation on small fixed dataset, verify plot file (PNG) and JSON report with mean CV R² and std dev.

### Tests for User Story 3 (MANDATORY)

- [ ] T026 [P] [US3] Unit test for `src/stats.py` CV logic (5x5-Fold for all N)
- [ ] T027 [P] [US3] Unit test for `src/viz.py` heatmap generation and file saving

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement `src/viz.py` to generate heatmaps (X: metric A, Y: metric B, Color: Threshold) saved to `results/`
- [ ] T031 [US3] Create `main.py` logic to trigger CV and viz generation after regression completion
- [ ] T032 [US3] Generate `results/cv_report.json` with mean R², std dev, and stability flag

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `docs/` including `quickstart.md` and `data-model.md`
- [ ] T040 Code cleanup and refactoring (remove unused imports, ensure type hinting)
- [ ] T041 Performance optimization for large network loading (streaming if necessary)
- [ ] T042 [P] Additional unit tests for edge cases (e.g., N=2 graphs, self-loops) in `tests/unit/`
- [ ] T043 Run `quickstart.md` validation to ensure end-to-end pipeline works

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Consumes US1 output (T016/T017b)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Consumes US2 output

### Within Each User Story

- Tests (mandatory) MUST be written and FAIL before implementation
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
# Launch all tests for User Story 1 together:
Task: "Unit test for src/topology.py metrics calculation in tests/test_topology.py"
Task: "Unit test for src/simulation.py RK45 integration and threshold detection in tests/test_simulation.py"
Task: "Contract test for disconnected graph handling in tests/test_simulation.py"

# Launch all models for User Story 1 together:
Task: "Implement src/topology.py to compute degree distribution..."
Task: "Implement src/simulation.py with Kuramoto model..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (including mandatory tests)
4. **STOP and VALIDATE**: Test User Story 1 independently (Ring Graph check, verification report)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (incorporating 5x5-CV and VIF checks)
4. Add User Story 3 → Test independently → Deploy/Demo (comparative plots)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Simulation Core + Tests)
 - Developer B: User Story 2 (Regression Core + 5x5-CV)
 - Developer C: User Story 3 (CV & Viz)
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
- **Data Integrity**: All data loaders MUST attempt real fetch first; synthetic generation is only a fallback for sample size augmentation (N>=30) if real data is insufficient (T005), and only if real N >= 10.
- **Timeout Handling**: SC-004 compliance is ensured by T033 (aggregate pipeline monitoring) in Phase 4.
- **Statistical Rigor**: FR-006 compliance ensured by T021 (documenting alpha parameter) and T028 (5x5-Fold CV).
- **Validation**: SC-003 compliance ensured by T017b (SNAP list sorting and verification report generation).
- **Constitution Alignment**: All tasks align with Plan.md and Constitution Principle VII (5x5-Fold CV).
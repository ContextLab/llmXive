# Tasks: Exploring the Role of Network Topology on Synchronization in Coupled Oscillators

**Input**: Design documents from `/specs/001-explore-network-topology-synchronization/`
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

- [ ] T001 Create project structure by executing: `mkdir -p code/utils data/processed tests` in `projects/PROJ-096-exploring-the-role-of-network-topology-o/`
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (networkx, scipy, numpy, pandas, pyyaml)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/utils/graph_utils.py` for connectivity checks and metric calculations
- [ ] T005 [P] Implement `code/utils/stats_utils.py` for correlation, p-value, and multiple-comparison correction
- [ ] T006 Setup data directory structure (`data/processed/`, `data/checksums.txt`) and metadata schema
- [ ] T007 Configure deterministic random seeds and `t_eval` settings for `scipy.integrate.odeint`
- [ ] T008 Implement base logging infrastructure to capture simulation parameters and warnings
- [ ] T009 [P] Implement feasibility study script in `code/feasibility_study.py` to resolve [deferred] time steps by testing runtime vs. accuracy trade-offs, write the resolved value to `data/processed/config.json`, and log the chosen value.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Rewired Network Instances (Priority: P1) 🎯 MVP

**Goal**: Generate 50 network instances with varying small-world rewiring probabilities starting from a synthetic regular ring lattice (N=500).

**Independent Test**: The system can be tested by generating 50 network instances with rewiring probabilities ranging from 0.0 to 1.0 and verifying that each graph is connected, has the correct number of nodes (N=500), and preserves the average degree of the reconstructed lattice.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for graph generation in `tests/test_topology.py` (verify N=500, connected, degree preservation)
- [ ] T011 [P] [US1] Integration test for metadata logging in `tests/test_topology.py` (verify seed and p saved to `graph_metadata.json`)

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement synthetic ring lattice generator in `code/generate_topology.py` (N=500, k=2)
- [ ] T013 [P] [US1] Implement Watts-Strogatz rewiring function with seed logging in `code/generate_topology.py`
- [ ] T014 [US1] Implement connectivity validation logic in `code/generate_topology.py` to skip disconnected graphs and log warnings (FR-002 compliance)
- [ ] T015 [US1] Implement batch generation loop (p=0.0 to 1.0, 50 instances) in `code/generate_topology.py`
- [ ] T016 [US1] Save generated graphs as `.gpickle` and metadata as `.json` in `data/processed/`
- [ ] T017 [US1] Add checksum generation for all artifacts in `data/checksums.txt`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Simulate Kuramoto Dynamics and Detect Synchronization (Priority: P2)

**Goal**: Simulate Kuramoto oscillator dynamics on each generated network and determine the critical coupling strength ($K_c$), including verification of rotational invariance (FR-009) and stability (SC-001).

**Independent Test**: 
1. The system can be tested by running the simulation on a known topology (e.g., fully connected) with high coupling and verifying $R \to 1$.
2. The system can be tested by running the binary search on a synthetic dataset with known $K_c$ and verifying detection within tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for order parameter calculation in `tests/test_simulation.py`
- [ ] T019 [P] [US2] Integration test for binary search convergence in `tests/test_simulation.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement Kuramoto ODE derivative function in `code/simulate_kuramoto.py`
- [ ] T021 [US2] Implement order parameter $R$ calculation and time-series aggregation in `code/simulate_kuramoto.py`
- [ ] T022 [US2] Implement binary search algorithm for $K_c$ (threshold defined qualitatively, max 100 iters, tol 0.01) in `code/simulate_kuramoto.py`
- [ ] T023 [US2] Implement fallback linear sweep if binary search fails in `code/simulate_kuramoto.py`
- [ ] T024 [US2] Run simulation batch for all valid topologies from US1 using time steps resolved by T009 (read from `data/processed/config.json`), save results to `data/processed/results.csv` (schema: rewiring_prob, Kc, seed, time_steps), and verify file exists with a sufficient number of rows to support the analysis.
- [ ] T025 [US2] Implement phase reference frame transformation (single oscillator vs. center-of-mass) in `code/simulate_kuramoto.py`
- [ ] T026 [US2] Implement dual-frame simulation runner in `code/analyze_results.py` to re-execute the full binary search for both reference frames on a subset of topologies and verify $|K_{c,frame1} - K_{c,frame2}| < 1e-6$ by adding an assertion in `code/analyze_results.py`
- [ ] T027 [US2] Run stability check script in `code/simulate_kuramoto.py` to simulate Kuramoto dynamics repeatedly on a subset of topologies, calculate sample variance of R, and verify it is < 0.01 (SC-001)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently, with verified Kc values

---

## Phase 5: User Story 3 - Quantify Topological Influence via Statistical Correlation (Priority: P3)

**Goal**: Analyze the relationship between rewiring probability and critical coupling strength using Spearman correlation and sensitivity analysis.

**Independent Test**: The system can be tested by generating synthetic data with a known non-linear relationship and verifying the Spearman coefficient matches the expected value.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for Spearman correlation calculation in `tests/test_analysis.py`
- [ ] T029 [P] [US3] Integration test for sensitivity analysis sweep in `tests/test_analysis.py`

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement Spearman correlation and p-value calculation in `code/analyze_results.py`
- [ ] T031 [US3] Implement Bonferroni/Benjamini-Hochberg correction logic (if multiple tests) in `code/analyze_results.py`
- [ ] T032 [US3] Implement sensitivity analysis sweep over thresholds in `code/analyze_results.py`
- [ ] T033 [US3] Calculate the variation metric of the headline correlation rate across the sensitivity sweep and verify it is ≤ 5% (SC-004)
- [ ] T034 [US3] Generate summary plot (Critical Coupling vs. Rewiring Probability) with trend line in `code/analyze_results.py` saving to `data/processed/plot_kc_vs_p.png` and verify file exists and is non-empty
- [ ] T035 [US3] Write final report summary to `data/processed/analysis_report.md` containing Spearman correlation value, p-value, and a dedicated section explicitly defining and justifying the statistical model (single regression vs. multiple tests), then verify file exists and is non-empty with required content.
- [ ] T036 [US3] Implement runtime instrumentation in `code/analyze_results.py` to measure total execution time and verify it is ≤ 6 hours (SC-003)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` (including methodology for synthetic lattice vs. ca-AstroPh correction)
- [ ] T038 Code cleanup and refactoring
- [ ] T039 Performance optimization (vectorization of ODE steps if needed)
- [ ] T040 [P] Additional unit tests for edge cases (zero variance, numerical instability) in `tests/`
- [ ] T041 [P] Run `quickstart.md` validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Verification (Phase 4)**: Integrated into Phase 4 (US2) to ensure data flow
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 data generation (including verification)
- **Verification**: Integrated into Phase 4 to ensure Kc values are verified before Phase 5 analysis

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utils before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, and US3 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for graph generation in tests/test_topology.py"
Task: "Integration test for metadata logging in tests/test_topology.py"

# Launch all models for User Story 1 together:
Task: "Implement synthetic ring lattice generator in code/generate_topology.py"
Task: "Implement Watts-Strogatz rewiring function in code/generate_topology.py"
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
   - Developer A: User Story 1 (Topology)
   - Developer B: User Story 2 (Simulation + Verification)
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
- **Critical Correction**: The base graph is a synthetic regular ring lattice (N=500), NOT the ca-AstroPh dataset, to ensure theoretical validity of the Watts-Strogatz parameter.
- **Time Steps**: T009 resolves the [deferred] time steps; T024 uses the resolved value from `data/processed/config.json`.
- **Verification**: FR-009 verification is integrated into Phase 4 (US2) as T026 to ensure correct data flow.
- **Stability**: SC-001 stability check is integrated into Phase 4 (US2) as T027.
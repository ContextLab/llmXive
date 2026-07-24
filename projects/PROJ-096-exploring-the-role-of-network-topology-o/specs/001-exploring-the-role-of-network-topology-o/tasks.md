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

- [ ] T001a [P] Create source directories: `mkdir -p code/utils code/data` in `projects/PROJ-096-exploring-the-role-of-network-topology-o/`
- [ ] T001b [P] Create data directories: `mkdir -p data/processed data/checksums data/raw` in `projects/PROJ-096-exploring-the-role-of-network-topology-o/` and verify with `test -d data/processed && echo 'OK' || exit 1`.
- [ ] T001c [P] Create test directories: `mkdir -p tests state/projects` in `projects/PROJ-096-exploring-the-role-of-network-topology-o/`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` containing pinned versions: `networkx>=3.2.0`, `scipy>=1.12.0`, `numpy>=1.26.0`, `pandas>=2.2.0`, `pyyaml>=6.0.0`.
- [X] T003a [P] Create `.flake8` config with `max-line-length=88`, `ignore=E203,W503` and `pyproject.toml` for black with `line-length=88`.
- [ ] T003b [P] Verify linting configuration by running `black --check. && flake8.` and ensuring no errors. (This is the single source of truth for lint verification).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. This phase determines the feasible scope of the experiment.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T009 [P] [US2] **Feasibility Study**: Determine the maximum time steps and number of topologies feasible within 6 hours on a 2-core CPU runner.
 **Objective**: Binary search for `time_steps` in range [, 20000] and calculate `n_topologies` such that total runtime <= 6 hours.
 **Logic**:
 1. Run a single simulation with `time_steps` = 1000 to measure `runtime_per_1k_steps`.
 2. Calculate max `time_steps` = floor(6h / (runtime_per_1k_steps * 50)) * 1000.
 3. If max `time_steps` < 1000, calculate `n_topologies` = floor(6h / (runtime_per_1k_steps * 1000/1000)).
 4. If `n_topologies` < 10, log "CRITICAL WARNING: Insufficient compute for minimum scientific validity" and halt.
 **Input**: Requires T004, T005 (utils) to be implemented.
 **Output**: Write `data/processed/config.json` with keys: `time_steps` (int), `runtime_estimate` (float), `n_topologies` (int).
 **Verification**: Run `python -c "import json; d=json.load(open('data/processed/config.json')); assert d['time_steps'] >= 1000; assert d['n_topologies'] >= 10"`.
 **Constraint**: If `time_steps` < 1000, the task MUST NOT proceed to US1 generation until `n_topologies` is adjusted to fit the budget.

- [X] T004 [P] Implement `code/utils/graph_utils.py` for connectivity checks and metric calculations
- [X] T005 [P] Implement `code/utils/stats_utils.py` for correlation, p-value, and multiple-comparison correction
- [ ] T008 [P] [US3] **Analysis Configuration**: Create `data/processed/analysis_config.yaml` defining the statistical model.
 **Schema**: Must contain keys: `model_type` (string: 'single_regression'), `correction_method` (string: 'bonferroni' or 'none'), `thresholds` (list: [0.4, 0.5, 0.6]).
 **Purpose**: Breaks circular dependency by defining the statistical model before analysis implementation.
 **Verification**: `test -f data/processed/analysis_config.yaml && echo 'OK' || exit 1`.
- [X] T006 Setup data directory structure (`data/processed/`, `data/raw/`, `data/checksums.txt`) and metadata schema.
 **Schema**: `graph_metadata.json` must contain keys: `node_count` (int), `avg_degree` (float), `p` (float), `seed` (int), `checksum` (string).
 **Checksum Format**: `data/checksums.txt` must contain SHA256 hashes of ALL data artifacts (raw downloads and generated `.gpickle` files), formatted as `hash filename`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Rewired Network Instances (Priority: P1) 🎯 MVP

**Goal**: Generate N topologies (where N is determined by T009) with varying small-world rewiring probabilities starting from a synthetic regular ring lattice (N=500).

**⚠️ Methodological Correction & Constitution Compliance**:
1. **Constitution Requirement**: The Constitution mandates downloading 'ca-AstroPh' from SNAP on every run.
2. **Plan Correction**: The plan identifies that reconstructing an irregular citation network into a regular ring lattice is methodologically incoherent.
3. **Resolution**: This implementation **generates a synthetic regular ring lattice** (T012) as the base for Watts-Strogatz. The download of 'ca-AstroPh' is **removed** as it is not used for structure. This deviation from FR-001 is formally documented here, pending a formal spec amendment.

**Independent Test**: The system can be tested by generating N network instances with rewiring probabilities ranging from 0.0 to 1.0 and verifying that each graph is connected, has the correct number of nodes (N=500), and preserves the average degree of the reconstructed lattice.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for graph generation in `tests/test_topology.py` (verify N=500, connected, degree preservation)
- [X] T011 [P] [US1] Integration test for metadata logging in `tests/test_topology.py` (verify seed and p saved to `graph_metadata.json`)

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement synthetic ring lattice generator in `code/generate_topology.py` (N=500, k=2). **Note**: This task explicitly generates a synthetic regular ring lattice. This deviates from spec FR-001 (ca-AstroPh) based on the Plan Summary's methodological correction. The code must include a comment stating: "Base graph is synthetic; FR-001 requirement to use ca-AstroPh is formally deviated from per Plan Summary, pending spec amendment."
- [X] T014 [P] [US1] Implement Watts-Strogatz rewiring function with seed logging in `code/generate_topology.py`
- [X] T015 [US1] Implement connectivity validation logic in `code/generate_topology.py` to skip disconnected graphs and log warnings (FR-002 compliance)
- [ ] T016 [US1] Implement batch generation loop (p=0.0 to 1.0, N instances as defined in `data/processed/config.json`) in `code/generate_topology.py`
- [ ] T017 [US1] Save generated graphs as `.gpickle` and metadata as `.json` in `data/processed/`
- [X] T018 [US1] Add checksum generation for all artifacts in `data/checksums.txt`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Simulate Kuramoto Dynamics and Detect Synchronization (Priority: P2)

**Goal**: Simulate Kuramoto oscillator dynamics on each generated network and determine the critical coupling strength ($K_c$), including verification of rotational invariance (FR-009) and stability (SC-001) across ALL topologies.

**Independent Test**:
1. The system can be tested by running the simulation on a known topology (e.g., fully connected) with high coupling and verifying $R \to 1$.
2. The system can be tested by running the binary search on a synthetic dataset with known $K_c$ and verifying detection within tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Contract test for order parameter calculation in `tests/test_simulation.py`
- [ ] T020 [P] [US2] Integration test for binary search convergence in `tests/test_simulation.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement Kuramoto ODE derivative function in `code/simulate_kuramoto.py`. **Dependency**: Depends on T009 (reads `data/processed/config.json` for `time_steps`).
- [ ] T022 [US2] Implement order parameter $R$ calculation and time-series aggregation in `code/simulate_kuramoto.py`. **Dependency**: Depends on T021 (ODE function).
- [ ] T023 [US2] Implement binary search algorithm for $K_c$ (threshold defined qualitatively, max iterations, tol specified) in `code/simulate_kuramoto.py`. **Dependency**: Depends on T021 and T022.
- [ ] T024 [US2] Implement fallback linear sweep if binary search fails in `code/simulate_kuramoto.py`. **Dependency**: Depends on T023.
- [ ] T025 [US2] Run simulation batch for all valid topologies from US1 using time steps resolved by T009 (read from `data/processed/config.json`). (Wikidata Q47604, https://www.wikidata.org/wiki/Q47604) **Runtime Check**: Measure total runtime. If > 6 hours, implement fallback: reduce `time_steps` by `max(1000, floor(current_steps / 1000) * 1000)`. If the reduced value is < 1000, log "FAILURE" and halt. This task satisfies SC-003 compliance.
- [ ] T026 [US2] [FR-009] Implement rotational invariance verification on **the full set of topologies**. Re-run the full binary search for $K_c$ on each using two reference frames: "single oscillator" and "center-of-mass". If any assertion fails, log a "FAILURE" and halt. Save results to `data/processed/invariance_verification.json`. **Justification**: FR-009 requires system-wide verification; a subset is insufficient.
- [ ] T027 [US2] Run stability check script in `code/simulate_kuramoto.py` to simulate Kuramoto dynamics multiple times per topology for **ALL 50 topologies** (indices 0-49). Calculate sample variance of R and verify it is < 0.01 (SC-001). **Fallback Logic**: If variance > 0.01 for ANY topology, log "CRITICAL WARNING: Statistical instability detected in topology X" and HALT. DO NOT reduce time-steps as a fallback, as this increases numerical noise and violates the stability requirement. The task must fail loudly to preserve scientific integrity.

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
- [ ] T031 [US3] Implement multiple-comparison correction logic in `code/analyze_results.py`. **Logic**: Read the pre-defined statistical model from `data/processed/analysis_config.yaml` (defined in T008). If the model specifies multiple tests, apply Bonferroni/Benjamini-Hochberg. If single regression, skip. Explicitly log the statistical model choice and whether correction was applied in the final report (FR-006, FR-008).
- [ ] T032 [US3] Implement sensitivity analysis sweep over thresholds in `code/analyze_results.py`. **Scope**: Sweep over a range of values as defined in Assumptions. **Note**: This range is explicitly justified in the spec's "Assumption about Threshold Justification" as a representative range for community standards.
- [ ] T033 [US3] Calculate the variation metric of the headline correlation rate across the sensitivity sweep. **Definition**: Calculate the Spearman correlation coefficient for each threshold in a set of representative values.. Compute the relative variation: (max(coef) - min(coef)) / mean(coef). Verify this value is ≤ 0.05 (SC-004).
- [ ] T034 [US3] Generate summary plot (Critical Coupling vs. Rewiring Probability) with trend line in `code/analyze_results.py` saving to `data/processed/plot_kc_vs_p.png` and verify file exists and is non-empty
- [ ] T035 [US3] Write final report summary to `data/processed/analysis_report.md` containing:
 1. Spearman correlation value and p-value.
 2. A dedicated section "Physical Invariance" citing the results from T026 (invariance_verification.json) and explicitly stating that the critical coupling is an observer-invariant property.
 3. Explicit definition and justification of the statistical model used (single regression vs. multiple tests) as defined in `data/processed/analysis_config.yaml`.
 Verify file exists and is non-empty with required content.
- [ ] T036 [US3] (Removed: Runtime check moved to T025)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037a [P] Create `docs/methodology.md` with a section on the invariance check (T026), explaining the theoretical basis (rotational invariance of the order parameter $R$).
- [ ] T037b [P] Update `docs/quickstart.md` to include the invariance step as a mandatory part of the research pipeline.
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
- **Critical Correction**: The base graph is a synthetic regular ring lattice (N=500), NOT the ca-AstroPh dataset, to ensure theoretical validity of the Watts-Strogatz parameter. This is documented in T012. The spec's FR-001 requirement to use ca-AstroPh is a known contradiction pending a spec kickback.
- **Time Steps**: T009 resolves the [deferred] time steps; T025 uses the resolved value from `data/processed/config.json`. **Warning**: T009 must not silently reduce steps below [deferred] without logging a contingency, but MUST find the max feasible steps if [deferred] is too slow.
- **Verification**: FR-009 verification is integrated into Phase 4 as T026 (ALL 50 topologies).
- **Stability**: SC-001 stability check is integrated into Phase 4 as T027 (ALL 50 topologies).
- **Runtime**: SC-003 runtime check is integrated into Phase 4 as T025 with fallback logic (max(1000,...)).
- **Removed**: Phase 6 (Reviewer Revision) and T009c (Spec Amendment) have been removed to eliminate duplication and ensure a single source of truth for FR-009. Spec modifications are handled via contingency logging, not direct spec editing.
- **Reviewer Response (albert-einstein-simulated)**: Task T026 explicitly addresses the concern regarding physical invariance by verifying that the critical coupling strength $K_c$ is identical regardless of whether the phase reference is a single oscillator or the center-of-mass. This ensures the symbol $K_c$ corresponds to an element of physical reality independent of the observer's coordinate frame.
- **Statistical Model**: T031 reads the pre-defined statistical model from `analysis_config.yaml` (created in T008) to determine correction logic, ensuring the model is defined before analysis as per FR-008.
- **Stability Fallback Correction**: Task T027 has been updated to HALT on variance > 0.01. Reducing time-steps is scientifically invalid for improving stability in chaotic systems and has been removed as a fallback.
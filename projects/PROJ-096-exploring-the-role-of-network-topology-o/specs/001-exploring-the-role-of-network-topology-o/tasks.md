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

**Purpose**: Project initialization, spec alignment, and constitution amendment.

**⚠️ CRITICAL**: T000 and T000a MUST complete before any other tasks. They resolve the contradiction between the spec/plan and the constitution.

- [ ] T000 [P] **Update Spec for Synthetic Base**: Update `specs/001-exploring-the-role-of-network-topology-synchronization/spec.md` to explicitly replace the 'ca-AstroPh' requirement in FR-001 with a synthetic regular ring lattice.
 **Exact Replacement**: In FR-001, replace "reconstructed as a regular ring lattice of the ca-AstroPh dataset" with "reconstructed as a synthetic regular ring lattice of N=500 nodes".
 **Rationale**: The Plan Summary identifies the original spec requirement as methodologically incoherent. To satisfy the Constitution's "Single Source of Truth" principle, the Spec must be amended to reflect the implemented approach.
 **Verification**: `grep -q "synthetic regular ring lattice of N=500 nodes" specs/001-exploring-the-role-of-network-topology-synchronization/spec.md && echo 'OK' || exit 1`.

- [ ] T000a [P] **Amend Constitution for Synthetic Base**: Update `projects/PROJ-096-exploring-the-role-of-network-topology-o/specs/001-exploring-the-role-of-network-topology-o/constitution.md` to remove the 'ca-AstroPh' download requirement from the 'Reproducibility Requirements' section and replace it with a requirement to generate a synthetic regular ring lattice.
 **Exact Replacement**: In 'Reproducibility Requirements', replace "The external base graph (the Stanford Network Analysis Project 'ca-AstroPh' citation network) MUST be downloaded..." with "The base graph MUST be generated as a synthetic regular ring lattice of N=500 nodes using the Watts-Strogatz algorithm with p=0.0 and a documented random seed."
 **Rationale**: The Constitution currently mandates a dataset that is methodologically invalid for this study. This amendment aligns the Constitution with the Plan and Tasks.
 **Verification**: `grep -q "synthetic regular ring lattice of N=500 nodes" specs/001-exploring-the-role-of-network-topology-o/constitution.md && echo 'OK' || exit 1`.

- [X] T001 [P] **Initialize Project Directories**: Create `code/`, `code/utils/`, `data/`, `data/processed/`, `data/raw/`, `tests/`, `state/`, `state/projects/`. Verify creation by running `ls -R data/ code/ tests/ state/` and capturing the output to `data/checksums.txt` (as a log of directory structure).
 **Verification**: `test -f data/checksums.txt && echo 'OK' || exit 1`.

- [X] T002a [P] **Create Requirements File**: Create `code/requirements.txt` containing pinned versions: `networkx>=3.2.0`, `scipy>=1.12.0`, `numpy>=1.26.0`, `pandas>=2.2.0`, `pyyaml>=6.0.0`.
 **Verification**: `test -f code/requirements.txt && grep -q "networkx" code/requirements.txt && echo 'OK' || exit 1`.

- [X] T002b [P] **Initialize Virtual Environment**: Create a virtual environment in `code/.venv` and install dependencies from `requirements.txt`.
 **Verification**: `test -d code/.venv && code/.venv/bin/pip list | grep networkx && echo 'OK' || exit 1`.

- [X] T003a [P] Create `.flake8` config with `max-line-length=88`, `ignore=E203,W503` and `pyproject.toml` for black with `line-length=88`.

- [X] T003b [P] **Verify Linting Configuration**: Create `code/__init__.py` if it does not exist. Run `black --check code/` and `flake8 code/` on the `code/` directory. Redirect output to `data/checksums.txt` (append).
 **Verification**: `test -f code/__init__.py && black --check code/ && flake8 code/ && echo 'OK' || exit 1`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. This phase determines the feasible scope of the experiment.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T006 [P] **Setup Data Directory Structure and Metadata Schema**: Create `data/processed/`, `data/raw/`, and initialize `data/checksums.txt`. Define the `graph_metadata.json` schema in `docs/data_model.md` (or inline comment) containing keys: `node_count` (int), `avg_degree` (float), `p` (float), `seed` (int), `checksum` (string).
 **Checksum Format**: `data/checksums.txt` must contain SHA256 hashes of ALL data artifacts (raw downloads and generated `.gpickle` files), formatted as `hash filename`.
 **Verification**: `test -d data/processed && test -f data/checksums.txt && echo 'OK' || exit 1`.

- [ ] T009 [US2] **Feasibility Study**: Determine the maximum time steps, number of topologies, and run count feasible within 6 hours on a 2-core CPU runner.
 **Script**: `code/feasibility_study.py`.
 **Output**: Write `data/processed/config.json` with keys: `time_steps` (int), `n_topologies` (int), `run_count` (int), `runtime_estimate` (float), `contingency_flag` (bool, default false), `SC_003_VIOLATION` (bool), `scope_reduction_factor` (float), `error` (string, optional).
 **Objective**: Binary search for `time_steps` in range [1000, 20000] for a fixed N=50 topologies. If max `time_steps` < 1000, calculate max `n_topologies` for fixed 1000 steps.
 **Logic**:
 1. Run a single simulation with `time_steps` = 1000 to measure `runtime_per_1k_steps`.
 2. Binary search for max `time_steps` such that `50 * (time_steps/1000) * runtime_per_1k_steps <= 6 hours`.
 3. If max `time_steps` < 1000, calculate `n_topologies` = floor(6h / (runtime_per_1k_steps * 1)).
 4. **HALT CONDITION**: If the calculated feasible `n_topologies` < 10, log "CRITICAL WARNING: Insufficient compute for minimum scientific validity", set `n_topologies = 0`, set `error = 'INSUFFICIENT_SCOPE'`, and write `data/processed/config.json`. Downstream tasks MUST fail fast if `n_topologies == 0`.
 5. If feasible scope is sufficient, set `n_topologies` to the calculated max (capped at a predetermined limit), `time_steps` to the calculated max, and `run_count` to a representative default value.
 6. Calculate `scope_reduction_factor` = (actual feasible) / (target scope).

The research question remains: What is the impact of scope reduction on model efficiency?
The method remains: Comparative analysis of feasible versus target scope configurations.
References: [DOI/arXiv/author-year]
 **Error Handling**: If binary search fails to converge or yields invalid values, write `data/processed/config.json` with `time_steps=0`, `n_topologies=0`, `error='CONVERGENCE_FAILURE'`.
 **Note**: Once `config.json` is written, these parameters are FIXED for the entire experiment to ensure reproducibility (Constitution Principle VI).
 **Verification**: Run `python -c "import json; d=json.load(open('data/processed/config.json')); assert (d['n_topologies'] >= 10 or d['error'] in ['CONVERGENCE_FAILURE', 'INSUFFICIENT_SCOPE']); assert (d['time_steps'] >= 1000 or d['error'] in ['CONVERGENCE_FAILURE', 'INSUFFICIENT_SCOPE'])"`.
 **Constraint**: If `n_topologies` < 10, the task MUST log a contingency and set the error flag; it does NOT proceed to US1 generation until `n_topologies` is adjusted (which is not allowed; it halts).
 **Note**: This task determines the *fixed* parameters for all subsequent runs. Once `config.json` is written, the integration settings are fixed and reproducible.

- [X] T009b [P] **Log Compute Contingency**: If `data/processed/config.json` contains `SC_003_VIOLATION=true` or `error` is present, generate `data/processed/compute_contingency.md`.
 **Content**: Explicitly state the reduced scope (time steps, number of topologies) and justify it as a necessary contingency due to compute constraints, referencing the 'Assumption about Compute Feasibility'.
 **Verification**: `test -f data/processed/compute_contingency.md && echo 'OK' || exit 1`.

- [X] T008 [US3] **Analysis Configuration**: Create `data/processed/analysis_config.yaml` defining the statistical model.
 **Dependency**: Runs AFTER T009 (strictly, not parallel). Reads `data/processed/config.json` to determine the number of tests.
 **Schema**: Must contain keys: `model_type` (string: 'single_regression'), `correction_method` (string: 'bonferroni' or 'none'), `thresholds` (list: [0.4, 0.5, 0.6]).
 **Purpose**: Breaks circular dependency by defining the statistical model before analysis implementation.
 **Verification**: `test -f data/processed/analysis_config.yaml && echo 'OK' || exit 1`.

- [X] T004 [P] Implement `code/utils/graph_utils.py` for connectivity checks and metric calculations.
- [X] T005 [P] Implement `code/utils/stats_utils.py` for correlation, p-value, and multiple-comparison correction.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Rewired Network Instances (Priority: P1) 🎯 MVP

**Goal**: Generate N topologies (where N is determined by T009) with varying small-world rewiring probabilities starting from a synthetic regular ring lattice (N=500).

**⚠️ Methodological Correction & Constitution Compliance**:
1. **Constitution Requirement**: The Constitution (after T000a amendment) mandates generating a synthetic regular ring lattice.
2. **Plan Correction**: The plan identifies that reconstructing an irregular citation network into a regular ring lattice is methodologically incoherent.
3. **Resolution**: This implementation **generates a synthetic regular ring lattice** (T012) as the base for Watts-Strogatz. The download of 'ca-AstroPh' is **removed** as it is not used for structure. This deviation from the original FR-001 is formally documented in `docs/constitutional_amendment.md` (T012b) and **updated in spec.md** (T000) to resolve the conflict.

**Independent Test**: The system can be tested by generating N network instances with rewiring probabilities ranging from 0.0 to 1.0 and verifying that each graph is connected, has the correct number of nodes (N=500), and preserves the average degree of the reconstructed lattice.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for graph generation in `tests/test_topology.py` (verify N=500, connected, degree preservation)
- [X] T011 [P] [US1] Integration test for metadata logging in `tests/test_topology.py` (verify seed and p saved to `graph_metadata.json`)

### Implementation for User Story 1

- [X] T012b [US1] **Generate Constitutional Amendment Log**: Create `docs/constitutional_amendment.md` formally documenting the change from 'ca-AstroPh' to a synthetic ring lattice as the base graph. This document serves as the updated 'single source of truth' for the data source, resolving the conflict with Constitution Principle I.
 **Required Schema**:
 1. **Original Spec ID**: FR-001
 2. **Methodological Flaw**: Explanation of why ca-AstroPh cannot be reconstructed into a regular lattice.
 3. **New Approach**: Use of synthetic regular ring lattice (N=500).
 4. **Rationale**: Theoretical validity of Watts-Strogatz parameter.
 5. **Constitution Impact**: Reference to T000a amendment.
 **Verification**: `test -f docs/constitutional_amendment.md && grep -q "Original Spec ID: FR-001" docs/constitutional_amendment.md && echo 'OK' || exit 1`.

- [X] T012 [US1] **Implement Synthetic Ring Lattice Generator**: Implement synthetic ring lattice generator in `code/generate_topology.py` (N=500, k=2). **Dependency**: T000 (Spec Update) AND T012b (Amendment Log). **Note**: This task explicitly generates a synthetic regular ring lattice. This deviates from spec FR-001 (ca-AstroPh) based on the Plan Summary's methodological correction, which has been formally updated in spec.md via T000 and documented in T012b. The code must include a comment stating: "Base graph is synthetic; FR-001 requirement to use ca-AstroPh has been formally amended in spec.md per T000 and documented in T012b."
 **Additional Step**: Generate `data/processed/scope_limitation.log` documenting this deviation.
 **Verification**: `python -c "import networkx as nx; G=nx.watts_strogatz_graph(500, 2, 0); assert G.number_of_nodes() == 500 and nx.is_connected(G)"`.

- [X] T014 [P] [US1] Implement Watts-Strogatz rewiring function with seed logging in `code/generate_topology.py`.

- [X] T015 [US1] Implement connectivity validation logic in `code/generate_topology.py` to skip disconnected graphs and log warnings (FR-002 compliance).

- [X] T016 [US1] Implement batch generation loop (p=0.0 to 1.0, 50 steps, N instances as defined in `data/processed/config.json`) in `code/generate_topology.py`. <!-- FAILED: unspecified -->
 **Output**: Save graphs as `data/processed/graph_p{p:.2f}_seed_{seed}.gpickle` and metadata as `data/processed/graph_metadata.json`.
 **Dependency**: Requires `data/processed/config.json` from T009.
 **Logic**: For each p, generate a graph. If disconnected, log warning to `disconnected_log.json` and skip.
 **Verification**: Run `python -c "import json, glob; d=json.load(open('data/processed/config.json')); files = glob.glob('data/processed/graph_p*.gpickle'); skipped = json.load(open('data/processed/disconnected_log.json'))['count']; assert len(files) + skipped == d['n_topologies'], f'Expected {d[\"n_topologies\"]} total, got {len(files)} files and {skipped} skipped'"`.
 **Constraint**: File naming MUST follow `graph_p{p:.2f}_seed_{seed}.gpickle` to ensure uniqueness. Disconnected graphs MUST be skipped and logged.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Simulate Kuramoto Dynamics and Detect Synchronization (Priority: P2)

**Goal**: Simulate Kuramoto oscillator dynamics on each generated network and determine the critical coupling strength ($K_c$), including verification of rotational invariance (FR-009) and stability (SC-001) across ALL topologies.

**Independent Test**:
1. The system can be tested by running the simulation on a known topology (e.g., fully connected) with high coupling and verifying $R \to 1$.
2. The system can be tested by running the binary search on a synthetic dataset with known $K_c$ and verifying detection within tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for order parameter calculation in `tests/test_simulation.py`
- [X] T020 [P] [US2] Integration test for binary search convergence in `tests/test_simulation.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement Kuramoto ODE derivative function in `code/simulate_kuramoto.py`. **Dependency**: Depends on T009 (reads `data/processed/config.json` for `time_steps`). **Error Handling**: If `config.json` has `time_steps=0` OR `error` key is present, raise `RuntimeError('CONVERGENCE_FAILURE')`. If `SC_003_VIOLATION` is true, proceed with reduced scope (do NOT raise error).
- [X] T022 [US2] Implement order parameter $R$ calculation and time-series aggregation in `code/simulate_kuramoto.py`. **Dependency**: Depends on T021 (ODE function).
- [X] T023 [US2] Implement binary search algorithm for $K_c$ (threshold defined qualitatively, max iterations, tol specified) in `code/simulate_kuramoto.py`. **Dependency**: Depends on T021 and T022.
- [X] T024 [US2] Implement fallback linear sweep if binary search fails in `code/simulate_kuramoto.py`. **Dependency**: Depends on T023.
- [ ] T025 [US2] Run simulation batch for all valid topologies from US1 using time steps resolved by T009 (read from `data/processed/config.json`).
 **Input**: `data/processed/graph_p*.gpickle`.
 **Output**: `data/processed/simulation_results.csv`.
 **Logic**: Run binary search for each topology. If `SC_003_VIOLATION` flag is set in `config.json`, run the reduced scope defined in `config.json` and log the reduction.
 **Verification**: `test -f data/processed/simulation_results.csv && echo 'OK' || exit 1`. Verify row count matches number of valid (connected) topologies in the reduced scope.
 **Constraint**: This task relies on T009's configuration; no fallback logic for time steps is allowed here.

- [ ] T026a [US2] [FR-009] Implement rotational invariance verification script `code/verify_invariance.py`.
 **Logic**: Re-run the full binary search for $K_c$ on each topology using two reference frames: "single oscillator" and "center-of-mass". These two frames are explicitly defined as the complete set required by FR-009 based on the spec's "e.g." clause and the Plan's interpretation.
 **Output**: `data/processed/invariance_verification.json`.
 **Output Schema**:
 ```json
 [
 {
 "topology_id": "string",
 "kc_single": "float",
 "kc_com": "float",
 "difference": "float",
 "status": "invariant|variant"
 }
 ]
 ```
 **Dependency**: Requires `data/processed/simulation_results.csv` from T025.
 **Note**: Strictly ordered AFTER T025.

- [ ] T026b [US2] [FR-009] Run `code/verify_invariance.py` and verify results.
 **Verification**: `test -f data/processed/invariance_verification.json && echo 'OK' || exit 1`.
 **Justification**: FR-009 requires system-wide verification; a subset is insufficient.

- [ ] T027a [US2] [SC-001] Implement stability check script `code/check_stability.py`.
 **Logic**: Simulate Kuramoto dynamics multiple times per topology for **ALL valid topologies**. **Run Count**: Read `run_count` from `data/processed/config.json` (default 1000, adjusted by `scope_reduction_factor` if applicable). Calculate sample variance of R.
 **Constraint**: If `run_count` < 1000 AND `SC_003_VIOLATION` is false, the task must log a warning and proceed, but the final report must explicitly state the deviation from SC-001. If `SC_003_VIOLATION` is true, the reduced `run_count` is accepted as a contingency.
 **Output**: `data/processed/stability_results.json`. **Schema**: `[{topology_id, variance, status: 'stable'|'unstable'}]`.
 **Logic**: If variance > 0.01, mark topology as 'unstable'. Do NOT halt. Log warning.
 **Dependency**: Requires `data/processed/simulation_results.csv` from T025.
 **Constraint**: If the number of 'unstable' topologies exceeds **10%** of the total, the script must set a `STABILITY_FAILURE` flag in the output JSON. If `run_count` is reduced below 1000 due to `SC_003_VIOLATION`, the script must log this reduction and proceed, but the final report must explicitly state the deviation from SC-001.
 **Note**: Strictly ordered AFTER T025.

- [ ] T027b [US2] Run `code/check_stability.py` to check stability.
 **Verification**: `test -f data/processed/stability_results.json && echo 'OK' || exit 1`.
 **Logic**: If `STABILITY_FAILURE` flag is set, the pipeline must halt with a 'STABILITY_FAILURE' error. If <10% unstable, the pipeline continues with a 'Partial Stability' status.

- [ ] T027c [US2] [FR-007] Implement sensitivity analysis script `code/sensitivity_analysis.py`.
 **Logic**: Sweep the order parameter threshold over a range of representative values. For each threshold, re-calculate the Spearman correlation coefficient and p-value between rewiring probability and critical coupling strength.
 **Output**: `data/processed/sensitivity_analysis.json`. **Schema**: `[{threshold, correlation_coef, p_value}]`.
 **Verification**: Run `python -c "import json; d=json.load(open('data/processed/sensitivity_analysis.json')); assert len(d)==3; assert {row['threshold'] for row in d} == {0.4, 0.5, 0.6}; assert all('correlation_coef' in row for row in d)"`.
 **Dependency**: Requires `data/processed/simulation_results.csv` from T025.
 **Note**: Strictly ordered AFTER T025.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently, with verified Kc values

---

## Phase 5: User Story 3 - Quantify Topological Influence via Statistical Correlation (Priority: P3)

**Goal**: Analyze the relationship between rewiring probability and critical coupling strength using Spearman correlation and sensitivity analysis.

**Independent Test**: The system can be tested by generating synthetic data with a known non-linear relationship and verifying the Spearman coefficient matches the expected value.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for Spearman correlation calculation in `tests/test_analysis.py`
- [ ] T029 [P] [US3] Integration test for sensitivity analysis sweep in `tests/test_analysis.py`

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement Spearman correlation and p-value calculation in `code/analyze_results.py`.
 **Input**: `data/processed/simulation_results.csv`.
 **Output**: `data/processed/correlation_results.json`.

- [ ] T031 [US3] Implement multiple-comparison correction logic in `code/analyze_results.py`. **Logic**: Read the pre-defined statistical model from `data/processed/analysis_config.yaml` (defined in T008). If the model specifies multiple tests, apply Bonferroni/Benjamini-Hochberg. If single regression, skip. Explicitly log the statistical model choice and whether correction was applied in the final report (FR-006, FR-008).

- [ ] T032 [US3] Implement sensitivity analysis sweep over thresholds in `code/analyze_results.py`. **Scope**: Sweep over the set {0.4, 0.5, 0.6} as defined in SC-004. **Note**: This set is explicitly justified in the spec's "Assumption about Threshold Justification".
 **Output**: `data/processed/sensitivity_analysis.json`.

- [ ] T033 [US3] Calculate the variation metric of the headline correlation rate across the sensitivity sweep. **Definition**: Calculate the Spearman correlation coefficient for each threshold in {0.4, 0.5, 0.6} (from `data/processed/sensitivity_analysis.json`). Compute the relative variation: (max(coef) - min(coef)) / mean(coef). Verify this value is ≤ 0.05 (SC-004).
 **Output**: Append result to `data/processed/sensitivity_analysis.json`.
 **Verification**: `test -f data/processed/sensitivity_analysis.json && echo 'OK' || exit 1`.

- [ ] T034 [US3] Generate summary plot (Critical Coupling vs. Rewiring Probability) with trend line in `code/analyze_results.py` saving to `data/processed/plot_kc_vs_p.png` and verify file exists and is non-empty.

- [ ] T035 [US3] Write final report summary to `data/processed/analysis_report.md` using `code/generate_report.py`.
 **Template**: Use `templates/analysis_report.md.j2` to render the report.
 **Content**:
 1. Spearman correlation value (float) and p-value.
 2. A dedicated section "Physical Invariance" citing the results from T026 (invariance_verification.json) and explicitly stating that the critical coupling is an observer-invariant property.
 3. Explicit definition and justification of the statistical model used (single regression vs. multiple tests) as defined in `data/processed/analysis_config.yaml`.
 4. A section "Stability Status" reporting the outcome of T027b (Success/Partial/Failure).
 5. A section "Scope Status" reporting the outcome of T009 (Full Suite/Partial Suite with reduction factor).
 6. A section "Sensitivity Analysis" reporting the outcome of T027c and T033 (variation in headline correlation rate).
 **Verification**: `test -f data/processed/analysis_report.md && echo 'OK' || exit 1`.

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
- **Critical Correction**: The base graph is a synthetic regular ring lattice (N=500), NOT the ca-AstroPh dataset, to ensure theoretical validity of the Watts-Strogatz parameter. This is documented in T000 (Spec Update), T012, and T012b. The spec's FR-001 requirement to use ca-AstroPh is a known contradiction pending a spec kickback, which is now resolved via T000 and T000a.
- **Time Steps**: T009 resolves the [deferred] time steps; T025 uses the resolved value from `data/processed/config.json`. **Warning**: T009 must not silently reduce steps below [deferred] without logging a contingency, but MUST find the max feasible steps if [deferred] is too slow.
- **Verification**: FR-009 verification is integrated into Phase 4 as T026 (ALL 50 topologies).
- **Stability**: SC-001 stability check is integrated into Phase 4 as T027a (ALL 50 topologies). T027a flags unstable topologies; T027b aggregates and determines pipeline status (Success/Partial/Failure).
- **Sensitivity**: FR-007 sensitivity analysis is integrated into Phase 4 as T027c. T027c sweeps thresholds and records correlation coefficients; T033 calculates the variation metric.
- **Runtime**: SC-003 runtime check is integrated into Phase 4 as T025 with fallback logic (max(1000,...)). T009 sets `SC_003_VIOLATION` flag if scope is reduced; T025 runs reduced scope; T035 reports 'Partial Satisfaction'.
- **Removed**: T017 and T036 have been removed to eliminate duplication and ensure a single source of truth.
- **Reviewer Response (albert-einstein-simulated)**: Task T026 explicitly addresses the concern regarding physical invariance by verifying that the critical coupling strength $K_c$ is identical regardless of whether the phase reference is a single oscillator or the center-of-mass. This ensures the symbol $K_c$ corresponds to an element of physical reality independent of the observer's coordinate frame.
- **Statistical Model**: T031 reads the pre-defined statistical model from `analysis_config.yaml` (created in T008) to determine correction logic, ensuring the model is defined before analysis as per FR-008.
- **Stability Fallback Correction**: Task T027a has been updated to read `run_count` from `config.json` (generated by T009) to handle scope reduction dynamically.
- **Task Order**: T004/T005 are before T009. T006 is now first in Phase 2. T009 is before T008. T025 is before T026, T027a, and T027c. T008 is now listed after T009 in the task list to reflect the data flow. T012b is now before T012. T000 and T000a are now in Phase 1.
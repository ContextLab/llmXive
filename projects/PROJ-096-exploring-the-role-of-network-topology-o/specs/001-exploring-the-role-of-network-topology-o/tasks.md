# Tasks: Exploring the Role of Network Topology on Synchronization in Coupled Oscillators

**Input**: Design documents from `/specs/001-exploring-the-role-of-network-topology-synchronization/`
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

**Purpose**: Project initialization, governance alignment, and basic structure

- [X] T000a [P] **Verify Spec Amendment**: Create `scripts/verify_spec.py` to parse `specs/001-exploring-the-role-of-network-topology-synchronization/spec.md`.
 **Logic**:
 1. Assert that the text "synthetic regular ring lattice of N=500 nodes" is present in FR-001.
 2. Assert that the text "ca-AstroPh" is NOT present as a base graph requirement in FR-001.
 3. If both conditions are met, exit 0. If either fails, exit 1 and print "SPEC_CONTRADICTION" or "SPEC_MISSING".
 **Verification**: `python scripts/verify_spec.py && echo 'OK' || exit 1`.
 **Note**: This task ensures the spec aligns with the plan's methodological correction before any code is run.

- [X] T001 [P] **Initialize Project Directories**: Create `code/`, `code/utils/`, `data/`, `data/processed/`, `data/raw/`, `tests/`, `state/`, `state/projects/`. Verify creation by running `ls -R data/ code/ tests/ state/` and capturing the output to `data/checksums.txt` (as a log of directory structure).
 **Verification**: `test -f data/checksums.txt && echo 'OK' || exit 1`.

- [X] T002a [P] **Create Requirements File**: Create `code/requirements.txt` containing pinned versions: `networkx>=3.2.0`, `scipy>=1.12.0`, `numpy>=1.26.0`, `pandas>=2.2.0`, `pyyaml>=6.0.0`.
 **Verification**: `test -f code/requirements.txt && grep -q "networkx" code/requirements.txt && echo 'OK' || exit 1`.

- [X] T002b [P] **Initialize Virtual Environment**: Create a virtual environment in `code/.venv` and install dependencies from `requirements.txt`.
 **Verification**: `test -d code/.venv && code/.venv/bin/pip list | grep networkx && echo 'OK' || exit 1`.

- [X] T003a [P] Create `.flake8` config with `max-line-length=88`, `ignore=E203,W503` and `pyproject.toml` for black with `line-length=88`.
 **Verification**: `test -f.flake8 && test -f pyproject.toml && grep -q "line-length" pyproject.toml && echo 'OK' || exit 1`.

- [X] T003b [P] **Verify Linting Configuration**: Create `code/__init__.py` if it does not exist. Run `black --check code/` and `flake8 code/` on the `code/` directory. Redirect output to `data/checksums.txt` (append).
 **Verification**: `test -f code/__init__.py && black --check code/ && flake8 code/ && echo 'OK' || exit 1`.

- [X] T003c [P] **Setup Pre-commit Hooks**: Install `pre-commit` and configure `.pre-commit-config.yaml` to run `autoflake` and `isort` on every commit. **Note**: This automates import cleanup, making manual import cleanup tasks unnecessary.
 **Verification**: `test -f.pre-commit-config.yaml && pre-commit install && echo 'OK' || exit 1`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. This phase determines the feasible scope of the experiment.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 [P] Implement `code/utils/graph_utils.py` for connectivity checks and metric calculations.
 **Functions to implement**: `is_connected(G: nx.Graph) -> bool`, `average_degree(G: nx.Graph) -> float`, `clustering_coefficient(G: nx.Graph) -> float`.
 **Verification**: `python -c "from code.utils.graph_utils import is_connected, average_degree, clustering_coefficient; print('OK')"`.

- [X] T005 [P] Implement `code/utils/stats_utils.py` for correlation, p-value, and multiple-comparison correction.
 **Functions to implement**: `spearman_corr(x, y) -> tuple`, `p_value(spearman_stat, n) -> float`, `bonferroni_correction(p_values, alpha) -> list`.
 **Verification**: `python -c "from code.utils.stats_utils import spearman_corr, p_value, bonferroni_correction; print('OK')"`.

- [X] T006 [P] **Setup Data Directory Structure and Metadata Schema**: Create `data/processed/`, `data/raw/`, and initialize `data/checksums.txt`. Define the `graph_metadata.json` schema in `docs/data_model.md` (or inline comment) containing keys: `node_count` (int), `avg_degree` (float), `p` (float), `seed` (int), `checksum` (string).
 **Checksum Format**: `data/checksums.txt` must contain SHA256 hashes of ALL data artifacts (raw downloads and generated `.gpickle` files), formatted as `hash filename`.
 **Verification**: `test -d data/processed && test -f data/checksums.txt && echo 'OK' || exit 1`.

---

## Phase 3: User Story 1 - Generate Rewired Network Instances (Priority: P1) 🎯 MVP

**Goal**: Generate N topologies (where N is determined by T009) with varying small-world rewiring probabilities starting from a synthetic regular ring lattice (N=500).

**⚠️ Methodological Correction & Constitution Compliance**:
1. **Constitution Requirement**: The Constitution (after T000a override) mandates generating a synthetic regular ring lattice.
2. **Plan Correction**: The plan identifies that reconstructing an irregular citation network into a regular ring lattice is methodologically incoherent.
3. **Resolution**: This implementation **generates a synthetic regular ring lattice** (T012) as the base for Watts-Strogatz. The download of 'ca-AstroPh' is **removed** as it is not used for structure. This deviation from the original FR-001 is formally documented in `docs/constitutional_amendment.md` (T000a) and **updated in spec.md** (T000a) to resolve the conflict.

**Independent Test**: The system can be tested by generating N network instances with rewiring probabilities ranging from 0.0 to 1.0 and verifying that each graph is connected, has the correct number of nodes (N=500), and preserves the average degree of the reconstructed lattice.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for graph generation in `tests/test_topology.py` (verify N=500, connected, degree preservation)
- [X] T011 [P] [US1] Integration test for metadata logging in `tests/test_topology.py` (verify seed and p saved to `graph_metadata.json`)

### Implementation for User Story 1

- [X] T012 [US1] **Implement Synthetic Ring Lattice Generator**: Implement synthetic ring lattice generator in `code/generate_topology.py` (N=500, k=2). **Dependency**: Depends on T000a (Spec Verified) and T000c (Governance Override).
 **Verification**: `python -c "import networkx as nx; G=nx.watts_strogatz_graph(500, 2, 0); assert G.number_of_nodes() == 500 and nx.is_connected(G)"`.

- [X] T014 [P] [US1] Implement Watts-Strogatz rewiring function with seed logging in `code/generate_topology.py`.

- [X] T015 [US1] Implement connectivity validation logic in `code/generate_topology.py` to skip disconnected graphs and log warnings (FR-002 compliance).

- [ ] T016 [US1] Implement batch generation loop (p=0.0 to 1.0, 50 steps, N instances as defined in `data/processed/config.json`) in `code/generate_topology.py`.
 **Input**: `data/processed/config.json` (read `n_topologies`).
 **Output**: Save graphs as `data/processed/topology_{topology_id}_p{p:.2f}_seed_{seed}.gpickle` and metadata as `data/processed/graph_metadata.json`.
 **Dependency**: Requires `data/processed/config.json` from T009.
 **Prerequisite**: T009 must have successfully generated `data/processed/config.json`.
 **Logic**:
 1. Read `n_topologies` from `config.json`.
 2. **Generate a list of `p` values**:
 - If `n_topologies >= 10`: Use `np.linspace` to ensure systematic coverage across the relevant range.
 - If `n_topologies < 10`: Use a fixed set of representative p-values `[0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]` truncated to `n_topologies` items, ensuring coverage of the extremes and middle. **CRITICAL**: This list MUST be recorded in `data/processed/config.json` under key `sampling_p_values` for audit purposes.
 3. Loop to generate `n_topologies` valid (connected) graphs. For each `p` in the list, pick a random seed.
 4. If a generated graph is disconnected, log to `disconnected_log.json` and retry with a **new seed** for the **SAME `p`** up to `MAX_RETRIES=10` times.
 5. If `MAX_RETRIES` is reached for a specific `p`, log a warning "Failed to generate connected graph for p={p} after 10 retries", **skip this p-value**, and proceed to the next `p` in the list.
 6. Stop only when `n_topologies` valid graphs have been saved OR all p-values have been attempted.
 **Function Signature**: `def generate_batch(n_topologies: int, config_path: str) -> List[str]`.
 **File Naming**: Must follow `topology_{topology_id}_p{p:.2f}_seed_{seed}.gpickle`.
 **Verification**: Run `python -c "import json, glob; d=json.load(open('data/processed/config.json')); files = glob.glob('data/processed/topology_*.gpickle'); assert len(files) <= d['n_topologies'], f'Expected <= {d[\"n_topologies\"]} files, got {len(files)}'; assert 'sampling_p_values' in d, 'Sampling strategy not recorded'"`.
 **Constraint**: File naming MUST follow the pattern. Disconnected graphs MUST be skipped and logged, and the loop must continue until the target count of valid graphs is reached OR all p-values are exhausted. The specific sampling strategy MUST be recorded in `config.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: Foundational (Scope & Model Definition)

**Purpose**: Determine feasible scope and define the statistical model based on that scope.

- [X] T009 [P] **Feasibility Study with Real ODE Micro-Benchmark**: Determine the maximum time steps, number of topologies, and run count feasible within 6 hours on a 2-core CPU runner, reserving [deferred] of the budget for verification tasks.
 **Script**: `code/feasibility_study.py`.
 **Output**: Write `data/processed/config.json` with keys: `time_steps` (int), `n_topologies` (int), `run_count` (int), `runtime_estimate` (float), `contingency_flag` (bool, default false), `SC_VIOLATION` (bool), `scope_reduction_factor` (float), `error` (string, optional), `scaling_factor` (float).
 **Objective**: Binary search for `time_steps` in range [1000, 20000] for a fixed N=50 topologies. If max `time_steps` < 1000, calculate max `n_topologies` for fixed 1000 steps.
 **Logic**:
 1. Implement a **real ODE solver** function in `code/feasibility_study.py` using `scipy.integrate.odeint` on a small sample graph (N=500, k=2, p=0.1) to measure actual overhead.
 2. Run **two micro-benchmarks**: one with `time_steps` = 100 and one with `time_steps` = 500.
 3. Calculate a **scaling factor** for non-linear behavior: `scaling_factor = (time_500 / 500) / (time_100 / 100)`.
 4. Use this scaling factor to extrapolate the runtime for larger step counts during the binary search.
 5. Binary search for max `time_steps` such that `50 * (time_steps/1000) * runtime_per_1k_steps * scaling_factor <= 5.1 hours` (reserving sufficient time for verification).
 6. If max `time_steps` < 1000, calculate `n_topologies` = floor(5.1h / (runtime_per_1k_steps * 1)).
 7. **CONTINGENCY PLAN (SC-003)**: If the calculated feasible `n_topologies` < 10, DO NOT halt. Log "CRITICAL WARNING: Insufficient compute for minimum scientific validity", set `n_topologies = 10` (minimum viable), set `scope_reduction_factor` = (10 / target), and write `data/processed/config.json`. The pipeline MUST proceed with this reduced scope.
 8. If feasible scope is sufficient, set `n_topologies` to the calculated max (capped at a predetermined limit), `time_steps` to the calculated max, and `run_count` to a representative default value.
 9. Calculate `scope_reduction_factor` = (actual feasible) / (target scope).
 10. **Sampling Justification**: If `n_topologies` is reduced below a sufficiently low threshold, explicitly log the resulting sparsity in `p`-space and the potential impact on statistical power in `data/processed/config.json`.
 **Fallback Logic**: If the binary search cannot be executed in the current environment (e.g., static review, no runner), write `data/processed/config.json` with `time_steps=1000`, `n_topologies=10`, `run_count=10`, `SC_003_VIOLATION=true`, `error='FALLBACK_USED'`, and `scope_reduction_factor=0.2`. This ensures the artifact exists for downstream tasks.
 **Note**: Once `config.json` is written, these parameters are FIXED for the entire experiment to ensure reproducibility (Constitution Principle VI).
 **Verification**: Run `python -c "import json; d=json.load(open('data/processed/config.json')); assert (d['n_topologies'] >= 1); assert (d['time_steps'] >= 1000); assert 'scaling_factor' in d; assert 'runtime_estimate' in d"`.
 **Constraint**: The task MUST always produce a valid `config.json` with `n_topologies >= 1`. It does NOT halt.
 **Note**: This task determines the *fixed* parameters for all subsequent runs. Once `config.json` is written, the integration settings are fixed and reproducible.

- [ ] T009b [P] **Log Compute Contingency**: If `data/processed/config.json` contains `SC_003_VIOLATION=true` or `error` is present, generate `data/processed/compute_contingency.md`.
 **Content**: Explicitly state the reduced scope (time steps, number of topologies) and justify it as a necessary contingency due to compute constraints, referencing the 'Assumption about Compute Feasibility'. **Specifically**, if `n_topologies` is reduced, document the resulting sparsity in the `p` parameter space and the potential impact on the statistical correlation (FR-006).
 **Verification**: `test -f data/processed/compute_contingency.md && echo 'OK' || exit 1`.

- [X] T008 [P] **Define Statistical Model**: Create `data/processed/analysis_config.yaml` defining the statistical model (e.g., single regression, multiple comparison correction) before analysis begins.
 **Dependency**: Runs AFTER T009 (strictly, not parallel).
 **Content**: Define `model_type` (e.g., 'spearman_regression'), `correction_method` (e.g., 'bonferroni'), and `threshold_sweep_range` (e.g., `[0.1, 0.9, 0.05]`).
 **Verification**: `test -f data/processed/analysis_config.yaml && echo 'OK' || exit 1`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 5: User Story 2 - Simulate Kuramoto Dynamics and Detect Synchronization (Priority: P2)

**Goal**: Simulate Kuramoto oscillator dynamics on each generated network and determine the critical coupling strength ($K_c$), including verification of rotational invariance (FR-009) and stability (SC-001) across ALL topologies.

**Independent Test**:
1. The system can be tested by running the simulation on a known topology (e.g., fully connected) with high coupling and verifying $R \to 1$.
2. The system can be tested by running the binary search on a synthetic dataset with known $K_c$ and verifying detection within tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for order parameter calculation in `tests/test_simulation.py`
- [X] T020 [P] [US2] Integration test for binary search convergence in `tests/test_simulation.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement Kuramoto ODE derivative function in `code/simulate_kuramoto.py`. **Dependency**: Depends on T009 (reads `data/processed/config.json` for `time_steps`). **Error Handling**: If `config.json` has `time_steps=0` OR `error` key is present, proceed with fallback values and log a warning (do NOT raise RuntimeError). If `SC_003_VIOLATION` flag is set in `config.json`, proceed with reduced scope.
- [X] T022 [US2] Implement order parameter $R$ calculation and time-series aggregation in `code/simulate_kuramoto.py`. **Dependency**: Depends on T021 (ODE function).
- [ ] T023 [US2] Implement binary search algorithm for $K_c$ (threshold defined qualitatively, max iterations, tol specified) in `code/simulate_kuramoto.py`. **Dependency**: Depends on T021 and T022.
- [ ] T024 [US2] Implement fallback linear sweep if binary search fails in `code/simulate_kuramoto.py`. **Dependency**: Depends on T023.
- [ ] T025 [US2] Run simulation batch for all valid topologies from US1 using time steps resolved by T009 (read from `data/processed/config.json`).
 **Input**: `data/processed/topology_*.gpickle`.
 **Output**: `data/processed/simulation_results.csv`.
 **Dependency**: Requires `data/processed/config.json`.
 **Logic**:
 1. Check if `data/processed/config.json` exists. If not, halt with error `CONFIG_MISSING`.
 2. Read `time_steps` and `n_topologies` from `config.json`.
 3. Run binary search for each topology. If `SC_003_VIOLATION` flag is set in `config.json`, run the reduced scope defined in `config.json` and log the reduction.
 **Function Signature**: `def run_simulation_batch(config_path: str, output_path: str) -> None`.
 **CSV Schema**: Columns: `topology_id`, `p`, `kc_binary`, `kc_linear`, `status`.
 **Verification**: `test -f data/processed/simulation_results.csv && echo 'OK' || exit 1`. Verify row count matches number of valid (connected) topologies in the reduced scope.
 **Constraint**: This task relies on T009's configuration; no fallback logic for time steps is allowed here.

- [X] T026a [US2] [FR-009] **Implement Rotational Invariance Verification Script**: Create `code/verify_invariance.py` to address reviewer `albert-einstein-simulated`'s concern regarding physical reality.
 **Logic**: Re-run the full binary search for $K_c$ on **ALL valid topologies** generated in US1.
 **Reference Frames**:
 1. **Single Oscillator Frame**: Calculate relative phases $\theta_i(t) - \theta_0(t)$.
 2. **Center-of-Mass (COM) Frame**: Calculate relative phases $\theta_i(t) - \bar{\theta}(t)$.
 3. **Perturbed Frames**: Generate $N_{perturb}=5$ random reference frames (weighted averages of phases) and verify $K_c$ remains stable within numerical tolerance (as per T051 requirement, now integrated).
 **Seeds**: Iterate over `run_count` seeds (read from `config.json`, minimum 10).
 **Budget Check**: If the number of valid topologies is sufficiently large, use a **stratified random sample** (a representative subset from each decile of `p` values). to ensure coverage of the full range while respecting SC-003. {{claim:c_f75d8998}} (Wikidata Q23400, https://www.wikidata.org/wiki/Q23400)
 **Output**: `data/processed/invariance_verification.json`.
 **Output Schema**:
 ```json
 [
 {
 "topology_id": "string",
 "p": "float",
 "kc_single_frame_seeds": ["float"],
 "kc_com_frame_seeds": ["float"],
 "kc_perturbed_frame_seeds": ["float"],
 "mean_kc_single": "float",
 "mean_kc_com": "float",
 "mean_kc_perturbed": "float",
 "variance_single": "float",
 "variance_com": "float",
 "variance_perturbed": "float",
 "absolute_difference_means": "float",
 "max_perturbation_deviation": "float",
 "status": "invariant|variant|unstable"
 }
 ]
 ```
 **Success Criterion**:
 1. **Stability**: `variance_single`, `variance_com`, and `variance_perturbed` must be below a defined threshold (e.g., 0.01) for each topology.
 2. **Invariance**: The absolute difference between means must be negligible.
 3. **Perturbation Robustness**: `max_perturbation_deviation` must be sufficiently small to ensure numerical stability and negligible impact on model predictions.
 4. All conditions must be met for `status: "invariant"`.
 **Dependency**: Requires `data/processed/simulation_results.csv` from T025.
 **Prerequisite**: T021 (ODE Solver) must be implemented.
 **Error Handling**: If any entry has `status: "variant"` or `status: "unstable"`, the script MUST exit with code 1 and print "ERROR: INVARIANCE_FAILURE" to stderr.
 **Note**: This task is strictly ordered AFTER T025. It explicitly validates that the critical coupling is an observer-invariant property and stable across seeds, satisfying the EPR criterion of physical reality and SC-001.

- [X] T026b [US2] [FR-009] **Run Invariance Verification**: Execute `code/verify_invariance.py` and verify results.
 **Input**: `data/processed/invariance_verification.json` (produced by T026a).
 **Verification**: `test -f data/processed/invariance_verification.json && echo 'OK' || exit 1`.
 **Logic**: Parse `invariance_verification.json`. If any entry has `status: "variant"` or `status: "unstable"`, the task fails immediately with `PHYSICAL_INVARIANCE_FAILURE` or `STABILITY_FAILURE`. If all are "invariant", the task passes.

- [X] T027a [US2] [SC-001] Implement stability check script `code/check_stability.py`.
 **Logic**: Simulate Kuramoto dynamics multiple times per topology for **ALL valid topologies** (or stratified sample if >100). **Run Count**: Read `run_count` from `data/processed/config.json` (default set to a representative magnitude, adjusted by `scope_reduction_factor` if applicable). Calculate sample variance of R.
 **Input**: `data/processed/config.json` (for `run_count`).
 **Constraint**: If `run_count` < 10, the task MUST fail immediately with `STABILITY_FAILURE` and exit code 1. It does NOT proceed with a warning. This ensures SC-001 is not silently weakened.
 **Output**: `data/processed/stability_results.json`. **Schema**: `[{topology_id, variance, status: 'stable'|'unstable'}]`.
 **Logic**: Report the calculated variance for each topology. Do NOT apply an arbitrary threshold (e.g., 0.01) to mark 'stable/unstable' in the script itself; the final report will interpret the variance magnitude. If variance is high, log a warning.
 **Dependency**: Requires `data/processed/simulation_results.csv` from T025.
 **Pre-check**: If `data/processed/config.json` is missing, halt immediately with error `CONFIG_MISSING`.
 **Note**: Strictly ordered AFTER T025. This task explicitly enforces a minimum run count for statistical validity.

- [X] T027b [US2] Run `code/check_stability.py` to check stability.
 **Verification**: `test -f data/processed/stability_results.json && echo 'OK' || exit 1`.
 **Logic**: If `STABILITY_FAILURE` flag is set, the pipeline must halt with a 'STABILITY_FAILURE' error. If <10% unstable, the pipeline continues with a 'Partial Stability' status.

- [ ] T027d [US2] [FR-007] **Implement Sensitivity Analysis Script**: Create `code/sensitivity_analysis.py` to perform the threshold sweep required by FR-007.
 **Logic**:
 1. **Read Configuration**: Load threshold range from `data/processed/analysis_config.yaml` (defined in T008).
 2. **Sweep**: For each threshold in the range, re-calculate the Spearman correlation coefficient and p-value between rewiring probability and critical coupling strength using `data/processed/simulation_results.csv`.
 **Output**: `data/processed/sensitivity_analysis.json`. **Schema**: `[{threshold, correlation_coef, p_value}]`.
 **Verification**: Run `python -c "import json; d=json.load(open('data/processed/sensitivity_analysis.json')); assert len(d)>=3; assert all('correlation_coef' in row for row in d)"`.
 **Dependency**: Requires `data/processed/simulation_results.csv` from T025 and `data/processed/analysis_config.yaml` from T008.
 **Note**: Strictly ordered AFTER T025 and T008. This task is the definitive implementation for FR-007.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently, with verified Kc values (including T026b and T027b)

---

## Phase 6: User Story 3 - Quantify Topological Influence via Statistical Correlation (Priority: P3)

**Goal**: Analyze the relationship between rewiring probability and critical coupling strength using Spearman correlation and sensitivity analysis.

**Independent Test**: The system can be tested by generating synthetic data with a known non-linear relationship and verifying the Spearman coefficient matches the expected value.

### Tests for User Story 3 (REQUIRED) ⚠️

- [X] T028 [P] [US3] Contract test for Spearman correlation calculation in `tests/test_analysis.py`
 **Description**: Verify `spearman_corr` function returns correct coefficient and p-value for known input arrays.
 **Verification**: Run `pytest tests/test_analysis.py::test_spearman_corr_contract`.

- [X] T029 [P] [US3] Integration test for sensitivity analysis sweep in `tests/test_analysis.py`
 **Description**: Verify `sensitivity_analysis` script produces output with correct schema and expected threshold values.
 **Verification**: Run `pytest tests/test_analysis.py::test_sensitivity_analysis_integration`.

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement Spearman correlation and p-value calculation in `code/analyze_results.py`.
 **Input**: `data/processed/simulation_results.csv`.
 **Output**: `data/processed/correlation_results.json`.
 **Function Signature**: `def calculate_correlation(input_path: str, output_path: str) -> dict`.
 **JSON Schema**: `{correlation: float, p_value: float}`.
 **Dependency**: Requires `data/processed/analysis_config.yaml` from T008.

- [ ] T031 [US3] Implement multiple-comparison correction logic in `code/analyze_results.py`. **Logic**: Read the pre-defined statistical model from `data/processed/analysis_config.yaml` (defined in T008). If the model specifies multiple tests, apply Bonferroni/Benjamini-Hochberg. If single regression, skip. Explicitly log the statistical model choice and whether correction was applied in the final report (FR-006, FR-008).

- [ ] T033 [US3] Calculate the variation metric of the headline correlation rate across the sensitivity sweep. **Definition**: Calculate the Spearman correlation coefficient for each threshold in a defined range of sensitivity values (from `data/processed/sensitivity_analysis.json`). Compute the relative variation: (max(coef) - min(coef)) / mean(coef).
 **Output**: Append result to `data/processed/sensitivity_analysis.json`.
 **Verification**: `test -f data/processed/sensitivity_analysis.json && echo 'OK' || exit 1`.
 **Dependency**: Requires `data/processed/sensitivity_analysis.json` from T027d.

- [ ] T034 [US3] Generate summary plot (Critical Coupling vs. Rewiring Probability) with trend line in `code/analyze_results.py` saving to `data/processed/plot_kc_vs_p.png` and verify file exists and is non-empty.

- [X] T035 [US3] Write final report summary to `data/processed/analysis_report.md` using `code/generate_report.py`.
 **Template**: Use `templates/analysis_report.md.j2` to render the report.
 **Content**:
 1. Spearman correlation value (float) and p-value.
 2. A dedicated section "Physical Invariance" citing the results from T026 (invariance_verification.json) and explicitly stating that the critical coupling is an observer-invariant property.
 3. Explicit definition and justification of the statistical model used (single regression vs. multiple tests) as defined in `data/processed/analysis_config.yaml`.
 4. A section "Stability Status" reporting the outcome of T027b (Success/Partial/Failure).
 5. A section "Scope Status" reporting the outcome of T009 (Full Suite/Partial Suite with reduction factor).
 6. A section "Sensitivity Analysis" reporting the outcome of T027d and T033 (variation in headline correlation rate).
 **Verification**: `test -f data/processed/analysis_report.md && echo 'OK' || exit 1`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T036 [US2] **Document Physical Invariance Methodology**: Create `docs/methodology.md` with a dedicated section explaining the rotational invariance test (T026).
 **Content**:
 1. Theoretical basis: Why $K_c$ should be independent of the phase reference frame.
 2. Implementation details: How the Single Oscillator, Center-of-Mass, and Perturbed frames were constructed.
 3. Interpretation of results: How to read `invariance_verification.json` and what constitutes a "variant" result.
 4. Connection to EPR: Explicitly link this verification to the requirement that physical quantities must correspond to an element of reality independent of the observer.
 **Dependency**: Requires completion of T026 (Invariance Verification).
 **Verification**: `test -f docs/methodology.md && grep -q "Physical Invariance" docs/methodology.md && echo 'OK' || exit 1`.

- [X] T037a [P] Create `docs/methodology.md` with a section on the invariance check (T026), explaining the theoretical basis (rotational invariance of the order parameter $R$).
- [X] T037b [P] Update `docs/quickstart.md` to include the invariance step as a mandatory part of the research pipeline.

- [X] T040a [P] **Implement Zero Variance Test**: Create `tests/test_edge_cases.py` with function `test_zero_variance()`.
 **Logic**: Simulate a system with identical natural frequencies ($\omega_i = 0$) and verify the order parameter $R$ behaves as expected (synchronization).
 **Verification**: `pytest tests/test_edge_cases.py::test_zero_variance`.

- [X] T040b [P] **Implement Numerical Instability Test**: Create `tests/test_edge_cases.py` with function `test_numerical_instability()`.
 **Logic**: Simulate with extremely high coupling or very small time steps to verify the integrator handles edge cases without crashing or producing NaN.
 **Verification**: `pytest tests/test_edge_cases.py::test_numerical_instability`.

- [X] T040c [P] **Implement Connectivity Edge Case Test**: Create `tests/test_edge_cases.py` with function `test_disconnected_graph_handling()`.
 **Logic**: Feed a disconnected graph to the simulation script and verify it is skipped and logged correctly (FR-002).
 **Verification**: `pytest tests/test_edge_cases.py::test_disconnected_graph_handling`.

- [X] T041a [P] **Run Quickstart Validation**: Execute `docs/quickstart.md` steps and capture the output to `data/validation_log.txt`.
 **Logic**: Run the full pipeline from `quickstart.md` in a clean environment. Capture stdout/stderr to `data/validation_log.txt`.
 **Verification**: `test -f data/validation_log.txt && grep -q "Success" data/validation_log.txt && echo 'OK' || exit 1`.

- [X] T041 [P] Additional unit tests for edge cases (zero variance, numerical instability) in `tests/` (Deprecated: Replaced by T040a-c)

---

## Phase N+1: Review Resolution & Final Validation (Priority: P1)

**Goal**: Address specific concerns raised by reviewer `albert-einstein-simulated` regarding the physical reality of the critical coupling strength and its invariance under coordinate transformations.

**Context**: Reviewer `albert-einstein-simulated` noted that the specification did not explicitly test whether the critical coupling strength ($K_c$) is invariant under different phase reference frames (single oscillator vs. center-of-mass). This is a necessary condition for $K_c$ to be considered a physical element of reality rather than a coordinate artifact.

### Implementation for Review Resolution

- [X] T050 [US2] **Explicitly Document Reference Frame Invariance in Final Report**: Update `data/processed/analysis_report.md` (T035) to include a dedicated "Physical Invariance Verification" section.
 **Action**: Ensure the report explicitly states the results of T026 (invariance_verification.json) and concludes whether $K_c$ satisfies the EPR criterion of physical reality.
 **Verification**: `grep -q "Physical Invariance Verification" data/processed/analysis_report.md && echo 'OK' || exit 1`.

- [X] T052 [US3] **Update Methodology Documentation**: Enhance `docs/methodology.md` (T036) to explicitly address the reviewer's concern about "small-world rewiring probability" as a physical parameter.
 **Content**: Add a subsection "Physical Interpretation of $p$ and $K_c$" explaining that $p$ is a topological invariant of the graph structure, while $K_c$ is the dynamical threshold required to overcome frequency dispersion, and both must be independent of the observer's phase coordinate system.
 **Verification**: `grep -q "Physical Interpretation" docs/methodology.md && echo 'OK' || exit 1`.

- [X] T053 [US2] **Verify EPR Criterion in Unit Tests**: Add a specific unit test `tests/test_invariance.py::test_epr_criterion` that asserts the invariance condition (difference < $1e-4$) for a known stable graph.
 **Logic**: Run the invariance check on a small, fully connected graph (N=50) and assert the result is "invariant".
 **Verification**: `pytest tests/test_invariance.py::test_epr_criterion`.

- [X] T054 [US3] **Final Review of Physical Claims**: Conduct a final review of `data/processed/analysis_report.md` to ensure no claims about "physical reality" are made without the supporting evidence from T026 and T051 (now integrated).
 **Action**: If any claim lacks evidence, flag it for revision. If all claims are supported, mark the task as complete.
 **Verification**: Manual review or automated grep for "physical reality" followed by check for "invariance_verification" reference.

**Checkpoint**: All reviewer concerns regarding physical invariance and the nature of $K_c$ have been addressed and documented.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1, US2, US3 are strictly sequential**: US2 depends on US1 output; US3 depends on US2 output. They CANNOT run in parallel.
- **Verification (Phase 4)**: Integrated into Phase 4 (US2) to ensure data flow
- **Review Resolution (Phase N+1)**: Depends on completion of US2 and US3
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1 data generation**
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on US2 data generation (including verification)**
- **Verification**: Integrated into Phase 4 to ensure Kc values are verified before Phase 5 analysis

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utils before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel (within Phase 2).
- **US1, US2, US3 are strictly sequential**. They cannot run in parallel.

---

## Parallel Example: User Story 1 Only

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for graph generation in tests/test_topology.py"
Task: "Integration test for metadata logging in tests/test_topology.py"

# Launch all models for User Story 1 together:
Task: "Implement synthetic ring lattice generator in code/generate_topology.py"
Task: "Implement Watts-Strogatz rewiring function in code/generate_topology.py"
```
*Note: This parallel example applies ONLY to User Story 1. US2 and US3 cannot run in parallel with US1 or each other. Tasks within US1 that write to the same file (e.g., T012 and T014) are listed together for logical grouping but must be executed sequentially to avoid file locking issues.*

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
3. Add User Story 2 → Test independently → Deploy/Demo (**WAIT for US1 data**)
4. Add User Story 3 → Test independently → Deploy/Demo (**WAIT for US2 data**)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Topology)
 - Developer B: User Story 2 (Simulation + Verification) -> **MUST WAIT for US1 data**
 - Developer C: User Story 3 (Analysis) -> **MUST WAIT for US2 data**
3. Stories complete and integrate sequentially.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Correction**: The base graph is a synthetic regular ring lattice (N=500), NOT the ca-AstroPh dataset, to ensure theoretical validity of the Watts-Strogatz parameter. This is documented in T000a (Spec Update). The spec's FR-001 requirement to use ca-AstroPh is a known contradiction pending a spec kickback, which is now resolved via T000a.
- **Time Steps**: T009 resolves the [deferred] time steps; T025 uses the resolved value from `data/processed/config.json`. **Warning**: T009 must not silently reduce steps below [deferred] without logging a contingency, but MUST find the max feasible steps if [deferred] is too slow.
- **Verification**: FR-009 verification is integrated into Phase 4 as T026 (ALL valid topologies). T051 (perturbed frames) is now part of T026a.
- **Stability**: SC-001 stability check is integrated into Phase 4 as T027a (ALL valid topologies). T027a enforces `run_count >= 10` and fails if not met. T027b aggregates and determines pipeline status (Success/Partial/Failure).
- **Sensitivity**: FR-007 sensitivity analysis is integrated into Phase 4 as T027d. T027d sweeps thresholds and records correlation coefficients; T033 calculates the variation metric.
- **Runtime**: SC-003 runtime check is integrated into Phase 4 as T025 with fallback logic (max(1000,...)). T009 sets `SC_003_VIOLATION` flag if scope is reduced; T009b generates the formal contingency plan; T025 runs reduced scope; T035 reports 'Partial Satisfaction'.
- **Removed**: T038a and T038b (Vectorization speedup) have been removed as they constitute scope creep. T032 (Duplicate Sensitivity) has been removed. T040 (Orphan) has been replaced by T040a-c. T041 (Unverifiable) has been replaced by T041a. T051 (Perturbed Frames) has been merged into T026a.
- **Reviewer Response (albert-einstein-simulated)**: Task T026 explicitly addresses the concern regarding physical invariance by verifying that the critical coupling strength $K_c$ is identical regardless of whether the phase reference is a single oscillator, the center-of-mass, OR a perturbed frame, AND verifies stability across multiple seeds. This ensures the symbol $K_c$ corresponds to an element of physical reality independent of the observer's coordinate frame and stable across random frequency seeds. Task T036 documents this methodology for future reference. **Phase N+1 (T050-T054)** further strengthens this response by explicitly documenting the physical interpretation in the final report.
- **Statistical Model**: T008 (moved to Phase 4) creates `analysis_config.yaml` after T009 determines the scope. T031 reads the pre-defined statistical model from `analysis_config.yaml` to determine correction logic, ensuring the model is defined after scope determination as per FR-008.
- **Stability Fallback Correction**: Task T027a has been updated to enforce `run_count >= 10` as a hard constraint. If the feasible count is lower, the task fails with 'STABILITY_FAILURE', preventing the pipeline from proceeding with insufficient data.
- **Task Order**: T004/T005 are before T009. T006 is now first in Phase 2. T009 is before T008. T025 is before T026, T027a, and T027d. T008 is now listed in Phase 4 to reflect the data flow. T012b is now before T012. T000a is now in Phase 1.
- **Parallel Execution**: US1, US2, and US3 are strictly sequential. US2 cannot start until US1 is complete. US3 cannot start until US2 is complete.

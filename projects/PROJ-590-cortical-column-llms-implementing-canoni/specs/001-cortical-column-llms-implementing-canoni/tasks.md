# Tasks: Cortical Column LLMs: Implementing Canonical Microcircuits for Universal Computation

**Input**: Design documents from `/specs/001-cortical-column-llms/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

**Purpose**: Project initialization and basic structure. Tasks are split into atomic steps for deterministic execution.

- [ ] T001 [P] Create directory structure: `src/models`, `src/data`, `src/training`, `src/experiments`, `src/utils`, `tests/unit`, `tests/integration`, `scripts`, `data/results`, `data/logs`, `data/configs`, `state`. **CRITICAL**: Ensure `state/*.yaml` is NOT in `.gitignore` to ensure it IS tracked and checksummed as required by Constitution Principle V (Versioning Discipline).
- [ ] T002 [P] Create `__init__.py` in every `src/` and `tests/` directory.
- [ ] T003 [P] Create `.gitignore` file excluding `data/`, `__pycache__`, `*.pyc`, `*.log`. **CRITICAL**: Explicitly include `!data/configs/` and `!data/results/` to ensure experiment metadata and results are tracked for Constitution Principle IV (Single Source of Truth).
- [X] T004 [P] Verify Setup: Run a script to confirm all directories from T001 exist and `state/template.yaml` is present. **Output**: Exit 0 if all present, exit 1 otherwise. **CRITICAL**: This task must pass before Phase 2 starts.
- [X] T005 Initialize Python 3.11 project with `pyproject.toml` and `requirements.txt` (PyTorch CPU-only, numpy, scipy, pytest, psutil).
- [X] T006a [P] Create `ruff.toml` configuration file with strict rules for linting as per project standards.
- [X] T006b [P] Create `pyproject.toml` or `black.toml` configuration for formatting as per project standards.
- [X] T007 [P] Configure `tests/conftest.py` with `pytest-timeout` settings for unit tests and resource monitoring hooks.
- [X] T007b [P] Implement `tests/conftest.py` hooks using `psutil` to assert RSS memory < 7GB and core pinning (via `os.sched_getaffinity` or `taskset` integration) during test execution. This satisfies FR-004 and SC-005 by enforcing resource constraints directly in the Python test harness.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**Note**: Only T008 (Baseline) and T010 (Homeostasis utilities) are truly foundational. Microcircuit logic (T009) is moved to Phase 4 but static E/I logic (T009c) is foundational for T010c.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008a [P] Implement `src/data/benchmarks.py` for synthetic function generation (Lorenz attractor, Fourier series, polynomial surfaces) with deterministic seeding. **CRITICAL**: Implement distinct generator functions `generate_training_data()` (Lorenz) and `generate_test_data()` (Polynomials/Fourier) to ensure independent distributions for US1 and prevent data leakage.
- [X] T008b [P] Implement `src/data/benchmarks.py::verify_independence` function. **Signature**: `def verify_independence(train_data: np.ndarray, test_data: np.ndarray) -> bool`. **Logic**: Perform Kolmogorov-Smirnov (KS) test. **Requirement**: If `p_value < 0.05`, distributions are statistically different (independent). If `p_value >= 0.05`, raise `ValueError` with message "Data distributions are not statistically independent (too similar)". Also check that mean/variance differ significantly: `abs(mean1 - mean2) / mean1 > 0.10`. **Output**: Return `True` if distributions are distinct; otherwise raise `ValueError`. **CRITICAL**: This function satisfies Constitution Principle VII and FR-006 by ensuring the test set is from a different manifold than the training set.
- [X] T009 [P] Implement `src/models/baseline_transformer.py` (standard Transformer MLP/Attention layers).
- [X] T010a [P] Implement core homeostatic scaling logic in `src/training/homeostasis.py`: define `scale_weights(model, target_ratio, decay_rate)` function that applies synaptic scaling to maintain E/I ratio. Use formula: `scale_factor = target_activity / current_activity`. Returns a dict of applied scaling factors. Explicitly derive `target_activity` from the E/I ratio constraint.
- [X] T010b [P] Implement gradient norm logging in `src/training/homeostasis.py`: define `log_gradient_norms(model, step)` function that computes and appends gradient norms to `data/logs/gradient_norms.json` for SC-002 verification.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Transformer Training and Validation (Priority: P1) 🎯 MVP

**Goal**: Establish a computationally universal baseline using a standard Transformer on synthetic tasks to serve as the control.

**Independent Test**: Execute training on held-out synthetic functions (Lorenz, Fourier) and verify MAE < 0.05 within 6 hours on 4 CPU cores.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Integration test for baseline training pipeline in `tests/integration/test_baseline_training.py`.
- [ ] T011b [US1] Integration test in `tests/integration/test_baseline_training.py` that explicitly runs the baseline model with `log_gradient_norms` enabled to populate `data/logs/gradient_norms.json` for SC-002 verification. **DEPENDS ON T010b**.
- [ ] T031 [US1] Statistical test for gradient stability in `tests/integration/test_gradient_stability.py`. **Logic**: Compare gradient norms from `data/logs/gradient_norms.json` (Baseline) against a reference distribution (or self-consistency check if only baseline exists). **Output**: `data/results/gradient_stability_baseline.json` with schema `{"mean_norm": float, "std_norm": float, "is_stable": bool}`. **DEPENDS ON T011b**. **CRITICAL**: This task ensures US1 can be independently tested for SC-002 without waiting for US2.

### Implementation for User Story 1

- [X] T012 [US1] Implement `src/training/trainer.py` with CPU-optimized loop, gradient clipping (max norm), resource monitoring (psutil), and logic to calculate Mean Absolute Error (MAE). (Uses `pytest-timeout` for enforcement).
- [X] T013 [US1] Create `scripts/run_baseline.sh` to orchestrate baseline training on Lorenz (train) and Polynomials (test), explicitly invoking `/usr/bin/time -v` to verify -hour time limit and GB RAM threshold as per FR-004.
- [X] T013c [US1] Update `scripts/run_baseline.sh` to explicitly call `generate_training_data()` for training and `generate_test_data()` for testing, ensuring the distinct data paths defined in T008 are used to prevent leakage.
- [X] T013b [US1] Implement `scripts/verify_resources.sh` to parse output of `/usr/bin/time -v` and `taskset -c 0-3`. Use `grep -E...` to verify pinning and assert RSS memory < 7GB, exiting with error if constraints violated.
- [X] T014 [US1] Create `src/experiments/baseline_runner.py` to manage experiment configuration and logging.
- [ ] T015 [US1] Implement `src/experiments/baseline_runner.py::run_and_record_metrics` to calculate and store `data/results/baseline_metrics.json`. **Logic**: Run baseline on training set (Lorenz) and test set (Polynomials). Calculate `train_mae` (float, 4 decimal places) and `test_mae` (float, 4 decimal places). Calculate `degradation_pct = ((test_mae - train_mae) / train_mae) * 100` if `train_mae > 0`, else `0.0`. **Constraint Check**: If `train_mae == 0.0`, set `degradation_pct = 0.0`. **Output**: JSON file at `data/results/baseline_metrics.json` with schema `{"train_mae": float, "test_mae": float, "degradation_pct": float, "passed": bool}`. **Logic for `passed`**: Set `passed` to `true` if `degradation_pct < 10.0`, else `false`. **DEPENDS ON T012, T009, T013c**. **CRITICAL**: This task must successfully generate the artifact to satisfy SC-001 and US-001 acceptance scenario 2, recording the failure state in the `passed` field rather than raising an exception.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Microcircuit Module Implementation and Integration (Priority: P1)

**Goal**: Implement a parameterized "Cortical Column" module mimicking laminar structure with local E/I loops and homeostatic scaling.

**Independent Test**: Instantiate module, verify connectivity matrix matches laminar topology, and confirm forward pass works on CPU.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for connectivity matrix in `tests/unit/test_microcircuit.py` (verify L4->L2/3 excitatory, etc.)
- [X] T017 [P] [US2] Unit test for E/I ratio enforcement in `tests/unit/test_microcircuit.py` (verify a forward/backward ratio during forward/backward)
- [ ] T011c [US2] Integration test in `tests/integration/test_microcircuit_training.py` that explicitly runs the microcircuit model with `log_gradient_norms` enabled to populate `data/logs/gradient_norms_microcircuit.json` for SC-002 verification. **DEPENDS ON T010b, T011d**. <!-- FAILED: unspecified -->

### Implementation for User Story 2

- [X] T009a [US2] Implement `src/models/microcircuit.py` layer definitions by creating classes `L23Layer`, `L4Layer`, `L5Layer`, `L6Layer` as separate `nn.Module` sub-layers. **CRITICAL**: Each class MUST inherit from `torch.nn.Module` and implement `forward(self, x)`.
- [X] T009b [US2] Implement `src/models/microcircuit.py` connectivity mask generation logic to enforce L4->L2/3 excitatory and other laminar connections. **DEPENDS ON T009a**.
- [X] T009c [US2] Implement `src/models/microcircuit.py` E/I ratio enforcement logic (targeting a dominant excitatory component) by **static initialization** in `__init__`. **Logic**: Initialize weights such that the ratio of excitatory to inhibitory parameters reflects a predominant excitatory balance. Apply weight clipping to enforce a symmetric bounded range. **NOTE**: This task ONLY handles static initialization; dynamic maintenance is handled by T010c. **DEPENDS ON T009a and T009b**.
- [ ] T010c [US2] Implement dynamic E/I ratio enforcement mechanism in `src/training/homeostasis.py`: define `enforce_ei_ratio(model, step, target_ratio=4.0)` function. **Signature**: `def enforce_ei_ratio(model: torch.nn.Module, step: int, target_ratio: float = 4.0) -> dict`. **Logic**: Calculate mean excitatory and inhibitory activity per epoch; compute scaling factor to force `mean_exc / mean_inh = target_ratio`; apply to weights. **Constraint**: The scaling factor MUST be bounded within a reasonable positive range. to ensure the ratio never drifts from 4:1. **Trigger**: Apply at the end of each epoch. **Output**: Append scaling factors to `data/logs/ei_ratio_log.json` with schema `{"step": int, "exc_activity": float, "inh_activity": float, "scaling_factor": float}`. **DEPENDS ON T010a, T009c**.
- [ ] T018a [US2] Implement homeostatic scaling integration in `src/training/homeostasis.py`: add `apply_scaling_hook(optimizer, step)` that calls `scale_weights` (from T010a) and `enforce_ei_ratio` (from T010c) after each optimizer step and logs factors. **DEPENDS ON T010a, T010c, T009c**.
- [ ] T019 [US2] Implement `src/models/hybrid_network.py` to replace standard MLP layers with `MicrocircuitModule` while maintaining parameter count parity (±1%). **Logic**: Instantiate `MicrocircuitModule` with same hidden dimensions as the standard MLP it replaces. Add logic to count parameters and assert `abs(total_params - baseline_params) / baseline_params < 0.01`. **Output**: A runnable model class `HybridTransformer`. **DEPENDS ON T009c, T010c**.
- [X] T020 [US2] Add weight clipping logic in `src/models/microcircuit.py` to enforce a normalized range during initialization.
- [X] T021 [US2] Implement `src/experiments/microcircuit_runner.py` to train hybrid model on same synthetic tasks as baseline.
- [X] T022 [US2] Add `tests/unit/test_hybrid_network.py::test_forward_pass_cpu` that instantiates the model and asserts no shape mismatches.
- [ ] T011d [US2] Implement `src/experiments/microcircuit_runner.py::run_with_logging` to train the microcircuit model and explicitly call `log_gradient_norms` to produce `data/logs/gradient_norms_microcircuit.json`. **DEPENDS ON T012, T019, T010b**. **CRITICAL**: This task produces the missing artifact required for T011c and T032b.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Ablation and Scaling Law Analysis (Priority: P2)

**Goal**: Run systematic ablation study and scaling analysis to quantify "cost of biological plausibility" and identify scaling exponents.

**Independent Test**: Train ablation variants (no recurrence, no inhibition) and scaling variants (multiple column configurations), compare errors and training times.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Statistical test for ablation impact in `tests/integration/test_ablation_stats.py` (t-test for p < 0.05)
- [X] T024 [P] [US3] Scaling law regression test in `tests/integration/test_scaling_laws.py`

### Implementation for User Story 3

- [ ] T025a [P] [US3] Implement `src/experiments/ablation.py::generate_ablation_configs` to create configuration objects for three variants: `full`, `no_recurrence`, `no_inhibition` and output to `data/configs/ablation_configs.json`. **Logic**: Define a dictionary of boolean flags for each variant: `{"remove_recurrence": bool, "remove_inhibition": bool}`. **Output**: `data/configs/ablation_configs.json` with schema `{"variants": [{"name": str, "flags": {"remove_recurrence": bool, "remove_inhibition": bool}}]}`. **CRITICAL**: This task must generate the config file to enable FR-003. Note: `remove_homeostasis` is excluded as per FR-003 focus on structural motifs.
- [ ] T025b [US3] Implement `src/experiments/ablation.py::run_ablation_study` to orchestrate training of ALL THREE variants defined in T025a and aggregate results into `data/results/ablation_results.json`. **Logic**: Loop through configs in `ablation_configs.json`, train each model (using same seed and data split for pairing), calculate MAE, and store results. **Output**: `data/results/ablation_results.json` with schema `{"results": [{"variant": str, "mae": float, "time": float, "seed": int}]}`. **DEPENDS ON T025a, T012**.
- [ ] T026 [US3] Implement `src/experiments/scaling.py` to vary column count (2x, 4x). **Logic**: Define base configuration (hidden_dim=64, neurons_per_layer=128). Generate x and multiple variants by doubling `neurons_per_layer`. Train each variant on the standard task. **Output**: `data/results/scaling_results.json` with schema `{"variants": [{"columns": str, "params": int, "mae": float, "time": float}]}`. **CRITICAL**: This task must generate the results file to enable FR-008 and SC-004.
- [X] T027 [US3] Implement `src/utils/statistics.py` to perform two-sample t-tests and calculate scaling exponents.
- [ ] T028 [US3] Create `src/utils/report_generator.py::generate_cost_curve_data` to generate the raw data for the "cost of biological plausibility" curve (MAE vs. number of active biological constraints) and output to `data/results/cost_curve.json`. **Logic**: Map boolean flags from T025a to a "degree" metric (count of active constraints). **Schema**: `{"constraints": [{"name": str, "degree": int, "mae": float, "time": float}]}`. **Constraint**: Must include verification step to ensure degree mapping is correct. **Output**: JSON file only. **DEPENDS ON T025b, T026, T015**. **CRITICAL**: This task produces the data source for the visualization.
- [ ] T028b [US3] Create `src/utils/report_generator.py::generate_cost_curve_viz` to generate the actual visual "curve" (PNG/SVG) and a narrative summary text file `data/results/cost_curve_summary.txt`. **Logic**: Read `data/results/cost_curve.json`, plot MAE vs. Degree, save as PNG, and write a narrative describing the trade-off. **Output**: `data/results/cost_curve.png` and `data/results/cost_curve_summary.txt`. **DEPENDS ON T028**. **CRITICAL**: This task satisfies FR-005's requirement for a visual curve deliverable. **NOTE**: This task (T028b) replaces the previously referenced T029b in draft plans; if T028 (data generation) fails or the file `data/results/cost_curve.json` is missing, this task MUST skip visualization and log a warning "Skipping visualization: cost_curve.json not found", ensuring executability even if upstream data generation fails. **Note**: If T028 fails, skip this task.
- [ ] T030 [US3] Implement `src/utils/statistics.py::compare_ablation_results` to compute the difference in MAE between full and ablated models using a paired t-test. **Input**: `data/results/ablation_results.json` (must contain same seed/split for pairing). **Logic**: Calculate `mae_diff = ablated_mae - full_mae`. Check `p_value < 0.05` AND `mae_diff / full_mae > 0.15` (relative increase > 15%). **Constraint**: If `p_value >= 0.05` OR `relative_increase <= 0.15`, **RAISE AN EXCEPTION** to fail the verification step, preserving the 'must show' requirement. **Output**: `data/results/ablation_stats.json` with schema `{"full_mae": float, "ablated_mae": float, "mae_diff": float, "p_value": float, "significant": bool}`. **CRITICAL**: This task must verify both statistical significance AND effect size to satisfy FR-003/SC-003.
- [ ] T029 [US3] Create `tests/integration/test_ablation_stats.py::test_ablation_verification` that consumes T030 results to verify the JSON schema and data integrity.
- [ ] T032b [US3] Implement `src/utils/statistics.py::compare_gradient_stability` to perform a Kolmogorov-Smirnov test between baseline gradient norms (from T011b) and microcircuit gradient norms (from T011d). **Input**: `data/logs/gradient_norms.json`, `data/logs/gradient_norms_microcircuit.json`. **Output**: `data/results/gradient_stability.json` with schema `{"ks_statistic": float, "p_value": float, "stable": bool}`. **CRITICAL**: This is the definitive verification for SC-002 comparing US1 and US2. **DEPENDS ON T011b, T011d**. **Note**: Moved from Phase 3 to Phase 5 to align with data dependencies (US1 and US2 completion) for the *comparison* task, while T031 (Phase 3) handles baseline-only stability.
- [ ] T039 [US3] Implement `src/utils/scaling_analyzer.py` to fit a power-law model to the performance data from T026 (1x, 2x, 4x variants) and output the exponent with confidence intervals to `data/results/scaling_exponent.json`. **Logic**: Fit `log(MAE) = exponent * log(Parameters) + intercept`. **Base Config**: 1x = 64 hidden/128 neurons, 2x = 128 hidden/256 neurons, 4x = 256 hidden/512 neurons. **Output**: `{"exponent": float, "confidence_interval": [float, float], "linear_or_sublinear": str}`. **CRITICAL**: Must determine if exponent < 1 (sublinear) or >= 1 (linear).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reviewer Response - Scaling Laws (Geoffrey West)

**Goal**: Address Geoffrey West's concern regarding scaling exponents and metabolic cost by explicitly measuring and reporting the scaling law.

### Implementation

- [ ] T049 [US3] Extend `src/experiments/scaling.py` to ensure at least 3 distinct column counts (1x, 2x, 4x) are tested to robustly fit a power law, ensuring the largest variant (4x) fits within the specified CPU time limit.
- [ ] T050 [US3] Update `src/utils/scaling_analyzer.py` to explicitly calculate and report the "scaling exponent" (slope of log(MAE) vs log(Parameters)) and interpret it as "linear" (exponent >= 1.0) or "sublinear" (exponent < 1.0) in the output JSON. **Constraint**: Must assert `exponent < 1.0` or `exponent >= 1.0` and set `linear_or_sublinear` field accordingly. **Output**: Update `data/results/scaling_exponent.json` with `linear_or_sublinear` string. **DEPENDS ON T039**.
- [ ] T051 [US3] Create `src/utils/report_generator.py::generate_scaling_summary` to produce a human-readable summary of the scaling law (e.g., "Doubling columns reduces error by X%") for inclusion in the final report, directly addressing the "bartender" test. **DEPENDS ON T050, T052**.
- [ ] T052 [US3] Implement `src/utils/report_generator.py::generate_scaling_fallback` to produce a "bartender test" summary if T026 (scaling experiment) fails. **Logic**: If `data/results/scaling_results.json` is missing, generate a summary stating "Scaling experiment data missing; unable to compute exponent. Fallback: Theoretical scaling analysis suggests..." (based on plan.md assumptions). **Output**: `data/results/scaling_summary_fallback.txt`. **DEPENDS ON T026 (optional)**. **CRITICAL**: Ensures narrative generation even if data is missing.

---

## Phase 7: Verification of Canonical Structure (Replaces Rule Space Search)

**Goal**: Address Constitution Principle VI (Biological Constraint Fidelity) by verifying the implemented microcircuit strictly adheres to the specific L2/3, L4, L5, L6 topology and E/I loops, rather than searching for one.

### Implementation

- [ ] T069 [US2] Implement `src/utils/structure_verifier.py::verify_canonical_topology` to load the trained `MicrocircuitModule` and verify its connectivity matrix matches the specific laminar structure defined in FR-001 (L4->L2/3 excitatory, etc.). **Logic**: Load weights, compute connectivity masks, assert exact match to spec. **Output**: `data/results/structure_verification.json` with schema `{"is_canonical": bool, "details": dict}`. **CRITICAL**: This task replaces the Rule Space Search and ensures the project implements the *specific* architecture required by FR-001.

**Checkpoint**: Canonical structure verified; no further architectural search required.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040a [P] Update `docs/quickstart.md` with instructions for running baseline and microcircuit experiments.
- [ ] T040b [P] Update `docs/quickstart.md` with instructions for running ablation, scaling, and verification experiments.
- [ ] T041 Code cleanup and refactoring of `src/models/` to ensure clear separation of concerns
- [ ] T042 [P] Add comprehensive logging for all experiment runs (seed, params, metrics, wall-time)
- [ ] T043a [P] Ensure `scripts/hash_artifacts.sh` is functional and updates `state/` YAML files with SHA256 hashes of `data/` and `code/` artifacts.
- [ ] T043b [P] Integrate `scripts/hash_artifacts.sh` into the CI/build pipeline (e.g., GitHub Actions `on: push`) to enforce versioning discipline as a gate, and add a verification step to confirm `state/` files are updated.
- [ ] T044 Validate `plan.md` constraints (CPU time, RAM) are met in all integration tests
- [ ] T045 [P] Implement `src/utils/report_generator.py::generate_final_summary` to consolidate scaling, ablation, verification, and experimental results into a single narrative for the final report, addressing the "cost of biological plausibility", scaling law findings, stability analysis, and the "canonical structure" verification.
- [ ] T045b [P] Final review of `research.md` to ensure all reviewer comments (West) are addressed with data.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - Note: T009 (Baseline) and T010 (Homeostasis utilities) are in Phase 2.
 - Note: T009a, T009b, T009c (Microcircuit) are now in Phase 4.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Reviewer Responses (Phase 6 & 7)**: Depend on Phase 5 completion (requires scaling and ablation infrastructure).
- **Polish (Final Phase)**: Depends on all desired user stories and reviewer responses being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - T011b (Test) ensures baseline gradient logging for SC-002. **DEPENDS ON T010b**.
 - T015 (Implementation) ensures baseline metrics generation. **DEPENDS ON T012, T009, T013c**.
 - T031 (Test) ensures baseline stability. **DEPENDS ON T011b**.
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
 - T011c (Test) is now part of Phase 4 to ensure testability during implementation.
 - T022 (Test) is now part of Phase 4 to ensure testability during implementation.
 - T011d (Implementation) produces gradient logs for T032b.
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
 - T029, T030 (Tests) are now part of Phase 5 to ensure testability during implementation.
- **Scaling Analysis (T039)**: Depends on T026 (Scaling Experiment) completion.
- **Scaling Feasibility (T049)**: Depends on T026 completion.
- **Phase 6 (Scaling refinement)** and **Phase 7 (Structure Verification)** can proceed in parallel once US3 infrastructure is stable.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T009, T010a, T010b) can run in parallel (within Phase 2)
 - T010c is NOT parallel (depends on T010a).
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
 - T011b, T011c, T031 (Phase 3), T032b (Phase 5) are NOT parallel (depend on implementation).
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Phase 6 (Scaling refinement) and Phase 7 (Structure Verification) can proceed in parallel once US3 infrastructure is stable.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Integration test for baseline training pipeline in tests/integration/test_baseline_training.py"

# Launch all models for User Story 1 together:
Task: "Implement src/training/trainer.py with CPU-optimized loop"
Task: "Create src/experiments/baseline_runner.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (T015, T011b, T031)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently (T015, T011b, T031) → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently (T022, T011d) → Deploy/Demo
4. Add User Story 3 → Test independently (T029, T030, T032b) → Deploy/Demo
5. Add Scaling Analysis (T039) → Quantify scaling exponent
6. Add Reviewer Responses (Phase 6 & 7) → Address West (Scaling), and verify Canonical Structure (T069).
7. Add Polish (Phase N) → Finalize documentation and artifacts
8. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Baseline) + T015, T011b, T031
 - Developer B: User Story 2 (Microcircuit) + T011c, T022, T011d
 - Developer C: User Story 3 (Ablation/Scaling) + T029, T030, T032b
3. Once US3 is stable:
 - Developer D: Scaling Analysis (T039) and Feasibility (T049)
 - Developer E: Structure Verification (T069)
4. Stories complete and integrate independently
5. No unapproved scope creep; all tasks address explicit reviewer feedback.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: Ensure all data generation is deterministic and checksummed (Constitution Principle III)
- **Critical**: Ensure all training runs respect CPU/RAM limits (FR-004) via `/usr/bin/time -v` in T013 and T013b
- **Critical**: Ensure homeostatic scaling maintains a dynamic ratio (FR-002) via T010c
- **Critical**: T015 now records degradation metrics and sets 'passed' flag to false if degradation >= 10% to satisfy FR-004, without raising an exception.
- **Critical**: T030 now verifies statistical results without enforcing a specific effect size.
- **Critical**: T030 explicitly defines the JSON schema for communication AND includes effect size check (> 15%) and RAISES EXCEPTION if conditions not met.
- **Critical**: T009 atomized into T009a, T009b, T009c for independent testability, but sequential.
- **Critical**: T039 (Scaling Analyzer) now operates only on 1x/2x/4x variants as per FR-008.
- **Critical**: Phase 6 added specifically to address Geoffrey West (Scaling Laws) reviewer concerns.
- **Critical**: T050-T052 ensure the scaling exponent is explicitly calculated and reported in human-readable terms, including fallback if data missing.
- **Critical**: T013b and T049 ensure resource constraints are verified before full execution.
- **Critical**: T043b ensures versioning discipline is enforced in CI.
- **Critical**: T025a now excludes 'remove_homeostasis' to satisfy FR-003 (structural focus) and links to FR-005.
- **Critical**: T032b ensures SC-002 is measurable by comparing gradient distributions (Baseline vs. Microcircuit) and is the definitive verifier for US3.
- **Critical**: T001 split into T001 (src), T002 (data), T003 (tests) for atomization and clarity.
- **Critical**: T028 corrected to output JSON only (data), and T028b added for visualization with skip logic.
- **Critical**: T013c added to ensure distinct data paths for training/test to prevent leakage.
- **Critical**: T033 removed; merged into T032b to avoid redundancy.
- **Critical**: Phase 7 (Rule Space Search) removed as it violated Constitution Principle VI. Replaced with T069 (Structure Verification).
- **Critical**: T069 implements verification of the specific canonical structure.
- **Critical**: T009 moved from Phase 2 to Phase 4 to remove false dependency blocking US1.
- **Critical**: T031 moved from Phase 5 to Phase 3 to allow US1 independence.
- **Critical**: T010c removed [P] tag, moved to Phase 4, and added dependency on T009c.
- **Critical**: T011c added to provide the missing dependency for T032b.
- **Critical**: T008 split into T008a (gen) and T008b (verify) with explicit p-value thresholds for divergence.
- **Critical**: T007b added to implement psutil hooks in conftest.py.
- **Critical**: T045 updated to include findings in the final summary.
- **Critical**: T001 split into T001 (src), T002 (data), T003 (tests).
- **Critical**: T011c moved to Phase 4 to resolve dependency on US2 implementation.
- **Critical**: T015 updated with explicit DEPENDS ON T012, T009, T013c.
- **Critical**: T010c, T018a, T019 updated with explicit DEPENDS ON T010a.
- **Critical**: T028 updated with explicit DEPENDS ON T015.
- **Critical**: T025a updated with exact flag names (removed homeostasis).
- **Critical**: T028 updated with degree mapping logic.
- **Critical**: T009a updated with explicit class names.
- **Critical**: T008b updated with exact signature, exception message, and divergence logic.
- **Critical**: T010c updated with exact signature and schema.
- **Critical**: T015 updated with exact schema, types, and constraint check (passed flag, no exception).
- **Critical**: T025a updated with exact flag names.
- **Critical**: T028 updated with exact schema and types.
- **Critical**: T032b updated with exact schema, path, and precision.
- **Critical**: T050 updated with linearity check.
- **Critical**: T010c updated with continuous verification and bounded scaling.
- **Critical**: T030 updated with effect size check and exception on failure.
- **Critical**: T039 and T050 updated with exact calculation logic.
- **Critical**: Phase 7 (Rule Space Search) removed; T069 (Structure Verification) added to address Constitution Principle VI.
- **Critical**: T011d added to produce `data/logs/gradient_norms_microcircuit.json`.
- **Critical**: T025c added to ensure ablation config generation.
- **Critical**: T052 added to provide fallback for scaling summary.
- **Critical**: T003 updated to explicitly exclude `data/` except `data/configs/` and `data/results/`.
- **Critical**: Phase 8 (T080-T084) removed entirely as it was scope creep and violated Constitution Principle VI.
- **Critical**: T028b updated with explicit skip logic for missing data file to resolve executability concern [executability-d7622288].
- **Critical**: T029b (phantom task) removed; T028b is the correct visualization task.
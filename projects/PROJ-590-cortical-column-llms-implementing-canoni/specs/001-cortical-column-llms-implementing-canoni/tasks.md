# Tasks: Cortical Column LLMs: Implementing Canonical Microcircuits for Universal Computation

**Input**: Design documents from `/specs/001-cortical-column-llms/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [X] T001 [P] Initialize Project Structure: Execute `mkdir -p data data/results data/logs data/configs state src src/models src/data src/training src/experiments src/utils tests/unit tests/integration scripts`. Create `__init__.py` in every `src/` and `tests/` directory. Create `.gitignore` excluding `data/` (except `data/configs/`, `data/results/`, `data/logs/`) and `__pycache__`, `*.pyc`, `*.log`. **CRITICAL**: Ensure `state/*.yaml` is tracked and checksummed as required by Constitution Principle V. Create `requirements.txt` including `torch==2.3.0+cpu` (install via `--index-url https://download.pytorch.org/whl/cpu`), `numpy`, `scipy`, `pytest`, `pytest-timeout`, `psutil`, `scikit-learn`. **CRITICAL**: `pytest-timeout` and `psutil` are required for resource monitoring in T007b and T005.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**Note**: T009 (Baseline) and T010 (Homeostasis utilities) are now in phase 4.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003b [P] Implement `scripts/hash_artifacts.sh` and `src/utils/checksum.py` to generate and record SHA256 checksums for all files in `data/configs/`, `data/results/`, `data/logs/`, and `state/`. **CRITICAL**: This task is a MANDATORY prerequisite for any data generation task to satisfy Constitution Principle III (Data Hygiene) and Principle V (Versioning Discipline). **Dependency**: Requires T001 to have completed successfully to ensure `data/` directory exists.
- [X] T004 [P] Verify Setup: Run a script to confirm all directories from T001 exist and `state/template.yaml` is present. **Output**: Exit 0 if all present, exit 1 otherwise. **CRITICAL**: This task must pass before Phase 2 starts.
- [X] T005 [P] Configure `tests/conftest.py` with `pytest-timeout` settings for unit tests and resource monitoring hooks. **CRITICAL**: Requires `pytest-timeout` installed in T001.
- [X] T007b [P] Implement `tests/conftest.py` hooks using `psutil.Process.cpu_affinity()` to assert RSS memory < 7GB and core pinning (via `psutil`) during test execution. **CRITICAL**: `psutil` must be installed (see T001). This satisfies FR-004 and SC-005 by enforcing resource constraints directly in the Python test harness.
- [X] T008a [P] Implement `src/data/benchmarks.py` for synthetic function generation (Lorenz attractor, Fourier series, polynomial surfaces) with deterministic seeding. **CRITICAL**: Implement distinct generator functions `generate_training_data()` (Lorenz) and `generate_test_data()` (Polynomials/Fourier) to ensure independent distributions for US1 and prevent data leakage.
- [ ] T008c [P] Implement `src/data/benchmarks.py::generate_polynomial_test_data` to generate independent test data for ablation/generalization metrics. **Output**: `data/results/test_data_polynomial.npy`. **CRITICAL**: Use **3rd-order polynomials** with **5 input variables** over domain **[-1, 1]**, generating **N=5000** samples. The function must write a `.npy` file containing the generated data. **Dependency**: T003b.
- [X] T008b [P] Implement `src/data/benchmarks.py::verify_independence` function. **Signature**: `def verify_independence(train_data: np.ndarray, test_data: np.ndarray) -> bool`. **Logic**: Verify that the *generators* are distinct by construction (Lorenz vs Polynomials). **Requirement**: If generators are not distinct by design, log an error and raise an exception. **CRITICAL**: This function satisfies Constitution Principle VII and FR-006 by ensuring the test set is from a different distribution by design, not just by statistical test.
- [X] T010b [P] Implement `src/training/homeostasis.py::log_gradient_norms` to compute and append gradient norms to `data/logs/gradient_norms.json` for SC-002 verification. **Signature**: `def log_gradient_norms(model, step) -> None`. **Output**: Append a JSON object `{step: int, norms: dict}` to `data/logs/gradient_norms.json`. **CRITICAL**: This task is a prerequisite for T011b and SC-002. The JSON schema is: `{"step": integer, "norms": {"param_name": float}}`.

---

## Phase 3: User Story 1 - Baseline Transformer Training and Validation (Priority: P1) 🎯 MVP

**Goal**: Establish a computationally universal baseline using a standard Transformer on synthetic tasks to serve as the control.

**Independent Test**: Execute training on held-out synthetic functions (Lorenz, Fourier) and verify MAE < 0.05 within 6 hours on 4 CPU cores.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T011 [US1] Integration test for baseline training pipeline in `tests/integration/test_baseline_training.py`.
- [X] T011b [US1] Integration test in `tests/integration/test_gradient_norms_test.py` that explicitly runs the baseline model with `log_gradient_norms` enabled to populate `data/logs/gradient_norms.json` for SC-002 verification. **CRITICAL**: This task depends on T010b. It must assert that the file exists at the project root path (not tmp_path), contains valid JSON, and matches the schema `{step: int, norms: dict}`. **Dependencies**: T010b.
- [X] T031 [US1] Statistical test for gradient stability in `tests/integration/test_gradient_stability.py`.
- [ ] T003c [P] Execute `scripts/hash_artifacts.sh` to checksum all generated data in `data/results/` (specifically `test_data_polynomial.npy` and `training_data.npy` from T008a/b). **CRITICAL**: This task must run AFTER T008a/b and T008c to satisfy Constitution Principle III (Data Hygiene). **Dependencies**: T008a, T008b, T008c.

### Implementation for User Story 1

- [X] T009a [US1] Implement `src/models/baseline_transformer.py` (standard Transformer MLP/Attention layers).
- [ ] T012b_impl [US1] Implement CPU-optimized training loop in `src/training/trainer.py`, gradient clipping, resource monitoring and logging of MAE. **Output**: `data/logs/training_log.json`. **CRITICAL**: Explicitly log MAE and loss to `data/logs/training_log.json` and enforce resource constraints (limited RAM, limited cores) as per FR-004. **Dependency**: T008c.
- [X] T013 [US1] Create `scripts/run_baseline.sh`.
- [X] T013b [US1] Update `scripts/run_baseline.sh` to explicitly call data generation functions for training and testing.
- [X] T013c [US1] Implement `src/experiments/baseline_runner.py` to manage experiment configuration and logging.
- [X] T015 [US1] Implement `src/experiments/baseline_runner.py::run_and_record_metrics`.
- [ ] T014 [US1] Implement `src/experiments/baseline_runner.py::validate_generalization` to execute the validation on the independent test set (polynomial surfaces) as required by FR-006 and US-001 Acceptance Scenario 2. **Output**: `data/results/generalization_report.md`. **CRITICAL**: This function must load `data/results/test_data_polynomial.npy`, run the baseline model, compute MAE, and **log** the degradation percentage. If degradation >= 10%, **flag** the result as "Failed Generalization" in the report but **DO NOT raise an exception**. The report must summarize the performance regardless of the outcome to allow downstream cost curve generation. **Dependencies**: T008c, T012b_impl, T010b.

---

## Phase 4: User Story 2 - Microcircuit Module Implementation and Integration (Priority: P1)

**Goal**: Implement a parameterized "Cortical Column" module mimicking laminar structure with local E/I loops and homeostatic scaling.

- [X] T010a [P] Implement core homeostatic scaling logic in `src/training/homeostasis.py`: define `scale_weights(model, target_ratio, decay_rate)` function that applies synaptic scaling to maintain E/I ratio. Use formula: `scale_factor = target_activity / current_activity`. Returns a dict of applied scaling factors. Explicitly derive `target_activity` from the E/I ratio constraint.
- [X] T010c [P] Implement dynamic E/I ratio enforcement mechanism in `src/training/homeostasis.py`: enforce a *fixed ratio* as a *structural constraint* (fixed connectivity) that is *preserved* by homeostasis during training, NOT a dynamic per-batch target adjustment. **CRITICAL**: This task clarifies the structural nature of the ratio constraint as defined in the Plan.
- [X] T009d [US2] Implement `src/models/microcircuit.py` layer definitions by creating classes `L23Layer`, `L4Layer`, `L5Layer`, `L6Layer`.
- [X] T009f [US2] Implement `src/models/microcircuit.py` connectivity mask generation logic to enforce laminar topology.
- [ ] T069 [US2] Implement `src/utils/structure_verifier.py::verify_canonical_topology` to assert that the instantiated `MicrocircuitModule` has the exact connectivity masks for L2/3, L4, L5, L6 as defined in spec.md:FR-001 and plan.md:Project Structure. **Test**: Fail if any unexpected connections exist or if the E/I ratio deviates from 4:1 by > 5%. **Expected Masks**: L4->L2/3 (Excitatory), L2/3->L5 (Excitatory), L5->L6 (Excitatory), L2/3 Recurrent (Excitatory), L2/3->L2/3 (Inhibitory). **CRITICAL**: This task consolidates the verification logic previously split between Phase 4 and Phase 7.
- [X] T069b [US2] Implement `tests/unit/test_homeostasis.py` to assert the `scale_weights` function modifies weights to restore target activity after a noise perturbation. **Parameters**: Target activity at a specified level, tolerance within an acceptable margin of error. **CRITICAL**: This task consolidates the verification logic previously split between Phase 4 and Phase 7.
- [ ] T071_impl [US2] Implement `src/utils/statistics.py::verify_gradient_distribution` to verify the *distribution* of gradient norms (SC-002) by comparing the variance and overlap against the baseline. **Output**: `data/logs/gradient_distribution_report.md`. **CRITICAL**: This task must read `data/logs/gradient_norms.json` (from T010b), compute distribution statistics, and write a report. It is a mandatory prerequisite for the final report. **Dependencies**: T010b.
- [ ] T048a [US2] Implement `src/models/hybrid_network.py::HybridNetwork` class to instantiate the hybrid network by replacing standard Transformer MLP layers with `MicrocircuitModule`. **CRITICAL**: Ensure parameter count is within ±1% of baseline. **Dependencies**: T069.
- [ ] T048b [US2] Implement `src/utils/param_verifier.py::verify_parameter_parity` to explicitly check the parameter count of the hybrid network against the baseline. **Output**: `data/results/param_parity_check.json` with keys `baseline_params`, `hybrid_params`, `diff_percent`, `pass`. **CRITICAL**: This task is a BLOCKING prerequisite for T049. **Dependencies**: T048a, T009a.

---

## Phase 5: User Story 3 - Ablation and Scaling Law Analysis (Priority: P2)

**Goal**: Run systematic ablation study and scaling analysis to quantify "cost of biological plausibility".

- [X] T025a [US3] Implement `src/experiments/ablation.py::generate_ablation_configs`.
- [ ] T025b [US3] Implement `src/experiments/ablation.py::run_ablation_study`. **CRITICAL**: This task MUST train three distinct variants (full microcircuit, ablated recurrence, ablated inhibition) on the same dataset using the training loop from T012b_impl. **Ablation Configs**: 1) `ablated recurrence`: Zero out the L2/3->L2/3 recurrent mask. 2) `ablated inhibition`: Zero out the L2/3->L2/3 inhibitory connections. It must compute and log the validation MAE for each variant to `data/results/ablation_results.csv`. **Dependencies**: T012b_impl, T048b.
- [ ] T049 [US3] Implement `src/experiments/scaling.py` to implement a loop that trains models with column counts `[1x, 2x, 4x]` and records `parameter_count` vs `validation_mae` and `training_time`. **Constraint**: Must output `data/results/scaling_law.csv` with columns `columns, params, mae, time_sec`. **CRITICAL**: This task depends on T048b (Hybrid Network Instantiation) being complete and verified. **Dependencies**: T048b, T012b_impl.
- [ ] T050 [US3] Update `src/utils/scaling_analyzer.py` to perform a log-log linear regression on the scaling data. **Requirement**: Calculate and report the scaling exponent `beta` using the formula `log(MAE) ~ beta * log(Parameter Count)`. **Output**: Write a summary to `data/results/scaling_law_report.md` stating the metric used (MAE) and whether the exponent is linear, sublinear, or superlinear. **CRITICAL**: Explicitly state the metric used in the report to satisfy SC-004. **Dependencies**: T049.

---

## Phase 6: Cost of Biological Plausibility Analysis (Priority: P2)

**Goal**: Address FR-005 by generating the "cost of biological plausibility" curve using ablation and scaling data.

- [ ] T074 [US3] Implement `src/utils/cost_curve_generator.py::generate_cost_curve_data` to compute the "cost of biological plausibility" curve by comparing the ablated variants (recurrence, inhibition) against the full model and baseline. **Output**: `data/results/cost_curve_data.csv`. **CRITICAL**: This task must read `data/results/ablation_results.csv` (from T025b) and `data/results/scaling_law.csv` (from T049). **Cost Formula**: `Cost = (MAE_microcircuit - MAE_baseline) / MAE_baseline`. This represents the relative increase in error due to biological constraints. **Dependencies**: T025b, T049.
- [ ] T075 [US3] Update `src/utils/report_generator.py::generate_cost_curve_report` to visualize the cost curve and explicitly link it to the scaling exponent from T050. **Output**: `data/results/cost_curve_report.md`. **CRITICAL**: This task depends on T074 and T050.
- [ ] T076 [US3] Implement `src/experiments/cost_analyzer.py::compute_cost_metrics` to explicitly compute the cost curve using the ablation data generated in Phase 5 and the scaling metrics from T050. **Output**: `data/results/cost_metrics.json`. **CRITICAL**: This task ensures the cost curve is generated before the final report. **Dependencies**: T074, T050.

---

## Phase 7: Final Integration and Reporting (Priority: P3)

**Goal**: Consolidate all findings into a final report that explicitly addresses the "Cost of Biological Plausibility".

- [ ] T080 [US3] Implement `src/experiments/final_verification.py::verify_universal_approximation` to verify the microcircuit models' universal approximation capability using the *same* test harness, dataset (polynomial surfaces), and seed configuration as T014 (Baseline). **Output**: `data/results/universal_approximation_report.md`. **CRITICAL**: Explicitly state that the same test harness is used for microcircuit models as for the baseline. **Dependencies**: T014.
- [ ] T081 [US3] Implement `src/utils/report_generator.py::generate_final_report` to consolidate all findings. **Requirement**: The report MUST explicitly state the "Cost of Biological Plausibility" curve as the primary finding. **Output**: `data/results/final_report.md`. **CRITICAL**: This task depends on T080 and T075.
- [ ] T082 [US3] Implement `scripts/run_final_report.sh` to orchestrate the final verification and reporting pipeline, ensuring all dependencies (T080, T075) are met.
- [ ] T084_new [US3] Implement `src/utils/scaling_summary_generator.py::generate_scaling_summary` to produce a strictly formatted JSON summary in `data/results/scaling_summary.json`. **Requirement**: Output must be valid JSON with keys `scaling_exponent` (float), `trend_type` (string: "linear"|"sublinear"|"superlinear"), and `explanation` (string: "Doubling columns reduces error by X% but increases time by Y%"). **CRITICAL**: This replaces the subjective 'Bartender' task with a deterministic JSON schema. **Dependencies**: T050.

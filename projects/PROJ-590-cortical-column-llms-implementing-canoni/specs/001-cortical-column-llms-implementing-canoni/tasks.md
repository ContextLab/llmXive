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

- [X] T001a [P] Initialize Project Structure: Create all required directories (`src/`, `src/models/`, `src/data/`, `src/training/`, `src/experiments/`, `src/utils/`, `tests/unit/`, `tests/integration/`, `scripts/`, `data/results/`, `data/logs/`, `data/configs/`, `state/`). Create `__init__.py` in every `src/` and `tests/` directory. Create `.gitignore` excluding `data/` (except `data/configs/`, `data/results/`, `data/logs/`) and `__pycache__`, `*.pyc`, `*.log`. **CRITICAL**: Ensure `state/*.yaml` is tracked and checksummed as required by Constitution Principle V.
- [X] T001b [P] Define Dependencies: Create `requirements.txt` including `torch==2.3.0+cpu` (install via `--index-url https://download.pytorch.org/whl/cpu`), `numpy`, `scipy`, `pytest`, `pytest-timeout`, `psutil`, `scikit-learn`. **CRITICAL**: `pytest-timeout` and `psutil` are required for resource monitoring in T007b and T005.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**Note**: T009 (Baseline) and T010 (Homeostasis utilities) are now in phase 4.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003b [P] Implement `scripts/hash_artifacts.sh` and `src/utils/checksum.py` to generate and record SHA256 checksums for all files in `data/configs/`, `data/results/`, `data/logs/`, and `state/`. **CRITICAL**: This task is a MANDATORY prerequisite for any data generation task to satisfy Constitution Principle III (Data Hygiene) and Principle V (Versioning Discipline).
- [X] T004 [P] Verify Setup: Run a script to confirm all directories from T001 exist and `state/template.yaml` is present. **Output**: Exit 0 if all present, exit 1 otherwise. **CRITICAL**: This task must pass before Phase 2 starts.
- [X] T005 [P] Configure `tests/conftest.py` with `pytest-timeout` settings for unit tests and resource monitoring hooks. **CRITICAL**: Requires `pytest-timeout` installed in T001.
- [X] T007b [P] Implement `tests/conftest.py` hooks using `psutil.Process.cpu_affinity()` to assert RSS memory < 7GB and core pinning (via `psutil`) during test execution. **CRITICAL**: `psutil` must be installed (see T001). This satisfies FR-004 and SC-005 by enforcing resource constraints directly in the Python test harness.
- [X] T010b [P] Implement `src/training/homeostasis.py::log_gradient_norms` as a utility function to compute and append gradient norms to a specified JSON file. **Signature**: `def log_gradient_norms(model, step, output_file: str) -> None`. **Implementation**: 1. If `output_file` does not exist, create it as an empty list `[]`. 2. Compute L2 norms for each parameter group using `model.register_full_backward_hook`. 3. Append `{step: int, norms: {param_name: float}}` to the list. 4. Write the list back with 2-space indentation and a trailing newline. **CRITICAL**: This is a utility definition only. It must be called by specific execution tasks (T071b_exec, T071c_exec) in later phases. **Atomicity**: Use file locking or atomic write to ensure parallel safety if run concurrently.

---

## Phase 3: User Story 1 - Baseline Transformer Training and Validation (Priority: P1) 🎯 MVP

**Goal**: Establish a computationally universal baseline using a standard Transformer on synthetic tasks to serve as the control.

**Independent Test**: Execute training on held-out synthetic functions (Lorenz, Fourier) and verify MAE < 0.05 within 6 hours on 4 CPU cores.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T031 [US1] Statistical test for gradient stability in `tests/integration/test_gradient_stability.py`.
- [X] T011b [US1] Integration test in `tests/integration/test_baseline_training.py` that explicitly runs the baseline model with `log_gradient_norms` enabled to populate `data/logs/baseline_gradient_norms.json` for SC-002 verification. **CRITICAL**: This task depends on T071b_exec. It must assert that the file exists at the project root path (not tmp_path) and contains valid JSON. **Dependency**: Requires T009a (Baseline Implementation) and T011a_run (Training Execution) to be complete.

### Implementation for User Story 1

- [X] T009a [US1] Implement `src/models/baseline_transformer.py` (standard Transformer MLP/Attention layers).
- [X] T008a [P] Implement `src/data/benchmarks.py::generate_training_data` to generate training data (Lorenz attractor) with deterministic seeding. **CRITICAL**: Implement distinct generator functions `generate_training_data()` (Lorenz) to ensure independent distributions for US1 and prevent data leakage. **Output**: `data/results/train_data_lorenz.npy`. **Verification**: Run `scripts/hash_artifacts.sh` and assert exit code 0 and file `data/results/train_data_lorenz.npy` exists. **CRITICAL**: If the file does not exist or checksum fails, the task MUST exit with code 1 and report failure. Do not proceed. **Dependency**: Requires T003b (Checksum Script) to be complete.
- [ ] T008c [P] Implement `src/data/benchmarks.py::generate_polynomial_test_data` to generate independent test data for ablation/generalization metrics. **Output**: `data/results/test_data_polynomial.npy`. **CRITICAL**: Use `polynomial surfaces` as the function family (distinct from Lorenz) to ensure statistical independence by design. **Parameters**: `SEED=42`, `N=1000`, `coeffs=[1, 0, -1]` (for $x^2 - 1$). **Logic**: `X = np.random.seed(42); X = np.random.rand(N)`. `Y = np.polyval([1, 0, -1], X) + noise`. **Note**: X must be 1D for `np.polyval`. **Verification**: Run `scripts/hash_artifacts.sh` and assert exit code 0 and file `data/results/test_data_polynomial.npy` exists. **CRITICAL**: If the file does not exist or checksum fails, the task MUST exit with code 1 and report failure. Do not proceed.
- [X] T008b [P] Implement `src/data/benchmarks.py::verify_independence` function. **Signature**: `def verify_independence(train_data: np.ndarray, test_data: np.ndarray) -> bool`. **Logic**: 1. Verify generators are distinct by design (Lorenz vs Polynomials). 2. Perform a Kolmogorov-Smirnov test on the generated samples to ensure statistical independence (p-value < 0.05). **Requirement**: If generators are not distinct or samples are statistically dependent, log an error and raise an exception. **CRITICAL**: This function satisfies Constitution Principle VII and FR-006 by ensuring the test set is from a different distribution by design AND by statistical verification. **Dependency**: Requires T008a and T008c to be complete. **Note**: T008b must pass before Phase 3 begins.
- [X] T012b_impl [US1] Implement CPU-optimized training loop in `src/training/trainer.py`, gradient clipping, resource monitoring and logging of MAE. **Output**: `data/logs/training_log.json`. **CRITICAL**: Explicitly log MAE and loss to `data/logs/training_log.json` and enforce resource constraints (limited RAM, limited cores) as per FR-004.
- [X] T011a_run [US1] Implement `src/experiments/baseline_runner.py::run_baseline_training` to execute the training loop defined in T012b_impl. **CRITICAL**: This task runs the actual training. It depends on T009a and T012b_impl. **Output**: Trained model weights in `data/models/baseline.pt`.
- [X] T013 [US1] Create `scripts/run_baseline.sh`.
- [X] T013b [US1] Update `scripts/run_baseline.sh` to explicitly call data generation functions for training and testing.
- [X] T013c [US1] Implement `src/experiments/baseline_runner.py` to manage experiment configuration and logging.
- [X] T015 [US1] Implement `src/experiments/baseline_runner.py::run_and_record_metrics`.
- [ ] T014a [US1] Load Test Data: Implement `src/experiments/baseline_runner.py::load_test_data` to load `data/results/test_data_polynomial.npy`. **Output**: Returns `X_test`, `y_test`. **CRITICAL**: This is the first step of the atomized validation process. **Dependency**: Requires T008c and T008b (verification passed).
- [X] T014b [US1] Run Inference: Implement `src/experiments/baseline_runner.py::run_inference` to execute the trained baseline model on `X_test`. **Output**: `y_pred`. **CRITICAL**: This is the second step of the atomized validation process. **Dependency**: Requires T011a_run (trained model).
- [X] T014c [US1] Compute Metrics: Implement `src/experiments/baseline_runner.py::compute_generalization_mae` to calculate MAE between `y_test` and `y_pred`. **Output**: `mae_value`. **CRITICAL**: This is the third step of the atomized validation process.
- [X] T014d [US1] Write Report: Implement `src/experiments/baseline_runner.py::write_generalization_report` to generate `data/results/generalization_report.md` summarizing the MAE and comparing it to the training set MAE. **CRITICAL**: This is the final step of the atomized validation process, satisfying FR-006 and US-001 Acceptance Scenario 2.
- [X] T071b_exec [US1] Implement `src/experiments/baseline_gradient_extractor.py::run_baseline_gradient_extraction` to run the baseline model (T011a_run) and extract its gradient distribution using T010b. **Output**: `data/logs/baseline_gradient_norms.json`. **CRITICAL**: This task provides the baseline data required for T071a to perform the comparative analysis mandated by SC-002. **Dependency**: Requires T011a_run (trained baseline). **Action**: Invoke `log_gradient_norms(model, step, "data/logs/baseline_gradient_norms.json")` during training.

---

## Phase 4: User Story 2 - Microcircuit Module Implementation and Integration (Priority: P1)

**Goal**: Implement a parameterized "Cortical Column" module mimicking laminar structure with local E/I loops and homeostatic scaling.

- [X] T010a [P] Implement core homeostatic scaling logic in `src/training/homeostasis.py`: define `scale_weights(model, target_ratio, decay_rate)` function that applies synaptic scaling to maintain E/I ratio. Use formula: `scale_factor = target_activity / current_activity`. Returns a dict of applied scaling factors. Explicitly derive `target_activity` from the E/I ratio constraint.
- [X] T009d [US2] Implement `src/models/microcircuit.py` layer definitions by creating classes `L23Layer`, `L4Layer`, `L5Layer`, `L6Layer`.
- [X] T009f [US2] Implement `src/models/microcircuit.py` connectivity mask generation logic to enforce laminar topology.
- [X] T010c [US2] Implement dynamic E/I ratio enforcement mechanism in `src/training/homeostasis.py`: enforce the 4: ratio as a *dynamic constraint* maintained during training using ONLY homeostatic scaling. **Algorithm**: 1. Apply `scale_weights` post-backpropagation to restore target activity. 2. **CRITICAL**: The ratio must be maintained via scaling dynamics alone. Do NOT use hard masks or zero-out operations during the forward pass. 3. Update rule: `new_weight = old_weight * (target_activity / current_activity) ** decay_rate`. **CRITICAL**: This task clarifies the dynamic nature of the ratio constraint as defined in FR-002.
- [X] T048 [US2] Implement `src/models/hybrid_network.py` to instantiate the hybrid network by replacing standard Transformer MLP layers with `MicrocircuitModule`. **CRITICAL**: Verify parameter count is within ±1% of baseline and this verification is a BLOCKING prerequisite for T049 (Scaling).
- [X] T069 [US2] Implement `src/utils/structure_verifier.py::verify_canonical_topology` to assert that the instantiated `MicrocircuitModule` has the exact connectivity masks for L2/3, L4, L5, L6 as defined in the spec. **Test**: Fail if any unexpected connections exist or if the E/I ratio deviates from 4:1 by > 5%. **CRITICAL**: This task consolidates the verification logic previously split between Phase 4 and Phase 7.
- [X] T069b [US2] Implement `tests/unit/test_homeostasis.py` to assert the `scale_weights` function modifies weights to restore target activity after a noise perturbation. **Parameters**: Target activity at a specified level, tolerance within an acceptable margin of error. **CRITICAL**: This task consolidates the verification logic previously split between Phase 4 and Phase 7.
- [X] T071c_exec [US2] Implement `src/experiments/microcircuit_gradient_extractor.py::run_microcircuit_gradient_extraction` to run the microcircuit model (T048) and extract its gradient distribution using T010b. **Output**: `data/logs/microcircuit_gradient_norms.json`. **CRITICAL**: This task provides the microcircuit data required for T071a to perform the comparative analysis mandated by SC-002. **Dependency**: Requires T048 (Microcircuit Implementation). **Action**: Invoke `log_gradient_norms(model, step, "data/logs/microcircuit_gradient_norms.json")` during training.
- [X] T071a_impl [US2] Implement `src/utils/statistics.py::verify_gradient_distribution` to verify the *distribution* of gradient norms (SC-002) by comparing the variance and overlap against the baseline. **Input**: `data/logs/baseline_gradient_norms.json` (from T071b_exec) and `data/logs/microcircuit_gradient_norms.json` (from T071c_exec). **Output**: `data/logs/gradient_distribution_report.md`. **Method**: Perform a two-sample Kolmogorov-Smirnov test to compare distributions. **CRITICAL**: This task depends on T011a_run (Baseline Training) and T048 (Microcircuit Implementation) being complete.
- [X] T071a_report [US2] Implement `src/utils/report_generator.py::generate_gradient_report` to write the final report from T071a_impl. **Output**: `data/logs/gradient_distribution_report.md`. **CRITICAL**: Separates logic from reporting.

---

## Phase 5: User Story 3 - Ablation and Scaling Law Analysis (Priority: P2)

**Goal**: Run systematic ablation study and scaling analysis to quantify "cost of biological plausibility".

- [X] T025a [US3] Implement `src/experiments/ablation.py::generate_ablation_configs` to define variants (full, ablated recurrence, ablated inhibition).
- [X] T025b [US3] Implement `src/experiments/ablation.py::run_ablation_study` to train and evaluate the defined variants on the same dataset.
- [ ] T049a [US3] Implement `src/experiments/scaling.py::train_single_config` to train a single model configuration with specified column count. **Constraint**: Must output `data/results/scaling_single_{config}.json`.
- [ ] T049b [US3] Implement `src/experiments/scaling.py::run_scaling_loop` to orchestrate training for column counts `[x, 2x, 4x]`. **Constraint**: Must call T049a for each config.
- [ ] T049c [US3] Implement `src/experiments/scaling.py::write_scaling_results` to aggregate results into `data/results/scaling_law.csv` with columns `columns, params, mae, time_sec`. **Constraint**: Must include a verification step to ensure `data/results/scaling_law.csv` exists and is valid before completing. **CRITICAL**: This task depends on T048 (Hybrid Network Instantiation) being complete and verified.
- [X] T050 [US3] Update `src/utils/scaling_analyzer.py` to perform a log-log linear regression on the scaling data. **Requirement**: Calculate and report the scaling exponent `beta` using the formula `log(MAE) ~ beta * log(Parameter Count)`. **Output**: Write a summary to `data/results/scaling_law_report.md` stating the metric used (MAE) and whether the exponent is linear, sublinear, or superlinear. **CRITICAL**: Explicitly state the metric used in the report to satisfy SC-004.

---

## Phase 6: Cost of Biological Plausibility Analysis (Priority: P2)

**Goal**: Address FR-005 by generating the "cost of biological plausibility" curve using ablation and scaling data.

- [ ] T074 [US3] Implement `src/utils/cost_curve_generator.py::generate_cost_curve_data` to compute the "cost of biological plausibility" curve by comparing the ablated variants (recurrence, inhibition) against the full model and baseline. **Output**: `data/results/cost_curve_data.csv`. **Logic**: Calculate relative MAE increase and training time increase for each ablation variant. **CRITICAL**: Explicitly calculate "Metabolic Cost" as `Training Time (sec) / MAE` for each variant to quantify the trade-off.
- [X] T075 [US3] Update `src/utils/report_generator.py::generate_cost_curve_report` to visualize the cost curve and explicitly link it to the scaling exponent from T050. **Output**: `data/results/cost_curve_report.md`. **CRITICAL**: This task depends on T074 and T050. The report MUST include the "Metabolic Cost" metric (Time/MAE) as the primary measure of biological plausibility cost.
- [ ] T076 [US3] Implement `src/experiments/cost_analyzer.py::compute_cost_metrics` to explicitly compute the cost curve using the ablation data generated in Phase 5 and the scaling metrics from T050. **Output**: `data/results/cost_metrics.json`. **CRITICAL**: This task ensures the cost curve is generated before the final report.

---

## Phase 7: Interim Reporting and Universality Verification (Priority: P3)

**Goal**: Generate an interim report containing all findings up to this point, and verify the "Universal Computation" claim via Logic Gate benchmarks.

- [X] T082 [US3] Implement `src/experiments/universality_test.py::run_logic_gate_benchmark` to verify the microcircuit models' universal approximation capability on discrete functions. **Logic**: Train/evaluate the microcircuit model (T048) on a held-out set of logic gates (AND, OR, XOR) generated from synthetic binary inputs. **Output**: `data/results/universality_report.md`. **CRITICAL**: This task explicitly addresses the "Universal Computation" claim in the project title by verifying the model can compute standard logic gates, satisfying the requirement for universal approximation without requiring an exhaustive rule space search. **Dependency**: Requires T048 (Microcircuit Implementation) and T025b (Ablation Study) to be complete.
- [X] T080 [US3] Implement `src/experiments/final_verification.py::verify_universal_approximation` to verify the microcircuit models' universal approximation capability using the *same* test harness, dataset (polynomial surfaces), and seed configuration as T014 (Baseline). **Output**: `data/results/universal_approximation_report.md`. **CRITICAL**: Explicitly state that the same test harness is used for microcircuit models as for the baseline.
- [X] T081 [US3] Implement `src/utils/report_generator.py::generate_interim_report` to consolidate all findings from Phases 1-6. **Requirement**: The report MUST explicitly state the "Cost of Biological Plausibility" curve and scaling exponent. **Output**: `data/results/interim_report.md`. **CRITICAL**: This task depends on T080, T082, T075, and T050. This is NOT the final report; it is a precursor to the final synthesis.

---

## Phase 8: Final Synthesis and Reporting (Priority: P3)

**Goal**: Synthesize findings into the final report that explicitly addresses the "Cost of Biological Plausibility" and "Universal Computation".

- [X] T105 [US3] Implement `src/utils/report_generator.py::generate_final_report` to consolidate all findings including the interim report, scaling analysis, cost metrics, and universality verification. **Requirement**: The report MUST explicitly state that the "Cost of Biological Plausibility" curve is the primary finding, derived from the fixed canonical microcircuit and its ablation variants, and that the "Universal Computation" claim is verified by the Logic Gate benchmark (T082). **Output**: `data/results/final_report.md`. **CRITICAL**: This task depends on T081 (interim report), T075 (cost curve), and T082 (Universality Test). This is the FINAL report generation.
- [X] T106 [US3] Implement `scripts/run_final_report.sh` to orchestrate the final verification and reporting pipeline, ensuring all dependencies (T080, T081, T075, T082, T105) are met.
- [X] T107 [US3] Implement `tests/integration/test_final_synthesis.py` to verify that the final report contains all required answers to the spec (Cost curve, Scaling exponent, Universal approximation).
- [X] T108 [US3] Add unit test `tests/unit/test_final_report_completeness.py` to assert that the final report contains all required sections (Cost Curve, Scaling Law, Universal Approximation).

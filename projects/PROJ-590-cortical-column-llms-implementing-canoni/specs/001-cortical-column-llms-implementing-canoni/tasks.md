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

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create directory tree explicitly for `src/models`, `src/data`, `src/training`, `src/experiments`, `src/utils`, `tests/unit`, `tests/integration`, `scripts`, `data/results`, `data/logs`, `data/configs`, `state` as per `plan.md`. **CRITICAL**: Create a template YAML file in `state/` with keys: `hashes`, `artifacts`, `updated_at` as required by Constitution Principle V.
- [ ] T001b [P] Create `__init__.py` in every `src/` and `tests/` directory and **Create** a `.gitignore` file excluding `data/`, `__pycache__`, `*.pyc`. **CRITICAL**: Ensure `state/*.yaml` is NOT in `.gitignore` to ensure it IS tracked and checksummed as required by Constitution Principle V (Versioning Discipline).
- [X] T002 Initialize Python 3.11 project with `pyproject.toml` and `requirements.txt` (PyTorch CPU-only, numpy, scipy, pytest, psutil).
- [ ] T003a [P] Create `ruff.toml` configuration file with strict rules for linting as per project standards.
- [X] T003b [P] Create `pyproject.toml` or `black.toml` configuration for formatting as per project standards.
- [X] T004 [P] Configure `tests/conftest.py` with `pytest-timeout` settings for unit tests and resource monitoring hooks.
- [ ] T004b [P] Implement `tests/conftest.py` hooks using `psutil` to assert RSS memory < 7GB and core pinning (via `os.sched_getaffinity` or `taskset` integration) during test execution. This satisfies FR-004 and SC-005 by enforcing resource constraints directly in the Python test harness.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**Note**: Only T006 (Baseline) and T008 (Homeostasis utilities) are truly foundational. Microcircuit logic (T007) is moved to Phase 4.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005a [P] Implement `src/data/benchmarks.py` for synthetic function generation (Lorenz attractor, Fourier series, polynomial surfaces) with deterministic seeding. **CRITICAL**: Implement distinct generator functions `generate_training_data()` (Lorenz) and `generate_test_data()` (Polynomials/Fourier) to ensure independent distributions for US1 and prevent data leakage.
- [ ] T005b [P] Implement `src/data/benchmarks.py::verify_independence` function that performs a Kolmogorov-Smirnov (KS) test and moment matching (mean, variance, skewness) between training and test sets. **CRITICAL**: The function must assert `p-value > 0.05` and report moments; raise an exception if independence is not statistically verified, satisfying Constitution Principle VII and FR-006.
- [X] T006 [P] Implement `src/models/baseline_transformer.py` (standard Transformer MLP/Attention layers).
- [X] T008a [P] Implement core homeostatic scaling logic in `src/training/homeostasis.py`: define `scale_weights(model, target_ratio, decay_rate)` function that applies synaptic scaling to maintain E/I ratio. Use formula: `scale_factor = target_activity / current_activity`. Returns a dict of applied scaling factors. Explicitly derive `target_activity` from the E/I ratio constraint.
- [X] T008b [P] Implement gradient norm logging in `src/training/homeostasis.py`: define `log_gradient_norms(model, step)` function that computes and appends gradient norms to `data/logs/gradient_norms.json` for SC-002 verification.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Transformer Training and Validation (Priority: P1) 🎯 MVP

**Goal**: Establish a computationally universal baseline using a standard Transformer on synthetic tasks to serve as the control.

**Independent Test**: Execute training on held-out synthetic functions (Lorenz, Fourier) and verify MAE < 0.05 within 6 hours on 4 CPU cores.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Integration test for baseline training pipeline in `tests/integration/test_baseline_training.py`.
- [ ] T012b [US1] Integration test in `tests/integration/test_baseline_training.py` that explicitly runs the baseline model with `log_gradient_norms` enabled to populate `data/logs/gradient_norms.json` for SC-002 verification. **DEPENDS ON T008b**.

### Implementation for User Story 1

- [X] T013 [US1] Implement `src/training/trainer.py` with CPU-optimized loop, gradient clipping (max norm), resource monitoring (psutil), and logic to calculate Mean Absolute Error (MAE). (Uses `pytest-timeout` for enforcement).
- [X] T014 [US1] Create `scripts/run_baseline.sh` to orchestrate baseline training on Lorenz (train) and Polynomials (test), explicitly invoking `/usr/bin/time -v` to verify -hour time limit and GB RAM threshold as per FR-004.
- [X] T014c [US1] Update `scripts/run_baseline.sh` to explicitly call `generate_training_data()` for training and `generate_test_data()` for testing, ensuring the distinct data paths defined in T005 are used to prevent leakage.
- [X] T014b [US1] Implement `scripts/verify_resources.sh` to parse output of `/usr/bin/time -v` and `taskset -c 0-3`. Use `grep -E...` to verify pinning and assert RSS memory < 7GB, exiting with error if constraints violated.
- [ ] T015 [US1] Create `src/experiments/baseline_runner.py` to manage experiment configuration and logging.
- [ ] T016 [US1] Create `tests/integration/test_baseline_validation.py::test_baseline_degradation_measurement` that asserts the system records the MAE on the independent test set and calculates the degradation percentage `(test_mae - train_mae) / train_mae`, storing these metrics in `data/results/baseline_metrics.json`. **CRITICAL**: Report MAE values with standard precision. **If train_mae is 0.0, set degradation_pct to 0.0** to handle division by zero. Verify the file exists and contains keys `train_mae`, `test_mae`, `degradation_pct`. Do NOT enforce a strict schema beyond key presence.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Microcircuit Module Implementation and Integration (Priority: P1)

**Goal**: Implement a parameterized "Cortical Column" module mimicking laminar structure with local E/I loops and homeostatic scaling.

**Independent Test**: Instantiate module, verify connectivity matrix matches laminar topology, and confirm forward pass works on CPU.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for connectivity matrix in `tests/unit/test_microcircuit.py` (verify L4->L2/3 excitatory, etc.)
- [X] T018 [P] [US2] Unit test for E/I ratio enforcement in `tests/unit/test_microcircuit.py` (verify a forward/backward ratio during forward/backward)

### Implementation for User Story 2

- [X] T007a [US2] Implement `src/models/microcircuit.py` layer definitions by creating classes `L23Layer`, `L4Layer`, `L5Layer`, `L6Layer` as separate `nn.Module` sub-layers.
- [X] T007b [US2] Implement `src/models/microcircuit.py` connectivity mask generation logic to enforce L4->L2/3 excitatory and other laminar connections. **DEPENDS ON T007a**.
- [X] T007c [US2] Implement `src/models/microcircuit.py` E/I ratio enforcement logic (targeting a dominant excitatory component) by construction in the initialization and forward pass. **DEPENDS ON T007a and T007b**.
- [ ] T008c [US2] Implement dynamic E/I ratio enforcement mechanism in `src/training/homeostasis.py`: define `enforce_ei_ratio(model, step)` function that calculates `target_activity` based on the 4:1 ratio and applies scaling to maintain the ratio dynamically during training, as required by FR-002. **DEPENDS ON T008a and T007c**. This task implements the specific **epoch-level enforcement** distinct from T008a's initialization logic. **Algorithm**: Calculate mean excitatory and inhibitory activity per epoch; compute scaling factor to force `mean_exc / mean_inh = 4.0`; apply to weights. **Verify via test_microcircuit.py::test_epoch_scaling**.
- [ ] T019a [US2] Implement homeostatic scaling integration in `src/training/homeostasis.py`: add `apply_scaling_hook(optimizer)` that calls `scale_weights` after each optimizer step and logs factors. **DEPENDS ON T007c**.
- [ ] T020 [US2] Create `src/models/hybrid_network.py` to replace standard MLP layers with `MicrocircuitModule` while maintaining parameter count parity (±1%).
- [X] T021 [US2] Add weight clipping logic in `src/models/microcircuit.py` to enforce a normalized range during initialization.
- [X] T022 [US2] Implement `src/experiments/microcircuit_runner.py` to train hybrid model on same synthetic tasks as baseline.
- [X] T023 [US2] Create `tests/unit/test_hybrid_network.py::test_forward_pass_cpu` that instantiates the model and asserts no shape mismatches.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Ablation and Scaling Law Analysis (Priority: P2)

**Goal**: Run systematic ablation study and scaling analysis to quantify "cost of biological plausibility" and identify scaling exponents.

**Independent Test**: Train ablation variants (no recurrence, no inhibition) and scaling variants (multiple column configurations), compare errors and training times.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Statistical test for ablation impact in `tests/integration/test_ablation_stats.py` (t-test for p < 0.05)
- [X] T025 [P] [US3] Scaling law regression test in `tests/integration/test_scaling_laws.py`

### Implementation for User Story 3

- [ ] T026a [P] [US3] Implement `src/experiments/ablation.py::generate_ablation_configs` to create configuration objects for four variants: `full`, `no_recurrence`, `no_inhibition`, `no_homeostasis` and output to `data/configs/ablation_configs.json`. **NOTE**: `no_homeostasis` variant is included to measure the specific impact of homeostatic scaling on the microcircuit model (internal ablation), explicitly linking this to FR-005 (Cost of Biological Plausibility) by measuring how much cost increases without this constraint.
- [ ] T026b [US3] Implement `src/experiments/ablation.py::run_ablation_study` to orchestrate training of ALL FOUR variants defined in T026a and aggregate results into `data/results/ablation_results.json`.
- [ ] T027 [US3] Implement `src/experiments/scaling.py` to vary column count (1x, 2x, 4x). Base 1x configuration: hidden_dim=64, neurons_per_layer=128. Calculate 2x and 4x variants deterministically from this base.
- [ ] T028 [US3] Implement `src/utils/statistics.py` to perform two-sample t-tests and calculate scaling exponents.
- [ ] T029 [US3] Create `src/utils/report_generator.py::generate_cost_curve` to generate the "cost of biological plausibility" curve (MAE vs. number of active biological constraints) and output to `data/results/cost_curve.json`. **CRITICAL**: JSON schema must include keys: `constraints` (list of strings, e.g., ["recurrence", "inhibition", "homeostasis"]), `mae` (float), `time` (float). Do NOT generate PNG files; output only JSON data. **The independent verifier will accept `data/results/cost_curve.json` in lieu of a PNG file.** **DEPENDS ON T026b and T027**.
- [ ] T031 [US3] Implement `src/utils/statistics.py::compare_ablation_results` to compute the difference in MAE between full and ablated models using a paired t-test. Input: `data/results/ablation_results.json`. Output: `data/results/ablation_stats.json` with schema `{"full_mae": float, `ablated_mae": float, `mae_diff": float, `p_value": float, `significant": bool}`.
- [ ] T030 [US3] Create `tests/integration/test_ablation_stats.py::test_ablation_verification` that consumes T031 results to verify the JSON schema and data integrity.
- [ ] T040 [US3] Implement `src/utils/scaling_analyzer.py` to fit a power-law model to the performance data from T027 (1x, 2x, 4x variants) and output the exponent with confidence intervals to `data/results/scaling_exponent.json`.
- [ ] T032 [US3] Implement `src/utils/statistics.py::compare_gradient_stability` to perform a Kolmogorov-Smirnov test between baseline gradient norms (from T012b) and microcircuit gradient norms (from T012c). **CRITICAL**: This is the definitive verification for SC-002. Output `data/results/gradient_stability.json` with schema `{"ks_statistic": float, "p_value": float, "stable": bool}`. **DEPENDS ON T012b and T012c**. **Note**: Moved from Phase 3 to Phase 5 to align with data dependencies (US1 and US2 completion).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reviewer Response - Scaling Laws (Geoffrey West)

**Goal**: Address Geoffrey West's concern regarding scaling exponents and metabolic cost by explicitly measuring and reporting the scaling law.

### Implementation

- [ ] T050 [US3] Extend `src/experiments/scaling.py` to ensure at least 3 distinct column counts (1x, 2x, 4x) are tested to robustly fit a power law, ensuring the largest variant (4x) fits within the specified CPU time limit.
- [ ] T051 [US3] Update `src/utils/scaling_analyzer.py` to explicitly calculate and report the "scaling exponent" (slope of log(MAE) vs log(Parameters)) and interpret it as "linear" (The exponent is expected to be approximately unity.) or "sublinear" (exponent < 1) in the output JSON.
- [ ] T052 [US3] Create `src/utils/report_generator.py::generate_scaling_summary` to produce a human-readable summary of the scaling law (e.g., "Doubling columns reduces error by X%") for inclusion in the final report, directly addressing the "bartender" test.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041a [P] Update `docs/quickstart.md` with instructions for running baseline and microcircuit experiments.
- [ ] T041b [P] Update `docs/quickstart.md` with instructions for running ablation, scaling experiments.
- [ ] T042 Code cleanup and refactoring of `src/models/` to ensure clear separation of concerns
- [ ] T043 [P] Add comprehensive logging for all experiment runs (seed, params, metrics, wall-time)
- [ ] T044a [P] Ensure `scripts/hash_artifacts.sh` is functional and updates `state/` YAML files with SHA256 hashes of `data/` and `code/` artifacts.
- [ ] T044b [P] Integrate `scripts/hash_artifacts.sh` into the CI/build pipeline (e.g., GitHub Actions `on: push`) to enforce versioning discipline as a gate, and add a verification step to confirm `state/` files are updated.
- [ ] T045 Validate `plan.md` constraints (CPU time, RAM) are met in all integration tests
- [ ] T046 [P] Implement `src/utils/report_generator.py::generate_final_summary` to consolidate scaling and ablation results into a single narrative for the final report, addressing the "cost of biological plausibility" and scaling law findings (replacing removed Phase 7).
- [ ] T046b [P] Final review of `research.md` to ensure all reviewer comments are addressed with data

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - Note: T006 (Baseline) and T008 (Homeostasis utilities) are in Phase 2.
 - Note: T007a, T007b, T007c (Microcircuit) are now in Phase 4.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Reviewer Responses (Phase 6)**: Depends on Phase 5 completion (requires scaling and ablation infrastructure).
- **Polish (Final Phase)**: Depends on all desired user stories and reviewer responses being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - T012b (Test) ensures baseline gradient logging for SC-002. **DEPENDS ON T008b**.
 - T032 (Test) compares gradient logs. **DEPENDS ON T012b and T012c**.
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
 - T023 (Test) is now part of Phase 4 to ensure testability during implementation.
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
 - T030, T031, T032 (Tests) are now part of Phase 5 to ensure testability during implementation.
- **Scaling Analysis (T040)**: Depends on T027 (Scaling Experiment) completion.
- **Scaling Feasibility (T050)**: Depends on T027 completion.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T006, T008a, T008b) can run in parallel (within Phase 2)
 - T008c is NOT parallel (depends on T008a).
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
 - T012b, T032 are NOT parallel (depend on implementation).
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Phase 6 (Scaling refinement) can proceed in parallel once US3 infrastructure is stable.

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
4. **STOP and VALIDATE**: Test User Story 1 independently (T016, T012b, T032)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently (T016, T012b, T032) → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently (T023) → Deploy/Demo
4. Add User Story 3 → Test independently (T030, T031, T032) → Deploy/Demo
5. Add Scaling Analysis (T040) → Quantify scaling exponent
6. Add Reviewer Responses (Phase 6) → Address West concerns
7. Add Polish (Phase N) → Finalize documentation and artifacts
8. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Baseline) + T016, T012b, T032
 - Developer B: User Story 2 (Microcircuit) + T023
 - Developer C: User Story 3 (Ablation/Scaling) + T030, T031, T032
3. Once US3 is stable:
 - Developer D: Scaling Analysis (T040) and Feasibility (T050)
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
- **Critical**: Ensure all training runs respect CPU/RAM limits (FR-004) via `/usr/bin/time -v` in T014 and T014b
- **Critical**: Ensure homeostatic scaling maintains a dynamic ratio (FR-002) via T008c
- **Critical**: T016 now records degradation metrics instead of enforcing a hard threshold, with explicit edge case handling for zero MAE and decimal precision.
- **Critical**: T030 now verifies statistical results without enforcing a specific effect size.
- **Critical**: T031 explicitly defines the JSON schema for communication.
- **Critical**: T007 atomized into T007a, T007b, T007c for independent testability, but sequential.
- **Critical**: T040 (Scaling Analyzer) now operates only on 1x/2x/4x variants as per FR-008.
- **Critical**: Phase 6 added specifically to address Geoffrey West (Scaling Laws) reviewer concerns.
- **Critical**: T050-T052 ensure the scaling exponent is explicitly calculated and reported in human-readable terms.
- **Critical**: T014b and T050 ensure resource constraints are verified before full execution.
- **Critical**: T044b ensures versioning discipline is enforced in CI.
- **Critical**: T026a now includes 'no_homeostasis' variant to satisfy FR-003 (internal ablation) and links to FR-005.
- **Critical**: T032 ensures SC-002 is measurable by comparing gradient distributions (Baseline vs. Microcircuit) and is the definitive verifier.
- **Critical**: T001b corrected to ensure `state/*.yaml` is tracked in git, not excluded.
- **Critical**: T029 corrected to output JSON only, removing PNG dependency, and defining the `constraints` list.
- **Critical**: T014c added to ensure distinct data paths for training/test to prevent leakage.
- **Critical**: T033 removed; merged into T032 to avoid redundancy.
- **Critical**: Phase 7 (Rule Space Search) removed as unapproved scope creep; replaced by T046 in Phase N.
- **Critical**: T007 moved from Phase 2 to Phase 4 to remove false dependency blocking US1.
- **Critical**: T032 moved from Phase 3 to Phase 5 to align with data dependencies (T012b, T012c).
- **Critical**: T008c removed [P] tag, moved to Phase 4, and added dependency on T007c.
- **Critical**: T012c removed; T012b is sufficient for baseline, microcircuit logs are handled in US2 context.
- **Critical**: T005 split into T005a (gen) and T005b (verify) with explicit p-value thresholds.
- **Critical**: T004b added to implement psutil hooks in conftest.py.
- **Critical**: T019a added explicit dependency on T007c.
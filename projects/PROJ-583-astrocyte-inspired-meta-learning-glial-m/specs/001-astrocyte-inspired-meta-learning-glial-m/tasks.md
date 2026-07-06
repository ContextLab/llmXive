# Tasks: Astrocyte-Inspired Meta-Learning: Glial Modulation of Neural Networks

**Input**: Design documents from `/specs/001-astrocyte-meta-learning/`
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

- [ ] T001 Create project structure per implementation plan in `projects/PROJ-583-astrocyte-inspired-meta-learning-glial-m/`. **Deliverable**: Create directory tree: `code/`, `data/raw/`, `data/processed/`, `results/logs/`, `results/stats/`, `tests/unit/`, `tests/integration/` and empty `__init__.py` files in each.

- [ ] T002 Initialize a Python project with PyTorch (CPU-only), `torchvision`, `scipy`, `numpy`, `pandas`, and `huggingface/datasets` in `requirements.txt`. **Deliverable**: Create `requirements.txt` containing: `torch==2.0.0`, `torchvision==0.15.0`, `scipy==1.11.0`, `numpy==1.24.0`, `pandas==2.0.0`, `datasets==2.14.0`, `pytest==7.4.0`, `black==23.0.0`, `flake8==6.0.0`, `pylint==2.17.0`.

- [ ] T003a [P] Create GitHub Actions workflow file `.github/workflows/ci.yml` with triggers for `push` and `pull_request` on `main` and `001-astrocyte-meta-learning`. **Deliverable**: YAML file defining the CI job structure.

- [ ] T003b [P] Configure linting (flake8/pylint) and formatting (black) steps within the `.github/workflows/ci.yml` created in T003a. **Deliverable**: Workflow steps that install dependencies, run `black --check`, `flake8`, and `pylint`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004b [P] **DEPENDS ON: T005** Implement Mini-ImageNet pipeline and dynamic skip logic in `code/data/loaders.py`. **AMENDS FR-004**: This task implements the formal requirement change for CI validation as per the Plan.md "Spec Gap" mitigation. **Deliverable**: Function `load_mini_imagenet()` that checks `config.mini_imagenet_url`. If `None` or URL is not verified (fails checksum/ping), it logs a warning "Mini-ImageNet skipped: Spec Gap (CI Constraints)", sets a `SKIP_MINI_IMAGENET` flag, and returns `None`. If verified, it proceeds to download. **Note**: This logic must exist BEFORE the download utility to prevent crashes.

- [ ] T004 [P] **DEPENDS ON: T004b, T005** Implement robust dataset download utility with exponential backoff retry logic (configurable retry limit) in `code/data/loaders.py` handling Omniglot via `torchvision`. **Note**: Mini-ImageNet download is conditional based on T004b's `SKIP_MINI_IMAGENET` flag. **Deliverable**: If `config.mini_imagenet_url` is None, raise `ValueError('Mini-ImageNet URL not configured in config.yaml')` ONLY if T004b's skip logic is bypassed (i.e., if explicitly requested). Otherwise, handle gracefully.

- [ ] T005 [P] Configure configuration module in `code/config.py` enforcing `dataset_seed` for fairness constraints, defining `deferred_episodes`, exposing `sensitivity_scale_params` as a configurable list, and **explicitly including `mini_imagenet_url`** in the YAML/JSON schema. **Traceability**: Values align with spec's "Assumptions" section and "User Story 3" acceptance scenario. **Deliverable**: Create `code/config.py` with a `Config` dataclass or YAML file `config.yaml` containing keys: `dataset_seed` (int), `deferred_episodes` (int), `sensitivity_scale_params` (list[float] default [0.01, 0.05, 0.1]), `dataset_path` (str), and `mini_imagenet_url` (str or null).

- [ ] T006 [P] Implement logging infrastructure to capture per-episode metrics in `code/utils/logger.py`. **Deliverable**: Configure JSON logger writing to `results/logs/episode_{seed}.json` with fields: `task_id`, `plasticity_score`, `stability_score`, `loss`, `timestamp`.

- [ ] T007 Create base directory structure for `data/raw/`, `data/processed/`, `results/logs/`, `results/stats/`

- [ ] T008 [P] Implement checksum verification logic for downloaded datasets in `code/utils/checksum.py` to ensure data hygiene.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Meta-Learning with Astrocyte Modulation (Priority: P1) 🎯 MVP

**Goal**: Implement the MAML baseline with the astrocyte homeostatic module, enabling training episodes that log stability and plasticity metrics.

**Independent Test**: Run the training script for a sufficient number of episodes on Omniglot.; verify `results/logs/` contains a JSON/CSV with `plasticity_score` and `stability_score` per episode.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for calcium ODE solver convergence and clamping in `tests/unit/test_astrocyte_ode.py`
- [ ] T010 [P] [US1] Unit test for metric calculation (stability on older tasks vs plasticity on current) in `tests/unit/test_metrics.py`
- [ ] T011 [P] [US1] Integration test for end-to-end training loop with a sufficient number of episodes to validate convergence. in `tests/integration/test_training_loop.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement the differentiable Calcium-Wave ODE (Polykretis et al.) in `code/astrocyte/ode_module.py` including task-history buffer and $h_t$ calculation
- [ ] T013 [US1] **DEPENDS ON T012** Implement the MAML inner-loop update rule with $h_t$ multiplicative modulation in `code/astrocyte/maml_wrapper.py`
- [ ] T014 [US1] Implement Plasticity and Stability metric calculation logic in `code/training/metrics.py`. **Deliverable**: Implement function `calculate_metrics(current_task_acc: float, history_buffer: List[float]) -> Dict[str, float]`. **Stability Definition**: Strictly compute stability as the mean accuracy of the **last 3 tasks (N-1, N-2, N-3)** from the held-out buffer, as defined in the Plan.md "Meta-Test Buffer" (overriding FR-003's single-task requirement to reduce variance). **Plasticity**: Mean accuracy on current task at 5 steps.
- [ ] T015 [US1] Implement the main training loop in `code/training/trainer.py` that orchestrates dataset loading, episode generation, ODE updates, and metric logging
- [ ] T016 [US1] Add error handling for ODE divergence (clamp $Ca_t \in [0, 1]$) and dataset download failures in `code/training/trainer.py`
- [ ] T017 [US1] Implement result serialization to `results/logs/` in `code/training/trainer.py` ensuring deterministic output for the random seed

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline Comparison and Statistical Validation (Priority: P2)

**Goal**: Run comparative experiments (seeds) and perform statistical validation (Permutation Test primary, Hotelling's secondary) to validate the hypothesis against the baseline.

**Independent Test**: Provide two result files (baseline vs. astrocyte); verify `results/stats/` contains a report with the primary test statistic, p-value, and verdict.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for statistical test implementations (Permutation & Hotelling) handling covariance singularity in `tests/unit/test_statistical_analysis.py`
- [ ] T019 [P] [US2] Integration test for running 5 seeds and aggregating results in `tests/integration/test_baseline_comparison.py`

### Implementation for User Story 2

- [ ] T020 [US2] **DEPENDS ON T015** Implement the Baseline MAML runner (no modulation) in `code/training/trainer.py` (via config flag) ensuring identical dataset seeds. **This task must include the execution logic to generate the seed baseline result files required for the statistical test.**

- [ ] T021 [US2] **DEPENDS ON T020** Implement the script to orchestrate multiple independent training runs for both Baseline and Astrocyte models in `code/cli/run_experiment.py`. **This task MUST explicitly generate the baseline result files (`results/baseline_seeds.json`) and astrocyte result files required for the statistical test.**

- [ ] T021b [US2] **DEPENDS ON T015** Implement the Mini-ImageNet pipeline and dynamic skip logic. **Deliverable**: If a verified URL for Mini-ImageNet is not found in config, the system must dynamically skip Mini-ImageNet runs and log a warning, ensuring FR-004 is not silently dropped.

- [ ] T038 [US2] **PRIMARY STATISTICAL TEST** Implement the Permutation Test on joint [Stability, Plasticity] vectors in `code/analysis/stats.py`. **AMENDS FR-005**: This task implements the Plan.md "Constitution Check" override, making the Permutation Test the primary validation method due to N=5 constraints. **Deliverable**: Function `permutation_test(group_a, group_b)` returning `{'statistic': float, 'p_value': float, 'verdict': str}`. If `p < 0.05`, verdict is "significant".

- [ ] T022 [US2] **DEPENDS ON T038** Implement the secondary statistical analysis script in `code/analysis/stats.py` performing **Hotelling's T-squared test** on [Stability, Plasticity] vectors. **Deliverable**: Implement function `hotelling_t_squared(group_a: np.array, group_b: np.array)` that adds `1e-6 * I` to the covariance matrix if `np.linalg.cond(cov) > 1e10` before inversion. **Power Analysis**: Calculate post-hoc power; if power < 0.80, return `{'verdict': 'inconclusive', 'reason': 'insufficient_power', 'confidence_interval': null}`. **Note**: This task runs only if T038 is inconclusive or as a secondary reference.

- [ ] T023 [US2] Implement report generation in `code/analysis/visualizer.py` explicitly stating significance ($p < 0.05$) and trade-off interpretation based on the primary test result.

- [ ] T024 [US2] **DEPENDS ON T022** Add handling for "baseline failure" cases (accuracy ~0) to report "undefined" rather than crashing in `code/analysis/stats.py`. **Note**: T022 handles the mathematical singularity; T024 handles the high-level reporting logic.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Ablation (Priority: P3)

**Goal**: Verify robustness by sweeping homeostatic scale parameters and comparing dynamic ODE vs. constant homeostatic factor.

**Independent Test**: Run ablation script with scale params `[0.01, 0.05, 0.1]` and "constant mode"; verify summary table in `results/stats/` shows metric variation.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Unit test for constant homeostatic factor substitution in `tests/unit/test_ablation.py`
- [ ] T026 [P] [US3] Integration test for sensitivity sweep execution in `tests/integration/test_sensitivity_analysis.py`

### Implementation for User Story 3

- [ ] T027 [US3] **DEPENDS ON T005, T015** Implement sensitivity analysis loop in `code/analysis/ablation.py` iterating over configurable scale parameters **read from `code/config.py` (T005)**.
- [ ] T028 [US3] Implement "constant homeostatic" mode in `code/astrocyte/ode_module.py` to replace ODE with a fixed scalar when flag is set
- [ ] T029 [US3] Implement sensitivity summary generation in `code/analysis/ablation.py` creating a table of Stability/Plasticity vs. Scale Parameter
- [ ] T030 [US3] Add visualization or tabular output comparing dynamic vs. constant modes in `results/stats/ablation_summary.csv`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `README.md` and `docs/` covering usage, dependencies, and CPU-only constraints

- [ ] T032a [P] Implement memory profiling in `code/training/trainer.py` using `psutil` to log peak RSS after each epoch; if RSS > 6.5GB, raise a `MemoryLimitWarning` and trigger garbage collection.

- [ ] T032b [P] **DEPENDS ON T032a** Add a unit test `tests/unit/test_memory_limits.py` verifying memory profiling behavior with a mock large tensor.

- [ ] T033 Implement a timeout wrapper in `scripts/run_experiments.sh` that kills the process if runtime > 5.5 hours and logs a `TimeoutError`. **Deliverable**: Add a benchmark task `tests/integration/test_benchmark.py` that runs a single seed and asserts duration < 1.2 hours (scaled for 5 seeds).

- [ ] T034 [P] Additional unit tests for edge cases (divergence, singularity) in `tests/unit/`
- [ ] T035 Run `quickstart.md` validation and verify all artifacts match spec requirements

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 components (training loop)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US1 components

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models (ODE, Metrics) before Services (Training Loop)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel **(EXCEPT T012/T013 which are sequential due to semantic dependency)**
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for calcium ODE solver in tests/unit/test_astrocyte_ode.py"
Task: "Unit test for metric calculation in tests/unit/test_metrics.py"

# Launch all models for User Story 1 together (EXCEPT T012/T013):
# Note: T012 must complete before T013 due to semantic dependency
Task: "Implement Metric Calculation in code/training/metrics.py"
# T012 (ODE) and T013 (MAML) are NOT parallel; T013 depends on T012
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
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
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
- **Constraint**: All tasks must run on CPU-only CI (limited cores, GB RAM, no GPU). No 8-bit quantization or CUDA dependencies.
- **Note on T012/T013**: These are marked sequential in the "Parallel Opportunities" section due to data dependency, despite being in different files.
- **Note on T022**: Must implement Hotelling's T-squared (multivariate) with covariance singularity handling (adding epsilon to diagonal), NOT univariate t-tests. **Crucially, it must include the power analysis logic for 'inconclusive' verdicts.**
- **Note on T038**: This is the PRIMARY statistical test per Plan.md, overriding FR-005. T022 depends on it.
- **Note on T014**: Stability metric uses a 3-task buffer (N-1, N-2, N-3) as per Plan.md override of FR-003.
- **Note on T004b**: This task implements the "Spec Gap" mitigation for Mini-ImageNet, allowing conditional skip in CI.
- **Note on T027**: Must read parameters from `config.py`, not hardcode them.
- **Note on Data Integrity**: All tasks must consume real dataset sources (Omniglot via torchvision) and compute real metrics. No synthetic data or placeholder metrics are permitted.
- **Note on Execution Order**: T038 (Permutation Test) is the primary path. T022 (Hotelling's) runs as secondary or fallback.
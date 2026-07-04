# Tasks: Quantifying the Effects of Data Noise on Dynamical Systems Reconstruction

**Input**: Design documents from `/specs/001-quantifying-the-effects-of-data-noise-on/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan in `code/` and `tests/`
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (scipy, numpy, pandas, matplotlib, pyyaml, nolds, pytest)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. This phase includes TDD setup for generators.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` with constants: seeds, SNR levels spanning a range from low to high values, including near-zero conditions., system parameters (Lorenz: σ=10, ρ=28, β=8/3 (Wikipedia: Lorenz system, https://en.wikipedia.org/wiki/Lorenz_system); Rössler standard), batch size limits, AND define literature ranges based on standard references (e.g., Lorenz D2 ≈ 2.06 ± 0.05 [UNRESOLVED-CLAIM: c_e7264ae9 — status=not_enough_info], Lyapunov ≈ 0.90 ± 0.05) for validation
- [X] T005 [P] Implement `code/utils/io.py` with functions for CSV export (pandas), JSON artifact writing, and SHA256 checksumming of generated files
- [ ] T006 [P] Implement `code/utils/plotting.py` with base plot styles and error-bar visualization helpers
- [~] T007 [P] Implement `code/utils/data_models.py` with data classes (Trajectory, NoisyTrajectory, MetricResult) matching spec entities
- [~] T008 [P] Perform power analysis to determine sample size N for 80% power, alpha=0.05 (per spec Assumptions) and record the calculated N and methodology as a constant in `code/config.py`
- [~] T009 [P] Configure `code/main.py` orchestration script to enforce data flow: Generate → Inject → Compute → Analyze
- [ ] T010 Setup `tests/conftest.py` with `pytest-randomly` configuration and shared fixtures for deterministic seeds
- [ ] T011 [P] [US1] Unit test for Lorenz integration in `tests/test_generators.py` verifying no NaN/Inf and trajectory length ≥10,000 (Write first, ensure FAIL)
- [ ] T012 [P] [US1] Unit test for Rössler integration in `tests/test_generators.py` verifying state constraints (Write first, ensure FAIL)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Clean Chaotic Time-Series Data (Priority: P1) 🎯 MVP

**Goal**: Obtain ground-truth chaotic time-series data from Lorenz and Rössler attractors with known parameters.

**Independent Test**: Generate a Lorenz trajectory, compute its Lyapunov exponent, and verify it matches literature values within ±5% tolerance.

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `code/generators/lorenz.py` using `scipy.integrate.solve_ivp` with standard parameters
- [ ] T014 [P] [US1] Implement `code/generators/rossler.py` using `scipy.integrate.solve_ivp` with standard parameters
- [ ] T015 [US1] Implement `code/generators/__init__.py` to expose generation functions and validate output shapes
- [ ] T016 [US1] Implement `code/generators/validation.py` to validate the generated clean trajectory artifacts (from T018) against literature ranges defined in `code/config.py` using statistical confidence intervals (not binary assertions), acknowledging statistical uncertainty
- [ ] T017 [US1] Add error handling in generators to discard trajectories with overflow (NaN/Inf) and log warnings
- [ ] T018 [US1] Run generator to produce baseline clean trajectory artifacts in `data/raw/` for Lorenz and Rössler; artifacts MUST be saved as CSV/JSON with explicit file naming convention (e.g., `lorenz_clean_seed{seed}.csv`), include metadata, and be checksummed (SHA256) to register them for downstream consumption
- [ ] T019 [US1] Add logging for data generation steps in `code/generators/`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Inject Controlled Noise at Specified SNR Levels (Priority: P1)

**Goal**: Apply additive Gaussian noise and uniform quantization noise to clean trajectories across defined SNR ranges.

**Independent Test**: Inject Gaussian noise at a defined signal-to-noise ratio. and verify measured SNR matches target within ±0.5dB.

### Implementation for User Story 2

- [ ] T020 [P] [US2] Unit test for Gaussian noise injection in `tests/test_noise.py` verifying SNR calculation accuracy
- [ ] T021 [P] [US2] Unit test for quantization noise in `tests/test_noise.py` verifying step size = 2⁻ᵇ of dynamic range
- [ ] T022 [P] [US2] Implement `code/noise/gaussian.py` to add AWGN based on target SNR (·log₁₀(P_signal/P_noise))
- [ ] T023 [P] [US2] Implement `code/noise/quantization.py` to apply uniform quantization with user-specified bit resolution (variable bit depth)
- [ ] T024 [US2] Implement `code/noise/__init__.py` to route noise type and validate supported types (Gaussian, uniform quantization)
- [ ] T025 [US2] Implement `code/noise/verification.py` to compute post-injection SNR and assert it is within tolerance of target
- [ ] T026 [US2] Add validation to reject unsupported noise types with specific error message
- [ ] T027 [US2] Add logging for noise injection parameters and results in `code/noise/`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Compute Phase Space Reconstruction Metrics (Priority: P2)

**Goal**: Calculate Correlation Dimension, Lyapunov Exponents, and False Nearest Neighbors for noisy trajectories and compute error rates.

**Independent Test**: Run pipeline on 20dB SNR data; verify Lyapunov error ≤15% and 5dB SNR FNN rate >50%.

### Implementation for User Story 3

- [ ] T028 [P] [US3] Unit test for Grassberger-Procaccia in `tests/test_metrics.py` with synthetic data
- [ ] T029 [P] [US3] Unit test for Rosenstein's algorithm in `tests/test_metrics.py` verifying convergence behavior
- [ ] T030 [P] [US3] Unit test for FNN in `tests/test_metrics.py` verifying threshold logic (10× std dev)
- [ ] T031 [P] [US3] Implement `code/metrics/correlation_dim.py` using Grassberger-Procaccia with embedding dimension search
- [ ] T032 [P] [US3] Implement `code/metrics/lyapunov.py` using Rosenstein's algorithm with max evolution time logic
- [ ] T033 [P] [US3] Implement `code/metrics/fnn.py` with embedding dimension=2 and threshold=10× std dev
- [ ] T034 [US3] Implement `code/metrics/__init__.py` to orchestrate metric calculation on `NoisyTrajectory` inputs
- [ ] T035 [US3] Implement `code/analysis/error_analysis.py` to compute relative error as a percentage: |computed - ground_truth| / |ground_truth| scaled to a percentage basis
- [ ] T036 [US3] Add statistical aggregation logic in `code/analysis/` to handle multiple realizations and compute mean/std error
- [ ] T037 [US3] Add logging for metric computation and error calculation in `code/analysis/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Generate Error-vs-SNR Lookup Table and Visualization (Priority: P3)

**Goal**: Produce a lookup table and plots showing metric error rates across SNR levels.

**Independent Test**: Generate CSV with ≥6 SNR levels and verify columns match spec (SNR_dB, noise_type, metric_name, etc.).

### Implementation for User Story 4

- [ ] T038 [P] [US4] Unit test for CSV export in `tests/test_integration.py` verifying schema compliance
- [ ] T039 [P] [US4] Unit test for plot generation in `tests/test_integration.py` verifying critical threshold marking
- [ ] T040 [P] [US4] Implement `code/analysis/lookup_table.py` to aggregate results into CSV format with required columns
- [ ] T041 [P] [US4] Implement `code/analysis/plotting.py` to generate error-vs-SNR line plots with critical threshold markers
- [ ] T042 [US4] Implement `code/analysis/threshold_detection.py` to explicitly calculate and record TWO distinct SNR thresholds: (1) The SNR where metric error (Lyapunov/Correlation Dim) exceeds a substantial threshold (SC-004), and (2) The specific SNR where FNN rate exceeds 50% (SC-003), ensuring they are stored as separate values in the results
- [ ] T043 [US4] Integrate lookup table and plotting into `code/main.py` as the final pipeline step
- [ ] T044 [US4] Add validation to ensure lookup table contains all required SNR levels including the baseline and elevated values and noise types
- [ ] T045 [US4] Add logging for final output generation in `code/analysis/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories. Tasks here depend on the completion of US1-US4.

- [ ] T046 [P] Documentation updates in `docs/` including `quickstart.md` and `research.md`
- [ ] T047 Code cleanup and refactoring in `code/` for readability and performance
- [ ] T048 [P] Performance optimization across all stories to ensure ≤6h runtime on CPU cores; use `cProfile` to identify bottlenecks, then apply optimization techniques (e.g., vectorization, caching, algorithmic reduction) until the runtime is verified to be ≤6h (Depends on US1-US4 completion)
- [ ] T049 [P] Additional unit tests (if requested) in `tests/unit/`
- [ ] T050 Security hardening (input validation, error handling)
- [ ] T051 Run `quickstart.md` validation to ensure end-to-end reproducibility (Depends on T046)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 7)**: Depends on all desired user stories being complete
 - T048 (Performance) requires the full pipeline to be functional
 - T051 (Validation) requires T046 (Docs) to be complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Depends on US1 output (T018 artifact)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Depends on US2 output
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Depends on US3 output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation (T011/T012 in Phase 2, T020/T021 in Phase 4, etc.)
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- T046, T047, T049, T050 in Phase 7 can run in parallel, but T048 and T051 have specific dependencies

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for Lorenz integration in tests/test_generators.py"
Task: "Unit test for Rössler integration in tests/test_generators.py"

# Launch all models for User Story 1 together:
Task: "Implement code/generators/lorenz.py"
Task: "Implement code/generators/rossler.py"
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
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
 - Developer D: User Story 4
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (unless specified otherwise)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks MUST run on free CPU-only CI (limited CPU cores, constrained RAM, no GPU). No -bit/4-bit quantization, no CUDA, no large LLMs.
- **Data Integrity**: All tasks MUST use real data generation or real datasets. No fabrication of input data or metrics.
- **Scope**: Strictly limited to Lorenz, Rössler as per spec.md FR-001.
- **Reviewer Addressed**: Removed out-of-scope Cellular Automata tasks; clarified thresholds and dependencies.
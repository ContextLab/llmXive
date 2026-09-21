# Tasks: Normalized Gaps Between Consecutive Squarefree Numbers

**Input**: Design documents from `/specs/001-normalized-gaps-between-consecutive-squa/`
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

- [ ] T001 Create project structure per implementation plan: Execute `mkdir -p projects/PROJ-normalized-gaps-between-consecutive-squa/{code,data/{raw,processed,figures},tests/{contract,integration,unit},contracts,scripts}` to create the directory tree defined in plan.md.
- [ ] T002 Initialize Python 3.11 project: Create `projects/PROJ-722-normalized-gaps-between-consecutive-squa/requirements.txt` with pinned versions: `numpy>=1.24`, `scipy>=1.10`, `matplotlib>=3.7`, `pytest>=7.0`, `pyarrow>=12.0`.
- [ ] T003 [P] Configure linting and formatting: Create `projects/PROJ-722-normalized-gaps-between-consecutive-squa/pyproject.toml` with `[tool.black]` and `[tool.ruff]` sections configured for Python 3.11.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup directory structure and memory monitoring: Ensure `code/`, `data/raw/`, `data/processed/`, `data/figures/`, `tests/` exist (from T001) and implement memory monitoring utility in `code/utils.py` to track RSS via `/proc/self/status` (FR-007). **Note**: This utility will be invoked by T012c.
- [ ] T006 [P] Create base data schemas: Create `contracts/SquarefreeSequence.schema.yaml`, `contracts/GapDataset.schema.yaml`, and `contracts/TestResult.schema.yaml` in `contracts/` matching `data-model.md` entities.
- [X] T007 [P] Implement logging infrastructure: Create `code/logging_config.py` with a standard logger setup.
- [X] T009 [P] Setup environment configuration: Create `code/config.py` with a `Config` dataclass defining `N_cutoffs = [10**6, 5*10**6, 10**7]` and `random_seed = 42`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Squarefree Gaps and Compute Normalized Statistics (Priority: P1) 🎯 MVP

**Goal**: Generate squarefree numbers up to $N$, compute raw gaps, and normalize them by the empirical mean.

**Independent Test**: Run sieve for $N=10,000$, verify count against known values, and confirm mean of normalized gaps is 1.0.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test: Add `test_squarefree_sequence_schema` in `tests/contract/test_squarefree_sequence.py` that validates JSON against `contracts/SquarefreeSequence.schema.yaml`.
- [X] T011 [US1] Unit test: Add `test_normalize_gaps_mean_is_one` in `tests/unit/test_gaps_normalization.py` that verifies normalization logic.

### Implementation for User Story 1

- [X] T012a [P] [US1] Implement linear sieve: Implement `def sieve_squarefree(N: int) -> List[int]` in `code/sieve.py` returning a list of squarefree integers.
- [X] T012b [US1] Implement memory assertion wrapper: Wrap T012a execution in `code/sieve.py` to invoke the memory utility from T004, log peak RSS, and assert `peak_rss < 2 * 1024 * 1024 * 1024` bytes (2GB) to satisfy SC-005 and FR-007.
- [X] T012c [US1] **Explicit Verification Step**: Implement a wrapper function in `code/sieve.py` that explicitly calls the memory utility from T004 during the sieve run, captures the peak RSS, and raises an AssertionError if the 2GB limit is exceeded. This task ensures SC-005 is verified by an automated step in the execution flow.
- [X] T013 [P] [US1] Implement gap calculation: Implement `def calculate_gaps(squarefree_list: List[int]) -> List[int]` in `code/gaps.py` computing $\Delta_i = s_{i+1} - s_i$.
- [X] T014 [P] [US1] Implement normalization logic: Implement `def normalize_gaps(gaps: List[int]) -> List[float]` in `code/gaps.py` computing $g_i = \Delta_i / \bar{\Delta}$ with division-by-zero guard.
- [X] T015 [US1] Implement data persistence: Write normalized gaps to `data/raw/gaps_N={N}.parquet` using Parquet format in `code/gaps.py`.
- [X] T016 [US1] Add validation: Add `assert abs(mean(g) - 1.0) < 1e-9` in `code/gaps.py` before saving, explicitly referencing the theoretical value of 1.0 (SC-001).
- [X] T017 [US1] Add logging: Log sieve execution time and memory peak usage in `code/sieve.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Perform Statistical Goodness-of-Fit Testing (Priority: P2)

**Goal**: Perform a Lilliefors-style goodness-of-fit test via Monte Carlo simulation against Exponential(1).

**Independent Test**: Run test on synthetic exponential data (high p-value) and uniform data (low p-value).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test: Add `test_test_result_schema` in `tests/contract/test_test_result.py` that validates JSON against `contracts/TestResult.schema.yaml`.
- [X] T019 [P] [US2] Integration test: Add `test_lilliefors_monte_carlo` in `tests/integration/test_lilliefors.py` to verify resampling logic.

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement Lilliefors test logic: Implement `def lilliefors_ks(data: np.ndarray) -> float` in `code/stats.py`. **CRITICAL**: This function MUST first estimate the mean $\mu$ from `data`, shift the data by dividing by $\mu$ (or subtracting if using log-transform), and compare the empirical CDF of the shifted data against the standard exponential CDF (rate=1). This parameter estimation step distinguishes it from a standard KS test and satisfies FR-003.
- [X] T021 [US2] Implement Monte Carlo simulation: Implement `def monte_carlo_pvalue(ks_stat: float, data: np.ndarray, n_resamples: int = 10000) -> float` in `code/stats.py`.
- [X] T022 [US2] Implement edge case handling: Add logic in `code/stats.py` to handle p-value exactly 0.0 or 1.0 without crashing.
- [ ] T023a [P] [US2] Implement Random Thinning Control Generation: Implement `def generate_random_thinning(N: int, p: float) -> List[int]` in `code/control.py` with $p=6/\pi^2$ and save raw integers to `data/raw/control_thinning_raw_N={N}.parquet`.
- [ ] T023b [US2] Implement Random Thinning Control Stats: Compute raw gaps and normalized gaps for the dataset from T023a in `code/control.py` and save to `data/processed/control_thinning_normalized_N={N}.parquet`.
- [ ] T023c [US2] **Control Distribution Artifact**: Generate a unified "Control Distribution" artifact (Parquet) in `data/processed/control_distribution_N={N}.parquet` containing the normalized gaps. Additionally, generate a visual comparison plot in `code/viz.py` (CDF overlay of Squarefree vs. Control) and save to `data/figures/control_comparison_N={N}.png` to explicitly satisfy FR-006's requirement to distinguish distribution shape from heuristic validation.
- [ ] T024 [US2] Implement Gamma Control: Generate Gamma-distributed data, compute Lilliefors statistic, and **assert** that the resulting p-value is < 0.05 to validate test power (SC-007). This assertion must be explicit and fail the pipeline if the Gamma control is not rejected.
- [ ] T025 [US2] Save TestResult: Save `TestResult` (KS, p-value, N, control comparisons) to `data/processed/test_result_N={N}.json` as JSON.
- [ ] T026 [US2] Compare Squarefree vs Control: Calculate the difference between Squarefree KS statistic and Random Thinning KS statistic and assert the difference is < 0.01 (SC-006) in `code/control.py`. **Note**: This task now consumes the visual comparison artifact from T023c for comprehensive validation.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Convergence Analysis and Visualizations (Priority: P3)

**Goal**: Generate CDF/QQ-plots and convergence analysis charts for $N$ at multiple orders of magnitude.

**Independent Test**: Generate plots for fixed $N$ and verify file existence; verify convergence chart trend line.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Contract test: Add `test_viz_outputs` in `tests/contract/test_viz_outputs.py` to verify image file existence and metadata.
- [ ] T027b [US3] Implement Control Comparison Visualization: Generate a comparative plot in `code/viz.py` overlaying the Empirical CDF of the Squarefree gaps (from T015) and the Control Distribution (from T023c) to visually distinguish between testing distribution shape and validating the heuristic. Save to `data/figures/control_comparison_N={N}.png`.
- [ ] T028 [P] [US3] Unit test: Add `test_anderson_darling_statistic` in `tests/unit/test_anderson_darling.py` to verify A^2 calculation.

### Implementation for User Story 3

- [ ] T031 [P] [US3] Implement Anderson-Darling statistic: Implement `def anderson_darling_statistic(data: np.ndarray) -> float` in `code/stats.py` (replacing flawed R^2 metric).
- [ ] T029 [P] [US3] Implement Empirical CDF vs Exponential CDF plot: Implement `plot_cdf_comparison` in `code/viz.py` saving to `data/figures/cdf_N={N}.png`.
- [ ] T030 [US3] Implement QQ-plot generation: Implement `plot_qq_plot` in `code/viz.py` with $y=x$ reference line saving to `data/figures/qq_N={N}.png`.
- [ ] T032 [US3] Implement Convergence Analysis: Implement `plot_convergence` in `code/viz.py` plotting KS * sqrt(N) vs log N saving to `data/figures/convergence_analysis.png`.
- [ ] T033 [US3] **Convergence Trend Verification**: Implement a check for the stability of `KS * sqrt(N)` across different sample sizes. **Rationale**: The original SC-003 (KS within 10%) was discarded by the plan as statistically unsound; this task implements the corrected metric (KS*sqrt(N) stability) defined in the plan. Algorithm: Compute variance of `KS * sqrt(N)` across cutoffs; assert variance < 0.05. Save result to `data/processed/convergence_verification.json`.
- [ ] T034 [US3] Save all figures: Ensure all figures are saved to `data/figures/` (PNG/SVG).
- [ ] T035 [US3] Add warning logic: Add logic in `code/viz.py` to warn if $N < 1000$ and flag unreliable p-values.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T036 [P] Run full pipeline end-to-end: Create `tests/integration/test_pipeline.py` with `test_end_to_end_memory` that asserts peak RSS < 2GB (FR-007). **Note**: This test relies on the explicit assertion logic implemented in T012c.
- [ ] T037 [P] Generate final report: Aggregate all `TestResult` entries and generate `data/processed/final_report.md`.
- [ ] T038 [P] Code cleanup: Refactor `code/main.py` orchestration script for clarity.
- [ ] T039 [P] Documentation updates: Update `quickstart.md` with new CLI commands and `README.md` with project structure.
- [ ] T040 [P] Run validation: Create `scripts/validate_quickstart.sh` and run it to ensure reproducibility.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation (T015) and independent control generation (T023a)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 results

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for SquarefreeSequence schema in tests/contract/test_squarefree_sequence.py"

# Launch all models for User Story 1 together:
Task: "Implement linear sieve in code/sieve.py"
Task: "Implement gap calculation in code/gaps.py"
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
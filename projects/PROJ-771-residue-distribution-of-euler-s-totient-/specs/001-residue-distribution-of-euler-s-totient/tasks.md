# Tasks: Residue Distribution of Euler's Totient Function Modulo Small Primes

**Input**: Design documents from `/specs/001-residue-distribution-of-euler-s-totient/`
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

- [ ] T001a [P] Create `code/` directory (`mkdir -p code`)
- [ ] T001b [P] Create `data/raw/` and `data/processed/` directories (`mkdir -p data/raw data/processed`)
- [ ] T001c [P] Create `results/plots/` and `results/reports/` directories (`mkdir -p results/plots results/reports`)
- [ ] T001d [P] Create `tests/unit/` and `tests/integration/` directories (`mkdir -p tests/unit tests/integration`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `MemoryGuard` class in `code/sieve.py` using `psutil` to enforce a hard limit on memory usage, specifically failing if usage reaches >= 90% of the system's actual RAM limit (FR-007)
- [ ] T005 [P] Create base configuration loader in `code/run_analysis.py` to handle `N` and prime list `p ∈ {,, 7, 11}`
- [ ] T007a [P] Initialize random seed pinning in `code/sieve.py` for any deterministic operations
- [ ] T007b [P] Initialize random seed pinning in `code/stats.py` for Block Bootstrap and Monte Carlo simulations
- [ ] T007c [P] Initialize random seed pinning in `code/visualize.py` for any stochastic visual elements
- [ ] T007d [P] Initialize random seed pinning in `code/run_analysis.py` for orchestration-level randomness

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Totient Residues for Large Range (Priority: P1) 🎯 MVP

**Goal**: Generate the sequence of $\phi(n)$ for $n \in [1, N]$ and compute residues modulo $p$ using a linear sieve with arbitrary-precision integers.

**Independent Test**: Run on $N=100$ with $p=3, 5$ and verify output matches known mathematical values for $\phi(n) \pmod p$.

### Tests for User Story 1

- [ ] T008 [P] [US1] Unit test for linear sieve correctness in `tests/unit/test_sieve.py` (verify $\phi(n)$ against small known values)
- [ ] T009 [P] [US1] Unit test for memory guard trigger in `tests/unit/test_sieve.py` (mock memory spike to ensure graceful exit)

### Implementation for User Story 1

- [ ] T010 [US1] Implement `compute_phi_linear_sieve(N)` in `code/sieve.py` using Python's native `int` (arbitrary precision) to calculate $\phi(n)$ for all $n \le N$
- [ ] T011 [US1] Implement `compute_residues(phi_values, prime)` in `code/sieve.py` to aggregate counts for residue classes $\{0, \dots, p-1\}$
- [ ] T012 [US1] Integrate `MemoryGuard` polling inside the sieve loop in `code/sieve.py` to check usage based on `max(^5, N/100)` iterations OR dynamic memory thresholds, prioritizing the 90% memory limit check (FR-007)
- [ ] T014 [US1] Implement error handling to log specific $n$ if sieve fails or overflow is detected, ensuring this logic executes BEFORE any data save operation (Edge Case: Error Scenario)
- [ ] T013 [US1] Save raw residue counts to `data/raw/residues_{prime}_{N}.json` (JSON serialization of `ResidueDataset`) - **depends on T014**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Perform Statistical Goodness-of-Fit Tests (Priority: P2)

**Goal**: Apply Block Bootstrap and Chi-squared tests to determine deviation from theoretical bounds, handling dependent data.

**Independent Test**: Feed synthetic biased dataset and verify p-value $< 0.05$; feed uniform dataset and verify p-value $> 0.05$.

### Tests for User Story 2

- [ ] T015 [P] [US2] Unit test for Block Bootstrap logic in `tests/unit/test_stats.py` (verify resampling of contiguous blocks)
- [ ] T016 [P] [US2] Unit test for Chi-squared fallback in `tests/unit/test_stats.py` (verify exact/Monte Carlo switch when expected bin count < 5)

### Implementation for User Story 2

- [ ] T017 [US2] Implement `block_bootstrap_residues(residue_sequence, block_size, num_samples)` in `code/stats.py` to generate null distribution for the deviation metric D
- [ ] T019 [US2] Implement `calculate_chi_squared_statistic_D(observed_counts, theoretical_counts)` in `code/stats.py` to compute $D = \max_k |O_k - E_k^{theo}|$ - **DO NOT** compute or return any p-value; output D only for use by T020
- [ ] T020 [US2] Integrate Block Bootstrap p-value calculation: compare $D_{obs}$ (from T019) against the bootstrap distribution (from T017) to compute the final p-value. **Explicitly define D using the formula $D = \max_k |O_k - E_k^{theo}|$ where $E_k^{theo}$ is derived from the theoretical error bounds in Lebowitz-Lockard and Pollack & Roy.**
- [ ] T027a [US2] Research and define exact error bound formulas and constants from Lebowitz-Lockard and Pollack & Roy. for use in T027
- [ ] T022 [US2] Implement Bonferroni correction logic in `code/stats.py` to determine the 'pass/fail' flag using the corrected alpha ($\alpha_{adj} = 0.05/4$) as the primary metric - **depends on T027a**
- [ ] T021 [US2] Save statistical results to `data/processed/stats_{prime}_{N}.json` (JSON serialization of `StatisticalResult`) including the Bonferroni-corrected pass/fail flag - **depends on T022**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualize and Compare Against Theoretical Bounds (Priority: P3)

**Goal**: Generate bar plots and QQ-plots comparing observed frequencies to uniform expectation and annotated theoretical error bounds.

**Independent Test**: Generate plots for $p=5$ and verify "Uniform Expectation" line is at $N/5$ and error bounds are annotated.

### Tests for User Story 3

- [ ] T023 [P] [US3] Unit test for plot generation in `tests/unit/test_visualize.py` (verify image file creation and dimensions)
- [ ] T024 [P] [US3] Integration test for full report generation in `tests/integration/test_pipeline.py` (verify all artifacts created)

### Implementation for User Story 3

- [ ] T025 [US3] Implement `plot_bar_frequencies(residue_counts, prime)` in `code/visualize.py` to create bar plots with $N/p$ reference line
- [ ] T026 [US3] Implement `plot_residual_qq(residuals)` in `code/visualize.py` to generate QQ-plots for $\chi^2$ residuals
- [ ] T027 [US3] Implement `annotate_theoretical_bounds(plot, prime)` in `code/visualize.py` to overlay error bounds using formulas defined in T027a - **depends on T027a**
- [ ] T028 [US3] Generate summary report in `results/reports/summary_{N}.md` containing test statistics, p-values, and pass/fail flags (FR-006)
- [ ] T029 [US3] Ensure all output images are saved as PNG with high resolution (DPI equivalent) in `results/plots/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T022a [P] [US2] Flag contradiction: Create a note in `docs/contradictions.md` documenting the conflict between Plan's "primary alpha=0.05" and the Bonferroni-corrected pass/fail flag required by T022, requesting human review to update the Plan/Spec
- [ ] T030 [P] Documentation updates: Add `quickstart.md` with execution instructions for $N=5,000,000$
- [ ] T031 Code cleanup: Refactor `run_analysis.py` to ensure clean separation of orchestration logic
- [ ] T032 Performance optimization: Verify sieve loop efficiency and memory footprint on $N=5,000,000$ (Target: < 1 hour)
- [ ] T033 [P] Add `pytest` integration test for full pipeline in `tests/integration/test_pipeline.py`
- [ ] T034 Run `quickstart.md` validation to ensure reproducibility on fresh environment

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (residue data)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (statistical results)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Core algorithms (sieve, stats) before visualization
- Data generation before analysis
- Analysis before reporting

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for linear sieve correctness in tests/unit/test_sieve.py"
Task: "Unit test for memory guard trigger in tests/unit/test_sieve.py"

# Launch all models for User Story 1 together:
Task: "Implement compute_phi_linear_sieve(N) in code/sieve.py"
Task: "Implement compute_residues(phi_values, prime) in code/sieve.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify $\phi(n)$ values)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Statistical Analysis)
4. Add User Story 3 → Test independently → Deploy/Demo (Visualization)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Sieve & Data)
   - Developer B: User Story 2 (Stats & Bootstrap)
   - Developer C: User Story 3 (Visualization & Reports)
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
- **Critical**: Ensure `code/sieve.py` uses Python's native `int` (arbitrary precision) as per Constitution Principle VI.
- **Critical**: Ensure `code/stats.py` implements Block Bootstrap to handle sequence dependence, not simple i.i.d. bootstrapping.
- **Critical**: Ensure $N=5,000,000$ completes within 1 hour on 2 CPU cores; optimize sieve loop if necessary.
- **Critical**: T019 calculates D only; T020 calculates the p-value using the bootstrap distribution.
- **Critical**: T022 uses the Bonferroni-corrected alpha for the pass/fail flag.
- **Critical**: T027a defines the error bound formulas before T027 implements them.
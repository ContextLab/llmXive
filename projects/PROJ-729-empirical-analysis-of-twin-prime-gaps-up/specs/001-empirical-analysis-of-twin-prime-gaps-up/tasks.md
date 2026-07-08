# Tasks: Empirical Analysis of Twin Prime Gaps up to 10⁹

**Input**: Design documents from `/specs/001-twin-prime-gaps/`
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan in `projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/`
- [X] T002 Initialize Python 3.11 project with `primesieve`, `numpy`, `pandas`, `scipy`, `matplotlib` dependencies in `requirements.txt`
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data directory structure: `data/raw/`, `data/results/`, `data/figures/`
- [X] T005 [P] Create data schema definition in `contracts/twin_prime_schema.schema.yaml` defining `p`, `p_next`, `delta`, `normalized_gap`
- [X] T006 [P] Implement `code/hash_artifacts.py` to compute SHA-256 hashes and update project state YAML (Constitution Principle V)
- [X] T007 Create base configuration loader in `code/config.py` for reading range limits and paths
- [X] T008 Setup error handling infrastructure in `code/utils.py` (exit codes, logging) <!-- FAILED: unspecified -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate and Normalize Twin Prime Gaps (Priority: P1) 🎯 MVP

**Goal**: Generate the complete list of twin primes up to 10⁹, compute normalized gaps, and output a validated CSV dataset.

**Independent Test**: Run `code/generate_primes.py` and verify `data/raw/twin_primes.csv` exists with correct columns, finite positive normalized gaps, and a row count consistent with theoretical expectations (within ±5%).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for gap calculation logic in `tests/unit/test_gap_calc.py` (verify formula `delta / log(p)`). **Specific Task**: Add `tests/unit/test_gap_calc.py::test_normalized_gap_formula` asserting `delta / log(p)` equals expected float 1.8205 for input p=3, p_next=5. **Verification**: Use tolerance `assert abs(val - 1.8205) < 1e-4 ` to handle floating point precision.
- [ ] T011 [P] [US1] Integration test for full generation pipeline in `tests/integration/test_generation.py` (verify file creation and row count)

### Implementation for User Story 1

- [ ] T012 [US1] [FR-001] [FR-002] [SC-001] Implement `code/generate_primes.py` using `primesieve` to find twin primes up to 1,000,000,000. **Verification**: Run `python code/generate_primes.py` and verify `data/raw/twin_primes.csv` exists with row count within ±5% of the theoretical expectation calculated in T013b, and no NaN values in `normalized_gap`.
- [X] T013 [US1] [FR-002] Implement gap calculation and normalization logic in `code/generate_primes.py`
 - Must compute `delta = p_{n+1} - p_n` (gap between starts of consecutive pairs)
 - Must compute `normalized_gap = delta / log(p_n)`
 - Must handle edge cases (log(0 (Theorem DB: math/0506067, https://arxiv.org/abs/math/0506067)) guards)
- [~] T013b [US1] [FR-002] [SC-001] Compute expected twin prime count using Hardy-Littlewood constant and compare against actual count. **Verification**: Log the deviation percentage between actual count and theoretical expectation in the console output. <!-- FAILED: unspecified -->
- [~] T014 [US1] [FR-007] [SC-004] [SC-005] Implement CSV output and memory monitoring in `code/generate_primes.py`
 - Ensure RAM usage < 2 GiB and execution time < 45 mins
 - Output columns: `p`, `p_next`, `delta`, `normalized_gap`
- [~] T014b [US1] [SC-004] [SC-005] Measure and record execution time and peak memory usage for the generation pipeline. **Output**: Save metrics to `data/results/performance_gen.json`.
 - **Dependency**: Must run sequentially immediately after T014 to capture metrics of the just-completed run.
- [ ] T015 [US1] [P] Implement `code/validate_schema.py` to validate `data/raw/twin_primes.csv` against `contracts/twin_prime_schema.schema.yaml`
 - **Dependency**: Must run sequentially immediately after T014 to validate the generated artifact.
- [ ] T016 [US1] [P] Add execution guard in `code/generate_primes.py` to detect dependency failures (e.g., missing `primesieve` binary) and exit with code 1. Also run `code/hash_artifacts.py` to hash the generated CSV and update state.
 - **Dependency**: Must run after T015.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Goodness-of-Fit Testing (Priority: P2)

**Goal**: Perform Parametric Bootstrap KS tests and generate QQ-plots comparing empirical normalized gaps against the theoretical exponential distribution (λ=1).

**Independent Test**: Run `code/analyze_gaps.py` on the generated CSV and verify `data/results/stats.json` contains KS statistics/p-values and `data/figures/qq_plot.png` is generated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for Parametric Bootstrap KS logic in `tests/unit/test_bootstrap_ks.py`
- [ ] T019 [P] [US2] Integration test for analysis pipeline in `tests/integration/test_analysis.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/analyze_gaps.py` to load `data/raw/twin_primes.csv`
- [ ] T021 [US2] [FR-003] Implement Parametric Bootstrap Kolmogorov–Smirnov test in `code/analyze_gaps.py`
- Compare empirical distribution against `expon(scale=1)` using **Parametric Bootstrap** (3.141592653589793 (Wikipedia: pi, https://en.wikipedia.org/wiki/Pi) iterations, seed=42) to correct for self-normalization bias.
 - Explicitly document the "self-normalized" nature of the data.
 - Save results to `data/results/stats.json`
 - **Verification**: Check stats.json contains a non-zero KS statistic and a valid p-value.
- [ ] T021b [US2] [SC-002] Measure the KS p-value against the α=0.05 threshold and record the deviation status in `data/results/stats.json`.
 - **Dependency**: Must run sequentially immediately after T021.
- [ ] T021c [US2] [SC-004] [SC-005] Measure and record execution time and peak memory usage for the analysis pipeline. **Output**: Save metrics to `data/results/performance_analysis.json`.
 - **Dependency**: Must run sequentially immediately after T021.
- [ ] T022 [US2] [FR-004] Implement QQ-plot generation in `code/analyze_gaps.py`
 - Plot empirical quantiles (y) vs theoretical exponential quantiles (x)
 - Include reference line `y=x`
 - Save to `data/figures/qq_plot.png`
- [ ] T023 [US2] [P] Add logic to flag rejection status (p < 0.05 vs p ≥ 0.05) in the JSON summary. Run `code/hash_artifacts.py` to hash `stats.json` and update state.
 - **Dependency**: Must run after T021/T021b.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Localized Deviation Analysis near Powers of Two (Priority: P3)

**Goal**: Analyze normalized gaps in windows around powers of two (2^k ± 10⁴) to detect systematic deviations using one-sample t-tests as mandated by the Spec.

**Independent Test**: Run `code/analyze_local.py` and verify `data/results/local_stats.json` contains window metrics and `data/figures/local_deviation.png` is generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Unit test for window filtering logic in `tests/unit/test_window_filter.py`
- [ ] T025 [P] [US3] Integration test for localized analysis in `tests/integration/test_local_analysis.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `code/analyze_local.py` to load `data/raw/twin_primes.csv`
- [ ] T027 [US3] Implement window filtering logic for `k` in a range of exponents (range `[^k - 10000, 2^k + 10000]`) (FR-005)
- [ ] T028 [US3] [FR-005] [SC-003] Perform **one-sample t-tests** comparing each window's mean to the theoretical mean of 1.0.
 - **Note**: This task explicitly follows Spec FR-005 and SC-003, overriding the Plan's Complexity Tracking rationale which argued against one-sample tests.
 - Compute local mean and variance for each window.
 - Perform one-sample t-test against mean 1.0.
 - **Output**: Add a boolean column `is_significant` to `local_stats.json` for windows where p < 0.05.
 - Flag windows where the deviation is statistically significant (p < 0.05).
- [ ] T029 [US3] [FR-005] Generate bar chart of mean normalized gaps per window relative to 1.0 (FR-005)
 - Save to `data/figures/local_deviation.png`
- [ ] T030 [US3] [P] Save window statistics (mean, variance, t-stat, p-value) to `data/results/local_stats.json`. Run `code/hash_artifacts.py` to hash `local_stats.json` and update state.
 - **Dependency**: Must run after T028.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Verification (Polish)

**Purpose**: Generate final report, verify citations, andhash artifacts.

- [ ] T031 [P] [FR-009] Implement `code/verify_citations.py` to validate {{claim:c_ddd2cee1}} and {{claim:c_462d859b}} (OEIS A002386, https://oeis.org/A002386) citations against primary sources.
 - **Step 1**: Attempt to resolve missing URLs in spec.md Assumptions via DOI lookup using `requests` and crossref logic.
 - **Step 2 (Fallback)**: If DOI lookup fails, use a hardcoded canonical URL list for {{claim:c_ddd2cee1}} and Goldston et al. (2005) to ensure verification proceeds.
 - **Validation Criteria**: Verify title overlap >= 0.7 against resolved primary source URLs.
- [ ] T032 [P] [FR-006] Implement `code/report.py` to compile final Markdown report
 - Include KS statistics, p-values, QQ-plot, and localized deviation summary.
 - Include a section on historical framing (Cramér, Hardy-Littlewood) and computational limits (addresses Dan Rockmore review).
 - Explicitly consume the KS p-value deviation status from `data/results/stats.json` (SC-002).
- [ ] T033 [P] Run `code/hash_artifacts.py` to hash the final report and update state YAML.
 - **Dependency**: Must run after T032 (Report Generation).

---

## Phase 7: Review Response & Methodological Framing (Revision)

**Purpose**: Address Dan Rockmore's review regarding historical context and computational limits.

- [ ] T035 [P] Update `code/report.py` to include a dedicated "Historical Context" section citing Cramér (1930s) and Goldston, Pintz, Yıldırım (n.d.)

The specific value to remove/generalize: 'n.d.'

Rewritten passage:
Goldston, Pintz, Yıldırım (n.d.) (Addresses Rockmore Review)
 - **Dependency**: Must run sequentially after T032.
 - Must explicitly quote or paraphrase the heuristic regarding prime gap distribution.
 - Must reference the Hardy-Littlewood k-tuple conjecture context.
- [ ] T036 [P] Update `code/report.py` to include a "Computational Limits & Bias Analysis" section (Addresses Rockmore Review)
 - **Dependency**: Must run sequentially after T032.
 - Analyze how the bound $10^9$ might bias the observed tail of the distribution.
 - Discuss the robustness of the claim given the finite sample size.
 - Explicitly state the limitations of the CPU-only approach on the tail behavior.
- [ ] T037 [P] Update `specs/001-twin-prime-gaps/research.md` to include the missing lineage paragraph before the validation verdict (Addresses Rockmore Review)
 - **Content**: Insert the following specific paragraph: "The normalized gap metric Δₙ / log pₙ derives from Cramér's probabilistic model of primes, which posits that prime gaps follow an exponential distribution. [UNRESOLVED-CLAIM: c_32ba7555 — status=not_enough_info] This heuristic was refined by Goldston, Pintz, and Yıldıldırım (2005) in the context of small gaps between primes, and is consistent with the Hardy-Littlewood k-tuple conjecture which provides the asymptotic density for twin primes."

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all user stories being complete
- **Revision (Phase 7)**: Depends on Phase 6 completion (requires report generation logic)

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (requires `data/raw/twin_primes.csv`)
- **User Story 3 (P3)**: Depends on US1 completion (requires `data/raw/twin_primes.csv`)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Scripts before execution
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US2 and US3 can start in parallel (both depend only on US1 data)
- All tests for a user story marked [P] can run in parallel
- Verification, Reporting, and Revision tasks (Phase 6 & 7) can run in parallel after all analysis is done (subject to specific dependency notes)

---

## Parallel Example: User Story 2 & 3

```bash
# Once US1 data is generated, US2 and US3 can run in parallel:
Task: "Run Parametric Bootstrap KS test in code/analyze_gaps.py"
Task: "Run Localized Deviation Analysis in code/analyze_local.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Generate Data)
4. **STOP and VALIDATE**: Test data generation and schema validation independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Generate Data → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Statistical Analysis → Test independently → Deploy/Demo
4. Add User Story 3 → Localized Analysis → Test independently → Deploy/Demo
5. Add Phase 6 → Report & Verification
6. Add Phase 7 → Review Response & Framing
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Generation)
 - Developer B: User Story 2 (Global Analysis) - *Starts after A produces CSV*
 - Developer C: User Story 3 (Local Analysis) - *Starts after A produces CSV*
3. Stories complete and integrate independently
4. Phase 6 (Reporting) and Phase 7 (Revision) run after all analysis is complete

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All prime generation and analysis MUST run on CPU-only CI (a minimal core count, limited RAM, a constrained time budget). No GPU, no 8-bit quantization, no large LLMs.
- **Review Response**: Tasks T031, T032, T035, T036, and T037 specifically address the Dan Rockmore review regarding historical context, computational limits, and methodological framing.
- **Methodology Note**: This project uses Parametric Bootstrap KS tests and one-sample t-tests for local windows as explicitly mandated by the Spec (FR-005), overriding the Plan's Complexity Tracking rationale which argued against one-sample tests. The Spec takes precedence.
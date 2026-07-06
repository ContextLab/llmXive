# Tasks: Exploring the Relationship Between Prime Gaps and the Riemann Hypothesis

**Input**: Design documents from `/specs/001-exploring-the-relationship-between-prime/`
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

- [ ] T001 Create project structure per implementation plan: `src/data/`, `src/analysis/`, `src/utils/`, `src/cli/`, `tests/unit/`, `tests/integration/`, `data/raw/`, `data/processed/`, `data/results/`, `results/`, `state/`
- [ ] T002 Initialize Python 3.11 project with dependencies (`numpy`, `scipy`, `pandas`, `pyyaml`, `requests`, `pytest`) in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement memory-efficient logging infrastructure in `src/utils/logging.py` (handles chunked processing logs and OOM warnings)
- [ ] T005 [P] Create configuration management in `src/utils/config.py` (defines N=10^10, W=10^6, seeds, file paths)
- [ ] T006 [P] Implement deterministic random seed management for all Monte Carlo and simulation tasks
- [ ] T007 Create base data models in `src/utils/models.py` (PrimeGap, ZetaZero, WindowStats entities per spec)
- [ ] T008 Implement checksumming logic in `src/utils/io.py` for `state.yaml` updates on data changes

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Generate primes up to 10^10 and ingest zeta zeros, ensuring memory safety and data validity.

**Independent Test**: Run `src/data/generate_primes.py` and `src/data/ingest_zeros.py` in isolation; verify `data/processed/primes_gaps.csv` and `data/processed/zeta_zeros.csv` exist, contain correct counts, and peak RAM < 7GB.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T009 [P] [US1] Unit test for segmented sieve logic in `tests/unit/test_sieve.py` (verifies primality and chunk boundaries)
- [ ] T010 [P] [US1] Integration test for data pipeline in `tests/integration/test_data_ingestion.py` (verifies file generation and memory limits)

### Implementation for User Story 1

- [ ] T011 [US1] Implement segmented sieve algorithm in `src/data/generate_primes.py` to generate primes up to 10^10, processing in chunks to stay within 7GB RAM
- [ ] T012 [US1] Implement logic in `src/data/generate_primes.py` to compute consecutive prime gaps and stream results to `data/processed/primes_gaps.csv` (format: `prime_before, prime_after, gap_size, normalized_gap`)
- [ ] T013a [US1] **Verified Accuracy Check**: Implement logic in `src/data/ingest_zeros.py` to verify LMFDB/Odlyzko URLs for zeta zeros using the Reference-Validator Agent protocol. Target URLs: ` and `. Record verification status in `state.yaml`. (Traces to Constitution Principle II)
- [ ] T014 [US1] Implement data validation in `src/data/ingest_zeros.py` to skip malformed zero entries and log warnings. If verification fails, the pipeline MUST halt with a clear error message.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Extremal Gap and Zero-Spacing Distributional Comparison (Priority: P2)

**Goal**: Compute distributional similarity between normalized prime spacings and zeta zero spacings using KS test and Cramér model.

**Independent Test**: Run `src/analysis/distribution_test.py` on small synthetic datasets; verify `results/correlation_results.json` contains KS statistic, p-value, and plots.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Unit test for normalization logic (log^2 p) in `tests/unit/test_analysis.py`
- [ ] T017 [P] [US2] Unit test for KS test calculation in `tests/unit/test_analysis.py`

### Implementation for User Story 2

- [ ] T018b [US2] **Primary Analysis (FR-003)**: Implement sliding window analysis in `src/analysis/distribution_test.py` to compute *maximal* prime gap $g_{max}$ within windows of length $W=10^6$ and normalize by $\log^2 p$, satisfying spec FR-003.
- [ ] T019 [US2] Implement normalization of gaps by Cramér prediction ($\log^2 p$) in `src/analysis/distribution_test.py`.
- [ ] T020 [US2] Implement empirical distribution calculation for normalized maximal gaps (from T018b) in `src/analysis/distribution_test.py`.
- [ ] T021a [US2] **Theoretical Distribution**: Implement the theoretical pair-correlation distribution calculation for zeta zero spacings using the GUE formula (Montgomery-Odlyzko law), which models the distribution with a functional form characterized by a central peak and oscillatory decay. in `src/analysis/distribution_test.py`.
- [ ] T022 [US2] Perform Kolmogorov-Smirnov (KS) test comparing the *empirical maximal gap distribution* (from T020) against the GUE theoretical distribution (from T021a).
- [ ] T023 [US2] Implement Monte Carlo simulation using the Cramér model in `src/analysis/monte_carlo.py` to generate a null distribution of the KS statistic.
- [ ] T024 [US2] Calculate p-value for observed distributional alignment against the Cramér null distribution.
- [ ] T025 [US2] Generate visualization (CDF overlay of empirical vs. theoretical maximal gap distributions) using `matplotlib` and save to `results/correlation_plot.png` and `results/correlation_results.json`.
- [ ] T026 [US2] Implement permutation test (shuffling gap sequence) as a secondary null hypothesis check (per Principle VI).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Verification (Priority: P3)

**Goal**: Verify stability of results across window sizes and against synthetic Cramér data.

**Independent Test**: Run analysis with $W \in \{10^5, 10^6, 2 \cdot 10^6\}$; verify `results/robustness_report.md` lists KS statistics for each.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Integration test for sensitivity sweep in `tests/integration/test_robustness.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement sensitivity analysis loop in `src/analysis/robustness.py` sweeping window size $W$ over a range of magnitudes to measure stability (Traces to SC-002). **(Depends on T022 completion to access baseline KS statistic)**.
- [ ] T029 [US3] Generate synthetic Cramér model dataset of comparable size in `data/null/cramer_sample.csv`
- [ ] T030 [US3] Perform distributional analysis on the synthetic Cramér dataset to establish a baseline
- [ ] T031 [US3] Compare observed KS statistics from prime data against the synthetic Cramér baseline and the permutation test results
- [ ] T032 [US3] Generate `results/robustness_report.md` summarizing KS statistics for each window size and the Cramér comparison

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `docs/` (including `quickstart.md` and `research.md`)
- [ ] T039 Code cleanup and refactoring
- [ ] T040 Performance optimization across all stories (ensure a reasonable runtime limit is met

The research question remains: [Research Question]
The method remains: [Method]
The references remain: [References])
- [ ] T041 [P] Additional unit tests (if requested) in `tests/unit/`
- [ ] T042 Run `quickstart.md` validation to ensure full pipeline reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1 (T012)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data from US1 and results from US2
 - **Critical**: Task T028 (US3) explicitly depends on T022 (US2) completion to access the baseline KS statistic.
- **Phase N**: Depends on all user stories being complete

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
Task: "Unit test for segmented sieve logic in tests/unit/test_sieve.py"
Task: "Integration test for data pipeline in tests/integration/test_data_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement segmented sieve algorithm in src/data/generate_primes.py"
Task: "Implement zeta zero ingestion in src/data/ingest_zeros.py"
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
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Analysis)
 - Developer C: User Story 3 (Robustness)
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
- **Critical Constraint**: All tasks must run on CPU-only CI (limited cores, constrained RAM). No GPU, no 8-bit models, no large LLMs.
- **Data Integrity**: No fake data. All primes must be generated via sieve; all zeros must be from LMFDB/Odlyzko. If verification fails, pipeline halts.
- **Constitution Compliance**: T013a ensures Constitution Principle II (Verified Accuracy) is met. Local generation is strictly forbidden.
- **Removed Scope**: Phase 6 (Topological Visualization) and Tasks T015a/b (Subsampling) were removed as they were unapproved scope creep or introduced unnecessary complexity not authorized by the spec.
- **Clarified Scope**: Task T018b is the sole implementation of FR-003 (Maximal Gaps). Task T028 explicitly lists the required window sizes {^5, 10^6, 2*10^6}.
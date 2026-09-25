# Tasks: Exploring the Relationship Between Prime Gaps and the Riemann Hypothesis

**Input**: Design documents from `/specs/001-exploring-the-relationship-between-prime/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Validation Rule**: Every task MUST cite a specific FR, SC, or US ID from `spec.md` or `plan.md`. Tasks without a spec anchor are invalid.

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

- [ ] T001 Create project structure per implementation plan by running: `mkdir -p src/data src/analysis src/utils src/cli tests/unit tests/integration data/raw data/processed data/results results state` (Addresses FR-001, SC-004)
- [X] T002 Initialize Python project with dependencies (`numpy`, `scipy`, `pandas`, `pyyaml`, `requests`, `pytest`, `ruff`, `black`) in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement memory-efficient logging infrastructure in `src/utils/logging.py` (handles chunked processing logs and OOM warnings)
- [X] T005 [P] Create configuration management in `src/utils/config.py` (defines N=10^10, W=10^6, file paths, and `WINDOW_STEP` for sliding window stride).
- [X] T006 [US1] Implement deterministic random seed management in `src/utils/config.py` by defining a `GLOBAL_SEED` constant and ensuring all random generators use it. **(Depends on T005 completion; NOT [P] as it writes to config.py which T005 also edits. T006 must run before T007/T008a).**
- [X] T007 Create base data models in `src/utils/models.py` (PrimeGap, ZetaZero, WindowStats entities per spec)
- [X] T008a [P] **Initialize State File**: Create and initialize the file `state/projects/PROJ-548-exploring-the-relationship-between-prime.yaml` with the required schema, including an empty `artifact_hashes` map and `updated_at` timestamp, to satisfy Constitution Principle III (Data Hygiene) and Principle V (Versioning Discipline).
- [X] T008 [US1] Implement checksumming logic in `src/utils/io.py` for updates to `state/projects/PROJ-548-exploring-the-relationship-between-prime.yaml`. **(Depends on T008a).**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Generate primes up to 10^10 and ingest zeta zeros, ensuring memory safety and data validity.

**Independent Test**: Run `src/data/generate_primes.py` and `src/data/ingest_zeros.py` in isolation; verify `data/processed/raw_gaps.csv` and `data/processed/zeta_zeros.csv` exist, contain correct counts, and peak RAM < 7GB.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [P] [US1] Unit test for segmented sieve logic in `tests/unit/test_sieve.py` (verifies primality and chunk boundaries)
- [X] T010 [P] [US1] Integration test for data pipeline in `tests/integration/test_data_ingestion.py` (verifies file generation and memory limits)

### Implementation for User Story 1

- [X] T011 [US1] Implement segmented sieve algorithm in `src/data/generate_primes.py` to generate primes up to 10^10, processing in chunks to stay within 7GB RAM. **CRITICAL**: The task MUST generate primes up to $N=10^{10}$ as per FR-001. If the runtime exceeds the CI time limit, the run MUST fail (no fallback to $N=10^9$). The pipeline must log the failure and halt, ensuring FR-001 compliance is binary. **(Addresses FR-001, SC-004)**.
- [ ] T012 [US1] Implement logic in `src/data/generate_primes.py` to compute consecutive prime gaps and stream results to `data/processed/raw_gaps.csv` (format: `prime_before, prime_after, gap_size`). **Verification**: Verify output file schema matches spec Key Entities. **Status**: Active implementation required. **(Note: Normalization is handled in T018b).**
- [ ] T015 [US1] **Implement Ingestion & Verification**: Implement logic in `src/data/ingest_zeros.py` that FIRST verifies the zeta zero source URL against the hardcoded canonical list (LMFDB/Odlyzko) defined in the spec. If the verified sources are unreachable, the pipeline MUST halt with a clear "Data Unavailable" error. If verified, fetch and parse the zeta zero data to populate `data/raw/zeta_zeros.csv`. **(Addresses FR-002, US1).**
- [X] T014 [US1] Implement data validation in `src/data/ingest_zeros.py` to skip malformed zero entries and log warnings. If verification fails, the pipeline MUST halt with a clear error message.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Extremal Gap and Zero-Spacing Distributional Comparison (Priority: P2)

**Goal**: Compute distributional similarity between normalized prime spacings and zeta zero spacings using KS test and Cramér model.

**Independent Test**: Run `src/analysis/distribution_test.py` on small synthetic datasets; verify `results/correlation_results.json` contains KS statistic, p-value, and plots.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for normalization logic (log^2 p) in `tests/unit/test_analysis.py`
- [X] T017 [P] [US2] Unit test for KS test calculation in `tests/unit/test_analysis.py`

### Implementation for User Story 2

- [ ] T018b [US2] **Primary Analysis (FR-003)**: Implement sliding window analysis in `src/analysis/distribution_test.py` to compute *maximal* prime gap $g_{max}$ within **sliding windows** of length $W=10^6$. Use the `WINDOW_STEP` parameter defined in `config.py`. **Normalization**: Compute `normalized_max_gap = gap / log(p)^2` within this step. **Output**: Generate `data/processed/maximal_gaps.csv` with columns: `window_start, window_end, max_gap, normalized_max_gap`. **(Addresses FR-003, FR-004).**
- [X] T020 [US2] Implement empirical distribution calculation for normalized maximal gaps (from T018b) in `src/analysis/distribution_test.py`. <!-- FAILED: unspecified -->
- [X] T021b [US2] **Implement GUE Extreme Value CDF**: Implement the theoretical **GUE-derived extreme value CDF** for maximal gaps in `src/analysis/distribution_test.py`. **Formula**: Use `scipy.stats.tracy_widom.cdf(x, beta=2)` scaled by the normalization factor `log^2(p)` as defined in the spec's methodology. This CDF must be the integration of the pair-correlation distribution into an extreme value distribution as required by FR-004.
- [ ] T022 [US2] Perform Kolmogorov-Smirnov (KS) test comparing the *empirical maximal gap distribution* (from T020) against the GUE theoretical extreme value distribution (from T021b). **Output**: Generate `results/ks_test_results.json` with keys: `{ks_statistic, p_value, distribution_compared: "GUE_EVF", method: "scipy.stats.ks_2samp"}`. The primary comparison is against the GUE extreme value CDF.
- [X] T023 [US2] Implement Monte Carlo simulation using the Cramér model in `src/analysis/monte_carlo.py` to generate a null distribution of the KS statistic. **Output**: `results/cramer_null_distribution.json`. **(Addresses FR-005, SC-001).**
- [ ] T024 [US2] Calculate p-value for observed distributional alignment against the Cramér null distribution.
- [ ] T025 [US2] Generate visualization (CDF overlay of empirical vs. theoretical maximal gap distributions) using `matplotlib` and save to `results/correlation_plot.png` and `results/correlation_results.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Verification (Priority: P3)

**Goal**: Verify stability of results across window sizes and against synthetic Cramér data.

**Independent Test**: Run analysis with $W \in \{\text{small}, \text{medium}, \text{large}\}$; verify `results/robustness_report.md` lists KS statistics for each.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Integration test for sensitivity sweep in `tests/integration/test_robustness.py`

### Implementation for User Story 3

- [ ] T028 [US3] **Sensitivity Analysis**: Implement sensitivity analysis loop in `src/analysis/robustness.py` sweeping window size $W$ over a representative set of scales. **Execution Logic**: The task MUST re-run the full distributional analysis (T018b-T022) for *each* window size to generate the variation in KS statistics. **Output**: Generate `results/robustness_sweep.json` containing a list of objects with keys: `{window_size, ks_statistic, p_value, timestamp}`. (Traces to SC-002 and FR-006). **Dependency**: Requires T018b-T022 code implementation to be available.
- [ ] T029 [US3] Generate synthetic Cramér model dataset of comparable size in `data/null/cramer_sample.csv`
- [ ] T030 [US3] Perform distributional analysis on the synthetic Cramér dataset to establish a baseline
- [ ] T031 [US3] Compare observed KS statistics from prime data against the synthetic Cramér baseline and the permutation test results
- [ ] T032 [US3] Generate `results/robustness_report.md` summarizing KS statistics for each window size and the Cramér comparison

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `docs/` (including `quickstart.md`, `research.md`)
- [ ] T039 Code cleanup and refactoring
- [ ] T040 Performance optimization across all stories (ensure a reasonable runtime limit is met)
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
- **Phase 5 (Robustness)**: Depends on Phase 4 (US2) completion (requires analysis results)
- **Phase N (Polish)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1 (T012)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data from US1 and results from US2
 - **Critical**: Task T028 (US3) explicitly re-runs the analysis for each window size, ensuring it is self-contained but logically follows the definition of the analysis in US2. T028 requires the analysis logic defined in T018b-T022 to be complete.
- **Phase 6 (Topology)**: REMOVED. Topological tasks were removed due to lack of FR/SC authorization.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) EXCEPT T005 and T006 which both write to `src/utils/config.py` and must run sequentially (T005 then T006). T006 must run before T007 and T008a.
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

1. Team completes Setup + Foundational together (Note: T005 and T006 must be sequential; T006 before T007/T008a)
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
- **Data Integrity**: No fake data. All primes must be generated via sieve; all zeros must be from verified LMFDB/Odlyzko URLs. If verification fails, pipeline halts.
- **Constitution Compliance**: T008 and T015 use the correct constitutional path. T008a ensures the state file exists. T015 ensures verified sources are used.
- **Scope Correction**: Phase 6 (Topological Visualization) has been REMOVED. It lacked FR/SC authorization and constituted unapproved scope creep. The project now strictly adheres to FR-001 through FR-007.
- **Clarified Scope**: Task T018b is the sole implementation of FR-003 (Maximal Gaps) with explicit **sliding window** logic and **normalization**. The normalization step is now integrated into T018b to avoid redundancy (T019 removed).
- **Corrected Methodology**: Task T021b now correctly targets the GUE-derived extreme value CDF for maximal gaps, explicitly derived from the pair-correlation distribution required by FR-004.
- **Fallback Mechanism**: Task T011 has been updated to strictly enforce N=10^10. No fallback to N=10^9 is permitted; if the limit is exceeded, the run fails to ensure FR-001 compliance.
- **Parallelism Correction**: T005 and T006 both write to `src/utils/config.py` and cannot run in parallel. T006 must follow T005 and is NOT marked [P]. T006 must run before T007 and T008a.
- **Requirement Tracing**: Task T023b (Permutation Test) has been REMOVED as it was not mentioned in SC-001. The verification now strictly follows the Cramér model null distribution as defined in SC-001.
- **URL Configuration**: T015 reads URLs from the hardcoded canonical list (LMFDB/Odlyzko) defined in the spec, ensuring flexibility without external document dependencies.
- **Window Size Configuration**: T028 reads window sizes from `config.py` instead of hardcoding, ensuring flexibility.
- **Output Schema**: T018b, T022, and T028 now explicitly define their output file schemas to ensure executability.
- **Data Hygiene**: T012 outputs raw gaps; T018b normalizes them. This preserves raw data for re-normalization if needed.
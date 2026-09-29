# Tasks: Exploring the Relationship Between Prime Gaps and the Riemann Hypothesis

**Input**: Design documents from `/specs/001-exploring-the-relationship-between-prime/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Validation Rule**: Every task MUST cite a specific FR, SC, or US ID from `spec.md` or `plan.md`. Tasks without a spec anchor are invalid.

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e., US1, US2, US3)
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
- [X] T006 [US1] Implement deterministic random seed management in `src/utils/config.py` by defining a `GLOBAL_SEED` constant and ensuring all random generators use it. **Depends on T005 completion; NOT [P] as it writes to config.py which T005 also edits. T006 must run after T005.** (Addresses FR-001, SC-004)
- [X] T007 Create base data models in `src/utils/models.py` (PrimeGap, ZetaZero, WindowStats entities per spec)
- [X] T008 [US1] Implement checksumming logic in `src/utils/io.py` for updates to `state/projects/PROJ-548-exploring-the-relationship-between-prime.yaml`. (Addresses Constitution Principle III, V)
- [X] T008a [US1] **Initialize State File**: Run the state initialization script (dependent on T008) to create and initialize the file `state/projects/PROJ-548-exploring-the-relationship-between-prime.yaml` with the required schema, including an empty `artifact_hashes` map and `updated_at` timestamp, to satisfy Constitution Principle III (Data Hygiene) and Principle V (Versioning Discipline). **(Depends on T008 completion).**
- [X] T008b [P] **Update State Timestamp**: Implement logic in `src/utils/io.py` (or a dedicated state manager) to automatically update the `updated_at` timestamp in `state/projects/PROJ-548-exploring-the-relationship-between-prime.yaml` whenever any artifact is written or checksummed. **(Addresses Constitution Principle V).**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Generate primes up to 10^10 and ingest zeta zeros, ensuring memory safety and data validity.

**Independent Test**: Run `src/data/generate_primes.py` and `src/data/ingest_zeros.py` in isolation. **Conditional Verification**: If ingestion completes successfully, verify `data/raw/zeta_zeros.csv` exists and contains valid data. If the pipeline halts due to unreachable sources, the test for file existence is marked 'N/A' for that run, and the log must confirm the halt reason. Verify peak RAM < 7GB.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [P] [US1] Unit test for segmented sieve logic in `tests/unit/test_sieve.py` (verifies primality and chunk boundaries)
- [X] T010 [P] [US1] Integration test for data pipeline in `tests/integration/test_data_ingestion.py` (verifies file generation and memory limits)

### Implementation for User Story 1

- [X] T011 [US1] Implement segmented sieve algorithm in `src/data/generate_primes.py` to generate primes up to 10^10, processing in chunks to stay within 7GB RAM. **CRITICAL**: The task MUST generate primes up to $N=10^{10}$ as per FR-001. **Fallback**: If the runtime exceeds the CI time limit, the script MUST automatically switch to a "subsampled" mode ($N=10^9$) and log this limitation. **Output Labeling**: Fallback results MUST be saved to `data/raw/gaps_N10_9.csv` and metadata MUST explicitly label the dataset as "fallback_N10_9" to distinguish it from the primary target, satisfying SC-005. (Addresses FR-001, SC-004, SC-005)
- [ ] T012 [US1] Implement logic in `src/data/generate_primes.py` to compute consecutive prime gaps and stream results to `data/raw/gaps.csv` (format: `prime_before, prime_after, gap_size`). **Verification**: Verify output file schema matches spec Key Entities. **Status**: Active implementation required. **(Note: Normalization is handled in T018b).** (Addresses FR-001)
- [X] T015 [US1] **Implement Ingestion & Verification**: Implement logic in `src/data/ingest_zeros.py` that FIRST verifies the zeta zero source URL against a hardcoded canonical list defined in the task: 1) LMFDB API (`), 2) Odlyzko dataset. **Logic**: If the verified sources are completely unreachable, the pipeline MUST halt with a clear "Data Unavailable" error. If the source is partially accessible (some entries valid), the script MUST skip invalid/malformed entries, log a warning, and proceed with the remaining valid data. **(Addresses FR-002, US1, Edge Cases).**
- [X] T014 [US1] Implement data validation in `src/data/ingest_zeros.py` to skip malformed zero entries and log warnings. **(Depends on T015; runs on data fetched by T015).**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Extremal Gap and Zero-Spacing Distributional Comparison (Priority: P2)

**Goal**: Compute distributional similarity between normalized prime spacings and zeta zero spacings using KS test and Cramér model.

**Independent Test**: Run `src/analysis/distribution_test.py` on small synthetic datasets; verify `results/correlation_results.json` contains KS statistic, p-value, and plots.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for normalization logic (log^2 p) in `tests/unit/test_analysis.py`
- [X] T017 [P] [US2] Unit test for KS test calculation in `tests/unit/test_analysis.py`

### Implementation for User Story 2

- [ ] T018b [US2] **Sliding Window Max Gaps**: Implement sliding window analysis in `src/analysis/distribution_test.py` to compute *maximal* prime gap $g_{max}$ within **sliding windows** of length $W=10^6$. Use the `WINDOW_STEP` parameter defined in `config.py`. **Output**: Generate `data/processed/window_max_gaps.csv` with columns: `window_start, window_end, max_gap`. **(Addresses FR-003).**
- [ ] T018c [US2] **Normalization**: Implement normalization logic in `src/analysis/distribution_test.py` to compute `normalized_max_gap = max_gap / log(p)^2` using the data from T018b. **Output**: Generate `data/processed/normalized_max_gaps.csv`. **(Addresses FR-003).**
- [ ] T020 [US2] **Empirical Distribution Calculation**: Implement logic to calculate the empirical CDF of the normalized maximal gaps (from T018c) in `src/analysis/distribution_test.py`. **Output**: Generate `results/empirical_max_gap_cdf.csv`. **(Addresses FR-004).**
- [X] T021b [US2] **Implement GUE Extreme Value CDF**: Implement the theoretical **GUE-derived extreme value CDF** for maximal gaps in `src/analysis/distribution_test.py`. **Formula**: Use `scipy.stats.tracy_widom.cdf(x, beta=2)` scaled by the normalization factor `log^2(p)` as defined in the spec's methodology. This CDF must be the integration of the pair-correlation distribution into an extreme value distribution as required by FR-004.
- [ ] T022 [US2] Perform Kolmogorov-Smirnov (KS) test comparing the *empirical maximal gap distribution* (from T020) against the GUE theoretical extreme value distribution (from T021b). **Output**: Generate `results/ks_test_results.json` with keys: `{ks_statistic, p_value, distribution_compared: "GUE_EVF", method: "scipy.stats.ks_2samp"}`. **Note**: This computes the KS statistic required for T024. **(Addresses FR-004).**
- [X] T023 [US2] Implement Monte Carlo simulation using the Cramér model in `src/analysis/monte_carlo.py` to generate a null distribution of the KS statistic. **Output**: `results/cramer_null_distribution.json`. **(Addresses FR-005, SC-001).**
- [ ] T023b [US2] **Permutation Test**: Implement a permutation test in `src/analysis/distribution_test.py` that shuffles the gap sequence to establish an **independent, distinct null distribution** (distinct from the Cramér model). **Output**: Generate `results/permutation_null_distribution.json`. **Citation**: This satisfies Constitution Principle VI. **(Addresses Constitution Principle VI).**
- [ ] T024 [US2] **Calculate P-value**: Calculate the p-value for the observed distributional alignment. **Logic**: Compare the observed KS statistic from T022 against the distribution generated in T023 (Cramér null) and T023b (Permutation null). **Output**: Generate `results/cramer_p_value.json`. **(Addresses SC-001, FR-005).**
- [ ] T025 [US2] Generate visualization (CDF overlay of empirical vs. theoretical maximal gap distributions) using `matplotlib` and save to `results/correlation_plot.png` and update `results/correlation_results.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Verification (Priority: P3)

**Goal**: Verify stability of results across window sizes and against synthetic Cramér data.

**Independent Test**: Run analysis with $W \in \{\text{small}, \text{medium}, \text{large}\}$; verify `results/robustness_report.md` lists KS statistics for each.

### Tests for User Story 3 (MANDATORY per US3 Independent Test requirement) ⚠️

- [ ] T027 [US3] **Integration test for sensitivity sweep**: Implement and run the integration test in `tests/integration/test_robustness.py` to verify that the sensitivity sweep (T028) runs correctly and produces the expected `robustness_report.md`. **Status**: MANDATORY. (Addresses US3 Independent Test)

### Implementation for User Story 3

- [ ] T028a [US3] **Define Sweep Parameters**: Implement logic in `src/analysis/robustness.py` to define the set of window sizes $W$ to be swept across a range of magnitudes. **(Addresses FR-006).**
- [ ] T028b [US3] **Orchestrate Sweep Loop**: Implement the orchestration logic in `src/analysis/robustness.py` to re-run the full distributional analysis logic (T018b-T022) for *each* window size defined in T028a. **Requirement**: The analysis logic in T018b-T022 MUST be refactored into reusable functions to support this sweep. **Output**: Intermediate results for each window size. **(Addresses FR-006).**
- [ ] T028c [US3] **Aggregate Results**: Aggregate the results from T028b into a single JSON file. **Output**: Generate `results/robustness_sweep.json` containing a list of objects with keys: `{window_size, ks_statistic, p_value, timestamp}`. **(Addresses SC-002).**
- [ ] T029 [US3] **Generate Cramér Sample**: Generate synthetic Cramér model dataset of comparable size in `data/null/cramer_sample.csv`. **(Addresses FR-007).**
- [ ] T030 [US3] **Analyze Cramér Baseline**: Perform distributional analysis on the synthetic Cramér dataset (T029) to establish a baseline. **Output**: Generate `results/cramer_baseline_ks.json`. **(Addresses FR-007).**
- [ ] T031 [US3] **Compare Baselines**: Compare observed KS statistics from prime data (T028c) against the synthetic Cramér baseline (T030). **Output**: Generate `results/cramer_comparison.md`. **(Addresses SC-003).**
- [ ] T032 [US3] **Generate Robustness Report**: Generate `results/robustness_report.md` summarizing KS statistics for each window size and the Cramér comparison. **Schema**: Include a table with columns `window_size`, `ks_statistic`, `p_value`. **(Addresses SC-002).**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Topological Visualization & Narrative Context (Priority: P3 - Research Stage Review)

**Note**: Tasks T033 and T034 were removed. The spec defines FR-001 through FR-007 and SC-001 through SC-005, none of which authorize the generation of metaphors ("knot of information", "trees in a field") or narrative summaries. Generating such content constitutes unauthorized scope creep. The research narrative will be addressed in the final paper phase, not in the implementation tasks.

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
 - **Critical**: Task T028 (US3) explicitly re-runs the analysis for each window size, ensuring it is self-contained but logically follows the definition of the analysis in US2. T028 requires the analysis logic defined in T018b-T022 to be complete and modularized.
- **Phase N (Polish)**: NEW tasks T038-T042 address the specific research-stage review concerns regarding documentation and reproducibility, extending the scope beyond the original FR/SC list to incorporate the qualitative insights from the review.

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
5. Add Phase N (Polish) → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

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
- **Constitution Compliance**: T008a ensures the state file exists via script execution. T008b ensures timestamp updates. T015 ensures verified sources are used with explicit URLs.
- **Scope Correction**: Phase 6 (Topological Visualization) has been **REMOVED** to address unauthorized scope creep. The project now strictly adheres to FR-001 through FR-007 for the core pipeline.
- **Clarified Scope**: Task T018b, T018c, T020, T022, T024, T028c, T029, T030, T031, T032 now explicitly define their output file schemas to ensure executability.
- **Data Hygiene**: T012 outputs raw gaps to `data/raw/`; T018b-T018c normalize them to `data/processed/`. This preserves raw data for re-normalization if needed.
- **Reviewer Concerns Addressed**: Tasks T033 and T034 **REMOVED** to address the research-stage review concern regarding topological visualization and narrative context. T023b added for permutation test. T008a corrected for dependency. T015 corrected with explicit URLs. T027 marked MANDATORY. T011 corrected for fallback labeling.
- **URL Configuration**: T015 reads URLs from the hardcoded canonical list (LMFDB/Odlyzko) defined in the task, ensuring flexibility without external document dependencies.
- **Window Size Configuration**: T028a/b/c reads window sizes from `config.py` instead of hardcoding, ensuring flexibility.
- **Output Schema**: T018b, T018c, T020, T022, T024, T028c, T029, T030, T031, T032 now explicitly define their output file schemas to ensure executability.
- **Data Hygiene**: T012 outputs raw gaps to `data/raw/`; T018b-T018c normalize them to `data/processed/`. This preserves raw data for re-normalization if needed.
- **Corrected Methodology**: Task T023b now correctly targets the Permutation Test required by Constitution Principle VI.
- **Fallback Mechanism**: Task T011 has been updated to include explicit labeling for fallback results (N=10^9) to satisfy SC-005.
- **Partial Data Handling**: Task T015 corrected to handle partial data availability as per spec Edge Cases.
- **Requirement Tracing**: Task T023b (Permutation Test) added to satisfy Constitution Principle VI.
- **URL Configuration**: T015 reads URLs from the hardcoded canonical list (LMFDB/Odlyzko) defined in the task, ensuring flexibility without external document dependencies.
- **Window Size Configuration**: T028a/b/c reads window sizes from `config.py` instead of hardcoding, ensuring flexibility.
- **Output Schema**: T018b, T018c, T020, T022, T024, T028c, T029, T030, T031, T032 now explicitly define their output file schemas to ensure executability.
- **Data Hygiene**: T012 outputs raw gaps to `data/raw/`; T018b-T018c normalize them to `data/processed/`. This preserves raw data for re-normalization if needed.
- **Reviewer Concerns Addressed**: Tasks T033 and T034 **REMOVED** to address the research-stage review concern regarding topological visualization ("knot of information") and narrative context ("human story"). T023b added for permutation test. T008a corrected for dependency. T015 corrected with explicit URLs. T027 marked MANDATORY. T011 corrected for fallback labeling.
- **Spec/Plan Mismatch**: Note: A discrepancy exists between spec.md FR-004 (pair-correlation) and plan.md Methodological Correction (GUE extreme value CDF). Tasks align with the Plan's detailed implementation strategy. This discrepancy is flagged for kickback to the spec/plan authors.
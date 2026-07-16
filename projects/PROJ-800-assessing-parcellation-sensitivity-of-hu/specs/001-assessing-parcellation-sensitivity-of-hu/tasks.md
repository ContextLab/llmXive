# Tasks: Assessing Parcellation Sensitivity of Hub Resilience in Healthy Connectomes

**Input**: Design documents from `/specs/001-assessing-parcellation-sensitivity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- Paths shown below assume single project - adjusted based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (nibabel, nilearn, networkx, scikit-learn, pandas, numpy, matplotlib, seaborn, requests, scipy, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup directory structure: `data/raw`, `data/processed`, `data/results`, `code/`, `tests/`
- [X] T005 [P] Implement base logging and error handling utilities in `code/utils/logger.py`
- [X] T006 [P] Create configuration manager in `code/config.py` (handles paths, seeds, `default_hub_threshold` (fixed 0.10), and `sensitivity_sweep_values` ({0.08, 0.10, 0.12}) as distinct parameters explicitly for consumption by T033)
- [ ] T007 Create base data models/contracts in `code/models/` (AdjacencyMatrix, HubSet, CentralityScore)
- [X] T008 Setup random seed pinning utility in `code/utils/seed.py` (numpy, random)
- [X] T009 Implement data integrity check utility (checksums) in `code/utils/checksum.py`
- [ ] T024 [P] [US3] [FR-005] [FR-009] Implement spatial mapping function in `code/overlap.py` using binary masks and strict voxel containment check (no interpolation) to derive majority-vote overlap maps for aligning Schaefer/400 nodes to AAL-90. Output: `data/processed/mapping_schaefer_to_aal.npy` (format: lookup table mapping high-res indices to low-res indices).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Multi-Resolution Matrix Generation (Priority: P1) 🎯 MVP

**Goal**: Download raw fMRI data and generate three adjacency matrices (AAL-90, Schaefer-200, Schaefer) for a cohort [UNRESOLVED-CLAIM: c_23f9a25c — status=not_enough_info].

**Independent Test**: Verify existence of three distinct adjacency matrix files for a single subject, sharing raw source but differing in node count, within 7 GB RAM [UNRESOLVED-CLAIM: c_40f38d70 — status=not_enough_info].

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Unit test for atlas loading logic in `tests/unit/test_atlas_loader.py`
- [X] T011 [P] [US1] Integration test for matrix generation pipeline in `tests/integration/test_matrix_generation.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/download_data.py` to fetch raw fMRI NIfTI files from OpenNeuro dataset `ds000224` (HCP Young Adult) OR `ds000005` (OpenNeuro) for N=100 subjects; verify >= 100 usable subjects before processing [UNRESOLVED-CLAIM: c_2f8a0178 — status=not_enough_info]; handle missing/corrupted entries gracefully; fallback to alternate verified source if primary fails.
- [X] T016 [US1] Implement `code/parcellate.py` function `extract_timeseries_chunked` (memory-efficient extraction and shared matrix computation engine) that accepts raw fMRI paths and an atlas mask, outputs a raw time-series matrix, and computes the adjacency matrix. This task MUST complete before T013, T014, and T015. **Depends on: T012**.
- [X] T013 [P] [US1] Implement `code/parcellate.py` function `apply_aal3()` to load the AAL atlas mask, invoke the T016 engine to compute the adjacency matrix, and write the result to `data/processed/{subject}_aal90.npz`. **Depends on: T016**.
- [X] T014 [P] [US1] Implement `code/parcellate.py` function `apply_schaefer200()` to load the Schaefer_200Parcels_7Networks atlas mask, invoke the T016 engine to compute the adjacency matrix, and write the result to `data/processed/{subject}_schaefer200.npz`. **Depends on: T016**.
- [X] T015 [P] [US1] Implement `code/parcellate.py` function `apply_schaefer400()` to load the Schaefer_400Parcels_7Networks atlas mask, invoke the T016 engine to compute the adjacency matrix, and write the result to `data/processed/{subject}_schaefer400.npz`. **Depends on: T016**.
- [ ] T017 [US1] Implement validation logic to verify non-zero edge counts and correct node labels for all resolutions; output `data/results/validation_report.json`
- [ ] T018 [US1] Create `code/main.py` orchestration script to run download and parcellation sequentially

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Centrality Computation and Hub Definition (Priority: P2)

**Goal**: Calculate degree/betweenness centrality and define hubs as top [deferred] nodes.

**Independent Test**: Verify centrality calculation on a synthetic 5-node graph matches manual calculation; verify hub count is `floor(N * 0.10)`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Contract test for centrality output schema in `tests/contract/test_centrality_schema.py`
- [ ] T020 [P] [US2] Unit test for hub threshold logic in `tests/unit/test_hub_definition.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/centrality.py` function to compute Degree Centrality using NetworkX (CPU-only)
- [ ] T022 [P] [US2] Implement `code/centrality.py` function to compute Betweenness Centrality using NetworkX (CPU-only, optimized for sparse graphs)
- [ ] T023 [US2] Implement hub definition logic: `floor(N * 0.10)` cutoff for each resolution in `code/centrality.py`, reading the threshold from the configuration manager (T006). **Depends on: T021, T022, T006**.
- [ ] T025 [US2] Generate CSV outputs for centrality scores and hub flags for all subjects and resolutions; output `data/results/{subject}_{resolution}_centrality.csv`. **Depends on: T021, T022, T023, T024**.
- [ ] T026 [US2] Add validation to ensure no missing values in centrality outputs

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Quantification and Statistical Validation (Priority: P3)

**Goal**: Compute overlap indices, Spearman correlations, permutation tests, and visualizations.

**Independent Test**: Run on randomized node labels; verify p-value distribution is uniform and verify p-value distribution is uniform and Type I error < 5% [UNRESOLVED-CLAIM: c_f35d30a7 — status=not_enough_info].

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for Jaccard/Dice calculation in `tests/unit/test_overlap_metrics.py`
- [ ] T028 [P] [US3] Unit test for permutation test logic (randomization control) in `tests/unit/test_permutation_test.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/overlap.py` function to compute Jaccard and Dice coefficients between hub sets
- [ ] T030 [P] [US3] Implement `code/overlap.py` function to compute Spearman rank correlation after spatial mapping (using `data/processed/mapping_schaefer_to_aal.npy` from T024). **Depends on: T024**.
- [ ] T031 [US3] Implement permutation test engine in `code/overlap.py` with a **hard minimum of 1,000 iterations [UNRESOLVED-CLAIM: c_7dcf3017 — status=not_enough_info] ** as required by FR-006. If the A fixed time limit for the Confidence Interval (CI) will be established. is approached, the task must log a critical warning and **fail the run** rather than proceed with fewer iterations, ensuring statistical power is not compromised. Output `data/results/permutation_pvalue.csv`. **Depends on: T023, T024, T029**.
- [ ] T032 [US3] Implement 'Expected Random Overlap' baseline calculation (compare observed Jaccard/Dice vs. expected random overlap for matching cardinality; output as supplementary metric to support FR-004)
- [ ] T032a [US3] [FR-004] Update `specs/001-assessing-parcellation-sensitivity/data-model.md` to include schema for 'Expected Random Overlap' metric.
- [ ] T033 [US3] Implement sensitivity analysis module `code/sensitivity.py` to sweep thresholds across the range defined in T006 ({0.08, 0.10, 0.12}) AND perform fixed-cardinality comparisons (compare top N nodes where N=min cardinality across resolutions); output to `data/results/sensitivity_sweep.csv` (columns: threshold, jaccard, dice, expected_random, fixed_cardinality_jaccard). **Depends on: T006, T023, T029, T032**.
- [ ] T034 [P] [US3] Implement `code/visualize.py` to generate heatmaps of centrality correlation
- [ ] T035 [P] [US3] Implement `code/visualize.py` to generate Venn diagrams of hub overlap
- [ ] T036 [US3] Implement final report generation script aggregating all statistics and plots into `data/results/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `README.md` and `docs/` (explain spatial mapping and threshold logic)
- [ ] T038 Code cleanup and refactoring (remove unused imports, optimize memory usage)
- [ ] T039 Performance optimization: parallelize subject processing where safe (e.g., centrality calculation per subject)
- [ ] T040 [P] Additional unit tests for edge cases (N not divisible by 10, corrupted files) in `tests/unit/`
- [ ] T041 Run full pipeline integration test on a subset (N=5) to verify end-to-end flow within CI time limits
- [ ] T042 Run quickstart.md validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (matrices)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (hub sets) and T024 (spatial mapping)

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
- **Phase 3 Specific**: T013, T014, and T015 are parallel *only after* T016 completes. T016 is a sequential prerequisite for the parallel block.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for atlas loading logic in tests/unit/test_atlas_loader.py"
Task: "Integration test for matrix generation pipeline in tests/integration/test_matrix_generation.py"

# Launch all models for User Story 1 together:
Task: "Implement code/download_data.py"

# Sequence: T012 -> T016 -> [T013, T014, T015]
# T016 must complete before the parallel block [T013, T014, T015] can start.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (T012 -> T016 -> T013-T015)
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
 - Developer A: User Story 1 (Data & Matrices) - Note: T016 must finish before T013-T015
 - Developer B: User Story 2 (Centrality & Hubs)
 - Developer C: User Story 3 (Stats & Viz)
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
- **Constraint**: All tasks must run on CPU-only CI with limited computational resources (multiple cores, constrained RAM, 6h limit). No GPU, no 8-bit quantization, no large LLMs.
- **Data Integrity**: All data must be fetched from real sources (OpenNeuro/HCP). No synthetic/fake data generation for input.
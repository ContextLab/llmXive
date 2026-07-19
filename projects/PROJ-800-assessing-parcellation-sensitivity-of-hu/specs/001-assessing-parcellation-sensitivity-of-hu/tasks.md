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

- [ ] T001 Create project structure per implementation plan by executing `mkdir -p projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/data/{raw,processed,results} projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/{code,tests}` and creating `projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/requirements.txt`, `README.md`, and `projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/code/__init__.py`.
- [ ] T002 [P] Initialize Python 3.11 project with `requirements.txt` (nibabel, nilearn, networkx, scikit-learn, pandas, numpy, matplotlib, seaborn, requests, scipy, pytest).
- [ ] T003 [P] Configure linting and formatting tools by creating `.ruff.toml` with `[lint]` rules (E402, F401, W605) and `pyproject.toml` with `[tool.black]` section (line-length=88, target-version=['py311']).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup directory structure by executing `mkdir -p data/raw data/processed data/results code tests` at the project root.
- [ ] T005 [P] Implement base logging and error handling utilities in `code/utils/logger.py` (setup `logging` module with file and console handlers, JSON formatter).
- [ ] T006 [P] Create configuration manager in `code/config.py` (handles paths, seeds, `default_hub_threshold` (baseline value 0.10), and `sensitivity_sweep_values` ({0.08, 0.10, 0.12}) as distinct parameters. The `default_hub_threshold` serves as the baseline for single-run analysis, while `sensitivity_sweep_values` defines the range for the mandatory sensitivity sweep (FR-008). These parameters are explicitly for consumption by T033).
- [ ] T007 Create base data models/contracts in `code/models/` by defining classes: `AdjacencyMatrix` (fields: `matrix: np.ndarray`, `atlas_name: str`, `node_labels: list`), `HubSet` (fields: `node_ids: list`, `metric: str`, `threshold: float`), `CentralityScore` (fields: `node_id: int`, `degree: float`, `betweenness: float`).
- [ ] T008 [P] Setup random seed pinning utility in `code/utils/seed.py` (numpy, random) (functions: `set_seed(seed: int)`).
- [ ] T009 [P] Implement data integrity check utility (checksums) in `code/utils/checksum.py` (functions: `calculate_sha256(file_path: str)`).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Multi-Resolution Matrix Generation (Priority: P1) 🎯 MVP

**Goal**: Download raw fMRI data and generate three adjacency matrices (AAL-90, Schaefer-200, Schaefer-400) for a cohort of N=100 healthy adults from OpenNeuro/HCP.

**Independent Test**: Verify existence of three distinct adjacency matrix files for a single subject, sharing raw source but differing in node count, within 7 GB RAM.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T010 [P] [US1] Unit test for atlas loading logic in `tests/unit/test_atlas_loader.py` (verify atlas files load correctly).
- [ ] T011 [P] [US1] Integration test for matrix generation pipeline in `tests/integration/test_matrix_generation.py` (verify end-to-end flow on 1 subject).

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/download_data.py` to fetch raw fMRI NIfTI files from OpenNeuro dataset `ds000224` (HCP Young Adult) OR `ds000005` (OpenNeuro) for N=100 subjects; implement logic to **verify >= 100 usable subjects** before processing; handle missing/corrupted entries gracefully; implement **fallback to alternate verified source** if primary fails; write checksums to `state/data_checksums.yaml`. **Depends on: T009**.
- [ ] T016 [US1] Implement `code/parcellate.py` function `extract_timeseries_chunked` (memory-efficient extraction and shared matrix computation engine) that accepts raw fMRI paths and an atlas mask, outputs a raw time-series matrix, and computes the adjacency matrix. This task MUST complete before T013, T014, and T015. **Depends on: T012**.
- [ ] T013 [P] [US1] Implement `code/parcellate.py` function `apply_aal3()` to load the AAL atlas mask, invoke the T016 engine to compute the adjacency matrix, and write the result to `data/processed/{subject}_aal90.npz`. **Depends on: T016**.
- [ ] T014 [P] [US1] Implement `code/parcellate.py` function `apply_schaefer200()` to load the Schaefer_200Parcels_7Networks atlas mask, invoke the T016 engine to compute the adjacency matrix, and write the result to `data/processed/{subject}_schaefer200.npz`. **Depends on: T016**.
- [ ] T015 [P] [US1] Implement `code/parcellate.py` function `apply_schaefer400()` to load the Schaefer_400Parcels_7Networks atlas mask, invoke the T016 engine to compute the adjacency matrix, and write the result to `data/processed/{subject}_schaefer400.npz`. **Depends on: T016**.
- [ ] T017 [US1] Implement validation logic to verify non-zero edge counts and correct node labels for all resolutions; output `data/results/validation_report.json` with exact keys: `subject_id` (str), `node_counts` (dict: {atlas: int}), `edge_counts` (dict: {atlas: int}), `status` (str: 'valid'/'invalid'). **Depends on: T013, T014, T015**.
- [ ] T018 [US3] Create `code/main.py` orchestration script with `argparse` for `--subjects` and `--atlas` arguments, calling T012, T016, T013-T015 in sequence; return exit code 0 on success, 1 on failure. **Depends on: T012, T016, T013, T014, T015**.
- [ ] T024 [P] [US3] [FR-009] Implement spatial mapping function in `code/overlap.py` using binary masks to calculate the **percentage of voxel overlap** (proportional calculation) for each high-resolution node against low-resolution atlas regions, assigning the high-res node to the low-res region with the majority vote. Output: `data/processed/mapping_schaefer_to_aal.npy` (format: lookup table mapping high-res indices to low-res indices). **Depends on: T013, T014, T015**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Centrality Computation and Hub Definition (Priority: P2)

**Goal**: Calculate degree/betweenness centrality and define hubs as top [deferred] nodes.

**Independent Test**: Verify centrality calculation on a synthetic 5-node graph matches manual calculation; verify hub count is determined by a proportional threshold of the total network size $N$, consistent with scale-free network models (e.g., Barabási & Albert, 1999)..

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Contract test for centrality output schema in `tests/contract/test_centrality_schema.py` (validate CSV columns: `node_id` (int), `degree` (float), `betweenness` (float), `is_hub` (bool)).
- [ ] T020 [P] [US2] Unit test for hub threshold logic in `tests/unit/test_hub_definition.py` (test cases: verify `floor(90 * 0.10) == 9`, `floor(200 * 0.10) == 20`, `floor(400 * 0.10) == 40`; verify that the function raises an error for negative thresholds).

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/centrality.py` function `compute_degree_centrality(matrix: np.ndarray) -> np.ndarray` to compute Degree Centrality using NetworkX (CPU-only); return 1D array of scores indexed by node ID. **Depends on: T013, T014, T015**.
- [ ] T022 [P] [US2] Implement `code/centrality.py` function `compute_betweenness_centrality(matrix: np.ndarray) -> np.ndarray` to compute Betweenness Centrality using NetworkX (CPU-only, optimized for sparse graphs); return 1D array of scores indexed by node ID. **Depends on: T013, T014, T015**.
- [ ] T023 [US2] Implement hub definition logic: function `define_hubs(scores: np.ndarray, threshold: float) -> np.ndarray` to compute `floor(N * threshold)` cutoff for each resolution; read threshold from config (T006) but **accept variable threshold parameter** to support sensitivity analysis (FR-008); output binary mask array. **Depends on: T021, T022, T006**.
- [ ] T025 [US2] Generate CSV outputs for centrality scores and hub flags for all subjects and resolutions; output `data/results/{subject}_{resolution}_centrality.csv` with columns: `node_id`, `centrality_score`, `is_hub`. **Depends on: T021, T022, T023**.
- [ ] T026 [US2] Add validation to ensure no missing values in centrality outputs; implement in generation script (T025) to **raise exception** if NaN values found; log error to `code/utils/logger.py`. **Depends on: T025**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Quantification and Statistical Validation (Priority: P3)

**Goal**: Compute overlap indices, Spearman correlations, permutation tests, and visualizations.

**Independent Test**: Run on randomized node labels; verify p-value distribution is uniform and Type I error < 5%.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for Jaccard/Dice calculation in `tests/unit/test_overlap_metrics.py` (test inputs: Set A={1,2,3}, Set B={2,3,4}; expected outputs: Jaccard=0.5, Dice=0.66).
- [ ] T028 [P] [US3] Unit test for permutation test logic (randomization control) in `tests/unit/test_permutation_test.py` (test cases: A fixed number of iterations will be performed with a deterministic random seed., verify p-value distribution is uniform).

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/overlap.py` function `def compute_overlap(set_a: set, set_b: set) -> dict: {jaccard: float, dice: float}` to compute Jaccard and Dice coefficients between hub sets; return dict `{jaccard: float, dice: float}`. **Depends on: T023**.
- [ ] T030 [P] [US3] Implement `code/overlap.py` function `compute_spearman_correlation(ranks_a: np.ndarray, ranks_b: np.ndarray) -> tuple` to compute Spearman rank correlation after spatial mapping (using `data/processed/mapping_schaefer_to_aal.npy` from T024); input: two 1D arrays of ranks; output: `(correlation, p-value)` tuple. **Note**: This implements the correlation component of the "Spatial Spin Test" mentioned in the Plan. **Depends on: T024, T023**.
- [ ] T031 [US3] Implement permutation test engine in `code/overlap.py` with a **minimum of 1,000 iterations** as required by FR-006; if the 6-hour CI time limit is approached, **default to a reduced number of iterations (minimum 500) and log a warning** to ensure analysis completes; output `data/results/permutation_pvalue.csv` with columns: `iteration`, `overlap_stat`, `p_value`. **Note**: This implements the significance testing component of the "Spatial Spin Test" mentioned in the Plan. **Depends on: T023, T024, T029**.
- [ ] T033 [US3] Implement sensitivity analysis module `code/sensitivity.py` to sweep thresholds across the range defined in T006 ({0.08, 0.10, 0.12}) AND perform fixed-cardinality comparisons (compare top N nodes where N=min cardinality across resolutions); output to `data/results/sensitivity_sweep.csv` (columns: threshold, jaccard, dice, fixed_cardinality_jaccard). **Depends on: T006, T023, T029**.
- [ ] T034 [P] [US3] Implement `code/visualize.py` function `generate_heatmap(data: np.ndarray, title: str)` to generate heatmaps of centrality correlation using `seaborn.heatmap`; output file naming convention: `data/results/heatmap_{resolution_pair}.png`. **Depends on: T030**.
- [ ] T035 [P] [US3] Implement `code/visualize.py` function `generate_venn_diagram(set_a: set, set_b: set, title: str)` to generate Venn diagrams of hub overlap using `matplotlib_venn`; output file path: `data/results/venn_{resolution_pair}.png`. **Depends on: T029**.
- [ ] T036 [US3] Implement final report generation script aggregating all statistics and plots into `data/results/summary_report.md` (Markdown format); include sections: "Methodology", "Results", "Sensitivity Analysis", "Visualizations"; aggregate statistics from `data/results/` CSVs. **Depends on: T031, T033, T034, T035**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `README.md` and `docs/` (add section "Spatial Mapping" explaining the majority-vote method and threshold logic).
- [ ] T038 Code cleanup and refactoring (remove unused imports from all files in `code/`, optimize memory usage in `code/parcellate.py`).
- [ ] T039 Performance optimization: parallelize subject processing where safe (e.g., centrality calculation per subject); target metric: reduce RAM or runtime by a significant margin.
- [ ] T040 [P] Additional unit tests for edge cases in `tests/unit/` (test cases: N=99, N=101, corrupted file with 0 bytes, expected behavior: skip with warning or raise error).
- [ ] T041 Run full pipeline integration test on a subset (N=5) to verify end-to-end flow within CI time limits; execute command `python code/main.py --subjects 5`; verify all output files exist and are non-empty.
- [ ] T042 Run quickstart.md validation (execute `quickstart.md` commands and verify no errors; success criteria: all commands complete with exit code 0).

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
- **Revision Note**: T031 explicitly enforces the [deferred] iteration minimum for the permutation test (FR-006) but mandates graceful degradation (min 500 iterations + warning) if time constraints are threatened, resolving the previous hard-fail contradiction. T024 now correctly implements majority-vote via percentage overlap calculation. T032 and T032a (unverified 'Expected Random Overlap') have been removed to align with Spec FRs.
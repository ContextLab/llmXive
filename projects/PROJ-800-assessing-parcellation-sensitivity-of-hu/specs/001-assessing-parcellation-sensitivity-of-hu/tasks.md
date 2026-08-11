# Tasks: Assessing Parcellation Sensitivity of Hub Resilience in Healthy Connectomes

**Input**: Design documents from `/specs/001-assessing-parcellation-sensitivity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are REQUIRED for this project to ensure TDD compliance.

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

- [ ] T001 [P] Create project directory structure by executing `mkdir -p projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/data/{raw,processed,results} projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/{code,tests}`.
- [ ] T002 [P] Create `projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/requirements.txt` containing: `nibabel`, `nilearn`, `networkx`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `requests`, `scipy`, `pytest`, `huggingface_hub`.
- [ ] T003 [P] Create `projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/README.md` with project title, branch, and brief description.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement base logging and error handling utilities in `code/utils/logger.py` (setup `logging` module with file and console handlers, JSON formatter).
- [ ] T006 [P] Create configuration manager in `code/config.py` (handles paths, seeds, `default_hub_threshold` (0.10), and `sensitivity_sweep_values` ({0.05, 0.10, 0.15, 0.20}) as distinct parameters for the mandatory [deferred] to [deferred] sweep range).
- [ ] T007 Create base data models/contracts in `code/models/` by defining classes: `AdjacencyMatrix` (fields: `matrix: np.ndarray`, `atlas_name: str`, `node_labels: list`), `HubSet` (fields: `node_ids: list`, `metric: str`, `threshold: float`), `CentralityScore` (fields: `node_id: int`, `degree: float`, `betweenness: float`).
- [ ] T008 [P] Setup random seed pinning utility in `code/utils/seed.py` (numpy, random) (functions: `set_seed(seed: int)`).
- [ ] T009 [P] Implement data integrity check utility (checksums) in `code/utils/checksum.py` (functions: `calculate_sha256(file_path: str)`).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Multi-Resolution Matrix Generation (Priority: P1) 🎯 MVP

**Goal**: Download raw fMRI data and generate three adjacency matrices (AAL-90, Schaefer-200, Schaefer-400) for a cohort of N=20 healthy adults from OpenNeuro/HCP [UNRESOLVED-CLAIM: c_36881ddf — status=not_enough_info].

**Independent Test**: Verify existence of three distinct adjacency matrix files for a single subject, sharing raw source but differing in node count, within 7 GB RAM [UNRESOLVED-CLAIM: c_9a5e4658 — status=not_enough_info].

### Tests for User Story 1 (REQUIRED - TDD) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T010 [P] [US1] Unit test for atlas loading logic in `tests/unit/test_atlas_loader.py`. Test case: Load AAL atlas from `data/raw/atlases/AAL.nii` (or simulated path) and assert `loaded.shape == (90, 90)` and `loaded.dtype == int`.
- [ ] T011 [P] [US1] Integration test for matrix generation pipeline in `tests/integration/test_matrix_generation.py`. Test case: Load a pre-downloaded subject NIfTI from `tests/fixtures/subject_001.nii.gz`, apply AAL mask, and assert output matrix shape is `(90, 90)` and contains non-zero values.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/download_data.py` to fetch raw fMRI NIfTI files from OpenNeuro dataset `ds000114` (HCP S1200) for N=20 subjects. **Fallback**: If ds000114 is inaccessible, fetch from ABCD Study (ds000014). **Logic**: Verify >= 20 usable subjects before processing. Handle missing/corrupted entries by skipping and logging. **Constraint**: Do NOT use ds000224. If raw processing is infeasible, load pre-computed adjacency matrices from a verified source; otherwise fail loudly. Write checksums to `state/data_checksums.yaml`. **Depends on: T009**.
- [ ] T016 [US1] Implement `code/parcellate.py` function `extract_timeseries_chunked` (memory-efficient extraction and shared matrix computation engine) that accepts raw fMRI paths and an atlas mask, outputs a raw time-series matrix, and computes the adjacency matrix. This task MUST complete before T013, T014, and T015. **Depends on: T012**.
- [ ] T013 [P] [US1] Implement `code/parcellate.py` function `apply_aal3()` to load the AAL atlas mask, invoke the T016 engine to compute the adjacency matrix, and write the result to `data/processed/{subject}_aal90.npz`. **Depends on: T016**.
- [ ] T014 [P] [US1] Implement `code/parcellate.py` function `apply_schaefer200()` to load the Schaefer_200Parcels_7Networks atlas mask, invoke the T016 engine to compute the adjacency matrix, and write the result to `data/processed/{subject}_schaefer200.npz`. **Depends on: T016**.
- [ ] T015 [P] [US1] Implement `code/parcellate.py` function `apply_schaefer400()` to load the Schaefer_400Parcels_7Networks atlas mask, invoke the T016 engine to compute the adjacency matrix, and write the result to `data/processed/{subject}_schaefer400.npz`. **Depends on: T016**.
- [ ] T017 [US1] Implement validation logic to verify non-zero edge counts and correct node labels for all resolutions; output `data/results/validation_report.json` with exact keys: `subject_id` (str), `node_counts` (dict: {atlas: int}), `edge_counts` (dict: {atlas: int}), `status` (str: 'valid'/'invalid'). **Depends on: T013, T014, T015**.
- [ ] T018 [US1] Implement `code/main.py` orchestration script with `argparse` for `--subjects` and `--atlas` arguments, calling T012, T016, T013-T015 in sequence; return exit code 0 on success, 1 on failure. **Depends on: T012, T016, T013, T014, T015**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Centrality Computation and Hub Definition (Priority: P2)

**Goal**: Calculate degree/betweenness centrality and define hubs as top `floor(N * 0.10)` nodes.

**Independent Test**: Verify centrality calculation on a synthetic 5-node graph matches manual calculation; verify hub count is determined by a proportional threshold of the total network size $N$, consistent with scale-free network models (e.g., Barabási & Albert, year)..

### Tests for User Story 2 (REQUIRED - TDD) ⚠️

- [ ] T019 [P] [US2] Contract test for centrality output schema in `tests/contract/test_centrality_schema.py` (validate CSV columns: `node_id` (int), `degree` (float), `betweenness` (float), `is_hub` (bool)).
- [ ] T020 [P] [US2] Unit test for hub threshold logic in `tests/unit/test_hub_definition.py` (test cases: verify `floor(90 * 0.10) == 9`, `floor(200 * 0.10) == 20`, `floor(400 * 0.10) == 40`; verify that the function raises an error for negative thresholds).

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/centrality.py` function `compute_degree_centrality(matrix: np.ndarray) -> np.ndarray` to compute Degree Centrality using NetworkX on the **weighted adjacency matrix** (CPU-only); return 1D array of scores indexed by node ID. **Depends on: T013, T014, T015**.
- [ ] T022 [P] [US2] Implement `code/centrality.py` function `compute_betweenness_centrality(matrix: np.ndarray) -> np.ndarray` to compute Betweenness Centrality using NetworkX on the **binary graph derived by thresholding the weighted matrix** (CPU-only, optimized for sparse graphs); return 1D array of scores indexed by node ID. **Depends on: T013, T014, T015**.
- [ ] T023 [US2] Implement hub definition logic: function `define_hubs(scores: np.ndarray, threshold: float) -> np.ndarray` to compute `floor(N * threshold)` cutoff for each resolution; read threshold from config (T006) but **accept variable threshold parameter** to support sensitivity analysis (FR-008); output binary mask array. **Depends on: T021, T022, T006**.
- [ ] T025 [US2] Generate CSV outputs for centrality scores and hub flags for all subjects and resolutions; output `data/results/{subject}_{resolution}_centrality.csv` with columns: `node_id`, `centrality_score`, `is_hub`. **Depends on: T021, T022, T023**.
- [ ] T026 [US2] Add validation to ensure no missing values in centrality outputs; implement in generation script (T025) to **raise exception** if NaN values found; log error to `code/utils/logger.py`. **Depends on: T025**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Quantification and Statistical Validation (Priority: P3)

**Goal**: Compute Excess Overlap indices, Spearman correlations, Spatial Spin Test, and visualizations.

**Independent Test**: Run on randomized node labels; verify p-value distribution is uniform and {{claim:c_4f18774c}} (Wikipedia: Type I and type II errors, https://en.wikipedia.org/wiki/Type_I_and_type_II_errors).

### Tests for User Story 3 (REQUIRED - TDD) ⚠️

- [ ] T027 [P] [US3] Unit test for Jaccard/Dice calculation in `tests/unit/test_overlap_metrics.py` (test inputs: Set A={1,2,3}, Set B={2,3,4}; expected outputs: Jaccard=0.5, Dice=0.66 [UNRESOLVED-CLAIM: c_48c9b075 — status=not_enough_info]).
- [ ] T028 [P] [US3] Unit test for permutation test logic (randomization control) in `tests/unit/test_permutation_test.py` (test cases: A fixed number of iterations will be performed with a deterministic random seed., verify p-value distribution is uniform).

### Implementation for User Story 3

- [ ] T024 [P] [US3] [FR-009] Implement spatial mapping function in `code/overlap.py` using binary masks to calculate the **volume-weighted proportion of intersection** (weighted-vote method) for each high-resolution node against low-resolution atlas regions. Input: Atlas mask files from `data/raw/atlases/` (AAL.nii, Schaefer200.nii, Schaefer400.nii). Assign the high-res node to the low-res region with the largest intersection volume; if tied, use the **largest absolute intersection volume** as the tie-breaker. Output: `data/processed/mapping_schaefer_to_aal.npy` (format: lookup table mapping high-res indices to low-res indices). **Depends on: T013, T014, T015**.
- [ ] T024a [P] [US3] [FR-009, FR-005] Implement aggregation logic in `code/overlap.py`: function `aggregate_centrality(high_res_scores: np.ndarray, mapping: np.ndarray, low_res_node_count: int) -> np.ndarray`. Logic: Map high-res scores to low-res regions via `mapping`; compute mean score for each low-res region; assign 0 to unmapped low-res nodes. Output: Aligned centrality vector. **Depends on: T024**.
- [ ] T029 [P] [US3] Implement `code/overlap.py` function `compute_excess_overlap(set_a: set, set_b: set, total_nodes: int, k: int) -> float` to compute Excess Overlap index (observed overlap minus expected overlap from hypergeometric distribution) as per FR-004. **Validation**: Assert `total_nodes` equals the node count of the lower-resolution atlas before calculation. **Depends on: T023, T024**.
- [ ] T029a [P] [US3] Implement `code/overlap.py` function `compute_overlap_coefficients(set_a: set, set_b: set) -> dict` to calculate and output **Jaccard and Dice coefficients** for hub set validation, satisfying Constitution Principle VII. Output: `data/results/overlap_coefficients.csv`. **Depends on: T023**.
- [ ] T030 [P] [US3] [FR-005] Implement `code/overlap.py` function `compute_spearman_correlation(ranks_a: np.ndarray, ranks_b: np.ndarray) -> tuple` to compute Spearman rank correlation after spatial mapping (using `data/processed/mapping_schaefer_to_aal.npy` from T024 and aggregated vectors from T024a); input: two 1D arrays of ranks; output: `(correlation, p-value)` tuple. **Note**: This is a distinct metric from the Spatial Spin Test (T031a). **Depends on: T024, T024a, T023**.
- [ ] T031 [US3] Implement Volumetric Spatial Spin Test engine in `code/overlap.py` with a **default of a sufficient number of iterations** as required by FR-006; **IF** the estimated runtime exceeds a substantial duration (monitored via `tracemalloc` or time tracking), **fallback to a sufficient number of iterations [UNRESOLVED-CLAIM: c_2414f524 — status=not_enough_info]** and log a warning to ensure analysis completes; output `data/results/spin_test_pvalue.csv` with columns: `iteration`, `overlap_stat`, `p_value`. **Note**: This implements the significance testing component of the "Spatial Spin Test" mentioned in the Plan. **Depends on: T023, T024, T024a, T029**.
- [ ] T033 [US3] Implement sensitivity analysis module `code/sensitivity.py` to sweep thresholds across the range defined in T006 ({0.05, 0.10, 0.15, 0.20}) AND perform fixed-cardinality comparisons (compare top N nodes where N=min cardinality across resolutions); output to `data/results/sensitivity_sweep.csv` (columns: threshold, excess_overlap, jaccard, dice, fixed_cardinality_jaccard). **Depends on: T006, T023, T029, T029a, T024a**.
- [ ] T034 [P] [US3] Implement `code/visualize.py` function `generate_heatmap(data: np.ndarray, title: str)` to generate heatmaps of centrality correlation using `seaborn.heatmap`; output file naming convention: `data/results/heatmap_{resolution_pair}.png`. **Depends on: T030**.
- [ ] T035 [P] [US3] Implement `code/visualize.py` function `generate_venn_diagram(set_a: set, set_b: set, title: str)` to generate Venn diagrams of hub overlap using `matplotlib_venn`; output file path: `data/results/venn_{resolution_pair}.png`. **Depends on: T029, T029a**.
- [ ] T036 [US3] Implement final report generation script aggregating all statistics and plots into `data/results/summary_report.md` (Markdown format); include sections: "Methodology", "Results", "Sensitivity Analysis", "Visualizations"; aggregate statistics from `data/results/` CSVs. **Depends on: T031, T033, T034, T035**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `README.md` and `docs/` (add section "Spatial Mapping" explaining the weighted-vote method and threshold logic).
- [ ] T038 Code cleanup and refactoring (remove unused imports from all files in `code/`, optimize memory usage in `code/parcellate.py`).
- [ ] T039 [P] Performance optimization: parallelize subject processing where safe (e.g., centrality calculation per subject); target metric: reduce peak RAM by [deferred] or complete N=20 in < 4 hours [UNRESOLVED-CLAIM: c_076b903f — status=refuted].
- [ ] T040 [P] Additional unit tests for edge cases in `tests/unit/` (test cases: N=99, N=101, corrupted file with bytes, expected behavior: skip with warning or raise error).
- [ ] T041 [P] Run quickstart.md validation (execute `quickstart.md` commands and verify no errors; success criteria: all commands complete with exit code 0).
- [ ] T042 [P] [FR-010] Implement `code/utils/update_state.py` to update the project state file (`state/projects/PROJ-800-assessing-parcellation-sensitivity-of-hu.yaml`) with content hashes for all generated artifacts and a timestamp after each research-stage artifact change. **Depends on: T005**.
- [ ] T043 [P] [FR-011] Implement `code/validators/validate_citations.py` to integrate the Reference-Validator Agent; ensure all citations in `data/results/summary_report.md` are verified before artifact write; block write if any citation is unverified. **Depends on: T036**.
- [ ] T045 [US3] [SC-005] Run full pipeline integration test on N=20 subjects with timing measurement; execute command `python code/main.py --subjects 20`; verify total runtime < 6 hours [UNRESOLVED-CLAIM: c_c7db9df8 — status=not_enough_info]; record timing in `data/results/performance_log.json`. **Depends on: T018**.

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
- **Data Integrity**: All data must be fetched from real sources (OpenNeuro/HCP ds000114 or ABCD). No synthetic/fake data generation for input. **T012** explicitly allows loading pre-computed matrices if raw processing is infeasible, but forbids synthetic fallback; the pipeline must fail loudly if neither real nor pre-computed data is available.
- **Revision Note**: T031 explicitly enforces the 1000 iteration default with a strict fallback to 500 if time constraints are threatened, resolving the previous hard-fail contradiction. T024 now correctly implements weighted-vote via volume-weighted proportion with tie-breaker logic. T024a added to satisfy FR-009 aggregation requirements. T029a added to satisfy Constitution Principle VII (Jaccard/Dice). T006 and T033 updated to cover full [deferred]-20% sweep range. T021/T022 updated to distinguish weighted vs binary graph inputs. T012 updated to include pre-computed fallback logic and remove ds000224. T004 removed as duplicate. T010/T011 marked as required for TDD with specific assertions. T045 added for N=20 performance verification. T030 renamed to clarify it is separate from Spatial Spin Test. T031a added for Spatial Spin Test engine.
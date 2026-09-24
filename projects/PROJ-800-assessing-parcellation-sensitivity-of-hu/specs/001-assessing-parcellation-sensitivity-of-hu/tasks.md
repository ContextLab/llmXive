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

- [ ] T001 [P] Create project directory structure by executing `mkdir -p projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/data/{raw,processed,results} projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/{code,tests}`. **Verification**: Execute `ls -R projects/PROJ-800-assessing-parcellation-sensitivity-of-hu` and capture the output to `state/setup_verification.log` to confirm all directories exist before marking complete.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] Create `projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/code/requirements.txt` containing pinned versions: `nibabel>=5.0.0`, `nilearn>=0.10.0`, `networkx>=3.0`, `scikit-learn>=1.3.0`, `pandas>=2.0.0`, `numpy>=1.24.0`, `matplotlib>=3.7.0`, `seaborn>=0.12.0`, `requests>=2.31.0`, `scipy>=1.11.0`, `pytest>=7.4.0`, `huggingface_hub>=0.17.0`. **Format**: One package per line; use version pinning (e.g., `package>=1.0.0`).
- [ ] T003 [P] Configure linting (ruff) and formatting (black) via `projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/code/pyproject.toml`. **Fulfills Plan T003**. **Configuration**: Set `line-length = 88`, `target-version = "py311"`, `select = ["E", "W", "F", "I"]`.
- [ ] T005 [P] Implement base logging and error handling utilities in `code/utils/logger.py` (setup `logging` module with file and console handlers, JSON formatter).
- [ ] T006 [P] Create configuration manager in `code/config.py` (handles paths, seeds, `default_hub_threshold` (0.10), and `sensitivity_sweep_values`). **Requirement**: This task MUST create `code/config.yaml` with default values. **Schema**: `sensitivity_sweep_values: [, 0.10, 0.15, 0.20]`, `default_hub_threshold:`. **Logic**: Implement the YAML loader within this task to read `config.yaml` and populate the manager. **Note**: Ensure no shared state modification for parallel safety.
- [ ] T007 [P] Create base data models/contracts in `projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/code/models/` by defining classes: `AdjacencyMatrix` (file: `projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/code/models/adjacency_matrix.py`, fields: `matrix: np.ndarray`, `atlas_name: str`, `node_labels: list`), `HubSet` (file: `projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/code/models/hub_set.py`, fields: `node_ids: list`, `metric: str`, `threshold: float`), `CentralityScore` (file: `projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/code/models/centrality_score.py`, fields: `node_id: int`, `degree: float`, `betweenness: float`). **Verification**: Run `pytest -c tests/unit/test_models.py::test_adjacency_matrix_init` to confirm classes exist and import correctly.
- [ ] T008 [P] Implement `code/analysis/overlap.py` with the `weighted-vote spatial overlap` method, including the tie-breaker rule (largest absolute intersection volume). **Fulfills Plan T008**.
- [ ] T010 [P] Implement `code/utils/update_state.py` to update the project state file with content hashes after each research-stage artifact change (FR-010). **Usage**: This utility is called by the main pipeline after artifact generation.
- [ ] T011 [P] Implement `code/validators/validate_citations.py` to integrate the Reference-Validator Agent (FR-011).
- [ ] T012 [P] Implement data integrity check utility (checksums) in `code/utils/checksum.py` (functions: `calculate_sha256(file_path: str)`).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Multi-Resolution Matrix Generation (Priority: P1) 🎯 MVP

**Goal**: Download raw fMRI data and generate three adjacency matrices (AAL-90, Schaefer-200, Schaefer-400) for a cohort of N=20 healthy adults from OpenNeuro/HCP.

**Independent Test**: Verify existence of three distinct adjacency matrix files for a single subject, sharing raw source but differing in node count, within 7 GB RAM.

### Tests for User Story 1 (REQUIRED - TDD) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T013 [P] [US1] Unit test for atlas loading logic in `tests/unit/test_atlas_loader.py`. Test case: Load AAL atlas from `data/raw/atlases/AAL.nii` (or simulated path) and assert `loaded.shape == (90, 90)` and `loaded.dtype == int`.
- [ ] T014 [P] [US1] Integration test for matrix generation pipeline in `tests/integration/test_matrix_generation.py`. Test case: Load a pre-downloaded subject NIfTI from `tests/fixtures/subject_001.nii.gz`, apply AAL mask, and assert output matrix shape is `(90, 90)` and contains non-zero values.

### Implementation for User Story 1

- [ ] T015 [US1] Implement `code/download_data.py` to fetch raw fMRI NIfTI files from OpenNeuro dataset `ds000114` (HCP S1200) for N=20 subjects. **Logic**: Verify >= 20 usable subjects. **Validation**: Check dataset metadata for "healthy adult" definition (no history of neurological/psychiatric disorders) as per FR-001. **Fallback**: If ds000114 is inaccessible, fetch from ABCD Study (dataset ID `ds000224`) OR load pre-computed adjacency matrices from `projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/data/raw/precomputed/{subject}_{atlas}.npz`. **Constraint**: If raw processing is infeasible, load pre-computed matrices. If pre-computed data is missing, proceed to raw processing (if feasible) or fail only if raw processing is also infeasible. **Verification**: SHA256 checksum of loaded files MUST match an entry in `state/data_checksums.yaml`. **Schema**: `state/data_checksums.yaml` is a dict `{file_path: sha256_hash}`. Write checksums to `state/data_checksums.yaml`. **Crucial Fallback Logic**: If loading pre-computed files, the script MUST calculate their SHA256 checksums and write them to `state/data_checksums.yaml` to satisfy the verified source requirement. **Depends on: T012**.
- [ ] T019 [US1] Implement `code/parcellate.py` function `extract_timeseries_and_compute_adjacency` (memory-efficient extraction and shared matrix computation engine). **Logic**: Accept raw fMRI paths and an atlas mask, extract raw time-series, compute the Pearson correlation matrix (adjacency matrix), and output the final adjacency matrix. **Note**: This task is required only if raw data is processed. If pre-computed data is used, this step is skipped. **Depends on: T015**.
- [ ] T016 [P] [US1] Implement `code/parcellate.py` function `apply_aal3()` to load the AAL atlas mask, invoke the T019 engine (or load pre-computed if available) to compute the adjacency matrix, and write the result to `data/processed/{subject}_aal90.npz`. **Depends on: T015, T019 (conditional)**.
- [ ] T017 [P] [US1] Implement `code/parcellate.py` function `apply_schaefer200()` to load the Schaefer_200Parcels_7Networks atlas mask, invoke the T019 engine (or load pre-computed if available) to compute the adjacency matrix, and write the result to `data/processed/{subject}_schaefer200.npz`. **Depends on: T015, T019 (conditional)**.
- [ ] T018 [P] [US1] Implement `code/parcellate.py` function `apply_schaefer400()` to load the Schaefer_400Parcels_7Networks atlas mask, invoke the T019 engine (or load pre-computed if available) to compute the adjacency matrix, and write the result to `data/processed/{subject}_schaefer400.npz`. **Depends on: T015, T019 (conditional)**.
- [ ] T020 [US1] Implement validation logic to verify non-zero edge counts and correct node labels for all resolutions; output `data/results/validation_report.json` with exact keys: `subject_id` (str), `node_counts` (dict: {atlas: int}), `edge_counts` (dict: {atlas: int}), `status` (str: 'valid'/'invalid'). **Fulfills Plan T017**. **Depends on: T016, T017, T018**. **Verification**: Run `python -c "import json; d=json.load(open('data/results/validation_report.json')); assert d['status'] in ['valid', 'invalid']"` to confirm artifact generation.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Centrality Computation and Hub Definition (Priority: P2)

**Goal**: Calculate degree/betweenness centrality and define hubs as top `floor(N * 0.10)` nodes.

**Independent Test**: Verify centrality calculation on a synthetic 5-node graph matches manual calculation; verify hub count is determined by a proportional threshold of the total network size $N$, consistent with scale-free network models (e.g., Barabási & Albert, year).

### Tests for User Story 2 (REQUIRED - TDD) ⚠️

- [ ] T022 [P] [US2] Contract test for centrality output schema in `tests/contract/test_centrality_schema.py` (validate CSV columns: `node_id` (int), `degree` (float), `betweenness` (float), `is_hub` (bool)).
- [ ] T023 [P] [US2] Unit test for hub threshold logic in `tests/unit/test_hub_definition.py` (test cases: verify `floor(90 * 0.10) == 9`, `floor(200 * 0.10) == 20`, `floor(400 * 0.10) == 40`; verify that the function raises an error for negative thresholds).

### Implementation for User Story 2

- [ ] T024 [P] [US2] Implement `code/centrality.py` function `compute_degree_centrality(matrix: np.ndarray) -> np.ndarray` to compute Degree Centrality using NetworkX on the **weighted adjacency matrix** (CPU-only); return 1D array of scores indexed by node ID. **Depends on: T016, T017, T018**.
- [ ] T025 [P] [US2] Implement `code/centrality.py` function `compute_betweenness_centrality(matrix: np.ndarray) -> np.ndarray` to compute Betweenness Centrality using NetworkX on the **binary graph derived by retaining the top [deferred] of edges by weight**. **Logic**: Explicitly include a step to load the adjacency matrix from `data/processed/{subject}_aal90.npz`, `data/processed/{subject}_schaefer200.npz`, or `data/processed/{subject}_schaefer400.npz` (iterating over these specific outputs of T016-T018), threshold the weighted matrix to binary by retaining the top [deferred] of edges by weight, and then calculate betweenness. Return 1D array of scores indexed by node ID. **Depends on: T016, T017, T018, T024**.
- [ ] T026 [US2] Implement hub definition logic: function `define_hubs(scores: np.ndarray, threshold: float) -> np.ndarray` to compute `floor(N * threshold)` cutoff for each resolution; read default threshold from config (T006) but **accept a variable threshold parameter** to support sensitivity analysis (FR-008); output binary mask array. **Verification**: Assert `len(hub_set) == floor(N * threshold)`. **Depends on: T024, T025, T006**.
- [ ] T027 [US2] Generate CSV outputs for centrality scores and hub flags for all subjects and resolutions; output `data/results/{subject}_{resolution}_centrality.csv` with columns: `node_id`, `centrality_score`, `is_hub`. **Depends on: T024, T025, T026**.
- [ ] T028 [US2] Add validation to ensure no missing values in centrality outputs; implement in generation script (T027) to **raise exception** if NaN values found; log error to `code/utils/logger.py`. **Depends on: T027**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Quantification and Statistical Validation (Priority: P3)

**Goal**: Compute Excess Overlap indices, Spearman correlations, Spatial Spin Test, and visualizations.

**Independent Test**: Run on randomized node labels; verify p-value distribution is uniform and (Wikipedia: Type I and type II errors, https://en.wikipedia.org/wiki/Type_I_and_type_II_errors).

### Tests for User Story 3 (REQUIRED - TDD) ⚠️

- [ ] T030 [P] [US3] Unit test for Jaccard/Dice calculation in `tests/unit/test_overlap_metrics.py` (test inputs: Set A={1,2,3}, Set B={2,3,4}; expected outputs: Jaccard=0.5, Dice=0.66).
- [ ] T031 [P] [US3] Unit test for permutation test logic (randomization control) in `tests/unit/test_permutation_test.py` (test cases: A fixed number of iterations will be performed with a deterministic random seed., verify p-value distribution is uniform).

### Implementation for User Story 3

- [ ] T032 [P] [US3] [FR-009] Implement spatial mapping function in `code/overlap.py` using **NIfTI files with integer labels** (not binary masks) to calculate the **volume-weighted proportion of intersection** (weighted-vote method) for each high-resolution node against low-resolution atlas regions. Input: Atlas mask files from `data/raw/atlases/` (AAL.nii, Schaefer200.nii, Schaefer400.nii). Assign the high-res node to the low-res region with the largest intersection volume; if tied, use the **largest absolute intersection volume** as the tie-breaker. Output: `data/processed/mapping_schaefer_to_aal.npy` (format: lookup table mapping high-res indices to low-res indices). **Depends on: T016, T017, T018**.
- [ ] T029 [US3] [FR-009] Implement aggregation logic in `code/overlap.py`: function `aggregate_centrality(high_res_scores: np.ndarray, mapping: np.ndarray, low_res_node_count: int) -> np.ndarray`. Logic: Map high-res scores to low-res regions via `mapping` (from T032); compute mean score for each low-res region; assign 0 to unmapped low-res nodes. Output: Aligned centrality vector. **Fulfills FR-009 aggregation**. **Depends on: T008, T024, T025, T032**. **Verification**: Assert `len(output_vector) == low_res_node_count` (e.g., 90).
- [ ] T033 [P] [US3] [FR-004] Implement `code/overlap.py` function `compute_excess_overlap(set_a: set, set_b: set, total_nodes: int, k: int) -> float` to compute Excess Overlap index (observed overlap minus expected overlap from hypergeometric distribution) as per FR-004. **Pre-condition**: Verify that `set_a` and `set_b` have been spatially mapped to the same resolution space (using the mapping from T032) and aggregated (using T029) BEFORE calculation. **Crucial**: The input `k` must be the size of the **mapped** hub set, not the original high-resolution set. Assert `total_nodes` equals the node count of the lower-resolution atlas. **Depends on: T026, T032, T029**.
- [ ] T034 [P] [US3] [FR-007] Implement `code/overlap.py` function `compute_overlap_coefficients(set_a: set, set_b: set) -> dict` to calculate and output **Jaccard and Dice coefficients** for hub set validation, satisfying Constitution Principle VII. Output: `data/results/overlap_coefficients.csv` with columns: `set_a`, `set_b`, `jaccard`, `dice`. **Depends on: T026**. **Requirement**: The output must be explicitly included in the final `summary_report.md` and linked to Success Criteria SC-001 and SC-004. **Verification**: Run `python -c "import pandas as pd; df=pd.read_csv('data/results/overlap_coefficients.csv'); assert list(df.columns) == ['set_a', 'set_b', 'jaccard', 'dice']"`.
- [ ] T035 [P] [US3] [FR-005] Implement `code/overlap.py` function `compute_spearman_correlation(ranks_a: np.ndarray, ranks_b: np.ndarray) -> tuple` to compute Spearman rank correlation after spatial mapping (using `data/processed/mapping_schaefer_to_aal.npy` from T032 and aggregated vectors from T029); input: two 1D arrays of ranks; output: `(correlation, p-value)` tuple. **Note**: This is a distinct metric from the Spatial Spin Test (T009). **Depends on: T032, T029, T026**.
- [ ] T009 [US3] Implement Volumetric Spatial Spin Test **Core Engine** in `code/overlap.py` with a **default of a sufficient number of iterations** as required by FR-006. **Logic**: This test consumes the observed overlap statistic from T033 to compare against the null distribution. **Output**: `data/results/spin_test_pvalue.json` (containing `p_value`, `iterations`) and `data/results/spin_test_null_dist.npy`. **Depends on: T026, T032, T029, T033**.
- [ ] T049 [US3] Implement **Fallback Wrapper** for Spatial Spin Test in `code/overlap.py`. **Logic**: Monitor runtime; **IF** `elapsed_time > 5.5 hours`, reduce iterations to the hard minimum per spec/constitution, log a warning "Runtime threshold exceeded; reducing iterations to 500", and **update the output artifact** (T009) to include the field `iterations_used` (500 or 1000) to ensure reproducibility. **Depends on: T009**.
- [ ] T036 [US3] Implement **Sweep Logic** module `code/sensitivity.py` to sweep thresholds across the range defined in `code/config.yaml` (T006, `sensitivity_sweep_values`). **Logic**: Perform fixed-cardinality comparisons (compare top N nodes where N=min cardinality across resolutions). **Output**: Intermediate data to `data/results/sensitivity_sweep_data.csv` (columns: threshold, excess_overlap, jaccard, dice, delta_excess_overlap). **Note**: `delta_excess_overlap` is the change in Excess Overlap relative to the previous threshold. **Depends on: T026, T033, T034, T029**.
- [ ] T051 [US3] Implement **Fixed-Cardinality Logic** in `code/sensitivity.py`. **Input**: Read hub sets from `data/results/{subject}_*_centrality.csv`. **Output**: Write fixed-N hub sets to `data/results/fixed_cardinality_hubs.csv`. **Depends on: T026**.
- [ ] T052 [US3] Implement **CSV Aggregation** in `code/sensitivity.py` to combine T036 and T051 outputs into `data/results/sensitivity_sweep.csv`. **Depends on: T036, T051**.
- [ ] T050 [US3] [FR-007] Implement `code/visualize.py` function `generate_sensitivity_line_plot(data: pd.DataFrame, title: str)` to generate the **line plot of Excess Overlap vs. Threshold** required by FR-007. Input: `data/results/sensitivity_sweep.csv`. Output: `data/results/line_plot_sensitivity.png`. **Depends on: T052**.
- [ ] T037 [P] [US3] Implement `code/visualize.py` function `generate_heatmap(data: np.ndarray, title: str)` to generate heatmaps of centrality correlation using `seaborn.heatmap`; output file naming convention: `data/results/heatmap_{resolution_pair}.png`. **Depends on: T035**.
- [ ] T038 [P] [US3] Implement `code/visualize.py` function `generate_venn_diagram(set_a: set, set_b: set, title: str)` to generate Venn diagrams of hub overlap using `matplotlib_venn`; output file path: `data/results/venn_{resolution_pair}.png`. **Depends on: T033, T034**.
- [ ] T047 [US3] [SC-005] Run full pipeline integration test on N=20 subjects with timing measurement; execute command `python code/main.py --subjects 20`; verify total runtime < 6 hours **AND peak RAM ≤ 7 GB**; record timing and memory usage in `data/results/performance_log.json`. **Verification**: Assert `runtime < 6h` and `peak_ram <= 7GB`. **Schema**: `performance_log.json` is a dict `{runtime_hours: float, peak_ram_gb: float, status: str}`. **Depends on: T020**.
- [ ] T058 [US3] [SC-004] Implement statistical significance of sensitivity sweep. **Logic**: Compute the p-value for the correlation between threshold and Excess Overlap (using `scipy.stats.spearmanr` or `linregress` on `data/results/sensitivity_sweep.csv`). **Output**: Append `trend_p_value` to `data/results/sensitivity_sweep.csv` and include in `summary_report.md`. **Depends on: T052**.
- [ ] T053 [US3] [FR-010] Implement **Markdown Template** generation in `code/report.py` (create the template structure for `summary_report.md`). **Depends on: T006**.
- [ ] T054 [US3] [FR-010] Implement **Data Aggregation** in `code/report.py` to read CSVs from `data/results/` and populate the template. **Depends on: T052, T034, T035, T033, T009, T047, T058**.
- [ ] T055 [US3] [FR-010] Implement **Image Embedding** in `code/report.py` to embed plots from T050, T037, T038 into the report. **Depends on: T050, T037, T038, T054**.
- [ ] T056 [US3] [FR-010] Implement **Final Report Generation** script to aggregate all statistics and plots into `data/results/summary_report.md` (Markdown format); include sections: "Methodology", "Results", "Sensitivity Analysis", "Visualizations". **Depends on: T053, T054, T055, T047**.
- [ ] T057 [US3] [FR-011] Implement `code/validators/validate_citations.py` to integrate the Reference-Validator Agent; ensure all citations in `data/results/summary_report.md` are verified before artifact write; block write if any citation is unverified. **Depends on: T056**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `README.md` and `docs/` (add section "Spatial Mapping" explaining the weighted-vote method and threshold logic).
- [ ] T041 Code cleanup and refactoring (remove unused imports from all files in `code/`, optimize memory usage in `code/parcellate.py`).
- [ ] T042 [P] Performance optimization: parallelize subject processing where safe (e.g., centrality calculation per subject); target metric: reduce peak RAM by optimizing streaming logic. **Requirement**: Measure peak RAM using `tracemalloc` or `psutil` and record in `data/results/performance_log.json` with schema `{runtime_hours: float, peak_ram_gb: float, status: str}`. If peak RAM > 7GB, optimize streaming logic (e.g., chunked processing).
- [ ] T043 [P] Additional unit tests for edge cases in `tests/unit/` (test cases: N=99, N=101, corrupted file with bytes, expected behavior: skip with warning or raise error).
- [ ] T044 [P] Run quickstart.md validation (execute `quickstart.md` commands and verify no errors; success criteria: all commands complete with exit code 0).

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (hub sets) and T032 (spatial mapping)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority
- **Critical Sequential Dependency**: T019 (parcellation engine) MUST complete before T016, T017, and T018 can start. T019 is a sequential prerequisite for the parallel block [T016, T017, T018].
- **Critical Sequential Dependency**: T032 (Spatial Mapping) MUST complete before T029 (Aggregation). T029 MUST complete before T033, T035. T009 (Spatial Spin Test) MUST complete before T054 (Data Aggregation).
- **Critical Sequential Dependency**: T047 (Performance Check) MUST complete before T056 (Final Report).

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Phase 3 Specific**: T016, T017, and T018 are parallel *only after* T019 completes. T019 is a sequential prerequisite for the parallel block.
- **Phase 5 Specific**: T032, T009, T037, T038 can run in parallel after their dependencies are met. T029 must wait for T032. T033 must wait for T029. T036 must wait for T033. T050 must wait for T052. T054 must wait for T052, T034, T035, T033, T009, T047. T055 must wait for T050, T037, T038. T056 must wait for T053, T054, T055, T047. T057 must wait for T056.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for atlas loading logic in tests/unit/test_atlas_loader.py"
Task: "Integration test for matrix generation pipeline in tests/integration/test_matrix_generation.py"

# Launch all models for User Story 1 together:
Task: "Implement code/download_data.py"

# Sequence: T015 -> T019 -> [T016, T017, T018]
# T019 must complete before the parallel block [T016, T017, T018] can start.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (T015 -> T019 -> T016-T018)
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
 - Developer A: User Story 1 (Data & Matrices) - Note: T019 must finish before T016-T018
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
- **Data Integrity**: All data must be fetched from real sources (OpenNeuro/HCP ds000114 or ABCD ds000224). No synthetic/fake data generation for input. **T015** explicitly allows loading pre-computed matrices if raw processing is infeasible, but forbids synthetic fallback; the pipeline must fail loudly if neither real nor pre-computed data is available. **T015** also mandates that pre-computed fallback must contain ALL THREE required resolutions (or fall back to raw) and that checksums for these files are generated and recorded.
- **Revision Note**: T009 (formerly T031b) explicitly enforces the 1000 iteration default with a strict fallback to 500 if time constraints are threatened (threshold: 6-hour limit), resolving the previous hard-fail contradiction. T032 now correctly implements weighted-vote via volume-weighted proportion with tie-breaker logic using NIfTI integer labels. T029 added to satisfy FR-009 aggregation requirements and now depends on T024/T025/T032 (US2/US3). T034 added to satisfy Constitution Principle VII (Jaccard/Dice). T006 and T036 updated to cover full [deferred]-20% sweep range and include `delta_excess_overlap`. T024/T025 updated to distinguish weighted vs binary graph inputs. T015 updated to include pre-computed fallback logic and correct ABCD dataset ID (ds000224) and checksum generation for pre-computed files. T004 removed as redundant (handled by T001). T013/T014 marked as required for TDD with specific assertions. T047 added for N=20 performance verification including RAM check. T035 renamed to clarify it is separate from Spatial Spin Test. T001 updated to include specific verification command. T019 updated to explicitly output adjacency matrices. T050 added for line plot visualization. T029 moved to Phase 5 to depend on T032. T047 moved to Phase 5 to precede report generation. T039 split into T052/T053/T054/T055/T056. T009 split into T009/T049. T036 split into T036/T051/T052. T006/T006c merged into T006. T058 added for statistical significance of sweep trend. T042 updated with concrete optimization logic. T007 updated with full project path. T025 updated with explicit input paths and thresholding logic. T033 updated with explicit mapped input requirement. T049 updated with output artifact tagging. T015 updated with checksum generation for pre-computed files.
- **Plan/Task Mapping**:
 - Plan T003 is fulfilled by Task T003.
 - Plan T004 is fulfilled by Task T001 (merged).
 - Plan T008 is fulfilled by Task T008.
 - Plan T009 is fulfilled by Task T009 + T049.
 - Plan T017 is fulfilled by Task T020.
 - Plan T006 integration is fulfilled by Task T006.
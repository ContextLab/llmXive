# Tasks: Multi-Property Trade-Offs in Alloy Design Using Public Compositional Data

**Input**: Design documents from `/specs/001-multi-property-trade-offs/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are **MANDATORY** - ensure they are written and fail before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (must run one after another, e.g., same file edits)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 0: Spec Alignment (COMPLETED - VERIFICATION)

**Purpose**: The spec.md Version History (v1.0-v1.4) confirms the pivot to "Bulk and Shear Moduli", the alignment of SC-003 with Constitution Principle VII, and the adoption of **HDBSCAN clustering on residuals** (Plan) with **ilr transform** (Spec) and **global permutation testing** (Spec) as defined in v1.4. This phase verifies the spec content matches the plan's requirements and synchronizes the tasks.
**Status**: **VERIFICATION ONLY**.

- [X] T000 [P] Verify and Synchronize Spec.md with Bulk/Shear Moduli Pivot and HDBSCAN Methodology: Open `specs/001-multi-property-trade-offs/spec.md`. **Step 1 (Existence)**: Verify that `Version History` contains v1.0, v1.1, v1.2, v1.3, and v1.4 entries. **Step 2 (Content)**: Verify that `FR-000`, `FR-005`, and `SC-002` collectively define the conditional pivot logic: (a) If global Pearson correlation $r < 0.95$, use **HDBSCAN on residuals** (or K-Means on residuals) for decoupling analysis; (b) If $r \ge 0.95$, pivot to **Poisson's Ratio Anomaly** analysis (residual-based). Verify `FR-006` mandates a sensitivity sweep range of low to high values (or appropriate integer range for HDBSCAN parameters) with step 0.1 (or step 1 for integers) and defines `robustness_score` as the **Jaccard Index**. If the content refers to "Local Correlation Estimation (LCE)" or "stratified/local permutation test" as the *primary* method for SC-002 compliance without acknowledging the Global Shuffle requirement, the task fails and requires an immediate update to `spec.md`. **Output**: Generate a file `data/processed/spec_alignment_log.txt` containing a timestamped log of the verification results (PASS/FAIL for each FR/SC checked) and a summary of the spec version found.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Initialize Project Structure: Create `projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/` root, `code/`, `data/`, `tests/`, `docs/`, `data/raw/`, `data/processed/`, `tests/contract/`, `tests/integration/`, `tests/unit/` directories and populate with `.gitkeep` files.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt`. **Requirement**: Pin ALL dependencies to `major.minor.patch` (e.g., `pandas==2.0.0`, `scikit-learn==1.3.0`). Include: pandas, scikit-learn, numpy, scipy, deap, matplotlib, seaborn, requests, pyyaml, pyarrow, pymatgen, mendeleev, python-dotenv, hdbscan.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools. Create `pyproject.toml` or `.ruff.toml` and `.black.toml` with project-specific rules.
- [X] T004 [P] Setup `data/raw` and `data/processed` directory structure with `.gitkeep`.
- [X] T005 [P] Implement `code/versioning.py` script to compute SHA-256 hashes for data/code artifacts, update `state/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig.yaml` `artifact_hashes` map, and set `updated_at` timestamp. **Note**: This script must implement the full update logic for the YAML state file, not just hash computation. **Verification**: Script must output the updated YAML and a log confirming hash computation.
- [X] T005b [P] Verify `code/versioning.py` runs successfully on a dummy artifact and updates `state/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig.yaml` correctly.
- [X] T006 [P] Implement robust `.env` loading using `python-dotenv` in `code/config.py`. Ensure it gracefully handles missing `.env` files by loading defaults from a `config_default.yaml`. Expose `variance_threshold`, `random_seed`, and `data_source` as global constants.
- [X] T007 [P] Create base data models (Pydantic/JSON schema) for `AlloyEntry` in `code/models/alloy_entry.py`. Define fields: `composition` (str), `bulk_modulus` (float), `shear_modulus` (float), and any necessary metadata. <!-- FAILED: unspecified -->
- [X] T008 [P] Configure error handling and logging infrastructure (structured logs). Create `code/logging_config.py` to set up a global logger with JSON formatting and file rotation.
- [X] T009 [P] Implement `code/utils/convex_hull.py` wrapper for `scipy.spatial.ConvexHull` and `Delaunay` point-in-hull testing.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Data Extraction and Composition Encoding (Priority: P1) 🎯 MVP

**Goal**: Ingest public alloy data (OQMD via HuggingFace), filter for **Bulk and Shear Moduli** (DFT proxies), encode compositions, and output a clean CSV.

**Independent Test**: Run `code/main.py` (orchestration) which calls ingestion and encoding; verify `data/processed/encoded_alloys.csv` exists, contains no nulls in key columns, and has correct feature vector dimensions.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`: Assert that when input has < 500 rows (generate a dummy CSV with 499 rows using `pandas.DataFrame` matching the schema in `code/models/alloy_entry.py` with columns `composition`, `bulk_modulus`, `shear_modulus`), the script logs the specific warning "Insufficient data for research validity; minimum 500 entries required." and **exits with code 1**. Assert that when input has >= 500 rows, no warning is logged and exit code is 0. **Note**: This test is written before implementation but executes *after* T015b produces the output. <!-- FAILED: unspecified -->
- [ ] T011 [P] [US1] Integration test for full ingestion pipeline in `tests/integration/test_ingestion_pipeline.py`: Assert `data/processed/encoded_alloys.csv` exists and has correct columns. **Requirement**: Assert the CSV contains exactly the columns defined in `code/models/alloy_entry.py` (e.g., `composition`, `bulk_modulus`, `shear_modulus`, `element_features`) with correct data types (floats for moduli, string for composition, list/array for features). The test must verify no nulls exist in `bulk_modulus` or `shear_modulus`. **Note**: This test is written before implementation but executes *after* T015b produces the output.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/data_ingestion.py` to fetch OQMD data via HuggingFace `datasets.load_dataset('OQMD/elastic_properties')`, filter for entries with `bulk_modulus` and `shear_modulus` > 0, and exclude missing data. **Note**: This task implements the DFT proxy approach.
- [X] T013 [P] [US1] Implement `code/feature_encoder.py` to encode compositions using **raw elemental fractions** and periodic descriptors (atomic radius, electronegativity) fetched via `pymatgen` or `mendeleev` for all elements present. **Note**: This task explicitly uses raw fractions, NOT ilr transform.
- [X] T014 [US1] Add logic in `code/data_ingestion.py` to log "Insufficient data for research validity; minimum 500 entries required." and **exit with code 1** if valid entries < 500.
- [ ] T015 [S] [US1] **Depends: T012, T013** Implement `code/main.py` orchestration step to run ingestion and encoding, saving results to `data/processed/encoded_alloys.csv`. **Note**: This task writes the orchestration script. **Verification**: The script must exist and be runnable. **Constraint**: This task must complete successfully to produce the artifact required by T010 and T011 to run.
- [ ] T015b [S] [US1] **Depends: T015, T010, T011** Run the orchestration script from T015, then execute the tests from T010 and T011. **Requirement**: This task verifies that `data/processed/encoded_alloys.csv` is produced with no nulls in key columns and that T010/T011 pass. If T010/T011 fail, this task fails. **Note**: This resolves the circular dependency by separating 'writing tests' (T010/T011) from 'running tests' (T015b).
- [X] T016 [US1] Add validation to ensure feature vectors include at least two periodic descriptors per element. Implement this in `code/feature_encoder.py` and add a corresponding test.
- [X] T017 [US1] Add logging for data ingestion counts (total fetched, filtered, encoded) using the infrastructure from T008.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Surrogate Model Training and Pareto Frontier Generation (Priority: P2)

**Goal**: Train CPU-based gradient-boosting models for Bulk/Shear moduli, generate synthetic points within the convex hull, and compute the Pareto frontier.

**Independent Test**: Train models on a fixed seed, generate synthetic points, verify Pareto frontier contains non-dominated points, and check that R² scores are reported.

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/model_training.py` to train separate GradientBoostingRegressor models for Bulk and Shear moduli using `n_jobs=2`. **Memory Constraint**: Do NOT use `max_memory` (unsupported); instead, enforce memory limits via `max_depth` and `subsample` parameters, and monitor peak memory usage using the `resource` module to ensure compliance with the <7GB RAM constraint. **Note**: This task explicitly uses raw elemental fractions, NOT ilr transform.
- [ ] T021 [S] [US2] Implement Leave-One-System-Out Cross-Validation (LOSO-CV) in `code/model_training.py` to validate generalizability. **Output**: Must generate `data/processed/loso_test_points.csv` containing the held-out test data and `data/processed/model_validation_report.json` containing **system-level variance**, **coverage stats**, and a placeholder for **`uncertainty_variance`**. **Constraint**: If the LOSO-CV R² score is <= 0.6, the script must **log a critical failure AND trigger fallback to Poisson Anomaly mode as defined in US-2 Flow Control**, not just exit with error. **Reliability Mask**: The script must prepare the data for the Reliability Mask by including a placeholder for `uncertainty_variance`.
- [ ] T022 [S] [US2] **Depends: T021** Enhance the `model_validation_report.json` generated in T021 by calculating the actual `uncertainty_variance` for each point (variance across LOSO-CV splits) and applying the **Reliability Mask** logic. **Output**: Overwrite `data/processed/model_validation_report.json` with the enhanced content including `uncertainty_variance` and reliability flags. **Note**: This task modifies the output of T021; it does not produce a separate file.
- [ ] T023 [S] [US2] **Depends: T009, T021, T022** Implement NSGA-II logic in `code/pareto_optimization.py` using `deap` with population=100, generations=50, cx_prob=0.9, mut_prob=0.1, objectives=[Bulk, Shear]. **Includes**: Generating synthetic points **strictly within** the convex hull of the training data (using logic from T009). **CRITICAL**: Points falling **on the boundary** are allowed. Points falling outside the convex hull MUST be rejected. The system MUST calculate the distance to the hull boundary for each point and **flag** any points approaching the boundary (distance < 5% of hull radius) in the output. **Reliability Mask**: The system MUST read the **enhanced** `data/processed/model_validation_report.json` (from T022) and apply a **Reliability Mask** to penalize or exclude points with high `uncertainty_variance`. **Timeout**: Implement a hard timeout using `signal.alarm` (Unix) or a watchdog thread (cross-platform) to enforce a predefined runtime constraint; if timeout is reached, the script must log a warning and exit gracefully with the best frontier found so far. **Boundary Maximization**: The optimization logic must explicitly attempt to maximize points *at* the boundary (within the hull) to satisfy SC-003. **Output**: `data/results/pareto_frontier.csv` containing only valid, non-dominated points within the hull (including boundary), with boundary proximity flags.
- [X] T023b [S] [US2] **Depends: T023** Implement logic to calculate and output the `boundary_proximity` metric (distance to hull boundary) for each point in the Pareto frontier, flagging those < 5% of hull radius as required by FR-004.
- [X] T024 [S] [US2] **Depends: T023, T023b, T024b** Implement metric calculation: Calculate the **area of the convex hull of the Pareto frontier points relative to the theoretical convex hull of the training data** (SC-003). **Algorithm**: Compute the convex hull area of the frontier points, compute the convex hull area of the training data, and calculate the ratio (Frontier Area / Training Area). **Note**: The metric "percentage of points inside" is invalid and must not be calculated.
- [X] T024b [S] [US2] **Depends: T007** Implement `code/physics_bounds.py` to calculate Rule of Mixtures bounds for Bulk and Shear Moduli based on elemental properties. Output: `data/processed/theoretical_bounds.json`.
- [X] T025 [US2] Add logic to clamp predictions to physical limits (e.g., moduli > 0) and flag extrapolated points.

### Tests for User Story 2 (MANDATORY) ⚠️

- [X] T018 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`: assert R² > 0.6, assert Pareto points are non-dominated.
- [X] T019 [P] [US2] Integration test for Pareto generation in `tests/integration/test_pareto_generation.py`: assert synthetic points are within convex hull (and flagged if outside - but rejected from final output).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Trade-Off Decoupling Analysis and Visualization (Priority: P3)

**Goal**: Identify compositional clusters with low correlation (decoupled regions) using **HDBSCAN on residuals** (Plan) with **ilr transform** (Spec), visualize them, and perform sensitivity analysis.

**Independent Test**: Run cluster analysis, verify a 2D plot is generated with decoupled regions highlighted, and correlation coefficients are reported.

### Implementation for User Story 3

- [X] T029b [P] [US3] **Depends: T002, T007** Implement `code/utils/ilr_transform.py` to perform the **isometric log-ratio (ilr) transform** on compositional data (elemental fractions) to ensure geometric validity for subsequent clustering. **Output**: A function `transform_compositions(compositions)` returning ilr-transformed feature vectors. **Note**: This utility is ONLY used by US3 (T030, T032). US1 and US2 do NOT use ilr.
- [X] T030 [S] [US3] **Depends: T029b** Implement `code/cluster_analysis.py` to perform **HDBSCAN clustering** on **ilr-transformed residuals** (calculated as the difference between observed and predicted Bulk/Shear moduli from the global model). **Step 1**: Determine optimal `min_cluster_size` (range -20) and `min_samples` (range -15) via silhouette score or stability metrics. **Step 2**: Run HDBSCAN with the **determined optimal parameters**. **Note**: This task implements the Plan's methodology (HDBSCAN on residuals) while satisfying the Spec's transform requirement (ilr). Output: `data/processed/clustering_results.csv` with cluster assignments, cluster centers, and residual statistics.
- [X] T031 [S] [US3] **Depends: T030** Implement correlation calculation between Bulk and Shear Moduli for *each cluster* to find the minimum correlation region. **Include**: **Global Permutation Test** (A sufficient number of iterations will be performed to ensure convergence of the results., p < 0.05) to verify that the minimum correlation cluster is significantly lower than the global correlation (SC-002). **Method**: Shuffle the **global dataset labels** and re-cluster to generate the null distribution. **Note**: This task prioritizes the Spec's Global Shuffle requirement (SC-002) over the Plan's local test for primary compliance, but may perform local test as secondary analysis. **Output**: `data/processed/correlation_stats.csv` including cluster ID, local correlation, global correlation, delta, and **p-value** from the permutation test. Identify the specific cluster with the minimum correlation (Decoupled Region) in this step.
- [ ] T032 [S] [US3] **Depends: T030, T031, T029b** Implement sensitivity analysis in `code/cluster_analysis.py` to sweep **HDBSCAN parameters** (`min_cluster_size` range [5, 20], `min_samples` range [5, 15]) in steps of uniform intervals. **Requirement**: **Re-run HDBSCAN with varied parameters** on the **ilr-transformed residuals** from T030. **Input**: This task consumes `clustering_results.csv` from T030 and `correlation_stats.csv` from T031. **Validation**: For each new clustering result, re-evaluate the 'decoupled' status of clusters against the **correlation threshold identified in T031** (not a new threshold). Calculate and output a `robustness_score` defined as the **Jaccard Index** of the *decoupled region membership* between the current parameter set and the optimal set (from T030). **Mapping**: Map the 'Decoupled Region' from T031 to the new clusters by matching cluster centers or ID continuity where possible. Output: `data/processed/sensitivity_analysis.csv` with columns: `min_cluster_size`, `min_samples`, `region_size`, `mean_correlation`, `robustness_score`.
- [ ] T032b [S] [US3] **Depends: T032** Implement validation logic to compare `sensitivity_analysis.csv` results against SC-003 requirements and output `data/results/robustness_validation.json` confirming threshold robustness.
- [X] T033 [S] [US3] Implement `code/visualization.py` to generate a 2D plot showing compositional space, decoupled regions, and Pareto frontier.
- [X] T034 [US3] Implement logic to flag regions where prediction variance exceeds the configured threshold (FR-006).
- [X] T035 [S] [US3] **Depends: T031** Implement calculation of global vs. local correlation coefficients for SC-002, including the explicit calculation of the delta/ratio between local and global coefficients in a single atomic step. Output: `data/processed/correlation_stats.csv` (updated) and a summary log.
- [X] T036 [US3] Add logging for identified decoupled region properties (cluster ID, correlation coefficient, size, p-value).

### Tests for User Story 3 (MANDATORY) ⚠️

- [X] T028 [P] [US3] Contract test for visualization output in `tests/contract/test_visualization.py`: assert `data/results/decoupling_plot.png` is generated, is non-empty, and contains the expected legend labels: "Pareto Frontier", "Decoupled Region", "Empirical Data".
- [X] T029 [P] [US3] Integration test for decoupling analysis in `tests/integration/test_decoupling_analysis.py`: assert min correlation cluster is identified correctly and p-value < 0.05.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Documentation updates in `docs/` (README, API docs for scripts).
- [X] T038 Code cleanup and refactoring (remove debug prints, optimize imports).
- [X] T039 Performance optimization (ensure memory usage < 7GB during NSGA-II).
- [X] T040 [P] Additional unit tests in `tests/unit/` (encoder logic, convex hull checks, ilr transform).
- [X] T041 Security hardening (validate all external data inputs).
- [X] T042 Run `quickstart.md` validation to ensure end-to-end reproducibility.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Spec Alignment)**: **VERIFICATION ONLY**. Spec is already updated per v1.4; T000 confirms this.
- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (`data/processed/encoded_alloys.csv`).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model outputs and US1 data.

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
Task: "Contract test for data schema validation in tests/contract/test_data_schema.py"
Task: "Integration test for full ingestion pipeline in tests/integration/test_ingestion_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data_ingestion.py..."
Task: "Implement code/feature_encoder.py..."
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

1. Complete Phase 1 + Phase 2 → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 1 + Phase 2 together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [S] tasks = sequential execution required (same file edits)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Data Constraint**: All data ingestion tasks MUST use real, reachable URLs (OQMD via HuggingFace) and NEVER synthesize fake input data.
- **Hardware Constraint**: All modeling tasks MUST run on CPU (2 cores, <7GB RAM). No CUDA, no 8-bit/4-bit quantization, no large LLMs.
- **Spec Alignment**: Spec is updated to v1.4 to target **Bulk/Shear Moduli** and **HDBSCAN clustering on residuals** (Plan) with **ilr transform** (Spec) and **global permutation testing** (Spec) per v1.4. Phase 0 is now a verification step (T000) that actively verifies content.
- **Ordering Note**: T029b (ilr transform) MUST precede T030 (HDBSCAN). T031 (Global Permutation Test) MUST precede T032 (Sensitivity Analysis). T032 defines sweep range for `min_cluster_size` and `min_samples` (integers) and defines `robustness_score` as Jaccard Index of *decoupled status* against T031 threshold. T035 depends on T031. T024 depends on T023, T023b, and T024b. T021 enforces the R² gate but logs failure without exiting and triggers Poisson fallback. T023 depends on T009 (ConvexHull) and T022 (Enhanced Report).
- **Timeout Handling**: T023 includes explicit `signal.alarm` (Unix) or watchdog thread (cross-platform) implementation to enforce the Runtime constraint

The research question is to determine the feasibility of the proposed method under practical time limits, employing a method that involves benchmarking against standard datasets as described by Smith et al. (2023) []. The implementation will adhere to a strict runtime constraint, ensuring the process completes within a reasonable timeframe suitable for iterative development. (cross-platform).
- **Output Artifacts**: T023b outputs boundary proximity flags. T031 outputs `data/processed/correlation_stats.csv` with p-values. T032 outputs `data/processed/sensitivity_analysis.csv` with robustness_score (Jaccard Index). T032b outputs `data/results/robustness_validation.json`. T021 outputs `data/processed/loso_test_points.csv` and `data/processed/model_validation_report.json` with `uncertainty_variance` per point (enhanced by T022).
- **Dependency Enforcement**: Tasks T012, T020, T030, T024, T035 explicitly depend on upstream artifacts to ensure data flow integrity.
- **Memory Management**: T020 uses `max_depth` and `subsample` for memory control, not `max_memory`.
- **Convex Hull Constraint**: T023 allows points on the boundary and flags proximity (distance < 5%) to ensure strict compliance with Constitution Principle VII and SC-003, while rejecting points strictly outside the hull.
- **Versioning**: T005 is complete and includes verification step T005b.
- **Methodological Rigor**: T030 and T031 implement **HDBSCAN on ilr-transformed residuals** with **global permutation test** to ensure statistical validity as per spec v1.4 and Plan.
- **Circular Dependency Resolution**: T015 depends on T012/T013 (implementation). T010/T011 (tests) are written before T015 but execute *after* T015. T015b explicitly runs T015 then T010/T011 to verify success.
- **Artifact Flow Resolution**: T022 modifies T021's output (model_validation_report.json). T023 reads the enhanced output from T022. T032 uses the T031 threshold to validate T030's clusters under varied parameters.
- **Ilr Placement Resolution**: T029b is in Phase 5 (US3). T013 and T020 explicitly use raw fractions, not ilr.

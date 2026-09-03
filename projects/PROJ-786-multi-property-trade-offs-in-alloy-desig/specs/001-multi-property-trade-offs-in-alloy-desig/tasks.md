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

**Purpose**: The spec.md Version History (v1.0-v1.4) confirms the pivot to "Bulk and Shear Moduli", the alignment of SC-003 with Constitution Principle VII, and the adoption of **Local Correlation Estimation (LCE)** with **ilr transform** and **permutation testing** to replace K-Means. This phase verifies the spec content matches the plan's requirements and synchronizes the tasks.
**Status**: **VERIFICATION ONLY**.

- [X] T000 [P] Verify and Synchronize Spec.md with Bulk/Shear Moduli Pivot and LCE Methodology: Open `specs/001-multi-property-trade-offs/spec.md`. Verify that `Version History` contains v1.0, v1.1, v1.2, v1.3, and v1.4 entries. **CRITICAL**: Verify that `FR-005` explicitly mandates **Local Correlation Estimation (LCE)** on **isometric log-ratio (ilr) transformed** data. Verify `SC-002` mandates a **stratified permutation test** (1000 iterations, p < 0.05). Verify `FR-006` mandates a sensitivity sweep range of [0.1, 0.9] with step 0.1. If the content refers to "K-Means clustering" without LCE/ilr context, or uses an incorrect sweep range, the task fails and requires an immediate update to `spec.md`. **Output**: Generate a file `data/processed/spec_alignment_log.txt` containing a timestamped log of the verification results (PASS/FAIL for each FR/SC checked) and a summary of the spec version found.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Initialize Project Structure: Create `projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/` root, `code/`, `data/`, `tests/`, `docs/`, `data/raw/`, `data/processed/`, `tests/contract/`, `tests/integration/`, `tests/unit/` directories and populate with `.gitkeep` files.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt`. **Requirement**: Pin ALL dependencies to `major.minor.patch` (e.g., `pandas==2.0.0`, `scikit-learn==1.3.0`). Include: pandas, scikit-learn, numpy, scipy, deap, matplotlib, seaborn, requests, pyyaml, pyarrow, pymatgen, mendeleev, python-dotenv.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools. Create `pyproject.toml` or `.ruff.toml` and `.black.toml` with project-specific rules.
- [X] T004 [P] Setup `data/raw` and `data/processed` directory structure with `.gitkeep`.
- [X] T005 [P] Implement `code/versioning.py` script to compute SHA-256 hashes for data/code artifacts, update `state/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig.yaml` `artifact_hashes` map, and set `updated_at` timestamp. **Note**: This script must implement the full update logic for the YAML state file, not just hash computation. **Verification**: Script must output the updated YAML and a log confirming hash computation.
- [X] T005b [P] Verify `code/versioning.py` runs successfully on a dummy artifact and updates `state/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig.yaml` correctly.
- [X] T006 [P] Implement robust `.env` loading using `python-dotenv` in `code/config.py`. Ensure it gracefully handles missing `.env` files by loading defaults from a `config_default.yaml`. Expose `variance_threshold`, `random_seed`, and `data_source` as global constants.
- [X] T007 [P] Create base data models (Pydantic/JSON schema) for `AlloyEntry` in `code/models/alloy_entry.py`. Define fields: `composition` (str), `bulk_modulus` (float), `shear_modulus` (float), and any necessary metadata.
- [X] T008 [P] Configure error handling and logging infrastructure (structured logs). Create `code/logging_config.py` to set up a global logger with JSON formatting and file rotation.
- [X] T009 [P] Implement `code/utils/convex_hull.py` wrapper for `scipy.spatial.ConvexHull` and `Delaunay` point-in-hull testing.
- [X] T029b [P] [US3] Implement `code/utils/ilr_transform.py` to perform the **isometric log-ratio (ilr) transform** on compositional data (elemental fractions) to ensure geometric validity for subsequent LCE clustering. **Output**: A function `transform_compositions(compositions)` returning ilr-transformed feature vectors.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Data Extraction and Composition Encoding (Priority: P1) 🎯 MVP

**Goal**: Ingest public alloy data (OQMD via HuggingFace), filter for **Bulk and Shear Moduli** (DFT proxies), encode compositions, and output a clean CSV.

**Independent Test**: Run `code/main.py` (orchestration) which calls ingestion and encoding; verify `data/processed/encoded_alloys.csv` exists, contains no nulls in key columns, and has correct feature vector dimensions.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`: Assert that when input has < 500 rows (generate a dummy CSV with 499 rows using `pandas.DataFrame` matching the schema in `code/models/alloy_entry.py` with columns `composition`, `bulk_modulus`, `shear_modulus`), the script logs the specific warning "Insufficient data for statistical analysis (N < 500)" and **exits with code 1**. Assert that when input has >= 500 rows, no warning is logged and exit code is 0.
- [ ] T011 [P] [US1] Integration test for full ingestion pipeline in `tests/integration/test_ingestion_pipeline.py`: Assert `data/processed/encoded_alloys.csv` exists and has correct columns. **Requirement**: Assert the CSV contains exactly the columns defined in `code/models/alloy_entry.py` (e.g., `composition`, `bulk_modulus`, `shear_modulus`, `element_features`) with correct data types (floats for moduli, string for composition, list/array for features). The test must verify no nulls exist in `bulk_modulus` or `shear_modulus`.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/data_ingestion.py` to fetch OQMD data via HuggingFace `datasets.load_dataset('OQMD/elastic_properties')`, filter for entries with `bulk_modulus` and `shear_modulus` > 0, and exclude missing data. **Note**: This task implements the DFT proxy approach.
- [X] T013 [P] [US1] Implement `code/feature_encoder.py` to encode compositions using elemental fractions and periodic descriptors (atomic radius, electronegativity) fetched via `pymatgen` or `mendeleev` for all elements present.
- [X] T014 [US1] Add logic in `code/data_ingestion.py` to log "Insufficient data for statistical analysis (N < 500)" and **exit with code 1** if valid entries < 500.
- [ ] T015 [S] [US1] Implement `code/main.py` orchestration step to run ingestion and encoding, saving results to `data/processed/encoded_alloys.csv`. **Dependency**: T012 and T013 must be implemented before T015 can be fully tested, but T015 can be created in parallel. **Output**: Must produce `data/processed/encoded_alloys.csv` with no nulls in key columns.
- [X] T016 [US1] Add validation to ensure feature vectors include at least two periodic descriptors per element. Implement this in `code/feature_encoder.py` and add a corresponding test.
- [X] T017 [US1] Add logging for data ingestion counts (total fetched, filtered, encoded) using the infrastructure from T008.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Surrogate Model Training and Pareto Frontier Generation (Priority: P2)

**Goal**: Train CPU-based gradient-boosting models for Bulk/Shear moduli, generate synthetic points within the convex hull, and compute the Pareto frontier.

**Independent Test**: Train models on a fixed seed, generate synthetic points, verify Pareto frontier contains non-dominated points, and check that R² scores are reported.

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/model_training.py` to train separate GradientBoostingRegressor models for Bulk and Shear moduli using `n_jobs=2`. **Memory Constraint**: Do NOT use `max_memory` (unsupported); instead, enforce memory limits via `max_depth` and `subsample` parameters, and monitor peak memory usage using the `resource` module to ensure compliance with the <7GB RAM constraint.
- [ ] T021 [S] [US2] Implement Leave-One-System-Out Cross-Validation (LOSO-CV) in `code/model_training.py` to validate generalizability. **Output**: Must generate `data/processed/loso_test_points.csv` containing the held-out test data and `data/processed/model_validation_report.json` containing **system-level variance**, **coverage stats**, and **`uncertainty_variance` for each point**. **Constraint**: If the LOSO-CV R² score is <= 0.6, the script must raise a critical error and halt the pipeline. **Reliability Mask**: The script must prepare the data for the Reliability Mask by including `uncertainty_variance` for each point.
- [X] T022 [US2] Implement uncertainty calculation (cross-validation variance) in `code/model_training.py` and flag regions exceeding threshold.
- [ ] T023 [S] [US2] **Depends: T021, T022** Implement NSGA-II logic in `code/pareto_optimization.py` using `deap` with population=100, generations=50, cx_prob=0.9, mut_prob=0.1, objectives=[Bulk, Shear]. **Includes**: Generating synthetic points **strictly within** the convex hull of the training data. **CRITICAL**: Points falling outside the convex hull MUST be rejected (not flagged for inclusion) to comply with Constitution Principle VII. **Boundary Proximity**: The system MUST calculate the distance to the hull boundary for each point and **flag** any points approaching the boundary (distance < 5% of hull radius) in the output. **Reliability Mask**: The system MUST read `data/processed/model_validation_report.json` and apply a **Reliability Mask** to penalize or exclude points with high `uncertainty_variance`. **Timeout**: Implement a hard timeout using `signal.alarm` (Unix) or a watchdog thread (cross-platform) to enforce the 6-hour runtime constraint (21600 seconds); if timeout is reached, the script must log a warning and exit gracefully with the best frontier found so far. **Boundary Maximization**: The optimization logic must explicitly attempt to maximize points *at* the boundary (within the hull) to satisfy SC-003. **Output**: `data/results/pareto_frontier.csv` containing only valid, non-dominated points within the hull, with boundary proximity flags.
- [X] T023b [S] [US2] **Depends: T023** Implement logic to calculate and output the `boundary_proximity` metric (distance to hull boundary) for each point in the Pareto frontier, flagging those < 5% of hull radius as required by FR-004.
- [X] T024 [S] [US2] **Depends: T023, T023b, T024b** Implement metric calculation: Calculate the **percentage of the Pareto frontier that is strictly within the empirical convex hull** and **within the Rule of Mixtures bounds** (SC-003). Compare this against the percentage of the frontier that is dominated by the Rule of Mixtures bounds. **Algorithm**: Identify frontier points with (Bulk, Shear) within the training convex hull and theoretical bounds, divide by total frontier points. **Note**: The metric "percentage extending beyond hull" is invalid and must not be calculated.
- [X] T024b [S] [US2] **Depends: T007** Implement `code/physics_bounds.py` to calculate Rule of Mixtures bounds for Bulk and Shear Moduli based on elemental properties. Output: `data/processed/theoretical_bounds.json`.
- [X] T025 [US2] Add logic to clamp predictions to physical limits (e.g., moduli > 0) and flag extrapolated points.

### Tests for User Story 2 (MANDATORY) ⚠️

- [X] T018 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`: assert R² > 0.6, assert Pareto points are non-dominated.
- [X] T019 [P] [US2] Integration test for Pareto generation in `tests/integration/test_pareto_generation.py`: assert synthetic points are within convex hull (and flagged if outside - but rejected from final output).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Trade-Off Decoupling Analysis and Visualization (Priority: P3)

**Goal**: Identify compositional clusters with low correlation (decoupled regions) using **Local Correlation Estimation (LCE)** on **ilr-transformed** data, visualize them, and perform sensitivity analysis.

**Independent Test**: Run cluster analysis, verify a 2D plot is generated with decoupled regions highlighted, and correlation coefficients are reported.

### Implementation for User Story 3

- [X] T030 [S] [US3] Implement `code/cluster_analysis.py` to perform **Local Correlation Estimation (LCE)** on **ilr-transformed** compositional data (output from T029b). **Step 1**: Determine optimal neighborhood size `k` via the Elbow Method (calculate inertia for k=2 to k=10 using the Kneedle algorithm). **Step 2**: Run LCE with the **determined optimal k** (not a hardcoded value). **Note**: This task ONLY handles cluster count selection. It does NOT perform the correlation threshold sensitivity analysis. Output: `data/processed/clustering_results.csv` with cluster assignments and local correlation values.
- [X] T031 [S] [US3] Implement correlation calculation between Bulk and Shear Moduli for *each cluster* to find the minimum correlation region. **Include**: **Stratified Permutation Test** (1000 iterations, p < 0.05) to verify that the minimum correlation cluster is significantly lower than the global correlation (SC-002). **Output**: `data/processed/correlation_stats.csv` including cluster ID, local correlation, global correlation, delta, and **p-value** from the permutation test. Identify the specific cluster with the minimum correlation (Decoupled Region) in this step.
- [ ] T032 [S] [US3] **Depends: T031** Implement sensitivity analysis in `code/cluster_analysis.py` to sweep **decoupling threshold (correlation cutoff)** values across the range **[0.1, 0.9]** in steps of **0.1**. **Requirement**: **Apply varying correlation thresholds to the *fixed* clustering result from T030** (do NOT re-run LCE). Calculate and output a `robustness_score` (variance of the size of the cluster with the minimum correlation across cutoffs) to validate threshold robustness. Output: `data/processed/sensitivity_analysis.csv` with columns: `cutoff`, `region_size`, `mean_correlation`, `robustness_score`.
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
- **Spec Alignment**: Spec is updated to v1.4 to target **Bulk/Shear Moduli** and **Local Correlation Estimation (LCE)** with **ilr transform** and **permutation testing** per v1.4. Phase 0 is now a verification step (T000) that actively verifies content.
- **Ordering Note**: T029b (ilr transform) MUST precede T030 (LCE). T031 (Permutation Test) MUST precede T032 (Sensitivity Analysis). T032 defines sweep range [0.1, 0.9] with step 0.1. T035 depends on T031. T024 depends on T023, T023b, and T024b. T021 enforces the R² gate and includes `uncertainty_variance`.
- **Timeout Handling**: T023 includes explicit `signal.alarm` (Unix) or watchdog thread (cross-platform) implementation to enforce the 6h runtime constraint (cross-platform).
- **Output Artifacts**: T023b outputs boundary proximity flags. T031 outputs `data/processed/correlation_stats.csv` with p-values. T032 outputs `data/processed/sensitivity_analysis.csv` with robustness_score. T032b outputs `data/results/robustness_validation.json`. T021 outputs `data/processed/loso_test_points.csv` and `data/processed/model_validation_report.json` with `uncertainty_variance` per point.
- **Dependency Enforcement**: Tasks T012, T020, T030, T024, T035 explicitly depend on upstream artifacts to ensure data flow integrity.
- **Memory Management**: T020 uses `max_depth` and `subsample` for memory control, not `max_memory`.
- **Convex Hull Constraint**: T023 explicitly rejects points outside the hull and maximizes points *at* the boundary to ensure strict compliance with Constitution Principle VII and SC-003.
- **Versioning**: T005 is complete and includes verification step T005b.
- **Methodological Rigor**: T030 and T031 implement **Local Correlation Estimation (LCE)** with **ilr transform** and **stratified permutation test** to avoid tautology and ensure statistical validity.
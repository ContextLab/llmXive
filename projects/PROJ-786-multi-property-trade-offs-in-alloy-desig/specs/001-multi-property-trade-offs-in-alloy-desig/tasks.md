# Tasks: Multi-Property Trade-Offs in Alloy Design Using Public Compositional Data

**Input**: Design documents from `/specs/001-multi-property-trade-offs/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are **MANDATORY** - ensure they are written and fail before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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

## Phase 0: Spec Alignment (CRITICAL - BLOCKS ALL OTHER WORK)

**Purpose**: The current spec mandates "yield strength and elongation" but the plan pivots to "Bulk and Shear Moduli". This phase MUST be completed to update the spec before any implementation proceeds.
**Execution Order**: These tasks are marked **[S]** (Sequential) because they all edit `spec.md`. They must be executed in order to avoid merge conflicts and ensure consistent state.

- [ ] T000a [S] [Spec] Update `spec.md` FR-001, FR-003, US-1 to replace "yield strength and elongation" with "Bulk and Shear Moduli (DFT Proxies)". **Verification**: Verify FR-001 text matches regex for "Bulk and Shear Moduli". **Deliverable**: Updated `spec.md` file. <!-- FAILED: unspecified -->
- [ ] T000b [S] [Spec] Update `spec.md` SC-001 to replace "thermodynamic limits (Rule of Mixtures) for yield strength/elongation" with "DFT-derived physical bounds (Rule of Mixtures for Bulk/Shear)". **Verification**: Verify SC-001 text matches regex for "Bulk/Shear". **Deliverable**: Updated `spec.md` file.
- [ ] T000c [S] [Spec] Update `spec.md` FR-005, SC-002 to replace "strength and ductility" with "Bulk and Shear Moduli". **Verification**: Verify FR-005 text matches regex for "Bulk and Shear Moduli". **Deliverable**: Updated `spec.md` file.
- [ ] T000d [S] [Spec] Update `spec.md` US-1 Acceptance 1 to reference "Bulk and Shear Moduli" instead of "yield strength/elongation". **Verification**: Verify text matches. **Deliverable**: Updated `spec.md` file.
- [ ] T000e [S] [Spec] Update `spec.md` FR-003 to reference "Bulk and Shear Moduli" as the target for gradient-boosting regressors. **Verification**: Verify FR-003 text matches. **Deliverable**: Updated `spec.md` file.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Initialize Project Structure: Create `projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/` root, `code/`, `data/`, `tests/`, `docs/`, `data/raw/`, `data/processed/`, `tests/contract/`, `tests/integration/`, `tests/unit/` directories and populate with `.gitkeep` files.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` (pandas, scikit-learn, numpy, scipy, deap, matplotlib, seaborn, requests, pyyaml, pyarrow, pymatgen, mendeleev, python-dotenv).
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools.
- [ ] T004 [P] Setup `data/raw` and `data/processed` directory structure with `.gitkeep`.
- [X] T005 [P] Implement `code/versioning.py` script to compute SHA-256 hashes for data/code artifacts, update `state/projects/PROJ-786-...yaml` `artifact_hashes` map, set `updated_at` timestamp, and **explicitly invalidate stale review records** when hashes change. **Verification**: Script must output the updated YAML and a log confirming invalidation logic execution.
- [X] T005b [P] Verify `code/versioning.py` runs successfully on a dummy artifact and updates state YAML correctly.
- [X] T006 [P] Implement robust `.env` loading using `python-dotenv` in `code/config.py`. Ensure it gracefully handles missing `.env` files by loading defaults from a `config_default.yaml`. Expose `variance_threshold`, `random_seed`, and `data_source` as global constants.
- [X] T007 [P] Create base data models (Pydantic/JSON schema) for `AlloyEntry` in `code/models/alloy_entry.py`.
- [ ] T008 [P] Configure error handling and logging infrastructure (structured logs).
- [X] T009 [P] Implement `code/utils/convex_hull.py` wrapper for `scipy.spatial.ConvexHull` and `Delaunay` point-in-hull testing.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel (after Phase 0 spec update).

---

## Phase 3: User Story 1 - Data Extraction and Composition Encoding (Priority: P1) 🎯 MVP

**Goal**: Ingest public alloy data (OQMD via HuggingFace), filter for **Bulk and Shear Moduli** (DFT proxies), encode compositions, and output a clean CSV.

**Independent Test**: Run `code/data_ingestion.py` against a small OQMD subset; verify `data/processed/encoded_alloys.csv` exists, contains no nulls in key columns, and has correct feature vector dimensions.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`: Assert that when input has < 500 rows (generate a dummy CSV with 499 rows), the script logs the specific warning "Insufficient data for statistical analysis (N < 500)" and exits with code 0. Assert that when input has >= 500 rows, no warning is logged and exit code is 0.
- [X] T011 [P] [US1] Integration test for full ingestion pipeline in `tests/integration/test_ingestion_pipeline.py`: assert `data/processed/encoded_alloys.csv` exists and has correct columns.

### Implementation for User Story 1

- [X] T012 [US1] **Depends: T000a** Implement `code/data_ingestion.py` to fetch OQMD data via HuggingFace `datasets.load_dataset('OQMD/elastic_properties')`, filter for entries with `bulk_modulus` and `shear_modulus` > 0, and exclude missing data. **Note**: This task implements the DFT proxy approach AFTER spec update (T000a).
- [X] T013 [P] [US1] Implement `code/feature_encoder.py` to encode compositions using elemental fractions and periodic descriptors (atomic radius, electronegativity) fetched via `pymatgen` or `mendeleev` for all elements present.
- [X] T014 [US1] Add logic in `code/data_ingestion.py` to log "Insufficient data for statistical analysis (N < 500)" and exit with code 0 if valid entries < 500.
- [ ] T015 [US1] Implement `code/main.py` orchestration step to run ingestion and encoding, saving results to `data/processed/encoded_alloys.csv`.
- [ ] T016 [US1] Add validation to ensure feature vectors include at least two periodic descriptors per element.
- [ ] T017 [US1] Add logging for data ingestion counts (total fetched, filtered, encoded).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (after T000a-d).

---

## Phase 4: User Story 2 - Surrogate Model Training and Pareto Frontier Generation (Priority: P2)

**Goal**: Train CPU-based gradient-boosting models for Bulk/Shear moduli, generate synthetic points within the convex hull, and compute the Pareto frontier.

**Independent Test**: Train models on a fixed seed, generate synthetic points, verify Pareto frontier contains non-dominated points, and check that R² scores are reported.

### Implementation for User Story 2

- [X] T020 [P] [US2] **Depends: T000e** Implement `code/model_training.py` to train separate GradientBoostingRegressor models for Bulk and Shear moduli using `n_jobs=2` and `max_memory=7GB` constraints. **Note**: Targets Bulk/Shear Moduli AFTER spec update (T000e).
- [X] T021 [US2] Implement Leave-One-System-Out Cross-Validation (LOSO-CV) in `code/model_training.py` to validate generalizability.
- [X] T022 [US2] Implement uncertainty calculation (cross-validation variance) in `code/model_training.py` and flag regions exceeding threshold.
- [ ] T022b [US2] **Depends: T021, T022** Implement logic to explicitly link LOSO-CV results to uncertainty metrics by generating `data/processed/model_validation_report.json` containing system-level variance, coverage stats, and a flag for unreliable regions.
- [X] T023 [US2] Implement NSGA-II logic in `code/pareto_optimization.py` using `deap` with population=100, generations=50, cx_prob=0.9, mut_prob=0.1, objectives=[Bulk, Shear]. **Includes**: Generating synthetic points within convex hull, evaluating them, clamping predictions to physical limits (moduli > 0), flagging extrapolated points, and implementing timeout handling (signal.alarm) to enforce 6h runtime limit.
- [ ] T024 [US2] **Depends: T000b, T024b** Implement metric calculation: % of test points dominated by frontier and % of frontier dominating empirical set against **DFT-derived physical bounds (Rule of Mixtures for Bulk/Shear)** calculated in T024b.
- [ ] T024b [US2] **Depends: T000b** Implement `code/physics_bounds.py` to calculate DFT-derived Rule of Mixtures bounds for Bulk and Shear Moduli based on elemental properties. Output: `data/processed/theoretical_bounds.json`.
- [ ] T025 [US2] Add logic to clamp predictions to physical limits (e.g., moduli > 0) and flag extrapolated points.

### Tests for User Story 2 (MANDATORY) ⚠️

- [ ] T018 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`: assert R² > 0.6, assert Pareto points are non-dominated.
- [ ] T019 [P] [US2] Integration test for Pareto generation in `tests/integration/test_pareto_generation.py`: assert synthetic points are within convex hull.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (after T000a, T000e, T000b).

---

## Phase 5: User Story 3 - Trade-Off Decoupling Analysis and Visualization (Priority: P3)

**Goal**: Identify compositional clusters with low correlation (decoupled regions) using K-Means, visualize them, and perform sensitivity analysis.

**Independent Test**: Run cluster analysis, verify a 2D plot is generated with decoupled regions highlighted, and correlation coefficients are reported.

### Implementation for User Story 3

- [ ] T030 [US3] **Depends: T000c** Implement `code/cluster_analysis.py` to perform K-Means clustering on elemental fractions with k=5 (determined via Elbow Method). **Note**: Targets Bulk/Shear Moduli AFTER spec update (T000c).
- [ ] T031 [US3] Implement correlation calculation between Bulk and Shear Moduli for *each cluster* to find the minimum correlation region. Output: `data/processed/correlation_stats.csv`.
- [ ] T030b [US3] Identify the specific cluster with the minimum correlation (Decoupled Region) based on the output of T031. **Dependency**: Must complete T031 first.
- [ ] T034 [US3] Implement logic to flag regions where prediction variance exceeds the configured threshold (FR-006).
- [ ] T032 [US3] **Depends: T000c** Implement sensitivity analysis in `code/cluster_analysis.py` to sweep **decoupling threshold (correlation cutoff)** values across a representative range. **Requirement**: Calculate and output a `robustness_score` (variance of region sizes across cutoffs) to validate threshold robustness. Output: `data/processed/sensitivity_analysis.csv` with columns: `cutoff`, `region_size`, `mean_correlation`, `robustness_score`. **Dependency**: Must complete T030b first to define the baseline region.
- [ ] T032b [US3] **Depends: T032** Implement validation logic to compare `sensitivity_analysis.csv` results against SC-003 requirements and output `data/results/robustness_validation.json` confirming threshold robustness.
- [ ] T033 [US3] Implement `code/visualization.py` to generate a 2D plot showing compositional space, decoupled regions, and Pareto frontier.
- [ ] T035 [US3] Implement calculation of global vs. local correlation coefficients for SC-002.
- [ ] T035b [US3] **Depends: T000c, T035** Implement logic to explicitly calculate the delta/ratio between local and global correlation coefficients to satisfy SC-002 measurement requirement. **Dependency**: Must complete T035 first.
- [ ] T036 [US3] Add logging for identified decoupled region properties (cluster ID, correlation coefficient, size).

### Tests for User Story 3 (MANDATORY) ⚠️

- [ ] T028 [P] [US3] Contract test for visualization output in `tests/contract/test_visualization.py`: assert `data/results/decoupling_plot.png` is generated, is non-empty, and contains the expected legend labels: "Pareto Frontier", "Decoupled Region", "Empirical Data".
- [ ] T029 [P] [US3] Integration test for decoupling analysis in `tests/integration/test_decoupling_analysis.py`: assert min correlation cluster is identified correctly.

**Checkpoint**: All user stories should now be independently functional (after T000a-c).

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` (README, API docs for scripts).
- [ ] T038 Code cleanup and refactoring (remove debug prints, optimize imports).
- [ ] T039 Performance optimization (ensure memory usage < 7GB during NSGA-II).
- [ ] T040 [P] Additional unit tests in `tests/unit/` (encoder logic, convex hull checks).
- [ ] T041 Security hardening (validate all external data inputs).
- [ ] T042 Run `quickstart.md` validation to ensure end-to-end reproducibility.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Spec Alignment)**: NO dependencies - MUST be completed FIRST. Blocks all other phases. **Executed Sequentially [S]**.
- **Setup (Phase 1)**: Depends on Phase 0 completion.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion AND Phase 0 completion.
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) AND Phase 0 - No dependencies on other stories.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) AND Phase 0 - Depends on US1 data output (`data/processed/encoded_alloys.csv`).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) AND Phase 0 - Depends on US2 model outputs and US1 data.

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

1. Complete Phase 0: Spec Alignment (CRITICAL) - **Sequential**
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 (Sequential) + Setup + Foundational together
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
- **Spec Alignment**: All tasks now explicitly target **Bulk/Shear Moduli** and **K-Means clustering** as per updated plan. **Phase 0 tasks (T000a-e) MUST be completed to update the spec to match these targets.**
- **Ordering Note**: T030b (Identify Min Correlation) MUST precede T032 (Sensitivity Analysis). T032 is marked [~] (Incomplete) and depends on T030b. T035b depends on T035.
- **Timeout Handling**: T023 includes explicit timeout logic to enforce the 6h runtime constraint.
- **Output Artifacts**: T024b outputs `data/processed/theoretical_bounds.json`. T031/T035 output `data/processed/correlation_stats.csv`. T032 outputs `data/processed/sensitivity_analysis.csv` with robustness_score. T032b outputs `data/results/robustness_validation.json`.
- **Dependency Enforcement**: Tasks T012, T020, T030, T024, T035b explicitly depend on Phase 0 tasks (T000a-e) to ensure spec is updated before implementation.
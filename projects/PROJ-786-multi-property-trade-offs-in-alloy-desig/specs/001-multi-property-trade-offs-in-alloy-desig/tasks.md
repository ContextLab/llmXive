# Tasks: Multi-Property Trade-Offs in Alloy Design Using Public Compositional Data

**Input**: Design documents from `/specs/001-multi-property-trade-offs/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are **MANDATORY** - ensure they are written and fail before implementation.

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

- [ ] T001a Create `projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/` root directory
- [ ] T001b Create `code/`, `data/`, `tests/`, `docs/` subdirectories
- [ ] T001c Create `data/raw/` and `data/processed/` subdirectories
- [ ] T001d Create `tests/contract/`, `tests/integration/`, `tests/unit/` subdirectories
- [ ] T001e Create `projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/specs/001-multi-property-trade-offs/` directory structure
- [ ] T001f Create `.gitkeep` files in all empty directories

- [~] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, scikit-learn, numpy, scipy, deap, matplotlib, seaborn, requests, pyyaml, pyarrow, pymatgen, mendeleev)
- [~] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [~] T004 [P] Setup `data/raw` and `data/processed` directory structure with `.gitkeep`
- [~] T005 [P] Implement `code/versioning.py` script to compute SHA-256 hashes for data/code artifacts and update state YAML
- [~] T005b [P] Verify `code/versioning.py` runs successfully on a dummy artifact and updates state YAML correctly
- [~] T006 [P] Setup environment configuration management (`.env` loading, seed pinning) <!-- SKIPPED: YAML+regex parse failed (while scanning an alias
 in "<unicode string>", line 2, column 1:
 **Summary**: Implemented `code/c...
 ^
expected alphabetic or numeric character, but found '*'
 in "<unicode string>", line 2, column 2:
 **Summary**: Implemented `code/co...
 ^) -->
- [~] T006b [P] Implement CLI argument and `.env` support for `variance_threshold` parameter (FR-006) and verify it is read correctly by downstream tasks
- [~] T007 Create base data models (Pydantic/JSON schema) for `AlloyEntry` in `code/models/alloy_entry.py`
- [~] T008 Configure error handling and logging infrastructure (structured logs)
- [~] T009 Implement `code/utils/convex_hull.py` wrapper for `scipy.spatial.ConvexHull` and `Delaunay` point-in-hull testing

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Extraction and Composition Encoding (Priority: P1) 🎯 MVP

**Goal**: Ingest public alloy data (OQMD via HuggingFace), filter for **Bulk and Shear Moduli** (DFT proxies), encode compositions, and output a clean CSV.

**Independent Test**: Run `code/data_ingestion.py` against a small OQMD subset; verify `data/processed/encoded_alloys.csv` exists, contains no nulls in key columns, and has correct feature vector dimensions.

### Implementation for User Story 1

- [~] T012 [US1] Implement `code/data_ingestion.py` to fetch OQMD data via HuggingFace `datasets.load_dataset('OQMD/elastic_properties')`, filter for entries with `bulk_modulus` and `shear_modulus` > 0, and exclude missing data (FR-001). **Note**: This task implements the pivot to DFT proxies as documented in spec.md FR-001/US-1.
- [~] T013 [P] [US1] Implement `code/feature_encoder.py` to encode compositions using elemental fractions and periodic descriptors (atomic radius, electronegativity) fetched via `pymatgen` or `mendeleev` for all elements present (FR-002)
- [ ] T014 [US1] Add logic in `code/data_ingestion.py` to log "Insufficient data for statistical analysis (N < 500)" and exit with code 0 if valid entries < 500 (US-1 Acceptance 1)
- [ ] T015 [US1] Implement `code/main.py` orchestration step to run ingestion and encoding, saving results to `data/processed/encoded_alloys.csv`
- [ ] T016 [US1] Add validation to ensure feature vectors include at least two periodic descriptors per element
- [ ] T017 [US1] Add logging for data ingestion counts (total fetched, filtered, encoded)

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`: Assert that when input has < 500 rows, the script logs the specific warning and exits with code 0 (Graceful Failure). Assert that when input has >= 500 rows, no warning is logged and exit code is 0.
- [ ] T011 [P] [US1] Integration test for full ingestion pipeline in `tests/integration/test_ingestion_pipeline.py`: assert `data/processed/encoded_alloys.csv` exists and has correct columns

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Surrogate Model Training and Pareto Frontier Generation (Priority: P2)

**Goal**: Train CPU-based gradient-boosting models for Bulk/Shear moduli, generate synthetic points within the convex hull, and compute the Pareto frontier.

**Independent Test**: Train models on a fixed seed, generate synthetic points, verify Pareto frontier contains non-dominated points, and check that R² scores are reported.

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/model_training.py` to train separate GradientBoostingRegressor models for Bulk and Shear moduli using `n_jobs=2` and `max_memory=7GB` constraints (FR-003)
- [ ] T021 [US2] Implement Leave-One-System-Out Cross-Validation (LOSO-CV) in `code/model_training.py` to validate generalizability (FR-008)
- [ ] T022 [US2] Implement uncertainty calculation (cross-validation variance) in `code/model_training.py` and flag regions exceeding threshold (FR-006)
- [ ] T022b [US2] Implement logic to explicitly link LOSO-CV results (T021) to the uncertainty metrics (FR-006), ensuring FR-008 coverage is integrated with uncertainty flagging
- [ ] T023 [US2] Implement NSGA-II logic in `code/pareto_optimization.py` using `deap` with population=100, generations=50, cx_prob=0.9, mut_prob=0.1, objectives=[Bulk, Shear]. **Note**: This task includes generating synthetic points within the convex hull and evaluating them (FR-004).
- [ ] T025 [US2] Add logic to clamp predictions to physical limits (e.g., moduli > 0) and flag extrapolated points (Edge Case)
- [ ] T026 [US2] Implement metric calculation: % of test points dominated by frontier and % of frontier dominating empirical set against **Rule of Mixtures for Bulk/Shear** (SC-001)
- [ ] T027 [US2] Add convergence timeout handling to NSGA-II, logging a warning if incomplete (Edge Case)

### Tests for User Story 2 (MANDATORY) ⚠️

- [ ] T018 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`: assert R² > 0.6, assert Pareto points are non-dominated
- [ ] T019 [P] [US2] Integration test for Pareto generation in `tests/integration/test_pareto_generation.py`: assert synthetic points are within convex hull

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Trade-Off Decoupling Analysis and Visualization (Priority: P3)

**Goal**: Identify compositional clusters with low correlation (decoupled regions) using K-Means, visualize them, and perform sensitivity analysis.

**Independent Test**: Run cluster analysis, verify a 2D plot is generated with decoupled regions highlighted, and correlation coefficients are reported.

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/cluster_analysis.py` to perform K-Means clustering on elemental fractions with k=5 (determined via Elbow Method) (FR-005)
- [ ] T031 [US3] Implement correlation calculation between Bulk and Shear Moduli for each cluster to find the minimum correlation region (FR-005)
- [ ] T030b [US3] Identify the specific cluster with the minimum correlation (Decoupled Region) based on the output of T031 (FR-005)
- [ ] T034 [US3] Implement logic to flag regions where prediction variance exceeds the configured threshold (FR-006)
- [ ] T032 [US3] Implement sensitivity analysis in `code/cluster_analysis.py` to sweep **decoupling threshold (correlation cutoff)** values across a representative range. and output a CSV mapping cutoff to identified decoupled region size (FR-007)
- [ ] T033 [US3] Implement `code/visualization.py` to generate a 2D plot showing compositional space, decoupled regions, and Pareto frontier (US-3)
- [ ] T035 [US3] Implement calculation of global vs. local correlation coefficients for SC-002
- [ ] T035b [US3] Implement logic to explicitly calculate the delta/ratio between local and global correlation coefficients to satisfy SC-002 measurement requirement
- [ ] T036 [US3] Add logging for identified decoupled region properties (cluster ID, correlation coefficient, size)

### Tests for User Story 3 (MANDATORY) ⚠️

- [ ] T028 [P] [US3] Contract test for visualization output in `tests/contract/test_visualization.py`: assert plot file exists, assert decoupled region is highlighted
- [ ] T029 [P] [US3] Integration test for decoupling analysis in `tests/integration/test_decoupling_analysis.py`: assert min correlation cluster is identified correctly

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` (README, API docs for scripts)
- [ ] T038 Code cleanup and refactoring (remove debug prints, optimize imports)
- [ ] T039 Performance optimization (ensure memory usage < 7GB during NSGA-II)
- [ ] T040 [P] Additional unit tests in `tests/unit/` (encoder logic, convex hull checks)
- [ ] T041 Security hardening (validate all external data inputs)
- [ ] T042 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (`data/processed/encoded_alloys.csv`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model outputs and US1 data

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

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
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
- **Critical Data Constraint**: All data ingestion tasks MUST use real, reachable URLs (OQMD via HuggingFace) and NEVER synthesize fake input data.
- **Hardware Constraint**: All modeling tasks MUST run on CPU (2 cores, <7GB RAM). No CUDA, no 8-bit/4-bit quantization, no large LLMs.
- **Spec Alignment**: All tasks now explicitly target **Bulk/Shear Moduli** and **K-Means clustering** as per updated spec.md.
- **Ordering Note**: T031 (Correlation Calculation) MUST precede T030b (Min-Correlation Identification). T030 (Clustering) and T031 (Correlation) are sequential in data flow.
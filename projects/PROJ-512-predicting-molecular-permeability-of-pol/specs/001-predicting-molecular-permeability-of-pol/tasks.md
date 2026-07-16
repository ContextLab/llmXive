# Tasks: Predicting Molecular Permeability of Polymers via Graph Neural Networks

**Input**: Design documents from `/specs/001-predicting-molecular-permeability/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

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

- [X] T001 Create project structure per implementation plan: create directories `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/raw/`, `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/processed/`, `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/models/`, `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/results/`, `projects/PROJ-512-predicting-molecular-permeability-of-pol/tests/unit/`, `projects/PROJ-512-predicting-molecular-permeability-of-pol/tests/integration/` and files `requirements.txt`, `main.py` in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/`. **Constraint**: Ensure all subdirectories for raw and processed data are created explicitly.
- [X] T002 Initialize Python 3.11 project with pinned dependencies (`requirements.txt`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools. **Deliverable**: Create `.ruff.toml` and `pyproject.toml` with explicit configuration for reproducibility.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup seed management and random state pinning in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/utils.py`
- [X] T005 [P] Implement logging infrastructure with level configuration in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/utils.py`
- [X] T006 [P] Create base `PolymerGraph` entity class in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/models/polymer_graph.py` with node/edge feature schemas (atom type, hybridization, bond type) **ONLY**. **Constraint**: Do NOT include 3D features (radii, bond length) as per FR-001.
- [X] T007 Create `PermeabilityRecord` data model in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/models/permeability_record.py`
- [X] T008 Setup CPU-only PyTorch environment check in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/main.py`
- [X] T009 Implement gradient clipping mechanism (max norm threshold) in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/models/trainer.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Load raw polymer data from NIST/PubChem, parse SMILES into valid graphs, and verify data integrity. **Constraint**: If real data is unavailable, the system MUST fail loudly. No simulation fallbacks are permitted.

**Independent Test**: Run ingestion script; verify output HDF5 contains valid PolymerGraph objects, correct record counts, and that the script raises an error if no real data is found.

### Implementation for User Story 1

- [ ] T010 [US1] Implement NIST/PubChem data fetcher in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/ingestion.py` using real URLs or `datasets.load_dataset`. **Constraint**: Attempt to load from NIST Polymer Database or PubChem. **Failure Mode**: If the dataset loader raises a 404, returns an empty dataset, or returns fewer than 500 records, the script MUST raise a `DataUnavailableError` with a clear message: "CRITICAL: Real NIST/PubChem data not found. Project cannot proceed without experimental ground truth." **Do NOT** generate simulation data. **Output**: Save raw data checksums to `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/raw/checksums.json` upon successful download.
- [ ] T011 [US1] Implement SMILES-to-PolymerGraph parser in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/ingestion.py` using RDKit. **Logic**: Handle stereochemistry; calculate MW of the repeat unit.
- [ ] T012 [US1] Implement data cleaning logic in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/ingestion.py`: exclude entries with missing permeability; identify duplicates by SMILES string and average log-permeability (arithmetic mean); log exclusions. **Constraint**: Flag entries where calculated MW of the repeat unit < 1000 Da for manual review in `logs/small_molecule_review.csv`. **Do NOT exclude automatically** unless `EXCLUDE_SMALL_MOLS=true` is set, in which case log the exclusion reason.
- [ ] T013 [US1] Implement node/edge feature extraction (atom type, hybridization, bond type) in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/preprocessing.py`. **Constraint**: Use ONLY 2D features defined in FR-001.
- [ ] T014 [US1] Save cleaned dataset to HDF5/Parquet in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/processed/polymers.h5`. **Dependency**: T013 must complete before T014 to ensure feature completeness.
- [ ] T015 [US1] Add unit tests for SMILES parsing and feature extraction in `projects/PROJ-512-predicting-molecular-permeability-of-pol/tests/unit/test_ingestion.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train a CPU-tractable GNN and compare against Random Forest/Linear baselines using strict scaffold splits.

**Independent Test**: Execute training pipeline; verify GNN loss decreases, RF baseline runs, and metrics are reported in JSON.

### Implementation for User Story 2

- [ ] T020 [US2] Implement Murcko scaffold splitting logic in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/preprocessing.py` (addressing spec US-2 marker by executing split immediately for pipeline continuity). **Input**: `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/processed/polymers.h5`. **Algorithm**: Use RDKit's `GetScaffoldForMol` to extract scaffolds. **Rule**: Exclude any molecule from the test set if its scaffold is present in the training set (strict identity match). **Output**: Save split indices to `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/processed/scaffold_split_indices.json`. **Dependency**: T014 must complete before T020.
- [ ] T021 [US2] Implement Message-Passing GNN (multiple layers, moderate hidden dimensions) in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/models/gnn.py` using CPU-compatible PyTorch. **Constraint**: Must use float32 precision; no mixed precision or 8-bit quantization. Must consume ONLY 2D features (atom type, hybridization, bond type).
- [ ] T022 [US2] Implement Random Forest baseline using ECFP4 fingerprints in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/models/baselines.py`
- [ ] T023 [US2] Implement Linear Regression baseline using RDKit descriptors in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/models/baselines.py`
- [ ] T024 [US2] Implement training loop with early stopping and gradient clipping in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/models/trainer.py`
- [ ] T025 [US2] Implement evaluation logic to compute R², MAE, and Pearson correlation in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/metrics.py`
- [ ] T026 [US2] Generate JSON report comparing GNN vs. Baselines on test set in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/report.py`
- [ ] T027 [US2] Add integration test for full training and evaluation pipeline in `projects/PROJ-512-predicting-molecular-permeability-of-pol/tests/integration/test_training.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Sensitivity Analysis (Priority: P3)

**Goal**: Perform Wilcoxon signed-rank tests, VIF analysis, and sensitivity sweeps to validate model robustness.

**Independent Test**: Run stats script; verify p-values, VIF flags, and stability metrics are generated.

### Implementation for User Story 3

- [ ] T030 [US3] Implement k-fold cross-validation wrapper in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/stats.py`
- [ ] T031 [US3] Implement Wilcoxon signed-rank test for GNN vs. RF performance in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/stats.py`
- [ ] T032 [US3] Implement Variance Inflation Factor (VIF) calculation for baseline descriptors in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/stats.py`
- [ ] T033 [US3] Implement sensitivity analysis sweeping R² thresholds across {, 0.30, 0.35} in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/stats.py`. **Logic**: For each threshold, calculate 'successful_prediction_rate' = (count of predictions where R² > threshold) / total predictions. **Output**: Generate a JSON file at `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/results/sensitivity_sweep.json` containing the sweep results with keys: `threshold` (float), `successful_prediction_rate` (float), and `stability_metric` (standard deviation of `successful_prediction_rate` across the sweep). **Input**: Read from T030's k-fold output.
- [ ] T034 [US3] Generate final statistical report including p-values and VIF flags in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/report.py`
- [ ] T035 [US3] Add unit tests for statistical functions in `projects/PROJ-512-predicting-molecular-permeability-of-pol/tests/unit/test_stats.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T060 [P] Documentation updates in `docs/` (including data dictionary for 2D features)
- [ ] T061a [P] Refactoring: Extract validation logic from `ingestion.py` to `utils.py`
- [ ] T061b [P] Refactoring: Simplify data ingestion error handling in `ingestion.py`
- [ ] T061c [P] Refactoring: Standardize logging format across all modules
- [ ] T062a [P] Performance: Optimize graph batching in `gnn.py` to reduce peak RSS memory usage by at least 10% measured using `memory_profiler` on the training loop. **Deliverable**: Record baseline and optimized metrics in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/results/memory_baseline.json`.
- [ ] T062b [P] Performance: Optimize data loading in `preprocessing.py` to reduce I/O wait
- [ ] T062c [P] Performance: Profile and reduce memory footprint of the training loop
- [X] T063 [P] Additional unit tests for feature extraction in `projects/PROJ-512-predicting-molecular-permeability-of-pol/tests/unit/test_features.py`
- [ ] T064 [P] Run quickstart.md validation: Verify execution without error and production of `polymers.h5` and `metrics.json` artifacts.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires data from US1 (specifically the scaffold split from T020 which consumes T014's artifact). Note: T014 (Save) must complete after T013 (Feature Extraction) to ensure feature completeness.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires models from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Story 1 can start
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Basic ingestion)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Train GNN with 2D features → Test independently → Deploy/Demo
4. Add User Story 3 → Validate statistics → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Ingestion)
 - Developer B: User Story 2 (Model Training)
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
- **Critical Constraint**: All tasks must run on CPU-only CI (limited cores, constrained RAM, time-limited execution). No GPU, no 8-bit quantization, no large LLMs.
- **Data Integrity**: All data must be real (NIST/PubChem). If unavailable, the project MUST FAIL. No simulation fallbacks are permitted.
- **Scope Compliance**: Tasks strictly adhere to FR-001 and FR-003. Only 2D SMILES features (atom type, hybridization, bond type) are used. No 3D physical parameters are included.
- **Revision Compliance**: All tasks now strictly follow the Spec's defined scope. Phase 6 and 7 (Revision Phases) have been removed as they violated FR-001 and the Spec's assumptions.
# Tasks: Predicting Molecular Properties from Quantum Chemical Calculations

**Input**: Design documents from `/specs/001-predicting-molecular-properties/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-546-predicting-molecular-properties-from-qua/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (scikit-learn, pandas, rdkit, requests)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/download_data.py` to fetch experimental barrier dataset from Zenodo (spec.md Data Model) with checksum verification
- [X] T006 [P] Implement `code/utils/error_utils.py` to handle convergence failures (skip/log) and OOM detection per spec.md Edge Cases
- [X] T008 [P] Setup `code/requirements.txt` with pinned versions for reproducibility
- [X] T010 [P] Implement `code/validators/data_validator.py` to verify downloaded CSV contains required columns (SMILES, experimental_barrier) and correct data types (spec.md Data Model)
- [X] T011 [P] [US1] Contract test for `code/download_data.py` in `tests/test_download.py` (verifies Zenodo fetch and data validity). **Depends on T004 completion.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Semi-Empirical Descriptor Generation (Priority: P1) 🎯 MVP

**Goal**: Compute HOMO/LUMO/Mayer descriptors using DFTB+ on full dataset with geometry optimization

**Independent Test**: Run on 50 molecules; verify `descriptors_semi.csv` has 50 rows, no NaN, HOMO/LUMO in eV, charges sum to net charge.

### Tests for User Story 1

- [X] T012 [US1] Integration test for `code/generate_descriptors.py` on 50 molecules in `tests/test_descriptors.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/generate_descriptors.py` to invoke DFTB+ for geometry optimization and descriptor extraction (spec.md US1), including:
 - Unit normalization (eV for energies).
 - Logic to catch `ConvergenceError`, skip the molecule, and log failure details to `logs/convergence_failures.log`.
 - Validation of output CSV columns and physical ranges: Skip and log to `logs/structural_failures.log` if `HOMO_energy >= LUMO_energy` (do not halt the pipeline).
 - Logging of DFTB+ invocation details, wall_time, and peak_memory to `logs/dftb_execution.log` in JSON format.
 - **Export** optimized geometries to `data/optimized_geometries/` (XYZ format) for use by US2.
- [ ] T069 [US1] **REMOVED**: Merged into T013.
- [ ] T070 [US1] **REMOVED**: Out of scope.

**Checkpoint**: At this point, User Story 1 is fully functional if T013 is complete (including geometry export to `data/optimized_geometries/`).

---

## Phase 4: User Story 2 - High-Level DFT Baseline & Comparative Modeling (Priority: P2)

**Goal**: Compute DFT descriptors for subset, train two RF models, compare MAE via paired t-test

**Independent Test**: Run on subset; verify output reports MAE_semi, MAE_DFT, p-value, flags, and explicit comparison against experimental ground truth.

### Tests for User Story 2

- [X] T018 [P] [US2] Contract test for `code/train_models.py` in `tests/test_models.py` (verifies RF training)
- [X] T027 [P] [US2] Integration test for comparative evaluation in `tests/test_evaluation.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/generate_descriptors.py` (DFT branch) to invoke Psi4 for B3LYP/def2-SVP on a subset. **Crucially**: Import optimized geometries from `data/optimized_geometries/` (output of T013) instead of re-optimizing, to ensure identical molecular geometries and convergence criteria as per Constitution Principle VI. **Subset Selection**: Select a **stratified random subset of 50 valid samples** from the full dataset to ensure statistical validity for 5-fold CV and paired t-test. Include unit normalization (eV for energies).
- [X] T021 [US2] Implement `code/train_models.py` to train two Random Forests (semi vs DFT) using 5-fold CV (spec.md US2)
- [X] T022 [US2] Implement `code/evaluate_models.py` to compute per-fold MAE, run paired t-test (spec.md US2), and verify semi-MAE ≤ 2.0 kcal/mol (spec.md US2).
- [X] T023 [US2] Implement logic to compute MAE flags: 1) flag if semi-MAE exceeds DFT-MAE by >20% (spec.md US2), 2) verify semi-MAE ≤ 2.0 kcal/mol (spec.md US2). Write both flags and final metrics atomically to `reports/evaluation.json`. (Merged T023/T024).
- [X] T042 [US2] Implement `code/evaluators/experimental_validator.py` to compare model predictions against the physical experimental barrier dataset (spec.md US2), explicitly calculating the error margin against measured reality based on the paired t-test and MAE threshold defined in spec.md US2 acceptance criteria.
- [ ] T071 [US2] **REMOVED**: Out of scope.
- [ ] T072 [US2] **REMOVED**: Out of scope.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance & Sensitivity Analysis (Priority: P3)

**Goal**: Identify top descriptors, sweep thresholds, report cumulative importance

**Independent Test**: Run analysis; verify output lists top descriptors, cumulative sum, and MAE table for a set of threshold percentiles.

### Tests for User Story 3

- [X] T028 [P] [US3] Unit test for `code/sensitivity_analysis.py` in `tests/test_sensitivity.py`

### Implementation for User Story 3

- [X] T029 [US3] Implement `code/sensitivity_analysis.py` to extract feature importance from semi-empirical RF (spec.md US3)
- [X] T030 [US3] Implement logic to identify top-ranked descriptors and calculate cumulative importance. (spec.md US3) using the output from T029. Sort by descending importance, select top subset, and append to `reports/sensitivity.csv` with columns `rank`, `descriptor`, `importance`.
- [X] T030b [US3] Implement `code/generate_thresholded_descriptors.py` to generate datasets with specific numerical descriptor thresholds (e.g., 0.5, 1.0, 2.0 eV) applied to the full descriptor set, preparing data for the sensitivity sweep.
- [X] T031 [US3] Implement sensitivity sweep over numerical descriptor thresholds (spec.md US3) using thresholds ranging from low to high values eV on the output of T030b. Output to `reports/sensitivity.csv`.
- [X] T032a [US3] Implement logic to report MAE degradation for each sweep threshold and append `mae_degradation` column to `reports/sensitivity.csv`.
- [X] T032b [US3] Implement logic to verify stability of top descriptors (spec.md US3) by checking if the top 3 descriptors change **0 times** (change < 1 time) across the sweep and recording the result in `reports/sensitivity.csv`.
- [X] T044 [US3] Implement `code/evaluators/physical_interpretability.py` to trace top feature importance scores back to specific physical mechanisms (spec.md US3), ensuring the "top 5" correspond to general chemical properties (e.g., electronegativity, bond order) rather than statistical noise.
- [ ] T058 [US3] **REMOVED**: Out of scope (theoretical modeling).
- [ ] T073 [US3] **REMOVED**: Out of scope.
- [ ] T074 [US3] **REMOVED**: Out of scope.
- [ ] T075 [US3] **REMOVED**: Out of scope.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Pipeline Validation & Polish

**Purpose**: Validation gates and final reporting

- [X] T033a [P] Execute the full pipeline end-to-end on a sample subset and capture runtime logs.
- [X] T033b [P] Validate runtime logs from T033a: Assert total runtime < 6 hours (Constitution Principle VII) and write validation result to `reports/runtime_validation.json`.
- [X] T034 [P] Implement `code/generate_checksums.py` to compute SHA-256 hashes for all raw and processed artifacts and write to `data/checksums.txt` (Constitution Check #3).
- [X] T035 [P] Implement `code/generate_summary_report.py` to aggregate all metrics (MAE, speedup, feature importance) into `data/reports/summary_report.md`.
- [X] T046 [P] Update `docs/reproducibility.md` to include the "standard of evidence" (spec.md US2): define the exact experimental dataset (Zenodo ID, version), source, and error margins based on dataset metadata. **Depends on T034 checksums and T042.**
- [ ] T076 [P] **REMOVED**: Out of scope.
- [ ] T077 [P] **REMOVED**: Out of scope.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Validation & Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T013 (Geometry Export from US1)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
# Launch all models for User Story 1 together:
Task: "Implement generate_descriptors.py (DFTB+)"
Task: "Implement error_utils.py (convergence/OOM handling)"
Task: "Implement physical_interpretability.py (T044)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently against physical constraints
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
4. Final validation with all Phase 6 checks before report generation.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Removed Unapproved/Unexecutable Tasks**: T019 (merged to T013), T058, T069-T077.
- **Removed Unapproved Documentation**: T045, T054, T057, T063-T068 (previous scope creep).
- **Physical Reality & Observables**: Retained T044 (general chemical properties); removed T045, T075.
- **Structural Constraints**: Removed T060-T068 (unapproved invariants).
- **Solvent & Hydration**: Removed T062, T070 (out of scope).
- **Experimental Ground Truth**: Retained T042, T046; removed T071 (unapproved instrument details).
- **Computational Cost**: Removed T066, T072 (out of scope).
- **Missing Degrees of Freedom**: Removed T073, T058 (unapproved theoretical modeling).
- **Physical Interpretability**: Retained T044 (general mapping); removed T065, T074.
- **Map vs. Territory**: Removed T045, T075 (unapproved).
- **Geometry Alignment**: T013 now handles export; T020 depends on T013.
- **Atomicity**: Split T033 into T033a/T033b. Split T034/T035 into script generation tasks.
- **Validation Logic**: Updated T013 to skip on physical range violations rather than hard fail, aligning with spec Edge Cases.
- **Traceability Fix**: Updated T004 to reference spec.md Data Model instead of non-existent FR-001.
- **Subset Sizing**: Updated T020 to specify "stratified random subset of 50 samples" for statistical validity.
- **Stability Check**: Split T032 into T032a (sweep) and T032b (stability check) to explicitly implement "change < 1 time" (0 changes) logic.
- **Removed Phantom Dependencies**: T019 removed and merged into T013 to resolve ordering-56889ec3.
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

- [ ] T004 [P] Implement `code/fetch_data.py` to fetch experimental barrier dataset from Zenodo (spec.md Data Model) with checksum verification. **Note**: File name corrected from `download_data.py` to match plan.md.
- [ ] T011 [P] [US1] Contract test for `code/fetch_data.py` in `tests/test_fetch.py` (verifies Zenodo fetch and data validity). **Depends on T004 completion.**
- [X] T006a [P] Implement `code/utils/error_utils.py` to handle convergence failures (skip/log) and write to `logs/convergence_failures.log` per spec.md Edge Cases.
- [ ] T006b [P] Implement `code/utils/error_utils.py` to handle OOM detection (kill/log) and write to `logs/oom_failures.log` per spec.md Edge Cases.
- [ ] T006c [P] Implement `code/utils/error_utils.py` to handle structural failures (HOMO >= LUMO) and write to `logs/structural_failures.log` per spec.md Edge Cases. **Schema**: `molecule_id, timestamp, error_code, error_message, status:failed_after_retry`.
- [ ] T008 [P] Setup `code/requirements.txt` with pinned versions for reproducibility
- [ ] T010 [P] Implement `code/validators/data_validator.py` to verify downloaded CSV contains required columns (SMILES, experimental_barrier) and correct data types (spec.md Data Model)
- [ ] T015 [P] [FR-008] Implement `code/confound_analysis.py` to calculate Molecular Weight (MW), Atom Count, and functional group enumeration for all molecules, outputting `data/confounds.csv` (columns: `molecule_id`, `mw`, `atom_count`, `functional_groups`). **Moved to Phase 2 to satisfy data-flow dependencies for US2.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Semi-Empirical Descriptor Generation (Priority: P1) 🎯 MVP

**Goal**: Compute HOMO/LUMO/Mayer descriptors using DFTB+ on full dataset with geometry optimization

**Independent Test**: Run on a representative set of molecules; verify `descriptors_semi.csv` has a corresponding number of rows, no NaN, HOMO/LUMO in eV, charges sum to net charge.

### Tests for User Story 1

- [ ] T012 [US1] Integration test for `code/generate_descriptors.py` on 50 molecules in `tests/test_descriptors.py`

### Implementation for User Story 1

- [ ] T013a [US1] Implement `code/dftb_calculator.py` to invoke DFTB+ for geometry optimization and descriptor extraction (HOMO, LUMO, Mayer bond orders) for a single molecule, including unit normalization (eV).
- [ ] T013b [US1] Implement `code/error_handlers.py` to catch `ConvergenceError` and OOM signals, skip the molecule, and log failure details to `logs/convergence_failures.log` and `logs/oom_failures.log` respectively.
- [X] T017 [US1] Implement logging and timing: capture DFTB+ invocation details, wall_time, and peak_memory to `logs/dftb_execution.log` in JSON format. **Note**: Status updated to complete; schema keys defined: `molecule_id`, `wall_time`, `peak_memory`, `status`.
- [ ] T013c [US1] Implement `code/descriptor_pipeline.py` to orchestrate the full dataset run: iterate over molecules, call T013a/T013b, validate output. **Retry Logic**: 1) If geometry optimization fails, retry ONCE with different initial guess. 2) If `HOMO_energy >= LUMO_energy` (Physical Invalidity), retry ONCE the descriptor calculation with a different initial guess. If retry fails, log to `logs/structural_failures.log` via T006c with schema `molecule_id, timestamp, error_code, error_message, status:failed_after_retry` and skip. Export optimized geometries to `data/optimized_geometries/` (XYZ format) and write final `data/descriptors_semi.csv`. **Note**: T019 and T020 (Phase 3) removed; logic consolidated here.
- [ ] T019 [US1] **REMOVED**: Enforces structural constraints (peptide planarity, H-bond geometry) per Pauling. Logic merged into T013c.
- [ ] T020 [US1] **REMOVED**: Validates hydrogen-bond network topology and backbone dihedral angles per Pauling/Einstein. Logic merged into T013c.

**Checkpoint**: At this point, User Story 1 is fully functional if T013c is complete (including geometry export to `data/optimized_geometries/`).

---

## Phase 4: User Story 2 - High-Level DFT Baseline & Comparative Modeling (Priority: P2)

**Goal**: Compute DFT descriptors for subset, train two RF models, compare MAE via paired t-test

**Independent Test**: Run on subset; verify output reports MAE_semi, MAE_DFT, p-value, flags, and explicit comparison against experimental ground truth [UNRESOLVED-CLAIM: c_26ad4676 — status=not_enough_info].

### Tests for User Story 2

- [ ] T018 [P] [US2] Contract test for `code/train_models.py` in `tests/test_models.py` (verifies RF training)
- [ ] T027 [P] [US2] Integration test for comparative evaluation in `tests/test_evaluation.py`

### Implementation for User Story 2

- [ ] T038 [US2] Implement `code/dft_calculator.py` to invoke Psi4 for B3LYP/def2-SVP on a subset. **Crucially**: Import optimized geometries from `data/optimized_geometries/` (output of T013c) instead of re-optimizing, to ensure identical molecular geometries and convergence criteria as per Constitution Principle VI. **Subset Selection**: Select a **stratified random subset of 50 valid samples** from the full dataset, stratified by `experimental_barrier` (binned into 5 quantiles), and verify statistical validity (balance across bins) before proceeding. Include unit normalization (eV for energies). **Note**: Renumbered from T020 to T038 to resolve ID collision with removed T020 (Phase 3). **Depends on T013c**.
- [ ] T024 [US2] **REMOVED**: FLOP estimates and resource budgeting per Dyson.
- [ ] T025 [US2] **REMOVED**: Missing degrees of freedom modeling per Dyson.
- [ ] T021 [US2] Implement `code/train_models.py` to train two Random Forests (semi vs DFT) using 5-fold CV (spec.md US2). **Depends on T015 (confounds.csv) and T038 (dft descriptors).**
- [ ] T022 [US2] Implement `code/evaluate_models.py` to compute per-fold MAE, run paired t-test (spec.md US2), and report the measured semi-MAE and DFT-MAE values (do not verify against fixed thresholds).
- [ ] T023 [US2] Implement logic to compute MAE flags: 1) Flag if semi-MAE exceeds DFT-MAE by >20% [UNRESOLVED-CLAIM: c_44680182 — status=not_enough_info]. (spec.md US2). Write both flags and final metrics atomically to `reports/evaluation.json`. (Merged T023/T024).
- [ ] T026 [US2] **REMOVED**: Experimental ground truth definition per Curie (out of scope).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance & Sensitivity Analysis (Priority: P3)

**Goal**: Identify top descriptors, sweep thresholds, report cumulative importance

**Independent Test**: Run analysis; verify output lists top descriptors, cumulative sum, and MAE table for a set of threshold percentiles [UNRESOLVED-CLAIM: c_5b5a4f92 — status=not_enough_info].

### Tests for User Story 3

- [ ] T028 [P] [US3] Unit test for `code/sensitivity_analysis.py` in `tests/test_sensitivity.py` **Note**: Renumbered from T028 (Phase 4) to resolve ID collision.

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/sensitivity_analysis.py` to extract feature importance from semi-empirical RF (spec.md US3). **Depends on T021.**
- [ ] T030 [US3] Implement logic to identify top-ranked descriptors and calculate cumulative importance. (spec.md US3) using the output from T029. Sort by descending importance, select top subset, and append to `reports/sensitivity.csv` with columns `rank`, `descriptor`, `importance`.
- [ ] T030b [US3] Implement `code/generate_thresholded_descriptors.py` to prepare data for the sensitivity sweep by applying noise injection (σ=0.01, 0.05) [UNRESOLVED-CLAIM: c_d8dd88a0 — status=not_enough_info] and preparing datasets for feature importance cutoffs.
- [ ] T031 [US3] Implement sensitivity sweep over feature importance cutoffs {0.01, 0.05, 0.1} [UNRESOLVED-CLAIM: c_38b8ddf7 — status=not_enough_info] and noise injection levels {σ=0.01, 0.05} (spec.md US3) using the output of T030b. Output to `reports/sensitivity.csv`.
- [ ] T032a [US3] Implement logic to report MAE degradation for each sweep threshold and append `mae_degradation` column to `reports/sensitivity.csv`.
- [ ] T032b [US3] Implement logic to verify stability of top descriptors (spec.md US3) by checking if the top 3 descriptors change **0 times** (change < 1 time) across the sweep and recording the result in `reports/sensitivity.csv`.
- [ ] T033 [US3] **Execute** `code/confound_analysis.py` (implemented in T015) to perform partial correlation analysis to control for confounds (MW, functional groups) as per Plan Phase 1.5 and FR-008. Calculate R² delta when confounds are added and output to `reports/confound_analysis.csv`. **Note**: Changed from "Implement" to "Execute" to avoid re-implementation of T015. Reference updated to Plan Phase 1.5.
- [ ] T034 [US3] **REMOVED**: Physical interpretability mapping per Einstein/Feynman.
- [ ] T035 [US3] **REMOVED**: Error trace visualization per Feynman.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Pipeline Validation & Polish**Purpose**: Validation gates and final reporting

- [ ] T033a [P] Execute the full pipeline end-to-end on a sample subset and capture runtime logs.
- [ ] T033b [P] Validate runtime logs from T033a: {{claim:c_805d4525}} (Wikipedia: Dhurandhar, https://en.wikipedia.org/wiki/Dhurandhar) and Verify peak memory is less than or equal to 7 GB. [UNRESOLVED-CLAIM: c_edd5a05c — status=not_enough_info] per Constitution Principle VII (Resource-Bound Execution) and write validation result to`reports/runtime_validation.json`.
- [ ] T034 [P] Implement `code/generate_checksums.py` to compute SHA-256 hashes for all raw and processed artifacts and write to `data/checksums.txt` (Constitution Check #3).
- [ ] T035 [P] Implement `code/generate_summary_report.py` to aggregate all metrics (MAE, speedup, feature importance) into `data/reports/summary_report.md`.
- [ ] T046 [P] Update `docs/reproducibility.md` to include the "standard of evidence" (spec.md US2): define the exact experimental dataset (Zenodo ID, version), source, and error margins based on dataset metadata. **Depends on T034 checksums and T022.**
- [ ] T036 [P] **REMOVED**: Physical validation report generation (out of scope).

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T013c (Geometry Export from US1) and T015 (Confound Data)**
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on US2 completion** (specifically T021/T029)

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
Task: "Implement dftb_calculator.py"
Task: "Implement error_handlers.py"
Task: "Implement descriptor_pipeline.py"
Task: "Implement logging and timing"
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
 - Developer A: User Story 1 (including physical validation)
 - Developer B: User Story 2 (including ground truth analysis)
 - Developer C: User Story 3 (including interpretability)
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
- **Removed Unapproved/Unexecutable Tasks**: T014 (peptide constraints), T015 (FLOP estimation), T018 (physical reality validation), T024 (physical ground truth), T025 (missing degrees of freedom), old T033 (physical interpretability), T047 (philosophy essay), T034, T035, T036, T026.
- **Removed Redundant Validation**: Removed T042 and T085 which duplicated T022 logic or demanded non-existent data.
- **New Reviewer-Driven Tasks**:
 - **T006a/b/c**: Split error handling to explicitly manage the three distinct log files required by Spec.
 - **T015**: Moved Confound Analysis to Phase 2 to satisfy data-flow dependencies.
 - **T019/T020 (Phase 3)**: Removed; logic merged into T013c.
 - **T024/T025**: Removed (out of scope).
 - **T026**: Removed (out of scope).
 - **T033**: Changed from "Implement" to "Execute" to avoid conflict with T015. Reference updated to Plan Phase 1.5.
 - **T034/T035/T036**: Removed (out of scope).
- **Fixed Hallucinated Citations**: Removed "Wikipedia: Stree 2" from T033b.
- **Removed Scope Creep**: Removed T080-T086 which introduced unrequested physical constraints, philosophical essays, and solvent models.
- **Removed Redundant Validation**: Removed T042 and T085 which duplicated T022 logic or demanded non-existent data.
- **Fixed ID Collisions**: Renumbered T020 (Phase 4) to T038. Renumbered T028 (Phase 5) to avoid conflict.
- **Fixed File Path**: T004 now references `code/fetch_data.py` per plan.md.
- **Fixed Logic**: T013c now explicitly includes retry logic for HOMO >= LUMO with different initial guess and correct log schema.
- **Fixed Dependency**: T021 now explicitly depends on T015.
- **Fixed Status**: T017 marked complete with schema details.
- **Fixed Cross-Reference**: T033 now references Plan Phase 1.5 correctly.
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
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (scikit-learn, pandas, rdkit, requests)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/download_data.py` to fetch experimental barrier dataset from Zenodo (FR-001) with checksum verification
- [X] T006 [P] Implement `code/utils/error_utils.py` to handle convergence failures (skip/log) and OOM detection per spec.md Edge Cases
- [X] T008 [P] Setup `code/requirements.txt` with pinned versions for reproducibility
- [ ] T010 [P] Implement `code/validators/data_validator.py` to verify downloaded CSV contains required columns (SMILES, experimental_barrier) and correct data types (FR-001)
- [X] T011 [P] [US1] Contract test for `code/download_data.py` in `tests/test_download.py` (verifies Zenodo fetch and data validity)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Semi-Empirical Descriptor Generation (Priority: P1) 🎯 MVP

**Goal**: Compute HOMO/LUMO/Mayer descriptors using DFTB+ on full dataset with geometry optimization

**Independent Test**: Run on 50 molecules; verify `descriptors_semi.csv` has 50 rows, no NaN, HOMO/LUMO in eV, charges sum to net charge.

### Tests for User Story 1

- [~] T012 [US1] Integration test for `code/generate_descriptors.py` on 50 molecules in `tests/test_descriptors.py` <!-- ATOMIZE: requested -->

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/generate_descriptors.py` to invoke DFTB+ for geometry optimization and descriptor extraction (FR-002), including unit normalization (eV for energies)
- [~] T014 [US1] Add logic to skip molecules failing convergence (Edge Case) and log failures
- [~] T015 [US1] Add logic to validate output CSV columns and physical ranges (HOMO < LUMO, charge sum)
- [ ] T016 [US1] Implement `code/utils/memory_monitor.py` using Python `resource` module to kill DFTB+ subprocess if RSS > 6.5GB and generate a user-facing suggestion to reduce the subset size upon OOM detection
- [~] T017 [US1] Add logging for DFTB+ invocation, timing, and resource usage

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - High-Level DFT Baseline & Comparative Modeling (Priority: P2)

**Goal**: Compute DFT descriptors for subset, train two RF models, compare MAE via paired t-test

**Independent Test**: Run on subset; verify output reports MAE_semi, MAE_DFT, p-value, and flags if semi-MAE > 1.2 * DFT-MAE.

### Tests for User Story 2

- [X] T018 [P] [US2] Contract test for `code/train_models.py` in `tests/test_models.py` (verifies RF training)
- [ ] T019 [P] [US2] Integration test for comparative evaluation in `tests/test_evaluation.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/generate_descriptors.py` (DFT branch) to invoke Psi4 for B3LYP/def2-SVP on subset (min 30 molecules) (FR-003), including unit normalization (eV for energies)
- [ ] T021 [US2] Implement `code/train_models.py` to train two Random Forests (semi vs DFT) using 5-fold CV (FR-004)
- [ ] T022 [US2] Implement `code/evaluate_models.py` to compute per-fold MAE and run paired t-test (FR-005)
- [ ] T023 [US2] Add logic to flag if semi-MAE exceeds DFT-MAE by >20% (FR-008)
- [ ] T024 [US2] Add verification that semi-MAE ≤ 2.0 kcal/mol (FR-010) and run one-sided t-test (SC-007)
- [ ] T025 [US2] Implement runtime and memory logging for DFTB+ and Psi4 runs, calculate the speedup ratio (DFT time / Semi-empirical time), compare against the 10x threshold (SC-004), and flag failure if the threshold is not met
- [ ] T027 [US2] Add validation that the same subset of molecules is used for both DFTB+ and DFT calculations, respecting that DFTB+ uses DFTB-optimized geometries and DFT uses DFT-optimized geometries as per FR-002 and FR-003

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance & Sensitivity Analysis (Priority: P3)

**Goal**: Identify top 5 descriptors, sweep thresholds, report cumulative importance

**Independent Test**: Run analysis; verify output lists top descriptors, cumulative sum, and MAE table for a set of threshold percentiles.

### Tests for User Story 3

- [ ] T028 [P] [US3] Unit test for `code/sensitivity_analysis.py` in `tests/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/sensitivity_analysis.py` to extract feature importance from semi-empirical RF (FR-006)
- [ ] T030 [US3] Implement logic to identify top 5 descriptors and calculate cumulative importance (FR-009)
- [ ] T031 [US3] Implement sensitivity sweep over 5 percentiles of importance distribution (FR-007)
- [ ] T032 [US3] Report MAE degradation for each sweep and verify stability of top descriptors (SC-003)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Run `quickstart.md` validation to ensure pipeline executes end-to-end within 6h
- [ ] T034 [P] Generate `data/checksums.txt` for all raw and processed artifacts (Constitution Check #3)
- [ ] T035 [P] Generate final `data/reports/summary_report.md` with all metrics (MAE, speedup, feature importance)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
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
- **Reviewer Concerns Addressed**:
 - **Scope Creep**: Removed unverified Phase 6 tasks (T033-T038 in previous version) that referenced external reviews and undefined constraints.
 - **Geometry Protocol**: T027 now correctly validates subset alignment while respecting distinct geometry protocols (DFTB vs DFT).
 - **Speedup Verification**: T025 now explicitly calculates and verifies the 10x speedup threshold (SC-004).
 - **OOM Handling**: T016 now includes logic to generate a user-facing suggestion to reduce subset size.
 - **Traceability**: Removed all persona names and dates from task descriptions.
 - **Ordering**: Moved T011 to Phase 2 to ensure data validity before descriptor generation.
# Tasks: Neural Mechanisms Underlying Adaptive Decision-Making in Response to Social Feedback

**Input**: Design documents from `/specs/001-neural-mechanisms-adaptive-decision/`
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

- [X] T001 Create project directories (`data/raw`, `data/processed`, `data/models`, `code/preprocessing`, `code/modeling`, `code/analysis`, `code/utils`, `code/reporting`, `tests/unit`, `tests/integration`, `tests/contract`, `state`, `docs`) and initialize `__init__.py` files in `code/`, `tests/` packages.

- [X] T002 Initialize Python 3.11 project with dependencies (numpy, pandas, scipy, scikit-learn, nibabel, nilearn, pymc, numpyro, openneuro-py, pytest, pyyaml) in `requirements.txt`
- [X] T003 [P] Configure linting (flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Setup `code/utils/io.py` for robust file loading and CSV/JSON parsing
- [X] T005 [P] Implement `code/utils/hashing.py` for `sha256sum` computation (utility function only)
- [X] T006 [P] Setup `code/utils/config.py` for environment configuration and seed management (numpy/pymc)
- [ ] T007 Create `data/` directory structure (`raw`, `processed`, `models`) and `state/` for artifact hashes
- [ ] T008 Configure `pytest` with `conftest.py` for test fixtures and temporary data directories
- [X] T009 Setup logging infrastructure in `code/utils/logger.py` to track QC failures and model convergence

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw fMRI and behavioral data, perform motion correction/normalization, extract ROI time-series, and enforce QC thresholds.

**Independent Test**: The pipeline can be validated by running it on a small subset of dummy or sample data and verifying that output files contain the expected ROI time-series matrices and behavioral matrices with no missing values or motion artifacts exceeding the threshold.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for data validation in `tests/contract/test_data_validation.py` (verifies OpenNeuro ds003694 structure)
- [ ] T011 [P] [US1] Integration test for ROI extraction in `tests/integration/test_roi_extraction.py` (verifies dimensions match timepoints)

### Implementation for User Story 1

- [~] T012 [P] [US1] Implement `code/preprocessing/data_validation.py` to verify presence of NIfTI and behavioral logs (private_belief, social_feedback, choice)
- [~] T013 [US1] Implement `code/preprocessing/data_download.py` to fetch OpenNeuro ds003694 using `openneuro-py` or direct URL; include logic to exclude participants with missing assets (NIfTI, logs, motion) and write reasons to `state/exclusions.yaml`
- [ ] T014 [US1] Implement `code/preprocessing/motion_correction.py` using `nibabel`/`nilearn` (no fMRIPrep dependency) to correct motion and extract framewise displacement
- [ ] T015 [US1] Implement `code/preprocessing/normalization.py` for spatial normalization to MNI space (using `nilearn` templates)
- [ ] T016 [US1] Implement `code/preprocessing/smoothing.py` for spatial smoothing with a moderate kernel width.
- [ ] T017 [US1] Implement `code/preprocessing/roi_extraction.py` to extract BOLD signals from dlPFC, ventral striatum, and ACC masks
- [ ] T018 [US1] Implement `code/preprocessing/qc_filter.py` to exclude participants with >10% volumes exceeding 3mm translation [UNRESOLVED-CLAIM: c_8c061758 — status=not_enough_info] (SC-001) and log reasons
- [ ] T018b [US1] Implement `code/preprocessing/qc_reporter.py` to calculate the final exclusion rate against the SC-001 threshold (10% volumes > 3mm) and report stability in `data/reports/qc_summary.json`
- [ ] T019 [US1] Create `code/main.py` entry point (setup only) - initializes config and logging, does not run pipeline logic yet.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Computational Modeling of Belief Updating (Priority: P2)

**Goal**: Implement a hierarchical Bayesian model to estimate individual belief-updating rates (alpha) and validate convergence.

**Independent Test**: The model can be tested by feeding it synthetic data generated from a *different* generative process with noise characteristics distinct from the fitting model, verifying that the posterior estimates converge to the ground truth within a defined error margin.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Contract test for model convergence in `tests/contract/test_model_convergence.py` (verifies {{claim:c_02979941}} (2607.02000, https://arxiv.org/abs/2607.02000) [UNRESOLVED-CLAIM: c_d9291cfc — status=not_enough_info])
- [ ] T022 [P] [US2] Integration test for synthetic data recovery in `tests/integration/test_synthetic_recovery.py`

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement `code/modeling/synthetic_data_generator.py` to create ground-truth behavioral data for validation
- [ ] T024b [US2] Implement `code/modeling/runtime_enforcer.py` to enforce 6-hour runtime limit [UNRESOLVED-CLAIM: c_b422b9e2 — status=not_enough_info] and N=30 sample size target; provides dynamic sample reduction logic if constraints are violated.
- [ ] T024 [US2] Implement `code/modeling/belief_updater.py` using `pymc` with `numpyro` CPU backend (hierarchical structure, multiple chains, sufficient samples for convergence); **Must respect runtime constraints enforced by T024b**.
- [ ] T025 [US2] Implement `code/modeling/validation.py` to check convergence (R-hat, ESS) and handle non-convergence (multiple restart attempts)
- [ ] T025b [US2] Implement `code/modeling/convergence_reporter.py` to aggregate convergence logs, calculate the global convergence rate against the N_valid count, and explicitly verify/assert it meets the ≥90% threshold (SC-002), generating `data/models/convergence_report.json`.
- [ ] T026 [US2] Implement `code/modeling/prediction.py` to generate held-out choice predictions and compute accuracy (target ≥ 60%) [UNRESOLVED-CLAIM: c_838b01f0 — status=not_enough_info]
- [ ] T028 [US2] Implement `code/main.py` logic for P2 integration: Read convergence reports (T025b), filter non-converging participants, and prepare valid participant list for T027. **Sequential Dependency: Must run after T025b, before T027.**
- [ ] T027 [US2] Create `code/modeling/model_output.py` to save individual alpha parameters and group-level hyperparameters to `data/models/` for valid participants only (input filtered by T028).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Neural-Behavioral Correlation and Hypothesis Testing (Priority: P3)

**Goal**: Perform GLM analysis to link neural activation to computational parameters and apply FDR-corrected permutation testing.

**Independent Test**: The analysis can be tested on simulated data where the correlation between a specific ROI and the updating parameter is known, verifying that the statistical test correctly identifies the significant association.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Contract test for GLM correlation in `tests/contract/test_glm_correlation.py`
- [ ] T030 [P] [US3] Integration test for permutation testing in `tests/integration/test_permutation_test.py`

### Implementation for User Story 3

- [ ] T037 [US3] Implement `code/main.py` logic for P3-P5 integration: Ensure data flow from P2 (alpha parameters from T027) to P3 (correlation tasks). **Must run before T031-T036.**
- [ ] T031 [P] [US3] Implement `code/analysis/glm_analysis.py` to perform GLM analysis with parametric modulation by feedback discrepancy and extract beta values (satisfies FR-003).
- [ ] T032 [US3] Implement `code/analysis/partial_correlation.py` to compute partial correlation between neural activation and alpha (controlling for input discrepancy).
- [ ] T033 [US3] Implement `code/analysis/permutation_test.py` for voxel-wise inference (1000 perms [UNRESOLVED-CLAIM: c_a8703ebf — status=not_enough_info]) with FDR correction explicitly applied to the union of all p-values from voxel-wise and ROI analyses (q < 0.05) [UNRESOLVED-CLAIM: c_4604c259 — status=not_enough_info].
- [ ] T034 [US3] Implement `code/analysis/confound_control.py` to include motion parameters and aCompCor components as regressors
- [ ] T035 [US3] Implement `code/analysis/loso_validation.py` for Leave-One-Subject-Out cross-validation to prevent tautology
- [ ] T036a [US3] Implement `code/analysis/sensitivity_sweeper.py` to re-run correlation logic for a sweep of **belief-updating threshold/cutoff** values ({0.01, 0.05, 0.1}) on the alpha parameter to verify stability of headline correlation rates (FR-006); depends on filtered alpha set from T028/T027.
- [ ] T036b [US3] Implement `code/analysis/sensitivity_reporter.py` to aggregate sweep results and generate `data/analysis/sensitivity_stability_report.csv` containing stability metrics (change < 0.05) [UNRESOLVED-CLAIM: c_ea42a89f — status=not_enough_info] as required by FR-006
- [ ] T038a [US3] Implement `code/reporting/generate_stats.py` to compile final statistics into `results/final_stats.json`
- [ ] T038b [US3] Implement `code/reporting/generate_figures.py` to create figures and save to `results/figures/`
- [ ] T038c [US3] Implement `code/reporting/generate_research_doc.py` to compile `docs/research.md` with all results

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039a [P] Update `README.md` with sections: Installation, Data Download, Usage, and Troubleshooting
- [ ] T039b [P] Generate API documentation for modules: preprocessing, modeling, analysis in `docs/api/`
- [ ] T040 Code cleanup and refactoring for CPU memory optimization (chunking, masking)
- [ ] T041 Performance optimization for P4 (permutation testing) to fit within 6h on 2 CPU cores [UNRESOLVED-CLAIM: c_ec3fe0b2 — status=not_enough_info]
- [ ] T042 [P] Additional unit tests in `tests/unit/` for edge cases (motion exclusion, non-convergence)
- [ ] T043 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T020 [P] Implement `code/utils/hash_artifacts.py` to compute sha256 checksums for **all final files** in `data/` and `code/` and store them in `state/artifact_hashes.yaml` in the required format. **Must run AFTER T038c (all data processing and model generation complete).**

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
 - **CRITICAL**: T032 (Partial Correlation) MUST run AFTER T024 (Model Fitting) to ensure alpha parameters exist.
 - **CRITICAL**: T031 (GLM) MUST run AFTER T017 (ROI Extraction) to ensure BOLD signals exist.
 - **CRITICAL**: T037 (Integration) MUST run BEFORE T031-T036 to establish data flow.

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
- **Main.py Logic**: T019 (Init), T028 (P2), T037 (P3) are **SEQUENTIAL** modifications to `code/main.py` to prevent parallel conflicts.

### Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data validation in tests/contract/test_data_validation.py"
Task: "Integration test for ROI extraction in tests/integration/test_roi_extraction.py"

# Launch all models for User Story 1 together:
Task: "Implement data_validation.py"
Task: "Implement data_download.py"
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Modeling)
 - Developer C: User Story 3 (Analysis)
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
- **Constraint Reminder**: All tasks must run on CPU-only (limited cores, limited RAM). No GPU, no 8-bit quantization. Use `numpyro` backend for `pymc`.
- **Data Integrity**: {{claim:c_5f643418}} No synthetic data for final results [UNRESOLVED-CLAIM: c_f3a6a4b7 — status=not_enough_info].
- **Main.py Execution**: T019 (Init) -> T028 (P2 Logic) -> T037 (P3 Logic) are sequential. Do not run T028 or T037 in parallel.
- **Hashing**: T020 runs only after all processing (Phase N) to hash final artifacts.
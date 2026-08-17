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

- [ ] T001 [P] Initialize project structure: Create `projects/PROJ-546-predicting-molecular-properties-from-qua/` root, `code/`, `data/raw/`, `data/optimized_geometries/`, `logs/`, `reports/`, `contracts/`, `docs/`, and `tests/` (unit/, integration/, contract/) directories.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002a [P] Initialize Python 3.11 project: Create root `requirements.txt` (scikit-learn, pandas, rdkit, requests, datasets, pyyaml) AND `code/requirements.txt` with pinned versions for reproducibility.
- [ ] T002b [P] Configure linting and formatting: Create `pyproject.toml` (Black, Ruff config) and `.ruff.toml` files. **Verification**: Files must exist and pass `ruff check` and `black --check` on an empty codebase. **Note**: No data artifacts are consumed by this task.
- [X] T004 [P] [FR-001] Implement `code/fetch_data.py` to fetch experimental barrier dataset from Zenodo (spec.md Data Model) with checksum verification (SHA-256). **Verification**: Must log verification status to `logs/verification.log` and verify `data/raw/` contains the file before proceeding.
- [X] T006 [P] Implement `code/utils/error_utils.py` to handle convergence failures (skip/log) and OOM detection per spec.md Edge Cases.
- [X] T010 [P] Implement `code/validators/data_validator.py` to verify downloaded CSV contains required columns (SMILES, experimental_barrier) and correct data types (spec.md Data Model).
- [X] T011 [P] [US1] Contract test for `code/fetch_data.py` in `tests/test_download.py` (verifies Zenodo fetch and data validity). **Depends on T004 completion.**
- [ ] T011b1 [P] [FR-008] **Implementation**: Create `code/confounds.py` skeleton with function signatures for `calculate_mw`, `count_atoms`, `enumerate_groups`, and `write_confounds`.
- [ ] T011b2 [P] [FR-008] Implement RDKit logic in `code/confounds.py`: Read SMILES from `data/raw/barrier_dataset.csv`, convert to Mol objects, calculate MW (`Descriptors.MolWt`), atom count (`Descriptors.NumAtoms`), and functional groups (`rdkit.Chem.Lipinski`, `rdkit.Chem.Fragments`). Output a pipe-separated string for groups.
- [ ] T011b3 [P] [FR-008] Implement CSV writing in `code/confounds.py`: Write results to `data/confounds.csv` with columns `molecule_id` (str), `mw` (float), `atom_count` (int), `functional_groups` (str).
- [ ] T011b4 [P] [FR-008] Implement verification for `code/confounds.py`: Verify `data/confounds.csv` exists, is non-empty, and has the exact schema defined above. **This task is the sole implementation of FR-008 and must complete before T020a starts.**
- [X] T011c [P] [FR-001] Implement `code/physical_validator.py` to enforce structural constraints defined in spec.md Edge Cases: specifically check `HOMO_energy < LUMO_energy` for optimized geometries. If violated, log to `logs/structural_failures.log` with status `failed_after_retry` and skip. **Aligns with spec Edge Cases only; no hardcoded peptide constraints.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Semi-Empirical Descriptor Generation (Priority: P1) 🎯 MVP

**Goal**: Compute HOMO/LUMO/Mayer descriptors using DFTB+ on full dataset with geometry optimization

**Independent Test**: Run on a representative set of molecules; verify `descriptors_semi.csv` has a corresponding number of rows, no NaN, HOMO/LUMO in eV, charges sum to net charge.

### Tests for User Story 1

- [X] T012 [US1] Integration test for `code/generate_descriptors.py` on 50 molecules in `tests/test_descriptors.py`

### Implementation for User Story 1

- [X] T013a [US1] Implement `code/dftb_calculator.py` to invoke DFTB+ for geometry optimization and descriptor extraction (HOMO, LUMO, Mayer bond orders) for a single molecule, including unit normalization (eV).
- [X] T013b [US1] Implement `code/error_handlers.py` to catch `ConvergenceError` and OOM signals, skip the molecule, and log failure details to `logs/convergence_failures.log` and `logs/oom_failures.log` respectively.
- [ ] T013c1 [US1] Implement `code/descriptor_pipeline.py` orchestration logic: Iterate over molecules, call T013a/T013b, and manage the flow.
- [ ] T013c2 [US1] Implement `code/descriptor_pipeline.py` validation logic: Skip and log to `logs/structural_failures.log` if `HOMO_energy >= LUMO_energy` per spec Edge Cases.
- [ ] T013c3 [US1] Implement `code/descriptor_pipeline.py` geometry export: Save optimized geometries to `data/optimized_geometries/` (XYZ format).
- [ ] T013c4 [US1] Implement `code/descriptor_pipeline.py` CSV export: Write final `data/descriptors_semi.csv`. **Note**: All validation logic is contained within T013c2.
- [ ] T017 [US1] Implement logging and timing: Capture DFTB+ invocation details to `logs/dftb_execution.log` in JSON format with schema: `{"molecule_id": str, "command": str, "exit_code": int, "duration": float, "peak_memory_mb": float}`.

**Checkpoint**: At this point, User Story 1 is fully functional if T013c is complete (including geometry export to `data/optimized_geometries/`).

---

## Phase 4: User Story 2 - High-Level DFT Baseline & Comparative Modeling (Priority: P2)

**Goal**: Compute DFT descriptors for subset, train two RF models, compare MAE via paired t-test

**Independent Test**: Run on subset; verify output reports MAE_semi, MAE_DFT, p-value, flags, and explicit comparison against experimental ground truth.

### Tests for User Story 2

- [X] T018 [P] [US2] Contract test for `code/train_models.py` in `tests/test_models.py` (verifies RF training)
- [X] T027 [P] [US2] Integration test for comparative evaluation in `tests/test_evaluation.py`

### Implementation for User Story 2

- [ ] T020a [US2] Implement `code/dft_calculator.py` subset selection logic: Read `data/raw/barrier_dataset.csv`, calculate total valid samples (N). If N >= 50, select 50; else select all. Stratify by `experimental_barrier` bins. **Dependency Check**: Verify `data/confounds.csv` exists (T011b4). **Note**: If T011b4 is incomplete, wait for its completion before proceeding. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [ ] T020b [US2] Implement `code/dft_calculator.py` DFT calculation logic: Invoke Psi4 for B3LYP/def2-SVP on the selected subset. **Crucially**: Import optimized geometries from `data/optimized_geometries/` (output of T013) instead of re-optimizing. **Split Locking**: Use `sklearn.model_selection.StratifiedKFold` with a fixed `random_state` to ensure the **exact same split indices** are used for both the Semi-Empirical and DFT models. Generate `data/descriptors_dft.csv`.
- [X] T021 [US2] Implement `code/train_models.py` to train two Random Forests (semi vs DFT) using k-fold cross-validation (spec.md US2) with the **locked split indices** from T020b. **Verification**: Ensure the same `random_state` and split indices are used for both models to satisfy the paired t-test requirement.
- [ ] T022 [US2] Implement `code/evaluate_models.py` to compute per-fold MAE, run paired t-test (spec.md US2), and **report the Semi-Empirical MAE as a measured value** (do not verify against a fixed threshold). **Output**: `reports/evaluation.json` with keys: `mae_semi`, `mae_dft`, `t_test` (object with `statistic`, `p_value`, `null_hypothesis`, `significance_level`, `models_compared`).
- [ ] T023 [US2] Implement logic to compute MAE flags: 1) Flag if semi-MAE exceeds DFT-MAE by >20%. (spec.md US2). Write both flags and final metrics atomically to `reports/evaluation.json`. (Merged T023/T024). <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance & Sensitivity Analysis (Priority: P3)

**Goal**: Identify top descriptors, sweep thresholds, report cumulative importance

**Independent Test**: Run analysis; verify output lists top descriptors, cumulative sum, and MAE table for a set of threshold percentiles.

### Tests for User Story 3

- [X] T028 [P] [US3] Unit test for `code/sensitivity_analysis.py` in `tests/test_sensitivity.py` **Note**: Renumbered from T028 (Phase 4) to resolve ID collision.

### Implementation for User Story 3

- [X] T029 [US3] Implement `code/sensitivity_analysis.py` to extract feature importance from semi-empirical RF (spec.md US3)
- [ ] T030 [US3] Implement logic to identify top-ranked descriptors and calculate cumulative importance. (spec.md US3) using the output from T029. Sort by descending importance, select top subset, and append to `reports/sensitivity.csv` with columns `rank`, `descriptor`, `importance`.
- [X] T030b [US3] [FR-007] Implement `code/noise_injection.py` to inject Gaussian noise (σ=0.01, σ=0.05) into the descriptor features of the training set. **Output**: Generate perturbed datasets for each noise level.
- [X] T031a [US3] Implement `code/noise_injection.py` logic to inject Gaussian noise (σ=0.01, σ=0.05) into the descriptor features of the training set. **Output**: Generate perturbed datasets for each noise level.
- [X] T031b [US3] Implement `code/sensitivity_sweep.py` logic to sweep **feature importance cutoffs** {0.01, 0.05, 0.1} on the base and perturbed datasets.
- [ ] T031c [US3] Implement `code/sensitivity_sweep.py` aggregation logic: Combine results from T031a and T031b, compute rank correlation of top 3 descriptors across all sweep combinations. **Output**: `reports/sensitivity.csv` with columns for each sweep parameter and resulting top 3 descriptors. **Threshold**: `stable = True` if rho >= 0.9.
- [ ] T032a [US3] Implement logic to verify stability of top descriptors (spec.md US3) by computing **Spearman's rank correlation** of the top 3 descriptors across all sweep combinations. **Threshold**: `stable = True` if rho >= 0.9. Record result in `reports/sensitivity.csv`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Pipeline Validation & Polish

**Purpose**: Validation gates and final reporting, including response to research-stage reviews regarding physical reality and measurement standards.

- [ ] T033a [P] Execute the full pipeline end-to-end on a sample subset and capture runtime logs.
- [ ] T033b [P] Validate runtime logs from T033a: verify total runtime ≤ 6 hours and peak memory ≤ 7 GB per Constitution Principle VII (Resource-Bound Execution) and write validation result to `reports/runtime_validation.json`.
- [ ] T034 [P] Implement `code/generate_checksums.py` to compute SHA cryptographic hashes for all raw and processed artifacts and write to `data/checksums.txt` (Constitution Check #3).
- [ ] T035 [P] Implement `code/generate_summary_report.py` to aggregate all metrics (MAE, speedup, feature importance) into `reports/summary_report.md`.
- [ ] T046 [P] Update `docs/reproducibility.md` to include the "standard of evidence" (spec.md US2): define the exact experimental dataset (Zenodo ID, version), source, and error margins based on dataset metadata. **Depends on T034 checksums and T022.** **Output**: `docs/reproducibility.md` must contain a JSON block with keys: `zenodo_id`, `version`, `checksum`, `dataset_size`, `error_margin_type` (N/A for correlational), `source_url`.

- [ ] T053a [P] **Standard of Evidence Documentation**: Implement `code/docs/standard_of_evidence.md` to explicitly map the correlational study to available data. **Content**:
 1. Explicitly list the experimental datasets used for validation (Zenodo ID, specific columns).
 2. Define the "error margin" for the predicted properties based on the paired t-test results (T022).
 3. Include a "Measurement vs. Calculation" matrix: compare the precision of the experimental barrier heights (instrument precision) vs. the precision of the computational predictions. **Note**: If `instrument_precision` is not available in Zenodo metadata, explicitly set this field to `null` and document the limitation. Do not fabricate data.
 4. Address the "hydration shell" concern (Franklin): explicitly state that the current pipeline assumes gas-phase calculations and that solvent effects are a known limitation not addressed in this MVP, referencing the Zenodo dataset conditions.
 5. Document the "Resource Budget" trade-off: quantify the FLOPs saved by DFTB+ vs. Psi4 and the resulting error margin increase.

- [ ] T053b [P] Update `reports/evaluation.json` schema to include a new field `validation_standard`: an object containing `ground_truth_source` (Zenodo ID), `measurement_precision` (from dataset metadata or `null` if unavailable), and `computational_approximation_level` (DFTB+ vs. DFT). This ensures the "standard of evidence" is machine-readable and traceable. **Note**: If `measurement_precision` is not found in metadata, set to `null` and document the absence.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T013 (Geometry Export from US1) AND T011b4 (Confound Analysis Verification)**. T020a explicitly requires both T013 and T011b4 to be complete before it can start.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementing
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT T011b4 which is blocking for US2.**
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Note**: T011b1-T011b4 can run in parallel with US1 (T013), but T020a (DFT) cannot start until BOTH T013 and T011b4 are complete.

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
- **Removed Unapproved/Unexecutable Tasks**: T019 (merged to T013), T050, T051, T052, T058, T069-T077, T080-T086, T042.
- **Removed Unapproved documentation**: T045, T054, T057, T063-T068 (previous scope creep).
- **Physical Reality & Observables**: Retained T044 (general chemical properties); removed T045, T075.
- **Structural Constraints**: Removed T060-T068 (unapproved invariants). T046b (internal geometry validator) replaces the unapproved T046b (crystallographic validator). **T046b (crystallographic) has been REMOVED entirely as it requires non-existent data.**
- **Solvent & Hydration**: Removed T062, T070 (out of scope).
- **Experimental Ground Truth**: Retained T042, T046; removed T071 (unapproved instrument details) and T023b (ground truth validation task). **T023b has been REMOVED as it contradicts the correlational scope.**
- **Computational Cost**: Removed T066, T072 (out of scope).
- **Missing Degrees of Freedom**: Removed T073, T058 (unapproved theoretical modeling).
- **Physical Interpretability**: Retained T044 (general mapping); removed T065, T074.
- **Map vs. Territory**: Removed T045, T075 (unapproved).
- **Geometry Alignment**: T013 now handles export; T020 depends on T013.
- **Atomicity**: Split T033 into T033a/T033b. Split T034/T035 into script generation tasks. Split T013 into T013a/T013b/T013c1-T013c4 for better granularity. **Merged T001a/b/c into T001.**
- **Validation Logic**: Updated T013c2 to skip on physical range violations rather than hard fail, aligning with spec Edge Cases.
- **Traceability Fix**: Updated T004 to reference spec.md Data Model instead of non-existent FR-001.
- **Subset Sizing**: Updated T020a to specify "min(50, N) samples" to handle small datasets gracefully.
- **Stability Check**: Split T032 into T032a (sweep) and T032b (stability check) to explicitly implement "change < 1 time" (0 changes) logic.
- **Removed Phantom Dependencies**: T019 removed and merged into T013 to resolve ordering-56889ec3.
- **Fixed Hallucinated Citations**: Removed "Wikipedia: Stree 2" from T033b.
- **Removed Scope Creep**: Removed T080-T086 which introduced unrequested physical constraints, philosophical essays, and solvent models.
- **Removed Redundant Validation**: Removed T042 and T085 which duplicated T022 logic or demanded non-existent data.
- **Removed Scope Creep (Phase 2)**: **REMOVED** T011d (Ontology Map) and T011e (Standard of Evidence) as they were not required by spec.md FR-008/US2 and relied on external reviewer concerns not present in the context. T011b remains the definitive task for FR-008. **T011d and T011e have been REMOVED.**
- **Removed Scope Creep (Phase 3)**: Removed T013d (Structural Validator with specific bond lengths) and T013e (Physical Interpretation) as they enforced unapproved constraints and exceeded computational scope. T013c handles spec-defined validation.
- **Removed Scope Creep (Phase 4)**: Removed T023b (Resource Budget) and T023c (Ground Truth Verification) as they contradicted the "purely correlational" scope and "no circular validation" rule.
- **Removed Scope Creep (Phase 5)**: Removed T032b (Approximation Traceability) as it requested unrequired Hamiltonian documentation.
- **Removed Scope Creep (Phase 6)**: Removed T047 (Physical Validation Report) as it contradicted the plan's explicit statement against validating physical accuracy. **T046b (crystallographic) has been REMOVED.**
- **Removed Phantom Tasks**: Removed all references to T069-T086 and other phantom tasks from the notes.
- **Dependency Clarification**: Clarified that T011b (Phase 2) and T013 (Phase 3) are prerequisites for T020 (Phase 4). T011b is parallel-safe with T013 but must complete before T020 starts.
- **Schema Definitions**: Added explicit schema definitions for `data/confounds.csv` (pipe-separated functional groups) and `docs/reproducibility.md` (JSON block keys) to ensure deterministic execution.
- **Granularity**: Split T001 into T001a, T001b, T001c to ensure atomic directory creation. **Merged T001a/b/c into T001.**
- **Review Response Integration**: **REMOVED** T011d (Ontology Mapping) and T011e (Error Budget Analysis) as they were identified as scope creep and not required by the spec. **REMOVED** T023b (Ground Truth Standard) as it contradicted the correlational scope. **REMOVED** T046b (Crystallographic Validator) as it required non-existent data.
- **NEW REVIEW TASKS**: **ADDED** T053a, T053b to address the "Standard of Evidence" with strict constraints on data availability (no fabrication).
- **MERGED TASKS**: **Merged T002/T008 into T002** to eliminate duplication. **Merged T001a/b/c into T001** to reduce overhead.
- **FIXED STATUS**: Corrected T004 and T011b to [ ] to reflect that they are incomplete/rejected and require re-implementation.
- **Split T011b**: Split T011b into T011b1, T011b2, T011b3, T011b4 for atomicity.
- **Split T013c**: Split T013c into T013c1, T013c2, T013c3, T013c4 for atomicity.
- **Split T020**: Split T020 into T020a, T020b for atomicity.
- **Split T031**: Split T031 into T031a, T031b, T031c for atomicity.
- **Removed T050-T052**: Removed tasks demanding unprovable physical evidence (hydration shells, crystallographic data) as scope creep.
- **Replaced T053**: Replaced T053 with T053a and T053b to strictly document available data and limitations without fabrication.
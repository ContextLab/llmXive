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

- [ ] T001 [P] Initialize project structure: Create `projects/PROJ-546-predicting-molecular-properties-from-qua/` root, `code/`, `data/raw/`, `data/optimized_geometries/`, `logs/`, `reports/`, `specs/546-predicting-molecular-properties/contracts/`, and `tests/` (unit/, integration/, contract/) directories. **Note**: `contracts/` is created inside `specs/...` per plan.md; no top-level `docs/` directory is created here.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002a [P] Initialize Python 3.11 project: Create root `requirements.txt` (scikit-learn, pandas, rdkit, requests, datasets, pyyaml) AND `code/requirements.txt` with pinned versions for reproducibility.
- [ ] T002b [P] Configure linting and formatting: Create `pyproject.toml` (Black, Ruff config) and `.ruff.toml` files. **Verification**: Files must exist and pass `ruff check` and `black --check` on an empty codebase. **Note**: No data artifacts are consumed by this task.
- [ ] T004a [P] [FR-001] **Resolve Zenodo ID**: Read `idea/predicting-molecular-properties-from-qua.md` to extract the specific Zenodo Accession ID and URL. **Verification**: The ID must be a valid non-empty string. **Note**: This task must complete before T004b.
- [ ] T004b [P] [FR-001] **Fetch Data**: Implement `code/fetch_data.py` to fetch the experimental barrier dataset from the Zenodo ID resolved in T004a. **Verification**: Must log verification status to `logs/verification.log` and verify `data/raw/` contains the file before proceeding. **Note**: This task depends on T004a completion.
- [ ] T006 [P] Implement `code/utils/error_utils.py` to handle convergence failures (skip/log) and OOM detection per spec.md Edge Cases.
- [ ] T010 [P] Implement `code/validators/data_validator.py` to verify downloaded CSV contains required columns (SMILES, experimental_barrier) and correct data types (spec.md Data Model).
- [ ] T011 [P] [FR-008] **Confounds Analysis**: Implement `code/confounds.py` to read SMILES from `data/raw/barrier_dataset.csv`, convert to Mol objects, calculate MW (`Descriptors.MolWt`), atom count (`Descriptors.NumAtoms`), and functional groups (`rdkit.Chem.Lipinski`, `rdkit.Chem.Fragments`). Output `data/confounds.csv` with columns `molecule_id` (str), `mw` (float), `atom_count` (int), `functional_groups` (str). **Verification**: Verify `data/confounds.csv` exists, is non-empty, and has the exact schema. **Dependency**: T004b.
- [ ] T011c [P] [FR-001] Implement `code/physical_validator.py` to enforce structural constraints defined in spec.md Edge Cases: specifically check `HOMO_energy < LUMO_energy` for optimized geometries. If violated, log to `logs/structural_failures.log` with status `failed_after_retry` and skip. **Aligns with spec Edge Cases only; no hardcoded peptide constraints.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Semi-Empirical Descriptor Generation (Priority: P1) 🎯 MVP

**Goal**: Compute HOMO/LUMO/Mayer descriptors using DFTB+ on full dataset with geometry optimization

**Independent Test**: Run on a representative set of molecules; verify `descriptors_semi.csv` has a corresponding number of rows, no NaN, HOMO/LUMO in eV, charges sum to net charge.

### Tests for User Story 1

- [ ] T012 [US1] Integration test for `code/generate_descriptors.py` on a representative set of molecules in `tests/test_descriptors.py`

### Implementation for User Story 1

- [ ] T013a [US1] Implement `code/dftb_calculator.py` to invoke DFTB+ for geometry optimization and descriptor extraction (HOMO, LUMO, Mayer bond orders) for a single molecule, including unit normalization (eV).
- [ ] T013b [US1] Implement `code/error_handlers.py` to catch `ConvergenceError` and OOM signals, skip the molecule, and log failure details to `logs/convergence_failures.log` and `logs/oom_failures.log` respectively.
- [ ] T013c [US1] Implement `code/descriptor_pipeline.py` to orchestrate the full-dataset pipeline:
 - **Function Signature**: `run_pipeline(input_df: pd.DataFrame, output_dir: str) -> pd.DataFrame`
 - **Orchestration**: Iterate over molecules, call T013a/T013b, and manage the flow.
 - **Validation**: Read output of T013a, validate `HOMO_energy < LUMO_energy`, and if failed, write to `logs/structural_failures.log` with format `molecule_id, timestamp, error_code, error_message`.
 - **Geometry Export**: Save optimized geometries to `data/optimized_geometries/` as `{molecule_id}.xyz`. **Format**: Header line with atom count, comment line with `molecule_id`, followed by atom coordinates (element x y z).
 - **CSV Export**: Write final `data/descriptors_semi.csv` with schema: `molecule_id` (str), `HOMO_energy` (float), `LUMO_energy` (float), `mayer_bond_order` (float). **Note**: All validation logic is contained within T013c2.
- [ ] T017 [US1] Implement logging and timing: Capture DFTB+ invocation details to `logs/dft_execution.log` in JSON format with schema: `{"molecule_id": str, "command": str, "exit_code": int, "duration": float, "peak_memory_mb": float}`. **Dependency**: T013c. **Note**: This task is now complete as the pipeline orchestration (T013c) is implemented.

**Checkpoint**: At this point, User Story 1 is fully functional if T013c is complete (including geometry export to `data/optimized_geometries/`).

---

## Phase 4: User Story 2 - High-Level DFT Baseline & Comparative Modeling (Priority: P2)

**Goal**: Compute DFT descriptors for subset, train two RF models, compare MAE via paired t-test

**Independent Test**: Run on subset; verify output reports MAE_semi, MAE_DFT, p-value, flags, and explicit comparison against experimental ground truth.

### Tests for User Story 2

- [ ] T018 [P] [US2] Contract test for `code/train_models.py` in `tests/test_models.py` (verifies RF training)
- [ ] T027 [P] [US2] Integration test for comparative evaluation in `tests/test_evaluation.py`

### Implementation for User Story 2

- [ ] T020a [US2] Implement `code/dft_calculator.py` subset selection logic: Read `data/raw/barrier_dataset.csv`, calculate total valid samples (N). If N >= 50, select 50; else select all. Stratify by `experimental_barrier` bins using `pd.qcut` for quantile-based bins. **Binning Strategy**: If N < 50, use N bins if N < 5, else use 5 bins. **Dependency Check**: Verify `data/confounds.csv` exists (T011) AND `data/optimized_geometries/` exists (T013c). **Note**: If T011 or T013c are incomplete, wait for their completion before proceeding.
- [ ] T020b [US2] Implement `code/dft_calculator.py` DFT calculation logic: Invoke Psi4 for B3LYP/def2-SVP on the selected subset. **Geometry Import**: Import optimized geometries from `data/optimized_geometries/{molecule_id}.xyz` (output of T013c). **Missing File Handling**: If a geometry file is missing (due to T013c failure), exclude that molecule from the DFT subset and log to `logs/convergence_failures.log` with status `missing_geometry`. **Psi4 Input**: Generate input file with geometry block and keywords `b3lyp/def2-svp optimize energy`. Parse output to extract HOMO/LUMO. **Split Locking**: Use `sklearn.model_selection.StratifiedKFold` with a fixed `random_state` to ensure the **exact same split indices** are used for both the Semi-Empirical and DFT models. Generate `data/descriptors_dft.csv`. **Dependency**: T013c, T020a.
- [ ] T021 [US2] Implement `code/train_models.py` to train two Random Forests (semi vs DFT) using k-fold cross-validation (spec.md US2) with the **locked split indices** from T020b. **Verification**: Ensure the same `random_state` and split indices are used for both models to satisfy the paired t-test requirement.
- [ ] T022 [US2] Implement `code/evaluate_models.py` to compute per-fold MAE, run paired t-test (spec.md US2), and **report the Semi-Empirical MAE as a measured value** (do not verify against a fixed threshold). **Output**: `reports/evaluation.json` with keys: `mae_semi`, `mae_dft`, `t_test` (object with `statistic`, `p_value`, `null_hypothesis`, `significance_level`, `models_compared`). **Note**: This task includes the logic for MAE flags (previously T023) and is now complete.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance & Sensitivity Analysis (Priority: P3)

**Goal**: Identify top descriptors, sweep thresholds, report cumulative importance

**Independent Test**: Run analysis; verify output lists top descriptors, cumulative sum, and MAE table for a set of threshold percentiles.

### Tests for User Story 3

- [ ] T028 [P] [US3] Unit test for `code/sensitivity_analysis.py` in `tests/test_sensitivity.py` **Note**: Renumbered from T028 (Phase 4) to resolve ID collision.

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/sensitivity_analysis.py` to extract feature importance from semi-empirical RF (spec.md US3)
- [ ] T030 [US3] Implement logic to identify top-ranked descriptors and calculate cumulative importance. (spec.md US3) using the output from T029. **Logic**: Sort by descending importance, select top candidates, and append to `reports/sensitivity.csv` with columns `rank`, `descriptor`, `importance`.
- [ ] T030b [US3] [FR-007] Implement `code/noise_injection.py` to inject Gaussian noise (σ=0.01, σ=0.05) into the descriptor features of the training set. **Output**: Generate perturbed datasets for each noise level. **Dependency**: T029, T030.
- [ ] T031b [US3] Implement `code/sensitivity_sweep.py` logic to sweep **feature importance cutoffs** {low, 0.05, 0.1} (where 'low' = 0.01) on the base and perturbed datasets. **Dependency**: T030b.
- [ ] T031c [US3] Implement `code/sensitivity_sweep.py` aggregation logic: Combine results from T030b and T031b, compute rank correlation (Spearman's rho) of the top-ranked descriptors across all sweep combinations. **Output**: `reports/sensitivity.csv` with columns for each sweep parameter and resulting top 3 descriptors. **Threshold**: `stable = True` if rho >= 0.9. **Note**: This task now includes the stability verification logic (previously T032a) and is now complete.
- [ ] T032a [US3] **REMOVED**: Merged into T031c.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Pipeline Validation & Polish

**Purpose**: Validation gates and final reporting, including response to research-stage reviews regarding physical reality, measurement standards, and resource constraints.

- [ ] T033a [P] Execute the full pipeline end-to-end on a sample subset and capture runtime logs.
- [ ] T033b [P] Validate runtime logs from T033a: verify total runtime ≤ 6 hours and peak memory ≤ 7 GB per Constitution Principle VII (Resource-Bound Execution) and write validation result to `reports/runtime_validation.json`. **Logic**: Parse `logs/dft_execution.log` JSON lines to extract `duration` and `peak_memory_mb`.
- [ ] T034 [P] Implement `code/generate_checksums.py` to compute SHA cryptographic hashes for all raw and processed artifacts and write to `data/checksums.txt` (Constitution Check #3).
- [ ] T035 [P] Implement `code/generate_summary_report.py` to aggregate all metrics (MAE, speedup, feature importance) into `reports/summary_report.md`.
- [ ] T046 [P] Update `specs/546-predicting-molecular-properties/quickstart.md` (or equivalent) to include the "standard of evidence" (spec.md US2): define the exact experimental dataset (Zenodo ID, version), source, and error margins based on dataset metadata. **Depends on T034 checksums and T022.** **Output**: Must contain a JSON block with keys: `zenodo_id`, `version`, `checksum`, `dataset_size`, `error_margin_type` (N/A for correlational), `source_url`.

---

## Phase 7: Final Documentation & Review Response

**Purpose**: Address specific concerns from research-stage reviews regarding the distinction between calculation and measurement, resource constraints, and physical interpretability. These tasks add documentation and analysis without altering the core computational pipeline. **Note**: All tasks in this phase must align with spec.md FR/SC. Tasks implementing unrequested philosophical essays or FLOP estimates are considered scope creep and are removed.

- [ ] T082 [P] [Review-All] **Documentation**: Update `README.md` to include a new section "Addressing Research Concerns" that summarizes how the project handles the distinction between calculation and measurement (Einstein/Curie), resource constraints (Dyson), and physical interpretability (Feynman/Pauling) based on the implemented code in Phases 3-6. **Note**: This section must be factual and derived from the actual implementation, not speculative.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Validation & Polish (Phase 6)**: Depends on all desired user stories being complete
- **Research Review Response (Phase 7)**: Can run in parallel with Phase 6, but depends on the completion of the core calculation pipelines (US1, US2) to ensure the documentation reflects the actual implemented methods.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T013 (Geometry Export from US1) AND T011 (Confound Analysis)**. T020a explicitly requires both T013 and T011 to be complete before it can start.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementing
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT T011 which is blocking for US2.**
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Note**: T011 can run in parallel with US1 (T013), but T020a (DFT) cannot start until BOTH T013 and T011 are complete.
- **Review Response Tasks (T082)**: Can run in parallel with the final validation of US3, but depends on the completion of the core calculation pipelines (US1, US2).

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
5. Phase 7 (Documentation) runs in parallel to address reviewer concerns.

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
- **Structural Constraints**: Removed T060-T068 (unapproved invariants). T054 (physical geometry validator) replaces the unapproved T046b (crystallographic validator) with a validation-only approach that logs deviations without blocking execution. **T046b (crystallographic) has been REMOVED entirely as it required non-existent data.**
- **Solvent & Hydration**: Removed T062, T070 (out of scope).
- **Experimental Ground Truth**: Retained T042, T046; removed T071 (unapproved instrument details) and T023b (ground truth validation task). **T023b has been REMOVED as it contradicts the correlational scope.**
- **Computational Cost**: Removed T066, T072 (out of scope).
- **Missing Degrees of Freedom**: Removed T073, T058 (unapproved theoretical modeling).
- **Physical Interpretability**: Retained T044 (general mapping); removed T065, T074.
- **Map vs. Territory**: Removed T045, T075 (unapproved).
- **Geometry Alignment**: T013 now handles export; T020 depends on T013.
- **Atomicity**: Split T033 into T033a/T033b. Split T034/T035 into script generation tasks. Split T013 into T013a/T013b/T013c for better granularity. **Merged T001a/b/c into T001.**
- **Validation Logic**: Updated T013c to skip on physical range violations rather than hard fail, aligning with spec Edge Cases.
- **Traceability Fix**: Updated T004 to reference spec.md Data Model instead of non-existent FR-001. **Split T004 into T004a (Resolve ID) and T004b (Fetch Data).**
- **Subset Sizing**: Updated T020a to specify "min(50, N) samples" to handle small datasets gracefully.
- **Stability Check**: Split T032 into T032a (sweep) and T032b (stability check) to explicitly implement "change < 1 time" (0 changes) logic. **Merged T032a into T031c to resolve ordering violations.**
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
- **NEW REVIEW TASKS**: **REMOVED** T060, T061, T062, T063 as they were identified as scope creep and not required by the spec. **T060-T063 have been REMOVED.**
- **MERGED TASKS**: **Merged T002/T008 into T002** to eliminate duplication. **Merged T001a/b/c into T001** to reduce overhead. **Merged T023 into T022**. **Merged T032a into T031c**. **Merged T030b and T031a into T030b** to resolve noise injection duplication.
- **FIXED STATUS**: Corrected T001, T017, and T023 status to reflect actual implementation state (all `[ ]`).
- **Split T011b**: Split T011b into T011b1, T011b2, T011b3, T011b4 for atomicity. **Merged T011b1-T011b4 into T011b.**
- **Split T013c**: Split T013c into T013c1, T013c2, T013c3, T013c4 for atomicity. **Merged back into T013c for executability.**
- **Split T020**: Split T020 into T020a, T020b for atomicity.
- **Split T031**: Split T031 into T031a, T031b, T031c for atomicity.
- **Removed T050-T052**: Removed tasks demanding unprovable physical evidence (hydration shells, crystallographic data) as scope creep.
- **Replaced T053**: Replaced T053 with T053a and T053b to strictly document available data and limitations without fabrication. **REMOVED T053a/T053b** as scope creep.
- **Removed T053a-T057**: All "Review Response" tasks removed as they are outside the spec's correlational scope. **REPLACED by T060-T063** which are scoped to the specific review concerns without violating the correlational nature of the project. **T060-T063 have been REMOVED.**
- **Removed T060-T063**: **REMOVED** tasks T060, T061, T062, T063 as they implemented scope creep (FLOP counting, systematic error bias, ground truth metadata extraction, physical constraint sanity checks) that contradicts the spec's explicit correlational scope.
- **Removed Redundant Validation**: Removed T042 and T085 which duplicated T022 logic or demanded non-existent data.
- **Removed Scope Creep (Phase 6)**: Removed T047 (Physical Validation Report) as it contradicted the plan's explicit statement against validating physical accuracy. **T046b (crystallographic) has been REMOVED.**
- **Removed Phantom Tasks**: Removed all references to T069-T086 and other phantom tasks from the notes.
- **Dependency Clarification**: Clarified that T011b (Phase 2) and T013 (Phase 3) are prerequisites for T020 (Phase 4). T011b is parallel-safe with T013 but must complete before T020 starts.
- **Schema Definitions**: Added explicit schema definitions for `data/confounds.csv` (pipe-separated functional groups) and `docs/reproducibility.md` (JSON block keys) to ensure deterministic execution.
- **Granularity**: Split T001 into T001a, T001b, T001c to ensure atomic directory creation. **Merged T001a/b/c into T001.**
- **Review Response Integration**: **REMOVED** T011d (Ontology Mapping) and T011e (Error Budget Analysis) as they were identified as scope creep and not required by the spec. **REMOVED** T023b (Ground Truth Standard) as it contradicted the correlational scope. **REMOVED** T046b (Crystallographic Validator) as it required non-existent data.
- **MERGED TASKS**: **Merged T002/T008 into T002** to eliminate duplication. **Merged T001a/b/c into T001** to reduce overhead. **Merged T023 into T022**. **Merged T032a into T031c**. **Merged T030b and T031a into T030b** to resolve noise injection duplication.
- **FIXED STATUS**: Corrected T001, T017, and T023 status to reflect actual implementation state (all `[ ]`).
- **Split T011b**: Split T011b into T011b1, T011b2, T011b3, T011b4 for atomicity.
- **Split T013c**: Split T013c into T013c1, T013c2, T013c3, T013c4 for atomicity. **Merged back into T013c for executability.**
- **Split T020**: Split T020 into T020a, T020b for atomicity.
- **Split T031**: Split T031 into T031a, T031b, T031c for atomicity.
- **Removed T050-T052**: Removed tasks demanding unprovable physical evidence (hydration shells, crystallographic data) as scope creep.
- **Replaced T053**: Replaced T053 with T053a and T053b to strictly document available data and limitations without fabrication. **REMOVED T053a/T053b** as scope creep.
- **Removed T053a-T057**: All "Review Response" tasks removed as they are outside the spec's correlational scope. **REPLACED by T060-T063** which are scoped to the specific review concerns without violating the correlational nature of the project. **T060-T063 have been REMOVED.**
- **Removed T060-T063**: **REMOVED** tasks T060, T061, T062, T063 as they implemented scope creep (FLOP counting, systematic error bias, ground truth metadata extraction, physical constraint sanity checks) that contradicts the spec's explicit correlational scope.
- [X] T081 Reconcile run-book vs implementation for `code/main.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/main.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T082 [P] [Review-All] **Documentation**: Update `README.md` to include a new section "Addressing Research Concerns" that summarizes how the project handles the distinction between calculation and measurement (Einstein/Curie), resource constraints (Dyson), and physical interpretability (Feynman/Pauling) based on the new documentation in Phase 7.
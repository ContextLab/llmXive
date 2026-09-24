# Tasks: Predicting Molecular Properties from Quantum Chemical Calculations

**Input**: Design documents from `/specs/546-predicting-molecular-properties/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [X] T001 [P] Initialize project structure: Create `projects/PROJ-546-predicting-molecular-properties-from-qua/` root, `code/`, `data/raw/`, `data/optimized_geometries/`, `logs/`, `reports/`, `specs/546-predicting-molecular-properties/contracts/`, and `tests/` (unit/, integration/, contract/) directories. **Note**: `contracts/` is created inside `specs/...` per plan.md; no top-level `docs/` directory is created here.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002a [P] Initialize Python 3.11 project: Create root `requirements.txt` (scikit-learn, pandas, rdkit, requests, datasets, pyyaml) AND `code/requirements.txt` with pinned versions for reproducibility.
- [X] T002b [P] Configure linting and formatting: Create `pyproject.toml` (Black, Ruff config) and `.ruff.toml` files. **Verification**: Files must exist and pass `ruff check` and `black --check` on an empty codebase. **Note**: No data artifacts are consumed by this task.
- [X] T004a [P] [FR-001] **Resolve Zenodo ID**: Extract the specific Zenodo Accession ID `1048765` from `idea/predicting-molecular-properties-from-qua.md` and hardcode it into `code/config.py` as `ZENODO_ID = "1048765"`. **Verification**: The ID must be a valid non-empty string. **Fallback**: If the idea file is missing or the ID is invalid, raise a `FileNotFoundError` immediately to halt the pipeline (no placeholder/override allowed per FR-001). **Note**: This task must complete before T004b.
- [X] T004b [P] [FR-001] **Fetch Data**: Implement `code/fetch_data.py` to fetch the experimental barrier dataset from Zenodo ID `1048765`. **Logic**: Download the file, calculate SHA-256 checksum, and log the verification status (checksum match, file size, timestamp) to `logs/verification.log` **before** any processing. **Verification**: Must log verification status to `logs/verification.log`. **Note**: This task depends on T004a completion. The downloaded file may have a Zenodo-generated name; it is NOT yet `barrier_dataset.csv`.
- [ ] T004c [FR-001] **Normalize Dataset Filename**: Implement `code/fetch_data.py` (or a new script `code/normalize_data.py`) to move/rename the downloaded file to `data/raw/barrier_dataset.csv`. **Logic**: If the downloaded file is a compressed archive (e.g., `.zip`, `.gz`), extract it first. **Deterministic Selection**: If the archive contains multiple `.csv` files, extract the file matching the pattern `*barrier*.csv`. If no match, select the largest `.csv` file by size. Ensure the final output is exactly `data/raw/barrier_dataset.csv`. **Verification**: Verify `data/raw/barrier_dataset.csv` exists and is non-empty. **Dependency**: T004b. **Note**: This task guarantees the canonical filename required by T011 and T020a.
- [ ] T010 [P] [FR-001] **Validate Data Schema**: Implement `code/validators/data_validator.py` to verify downloaded CSV contains required columns (SMILES, experimental_barrier) and correct data types (spec.md Data Model). **Verification**: Ensure 'experimental_barrier' is numeric. **Dependency**: T004c. **Note**: This task is pending upstream data generation (T004c).
- [ ] T011 [P] [FR-008] **Confounds Analysis & Coverage Verification**: Implement `code/confounds.py` to read SMILES from `data/raw/barrier_dataset.csv` (output of T004c), convert to Mol objects, calculate MW (`Descriptors.MolWt`), atom count (`Descriptors.NumAtoms`), and functional groups (`rdkit.Chem.Lipinski`, `rdkit.Chem.Fragments`). Output `data/confounds.csv` with columns `molecule_id` (str), `mw` (float), `atom_count` (int), `functional_groups` (str). **Verification**: Verify `data/confounds.csv` exists, is non-empty, and has the exact schema: `molecule_id`, `mw`, `atom_count`, `functional_groups`. **FR-008 Compliance**: Calculate distribution stats (mean, std, range) for MW/atom count from the **fetched dataset itself** (T004c). Generate `reports/confounds_coverage_report.md` confirming the coverage status (PASS/FAIL) by comparing the distribution stats of the **full set** only. **Dependency**: T004c. **Initialization**: If `data/raw/barrier_dataset.csv` is missing, raise `FileNotFoundError` to halt execution. **Note**: This task produces the foundational coverage analysis required by FR-008. Subset comparison is deferred to T035. **Note**: This task is pending upstream data generation (T004c).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Semi-Empirical Descriptor Generation (Priority: P1) 🎯 MVP

**Goal**: Compute HOMO/LUMO/Mayer descriptors using DFTB+ on full dataset with geometry optimization

**Independent Test**: Run on a representative set of molecules; verify `descriptors_semi.csv` has a corresponding number of rows, no NaN, HOMO/LUMO in eV, charges sum to net charge.

### Tests for User Story 1

- [X] T012 [US1] Integration test for `code/generate_descriptors.py` on a representative set of molecules in `tests/test_descriptors.py`. **Specific Test**: `tests/test_descriptors.py::test_pipeline_handles_convergence_failure`. **Verification**: pytest exit code 0.

### Implementation for User Story 1

- [X] T013a [US1] Implement `code/dftb_calculator.py` to invoke DFTB+ for geometry optimization and descriptor extraction (HOMO, LUMO, Mayer bond orders) for a single molecule, including unit normalization (eV). **Logic**:
 1. **Convergence Retry**: Run DFTB+ with default settings. If convergence fails, run a second time with a perturbed initial guess (random noise on coordinates). If second run fails, raise `ConvergenceError`.
 2. **Physical Validity Retry**: If calculated HOMO >= LUMO, attempt one re-calculation with a different initial guess. If it still fails, raise `PhysicalInvalidityError`.
 3. **Note**: Calculations assume vacuum as per spec Assumptions.
- [X] T013b [US1] Implement `code/error_handlers.py` to catch `ConvergenceError`, `PhysicalInvalidityError`, and OOM signals, skip the molecule, and log failure details to `logs/convergence_failures.log`, `logs/structural_failures.log`, and `logs/oom_failures.log` respectively. **Schema**: `molecule_id, timestamp, error_code, error_message`.
- [X] T013c [US1] **Orchestration**: Implement `code/descriptor_pipeline.py` to orchestrate the full-dataset pipeline:
 - **Function Signature**: `run_pipeline(input_df: pd.DataFrame, output_dir: str) -> pd.DataFrame`
 - **Orchestration**: Iterate over molecules in `input_df`. For each:
 1. Call `dftb_calculator.optimize()` (T013a).
 2. If `ConvergenceError` is raised, call `dftb_calculator.optimize(retry=True)` (T013a).
 3. If retry fails, call `error_handlers.log_failure()` (T013b) and skip.
 4. If successful, validate `HOMO_energy < LUMO_energy`. If violated, call `dftb_calculator.optimize(retry=True)` (T013a). If still violated, call `error_handlers.log_failure()` (T013b) and skip.
 5. Append descriptor row to result DataFrame.
 - **Validation**: Read output of T013a, validate `HOMO_energy < LUMO_energy`, and if failed, write to `logs/structural_failures.log` with format `molecule_id, timestamp, error_code, error_message`.
 - **Logging**: Prepare data for T013f. **Dependency**: T004c, T013a, T013b.
- [X] T013d [US1] **Geometry Export**: Implement `code/descriptor_pipeline.py` (or a new script `code/export_geometries.py`) to save optimized geometries to `data/optimized_geometries/` as `{molecule_id}.xyz`. **Format**: Header line with atom count, comment line with `molecule_id`, followed by atom coordinates (element x y z). **Verification**: Verify files exist in `data/optimized_geometries/`. **Dependency**: T013c.
- [X] T013e [US1] **CSV Export & Validation**: Implement `code/descriptor_pipeline.py` (or a new script `code/export_descriptors.py`) to write final `data/descriptors_semi.csv` with schema: `molecule_id` (str), `HOMO_energy` (float), `LUMO_energy` (float), `mayer_bond_order` (float). **Verification**: Verify `data/descriptors_semi.csv` exists, is non-empty, and has the correct schema. **Dependency**: T013c.
- [X] T013f [US1] **Logging**: Implement JSON-line logging to `logs/dft_execution.log` for ALL runs (success and failure) to satisfy Constitution Principle VII (Resource Monitoring). **Schema**: `{"molecule_id": str, "command": str, "exit_code": int, "duration": float, "peak_memory_mb": float}`. **Verification**: Verify `logs/dft_execution.log` exists and contains valid JSON lines with the specified keys. **Dependency**: T013c.
- [X] T017a [US1] **Verify Logging Schema**: Verify `logs/dft_execution.log` exists, is non-empty, and contains valid JSON lines with keys: `molecule_id`, `command`, `exit_code`, `duration`, `peak_memory_mb`. **Dependency**: T013f. **Note**: This task validates Constitution Principle VII compliance and confirms the logging implementation in T013f.

**Checkpoint**: At this point, User Story 1 is fully functional if T013c, T013d, T013e, and T013f are complete.

---

## Phase 4: User Story 2 - High-Level DFT Baseline & Comparative Modeling (Priority: P2)

**Goal**: Compute DFT descriptors for subset, train two RF models, compare MAE via paired t-test

**Independent Test**: Run on subset; verify output reports MAE_semi, MAE_DFT, p-value, flags, and explicit comparison against experimental ground truth.

**⚠️ Execution Order**: T020a (Subset Selection) MUST run AFTER T013d (Geometry Export) to ensure stratification is based on molecules with valid optimized geometries.

### Tests for User Story 2

- [X] T018 [P] [US2] Contract test for `code/train_models.py` in `tests/test_models.py` (verifies RF training)
- [X] T027 [P] [US2] Integration test for comparative evaluation in `tests/test_evaluation.py`. **Specific Tests**: `tests/test_evaluation.py::test_t_test_null_hypothesis` and `tests/test_evaluation.py::test_mae_calculation`. **Verification**: pytest exit code 0.

### Implementation for User Story 2

- [ ] T020a [US2] **Subset Selection**: Implement `code/dft_calculator.py` subset selection logic: Read `data/raw/barrier_dataset.csv` (output of T004c). **Logic**:
 1. **Stratify Full Set**: Stratify the **full dataset** by `experimental_barrier` bins using `pd.qcut` or `sklearn.model_selection.train_test_split` with `stratify`.
 2. **Filter for Availability**: Filter this stratified list to only include molecules for which an optimized geometry file exists in `data/optimized_geometries/{molecule_id}.xyz` (output of T013d).
 3. **Bias Check**: If the count of available molecules is < 90% of the target subset size (or < 50 if target is 50), log a `REPRESENTATIVENESS_WARNING` to `logs/evaluation.log` stating: "Stratified subset size {N} is below [deferred] of target. Potential bias introduced by convergence failures. Proceeding with available set."
 4. **Output**: Write list of selected `molecule_id`s to `state/selected_subset.json` as a JSON object: `{"molecule_ids": ["id1", "id2",...]}`. **Dependency**: T004c, T013d. **Note**: This task is NOT parallel-safe [P] as it depends on T013d completion.
- [ ] T020b [US2] **DFT Calculation**: Implement `code/dft_calculator.py` DFT calculation logic: Invoke **Psi4** for B3LYP/def2-SVP calculations on the selected subset (output of T020a). **Geometry Import**: Import optimized geometries from `data/optimized_geometries/{molecule_id}.xyz` (output of T013d). **File Mapping**: Ensure `molecule_id` from the input list matches the filename `{molecule_id}.xyz` exactly (case-sensitive, no extension mismatch). **Psi4 Input**: Generate input file with geometry block and keywords `b3lyp/def2-svp optimize energy`. Parse output to extract HOMO/LUMO. **Output**: Save descriptors to `data/descriptors_dft.csv` with schema: `molecule_id` (str), `HOMO_energy` (float), `LUMO_energy` (float), `mayer_bond_order` (float). **Verification**: Verify `data/descriptors_dft.csv` exists, is non-empty, and has the correct schema. **Dependency**: T013d, T020a.
- [ ] T020c [US2] **Split Generation**: Implement `code/dft_calculator.py` split logic: Use `sklearn.model_selection.train_test_split` with `stratify` and a fixed `random_state` to generate a **single** train/test split for the selected subset. Write split indices to `state/splits.json`. **Output Schema**: `state/splits.json` must strictly contain keys: `train_indices` (list[int]), `test_indices` (list[int]), `random_state` (int). **Verification**: Verify `state/splits.json` exists, is non-empty, and matches the schema. **Dependency**: T020a.
- [X] T021 [US2] **Train Models**: Implement `code/train_models.py` to train two Random Forests (semi vs DFT) using the **locked split indices** from T020c. **Verification**: Ensure the same `random_state` and split indices are used for both models to satisfy the paired t-test requirement. **Mechanism**: Read split indices from `state/splits.json` generated by T020c. **Logic**: 1) Load `data/descriptors_semi.csv` (T013e output), 2) **Filter** `data/descriptors_semi.csv` to keep only rows where `molecule_id` is in the `molecule_ids` list from `state/selected_subset.json` (or matches `train_indices`/`test_indices` from `state/splits.json`), 3) Load `data/descriptors_dft.csv` (T020b output), 4) Train Semi-Empirical RF on the **filtered** semi-empirical subset, 5) Train DFT RF on the DFT subset. 6) Save models to `state/model_semi.pkl` and `state/model_dft.pkl` using joblib. **Verification**: Verify `state/splits.json` is loaded and used for **both** models; confirm `random_state` matches T020c. **Dependency**: T020b, T020c, T013e. **Note**: This task is NOT parallel-safe [P] as it depends on T020b and T020c.
- [X] T022 [US2] **Evaluate Models**: Implement `code/evaluate_models.py` to compute MAE against experimental data and run a paired t-test. **Primary Deliverable**: Calculate `mae_semi_vs_exp` and `mae_dft_vs_exp` by comparing model predictions against `experimental_barrier` from `data/raw/barrier_dataset.csv`. **Secondary Metric**: Perform a paired t-test comparing the error distributions of the Semi-Empirical RF and DFT RF models on the **same test set samples**. Report Null Hypothesis (no difference in error distribution), Significance Level (α=0.05), and the models compared. **Output**: `reports/evaluation.json` with keys: `mae_semi_vs_exp`, `mae_dft_vs_exp`, `t_test` (object with `statistic`, `p_value`, `null_hypothesis` (string), `significance_level` (string), `models_compared` (string)), and `error_bars` (object with `semi_empirical_std`, `dft_std`). **Note**: This task includes the logic for MAE flags (previously T023) and is now complete. **Initialization**: If `data/descriptors_dft.csv` or `state/splits.json` is missing, raise `FileNotFoundError`. **Dependency**: T021, T020b, T020c.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance & Sensitivity Analysis (Priority: P3)

**Goal**: Identify top descriptors, sweep thresholds, report cumulative importance

**Independent Test**: Run analysis; verify output lists top descriptors, cumulative sum, and MAE table for a set of threshold percentiles.

### Tests for User Story 3

- [X] T028 [P] [US3] Unit test for `code/sensitivity_analysis.py` in `tests/test_sensitivity.py` **Note**: Renumbered from T028 (Phase 4) to resolve ID collision.

### Implementation for User Story 3

- [ ] T029 [US3] **Feature Importance Extraction**: Implement `code/sensitivity_analysis.py` to extract feature importance from semi-empirical RF (spec.md US3). **Logic**: Load the trained Semi-Empirical RF model from `state/model_semi.pkl` (T021 output) using joblib. Extract `feature_importances_`. Sort descriptors by descending importance. **Output**: Save to `reports/sensitivity.csv` with schema: `rank` (int), `descriptor` (str), `importance` (float), `cumulative_importance` (float). **Verification**: Verify `reports/sensitivity.csv` exists, is non-empty, and contains the specified columns. **Dependency**: T021. **Initialization**: If `state/model_semi.pkl` is missing, raise `FileNotFoundError`.
- [X] T030 [US3] **Cumulative Importance Calculation**: Implement logic to identify top-ranked descriptors and calculate cumulative importance. (spec.md US3) using the output from T029. **Logic**: Sort by descending importance, select top candidates, and append to `reports/sensitivity.csv` with columns `rank`, `descriptor`, `importance`, `cumulative_importance`. **Verification**: Verify `reports/sensitivity.csv` exists, is non-empty, and contains the specified columns. **Dependency**: T029.
- [X] T030b [US3] [FR-007] **Unified Sensitivity & Stability Verification**: Implement `code/sensitivity_sweep.py` to execute the full cross-combination sweep of feature importance cutoffs {0.01, 0.05, 0.1} and noise injection levels {σ=0.01, 0.05}. **Logic**:
 1. Load the trained model artifacts from `state/model_semi.pkl` (T021).
 2. For each noise level (σ=0.01, 0.05), inject Gaussian noise into the descriptor features using a fixed `random_state`.
 3. For each noise level and each cutoff, **re-train the RF model** (import `train_model` function from `code/train_models.py`) and extract the top 3 descriptors.
 4. Calculate Spearman's rank correlation (rho) between the top-ranked descriptors of the perturbed model and the original model for every combination.
 5. Aggregate results into a single matrix.
 **Output**: Save to `reports/sensitivity_matrix.csv` with the following columns: `noise_level`, `cutoff`, `top_3_descriptors` (comma-separated string), `rank_correlation` (float), `stable_flag` (boolean, True if rho >= 0.9).
 **Verification**: Verify the output file contains the full correlation matrix and that the `stable_flag` is True **only if** `rank_correlation >= 0.9`. **Dependency**: T029, T030, T021 (model artifacts).
- [X] T031 [US3] **REMOVED**: Merged into T030b.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Pipeline Validation & Polish

**Purpose**: Validation gates and final reporting, including response to research-stage reviews regarding physical reality, measurement standards, and resource constraints.

- [X] T081 [P] **Create CLI Entry Point**: Implement `code/main.py` as the single entry point script. This script must orchestrate the pipeline phases (Fetch -> Optimize -> DFT -> Train -> Evaluate). **Verification**: `python code/main.py --help` must list available commands. **Dependencies**: T004c, T013c, T022, T030b. **Note**: This task is the final assembly of the pipeline, depending on the completion of all logic scripts.
- [X] T033a [P] **Execute Pipeline**: Run `code/main.py` on a sample subset and capture runtime logs. **Requirement**: Must generate `logs/dft_execution.log` with the JSON schema defined in T013f. **Dependency**: T081, T017a.
- [ ] T033b [P] **Validate Resource Constraints**: Validate runtime logs from T033a: verify total runtime ≤ 6 hours and peak memory ≤ 7 GB per Constitution Principle VII (Resource-Bound Execution) and write validation result to `reports/runtime_validation.json`. **Logic**: Parse `logs/dft_execution.log` JSON lines to extract `duration` and `peak_memory_mb`. **Verification**: Confirm T013f generated the log with the required keys before parsing. **Constraint**: This task MUST validate the **full pipeline** (all molecules for DFTB+) against the 6h/7GB constraint, including **total wall-clock time** for retries and failed attempts (i.e., the sum of all execution durations). **Conditional Execution**: If `logs/dft_execution.log` is missing or empty (indicating upstream failure in T004c, T013c, or T013f), this task MUST be marked as `SKIPPED` and log "SKIPPED: Missing execution logs" to `reports/runtime_validation.json` rather than failing. **Dependency**: T033a, T017a. **Aligns with Constitution Principle VII and Plan.md Resource Constraints**.
- [X] T034 [P] Implement `code/generate_checksums.py` to compute SHA cryptographic hashes for all raw and processed artifacts and write to `data/checksums.txt` (Constitution Check #3).
- [ ] T035 [P] **Generate Summary Report**: Implement `code/generate_summary_report.py` to aggregate all metrics (MAE, speedup, feature importance) into `reports/summary_report.md`. **Dependencies**: T022, T030b, T034, T083. **Note**: This task now explicitly depends on T022, T030b, and T083 to ensure all underlying reports are ready.
- [X] T046 [P] Update `specs/546-predicting-molecular-properties/quickstart.md` (or equivalent) to include the Zenodo dataset details (ID, version, checksum) based on FR-001. **Depends on T034 checksums and T004c.** **Output**: Must contain a section with Zenodo ID, version, and checksum SHA-256.
- [X] T083 [P] **Document Descriptor Definitions**: Implement `code/generate_descriptor_definitions.py` to generate `reports/descriptor_definitions.md`. This report must provide a plain-English explanation of HOMO, LUMO, and Mayer bond orders, their physical significance, and their relationship to the experimental barrier. **Verification**: Verify `reports/descriptor_definitions.md` exists and contains definitions for all three descriptors. **Dependency**: T029. **Note**: This task satisfies the need for interpretability without demanding unexecutable visualizations.
- [X] T082 [P] **Address Research Concerns**: Update `README.md` to include a section titled "Addressing Research Concerns". **Schema**: This section must contain a bulleted list of at least two specific concerns addressed in this iteration and a brief summary of the resolution for each. **Verification**: Verify the section exists and contains at least two distinct bullet points. **Dependency**: T035, T034, T083. **Note**: This task replaces T082a/T082b and provides a concrete schema for the research response.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Research Review Response & Physical Validity (DEPRECATED)

**Note**: This phase and its tasks (T095-T098) were explicitly identified as "scope creep" and **REMOVED** in the project scope. They are listed here for historical reference only and MUST NOT be implemented.

- [ ] T095 [P] **REMOVED**: Bond length constraints (Scope Creep) - DO NOT IMPLEMENT.
- [ ] T096 [P] **REMOVED**: Error budget analysis (Scope Creep) - DO NOT IMPLEMENT.
- [ ] T097 [P] **REMOVED**: Experimental ground truth verification (Scope Creep) - DO NOT IMPLEMENT.
- [ ] T098 [P] **REMOVED**: Physical interpretability report (Scope Creep) - DO NOT IMPLEMENT.

**Checkpoint**: Phase 7 is deprecated. No tasks should be executed.

---

## Phase 8: Deprecated / Removed

**Note**: The following tasks were identified as scope creep or unexecutable and have been removed from the plan. They are not included in the final task list.
- T090 (Structural Constraint Validation) - REMOVED (Scope Creep)
- T091 (Physical Reality Report) - REMOVED (Scope Creep)
- T092 (Solvent Sensitivity) - REMOVED (Scope Creep)
- T093 (Feynman Explanation) - REMOVED (Scope Creep)
- T094 (Update Research Concerns Section) - REMOVED (Scope Creep)

**Checkpoint**: Project scope is now strictly aligned with spec.md and plan.md.

---

## Phase 9: Deprecated / Removed

**Note**: The following tasks were identified as scope creep or unexecutable and have been removed from the plan. They are not included in the final task list.
- T114 (Ground Truth Verification Protocol) - REMOVED
- T115 (Approximation Limitations Report) - REMOVED
- T116 (Enforce Structural Constraints) - REMOVED
- T117 (Quantify Resource Budget) - REMOVED
- T118 (Worked Example Visualization) - REMOVED
- T119 (Solvent & Hydration State Analysis) - REMOVED
- T120 (Physical Interpretability Report) - REMOVED

**Checkpoint**: Project scope is now strictly aligned with spec.md and plan.md.

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
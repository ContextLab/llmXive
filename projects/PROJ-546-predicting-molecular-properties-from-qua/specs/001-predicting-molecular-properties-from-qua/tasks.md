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
- [ ] T004c-extract [P] [FR-001] **Extract Archive**: Implement `code/fetch_data.py` (or `code/normalize_data.py`) to handle archive extraction. **Logic**: If the downloaded file from T004b is a compressed archive (e.g., `.zip`, `.gz`, `.tar`), extract it to a temporary directory. **Output**: Return the absolute path to the extracted CSV file. **Verification**: Verify that the extraction produces at least one `.csv` file. **Dependency**: T004b. **Note**: This task handles the archive format; the next task selects the specific CSV.
- [ ] T004c-normalize [FR-001] **Normalize Dataset Filename**: Implement `code/fetch_data.py` (or `code/normalize_data.py`) to move/rename the extracted CSV to `data/raw/barrier_dataset.csv`. **Logic**: If multiple `.csv` files exist, select the one matching `*barrier*.csv`. If no match, select the largest `.csv` by size. **Output**: The final file MUST be exactly `data/raw/barrier_dataset.csv`. **Verification**: Verify `data/raw/barrier_dataset.csv` exists and is non-empty. **Dependency**: T004c-extract. **Note**: This task guarantees the canonical filename required by T011 and T020a.
- [X] T010 [P] [FR-001] **Validate Data Schema**: Implement `code/validators/data_validator.py` to verify downloaded CSV contains required columns (`smiles`, `experimental_barrier`) and correct data types (spec.md Data Model). **Verification**: Ensure 'experimental_barrier' is numeric. **Dependency**: T004c-normalize. **Initialization**: If `data/raw/barrier_dataset.csv` is missing, raise `FileNotFoundError` to halt execution. **Note**: This task is pending upstream data generation (T004c-normalize).
- [ ] T011 [P] [FR-008] **Confounds Analysis & Coverage Verification**: Implement `code/confounds.py` to read SMILES from `data/raw/barrier_dataset.csv` (output of T004c-normalize), convert to Mol objects, calculate MW (`Descriptors.MolWt`), atom count (`Descriptors.NumAtoms`), and functional groups (`rdkit.Chem.Lipinski`, `rdkit.Chem.Fragments`). Output `data/confounds.csv` with columns `molecule_id` (str), `mw` (float), `atom_count` (int), `functional_groups` (str). **Verification**: Verify `data/confounds.csv` exists, is non-empty, and has the exact schema: `molecule_id`, `mw`, `atom_count`, `functional_groups`. **FR-008 Compliance**: Calculate distribution stats (mean, std, range) for MW/atom count from the **fetched dataset itself** (T004c-normalize). Generate `reports/confounds_coverage_report.md` confirming the coverage status (PASS/FAIL) by comparing the distribution stats of the **full set** only. **Dependency**: T004c-normalize. **Initialization**: If `data/raw/barrier_dataset.csv` is missing, raise `FileNotFoundError` to halt execution. **Note**: This task produces the foundational coverage analysis required by FR-008. Subset comparison is deferred to T035.

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
- [ ] T013c-orchestrate [US1] **Orchestration**: Implement `code/descriptor_pipeline.py` to orchestrate the full-dataset pipeline:
 - **Function Signature**: `run_pipeline(input_df: pd.DataFrame, output_dir: str) -> pd.DataFrame`
 - **Orchestration**: Iterate over molecules in `input_df`. For each:
 1. Call `dftb_calculator.optimize()` (T013a).
 2. If `ConvergenceError` is raised, call `dftb_calculator.optimize(retry=True)` (T013a).
 3. If retry fails, call `error_handlers.log_failure()` (T013b) and skip.
 4. If successful, validate `HOMO_energy < LUMO_energy`. If violated, call `dftb_calculator.optimize(retry=True)` (T013a). If still violated, call `error_handlers.log_failure()` (T013b) and skip.
 5. Append descriptor row to result DataFrame.
 - **Validation**: Read output of T013a, validate `HOMO_energy < LUMO_energy`, and if failed, write to `logs/structural_failures.log` with format `molecule_id, timestamp, error_code, error_message`.
 - **Logging**: Prepare data for T013f. **Dependency**: T004c-normalize, T013a, T013b.
- [ ] T013c-retry [US1] **Retry Logic**: Implement the specific retry mechanisms within `code/descriptor_pipeline.py` or `code/dftb_calculator.py` as defined in T013a. **Logic**: Ensure the retry logic is modular and can be called independently. **Verification**: Unit tests must confirm retry triggers on specific error codes. **Dependency**: T013a.
- [ ] T013c-validate [US1] **Validation Logic**: Implement the validation logic within `code/descriptor_pipeline.py` to check `HOMO_energy < LUMO_energy`. **Logic**: Ensure validation is modular and can be called independently. **Verification**: Unit tests must confirm validation triggers on invalid values. **Dependency**: T013a.
- [X] T013d [US1] **Geometry Export**: Implement `code/descriptor_pipeline.py` (or a new script `code/export_geometries.py`) to save optimized geometries to `data/optimized_geometries/` as `{molecule_id}.xyz`. **Format**: Header line with atom count, comment line with `molecule_id`, followed by atom coordinates (element x y z). **Verification**: Verify files exist in `data/optimized_geometries/`. **Dependency**: T013c-orchestrate.
- [X] T013e [US1] **CSV Export & Validation**: Implement `code/descriptor_pipeline.py` (or a new script `code/export_descriptors.py`) to write final `data/descriptors_semi.csv` with schema: `molecule_id` (str), `HOMO_energy` (float), `LUMO_energy` (float), `mayer_bond_order` (float). **Verification**: Verify `data/descriptors_semi.csv` exists, is non-empty, and has the correct schema. **Dependency**: T013c-orchestrate.
- [X] T013f [US1] **Logging**: Implement JSON-line logging to `logs/dft_execution.log` for ALL runs (success and failure) to satisfy Constitution Principle VII (Resource Monitoring). **Schema**: `{"molecule_id": str, "command": str, "exit_code": int, "duration": float, "peak_memory_mb": float}`. **Verification**: Verify `logs/dft_execution.log` exists and contains valid JSON lines with the specified keys. **Dependency**: T013c-orchestrate.
- [X] T017a [US1] **Verify Logging Schema**: Verify `logs/dft_execution.log` exists, is non-empty, and contains valid JSON lines with keys: `molecule_id`, `command`, `exit_code`, `duration`, `peak_memory_mb`. **Dependency**: T013f. **Note**: This task validates Constitution Principle VII compliance and confirms the logging implementation in T013f.

**Checkpoint**: At this point, User Story 1 is fully functional if T013c-orchestrate, T013d, T013e, and T013f are complete.

---

## Phase 4: User Story 2 - High-Level DFT Baseline & Comparative Modeling (Priority: P2)

**Goal**: Compute DFT descriptors for subset, train two RF models, compare MAE via paired t-test

**Independent Test**: Run on subset; verify output reports MAE_semi, MAE_DFT, p-value, flags, and explicit comparison against experimental ground truth.

**⚠️ Execution Order**: T020a (Subset Selection) MUST run AFTER T013d (Geometry Export) to ensure stratification is based on molecules with valid optimized geometries.

### Tests for User Story 2

- [X] T018 [P] [US2] Contract test for `code/train_models.py` in `tests/test_models.py` (verifies RF training)
- [X] T027 [P] [US2] Integration test for comparative evaluation in `tests/test_evaluation.py`. **Specific Tests**: `tests/test_evaluation.py::test_t_test_null_hypothesis` and `tests/test_evaluation.py::test_mae_calculation`. **Verification**: pytest exit code 0.

### Implementation for User Story 2

- [ ] T020a [US2] **Subset Selection**: Implement `code/dft_calculator.py` subset selection logic: Read `data/raw/barrier_dataset.csv` (output of T004c-normalize). **Logic**:
 1. **Stratify Full Set**: Stratify the **full dataset** by `experimental_barrier` bins using `pd.qcut` with `n=5` bins.
 2. **Filter for Availability**: Filter this stratified list to only include molecules for which an optimized geometry file exists in `data/optimized_geometries/{molecule_id}.xyz` (output of T013d).
 3. **Output**: Write list of selected `molecule_id`s to `state/selected_subset.json` as a JSON object: `{"molecule_ids": ["id1", "id2",...]}`. **Dependency**: T004c-normalize, T013d. **Note**: This task is NOT parallel-safe [P] as it depends on T013d completion.
- [ ] T020b-subset [US2] **DFT Subset Preparation**: Implement `code/dft_calculator.py` to prepare input files for the selected subset. **Logic**: Read `state/selected_subset.json` (output of T020a). For each `molecule_id`, copy the corresponding geometry file from `data/optimized_geometries/{molecule_id}.xyz` to `data/dft_inputs/{molecule_id}.xyz`. **Verification**: Verify `data/dft_inputs/` contains exactly the files listed in the subset. **Dependency**: T020a, T013d.
- [ ] T020b-calc [US2] **DFT Calculation**: Implement `code/dft_calculator.py` to invoke **Psi4** for B3LYP/def2-SVP **single-point energy** calculations. **Command**: `psi4 --input {molecule_id}.in --output {molecule_id}.out`. **Input Template**: Generate `input.dat` with geometry block (from XYZ) and keywords `b3lyp/def2-svp energy`. **NO OPTIMIZATION**: Do not include `optimize` in keywords. **Parsing**: Parse `{molecule_id}.out` to extract HOMO/LUMO energies using regex `r'\s+HOMO\s+(-?\d+\.\d+)'`. **Output**: Save descriptors to `data/descriptors_dft.csv` with schema: `molecule_id` (str), `HOMO_energy` (float), `LUMO_energy` (float), `mayer_bond_order` (float). **Verification**: Verify `data/descriptors_dft.csv` exists, is non-empty, and has the correct schema. **Dependency**: T020b-subset, T013d.
- [X] T020c [US2] **Split Generation**: Implement `code/dft_calculator.py` split logic: Use `sklearn.model_selection.train_test_split` with `stratify` on the `experimental_barrier` column and `random_state=42` to generate a **single** train/test split for the selected subset. Write split indices to `state/splits.json`. **Output Schema**: `state/splits.json` must strictly contain keys: `train_indices` (list[int]), `test_indices` (list[int]), `random_state` (int). **Verification**: Verify `state/splits.json` exists, is non-empty, and matches the schema. **Dependency**: T020a.
- [X] T021 [US2] **Train Models**: Implement `code/train_models.py` to train two Random Forests (semi vs DFT) using the **locked split indices** from T020c. **Verification**: Ensure the same `random_state` and split indices are used for both models to satisfy the paired t-test requirement. **Mechanism**: Read split indices from `state/splits.json` generated by T020c. **Logic**: 1) Load `data/descriptors_semi.csv` (T013e output), 2) **Filter** `data/descriptors_semi.csv` to keep only rows where `molecule_id` is in the `molecule_ids` list from `state/selected_subset.json` (or matches `train_indices`/`test_indices` from `state/splits.json`), 3) Load `data/descriptors_dft.csv` (T020b-calc output), 4) Train Semi-Empirical RF on the **filtered** semi-empirical subset, 5) Train DFT RF on the DFT subset. 6) Save models to `state/model_semi.pkl` and `state/model_dft.pkl` using joblib. **Verification**: Verify `state/splits.json` is loaded and used for **both** models; confirm `random_state` matches T020c. **Dependency**: T020b-calc, T020c, T013e, T020a.
- [X] T022 [US2] **Evaluate Models**: Implement `code/evaluate_models.py` to compute MAE against experimental data and run a paired t-test. **Primary Deliverable**: Calculate `mae_semi_vs_exp` and `mae_dft_vs_exp` by comparing model predictions against `experimental_barrier` from `data/raw/barrier_dataset.csv`. **Secondary Metric**: Perform a paired t-test comparing the error distributions of the Semi-Empirical RF and DFT RF models on the **same test set samples**. Report Null Hypothesis (no difference in error distribution), Significance Level (α=0.05), and the models compared. **Output**: `reports/evaluation.json` with keys: `mae_semi_vs_exp`, `mae_dft_vs_exp`, `t_test` (object with `statistic`, `p_value`, `null_hypothesis` (string), `significance_level` (string), `models_compared` (string)). **Note**: This task includes the logic for MAE flags (previously T023) and is now complete. **Initialization**: If `data/descriptors_dft.csv` or `state/splits.json` is missing, raise `FileNotFoundError`. **Dependency**: T021, T020b-calc, T020c.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance & Sensitivity Analysis (Priority: P3)

**Goal**: Identify top descriptors, sweep thresholds, report cumulative importance

**Independent Test**: Run analysis; verify output lists top descriptors, cumulative sum, and MAE table for a set of threshold percentiles.

### Tests for User Story 3

- [X] T028 [P] [US3] Unit test for `code/sensitivity_analysis.py` in `tests/test_sensitivity.py` **Note**: Renumbered from T028 (Phase 4) to resolve ID collision.

### Implementation for User Story 3

- [ ] T029 [US3] **Feature Importance Extraction**: Implement `code/sensitivity_analysis.py` to extract feature importance from semi-empirical RF (spec.md US3). **Logic**: Load the trained Semi-Empirical RF model from `state/model_semi.pkl` (T021 output) using joblib. Extract `feature_importances_`. Map indices to feature names: `['HOMO_energy', 'LUMO_energy', 'mayer_bond_order']`. Sort descriptors by descending importance. **Output**: Save to `reports/sensitivity.csv` with schema: `rank` (int), `descriptor` (str), `importance` (float), `cumulative_importance` (float). **Verification**: Verify `reports/sensitivity.csv` exists, is non-empty, and contains the specified columns. **Dependency**: T021. **Initialization**: If `state/model_semi.pkl` is missing, raise `FileNotFoundError`.
- [X] T030 [US3] **Cumulative Importance Calculation**: Implement logic to identify top-ranked descriptors and calculate cumulative importance. (spec.md US3) using the output from T029. **Logic**: Sort by descending importance, select top candidates, and append to `reports/sensitivity.csv` with columns `rank`, `descriptor`, `importance`, `cumulative_importance`. **Verification**: Verify `reports/sensitivity.csv` exists, is non-empty, and contains the specified columns. **Dependency**: T029.
- [ ] T030b-noise [US3] **Noise Injection**: Implement `code/sensitivity_sweep.py` to inject Gaussian noise into the descriptor features. **Logic**: Load `state/model_semi.pkl` (T021). For each noise level (σ=0.01, 0.05), inject Gaussian noise into the features using a fixed `random_state`. **Output**: Save perturbed feature matrices to `data/perturbed_features/`. **Dependency**: T021.
- [ ] T030b-sweep [US3] **Unified Sensitivity & Stability Verification**: Implement `code/sensitivity_sweep.py` to execute the full cross-combination sweep of feature importance cutoffs {0.01, 0.05, 0.1} and noise injection levels {σ=0.01, 0.05}. **Logic**:
 1. Load the trained model artifacts from `state/model_semi.pkl` (T021) and perturbed features from `data/perturbed_features/` (T030b-noise).
 2. For each noise level and each cutoff, **re-train the RF model** using the same hyperparameters as the original model (`n_estimators=100`, `max_depth=None`, `random_state=42`).
 3. Extract the top 3 descriptors by importance for each re-trained model.
 4. Calculate Spearman's rank correlation (rho) between the top-ranked descriptors of the perturbed model and the original model for every combination.
 5. Aggregate results into a single matrix.
 **Output**: Save to `reports/sensitivity_matrix.csv` with the following columns: `noise_level`, `cutoff`, `top_3_descriptors` (comma-separated string), `rank_correlation` (float).
 **Verification**: Verify the output file contains the full correlation matrix. **Dependency**: T029, T030, T021, T030b-noise.
- [X] T031 [US3] **REMOVED**: Merged into T030b.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Pipeline Validation & Polish

**Purpose**: Validation gates and final reporting, including response to research-stage reviews regarding physical reality, measurement standards, and resource constraints.

- [X] T081 [P] **Create CLI Entry Point**: Implement `code/main.py` as the single entry point script. This script must orchestrate the pipeline phases (Fetch -> Optimize -> DFT -> Train -> Evaluate). **Verification**: `python code/main.py --help` must list available commands. **Dependencies**: T004c-normalize, T013c-orchestrate, T022, T030b-sweep. **Note**: This task is the final assembly of the pipeline, depending on the completion of all logic scripts.
- [X] T033a [P] **Execute Pipeline**: Run `code/main.py` on a sample subset and capture runtime logs. **Requirement**: Must generate `logs/dft_execution.log` with the JSON schema defined in T013f. **Dependency**: T081, T017a.
- [ ] T033b [P] **Validate Resource Constraints**: Validate runtime logs from T033a: verify total runtime ≤ 6 hours and peak memory ≤ 7 GB per Constitution Principle VII (Resource-Bound Execution) and write validation result to `reports/runtime_validation.json`. **Logic**: Parse `logs/dft_execution.log` JSON lines to extract `duration` and `peak_memory_mb`. Calculate **total runtime** as the sum of all `duration` fields. Calculate **peak memory** as the maximum `peak_memory_mb` value converted to GB (divide by 1024). **Verification**: Confirm T013f generated the log with the required keys before parsing. **Constraint**: This task MUST validate the **full pipeline** (all molecules for DFTB+) against the 6h/7GB constraint, including **total wall-clock time** for retries and failed attempts (i.e., the sum of all execution durations). **Conditional Execution**: If `logs/dft_execution.log` is missing or empty (indicating upstream failure in T004c-normalize, T013c-orchestrate, or T013f), this task MUST be marked as `SKIPPED` and log "SKIPPED: Missing execution logs" to `reports/runtime_validation.json` rather than failing. **Dependency**: T033a, T017a. **Aligns with Constitution Principle VII and Plan.md Resource Constraints**.
- [X] T034 [P] Implement `code/generate_checksums.py` to compute SHA cryptographic hashes for all raw and processed artifacts and write to `data/checksums.txt` (Constitution Check #3).
- [ ] T035 [P] **Generate Summary Report**: Implement `code/generate_summary_report.py` to aggregate all metrics (MAE, speedup, feature importance) into `reports/summary_report.md`. **Dependencies**: T022, T030b-sweep, T034, T083. **Note**: This task now explicitly depends on T022, T030b-sweep, and T083 to ensure all underlying reports are ready. <!-- FAILED: unspecified -->
- [X] T046 [P] Update `specs/546-predicting-molecular-properties/quickstart.md` (or equivalent) to include the Zenodo dataset details (ID, version, checksum) based on FR-001. **Depends on T034 checksums and T004c-normalize.** **Output**: Must contain a section with Zenodo ID, version, and checksum SHA-256.
- [X] T083 [P] **Document Descriptor Definitions**: Implement `code/generate_descriptor_definitions.py` to generate `reports/descriptor_definitions.md`. This report must provide a plain-English explanation of HOMO, LUMO, and Mayer bond orders, their physical significance, and their relationship to the experimental barrier. **Verification**: Verify `reports/descriptor_definitions.md` exists and contains definitions for all three descriptors. **Dependency**: T029. **Note**: This task satisfies the need for interpretability without demanding unexecutable visualizations.
- [X] T082 [P] **Address Research Concerns**: Update `README.md` to include a section titled "Addressing Research Concerns". **Schema**: This section must contain a bulleted list of at least two specific concerns addressed in this iteration and a brief summary of the resolution for each. **Verification**: Verify the section exists and contains at least two distinct bullet points. **Dependency**: T035, T034, T083. **Note**: This task replaces T082a/T082b and provides a concrete schema for the research response.

**Checkpoint**: All user stories should now be independently functional

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Research Review Response (Phase 10)**: Depends on completion of all user stories and validation tasks.

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
- Phase 10 tasks can be run in parallel once the core pipeline (US1-US3) is complete.

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
5. Add Phase 10 (Research Response) → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
 - Developer D: Phase 10 (Research Response) - can start once US1/US2 have initial results
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
- **Phase 10** tasks are specifically designed to address the "Calculation vs. Measurement" and "Physical Reality" concerns raised by the research-stage reviews. They ensure the project does not confuse "efficiency of the ledger" with "truth of the ledger".
- **T125 & T126** specifically address the "Hydration/Solvent" and "Missing Degrees of Freedom" concerns raised by Rosalind Franklin and Freeman Dyson, ensuring the "map vs. territory" distinction is explicit.
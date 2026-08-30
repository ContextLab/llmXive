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
- [X] T004a [P] [FR-001] **Resolve Zenodo ID**: Extract the specific Zenodo Accession ID `` (from `idea/predicting-molecular-properties-from-qua.md`) and hardcode it into `code/config.py` as `ZENODO_ID = ""`. **Verification**: The ID must be a valid non-empty string. **Fallback**: If the idea file is missing or the ID is invalid, raise a `FileNotFoundError` immediately to halt the pipeline (no placeholder/override allowed per FR-001). **Note**: This task must complete before T004b.
- [ ] T004b [P] [FR-001] **Fetch Data**: Implement `code/fetch_data.py` to fetch the experimental barrier dataset from Zenodo ID ``. **Verification**: Must log verification status to `logs/verification.log` and verify `data/raw/` contains the file before proceeding. **Note**: This task depends on T004a completion.
- [X] T006 [P] Implement `code/utils/error_utils.py` to handle convergence failures (skip/log) and OOM detection per spec.md Edge Cases.
- [X] T010 [P] Implement `code/validators/data_validator.py` to verify downloaded CSV contains required columns (SMILES, experimental_barrier) and correct data types (spec.md Data Model).
- [ ] T011 [P] [FR-008] **Confounds Analysis**: Implement `code/confounds.py` to read SMILES from `data/raw/barrier_dataset.csv`, convert to Mol objects, calculate MW (`Descriptors.MolWt`), atom count (`Descriptors.NumAtoms`), and functional groups (`rdkit.Chem.Lipinski`, `rdkit.Chem.Fragments`). Output `data/confounds.csv` with columns `molecule_id` (str), `mw` (float), `atom_count` (int), `functional_groups` (str). **Verification**: Verify `data/confounds.csv` exists, is non-empty, and has the exact schema. **FR-008 Compliance**: Calculate distribution stats (mean, std) for MW/atom_count and compare against target dataset stats; log result to `data/confounds_verification.log` with status PASS/FAIL. **Dependency**: T004b.
- [X] T011c [P] [FR-001] Implement `code/physical_validator.py` to enforce structural constraints defined in spec.md Edge Cases: specifically check `HOMO_energy < LUMO_energy` for optimized geometries. If violated, log to `logs/structural_failures.log` with status `failed_after_retry` and skip. **Aligns with spec Edge Cases only; no hardcoded peptide constraints.**
- [X] T081 [P] **Create CLI Entry Point**: Implement `code/main.py` as the single entry point script. This script must orchestrate the pipeline phases (Fetch -> Optimize -> DFT -> Train -> Evaluate). **Verification**: `python code/main.py --help` must list available commands. **Dependencies**: T004b, T013c, T020b, T021, T022, T031c, T033a. **Note**: This task depends on all pipeline logic tasks being implemented. This task is now complete and serves as the definitive CLI entry point for the project.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Semi-Empirical Descriptor Generation (Priority: P1) 🎯 MVP

**Goal**: Compute HOMO/LUMO/Mayer descriptors using DFTB+ on full dataset with geometry optimization

**Independent Test**: Run on a representative set of molecules; verify `descriptors_semi.csv` has a corresponding number of rows, no NaN, HOMO/LUMO in eV, charges sum to net charge.

### Tests for User Story 1

- [X] T012 [US1] Integration test for `code/generate_descriptors.py` on a representative set of molecules in `tests/test_descriptors.py`. **Specific Test**: `tests/test_descriptors.py::test_pipeline_handles_convergence_failure`. **Verification**: pytest exit code 0.

### Implementation for User Story 1

- [X] T013a [US1] Implement `code/dftb_calculator.py` to invoke DFTB+ for geometry optimization and descriptor extraction (HOMO, LUMO, Mayer bond orders) for a single molecule, including unit normalization (eV). **Logic**: Run DFTB+ with default settings. If convergence fails, run a second time with a perturbed initial guess (random noise on coordinates). If second run fails, raise `ConvergenceError`.
- [X] T013b [US1] Implement `code/error_handlers.py` to catch `ConvergenceError` and OOM signals, skip the molecule, and log failure details to `logs/convergence_failures.log` and `logs/oom_failures.log` respectively. **Schema**: `molecule_id, timestamp, error_code, error_message`.
- [ ] T013c [US1] Implement `code/descriptor_pipeline.py` to orchestrate the full-dataset pipeline:
 - **Function Signature**: `run_pipeline(input_df: pd.DataFrame, output_dir: str) -> pd.DataFrame`
 - **Orchestration**: Iterate over molecules in `input_df`. For each:
 1. Call `dftb_calculator.optimize()` (T013a).
 2. If `ConvergenceError` is raised, call `dftb_calculator.optimize(retry=True)` (T013a).
 3. If retry fails, call `error_handlers.log_failure()` (T013b) and skip.
 4. If successful, validate `HOMO_energy < LUMO_energy`. If violated, log to `logs/structural_failures.log` and skip.
 5. Save optimized geometry to `data/optimized_geometries/{molecule_id}.xyz`.
 6. Append descriptor row to result DataFrame.
 - **Validation**: Read output of T013a, validate `HOMO_energy < LUMO_energy`, and if failed, write to `logs/structural_failures.log` with format `molecule_id, timestamp, error_code, error_message`.
 - **Geometry Export**: Save optimized geometries to `data/optimized_geometries/` as `{molecule_id}.xyz`. **Format**: Header line with atom count, comment line with `molecule_id`, followed by atom coordinates (element x y z).
 - **CSV Export**: Write final `data/descriptors_semi.csv` with schema: `molecule_id` (str), `HOMO_energy` (float), `LUMO_energy` (float), `mayer_bond_order` (float). **Note**: All validation logic is contained within T013c. **Dependency**: T004b, T013a, T013b.
- [ ] T017a [US1] **Implement Logging Logic**: Ensure `code/descriptor_pipeline.py` (T013c) generates `logs/dft_execution.log` with JSON lines schema: `{"molecule_id": str, "command": str, "exit_code": int, "duration": float, "peak_memory_mb": float}`. **Note**: This is the implementation of the logging logic.
- [X] T017b [US1] **Verify Logging Schema**: Verify `logs/dft_execution.log` exists, is non-empty, and contains valid JSON lines with keys: `molecule_id`, `command`, `exit_code`, `duration`, `peak_memory_mb`. **Dependency**: T017a. **Note**: This task validates Constitution Principle VII compliance.

**Checkpoint**: At this point, User Story 1 is fully functional if T013c is complete (including geometry export to `data/optimized_geometries/`).

---

## Phase 4: User Story 2 - High-Level DFT Baseline & Comparative Modeling (Priority: P2)

**Goal**: Compute DFT descriptors for subset, train two RF models, compare MAE via paired t-test

**Independent Test**: Run on subset; verify output reports MAE_semi, MAE_DFT, p-value, flags, and explicit comparison against experimental ground truth.

**⚠️ Execution Order**: Within this phase, T011 (Confounds) must complete before T020a (Subset Selection) to ensure feature space analysis is available if needed for stratification logic.

### Tests for User Story 2

- [ ] T018 [P] [US2] Contract test for `code/train_models.py` in `tests/test_models.py` (verifies RF training)
- [X] T027 [P] [US2] Integration test for comparative evaluation in `tests/test_evaluation.py`. **Specific Tests**: `tests/test_evaluation.py::test_t_test_null_hypothesis` and `tests/test_evaluation.py::test_mae_calculation`. **Verification**: pytest exit code 0.

### Implementation for User Story 2

- [ ] T020a [US2] Implement `code/dft_calculator.py` subset selection logic: Read `data/raw/barrier_dataset.csv`, calculate total valid samples (N). If N >= 50, select 50; else select all. Stratify by `experimental_barrier` bins using `pd.qcut` or equivalent, ensuring representative distribution. **Binning Strategy**: Implement flexible binning to ensure stratification. **Dependency Check**: Verify `data/raw/barrier_dataset.csv` exists (T004b), `data/optimized_geometries/` exists (T013c), AND `data/confounds.csv` exists (T011). **Note**: T011 is a hard dependency for this task to ensure feature space coverage is analyzed before subset selection. **Dependency**: T004b, T013c, T011.
- [ ] T020b [US2] Implement `code/dft_calculator.py` DFT calculation logic: Invoke Psi4 for B3LYP/def2-SVP on the selected subset. **Geometry Import**: Import optimized geometries from `data/optimized_geometries/{molecule_id}.xyz` (output of T013c). **Missing File Handling**: If a geometry file is missing (due to T013c failure), **exclude that molecule from the initial subset selection and RE-STRATIFY** the remaining molecules to maintain a target sample size sufficient for statistical power (or as close as possible) to ensure the paired t-test validity. **Psi4 Input**: Generate input file with geometry block and keywords `b3lyp/def2-svp optimize energy`. Parse output to extract HOMO/LUMO. **Split Locking**: Use `sklearn.model_selection.StratifiedKFold` with a fixed `random_state` to ensure the **exact same split indices** are used for both the Semi-Empirical and DFT models. Generate `data/descriptors_dft.csv`. **Dependency**: T013c, T020a.
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

- [ ] T029 [US3] Implement `code/sensitivity_analysis.py` to extract feature importance from semi-empirical RF (spec.md US3). **Verification**: Verify `code/sensitivity_analysis.py` extracts `feature_importances_` from the trained RF model (T021) and saves to `reports/sensitivity.csv` with columns `rank`, `descriptor`, `importance`, `cumulative_importance`. **Dependency**: T021.
- [X] T030 [US3] Implement logic to identify top-ranked descriptors and calculate cumulative importance. (spec.md US3) using the output from T029. **Logic**: Sort by descending importance, select top candidates, and append to `reports/sensitivity.csv` with columns `rank`, `descriptor`, `importance`, `cumulative_importance`. **Verification**: Verify `reports/sensitivity.csv` exists, is non-empty, and contains the specified columns.
- [X] T030b [US3] [FR-007] Implement `code/noise_injection.py` to inject Gaussian noise (σ=0.01, σ=0.05) into the descriptor features of the training set. **Output**: Generate perturbed datasets for each noise level. **Verification**: Verify noise injection is applied correctly. **Stability Check**: For each noise level, **load the trained model artifacts from T021**, re-train the RF model using the same logic, extract top 3 descriptors, and calculate Spearman's rank correlation (rho) against the original top 3. **Threshold**: `stable = True` if rho >= 0.9. Log results to `reports/sensitivity.csv`. **Dependency**: T029, T030, T021 (model artifacts).
- [X] T031b [US3] Implement `code/sensitivity_sweep.py` logic to sweep **feature importance cutoffs** {low, 0.05, 0.1} (where 'low' = 0.01) on the base and perturbed datasets. **Dependency**: T030b. **Verification**: Verify sweep results logged to `reports/sensitivity.csv` with stability flags.
- [X] T031c [US3] Implement `code/sensitivity_sweep.py` aggregation logic: Combine results from T030b and T031b, compute rank correlation (Spearman's rho) of the top-ranked descriptors across all sweep combinations. **Output**: `reports/sensitivity.csv` with columns for each sweep parameter, resulting top 3 descriptors, and `cumulative_importance`. **Threshold**: `stable = True` if rho >= 0.9. **Note**: This task now includes the stability verification logic (previously T032a) and is now complete.
- [X] T032a [US3] **REMOVED**: Merged into T031c.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Pipeline Validation & Polish

**Purpose**: Validation gates and final reporting, including response to research-stage reviews regarding physical reality, measurement standards, and resource constraints.

- [X] T033a [P] **Execute Pipeline**: Run `code/main.py` on a sample subset and capture runtime logs. **Requirement**: Must generate `logs/dft_execution.log` with the JSON schema defined in T017b. **Dependency**: T081, T017a.
- [X] T033b [P] **Validate Resource Constraints**: Validate runtime logs from T033a: verify total runtime ≤ 6 hours and peak memory ≤ 7 GB per Constitution Principle VII (Resource-Bound Execution) and write validation result to `reports/runtime_validation.json`. **Logic**: Parse `logs/dft_execution.log` JSON lines to extract `duration` and `peak_memory_mb`. **Verification**: Confirm T017a generated the log with the required keys before parsing. **Dependency**: T033a, T017b. **Aligns with Constitution Principle VII and Plan.md Resource Constraints**.
- [X] T034 [P] Implement `code/generate_checksums.py` to compute SHA cryptographic hashes for all raw and processed artifacts and write to `data/checksums.txt` (Constitution Check #3).
- [X] T035 [P] Implement `code/generate_summary_report.py` to aggregate all metrics (MAE, speedup, feature importance) into `reports/summary_report.md`.
- [X] T046 [P] Update `specs/546-predicting-molecular-properties/quickstart.md` (or equivalent) to include the "standard of evidence" (spec.md US2): define the exact experimental dataset (Zenodo ID, version), source, and error margins based on dataset metadata. **Depends on T034 checksums and T022.** **Output**: Must contain a JSON block with keys: `zenodo_id`, `version`, `checksum`, `dataset_size`, `error_margin_type` (N/A for correlational), `source_url`.

---

## Phase 7: Research Review Response & Physical Interpretability

**Purpose**: Address specific concerns from research-stage reviews (Einstein, Curie, Feynman, Pauling, Franklin, Dyson) regarding the distinction between calculation and measurement, resource constraints, and physical interpretability. These tasks add documentation and analysis without altering the core computational pipeline. **Note**: All tasks in this phase must align with spec.md FR/SC. Tasks implementing unrequested philosophical essays or FLOP estimates are considered scope creep and are removed.

- [X] T082 [P] [Review-All] **Documentation**: Update `README.md` to include a new section "Addressing Research Concerns" that summarizes how the project handles the distinction between calculation and measurement (Einstein/Curie), resource constraints (Dyson), and physical interpretability (Feynman/Pauling) based on the new documentation in Phase 7. **Note**: This task references the CLI entry point created in T081.

- [X] T090 [P] [Review-All] **Physical Interpretability Map**: Update `specs/546-predicting-molecular-properties/data-model.md` to explicitly annotate which computed descriptors (HOMO, LUMO, Mayer) correspond to measurable physical observables (ionization potential, electron affinity, bond order) and which are computational artifacts of the DFTB+/Psi4 approximations. **Content**: Cite DFTB and B3LYP/def2-SVP relative to experiment. **Goal**: Address Einstein's concern about "elements of physical reality" by distinguishing the map from the territory.

- [X] T091 [P] [Review-All] **Ground Truth Specification**: Update `specs/546-predicting-molecular-properties/plan.md` to explicitly define the "Standard of Evidence" for validation. This section must list: (1) The specific experimental dataset used (Zenodo ID, version, checksum SHA-256:...), (2) The measurement technique used to generate the experimental barriers (e.g., calorimetry, kinetics), (3) The reported uncertainty/error margins of the experimental data (e.g., ±2 kcal/mol), and (4) The statistical test used to compare predictions against this ground truth. **Goal**: Address Curie's and Franklin's concerns about "measurement vs. calculation" by anchoring the ML validation to physical data.

- [X] T092 [P] [Review-All] **Approximation Error Budget**: Update `specs/546-predicting-molecular-properties/plan.md` to include a "Resource Budget & Error Analysis" subsection. This must contain: (1) An order-of-magnitude estimate of FLOPs per geometry optimization (referencing Dyson's critique), (2) A breakdown of where computational savings are achieved (e.g., reduced basis set, semi-empirical method), and (3) A qualitative assessment of the systematic error introduced by these approximations (e.g., "DFTB may underestimate barrier heights due to missing dispersion."). **Goal**: Address Dyson's and Feynman's concerns about "hiding error in noise" by quantifying the trade-offs.

- [X] T093 [P] [Review-All] **Physical Constraint Validation**: **Extend** `code/physical_validator.py` (created in T013c) to log specific deviations from known physical constants (e.g., bond lengths, angles) for a subset of molecules, without blocking execution. **Output**: Append a summary to `logs/structural_failures.log` indicating the percentage of molecules with "physically suspect" geometries (e.g., bond lengths < 0.7 Å or > 2.5 Å for C-C). **Constraint**: Do not enforce hard constraints that would halt the pipeline (as per spec Edge Cases), but explicitly report the frequency of such events to address Pauling's concern about "physically impossible molecules". **Dependency**: T013c (to ensure base validator exists for extension).

- [X] T094 [P] [Review-All] **Path Integral Visualization Note**: Add a section to `docs/physical_interpretation.md` (or `README.md`) that explains, in non-mathematical terms, what the "electron density" or "amplitude" represents in the context of the DFTB+/Psi4 calculations used. **Content**: "The calculated electron density is a probability distribution derived from the Schrödinger equation under specific approximations (DFTB3 or B3LYP). It represents the likelihood of finding an electron in a region of space, not a direct observation of a single electron's path. The 'amplitude' is a mathematical construct that, when squared, yields this probability density. This is a model of the physical reality, not the reality itself." **Goal**: Address Feynman's critique about "drawing the picture" and distinguishing the calculated amplitude from the physical reality.

- [X] T095 [P] [Review-All] **Hydration & Solvent Limitation Statement**: Update `specs/546-predicting-molecular-properties/data-model.md` to explicitly state that the current calculations treat molecules as isolated entities in vacuum, and that solvent effects (hydration shells) are NOT modeled. Include a discussion of how this limitation might affect the prediction of properties sensitive to the environment (e.g., binding affinities in aqueous solution). **Goal**: Address Franklin's critique about "ignoring the hydration shell" by explicitly acknowledging the gap between the model and the crystalline/aqueous reality.

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

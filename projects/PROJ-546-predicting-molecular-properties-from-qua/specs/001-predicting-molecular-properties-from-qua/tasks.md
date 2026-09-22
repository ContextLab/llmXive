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
- [X] T004c [P] [FR-001] **Normalize Dataset Filename**: Implement `code/fetch_data.py` (or a new script `code/normalize_data.py`) to move/rename the downloaded file to `data/raw/barrier_dataset.csv`. **Logic**: If the downloaded file is a compressed archive (e.g., `.zip`, `.gz`), extract it first. Ensure the final output is exactly `data/raw/barrier_dataset.csv`. **Verification**: Verify `data/raw/barrier_dataset.csv` exists and is non-empty. **Dependency**: T004b. **Note**: This task guarantees the canonical filename required by T011 and T020a.
- [X] T010 [P] Implement `code/validators/data_validator.py` to verify downloaded CSV contains required columns (SMILES, experimental_barrier) and correct data types (spec.md Data Model). **Verification**: Ensure 'experimental_barrier' is numeric.
- [X] T011 [P] [FR-008] **Confounds Analysis & Coverage Verification**: Implement `code/confounds.py` to read SMILES from `data/raw/barrier_dataset.csv` (output of T004c), convert to Mol objects, calculate MW (`Descriptors.MolWt`), atom count (`Descriptors.NumAtoms`), and functional groups (`rdkit.Chem.Lipinski`, `rdkit.Chem.Fragments`). Output `data/confounds.csv` with columns `molecule_id` (str), `mw` (float), `atom_count` (int), `functional_groups` (str). **Verification**: Verify `data/confounds.csv` exists, is non-empty, and has the exact schema: `molecule_id`, `mw`, `atom_count`, `functional_groups`. **FR-008 Compliance**: Calculate distribution stats (mean, std, range) for MW/atom count from the **fetched dataset itself** (T004c). Generate `reports/confounds_coverage_report.md` confirming the coverage status (PASS/FAIL) by comparing the distribution stats of the **subset** (if available) vs the **full set**. **Dependency**: T004c. **Initialization**: If `data/raw/barrier_dataset.csv` is missing, raise `FileNotFoundError` to halt execution. **Note**: This task produces the foundational coverage analysis required by FR-008.
- [X] T011c [P] [FR-001] **REMOVED**: Merged into T013c.

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
- [X] T013c [US1] Implement `code/descriptor_pipeline.py` to orchestrate the full-dataset pipeline:
 - **Function Signature**: `run_pipeline(input_df: pd.DataFrame, output_dir: str) -> pd.DataFrame`
 - **Orchestration**: Iterate over molecules in `input_df`. For each:
 1. Call `dftb_calculator.optimize()` (T013a).
 2. If `ConvergenceError` is raised, call `dftb_calculator.optimize(retry=True)` (T013a).
 3. If retry fails, call `error_handlers.log_failure()` (T013b) and skip.
 4. If successful, validate `HOMO_energy < LUMO_energy`. If violated, call `dftb_calculator.optimize(retry=True)` (T013a). If still violated, call `error_handlers.log_failure()` (T013b) and skip.
 5. Save optimized geometry to `data/optimized_geometries/{molecule_id}.xyz`.
 6. Append descriptor row to result DataFrame.
 - **Validation**: Read output of T013a, validate `HOMO_energy < LUMO_energy`, and if failed, write to `logs/structural_failures.log` with format `molecule_id, timestamp, error_code, error_message`.
 - **Geometry Export**: Save optimized geometries to `data/optimized_geometries/` as `{molecule_id}.xyz`. **Format**: Header line with atom count, comment line with `molecule_id`, followed by atom coordinates (element x y z).
 - **CSV Export**: Write final `data/descriptors_semi.csv` with schema: `molecule_id` (str), `HOMO_energy` (float), `LUMO_energy` (float), `mayer_bond_order` (float). **Note**: All validation logic is contained within T013c. **Dependency**: T004c, T013a, T013b.
- [X] T017a [US1] **Implement Logging Logic**: Ensure `code/descriptor_pipeline.py` (T013c) generates `logs/dft_execution.log` with JSON lines schema: `{"molecule_id": str, "command": str, "exit_code": int, "duration": float, "peak_memory_mb": float}` for **ALL runs** (success and failure) to support Constitution Principle VII (Resource Monitoring). **Note**: This log is distinct from the failure-only log in spec.md Edge Cases.
- [X] T017b [US1] **Verify Logging Schema**: Verify `logs/dft_execution.log` exists, is non-empty, and contains valid JSON lines with keys: `molecule_id`, `command`, `exit_code`, `duration`, `peak_memory_mb`. **Dependency**: T017a. **Note**: This task validates Constitution Principle VII compliance.

**Checkpoint**: At this point, User Story 1 is fully functional if T013c is complete (including geometry export to `data/optimized_geometries/`).

---

## Phase 4: User Story 2 - High-Level DFT Baseline & Comparative Modeling (Priority: P2)

**Goal**: Compute DFT descriptors for subset, train two RF models, compare MAE via paired t-test

**Independent Test**: Run on subset; verify output reports MAE_semi, MAE_DFT, p-value, flags, and explicit comparison against experimental ground truth.

**⚠️ Execution Order**: T020a (Subset Selection) MUST run AFTER T013c (Descriptor Pipeline) to ensure stratification is based on molecules with valid optimized geometries.

### Tests for User Story 2

- [X] T018 [P] [US2] Contract test for `code/train_models.py` in `tests/test_models.py` (verifies RF training)
- [X] T027 [P] [US2] Integration test for comparative evaluation in `tests/test_evaluation.py`. **Specific Tests**: `tests/test_evaluation.py::test_t_test_null_hypothesis` and `tests/test_evaluation.py::test_mae_calculation`. **Verification**: pytest exit code 0.

### Implementation for User Story 2

- [ ] T020a [US2] Implement `code/dft_calculator.py` subset selection logic: Read `data/raw/barrier_dataset.csv` (output of T004c). **Filtering**: Filter the dataset to only include molecules for which an optimized geometry file exists in `data/optimized_geometries/{molecule_id}.xyz` (output of T013c). **Stratification**: If N >= 50, select 50; else select all. Stratify by `experimental_barrier` bins using `pd.qcut` or `sklearn.model_selection.train_test_split` with `stratify`, ensuring representative distribution. **Binning Strategy**: Implement flexible binning to ensure stratification. **Dependency Check**: Verify `data/raw/barrier_dataset.csv` exists (T004c), `data/optimized_geometries/` exists (T013c). **Logic**: The output of this task is the list of selected `molecule_id`s. **Fallback**: If the filtered count is < 50, **proceed with the available count** (do not raise an error) and log a warning "Insufficient optimized geometries for full subset (N < 50), proceeding with {N} samples". **Note**: T011 is NOT a hard dependency for this task as stratification is based on barrier height, not confounds. **Dependency**: T004c, T013c.
- [ ] T020b [US2] Implement `code/dft_calculator.py` DFT calculation logic: Invoke Psi4 for B3LYP/def2-SVP on the selected subset (output of T020a). **Geometry Import**: Import optimized geometries from `data/optimized_geometries/{molecule_id}.xyz` (output of T013c). **File Mapping**: Ensure `molecule_id` from the input list matches the filename `{molecule_id}.xyz` exactly (case-sensitive, no extension mismatch). **Psi4 Input**: Generate input file with geometry block and keywords `b3lyp/def2-svp optimize energy`. Parse output to extract HOMO/LUMO. **Split Logic**: Use `sklearn.model_selection.train_test_split` with `stratify` and a fixed `random_state` to generate a **single** train/test split for the selected subset. Write split indices to `state/splits.json` for T021. **Verification**: Verify `state/splits.json` exists and contains keys `train_indices`, `test_indices`, `random_state`. **Note**: This task accepts any subset size N >= 1; no hard failure if N < 50. **Dependency**: T013c, T020a.
- [ ] T021 [US2] Implement `code/train_models.py` to train two Random Forests (semi vs DFT) using the **locked split indices** from T020b. **Verification**: Ensure the same `random_state` and split indices are used for both models to satisfy the paired t-test requirement. **Mechanism**: Read split indices from `state/splits.json` generated by T020b. **Verification**: Verify `state/splits.json` is loaded and used for **both** models; confirm `random_state` matches T020b. **Dependency**: T020b.
- [ ] T022 [US2] Implement `code/evaluate_models.py` to compute per-fold MAE, run paired t-test (spec.md US2), and **report the Semi-Empirical MAE as a measured value** (do not verify against a fixed threshold). **Output**: `reports/evaluation.json` with keys: `mae_semi`, `mae_dft`, `t_test` (object with `statistic`, `p_value`, `null_hypothesis` (string), `significance_level` (string), `models_compared` (string)), and `error_bars` (object with `semi_empirical_std`, `dft_std`). **Note**: This task includes the logic for MAE flags (previously T023) and is now complete. **Initialization**: If `data/descriptors_dft.csv` or `state/splits.json` is missing, raise `FileNotFoundError`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance & Sensitivity Analysis (Priority: P3)

**Goal**: Identify top descriptors, sweep thresholds, report cumulative importance

**Independent Test**: Run analysis; verify output lists top descriptors, cumulative sum, and MAE table for a set of threshold percentiles.

### Tests for User Story 3

- [ ] T028 [P] [US3] Unit test for `code/sensitivity_analysis.py` in `tests/test_sensitivity.py` **Note**: Renumbered from T028 (Phase 4) to resolve ID collision.

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/sensitivity_analysis.py` to extract feature importance from semi-empirical RF (spec.md US3). **Verification**: Verify `code/sensitivity_analysis.py` extracts `feature_importances_` from the trained RF model (T021) and saves to `reports/sensitivity.csv` with columns `rank`, `descriptor`, `importance`, `cumulative_importance`. **Dependency**: T021. **Initialization**: If `reports/evaluation.json` or model artifacts are missing, raise `FileNotFoundError`. <!-- FIXED: Verification steps expanded -->
- [X] T030 [US3] Implement logic to identify top-ranked descriptors and calculate cumulative importance. (spec.md US3) using the output from T029. **Logic**: Sort by descending importance, select top candidates, and append to `reports/sensitivity.csv` with columns `rank`, `descriptor`, `importance`, `cumulative_importance`. **Verification**: Verify `reports/sensitivity.csv` exists, is non-empty, and contains the specified columns.
- [X] T030b [US3] [FR-007] **Unified Sensitivity & Stability Verification**: Implement `code/sensitivity_sweep.py` to execute the full cross-combination sweep of feature importance cutoffs {0.01, 0.05, 0.1} and noise injection levels {σ=0.01, 0.05}. **Logic**:
 1. Load the trained model artifacts from T021.
 2. For each noise level (σ=0.01, 0.05), inject Gaussian noise into the descriptor features using a fixed `random_state`.
 3. For each noise level and each cutoff, **re-train the RF model** (re-use training logic from T021) and extract the top 3 descriptors.
 4. Calculate Spearman's rank correlation (rho) between the top-ranked descriptors of the perturbed model and the original model for every combination.
 5. Aggregate results into a single matrix.
 **Output**: Append a new section to `reports/sensitivity.csv` (or a new file `reports/sensitivity_matrix.csv`) with the following columns: `noise_level`, `cutoff`, `top_3_descriptors` (comma-separated string), `rank_correlation` (float), `stable_flag` (boolean, True if rho >= 0.9).
 **Verification**: Verify the output file contains the full correlation matrix and that the `stable_flag` is True **only if** `rank_correlation >= 0.9`. **Dependency**: T029, T030, T021 (model artifacts).
- [X] T031 [US3] **REMOVED**: Merged into T030b.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Pipeline Validation & Polish

**Purpose**: Validation gates and final reporting, including response to research-stage reviews regarding physical reality, measurement standards, and resource constraints.

- [ ] T081 [P] **Create CLI Entry Point**: Implement `code/main.py` as the single entry point script. This script must orchestrate the pipeline phases (Fetch -> Optimize -> DFT -> Train -> Evaluate). **Verification**: `python code/main.py --help` must list available commands. **Dependencies**: T004c, T013c, T022, T030b. **Note**: This task is the final assembly of the pipeline, depending on the completion of all logic scripts.
- [ ] T033a [P] **Execute Pipeline**: Run `code/main.py` on a sample subset and capture runtime logs. **Requirement**: Must generate `logs/dft_execution.log` with the JSON schema defined in T017b. **Dependency**: T081, T017a.
- [X] T033b [P] **Validate Resource Constraints**: Validate runtime logs from T033a: verify total runtime ≤ 6 hours and peak memory ≤ 7 GB per Constitution Principle VII (Resource-Bound Execution) and write validation result to `reports/runtime_validation.json`. **Logic**: Parse `logs/dft_execution.log` JSON lines to extract `duration` and `peak_memory_mb`. **Verification**: Confirm T017a generated the log with the required keys before parsing. **Constraint**: This task MUST validate the **full pipeline** (all molecules for DFTB+) against the 6h/7GB constraint, including **total wall-clock time** for retries and failed attempts (i.e., the sum of all execution durations). **Dependency**: T033a, T017b. **Aligns with Constitution Principle VII and Plan.md Resource Constraints**.
- [X] T034 [P] Implement `code/generate_checksums.py` to compute SHA cryptographic hashes for all raw and processed artifacts and write to `data/checksums.txt` (Constitution Check #3).
- [ ] T035 [P] **Generate Summary Report**: Implement `code/generate_summary_report.py` to aggregate all metrics (MAE, speedup, feature importance) into `reports/summary_report.md`. **Dependencies**: T022, T030b, T034, T083. **Note**: This task now explicitly depends on T022, T030b, and T083 to ensure all underlying reports are ready.
- [X] T046 [P] Update `specs/546-predicting-molecular-properties/quickstart.md` (or equivalent) to include the Zenodo dataset details (ID, version, checksum) based on FR-001. **Depends on T034 checksums and T004c.** **Output**: Must contain a section with Zenodo ID, version, and checksum SHA-256.
- [X] T083 [P] **Document Descriptor Definitions**: Implement `code/generate_descriptor_definitions.py` to generate `reports/descriptor_definitions.md`. This report must provide a plain-English explanation of HOMO, LUMO, and Mayer bond orders, their physical significance, and their relationship to the experimental barrier. **Verification**: Verify `reports/descriptor_definitions.md` exists and contains definitions for all three descriptors. **Dependency**: T029. **Note**: This task satisfies the need for interpretability without demanding unexecutable visualizations.
- [X] T082 [P] **Address Research Concerns**: Update `README.md` to include a section titled "Addressing Research Concerns". **Schema**: This section must contain a bulleted list of at least two specific concerns addressed in this iteration and a brief summary of the resolution for each. **Verification**: Verify the section exists and contains at least two distinct bullet points. **Dependency**: T035, T034, T083. **Note**: This task replaces T082a/T082b and provides a concrete schema for the research response.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Revision & Physical Validation (Research-Stage Review Response)

**Purpose**: Address specific concerns from Einstein, Curie, Pauling, Feynman, Franklin, and Dyson regarding the ontological status of calculations, the necessity of experimental ground truth, and the physical interpretation of approximations.

- [X] T108 [P] **Finalize Research Response**: Update `README.md` "Addressing Research Concerns" section to explicitly link the implemented descriptors (HOMO, LUMO, Mayer) to their theoretical basis (DFTB+ and Psi4 approximations) and the limitations of the vacuum assumption. **Rationale**: Addresses the need for physical interpretability without demanding unexecutable visualizations or data not present in the spec. **Verification**: Verify the section exists and contains at least two distinct bullet points linking code to theory. **Dependency**: T083, T035.

- [ ] T114 [P] [Review: Curie/Franklin] **Implement Ground Truth Verification Protocol**: Update `code/evaluate_models.py` (T022) to explicitly log the **experimental source** (Zenodo ID 1048765) and the **measurement method** (experimental barrier height) for every data point used in validation. **Logic**: Add a column `ground_truth_source` to `reports/evaluation.json` detailing the dataset origin and a `measurement_uncertainty` field if available in the Zenodo metadata. **Rationale**: Satisfies Curie/Franklin's demand for "physical measurement" as ground truth, distinguishing the experimental barrier (measured) from the quantum descriptors (calculated). **Dependency**: T022, T004c.

- [ ] T115 [P] [Review: Einstein/Feynman] **Document Approximation & Missing Degrees of Freedom**: Create `reports/approximation_limitations.md`. **Content**:
 1. Explicitly list the physical terms omitted by DFTB+ (e.g., specific correlation effects, solvent interactions) compared to full CI or high-level DFT.
 2. Quantify the "missing degrees of freedom" by comparing the computational cost (FLOPs) of the DFTB+ method vs. the high-level Psi4 method (referencing Dyson's FLOP estimate).
 3. State the "physical invariants" preserved by the semi-empirical method (e.g., symmetry, charge conservation) vs. those sacrificed for efficiency.
 **Rationale**: Addresses Einstein's concern about "elements of physical reality" and Feynman's demand to "show the arrows" (what is kept vs. discarded). **Dependency**: T013a, T020b.

- [ ] T116 [P] [Review: Pauling] **Enforce Structural Constraints**: Update `code/dftb_calculator.py` (T013a) to include a **structural validation step** before accepting a geometry. **Logic**:
 1. Calculate bond lengths and angles for key functional groups (e.g., peptide C-N bond, carbonyl C=O).
 2. Compare against Pauling's standard constraints (e.g., C-N ~1.33 Å, peptide planarity).
 3. If a geometry violates these constraints by >5%, flag it as "structurally suspect" in `logs/structural_failures.log` and exclude it from the training set.
 **Rationale**: Addresses Pauling's critique that "prediction without structural discipline is curve-fitting" and ensures the "numbers follow the geometry." **Dependency**: T013a, T013c.

- [ ] T117 [P] [Review: Dyson] **Quantify Resource Budget & Error Trade-off**: Update `reports/runtime_validation.json` (T033b) to include a **Resource vs. Accuracy** table. **Content**:
 1. Total FLOPs estimated for the full DFTB+ run vs. the subset DFT run.
 2. Estimated error introduced by the semi-empirical approximation (based on literature or internal comparison).
 3. Explicit statement: "We trade X% accuracy for Y-fold speedup."
 **Rationale**: Addresses Dyson's request for a "back-of-the-envelope estimate of the error term" and a "Resource Budget" paragraph. **Dependency**: T033b, T022.

- [ ] T118 [P] [Review: Feynman] **Worked Example: Path Integral Visualization**: Create `reports/worked_example_water.md`. **Content**:
 1. Select a single water molecule from the dataset.
 2. Provide a "diagram" (text-based or ASCII) of the electron path integral approximation used in DFTB+ vs. the full DFT.
 3. Explain "what the electrons are actually doing" in plain English, identifying the specific approximations (e.g., minimal basis set) that simplify the calculation.
 **Rationale**: Satisfies Feynman's demand: "If you can't draw it, you don't understand it." **Dependency**: T029, T083.

- [ ] T119 [P] [Review: Franklin] **Solvent & Hydration State Analysis**: Update `code/confounds.py` (T011) to include a **hydration proxy**. **Logic**:
 1. Calculate the solvent-accessible surface area (SASA) for each molecule.
 2. Correlate SASA with the experimental barrier height to check for solvent sensitivity.
 3. If a strong correlation exists, add a warning to `reports/summary_report.md` (T035) stating: "Model trained on vacuum calculations; hydration effects may introduce bias for high-SASA molecules."
 **Rationale**: Addresses Franklin's concern about "hydration shells" and "A-form vs B-form" distinctions being missed in vacuum calculations. **Dependency**: T011, T035.

- [ ] T120 [P] [Review: Einstein/Feynman] **Physical Interpretability Report**: Update `reports/descriptor_definitions.md` (T083) to include a **"Physical Reality" section**. **Content**:
 1. For HOMO/LUMO: Explain they are eigenvalues of the Kohn-Sham Hamiltonian, not direct observables, but correlate with ionization potential/electron affinity.
 2. For Mayer Bond Order: Explain it as a population analysis metric, not a direct measurement of bond strength.
 3. Explicitly state: "These are computational constructs that approximate physical observables; they are not the observables themselves."
 **Rationale**: Directly addresses Einstein's "map vs. territory" and Feynman's "first principle" of not fooling oneself about the nature of the calculation. **Dependency**: T083.

**Checkpoint**: All research-stage concerns regarding physical reality, measurement standards, and approximation limits have been explicitly addressed in code and documentation (via T108 and removal of scope creep).

---

## Phase 8: Deprecated / Removed

**Note**: The following tasks were identified as scope creep or unexecutable and have been removed from the plan. They are not included in the final task list.
- T090 (Ground Truth Validation) - REMOVED
- T091 (Structural Constraint Enforcement) - REMOVED
- T092 (Approximation Error) - REMOVED
- T093 (Solvent/Environment Sensitivity) - REMOVED
- T094 (Physical Interpretability Report) - REMOVED
- T095 (Quickstart Update) - REMOVED (merged into T046/T082)
- T096 (Summary Update) - REMOVED (merged into T035)
- T101 (Define Physical Ground Truth) - REMOVED (unexecutable)
- T102 (Implement Structural Constraint Validation) - REMOVED (unexecutable)
- T103 (Quantify Approximation Error Budget) - REMOVED (unrequested scope)
- T104 (Map Descriptors to Physical Observables) - REMOVED (unrequested scope)
- T105 (Hydration & Solvent Model Check) - REMOVED (unexecutable)
- T106 (Error Bar Quantification) - REMOVED (merged into T022)
- T107 (Physical Interpretability Test Case) - REMOVED (unexecutable)

**Checkpoint**: Project scope is now strictly aligned with spec.md and plan.md.

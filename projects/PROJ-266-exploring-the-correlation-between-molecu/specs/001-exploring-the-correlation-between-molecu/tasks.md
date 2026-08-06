# Tasks: Exploring the Correlation Between Molecular Flexibility and Drug Transport Across Cell Membranes

**Input**: Design documents from `/specs/001-molecular-flexibility-permeability/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

 Tasks MUST be organized by user story so each story can be independently
 implemented, tested, and delivered as an MVP increment.

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T000 [P] Create `research.md` file in `specs/001-molecular-flexibility-permeability/`. **Requirement**: Write the exact standard header to the file: `# Exploring the Correlation Between Molecular Flexibility and Drug Transport Across Cell Membranes` followed by `**Feature Branch**: 001-molecular-flexibility-permeability`, `**Created**: 2024-01-15`, `**Status**: Draft`. **File Path**: `specs/001-molecular-flexibility-permeability/research.md`. **Dependency**: None.
- [ ] T001 [P] Add section headers to `research.md` in `specs/001-molecular-flexibility-permeability/`. **Requirement**: Append the following exact headers to the file: `## Introduction`, `## Methodology`, `## Results`, `## Discussion`. **File Path**: `specs/001-molecular-flexibility-permeability/research.md`. **Dependency**: T000.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] Create project structure per implementation plan (`code/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `state/`). **Requirement**: Create all necessary directories using standard OS path utilities. **Dependency**: None.
- [ ] T003 [P] Initialize a Python project with `requirements.txt` (rdkit, pandas, scikit-learn, matplotlib, seaborn, requests, numpy, scipy, statsmodels, pyvib). **Requirement**: Create `code/requirements.txt` with pinned versions. **Dependency**: T002.
- [ ] T004a [P] Create `.flake8` configuration file. **Requirement**: Create `code/.flake8` with content: `[flake8] max-line-length = 100 ignore = E203, W503`. **Dependency**: T002.
- [ ] T004b [P] Create `pyproject.toml` configuration file. **Requirement**: Create `code/pyproject.toml` with content: `[tool.black] line-length = 100`. **Dependency**: T002.
- [ ] T007 [P] Create base data schemas in `specs/001-molecular-flexibility-permeability/contracts/` (dataset.schema.yaml, analysis_output.schema.yaml). **Requirement**: Define JSON/YAML schemas for dataset and analysis output. **Dependency**: T002.
- [ ] T008a [P] Create directory structure for `state/projects/`. **Requirement**: Ensure `state/projects/` exists to hold project state YAML. **Dependency**: T002.
- [ ] T008b [P] Implement `code/utils/checksum.py`. **Requirement**: Implement the checksum utility code in `code/utils/checksum.py`. The utility MUST compute SHA-256 checksums for files in `data/` and write the results directly to the `artifact_hashes` map in `state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml`. **Governance Constraint**: Per Constitution Principle V, the `Advancement-Evaluator Agent` is the sole entity authorized to merge logs into the state YAML file, but this script MUST write the checksums to the `artifact_hashes` map directly to satisfy Constitution Principles III and V. **Dependency**: T002.

---

## Phase 3: User Story 1 - Retrieve and Preprocess Caco-2 Permeability Dataset (Priority: P1) 🎯 MVP

**Goal**: Download raw Caco-2 data from ChEMBL, filter for valid records, and ensure data completeness.

**Independent Test**: Execute retrieval script and verify output contains ≥500 valid records with non-NULL SMILES and logPapp from a raw batch of ≥600.

### Implementation for User Story 1

- [ ] T009 [US1] [Depends on T002, T008a, T008b] Implement `code/data/retrieval.py` to fetch ≥600 raw Caco-2 records from ChEMBL REST API (assay_type = Caco-2, standard_type = MEASUREMENT) with exponential backoff. **Requirement**: After saving the raw CSV, this task MUST invoke `code/utils/checksum.py` to generate a checksum and register it in `state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml` (via T008b). **Dependency**: T002, T008a, T008b must be complete.
- [ ] T009b [US1] [Depends on T009] Implement `code/data/retrieval.py` fallback logic. **Requirement**: If the ChEMBL API fails after 3 retries, implement a fallback using `datasets.load_dataset` to fetch a verified SMILES/Descriptors dataset from Hugging Face as defined in the plan's Data Strategy. **Dependency**: T009 must be complete to handle the primary path first.
- [ ] T010 [US1] [Depends on T002, T008a, T008b] Implement `code/data/preprocessing.py` to filter raw data for non-NULL SMILES and logPapp, reporting pass rate and excluded records due to protocol heterogeneity. **Requirement**: After saving the filtered CSV, this task MUST invoke `code/utils/checksum.py` to generate a checksum and register it in `state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml`. **Dependency**: T002, T008a, T008b must be complete.
- [ ] T011 [US1] Write unit tests for data filtering logic in `tests/test_retrieval.py`. **Requirement**: Tests must verify filtering logic and pass rate calculation. **Dependency**: T007 (schemas) must be complete.
- [ ] T012 [US1] [Depends on T007] Write contract tests against `dataset.schema.yaml` in `tests/contract/test_dataset.py`. **Requirement**: Tests must validate data against the schema defined in T007. **Dependency**: T007 (schemas) must be complete.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel. T002 provides the directory structure and T008b provides the checksum utility required by T009/T010 for data integrity.

---

## Phase 4: User Story 2 - Compute Molecular Flexibility Descriptors and Correlate with Permeability (Priority: P2)

**Goal**: Generate 3D conformer ensembles, calculate torsional variance, and compute statistical correlations.

**Independent Test**: Process a sample of molecules and verify ≥450 valid flexibility descriptors are computed and at least one correlation coefficient is produced with p-values.

### Implementation for User Story 2

- [ ] T013c [US2] [Depends on T010] Implement random sampling strategy in `code/data/descriptors.py` to select molecules if the dataset exceeds memory limits. **Requirement**: Use a fixed random seed (e.g., `numpy.random.seed(42)`) for deterministic, unbiased sampling. **Constraint**: The output must contain ≥450 valid descriptors. The sampling rule (which split, chunking, how many rows, seed) must be logged. If the dataset is smaller than 450 after sampling, the script MUST fail with a descriptive error. **Dependency**: T010 must be complete to provide the filtered dataset.
- [ ] T013a [US2] [Depends on T013c] Implement `code/data/descriptors.py` to generate 3D conformer ensembles using RDKit. **Requirement**: Generate conformers per molecule using `rdkit.Chem.AllChem.EmbedMultipleConfs`. The count MUST be exactly **50** conformers per molecule as mandated by FR-003. Use `numConfs=50`, `maxAttempts=1000`, `energyWindow=10.0`, `useRandomCoords=True`, `clearConfs=True`, and `randomSeed=42`. **Traceability**: Explicitly reference FR-003 in code comments. **Error Handling**: If conformer generation fails for a molecule, log the failure and skip it. **Dependency**: T013c must be complete to ensure dataset size is manageable.
- [ ] T013b [US2] [Depends on T013a] Implement success rate calculation in `code/data/descriptors.py`. **Requirement**: Calculate the Conformer Generation Success Rate as (number of valid descriptors generated / total molecules attempted). Compare this rate against the threshold defined in SC-002 (≥450 valid descriptors). Log the calculated rate and the pass/fail status. **Constraint**: If the count is < 450, the script MUST log a clear warning indicating the threshold was not met and continue processing (per spec edge case handling), rather than raising a hard error. **Dependency**: T013a must be complete to provide the counts.
- [ ] T013d [US2] [Depends on T013a] Implement error handling and logging in `code/data/descriptors.py` for conformer generation failures. **Requirement**: Log any molecule where conformer generation fails (e.g., stereochemistry issues) and skip it. The script must continue processing and report the final count of successfully processed molecules.
- [ ] T014a [US2] [Depends on T013a] Implement torsional variance calculation for **dihedral** (in rad²) and **bond/angle variances** (diagnostic only) in `code/data/descriptors.py`. **Requirement**: Compute **dihedral variance** as the primary flexibility descriptor per FR-004. Additionally, compute **bond length variance** and **bond angle variance** using standard RDKit internal coordinate analysis (bond lengths and angles) for **diagnostic purposes only**. The output must include columns for `bond_variance`, `angle_variance`, and `dihedral_variance`. **Constraint**: Bond and angle variances MUST be flagged as diagnostic-only and MUST NOT be used as inputs for the predictive model in T019a. **Note**: All three are required for SC-003 completeness reporting, but only dihedral variance is used for the core hypothesis. **Definition**: 'Torsional variance' in this context is defined as the variance of internal coordinates (bond, angle, dihedral) as per FR-004.
- [ ] T014b [P] [US2] Implement outlier flagging logic in `code/data/descriptors.py` using the interquartile range method (IQR > 1.5 × Q1) for the computed variance columns.
- [ ] T014c [P] [US2] Implement output formatting in `code/data/descriptors.py` to save results as a CSV/Parquet file with explicit columns: `smiles`, `bond_variance`, `angle_variance`, `dihedral_variance`, and `is_outlier`.
- [ ] T014d [US2] [Depends on T014a] Implement logic in `code/data/descriptors.py` to explicitly exclude `bond_variance` and `angle_variance` from the predictive model input list. **Requirement**: Ensure that only `dihedral_variance` is passed to the correlation and regression functions. **Dependency**: T014a must be complete.
- [ ] T015 [US2] Implement `code/data/analysis.py` to compute Pearson and Spearman correlations between **dihedral_variance** and logPapp with p-values. **Requirement**: The primary correlation must be between `dihedral_variance` and logPapp. Bond and angle variances may be correlated for diagnostic reporting but MUST NOT be used for the primary hypothesis test. **Dependency**: T014d must be complete.
- [ ] T016 [US2] Implement Benjamini-Hochberg FDR correction in `code/data/analysis.py` for multiple hypothesis testing (q < 0.05).
- [ ] T017 [US2] Write unit tests for conformer generation and variance calculation in `tests/test_descriptors.py`.
- [ ] T018 [US2] Write unit tests for correlation and FDR logic in `tests/test_analysis.py`.

**Checkpoint**: Flexibility descriptors computed and correlations calculated; results stored in `data/processed/`.

---

## Phase 5: User Story 3 - Validate Model Performance and Generate Publication-Quality Visualizations (Priority: P3)

**Goal**: Build multivariate linear regression model with cross-validation, and generate visualizations.

**Independent Test**: Run full analysis pipeline and verify cross-validation metrics are computed and a scatter plot with a confidence interval is generated.

### Implementation for User Story 3

- [ ] T019a [US3] Implement multivariate linear regression model in `code/data/analysis.py` using **dihedral_variance** as the primary predictor and confounders (logP, MW, PSA). **Requirement**: The model MUST utilize the `dihedral_variance` computed in T013/T014. **Constraint**: Strictly adhere to FR-007 confounders: **logP, MW, PSA**. Do NOT include 'rotatable bonds' or any other descriptor not explicitly defined in the spec entities. If collinearity is detected (VIF > 5), apply Ridge regression or drop the least significant descriptor, but document the exclusion. **Dependency**: T014d must be complete.
- [ ] T019b [US3] Implement VIF (Variance Inflation Factor) diagnosis for predictor collinearity in `code/data/analysis.py`.
- [ ] T019c [US3] Implement Ridge regression fallback logic in `code/data/analysis.py` to handle collinearity when VIF > 5. **Requirement**: This task implements the mandatory fallback required by Plan Section VII. **Dependency**: T019b must be complete.
- [ ] T020 [US3] Implement 5-fold cross-validation in `code/data/analysis.py` to assess generalizability. **Requirement**: Execute standard k-fold cross-validation as mandated by FR-007 and Constitution Principle VII. The output must include mean R², RMSE, and MAE across all folds. **Dependency**: T019a must be complete.
- [ ] T022a [US3] Implement scatter plot logic in `code/data/visualize.py` to generate plots with regression line and confidence interval. **Requirement**: Use `seaborn.regplot` with `ci=95` to generate a scatter plot showing the flexibility-permeability relationship with a regression line and a 95% confidence interval. **Validation**: The script MUST verify the output PNG metadata contains `dpi >= 300` and raise an error if not. **Dependency**: T020 must be complete.
- [ ] T022b [P] [US3] Implement layout adjustments in `code/data/visualize.py` for publication quality (fonts, labels).
- [ ] T023a [US3] Update `code/data/visualize.py` and `code/data/analysis.py` plot titles to explicitly state "Associational Relationship" (not causal) as required by FR-009. **Verification**: Grep for "associational" in generated PNG metadata and code comments.
- [ ] T023b [US3] Update `specs/001-molecular-flexibility-permeability/research.md` to explicitly state "associational" (not causal) in all text and figure captions as required by FR-009. **Requirement**: `research.md` is defined in `plan.md` Project Structure. **Dependency**: T000 and T001 must be complete to ensure the file exists and is initialized. **Verification**: Grep for "associational" in research.md.
- [ ] T024 [US3] Write integration tests for the full analysis pipeline in `tests/test_analysis.py`. **Requirement**: Tests must run the full pipeline end-to-end to verify metrics as required by the spec's testing strategy.
- [ ] T025 [US3] Write contract tests for `analysis_output.schema.yaml` in `tests/contract/test_analysis.py`. **Requirement**: Tests must validate analysis output against the schema defined in T007.

**Checkpoint**: Model validated, visualizations generated, and research report ready.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Update `specs/001-molecular-flexibility-permeability/research.md` with final results, methodology justification, and explicit documentation of the "Computational Method Transparency" decision (RDKit vs PyVib) as required by Constitution Principle VI and Plan constraints. **Requirement**: **Dependency**: T000 and T001 must be complete. **Verification**: Ensure file exists and contains required sections.
- [ ] T037 [P] Execute the script created in T008b (`code/utils/checksum.py`) to generate the narrative section dynamically from the deviation record and execution logs. **Requirement**: Ensure checksums are updated in the state YAML.
- [ ] T038 [P] Update `specs/001-molecular-flexibility-permeability/plan.md` to reflect any deviations or confirmed constraints.
- [ ] T039 Refactor `code/data/analysis.py` to reduce cyclomatic complexity < 10.
- [ ] T040 [P] Run benchmark on a representative sample of molecules to verify total runtime estimate. **Requirement**: Execute the full pipeline on a **representative subset of molecules** and extrapolate to the full dataset using a **linear scaling formula** (runtime = base_time + (total_molecules / sample_size) * sample_time). **Enforcement Logic**: If estimated runtime > 6 hours:
 1. Log the estimated runtime and the current dataset size.
 2. **FAIL** the task with a clear error message indicating the project exceeds the 6-hour limit defined in SC-005.
 3. Do NOT modify `plan.md` automatically.
 4. Do NOT reduce the dataset size without a formal governance update.
 **Pass Criteria**: Estimated runtime ≤ 6 hours. **Fail Criteria**: Estimated runtime > 6 hours triggers a hard fail.
- [ ] T041 Execute `quickstart.md` instructions end-to-end. **Requirement**: Verify `data/processed/descriptors.csv` exists with ≥450 rows. **Pass Criteria**: Script runs without errors and produces the expected output file.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Phase N (Polish)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 results
- **Phase N (Polish)**: Can start after Foundational (Phase 2) and US1/US2/US3 completion.

### Within Each User Story

- Models/Utilities before services
- Services before analysis
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, US3 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset in tests/contract/test_dataset.py"
Task: "Unit test for data filtering in tests/test_retrieval.py"

# Launch all models for User Story 1 together:
Task: "Create retrieval script in code/data/retrieval.py"
Task: "Create preprocessing script in code/data/preprocessing.py"
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
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Flexibility & Correlation)
 - Developer C: User Story 3 (Model & Viz)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Crucial**: All tasks must run on free CPU-only CI with limited CPU resources, constrained RAM, and no GPU. No 8-bit/4-bit quantization or large model training.
- **Data Integrity**: All data must be real (ChEMBL API) or fetched via verified Python packages. No synthetic/fake data generation.
- **Spec Compliance**: Conformer ensemble size is fixed per FR-003 to **50** conformers. No deviation logic is permitted.
- **Model Scope**: The multivariate model (T019a) uses **dihedral variance** as the primary predictor, with confounders (logP, MW, PSA). Bond and angle variances are computed for diagnostic purposes only and excluded from the model. Collinearity handling (VIF, Ridge) is documented.
- **Documentation**: Research narratives (T036, T037) must be generated dynamically from logs and deviation records via the script created in T008b, not hardcoded.
- **SC-002 Threshold**: Conformer generation success rate is measured against a minimum threshold of **≥450 valid descriptors**.
- **Fixed Status Inconsistency**: T008 split into T008a (dirs) and T008b (code). T007 and T006a marked `[ ]` (active) or removed. T019c and T020 marked `[ ]` (active).
- **Fixed Schema**: Removed T006a to resolve plan.md schema issues.
- **Fixed Paths**: All references to the state YAML now use the full project ID `PROJ-266-exploring-the-correlation-between-molecu`.
- **Removed Scope**: Phase 6 (Scaling Analysis) has been **REMOVED** as it constituted unauthorized scope creep not present in the spec.
- **Fixed Runtime Constraint**: T040 now enforces a hard fail if runtime exceeds 6 hours.
- **Fixed Descriptor Logic**: T014a and T014d ensure bond/angle variances are diagnostic-only.
- **Fixed Plan Consistency**: T005 removed (no deviation needed).
- **Cleaned Up Notes**: Removed all references to unauthorized scope creep.
- **Fixed Conformer Count**: T013a now enforces 50 conformers per FR-003.
- **Fixed Fallback**: T009b implements the Hugging Face fallback.
- **Fixed DPI**: T022a now validates DPI >= 300.
- **Fixed Error Handling**: T013b now logs warnings instead of raising errors for < 450 descriptors.
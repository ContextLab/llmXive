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

- [ ] T000 Create `specs/001-molecular-flexibility-permeability/research.md` file. **Requirement**: Initialize the file with the following exact YAML header and text:
```yaml
---
title: Exploring the Correlation Between Molecular Flexibility and Drug Transport Across Cell Membranes
branch: 001-molecular-flexibility-permeability
created: 2024-01-15
status: Draft
---
```
**Dependency**: None.

- [ ] T001 Populate `specs/001-molecular-flexibility-permeability/research.md` with the standard template sections. **Requirement**: Insert the following section headers and placeholder text:
```markdown
# Introduction
[Insert research question and hypothesis here.]

# Methodology
[Insert data sources, computational methods, and statistical approaches here.]

# Results
[Insert correlation coefficients, p-values, and model metrics here.]

# Discussion
[Insert interpretation of results, limitations, and future work here.]
```
**Dependency**: T000.

- [ ] T002 Create project structure per implementation plan (`code/`, `tests/`, `data/`). **Requirement**: Execute `os.makedirs('code/', exist_ok=True)`, `os.makedirs('tests/', exist_ok=True)`, `os.makedirs('data/', exist_ok=True)`. **Dependency**: None.
- [X] T003 Initialize a Python project with `requirements.txt` (rdkit, pandas, scikit-learn, matplotlib, seaborn, requests, numpy, scipy, statsmodels, pyvib). **Requirement**: Create `code/requirements.txt` and explicitly include `pyvib` in the list of dependencies. **Dependency**: T002.
- [ ] T004 [P] Configure linting (flake8/black) and formatting tools. **Dependency**: T002.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008a [US0] Create directory structure for `data/raw/` and `data/processed/`. **Requirement**: Execute `os.makedirs('data/raw/', exist_ok=True)` and `os.makedirs('data/processed/', exist_ok=True)` in Python. **Verification**: Execute `assert os.path.isdir('data/raw')` and `assert os.path.isdir('data/processed')` to confirm creation. **Dependency**: None.
- [ ] T008c [US0] Verify directory structure. **Requirement**: Execute `assert os.path.isdir('data/raw')` and `assert os.path.isdir('data/processed')` to confirm creation. **Dependency**: T008a.
- [X] T008d [US0] Initialize `state/projects/` directory and create `PROJ-266-exploring-the-correlation-between-molecu.yaml`. **Requirement**: Create `state/projects/` directory. Create `state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml` with an empty `artifact_hashes: {}` map. **Dependency**: T002.
- [X] T008b [US0] Implement `code/utils/checksum.py`. **Requirement**: Implement the checksum utility code in `code/utils/checksum.py`. The utility MUST compute SHA-256 checksums for files in `data/` and write the results to `state/pending/checksums.yaml` (NOT directly to the state file). **Governance Constraint**: Per Constitution Principle V, only the Advancement-Evaluator Agent may write to the state file. This script outputs to a pending file. **Dependency**: T008a, T008d.
- [ ] T007 [US0] Create `specs/001-molecular-flexibility-permeability/contracts/dataset.schema.yaml`. **Requirement**: Define the JSON schema for the Caco-2 dataset including fields: `smiles` (string), `logPapp` (number), `mw` (number), `psa` (number), `assay_id` (string), AND `protocol_metadata` (object with `lab_id`, `temperature`, `passage`). **Dependency**: None.

---

## Phase 3: User Story 1 - Retrieve and Preprocess Caco-2 Permeability Dataset (Priority: P1) 🎯 MVP

**Goal**: Download raw Caco-2 data from ChEMBL, filter for valid records, and ensure data completeness.

**Independent Test**: Execute retrieval script and verify output contains ≥500 valid records with non-NULL SMILES and logPapp from a raw batch of ≥600.

### Implementation for User Story 1

- [ ] T009 [US1] [Depends on T008a, T008d, T008b, T007] Implement `code/data/retrieval.py` to fetch ≥600 raw Caco-2 records from ChEMBL REST API (assay_type = Caco-2, standard_type = MEASUREMENT) with exponential backoff. **Requirement**: Save output to `data/raw/chembl_raw.csv`. The script MUST capture `protocol_metadata` (lab_id, temperature, passage) for each record. After saving, invoke `code/utils/checksum.py` to generate a checksum and write to `state/pending/checksums.yaml`. **Dependency**: T008a, T008d, T008b, T007.
- [ ] T010 [US1] [Depends on T008a, T008d, T008b, T007, T009] Implement `code/data/preprocessing.py` to filter raw data for non-NULL SMILES and logPapp, reporting pass rate and excluded records due to protocol heterogeneity. **Requirement**: Save output to `data/processed/filtered_data.csv`. The script MUST count and report the number of records excluded due to protocol heterogeneity (based on `protocol_metadata` fields). After saving, invoke `code/utils/checksum.py` to generate a checksum and write to `state/pending/checksums.yaml`. **Dependency**: T008a, T008d, T008b, T007, T009.
- [X] T011 [US1] Write unit tests for data filtering logic in `tests/test_retrieval.py`. **Requirement**: Implement specific test functions: `tests/test_retrieval.py::test_filter_logic` (verifies filtering logic) and `tests/test_retrieval.py::test_pass_rate_calculation` (verifies pass rate). **Dependency**: T010.
- [ ] T012 [US1] [Depends on T007] Write contract tests against `dataset.schema.yaml` in `tests/contract/test_dataset.py`. **Requirement**: Implement specific test function: `tests/contract/test_dataset.py::test_schema_compliance` (validates data against the schema defined in T007). **Verification**: Ensure `specs/.../contracts/dataset.schema.yaml` exists before running tests. **Dependency**: T007.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel. T008a, T008d, T008b, T008c, and T007 provide the directory structure, state init, checksum utility, and schema required by T009/T010 for data integrity.

---

## Phase 4: User Story 2 - Compute Molecular Flexibility Descriptors and Correlate with Permeability (Priority: P2)

**Goal**: Generate 3D conformer ensembles, calculate torsional variance, and compute statistical correlations.

**Independent Test**: Process a sample of molecules and verify ≥450 valid flexibility descriptors are computed and at least one correlation coefficient is produced with p-values.

### Implementation for User Story 2

- [ ] T013 [US2] [Depends on T010] Implement conformer generation and descriptor calculation in `code/data/descriptors.py`. **Requirement**: Implement three specific functions:
 1. `generate_conformers(smiles_list)`: Uses RDKit to generate 3D conformer ensembles (size = 50, energy window ≤ 10 kcal/mol).
 2. `handle_conformer_errors(errors_list)`: Logs failures, skips molecules, and continues processing.
 3. `calculate_success_rate(total, valid)`: Computes the Conformer Generation Success Rate and compares against SC-002 (≥450 valid descriptors).
 **Traceability**: Explicitly reference FR-003 in code comments and logs. **Dependency**: T010 (data ready).
- [ ] T014a [US2] Implement flexibility descriptor calculation in `code/data/descriptors.py`. **Requirement**: Compute torsional variance (dihedral, bond, angle) in rad². **CRITICAL**: `dihedral_variance` is the **primary** descriptor for modeling (FR-004). `bond_variance` and `angle_variance` are **diagnostic only** (Plan Constitution Check VI). **Output**: Save all three to CSV for SC-003 completeness reporting, but note that only dihedral is used for prediction. **Dependency**: T013.
- [ ] T014b [P] [US2] Implement outlier flagging logic in `code/data/descriptors.py` using the interquartile range method (IQR > 1.5 × Q1) for the computed variance columns. **Dependency**: T014a.
- [ ] T014c [P] [US2] Implement output formatting in `code/data/descriptors.py` to save results as a CSV/Parquet file with explicit columns: `smiles`, `bond_variance`, `angle_variance`, `dihedral_variance`, and `is_outlier`. **Dependency**: T014b.
- [ ] T015 [US2] [Depends on T010, T014c] Implement `code/data/analysis.py` to compute Pearson and Spearman correlations between **dihedral_variance** (primary) and **bond/angle_variance** (diagnostic) and logPapp with p-values. **Requirement**: Report all three for SC-003 completeness, but explicitly label bond/angle as diagnostic. **Dependency**: T010, T014c.
- [ ] T016 [US2] Implement Benjamini-Hochberg FDR correction in `code/data/analysis.py` for multiple hypothesis testing (q < 0.05). **Requirement**: Apply FDR correction to the **full set of 3 descriptors** (bond, angle, dihedral) as required by FR-006. **Dependency**: T015.
- [ ] T017 [US2] Write unit tests for conformer generation and variance calculation in `tests/test_descriptors.py`. **Dependency**: T014c.
- [ ] T018 [US2] Write unit tests for correlation and FDR logic in `tests/test_analysis.py`. **Dependency**: T016.

**Checkpoint**: Flexibility descriptors computed and correlations calculated; results stored in `data/processed/`.

---

## Phase 5: User Story 3 - Validate Model Performance and Generate Publication-Quality Visualizations (Priority: P3)

**Goal**: Build multivariate linear regression model with standard cross-validation, and generate visualizations.

**Independent Test**: Run full analysis pipeline and verify cross-validation metrics are computed and a scatter plot with a confidence interval is generated.

### Implementation for User Story 3

- [ ] T019a [US3] [Depends on T014c] Implement multivariate linear regression model in `code/data/analysis.py` using **dihedral_variance** as the primary predictor and confounders (logP, MW, PSA). **Requirement**: The model MUST utilize `dihedral_variance` as the primary flexibility descriptor. **Constraint**: Strictly adhere to FR-007 confounders: **logP, MW, PSA**. **Fallback**: If collinearity is detected (VIF > 5), apply Ridge regression (alpha=1.0) as the **mandatory** fallback. Do NOT drop descriptors. **Dependency**: T014c.
- [ ] T019b [US3] Implement VIF (Variance Inflation Factor) diagnosis for predictor collinearity in `code/data/analysis.py`. **Dependency**: T019a.
- [ ] T019c [US3] [Depends on T019a, T019b] Implement Ridge regression fallback logic in `code/data/analysis.py`. **Requirement**: If VIF > 5, automatically switch to Ridge regression (alpha=1.0). **Dependency**: T019a, T019b.
- [ ] T020 [US3] Implement k-fold cross-validation in `code/data/analysis.py` to assess generalizability. **Requirement**: Execute 5-fold cross-validation as mandated by FR-007. Output mean R², RMSE, and MAE. **Dependency**: T019c.
- [ ] T022a [US3] Implement scatter plot logic in `code/data/visualize.py` to generate plots with regression line and confidence interval. **Requirement**: Use `seaborn.regplot` to generate a scatter plot showing the flexibility-permeability relationship. **Dependency**: T020.
- [ ] T022b [P] [US3] Implement layout adjustments in `code/data/visualize.py` for publication quality (fonts, labels). **Dependency**: T022a.
- [ ] T023a [US3] Update `code/data/visualize.py` and `code/data/analysis.py` plot titles to explicitly state "Associational Relationship" (not causal) as required by FR-009. **Verification**: Grep for "associational" in generated PNG metadata and code comments. **Dependency**: T022a.
- [ ] T023b [US3] [Depends on T000, T001, T015, T019a, T022a, T023c] Update `specs/001-molecular-flexibility-permeability/research.md` to explicitly state "associational" (not causal) in all text and figure captions as required by FR-009. **Requirement**: Verify `research.md` exists before updating. **Dependency**: T000, T001, T015, T019a, T022a, T023c.
- [ ] T023c [US3] Implement metadata injection in `code/data/visualize.py` to add "Associational Relationship" disclaimer to PNG metadata and analysis output JSON/CSV headers. **Requirement**: Ensure FR-009 compliance for all output deliverables. **Dependency**: T022a.
- [ ] T024 [US3] Write integration tests for the full analysis pipeline in `tests/test_analysis.py`. **Requirement**: Tests must run the full pipeline end-to-end to verify metrics. **Dependency**: T020.
- [ ] T025 [US3] Write contract tests for `analysis_output.schema.yaml` in `tests/contract/test_analysis.py`. **Requirement**: Tests must validate analysis output against the schema. **Dependency**: T007 (schema pattern).

**Checkpoint**: Model validated, visualizations generated, and research report ready.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T006 [P] Implement `code/utils/generate_transparency_report.py`. **Requirement**: Create a script that reads execution logs and deviation records to generate the "Computational Method Transparency" section dynamically. **Dependency**: None.
- [ ] T036 [P] Update `specs/001-molecular-flexibility-permeability/research.md` with final results, methodology justification, and explicit documentation of the "Computational Method Transparency" section as required by Constitution Principle VI and Plan constraints. **Requirement**: **Do NOT create the file** (T000/T001 must have created it). **Content Template**:
```markdown
## Computational Method Transparency
- **Conformer Generation**: RDKit `EmbedMultipleConfs` with [count] conformers per molecule.
- **Flexibility Metric**: Torsional variance (dihedral) computed via [method].
- **Statistical Rigor**: Pearson/Spearman correlations with Benjamini-Hochberg FDR correction.
- **Model Validation**: 5-fold cross-validation with [R²] mean.
- **Constraint**: All steps are CPU-tractable; no GPU offload.
```
**Dependency**: T000, T001, T015, T020, T022a, T019a.

- [ ] T037 [P] Execute the script created in T006 (`code/utils/generate_transparency_report.py`) to generate the narrative section dynamically from logs and deviation records. **Note**: If T006 was not implemented, skip this task. **Dependency**: T006.
- [ ] T038 [P] Update `specs/001-molecular-flexibility-permeability/plan.md` to reflect any deviations or confirmed constraints. **Dependency**: None.
- [ ] T039 Refactor `code/data/analysis.py` to reduce cyclomatic complexity < 10. **Dependency**: T020.
- [ ] T040a [P] [US3] Execute benchmark on a representative sample of molecules to verify total runtime estimate. **Requirement**: Execute the full pipeline on a **representative subset of the initial molecules**. Measure `sample_time`. Calculate `estimated_runtime` = `sample_time` * (total_molecules / 50). **Dependency**: T020.
- [ ] T040b [P] [US3] [Depends on T040a] Implement governance review logic. **Requirement**: If `estimated_runtime` > 6 hours, log a "Manual Governance Review Required" warning and flag the project. Do NOT modify `plan.md` automatically. Do NOT reduce the dataset size without a formal governance update. **Pass Criteria**: Estimated runtime ≤ 6 hours or a documented flag for governance review. **Traceability**: SC-005. **Dependency**: T040a.
- [ ] T041 Execute `quickstart.md` instructions end-to-end. **Requirement**: Verify `data/processed/descriptors.csv` exists with ≥450 rows. **Pass Criteria**: Script runs without errors and produces the expected output file. **Dependency**: T040a.

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
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT T008a and T008c**. T008c depends on T008a.
- Once Foundational phase completes, US1, US2, and US3 can start in parallel (if team capacity allows)
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
5. Add Phase N (Polish) → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

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
- **Model Scope**: The multivariate model (T019a) uses **dihedral variance** as the primary predictor, with confounders (logP, MW, PSA). Bond and angle variances are computed for diagnostics only. Collinearity handling (VIF, Ridge) is documented and implemented (T019b, T019c).
- **Documentation**: Research narratives (T036, T037) must be generated dynamically from logs and deviation records via the script created in T006, not hardcoded.
- **SC-002 Threshold**: Conformer generation success rate is measured against a minimum threshold of **≥450 valid descriptors**.
- **Fixed Status Inconsistency**: T008 split into T008a (dirs), T008c (verify), T008d (state init), T008b (checksum). T008e (governance proxy) REMOVED to comply with Constitution Principle V (Agent-only state writes).
- **Cleaned Up Notes**: Removed all references to unauthorized scope creep (Phase 6 / Geoffrey West).
- **Fixed Granularity**: T013 merged into a single task with explicit function signatures. T011/T012 updated with specific function names.
- **Fixed Executability**: T000, T001, T009, T010 updated with explicit content/commands.
- **Fixed Dependency**: T009, T010 now explicitly depend on T008b, T008d. T015 depends on T014c. T019a depends on T014c. T036 depends on T015.
- **Reviewer Concern Addressed**: All concerns regarding scope creep, model predictors, and cross-validation methods have been resolved by removing unauthorized tasks and aligning with spec.md FR-001 to FR-010.
- **Fixed T019c**: Status corrected to [ ]; dependencies updated to T019a, T019b.
- **Fixed T006**: Explicitly defined as script creation task.
- **Governance Fix**: T008b writes to `state/pending/`, T008e REMOVED (Agent action).
- **Dependency Fix**: T015 depends on T014c. T019a depends on T014c. T036 depends on T015.
- **Fixed T003**: Added `pyvib` to requirements.
- **Fixed T007**: Schema updated to include `protocol_metadata`.
- **Fixed T016**: FDR correction explicitly applies to all 3 descriptors.
- **Removed Phase 6**: All tasks T042-T048 (Scaling Law Analysis) removed as they are unauthorized scope creep.
- **Note on State File**: The application of checksums from `state/pending/` to `state/projects/...yaml` is an action performed by the Advancement-Evaluator Agent, not a script task.
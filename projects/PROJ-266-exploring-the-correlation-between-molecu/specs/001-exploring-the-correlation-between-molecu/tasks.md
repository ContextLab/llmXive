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

- [ ] T002 Create project structure per implementation plan (`code/`, `tests/`, `data/`). **Requirement**: Execute `os.makedirs('code/', exist_ok=True)`, `os.makedirs('tests/', exist_ok=True)`, `os.makedirs('data/', exist_ok=True)`. **Dependency**: None.
- [X] T003 Initialize a Python project with `requirements.txt` (rdkit, pandas, scikit-learn, matplotlib, seaborn, requests, numpy, scipy, statsmodels, pyvib). **Requirement**: Create `code/requirements.txt` and explicitly include `pyvib` in the list of dependencies. **Dependency**: T002.
- [ ] T004 [P] Configure linting (flake8/black) and formatting tools. **Dependency**: T002.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008a [US0] Create and verify directory structure for `data/raw/`, `data/processed/`, `state/projects/`, and `state/pending/`. **Requirement**: Execute `os.makedirs('data/raw/', exist_ok=True)`, `os.makedirs('data/processed/', exist_ok=True)`, `os.makedirs('state/projects/', exist_ok=True)`, `os.makedirs('state/pending/', exist_ok=True)`. Immediately verify creation by executing `assert os.path.isdir('data/raw')` and `assert os.path.isdir('data/processed')` and `assert os.path.isdir('state/projects')`. **Dependency**: None.
- [X] T008d [US0] Initialize `state/projects/` directory and create `PROJ-266-exploring-the-correlation-between-molecu.yaml`. **Requirement**: Create `state/projects/` directory. Create `state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml` with an empty `artifact_hashes: {}` map. **Dependency**: T002.
- [ ] T008b [US0] Implement `code/utils/checksum.py`. **Requirement**: Implement the checksum utility code in `code/utils/checksum.py`. The utility MUST compute SHA-256 checksums for files in `data/` and write the results to `state/pending/checksums.yaml` (NOT directly to the state file). **Governance Constraint**: Per Constitution Principle V, only the Advancement-Evaluator Agent may write to the state file. This script outputs to a pending file. **Dependency**: T008a.
- [ ] T007 [US0] Create `specs/001-molecular-flexibility-permeability/contracts/dataset.schema.yaml`. **Requirement**: Define the JSON schema for the Caco-2 dataset including fields: `smiles` (string), `logPapp` (number), `mw` (number), `psa` (number), `assay_id` (string), AND `protocol_metadata` (object with `lab_id`, `temperature`, `passage`). **Dependency**: None.

---

## Phase 3: User Story 1 - Retrieve and Preprocess Caco-2 Permeability Dataset (Priority: P1) 🎯 MVP

**Goal**: Download raw Caco-2 data from ChEMBL, filter for valid records, and ensure data completeness.

**Independent Test**: Execute retrieval script and verify output contains ≥500 valid records with non-NULL SMILES and logPapp from a raw batch of ≥600.

### Implementation for User Story 1

- [ ] T009 [US1] [Depends on T008a, T008d, T008b, T007] Implement `code/data/retrieval.py` to fetch ≥600 raw Caco-2 records from ChEMBL REST API (assay_type = Caco-2, standard_type = MEASUREMENT) with exponential backoff. **Requirement**: Save output to `data/raw/chembl_raw.csv`. The CSV schema MUST strictly match `specs/001-molecular-flexibility-permeability/contracts/dataset.schema.yaml`. The `protocol_metadata` object MUST be serialized as a JSON string within a single column to ensure CSV compatibility. The script MUST implement exponential backoff with a maximum of 3 retries at 5-second intervals for rate limit errors. After saving, invoke `code/utils/checksum.py` to generate a checksum and write to `state/pending/checksums.yaml`. **Dependency**: T008a, T008d, T008b, T007.
- [ ] T010 [US1] [Depends on T008a, T008d, T008b, T007, T009] Implement `code/data/preprocessing.py` to filter raw data for non-NULL SMILES and logPapp, reporting pass rate and excluded records due to protocol heterogeneity. **Requirement**: Read `data/raw/chembl_raw.csv` and parse the `protocol_metadata` JSON string back into an object. Filter for non-NULL SMILES and logPapp. Count and report the number of records excluded due to protocol heterogeneity (based on variance in `protocol_metadata` fields such as `lab_id`, `temperature`, or `passage`). Save output to `data/processed/filtered_data.csv`. **Traceability**: Explicitly reference FR-010 in code comments. After saving, invoke `code/utils/checksum.py` to generate a checksum and write to `state/pending/checksums.yaml`. **Dependency**: T008a, T008d, T008b, T007, T009.
- [X] T011 [US1] Write unit tests for data filtering logic in `tests/test_retrieval.py`. **Requirement**: Implement specific test functions: `tests/test_retrieval.py::test_filter_logic` (verifies filtering logic) and `tests/test_retrieval.py::test_pass_rate_calculation` (verifies pass rate). **Dependency**: T010.
- [~] T012 [US1] Write contract tests against `dataset.schema.yaml` in `tests/contract/test_dataset.py`. **Requirement**: Implement specific test function: `tests/contract/test_dataset.py::test_schema_compliance` (validates data against the schema defined in T007). **Verification**: Ensure `specs/.../contracts/dataset.schema.yaml` exists before running tests. **Dependency**: T007.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel. T008a, T008d, T008b, and T007 provide the directory structure, state init, checksum utility, and schema required by T009/T010 for data integrity.

---

## Phase 4: User Story 2 - Compute Molecular Flexibility Descriptors and Correlate with Permeability (Priority: P2)

**Goal**: Generate 3D conformer ensembles, calculate torsional variance via NMA, and compute statistical correlations.

**Independent Test**: Process a sample of molecules and verify ≥450 valid flexibility descriptors are computed and at least one correlation coefficient is produced with p-values.

### Implementation for User Story 2

- [~] T013 [US2] [Depends on T010] Implement conformer generation in `code/data/conformer_gen.py`. **Requirement**: Implement `generate_conformers(smiles_list)` using RDKit to generate 3D conformer ensembles (size = 50, energy window ≤ 10 kcal/mol). **Output**: Save the generated conformer ensembles to `data/processed/conformers.pkl`. **Traceability**: Explicitly reference FR-003 in code comments. **Dependency**: T010.
- [~] T014 [US2] [Depends on T010, T013] Implement descriptor calculation and NMA in `code/data/descriptors.py`. **Requirement**: Read `data/processed/conformers.pkl` and verify the presence of the `lowest_energy_conformer_id` column from the previous step. Compute torsional variance (dihedral) in rad² derived from PyVib vibrational frequencies (primary metric). Bond and angle variances are computed for diagnostic purposes only and MUST NOT be included in the primary correlation analysis. **Output**: Save all three to `data/processed/descriptors_raw.csv` with columns: `smiles`, `bond_variance`, `angle_variance`, `dihedral_variance`. **Traceability**: Explicitly reference FR-004 and Plan Constitution Check VI. **Dependency**: T013, T010.
- [~] T015 [US2] [Depends on T014] Implement correlation analysis in `code/data/analysis.py`. **Requirement**: Compute Pearson and Spearman correlations between **dihedral_variance** (primary) and logPapp with p-values, while controlling for confounders (logP, MW, PSA). **Output**: Save correlation results to `data/processed/correlation_results.csv`. **Dependency**: T014.
- [~] T016 [US2] [Depends on T015] Implement Benjamini-Hochberg FDR correction in `code/data/analysis.py` for multiple hypothesis testing (q < 0.05). **Requirement**: Apply FDR correction to the correlation results with dihedral variance. **Output**: Update `data/processed/correlation_results.csv` with FDR-corrected q-values. **Dependency**: T015.
- [X] T017 [US2] Write unit tests for conformer generation and NMA in `tests/test_descriptors.py`. **Dependency**: T013.
- [X] T018 [US2] Write unit tests for correlation and FDR logic in `tests/test_analysis.py`. **Dependency**: T016.

**Checkpoint**: Flexibility descriptors computed and correlations calculated; results stored in `data/processed/`.

---

## Phase 4.5: Scaling Law Analysis (Advanced Exploration)

**Goal**: Investigate non-linear scaling relationships if linear models show insufficient fit, strictly adhering to statistical power requirements.

- [X] T026 [US2] [Depends on T016] Implement scaling law analysis logic in `code/data/analysis.py`. **Requirement**: If linear correlation (R² < 0.3) is observed, initiate scaling law analysis. Compute a `complexity_index` based on molecular size and flexibility. **Dependency**: T016.
- [ ] T027 [US2] [Depends on T026] Implement power-law regression model in `code/data/analysis.py`. **Requirement**: Fit a model `log(Permeability) ~ log(Flexibility) + log(Complexity)` using `scipy.optimize.curve_fit`. **Dependency**: T026.
- [ ] T028 [US2] [Depends on T027] Perform statistical power analysis and hypothesis testing for scaling exponents. **Requirement**: Use `statsmodels.stats.power` to calculate the detectable effect size for exponents 0.25, 0.5, and 1.0 given the current sample size. Test if the estimated scaling exponent is statistically distinguishable from these null hypotheses (p < 0.05 after FDR correction). **Output**: Save power analysis results and hypothesis test outcomes to `data/processed/scaling_analysis_results.json`. **Dependency**: T027.
- [ ] T029 [US2] [Depends on T028] Validate scaling law model performance against linear model. **Requirement**: Compare AIC/BIC of the power-law model vs. the linear model. **Dependency**: T028.
- [ ] T030 [US2] [Depends on T029] Update `research.md` with scaling law findings. **Requirement**: If the power-law model is statistically superior, update `research.md` to reflect the scaling law hypothesis. **Dependency**: T029.

**Checkpoint**: Scaling law analysis complete; results stored in `data/processed/`.

---

## Phase 5: User Story 3 - Validate Model Performance and Generate Publication-Quality Visualizations (Priority: P3)

**Goal**: Build multivariate linear regression model with standard cross-validation, and generate visualizations.

**Independent Test**: Run full analysis pipeline and verify cross-validation metrics are computed and a scatter plot with a confidence interval is generated.

### Implementation for User Story 3

- [ ] T019a [US3] [Depends on T014] Implement multivariate linear regression model in `code/data/analysis.py` using **dihedral_variance** as the primary predictor and confounders (logP, MW, PSA). **Requirement**: The model MUST utilize **dihedral_variance** as the primary flexibility descriptor. **Constraint**: Strictly adhere to FR-007 confounders: **logP, MW, PSA**. **Output**: Save model coefficients, metrics, and validation results to `data/processed/model_results.json`. **Dependency**: T014.
- [ ] T020 [US3] [Depends on T019a] Implement k-fold cross-validation in `code/data/analysis.py` to assess generalizability. **Requirement**: Execute 5-fold cross-validation as mandated by FR-007. Output mean R², RMSE, and MAE. **Dependency**: T019a.
- [ ] T022a [US3] Implement scatter plot logic in `code/data/visualize.py` to generate plots with regression line and confidence interval. **Requirement**: Use `seaborn.regplot` to generate a scatter plot showing the flexibility-permeability relationship. **Dependency**: T020.
- [ ] T023a [US3] Update `code/data/visualize.py` and `code/data/analysis.py` plot titles to explicitly state "Associational Relationship" (not causal) as required by FR-009. **Verification**: Grep for "associational" in generated PNG metadata and code comments. **Dependency**: T022a.
- [ ] T024 [US3] Write integration tests for the full analysis pipeline in `tests/test_analysis.py`. **Requirement**: Tests must run the full pipeline end-to-end to verify metrics. **Dependency**: T020.

**Checkpoint**: Model validated, visualizations generated, and research report ready.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T006 [P] Implement `code/utils/generate_transparency_report.py`. **Requirement**: Create a script that reads execution logs and deviation records to generate the "Computational Method Transparency" section dynamically. **Dependency**: None.
- [ ] T036 [P] Execute the script created in T006 (`code/utils/generate_transparency_report.py`) to generate the narrative section dynamically. **Requirement**: This task MUST also generate `specs/001-molecular-flexibility-permeability/research.md` with final results, methodology justification, and the "Computational Method Transparency" section as required by Constitution Principle VI and Plan constraints. **Content Template**:
```markdown
## Computational Method Transparency
- **Conformer Generation**: RDKit `EmbedMultipleConfs` with [count] conformers per molecule.
- **Flexibility Metric**: Torsional variance (dihedral) computed via PyVib Normal Mode Analysis.
- **Statistical Rigor**: Pearson/Spearman correlations with Benjamini-Hochberg FDR correction.
- **Model Validation**: 5-fold cross-validation with [R²] mean.
- **Constraint**: All steps are CPU-tractable; no GPU offload.
```
**Dependency**: T015, T020, T022a, T028.

- [ ] T038 [P] Update `specs/001-molecular-flexibility-permeability/plan.md` to reflect any deviations or confirmed constraints. **Dependency**: None.
- [ ] T039 Refactor `code/data/analysis.py` to reduce cyclomatic complexity < 10. **Dependency**: T020.
- [ ] T040a [P] [US3] Execute benchmark on a representative sample of molecules to verify total runtime estimate. **Requirement**: Execute the full pipeline on a **representative subset of the initial molecules**. Measure `sample_time`. Calculate `estimated_runtime` = `sample_time` * (total_molecules / 50). **Dependency**: T020.
- [ ] T040b [P] [US3] [Depends on T040a] Implement governance review logic. **Requirement**: If `estimated_runtime` > 6 hours, reduce sample size by [deferred]. Log a "Manual Governance Review Required" if runtime still exceeds the limit. Do NOT modify `plan.md` automatically. **Pass Criteria**: Estimated runtime ≤ 6 hours or a documented flag for governance review. **Traceability**: SC-005. **Dependency**: T040a.
- [ ] T041 Execute `quickstart.md` instructions end-to-end. **Requirement**: Verify `data/processed/descriptors_final.csv` exists with ≥450 rows. **Pass Criteria**: Script runs without errors and produces the expected output file. **Dependency**: T040a.

---

## Dependencies & Execution Order

(Details omitted for brevity - see original tasks.md)
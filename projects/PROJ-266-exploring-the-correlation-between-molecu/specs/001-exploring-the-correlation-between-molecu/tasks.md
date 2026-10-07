# Tasks: Exploring the Correlation Between Molecular Flexibility and Drug Transport Across Cell Membranes

**Input**: Design documents from `/specs/001-molecular-flexibility-permeability/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [ ] T002 Create project directory structure. **Requirement**: Execute `mkdir -p code tests data data/raw data/processed state/projects state/pending specs/001-molecular-flexibility-permeability/contracts` at the repository root. **Dependency**: None.
- [X] T003 Initialize a Python project with `requirements.txt` (rdkit, pandas, scikit-learn, matplotlib, seaborn, requests, numpy, scipy, statsmodels, nolds, pyvib). **Requirement**: Create `code/requirements.txt` and explicitly include `rdkit`, `pandas`, `scikit-learn`, `matplotlib`, `seaborn`, `requests`, `numpy`, `scipy`, `statsmodels`, `nolds`, and `pyvib`. **Dependency**: T002.
- [ ] T004 [P] Configure linting (flake8/black) and formatting tools. **Dependency**: T002.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008a [US0] Create and verify directory structure for `data/raw/`, `data/processed/`, `state/projects/`, and `state/pending/`. **Requirement**: Create the `data/raw/`, `data/processed/`, `state/projects/`, and `state/pending/` directories. Immediately verify creation by checking that each directory exists. **Dependency**: T002.
- [X] T008d [US0] Initialize `state/projects/` directory and create `PROJ-266-exploring-the-correlation-between-molecu.yaml`. **Requirement**: Create `state/projects/` directory. Create `state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml` with an empty `artifact_hashes: {}` map. **Dependency**: T002.
- [ ] T008b [US0] Implement `code/utils/checksum.py`. **Requirement**: Implement the checksum utility code in `code/utils/checksum.py`. The utility MUST compute SHA-256 checksums for files in `data/` and write the results to `state/pending/checksums.yaml` (NOT directly to the state file). **Governance Constraint**: Per Constitution Principle V, only the Advancement-Evaluator Agent may write to the state file. This script outputs to a pending file. **Dependency**: T008a.
- [ ] T007 [US0] Create `specs/001-molecular-flexibility-permeability/contracts/dataset.schema.yaml`. **Requirement**: Define the JSON schema for the Caco-2 dataset including fields: `smiles` (string), `logPapp` (number), `mw` (number), `psa` (number), `assay_id` (string), AND `protocol_metadata` (object with `standard_type` (string)). **Dependency**: T002.

---

## Phase 3: User Story 1 - Retrieve and Preprocess Caco-2 Permeability Dataset (Priority: P1) 🎯 MVP

**Goal**: Download raw Caco-2 data from ChEMBL, filter for valid records, and ensure data completeness.

**Independent Test**: Execute retrieval script and verify output contains ≥500 valid records with non-NULL SMILES and logPapp from a raw batch of ≥600.

### Implementation for User Story 1

- [ ] T009 [US1] [Depends on T008a, T008d, T008b, T007] Implement `code/data/retrieval.py` to fetch ≥600 raw Caco-2 records from ChEMBL REST API (assay_type = Caco-2, standard_type = MEASUREMENT) with exponential backoff. **Requirement**: Save output to `data/raw/chembl_raw.csv`. The CSV schema MUST strictly match `specs/001-molecular-flexibility-permeability/contracts/dataset.schema.yaml`. The `protocol_metadata` object MUST be serialized as a JSON string within a single column to ensure CSV compatibility. The script MUST implement exponential backoff with a maximum of 3 retries at 5-second intervals for rate limit errors. After saving, invoke `code/utils/checksum.py` to generate a checksum and write to `state/pending/checksums.yaml`. **Dependency**: T008a, T008d, T008b, T007.
- [ ] T010 [US1] [Depends on T008a, T008d, T008b, T007, T009] Implement `code/data/preprocessing.py` to filter raw data for non-NULL SMILES and logPapp, reporting pass rate and excluded records due to protocol heterogeneity. **Requirement**: Read `data/raw/chembl_raw.csv` and parse the `protocol_metadata` JSON string back into an object. Filter for non-NULL SMILES and logPapp. Filter for records where `protocol_metadata.standard_type` is 'MEASUREMENT'. Count and report the number of records excluded due to protocol heterogeneity. Save output to `data/processed/filtered_data.csv`. **Traceability**: Explicitly reference FR-010 in code comments. After saving, invoke `code/utils/checksum.py` to generate a checksum and write to `state/pending/checksums.yaml`. **Dependency**: T008a, T008d, T008b, T007, T009.
- [X] T011 [US1] Write unit tests for data filtering logic in `tests/test_preprocessing.py`. **Requirement**: Implement specific test functions: `tests/test_preprocessing.py::test_filter_logic` (verifies filtering logic in `code/data/preprocessing.py`) and `tests/test_preprocessing.py::test_pass_rate_calculation` (verifies pass rate). **Dependency**: T010.
- [ ] T012 [US1] Write contract tests against `dataset.schema.yaml` in `tests/contract/test_dataset.py`. **Requirement**: Implement specific test function: `tests/contract/test_dataset.py::test_schema_compliance` (validates data against the schema defined in T007). **Verification**: Ensure `specs/.../contracts/dataset.schema.yaml` exists before running tests. **Dependency**: T007. <!-- FAILED: unspecified -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel. T008a, T008d, T008b, and T007 provide the directory structure, state init, checksum utility, and schema required by T009/T010 for data integrity.

---

## Phase 4: User Story 2 - Compute Molecular Flexibility Descriptors and Correlate with Permeability (Priority: P2)

**Goal**: Generate 3D conformer ensembles, calculate torsional variance via NMA, and compute statistical correlations.

**Independent Test**: Process a sample of molecules and verify ≥450 valid flexibility descriptors are computed and at least one correlation coefficient is produced with p-values.

### Implementation for User Story 2

- [ ] T010b [US3] [Depends on T010] Compute physicochemical confounders (logP, MW, PSA) for the filtered dataset to support controlled correlation analysis (T015b) and multivariate regression (T019a) per FR-007. **Requirement**: Read `data/processed/filtered_data.csv`. Calculate logP (using RDKit MolLogP), MW (using RDKit MolWt), and PSA (using RDKit CalcTPSA) for each SMILES. Append these columns to the dataset. Save output to `data/processed/enriched_data.csv`. **Dependency**: T010. <!-- FAILED: unspecified -->
- [ ] T025 [US2] [Depends on T010b] Calculate Molecular Weight (MW) as the complexity metric for Scaling Law analysis. **Requirement**: Read `data/processed/enriched_data.csv`. Use the existing `mw` column as the complexity metric. Append a copy to `data/processed/enriched_data.csv` as `complexity_metric`. **Rationale**: Required to test the hypothesis that transport scales with molecular complexity. **Dependency**: T010b.
- [ ] T013 [US2] [Depends on T010] Implement conformer generation in `code/data/conformer_gen.py`. **Requirement**: Implement `generate_conformers(smiles_list)` using RDKit to generate 3D conformer ensembles (size = 50, energy window ≤ 10 kcal/mol). **Output**: Save the generated conformer ensembles to `data/processed/conformers.pkl`. **Traceability**: Explicitly reference FR-003 in code comments. **Dependency**: T010.
- [X] T017 [US2] [P] Write unit tests for conformer generation and NMA in `tests/test_descriptors.py`. **Requirement**: Implement specific test functions for conformer generation logic. Can run in parallel with subsequent analysis tasks once code is written. **Dependency**: T013.
- [ ] T014 [US2] [Depends on T013] Implement descriptor calculation and NMA in `code/data/descriptors.py`. **Requirement**: Read `data/processed/conformers.pkl`. For each molecule: 1) Load the lowest energy conformer. 2) Convert to XYZ format. 3) Call `pyvib.analyze_molecule(xyz_file)`. 4) Extract eigenvalues (frequencies). 5) Compute torsional variance (dihedral) in rad². **Primary Metric**: dihedral_variance. **Diagnostic Metrics**: bond_variance, angle_variance. **Constraint**: If dihedral_variance fails for a molecule, skip that molecule entirely (do not output diagnostic metrics for it). **Output**: Save all three to `data/processed/descriptors_raw.csv` with columns: `smiles`, `bond_variance` (diagnostic), `angle_variance` (diagnostic), `dihedral_variance` (primary). **Traceability**: Explicitly reference FR-004 and Plan Constitution Check VI. **Threshold Check**: If <450 valid descriptors are generated, halt the pipeline and log an error. **Dependency**: T013, T010. <!-- FAILED: unspecified -->
- [X] T014b [US2] [Depends on T003] Verify PyVib installation and version pinning. **Requirement**: Create `code/utils/verify_pyvib.py`. Run `import pyvib; print(pyvib.__version__)`. Ensure version matches `requirements.txt`. **Dependency**: T003.
- [ ] T015 [US2] [Depends on T014, T010] Implement DIAGNOSTIC bivariate correlation analysis in `code/data/analysis.py`. **Requirement**: Compute Pearson and Spearman correlations between EACH flexibility descriptor (bond, angle, dihedral) and logPapp with p-values. **Constraint**: Do NOT control for confounders in this step. This is a diagnostic baseline only. **Output**: Save correlation results to `data/processed/correlation_diagnostic.csv`. **Dependency**: T014, T010.
- [ ] T015b [US2] [Depends on T014, T010b] Implement CONTROLLED partial correlation analysis in `code/data/analysis.py`. **Requirement**: Compute partial correlations between `dihedral_variance` and logPapp, controlling for logP, MW, and PSA. **Output**: Save results to `data/processed/correlation_controlled.csv`. **Dependency**: T014, T010b.
- [X] T018 [US2] [P] Write unit tests for correlation and FDR logic in `tests/test_analysis.py`. **Requirement**: Implement specific test functions for correlation and FDR logic. Can run in parallel with subsequent analysis tasks once code is written. **Dependency**: T015, T015b.
- [ ] T016 [US2] [Depends on T015] Implement Benjamini-Hochberg FDR correction in `code/data/analysis.py` for multiple hypothesis testing (q < 0.05). **Requirement**: Apply FDR correction to the diagnostic correlation results for all descriptors. **Output**: Update `data/processed/correlation_diagnostic.csv` with FDR-corrected q-values. **Dependency**: T015.

**Checkpoint**: Flexibility descriptors computed and correlations calculated; results stored in `data/processed/`.

---

## Phase 5: User Story 3 - Validate Model Performance and Generate Publication-Quality Visualizations (Priority: P3)

**Goal**: Build multivariate linear regression model with standard cross-validation, and generate visualizations.

**Independent Test**: Run full analysis pipeline and verify cross-validation metrics are computed and a scatter plot with a confidence interval is generated.

### Implementation for User Story 3

- [ ] T019a [US3] [Depends on T014, T010b] Implement multivariate linear regression model in `code/data/analysis.py` using `dihedral_variance` as the primary predictor and confounders (logP, MW, PSA). **Requirement**: The model MUST utilize `dihedral_variance` as the primary flexibility descriptor. Include logP, MW, and PSA as fixed covariates. **Constraint**: Do NOT use conditional logic for covariate inclusion; the model structure is fixed per FR-007. **Input**: Use `data/processed/enriched_data.csv` from T010b. **Output**: Save model coefficients, metrics, and validation results to `data/processed/model_results.json`. **Dependency**: T014, T010b.
- [X] T020 [US3] [Depends on T019a] Implement k-fold cross-validation in `code/data/analysis.py` to assess generalizability. **Requirement**: Execute k-fold cross-validation as mandated by FR-007. Output mean R², RMSE, MAE, AND standard deviation of R² across folds. **Dependency**: T019a.
- [X] T022a [US3] Implement scatter plot logic in `code/data/visualize.py` to generate plots with regression line and confidence interval. **Requirement**: Use `seaborn.regplot` to generate a scatter plot showing the flexibility-permeability relationship. **Dependency**: T020.
- [X] T023a [US3] Update `code/data/visualize.py` and `code/data/analysis.py` plot titles to explicitly state "Associational Relationship" (not causal) as required by FR-009. **Verification**: Grep for "associational" in generated PNG metadata and code comments. **Dependency**: T022a.
- [X] T024 [US3] Write integration tests for the full analysis pipeline in `tests/test_analysis.py`. **Requirement**: Tests must run the full pipeline end-to-end to verify metrics. **Dependency**: T020.

**Checkpoint**: Model validated, visualizations generated, and research report ready.

---

## Phase 6: Scaling Law Analysis (Conditional: If Linear R² < 0.3)

**Goal**: Investigate the scaling exponent of transport rates relative to molecular complexity, testing for power-law relationships as suggested by the plan.

**Independent Test**: Execute scaling analysis script and verify that a power-law model is fitted and compared against the linear model, with a reported scaling exponent.

### Implementation for Scaling Analysis

- [~] T026 [US3] [Depends on T025, T019a] Implement power-law model fitting in `code/data/analysis.py`. **Requirement**: Fit a power-law model: `logPapp = a * (complexity_metric)^b + c` using `scipy.optimize.curve_fit`. Initial parameters: [1.0, -0.5, 0.0]. **Output**: Save fitted parameters (a, b, c) and R² to `data/processed/scaling_analysis_results.json`. **Traceability**: Explicitly reference the plan's deviation section regarding "Scaling Law". **Dependency**: T025, T019a.
- [~] T027 [US3] [Depends on T026] Implement model comparison and hypothesis testing in `code/data/analysis.py`. **Requirement**: Compare the power-law model (T026) against the linear model (T019a) using AIC/BIC and F-tests. **Output**: Update `data/processed/scaling_analysis_results.json` with comparison metrics and a conclusion on whether a power-law relationship is statistically superior. **Dependency**: T026.
- [~] T028 [US3] [Depends on T027] Implement visualization for scaling analysis in `code/data/visualize.py`. **Requirement**: Generate a log-log plot of `logPapp` vs `complexity_metric` with the fitted power-law curve and confidence intervals. **Output**: Save as `data/processed/scaling_plot.png` with dpi ≥ 300. **Dependency**: T027. <!-- FAILED: unspecified -->
- [X] T029 [US3] Write unit tests for scaling law analysis in `tests/test_scaling.py`. **Requirement**: Implement tests for power-law fitting and model comparison logic. **Dependency**: T027.

**Checkpoint**: Scaling law analysis complete; power-law vs linear model comparison available.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T006 [P] Implement `code/utils/generate_transparency_report.py`. **Requirement**: Create a script that reads execution logs and deviation records to generate the "Computational Method Transparency" section dynamically. **Dependency**: None.
- [X] T036 [P] Execute the script created in T006 (`code/utils/generate_transparency_report.py`) to generate the narrative section dynamically. **Requirement**: This task MUST also generate `specs/001-molecular-flexibility-permeability/research.md` with final results, methodology justification, and the "Computational Method Transparency" section as required by Constitution Principle VI and Plan constraints. **Content Template**:
```markdown
## Computational Method Transparency
- **Conformer Generation**: RDKit `EmbedMultipleConfs` with [count] conformers per molecule.
- **Flexibility Metric**: Torsional variance (dihedral) computed via PyVib Normal Mode Analysis.
- **Statistical Rigor**: Pearson/Spearman correlations with Benjamini-Hochberg FDR correction.
- **Model Validation**: -fold cross-validation with [R²] mean.
- **Scaling Law Analysis**: Power-law model fitting with exponent [b] and comparison to linear model.
- **Constraint**: All steps are CPU-tractable; no GPU offload.
```
**Dependency**: T015, T016, T019a, T020, T022a, T028. **Note**: This task MUST check for the existence of `data/processed/scaling_analysis_results.json`. If it exists and contains results, include the respective sections. **Dependency**: T015, T016, T020, T022a, T028.

- [~] T038 [P] Update `specs/001-molecular-flexibility-permeability/plan.md` to reflect any deviations or confirmed constraints. **Dependency**: None. <!-- FAILED: unspecified -->
- [X] T039 Refactor `code/data/analysis.py` to reduce cyclomatic complexity < 10. **Dependency**: T020. <!-- FAILED: unspecified -->
- [~] T040a [P] [US3] Execute benchmark on a representative sample of molecules to verify total runtime estimate. **Requirement**: Execute the full pipeline on a **fixed representative subset of 100 molecules**. Measure `sample_time`. Calculate `estimated_runtime` = `sample_time` * (total_molecules / 100). **Dependency**: T020.
- [ ] T041 Execute `quickstart.md` instructions end-to-end. **Requirement**: Verify `data/processed/descriptors_raw.csv` exists with ≥450 rows. Verify `state/pending/checksums.yaml` contains valid checksums for `data/processed/` files. **Pass Criteria**: Script runs without errors and produces the expected output file. **Dependency**: T040a. <!-- FAILED: unspecified -->
- [~] T047 [P] [US3] Update `research.md` to include the final results from the analysis. **Requirement**: Explicitly discuss the findings regarding the flexibility-permeability relationship AND the scaling law analysis. This task updates `research.md` with the final results of the linear regression, correlation analysis (US1-US3), and the power-law scaling analysis (Phase 6). **Dependency**: T023a, T024, T028, T029. <!-- FAILED: unspecified -->

---

## Dependencies & Execution Order

(Details omitted for brevity - see original tasks.md)
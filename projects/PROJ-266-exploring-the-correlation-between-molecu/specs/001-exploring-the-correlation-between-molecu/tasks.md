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

- [ ] T000 Create `research.md` file in `specs/001-molecular-flexibility-permeability/` if it does not exist. **Requirement**: Initialize the file with the standard header (Title, Branch, Created, Status). **Dependency**: None.
- [ ] T001 Populate `research.md` in `specs/001-molecular-flexibility-permeability/` with the standard template sections (Introduction, Methodology, Results, Discussion). **Requirement**: Ensure all sections exist as headers for future content. **Dependency**: T000.
- [ ] T002 Create project structure per implementation plan (`code/`, `tests/`, `data/`)
- [X] T003 Initialize a Python project with `requirements.txt` (rdkit, pandas, scikit-learn, matplotlib, seaborn, requests, numpy, scipy, statsmodels)
- [ ] T004 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006a [US0] Create and initialize the spec deviation record in `state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml` with ID DEV-001. **Requirement**: This task MUST create the record from scratch (as none exists) with the correct YAML syntax. It must populate the fields: `id` ("DEV-001"), `spec_requirement` ("FR-003"), `conformer_count` (20 - integer), `rationale` ("CPU feasibility on GitHub Actions free-tier"), `impact_assessment` ("Potential loss of variance stability; mitigated by sensitivity analysis"), `approved_by` ("Project Governance Board"), and `approved_at` ("2026-07-04"). The YAML schema is:
```yaml
spec_deviations:
 - id: "DEV-001"
   spec_requirement: "FR-003"
   conformer_count: 20
   rationale: "CPU feasibility on GitHub Actions free-tier"
   impact_assessment: "Potential loss of variance stability; mitigated by sensitivity analysis"
   approved_by: "Project Governance Board"
   approved_at: "2026-07-04"
```
**Note**: This schema corrects the malformed block in `plan.md` and ensures the `conformer_count` is a valid integer for downstream consumption. Implementers MUST use this corrected schema. **Dependency**: None. **Validation**: Ensure the YAML is valid and the `conformer_count` field is exactly 20. **File Path**: `state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml`.
- [X] T006 [US0] Implement `code/utils/generate_transparency_report.py` script. **Requirement**: This script must be created now to generate the "Computational Method Transparency" section for `research.md` (as defined in `plan.md` Project Structure) at execution time. The script reads the deviation record (`state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml`). **Error Handling**: The script MUST handle the case where the deviation record is missing or empty (e.g., if T006a hasn't run yet) by logging a warning and proceeding with default values or halting gracefully, rather than crashing. **Dependency**: None (Graceful fallback if T006a is missing). **Validation**: Ensure the script runs without crashing even if the deviation record is absent. **File Path**: `code/utils/generate_transparency_report.py`.
- [X] T007 [US0] Create base data schemas in `specs/001-molecular-flexibility-permeability/contracts/` (dataset.schema.yaml, analysis_output.schema.yaml). **Requirement**: Define JSON/YAML schemas for dataset and analysis output. **Status**: Marked complete to unblock T012.
- [ ] T008a [US0] Create directory structure for `data/raw/` and `data/processed/`. **Requirement**: Create the necessary folders (`data/raw/`, `data/processed/`) using standard OS path utilities. **Dependency**: T009 and T010 depend on these directories existing.
- [X] T008b [US0] Implement `code/utils/checksum.py`. **Requirement**: Implement the checksum utility code in `code/utils/checksum.py`. The utility MUST compute SHA-256 checksums for files in `data/` and write the results directly to the `artifact_hashes` map in `state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml`. **Governance Constraint**: Per Constitution Principle V, the `Advancement-Evaluator Agent` is the sole entity authorized to merge logs into the state YAML file, but this script MUST write the checksums to the `artifact_hashes` map directly to satisfy Constitution Principles III and V. **Dependency**: T008a must be complete (directories must exist).

---

## Phase 3: User Story 1 - Retrieve and Preprocess Caco-2 Permeability Dataset (Priority: P1) 🎯 MVP

**Goal**: Download raw Caco-2 data from ChEMBL, filter for valid records, and ensure data completeness.

**Independent Test**: Execute retrieval script and verify output contains ≥500 valid records with non-NULL SMILES and logPapp from a raw batch of ≥600.

### Implementation for User Story 1

- [X] T009 [US1] [Depends on T008a] Implement `code/data/retrieval.py` to fetch ≥600 raw Caco-2 records from ChEMBL REST API (assay_type = Caco-2, standard_type = MEASUREMENT) with exponential backoff. **Requirement**: After saving the raw CSV, this task MUST invoke `code/utils/checksum.py` to generate a checksum and register it in `state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml` (via T008b). **Dependency**: T008a must be complete.
- [X] T010 [US1] [Depends on T008a] Implement `code/data/preprocessing.py` to filter raw data for non-NULL SMILES and logPapp, reporting pass rate and excluded records due to protocol heterogeneity. **Requirement**: After saving the filtered CSV, this task MUST invoke `code/utils/checksum.py` to generate a checksum and register it in `state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml`. **Dependency**: T008a must be complete.
- [X] T011 [US1] Write unit tests for data filtering logic in `tests/test_retrieval.py`. **Requirement**: Tests must verify filtering logic and pass rate calculation. **Dependency**: T007 (schemas) must be complete.
- [ ] T012 [US1] [Depends on T007] Write contract tests against `dataset.schema.yaml` in `tests/contract/test_dataset.py`. **Requirement**: Tests must validate data against the schema defined in T007. **Dependency**: T007 (schemas) must be complete.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel. T008a and T008b provide the directory structure and checksum utility required by T009/T010 for data integrity. T006a and T007 are marked complete to unblock US2 and T012.

---

## Phase 4: User Story 2 - Compute Molecular Flexibility Descriptors and Correlate with Permeability (Priority: P2)

**Goal**: Generate 3D conformer ensembles, calculate torsional variance, and compute statistical correlations.

**Independent Test**: Process a sample of molecules and verify ≥450 valid flexibility descriptors are computed and at least one correlation coefficient is produced with p-values.

### Implementation for User Story 2

- [X] T013a [US2] Implement `code/data/descriptors.py` to generate 3D conformer ensembles using RDKit. **Requirement**: Generate conformers per molecule. The count MUST be read dynamically from the deviation record in `state/projects/PROJ-exploring-the-correlation-between-molecu.yaml` (key: `spec_deviations[0].conformer_count`). **Fallback**: If the deviation record is missing or the `conformer_count` field is absent/invalid, use the default value as specified in Plan.md Deviation and log a warning. **Traceability**: Explicitly reference Deviation ID **DEV-001** from `plan.md` in code comments and logs. **Error Handling**: If the deviation record is missing, do NOT fail; use the fallback default. **Note**: This task implements the ADAPTED requirement (20 conformers) documented in DEV-001, not the original Spec FR-003 (50 conformers). **Dependency**: None (Graceful fallback if T006a is missing).
- [X] T013b [US2] [Depends on T013a] Implement success rate calculation in `code/data/descriptors.py`. **Requirement**: Calculate the Conformer Generation Success Rate as (number of valid descriptors generated / total molecules attempted). Compare this rate against the threshold defined in SC-002 (≥450 valid descriptors). Log the calculated rate and the pass/fail status. If the count is < 450, the script MUST raise a clear error indicating the threshold was not met. **Dependency**: T013a must be complete to provide the counts.
- [X] T013c [US2] [Depends on T013a] Implement random sampling strategy in `code/data/descriptors.py` to select molecules if the dataset exceeds memory limits. **Requirement**: Use a fixed random seed (e.g., `numpy.random.seed()`) for deterministic, unbiased sampling. **Constraint**: The output must contain ≥450 valid descriptors. The sampling rule (which split, chunking, how many rows, seed) must be logged. If the dataset is smaller than 450 after sampling, the script MUST fail with a descriptive error. **Dependency**: T013b must confirm the dataset size allows for the threshold.
- [X] T013d [US2] [Depends on T013a, T013c] Implement error handling and logging in `code/data/descriptors.py` for conformer generation failures. **Requirement**: Log any molecule where conformer generation fails (e.g., stereochemistry issues) and skip it. The script must continue processing and report the final count of successfully processed molecules.
- [X] T014a [US2] Implement torsional variance calculation for **bond, angle, AND dihedral** (in rad²) in `code/data/descriptors.py`. **Requirement**: Compute ALL three variances as primary flexibility descriptors per FR-004. The output must include columns for `bond_variance`, `angle_variance`, and `dihedral_variance`. **Note**: All three are required for SC-003 completeness reporting. **Definition**: 'Torsional variance' in this context is defined as the variance of internal coordinates (bond, angle, dihedral) as per FR-004.
- [X] T014b [P] [US2] Implement outlier flagging logic in `code/data/descriptors.py` using the interquartile range method (IQR > 1.5 × Q1) for the computed variance columns.
- [X] T014c [P] [US2] Implement output formatting in `code/data/descriptors.py` to save results as a CSV/Parquet file with explicit columns: `smiles`, `bond_variance`, `angle_variance`, `dihedral_variance`, and `is_outlier`.
- [X] T015 [US2] Implement `code/data/analysis.py` to compute Pearson and Spearman correlations between **bond_variance, angle_variance, and dihedral_variance** and logPapp with p-values. **Requirement**: All three descriptors must be correlated and reported to satisfy SC-003.
- [X] T016 [US2] Implement Benjamini-Hochberg FDR correction in `code/data/analysis.py` for multiple hypothesis testing (q < 0.05).
- [X] T017 [US2] Write unit tests for conformer generation and variance calculation in `tests/test_descriptors.py`.
- [X] T018 [US2] Write unit tests for correlation and FDR logic in `tests/test_analysis.py`.

**Checkpoint**: Flexibility descriptors computed and correlations calculated; results stored in `data/processed/`.

---

## Phase 5: User Story 3 - Validate Model Performance and Generate Publication-Quality Visualizations (Priority: P3)

**Goal**: Build multivariate linear regression model with scaffold-based cross-validation, and generate visualizations.

**Independent Test**: Run full analysis pipeline and verify cross-validation metrics are computed and a scatter plot with a confidence interval is generated.

### Implementation for User Story 3

- [X] T019a [US3] Implement multivariate linear regression model in `code/data/analysis.py` using **bond_variance, angle_variance, and dihedral_variance** as predictors and confounders (logP, MW, PSA). **Requirement**: The model MUST utilize ALL flexibility descriptors computed in T013/T014. **Constraint**: Strictly adhere to FR-007 confounders: **logP, MW, PSA**. Do NOT include 'rotatable bonds' or any other descriptor not explicitly defined in the spec entities. If collinearity is detected (VIF > 5), apply Ridge regression or drop the least significant descriptor, but document the exclusion.
- [X] T019b [US3] Implement VIF (Variance Inflation Factor) diagnosis for predictor collinearity in `code/data/analysis.py`.
- [ ] T019c [US3] Implement Ridge regression fallback logic in `code/data/analysis.py` to handle collinearity when VIF > 5.
- [ ] T020 [US3] Implement scaffold-based cross-validation in `code/data/analysis.py` to assess generalizability. **Requirement**: Execute k-fold cross-validation as mandated by FR-007 and Constitution Principle VII. The output must include mean R², RMSE, and MAE across all folds.
- [ ] T022a [US3] Implement scatter plot logic in `code/data/visualize.py` to generate plots with regression line and % confidence interval. **Requirement**: Use `seaborn.regplot` to generate a scatter plot showing the flexibility-permeability relationship with a regression line and a confidence interval.
- [ ] T022b [P] [US3] Implement layout adjustments in `code/data/visualize.py` for publication quality (fonts, labels).
- [ ] T023a [US3] Update `code/data/visualize.py` and `code/data/analysis.py` plot titles to explicitly state "Associational Relationship" (not causal) as required by FR-009. **Verification**: Grep for "associational" in generated PNG metadata and code comments.
- [ ] T023b [US3] Update `specs/001-molecular-flexibility-permeability/research.md` to explicitly state "associational" (not causal) in all text and figure captions as required by FR-009. **Requirement**: `research.md` is defined in `plan.md` Project Structure. **Create the file if it does not exist** (even if T000 is incomplete). **Verification**: Grep for "associational" in research.md.
- [ ] T024 [US3] Write integration tests for the full analysis pipeline in `tests/test_analysis.py`. **Requirement**: Tests must run the full pipeline end-to-end to verify metrics as required by the spec's testing strategy.
- [ ] T025 [US3] Write contract tests for `analysis_output.schema.yaml` in `tests/contract/test_analysis.py`. **Requirement**: Tests must validate analysis output against the schema defined in T007.

**Checkpoint**: Model validated, visualizations generated, and research report ready.

---

## Phase 6: Scaling Analysis & Network Topology (Priority: P2 - Revised by Review)

**Goal**: Address Geoffrey West's review by investigating the scaling laws of transport relative to molecular complexity and membrane network density.

**Independent Test**: Compute scaling exponents for transport rates and verify if a power-law relationship (e.g., quarter-power) exists between flexibility metrics and permeability when controlling for network topology.

### Implementation for Scaling Analysis

- [ ] T026 [P] [US3-REV] Implement `code/data/scaling_analysis.py` to calculate molecular complexity metrics (e.g., molecular weight, number of rotatable bonds, graph diameter) and membrane network proxies (e.g., pore density estimates from literature or structural data if available, or surrogate metrics like logP as a proxy for membrane interaction complexity). **Requirement**: This task addresses the reviewer's concern about "landscape" and "network topology". If direct membrane network data is unavailable, use established surrogate metrics from literature (cite sources) and explicitly state the limitation. **Dependency**: T013 (descriptors) and T010 (preprocessed data).
- [ ] T027 [US3-REV] Implement power-law regression analysis in `code/data/scaling_analysis.py` to test the hypothesis: `log(Permeability) = alpha * log(Flexibility) + beta * log(Complexity) + epsilon`. **Requirement**: Compare linear, quadratic, and power-law models. Extract the scaling exponent `alpha`. **Dependency**: T026.
- [ ] T028 [US3-REV] Implement fractal dimension estimation or network topology metrics (if applicable) for the membrane model used in the study. **Requirement**: If the study assumes a specific membrane model (e.g., lipid bilayer), calculate its fractal dimension or porosity metrics to serve as the "network density" variable. If no specific model is used, document the assumption that the membrane is a homogeneous barrier and note this as a limitation. **Dependency**: T026.
- [ ] T029 [P] [US3-REV] Visualize the scaling relationship in `code/data/visualize.py` with a log-log plot of Permeability vs. Flexibility, colored by Complexity. **Requirement**: Overlay the fitted power-law line and report the R² of the scaling model. **Dependency**: T027.
- [ ] T030 [US3-REV] Update `specs/001-molecular-flexibility-permeability/research.md` to include the "Scaling Laws and Network Topology" section, discussing the findings from T026-T029. **Requirement**: Explicitly address the reviewer's question about whether the relationship is linear or follows a universal law (e.g., quarter-power). **Dependency**: T029.

**Checkpoint**: Scaling analysis complete, addressing the "landscape" and "network topology" concerns raised in the review.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Update `specs/001-molecular-flexibility-permeability/research.md` with final results, methodology justification, and explicit documentation of the "Computational Method Transparency" decision (RDKit vs PyVib) as required by Constitution Principle VI and Plan constraints. **Requirement**: **Create the file if it does not exist** (even if T000 is incomplete).
- [ ] T037 [P] Execute the script created in T006 (`code/utils/generate_transparency_report.py`) to generate the narrative section dynamically from the deviation record and execution logs.
- [ ] T038 [P] Update `specs/001-molecular-flexibility-permeability/plan.md` to reflect any deviations or confirmed constraints.
- [ ] T039 Refactor `code/data/analysis.py` to reduce cyclomatic complexity < 10.
- [ ] T040 [P] Run benchmark on a representative sample of molecules to verify total runtime estimate. **Requirement**: Execute the full pipeline on a **representative subset of molecules** and extrapolate to the full dataset using a **linear scaling formula** (runtime = base_time + (total_molecules / sample_size) * sample_time). **Enforcement Logic**: If estimated runtime > 6 hours:
 1. Log the estimated runtime and the current dataset size.
 2. Flag the project for **manual governance review** to determine if dataset sampling is required.
 3. Do NOT modify `plan.md` automatically.
 4. Do NOT reduce the dataset size without a formal governance update.
 **Pass Criteria**: Estimated runtime ≤ 6 hours or a documented flag for governance review.
- [ ] T041 Execute `quickstart.md` instructions end-to-end. **Requirement**: Verify `data/processed/descriptors.csv` exists with ≥450 rows. **Pass Criteria**: Script runs without errors and produces the expected output file.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Scaling Analysis (Phase 6)**: Depends on Foundational and US2 completion (requires descriptors and preprocessed data).
- **Phase N (Polish)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 results
- **Scaling Analysis (Phase 6)**: Can start after Foundational and US2 completion.
- **Phase N (Polish)**: Can start after Foundational (Phase 2) and US1/US2/US3/Scaling completion.

### Within Each User Story

- Models/Utilities before services
- Services before analysis
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT T006a and T006**. T006a is NOT parallel-safe with T006 if T006 requires the record, but T006 now handles missing records gracefully.
- Once Foundational phase completes, US1, US2, US3, and Scaling Analysis can start in parallel (if team capacity allows)
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
5. Add Scaling Analysis → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Flexibility & Correlation)
 - Developer C: User Story 3 (Model & Viz)
 - Developer D: Scaling Analysis (Network Topology)
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
- **Spec Deviation**: Conformer ensemble size is fixed per Plan.md to ensure CPU feasibility (DEV-001). Spec FR-003's 50 conformers is overridden by this approved deviation.
- **Model Scope**: The multivariate model (Ta) uses **bond, angle, and dihedral variances** as predictors, with confounders (logP, MW, PSA). Collinearity handling (VIF, Ridge) is documented.
- **Documentation**: Research narratives (T036, T037) must be generated dynamically from logs and deviation records via the script created in T006, not hardcoded.
- **SC-002 Threshold**: Conformer generation success rate is measured against a minimum threshold of **≥450 valid descriptors**.
- **Removed Scope**: Phase 6 (Scaling Analysis) has been **ADDED** to address the reviewer's concern about network topology and scaling laws, replacing the previous "Phase 6 (Scaling Analysis)" which was removed as scope creep. This new phase is now a core part of the research hypothesis.
- **Fixed Status Inconsistency**: T008 split into T008a (dirs) and T008b (code), both marked `[ ]` (active). T007 and T006a marked `[X]` (complete) to unblock dependents.
- **Cleaned Up Notes**: Removed all references to unauthorized scope creep.
- **Fixed Schema**: T006a now correctly defines `conformer_count` as an integer to resolve plan.md schema issues.
- **Fixed Paths**: All references to the state YAML now use the full project ID `PROJ-266-exploring-the-correlation-between-molecu`.
- **Reviewer Concern Addressed**: Phase 6 tasks (T026-T030) explicitly address the Geoffrey West review regarding "scaling laws", "network topology", and "fractal nature" of the membrane.

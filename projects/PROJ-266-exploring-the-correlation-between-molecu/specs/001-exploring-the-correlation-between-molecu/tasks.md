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

- [ ] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`)
- [X] T002 Initialize a Python project with `requirements.txt` (rdkit, pandas, scikit-learn, matplotlib, seaborn, requests, numpy, scipy)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils/config.py` for random seeds, paths, and constants
- [X] T005 [P] Implement `code/utils/logging.py` for standardized logging
- [X] T006a [US0] Create and initialize the spec deviation record in `state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml` with ID DEV-001. **Requirement**: This task MUST create the record from scratch (as none exists) with the correct YAML syntax. It must populate the fields: `id` ("DEV-001"), `spec_requirement` ("FR-003"), `rationale` ("CPU feasibility on GitHub Actions free-tier"), `impact_assessment` ("Potential loss of variance stability; mitigated by sensitivity analysis"), and `approved_by` ("Convergence Panel"). Do NOT attempt to read an existing file; create the file with valid YAML. **Dependency**: This task is NOT parallel-safe ([P] removed) and must complete before T006.
- [ ] T006 [US0] [Depends on T006a] Implement `code/utils/generate_transparency_report.py` script. **Requirement**: This script must be created now to generate the "Computational Method Transparency" section for `research.md` at execution time. The script reads the deviation record (`state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml`) created by T006a. **Error Handling**: The script MUST handle the case where the deviation record is missing or empty (e.g., if T006a hasn't run yet) by logging a warning and proceeding with default values or halting gracefully, rather than crashing. **Dependency**: This task depends on T006a completion to ensure the deviation record exists. Do NOT mark as [P].
- [ ] T007 Create base data schemas in `specs/001-molecular-flexibility-permeability/contracts/` (dataset.schema.yaml, analysis_output.schema.yaml)
- [ ] T007a [US0] Update `spec.md` to define SC-002 threshold. **Requirement**: Modify the Success Criteria section in `specs/001-molecular-flexibility-permeability/spec.md` to explicitly state: "Conformer generation success rate is measured against a minimum threshold of ≥450 valid descriptors." This makes SC-002 testable. **Dependency**: Must be completed before T013a.
- [ ] T008 [US0] Setup directory structure for `data/raw/` and `data/processed/` AND implement `code/utils/checksum.py`. **Requirement**: Create the necessary folders (`data/raw/`, `data/processed/`) AND implement the checksum utility code in `code/utils/checksum.py`. The utility MUST compute SHA-256 checksums for files in `data/` and update the `state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml` file with the new hashes. **Dependency**: T009 and T010 depend on this utility being present.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel. T008 provides the directory structure and checksum utility required by T009/T010 for data integrity.

---

## Phase 3: User Story 1 - Retrieve and Preprocess Caco-2 Permeability Dataset (Priority: P1) 🎯 MVP

**Goal**: Download raw Caco-2 data from ChEMBL, filter for valid records, and ensure data completeness.

**Independent Test**: Execute retrieval script and verify output contains ≥500 valid records with non-NULL SMILES and logPapp from a raw batch of ≥600.

### Implementation for User Story 1

- [X] T009 [US1] Implement `code/data/retrieval.py` to fetch ≥600 raw Caco-2 records from ChEMBL REST API (assay_type = Caco-2, standard_type = MEASUREMENT) with exponential backoff. **Requirement**: After saving the raw CSV, this task MUST invoke `code/utils/checksum.py` to generate a checksum and register it in `state/projects/PROJ-<ID>-exploring-the-correlation-between-molecu.yaml`. **Dependency**: T008 must be complete.
- [X] T010 [US1] Implement `code/data/preprocessing.py` to filter raw data for non-NULL SMILES and logPapp, reporting pass rate and excluded records due to protocol heterogeneity. **Requirement**: After saving the filtered CSV, this task MUST invoke `code/utils/checksum.py` to generate a checksum and register it in `state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml`. **Dependency**: T008 must be complete.
- [ ] T011 [US1] Write unit tests for data filtering logic in `tests/test_retrieval.py`. **Requirement**: Tests must verify filtering logic and pass rate calculation. **Dependency**: T007 (schemas) must be complete.
- [ ] T012 [US1] Write contract tests against `dataset.schema.yaml` in `tests/contract/test_dataset.py`. **Requirement**: Tests must validate data against the schema defined in T007. **Dependency**: T007 (schemas) must be complete.

**Checkpoint**: Raw data downloaded and validated; ≥500 records ready for analysis.

---

## Phase 4: User Story 2 - Compute Molecular Flexibility Descriptors and Correlate with Permeability (Priority: P2)

**Goal**: Generate 3D conformer ensembles, calculate torsional variance, and compute statistical correlations.

**Independent Test**: Process a sample of 50 molecules and verify ≥450 valid flexibility descriptors are computed and at least one correlation coefficient is produced with p-values.

### Implementation for User Story 2

- [X] T013a [US2] Implement `code/data/descriptors.py` to generate 3D conformer ensembles using RDKit. **Requirement**: Generate 20 conformers per molecule as per Plan.md Deviation ID: **DEV-001** (overriding Spec FR-003's 50 due to CPU feasibility). **Traceability**: Explicitly reference Deviation ID **DEV-001** from `plan.md` in code comments and logs. **Dependency**: This task assumes the deviation record created in T006a exists. **Note**: This task implements the ADAPTED requirement (20 conformers) documented in DEV-001, not the original Spec FR-003 (50 conformers).
- [X] T013b [US2] Implement random sampling strategy in `code/data/descriptors.py` to select molecules if the dataset exceeds memory limits. **Requirement**: Use a fixed random seed for deterministic, unbiased sampling (e.g., `numpy.random.seed(...)` and `numpy.random.choice`). **Constraint**: The output must contain ≥450 valid descriptors. The sampling rule (which split, how many rows, seed) must be logged.
- [X] T013c [US2] Implement error handling and logging in `code/data/descriptors.py` for conformer generation failures. **Requirement**: Log any molecule where conformer generation fails (e.g., stereochemistry issues) and skip it. The script must continue processing and report the final count of successfully processed molecules.
- [X] T014a [US2] Implement torsional variance calculation for **bond, angle, AND dihedral** (in rad²) in `code/data/descriptors.py`. **Requirement**: Compute ALL three variances as primary flexibility descriptors per FR-004. The output must include columns for `bond_variance`, `angle_variance`, and `dihedral_variance`. **Note**: All three are required for SC-003 completeness reporting.
- [X] T014b [P] [US2] Implement outlier flagging logic in `code/data/descriptors.py` using the interquartile range method (IQR > 1.5 × Q1) for the computed variance columns.
- [X] T014c [P] [US2] Implement output formatting in `code/data/descriptors.py` to save results as a CSV/Parquet file with explicit columns: `smiles`, `bond_variance`, `angle_variance`, `dihedral_variance`, and `is_outlier`.
- [X] T015 [US2] Implement `code/data/analysis.py` to compute Pearson and Spearman correlations between **bond_variance, angle_variance, and dihedral_variance** and logPapp with p-values. **Requirement**: All three descriptors must be correlated and reported to satisfy SC-003.
- [X] T016 [US2] Implement Benjamini-Hochberg FDR correction in `code/data/analysis.py` for multiple hypothesis testing (q < 0.05).
- [ ] T017 [US2] Write unit tests for conformer generation and variance calculation in `tests/test_descriptors.py`.
- [ ] T018 [US2] Write unit tests for correlation and FDR logic in `tests/test_analysis.py`.

**Checkpoint**: Flexibility descriptors computed and correlations calculated; results stored in `data/processed/`.

---

## Phase 5: User Story 3 - Validate Model Performance and Generate Publication-Quality Visualizations (Priority: P3)

**Goal**: Build multivariate linear regression model with scaffold-based cross-validation, and generate visualizations.

**Independent Test**: Run full analysis pipeline and verify cross-validation metrics are computed and a scatter plot with a confidence interval is generated.

### Implementation for User Story 3

- [X] T019a [US3] Implement multivariate linear regression model in `code/data/analysis.py` using **bond_variance, angle_variance, and dihedral_variance** as predictors and confounders (logP, MW, PSA). **Requirement**: The model MUST utilize ALL flexibility descriptors computed in T013/T014. **Constraint**: Strictly adhere to FR-007 confounders: **logP, MW, PSA**. Do NOT include 'rotatable bonds' or any other descriptor not explicitly defined in the spec entities. If collinearity is detected (VIF > 5), apply Ridge regression or drop the least significant descriptor, but document the exclusion.
- [X] T019b [US3] Implement VIF (Variance Inflation Factor) diagnosis for predictor collinearity in `code/data/analysis.py`.
- [X] T019c [US3] Implement Ridge regression fallback logic in `code/data/analysis.py` to handle collinearity when VIF > 5.
- [ ] T020 [US3] Implement scaffold-based cross-validation in `code/data/analysis.py` to assess generalizability. **Requirement**: Execute k-fold cross-validation as mandated by FR-007 and Constitution Principle VII. The output must include mean R², RMSE, and MAE across all folds.
- [ ] T022a [US3] Implement scatter plot logic in `code/data/visualize.py` to generate plots with regression line and 95% confidence interval. **Requirement**: Use `seaborn.regplot` to generate a scatter plot showing the flexibility-permeability relationship with a regression line and a confidence interval. Save as PNG with metadata dpi ≥ 300.
- [ ] T022b [P] [US3] Implement layout adjustments in `code/data/visualize.py` for publication quality (fonts, labels).
- [ ] T023a [US3] Update `code/data/visualize.py` and `code/data/analysis.py` plot titles to explicitly state "Associational Relationship" (not causal) as required by FR-009. **Verification**: Grep for "associational" in generated PNG metadata and code comments.
- [ ] T023b [US3] Update `specs/001-molecular-flexibility-permeability/research.md` to explicitly state "associational" (not causal) in all text and figure captions as required by FR-009. **Verification**: Grep for "associational" in research.md.
- [ ] T024 [US3] Write integration tests for the full analysis pipeline in `tests/test_analysis.py`. **Requirement**: Tests must run the full pipeline end-to-end to verify metrics as required by the spec's testing strategy.
- [ ] T025 [US3] Write contract tests for `analysis_output.schema.yaml` in `tests/contract/test_analysis.py`. **Requirement**: Tests must validate analysis output against the schema defined in T007.

**Checkpoint**: Model validated, visualizations generated, and research report ready.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T027a [P] Update `specs/001-molecular-flexibility-permeability/research.md` with final results, methodology justification, and explicit documentation of the "Computational Method Transparency" decision (RDKit vs PyVib) as required by Constitution Principle VI and Plan constraints.
- [ ] T027b [P] Execute the script created in T006 (`code/utils/generate_transparency_report.py`) to generate the narrative section dynamically from the deviation record and execution logs.
- [ ] T027c [P] Update `specs/001-molecular-flexibility-permeability/plan.md` to reflect any deviations or confirmed constraints.
- [ ] T028 Refactor `code/data/analysis.py` to reduce cyclomatic complexity < 10.
- [ ] T029 [P] Run benchmark on a representative sample of molecules to verify total runtime estimate. **Requirement**: Execute the full pipeline on a representative subset of molecules and extrapolate to the full dataset. **Enforcement Logic**: If estimated runtime > 6 hours:
 1. Log the estimated runtime and the current dataset size.
 2. Flag the project for **manual governance review** to determine if dataset sampling is required.
 3. Do NOT modify `plan.md` automatically.
 4. Do NOT reduce the dataset size without a formal governance update.
 **Pass Criteria**: Estimated runtime ≤ 6 hours or a documented flag for governance review.
- [ ] T030 Execute `quickstart.md` instructions end-to-end. **Requirement**: Verify `data/processed/descriptors.csv` exists with ≥450 rows. **Pass Criteria**: Script runs without errors and produces the expected output file.

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
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT T006a and T006**. T006a must complete before T006. T006a is NOT parallel-safe with T006.
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
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Crucial**: All tasks must run on free CPU-only CI with limited CPU resources, constrained RAM, and no GPU. No 8-bit/4-bit quantization or large model training.
- **Data Integrity**: All data must be real (ChEMBL API) or fetched via verified Python packages. No synthetic/fake data generation.
- **Spec Deviation**: Conformer ensemble size is fixed per Plan.md to ensure CPU feasibility (DEV-001). Spec FR-003's 50 conformers is overridden by this approved deviation.
- **Model Scope**: The multivariate model (T019a) uses **bond, angle, and dihedral variances** as predictors, with confounders (logP, MW, PSA). Collinearity handling (VIF, Ridge) is documented.
- **Documentation**: Research narratives (T027a, T027b) must be generated dynamically from logs and deviation records via the script created in T006, not hardcoded.
- **Removed Scope**: Phase 5b (Scaling Analysis) has been removed as it was not authorized by spec.md or plan.md. This resolves the scope creep violation.
- **Reviewer Response**: Addressed panel concerns regarding:
 1. Removed unapproved Phase 5b (Scaling Analysis) entirely.
 2. Restored T006a to explicitly CREATE the DEV-001 record (Conformer size reduction) before T006 reads it, and removed [P] tag to ensure ordering.
 3. Clarified T013a to explicitly reference Deviation ID DEV-001.
 4. Enhanced T029 to remove dynamic plan.md modification and flag for governance review.
 5. Removed 'rotatable bonds' from T019a confounder list.
 6. Fixed contradictory 'Removed Scope' notes.
 7. Clarified dependency ordering for T006/T006a and added explicit '[Depends on T006a]' in task header and updated 'Parallel Opportunities' section.
 8. Merged T008 and T008a into a single task T008 to ensure atomic data hygiene.
 9. Marked T020, T022a, T023a, T023b, T024, T025 as [ ] (active/incomplete) to satisfy FR/SC requirements.
 10. Updated T009/T010 to explicitly mandate checksumming and state registration.
 11. Updated T014a to compute ALL three variances (bond, angle, dihedral) and T015/T019a to use all three in analysis.
 12. Changed T001, T003, T007, T008 status from [X] to [ ] to reflect missing artifacts (Draft state).
 13. Added T007a to update spec.md to define SC-002 threshold as ≥450 valid descriptors.
 14. Removed [P] tag from T011 and T012 to correctly reflect dependency on T007.
 15. Replaced broken placeholder in T022a with concrete visualization requirements (seaborn.regplot).
 16. Explicitly marked T006 as dependent on T006a in the task line to prevent parallel execution.
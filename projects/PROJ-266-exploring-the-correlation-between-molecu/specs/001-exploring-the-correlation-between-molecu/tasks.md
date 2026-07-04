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
  
  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (rdkit, pandas, scikit-learn, matplotlib, seaborn, requests, numpy, scipy)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/utils/config.py` for random seeds, paths, and constants
- [ ] T005 [P] Implement `code/utils/logging.py` for standardized logging
- [ ] T006 [P] Implement `code/utils/versioning.py` for state file updates (Principle V). **Requirement**: Document the "Computational Method Transparency" decision in `research.md` with the exact text: "Plan explicitly rejects Normal Mode Analysis (PyVib) in favor of RDKit geometric proxies for CPU feasibility, as documented in the Technical Context."
- [ ] T007 Create base data schemas in `specs/001-molecular-flexibility-permeability/contracts/` (dataset.schema.yaml, analysis_output.schema.yaml)
- [ ] T008 Setup directory structure for `data/raw/` and `data/processed/` with checksum generation utility

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Retrieve and Preprocess Caco-2 Permeability Dataset (Priority: P1) 🎯 MVP

**Goal**: Download raw Caco-2 data from ChEMBL, filter for valid records, and ensure data completeness.

**Independent Test**: Execute retrieval script and verify output contains ≥500 valid records with non-NULL SMILES and logPapp from a raw batch of ≥600.

### Implementation for User Story 1

- [ ] T009 [US1] Implement `code/data/retrieval.py` to fetch ≥600 raw Caco-2 records from ChEMBL REST API (assay_type = Caco-2, standard_type = MEASUREMENT) with exponential backoff
- [ ] T010 [US1] Implement `code/data/preprocessing.py` to filter raw data for non-NULL SMILES and logPapp, reporting pass rate and excluded records due to protocol heterogeneity
- [ ] T011 [P] [US1] Write unit tests for data filtering logic in `tests/test_retrieval.py`
- [ ] T012 [P] [US1] Write contract tests against `dataset.schema.yaml` in `tests/contract/test_dataset.py`

**Checkpoint**: Raw data downloaded and validated; ≥500 records ready for analysis.

---

## Phase 4: User Story 2 - Compute Molecular Flexibility Descriptors and Correlate with Permeability (Priority: P2)

**Goal**: Generate 3D conformer ensembles, calculate torsional variance, and compute statistical correlations.

**Independent Test**: Process a sample of 50 molecules and verify ≥450 valid flexibility descriptors are computed and at least one correlation coefficient is produced with p-values.

### Implementation for User Story 2

- [ ] T013 [US2] Implement `code/data/descriptors.py` to generate 3D conformer ensembles using RDKit. **Requirement**: Must generate ≥ 50 conformers per molecule as per FR-003. **Constraint Override**: This task overrides the plan's previous "20 conformers" constraint; the spec's requirement of ≥50 is mandatory. **Resource Management**: If RAM usage exceeds a high threshold during batch processing, the script MUST reduce the input dataset size (N) by removing molecules with the highest molecular weight. (to minimize memory footprint) and retry, ensuring ≥50 conformers are generated for every remaining molecule. The task fails only if N drops below a critical threshold after downsampling.
- [ ] T013b [P] [US2] Implement resource management logic in `code/data/descriptors.py` to handle memory constraints. **Logic**: If RAM > 6GB, reduce the input dataset size (N) by removing heaviest molecules and retry. **Failure Condition**: If downsampling reduces N below 450 molecules, log a critical error and fail the task, as this violates FR-003 (≥450 molecules with ≥50 conformers).
- [ ] T014a [US2] Implement torsional variance calculation for **bond, angle, and dihedral** (in rad²) in `code/data/descriptors.py`. **Requirement**: Compute ALL three variance components as mandated by FR-004. **Note**: While dihedral variance is the primary predictor for the regression model (FR-007), bond and angle variances are REQUIRED outputs for dataset completeness per FR-004 and will be stored in the output file, but only dihedral_variance is used as the primary predictor in T019.
- [ ] T014b [P] [US2] Implement outlier flagging logic in `code/data/descriptors.py` using the interquartile range method (IQR > 1.5 × Q1) for the computed variance columns.
- [ ] T014c [P] [US2] Implement output formatting in `code/data/descriptors.py` to save results as a CSV/Parquet file with explicit columns: `smiles`, `bond_variance`, `angle_variance`, `dihedral_variance` (primary), and `is_outlier`.
- [ ] T015 [US2] Implement `code/data/analysis.py` to compute Pearson and Spearman correlations between **each** flexibility descriptor (bond, angle, dihedral) and logPapp with p-values. **Note**: All three correlations are computed for completeness, but the primary hypothesis focuses on dihedral_variance.
- [ ] T016 [US2] Implement Benjamini-Hochberg FDR correction in `code/data/analysis.py` for multiple hypothesis testing (q < 0.05).
- [ ] T017 [P] [US2] Write unit tests for conformer generation and variance calculation in `tests/test_descriptors.py`.
- [ ] T018 [P] [US2] Write unit tests for correlation and FDR logic in `tests/test_analysis.py`.

**Checkpoint**: Flexibility descriptors computed and correlations calculated; results stored in `data/processed/`.

---

## Phase 5: User Story 3 - Validate Model Performance and Generate Publication-Quality Visualizations (Priority: P3)

**Goal**: Build multivariate linear regression model with scaffold-based cross-validation and generate visualizations.

**Independent Test**: Run full analysis pipeline and verify cross-validation metrics are computed and a scatter plot with a confidence interval is generated.

### Implementation for User Story 3

- [ ] T019 [US3] Implement multivariate linear regression model in `code/data/analysis.py` using the **dihedral_variance** descriptor as the primary predictor and confounders (logP, MW, PSA, rotatable bonds). **Clarification**: Although T014a computes bond and angle variances for dataset completeness (FR-004), this model specifically uses only `dihedral_variance` as the flexibility predictor, aligning with the Plan's summary focus on dihedral angles as the primary metric. Bond and angle variances are excluded from this specific regression model but remain available for exploratory analysis.
- [ ] T020 [US3] Implement scaffold-based cross-validation in `code/data/analysis.py` to assess generalizability.
- [ ] T021 [US3] Implement VIF (Variance Inflation Factor) diagnosis for predictor collinearity in `code/data/analysis.py`.
- [ ] T022a [US3] Implement scatter plot logic in `code/data/analysis.py` to generate plots with regression line and confidence interval.
- [ ] T022b [P] [US3] Implement output formatting in `code/data/analysis.py` to save the scatter plot as PNG with metadata dpi ≥ 300.
- [ ] T023 [US3] Ensure all outputs explicitly state "associational" (not causal) in documentation and plot titles (FR-009).
- [ ] T024 [P] [US3] Write integration tests for the full analysis pipeline in `tests/test_analysis.py`.
- [ ] T025 [P] [US3] Write contract tests for `analysis_output.schema.yaml` in `tests/contract/test_analysis.py`.

**Checkpoint**: Model validated, visualizations generated, and research report ready.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Update `specs/001-molecular-flexibility-permeability/research.md` with final results, methodology justification, and explicit documentation of the "Computational Method Transparency" decision (RDKit vs PyVib) as required by Constitution Principle VI and Plan constraints.
- [ ] T034 [P] Update `specs/001-molecular-flexibility-permeability/plan.md` to reflect any deviations or confirmed constraints.
- [ ] T035 Refactor `code/data/analysis.py` to reduce cyclomatic complexity < 10.
- [ ] T036 Optimize `code/data/descriptors.py` to ensure total runtime ≤ 6 hours on CPU-only runner.
- [ ] T037 Run `quickstart.md` validation.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Phase N (Polish)**: Depends on all desired user stories being complete

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
   - Developer A: User Story 1
   - Developer B: User Story 2 (Flexibility & Correlation)
   - Developer C: User Story 3 (Model & Viz)
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
- **Crucial**: All tasks must run on free CPU-only CI with limited CPU resources, constrained RAM, and no GPU. No 8-bit/4-bit quantization or large model training.
- **Data Integrity**: All data must be real (ChEMBL API) or fetched via verified Python packages. No synthetic/fake data generation.
- **Scope**: Phase 6 (Scaling Law Analysis) has been explicitly removed from this project scope. The scope is strictly limited to the flexibility vs. permeability correlation as defined in spec.md. Any work related to "Scaling Law Analysis" or "membrane network topology" is out of scope and not approved. Tasks T026-T032 (previously referenced in concerns) have been permanently removed and do not exist in this artifact.
- **Reviewer Concern Addressed**: The contradiction between spec.md (size ≥ 50) and plan.md (size 20) in T013 is resolved by enforcing the spec's requirement (≥50) as mandatory. The plan's constraint is overridden by the spec. Memory constraints are handled by downsampling the dataset (N) via T013b, NOT by reducing the ensemble size. If N < 450, the task fails.
- **Clarity**: T014 and T019 now clearly distinguish between the mandatory outputs (bond, angle, dihedral variances for dataset completeness) and the primary predictor used in the regression model (dihedral_variance only). T015 computes correlations for all three, but T019 specifically uses dihedral_variance as the primary predictor, aligning with the Plan's focus on dihedral angles.
- **Feasibility**: T013 explicitly implements a fallback strategy to reduce N (molecule count) if RAM exceeds 6GB, ensuring the spec's ≥50 conformers requirement is always met for the remaining molecules.
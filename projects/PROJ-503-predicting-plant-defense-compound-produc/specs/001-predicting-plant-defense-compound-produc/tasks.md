# Tasks: Predicting Plant Defense Compound Production from Publicly Available Genomic and Transcriptomic Data

**Input**: Design documents from `/specs/001-predict-plant-defense/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: User story tests are REQUIRED per spec.md Independent Test requirements.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Full repo paths**: All paths MUST use full repository path: `projects/PROJ-503-predicting-plant-defense-compound-produc/`
- **Never use relative paths**: Do NOT use `code/`, `tests/`, `logs/` without the full repo prefix
- **Example**: `projects/PROJ-503-predicting-plant-defense-compound-produc/code/data_download.py`

<!--
 ============================================================================
 IMPORTANT: The tasks below are generated based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure with exact directories: `projects/PROJ-503-predicting-plant-defense-compound-produc/code/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/data/raw/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/data/processed/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/data/paired/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/outputs/models/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/integration/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/unit/`

- [X] T002 Initialize Python 3.11 project with requirements.txt at `projects/PROJ-503-predicting-plant-defense-compound-produc/code/requirements.txt` (pandas, numpy, scikit-learn, scipy, requests, pyyaml, biopython, statsmodels, pytest)

- [ ] T003 [P] Configure linting and formatting: Create `projects/PROJ-503-predicting-plant-defense-compound-produc/.flake8` and `projects/PROJ-503-predicting-plant-defense-compound-produc/pyproject.toml` with black configuration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement logging logic: Create utility functions to write to `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/data_pairing.json` (on mismatch) and `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/feature_filtering.csv` (on zero-variance filter) per spec.md edge cases

- [X] T005 [P] Setup environment configuration management: Create `projects/PROJ-503-predicting-plant-defense-compound-produc/data/sources.yaml` for dataset version traceability

- [ ] T006 [P] Create base data model classes (ExpressionMatrix, MetaboliteMatrix, FeatureSet, ModelArtifact) in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/models/`

- [ ] T007 Implement error handling framework with E-DATASET, E-PAIRING, E-TIMEOUT, and E-POWER error codes per plan.md (Note: E-POWER is required for power analysis failures)

- [X] T008 Setup CI resource monitoring: Implement runtime timer in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/main.py` that logs elapsed CPU time and raises E-TIMEOUT if >4h per FR-008

- [ ] T009 Create power analysis utility for Phase 0: Implement calculation for effect size r=0.5, alpha=0.05, power=0.8; output JSON summary of required n to `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/power_analysis.json`. **MUST abort with E-POWER if n < 28** per plan.md Phase 0 T009 and T015.

- [ ] T010 [P] Create SHA-256 checksum validation utility for data integrity (SC-004)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 0: Data Discovery (MANDATORY BLOCKER)

**Purpose**: Verify dataset availability before proceeding to Phase 1

**⚠️ ABORT CRITERIA**: If no verified plant omics datasets with ≥95% pairing (or sufficient condition-level fallback), project halts with E-DATASET

- [X] T011 [P] [US1] Search GEO for Arabidopsis herbivore-stress series with explicit treatment annotations (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/data_download.py`)

- [X] T012 [P] [US1] Search GEO for Solanum herbivore-stress series with explicit treatment annotations (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/data_download.py`)

- [~] T013 [P] [US1] Search Metabolomics Workbench for defense metabolite experiments (terpenoids, alkaloids, phenylpropanoids)

- [~] T014 [US1] Verify sample-level pairing feasibility (≥95% match rate per FR-009) using metadata comparison <!-- ATOMIZE: requested -->

- [~] T015 [US1] Run power analysis utility (T009) to log required sample size (n) for r=0.5; **ABORT with E-POWER if n < 28** (Plan T009/T015, FR-009). If n >= 28, proceed to T016.

- [~] T016 [US1] Document verified dataset sources in `projects/PROJ-503-predicting-plant-defense-compound-produc/data/sources.yaml` with accession IDs + version/release date (VI. Dataset Version Traceability)

- [~] T016b [US1] Implement fallback to condition-level aggregation if sample-level pairing <95% but condition-level aggregation yields sufficient n (Plan T016 mitigation strategy). **MUST log a warning and proceed ONLY if aggregated n >= 28; otherwise ABORT with E-PAIRING.**

- [~] T017 [US1] Create research.md with dataset citations and availability status for Phase 0

**Checkpoint**: Phase 0 complete - datasets verified OR project aborted with E-DATASET

---

## Phase 3: User Story 1 - End‑to‑end data acquisition & pairing (Priority: P1) 🎯 MVP

**Goal**: Obtain paired dataset of gene‑expression profiles and defense‑metabolite concentrations for Arabidopsis and Solanum samples under herbivore stress

**Independent Test**: Run the data‑download module on specified GEO series IDs and Metabolomics Workbench experiment IDs and verify that every expression sample has a matching metabolite record from the same biological sample.

### Tests for User Story 1 (REQUIRED per spec.md Independent Test) ⚠️

- [X] T018 [P] [US1] Contract test for GEO download in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/test_geo_download.py`
- [X] T019 [P] [US1] Contract test for Metabolomics Workbench download in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/test_metabolomics_download.py`
- [X] T020 [P] [US1] Integration test for end-to-end data pairing in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/integration/test_data_pairing.py`

### Implementation for User Story 1

- [X] T021 [P] [US1] Implement GEO expression matrix downloader in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/data_download.py` (FR-001) <!-- FAILED: unspecified -->
- [X] T022 [P] [US1] Implement Metabolomics Workbench metabolite retriever in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/data_download.py` (FR-002)
- [~] T023 [US1] Implement sample-level pairing logic using biological sample identifiers (not condition IDs alone) (FR-002)
- [~] T027 [US1] Implement validation to halt with E-PAIRING if <95% samples have matched pairs (FR-009, SC-005). **MUST precede T024/T025. If T016b fallback was triggered, this task validates the aggregated pairing rate.**
- [~] T024 [US1] Create expression CSV with normalized TPM/FPKM values for each sample. Rule: Prefer TPM; if missing, calculate from raw counts using standard formula. If neither available, log error and skip sample (US-1 acceptance scenario 1). **Conditional on T027 passing.**
- [ ] T025 [US1] Create metabolite CSV with log‑transformed concentrations aligned by experimental sample identifier (US-1 acceptance scenario 2). **Conditional on T027 passing.**
- [ ] T026 [US1] Log mismatches to `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/data_pairing.json` with fields {sample_id, expression_source, metabolite_source, reason: "no_sample_level_pair"} (edge case handling)
- [ ] T028 [US1] Verify downloaded files match expected SHA-256 checksums for ≥99% of requested IDs (SC-004)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Feature selection & preprocessing (Priority: P2)

**Goal**: Isolate expression features belonging to known defense‑biosynthetic pathways and ensure both expression and metabolite matrices are properly normalized before modelling

**Independent Test**: Execute the feature‑selection module and confirm that the resulting feature matrix contains only genes whose KEGG IDs map to terpenoid, alkaloid, or phenylpropanoid pathways.

### Tests for User Story 2 (REQUIRED per spec.md Independent Test) ⚠️

- [ ] T029 [P] [US2] Contract test for KEGG pathway mapping in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/test_kegg_mapping.py`
- [ ] T030 [P] [US2] Integration test for feature selection pipeline in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/integration/test_feature_selection.py`

### Implementation for User Story 2

- [ ] T031 [P] [US2] Implement expression normalization to TPM/FPKM in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py` (FR-003)
- [ ] T032 [P] [US2] Implement metabolite log‑transformation in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py` (FR-003)
- [ ] T035 [US2] Implement KEGG pathway ID mapping for defense biosynthetic genes (terpenoid, alkaloid, phenylpropanoid) (FR-004)
- [ ] T036 [US2] Create FeatureSet output matrix containing only pathway-mapped genes (US-2 acceptance scenario 1)
- [ ] T035b [US2] **Mandatory PCA**: If features (p) > 2 * samples (n), reduce to top components. Log components to `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/pca_summary.csv` (Plan T025).
- [ ] T033 [US2] Implement zero‑variance gene filtering (variance < 1e-10) in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py` (FR-003)
- [ ] T034 [US2] Log zero-variance genes to `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/feature_filtering.csv` with columns gene_id, variance, reason: "zero_variance" (edge case handling)
- [ ] T037 [US2] Implement ortholog fallback for unannotated Solanum genes using Arabidopsis reference (≥60% sequence identity) (edge case handling)
- [ ] T038 [US2] Document ortholog substitutions in `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/edge_cases.md` with original gene ID, substituted gene ID, and sequence identity percentage
- [ ] T039 [US2] Verify ≥75% of known defense pathway genes retained per species (SC-006)
- [ ] T040 [US2] Implement species-specific z-score normalization in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py` (FR-010) **After T036**
- [ ] T041 [US2] Implement ComBat batch correction for cross-species expression scale differences (FR-010)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive modelling & evaluation (Priority: P3)

**Goal**: Train a Ridge Regression model to predict defense‑metabolite abundance from the selected gene‑expression features and assess performance using cross‑validation and permutation testing

**Independent Test**: Run the modelling script on the paired dataset and verify that it reports RMSE, Pearson r, and a permutation‑test p‑value for each metabolite.

### Tests for User Story 3 (REQUIRED per spec.md Independent Test) ⚠️

- [ ] T042 [P] [US3] Contract test for Ridge Regression model training in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/test_ridge_model.py`
- [ ] T043 [P] [US3] Contract test for permutation testing in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/test_permutation_test.py`
- [ ] T044 [P] [US3] Integration test for end-to-end modeling pipeline in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/integration/test_modeling_pipeline.py`

### Implementation for User Story 3

- [ ] T045 [P] [US3] Implement species-specific Ridge Regression model training **with k-fold cross-validation** in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/modeling.py` (FR-005)
- [ ] T045b [US3] Implement outer k-fold cross-validation split with constraint of maintaining paired samples (Plan T031).
- [ ] T046 [US3] Implement inner cross-validation to select Ridge alpha (grid search) within each outer fold (Plan T032).
- [ ] T047 [US3] Implement permutation test with 1 000 iterations in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/evaluation.py` (FR-006). **Depends on T045**.
- [ ] T048 [US3] Report two‑sided p‑value ≤ 0.05 for metabolites showing true predictive signal (US-3 acceptance scenario 2) (FR-006)
- [ ] T049 [US3] Apply Bonferroni correction across all metabolites tested (FR-007)
- [ ] T050 [US3] Verify Pearson r ≥ 0.5 for metabolite with highest correlation across 5‑fold CV (SC-001)
- [ ] T051 [US3] Verify permutation-test p‑value ≤ 0.05 after Bonferroni correction for highest-correlation metabolite (SC-002)
- [ ] T052 [US3] Log runtime and resource usage; abort if CPU time exceeds a predefined computational budget (FR-008)
- [ ] T053 [US3] Serialize ModelArtifact (coefficients and evaluation metrics) to `projects/PROJ-503-predicting-plant-defense-compound-produc/outputs/models/`
- [ ] T054 [US3] Implement VIF collinearity diagnostics and create `projects/PROJ-503-predicting-plant-defense-compound-produc/outputs/vif_diagnostics.csv` with columns gene_id, vif_score, threshold_exceeded (multicollinearity handling assumption)
- [ ] T055 [US3] Create exploratory cross-species model: Create `projects/PROJ-503-predicting-plant-defense-compound-produc/outputs/models/cross_species_model.pkl` **only if paired samples ≥50**; otherwise log E-SAMPLESIZE. (FR-010, Plan T039)
- [ ] T056 [US3] **Mandatory**: Evaluate species‑holdout generalization (train on A, test on S; train on S, test on A). If holdout fails, discard cross-species model. (Plan T040)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T057a [P] Create `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/quickstart.md` with E2E pipeline instructions
- [ ] T057b [P] Update `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/data-model.md` with schema definitions for ExpressionMatrix, MetaboliteMatrix, FeatureSet, ModelArtifact
- [ ] T057c [P] Create `projects/PROJ-503-predicting-plant-defense-compound-produc/contracts/` directory with module specifications

- [ ] T058 Code cleanup and refactoring: Run `black --check` and `flake8`; fix all violations; document changes in `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/refactoring_log.md`

- [ ] T059 Performance optimization: Profile pipeline with cProfile; identify bottlenecks; optimize data loading and model training; verify E2E runtime <4h in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/integration/test_e2e_runtime.py` (SC-003)

- [ ] T060 [P] Create unit tests with ≥80% line coverage: `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/unit/test_data_download.py`, `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/unit/test_preprocessing.py`, `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/unit/test_modeling.py`

- [ ] T061 Security hardening: Run pip-audit or safety check; create `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/security_report.md` with vulnerability findings and remediation status

- [ ] T062 Run quickstart.md validation: Execute quickstart.md instructions on fresh environment; verify all steps complete without error; document in `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/quickstart_validation.md`

- [ ] T065 Verify all assumptions in spec.md have deferred citations resolved: Parse spec.md assumptions for [deferred: citation required] markers; confirm each has corresponding entry in research.md with verified URL; create `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/assumption_resolution_log.md`

- [ ] T066 [Plan Update] Update plan.md Constitution Check: Add explicit verification steps for Principles I, II, VI to transition from PENDING VERIFICATION to PASS status

- [ ] T067 [Spec Update] Update spec.md Assumptions: Change power analysis from [deferred] to Phase 0 mandatory blocker (n≥28-30 samples) per plan.md

- [ ] T068 [Spec Update] Update spec.md FR-010: Change cross-species model from primary to exploratory-only per plan.md Complexity Tracking note

- [ ] T069 [Plan Update] Update plan.md Constitution Check: Add explicit task mapping for Principle VII (Statistical Validation) to tasks T047, T048, T049

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Phase 0 Data Discovery**: Must complete BEFORE Phase 1 (Data Acquisition) - MANDATORY BLOCKER
- **User Stories (Phase 3+)**: All depend on Foundational phase completion AND Phase 0 verification
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) AND Phase 0 verification - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (data/processed/, data/paired/)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data output AND US2 feature selection output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Phase 0 tasks T011-T013 can run in parallel (GEO search, Metabolomics search, power analysis)
- Once Foundational phase and Phase 0 complete, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for GEO download in projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/test_geo_download.py"
Task: "Contract test for Metabolomics Workbench download in projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/test_metabolomics_download.py"
Task: "Integration test for end-to-end data pairing in projects/PROJ-503-predicting-plant-defense-compound-produc/tests/integration/test_data_pairing.py"

# Launch all download tasks for User Story 1 together:
Task: "Implement GEO expression matrix downloader in projects/PROJ-503-predicting-plant-defense-compound-produc/code/data_download.py (FR-001)"
Task: "Implement Metabolomics Workbench metabolite retriever in projects/PROJ-503-predicting-plant-defense-compound-produc/code/data_download.py (FR-002)"
```

---

## Parallel Example: User Story 2

```bash
# Launch preprocessing tasks in parallel:
Task: "Implement expression normalization to TPM/FPKM in projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py (FR-003)"
Task: "Implement metabolite log‑transformation in projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py (FR-003)"
Task: "Implement zero‑variance gene filtering (variance < 1e-10) in projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py (FR-003)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 0: Data Discovery (MANDATORY BLOCKER - verify datasets)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Complete Phase 0 → Datasets verified OR project aborted
3. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done AND Phase 0 verifies datasets:
 - Developer A: User Story 1 (data acquisition)
 - Developer B: User Story 2 (preprocessing & feature selection)
 - Developer C: User Story 3 (modeling & evaluation)
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
- **CRITICAL**: Phase 0 Data Discovery MUST complete successfully before any data acquisition tasks (T021-T028) can proceed
- **CRITICAL**: All tasks must run on free CPU-only CI (2 CPU cores, ~7 GB RAM, ~14 GB disk, NO GPU, ≤4 hours) per FR-008 and SC-003
- **CRITICAL**: Do NOT use 8-bit/4-bit quantization, CUDA, or large LLMs - use scikit-learn Ridge Regression only
- **CRITICAL**: All paths use full repo path: `projects/PROJ-503-predicting-plant-defense-compound-produc/`
- **CRITICAL**: T015 and T009 enforce mandatory abort on power analysis failure (n<28)
- **CRITICAL**: T027 (pairing validation) MUST precede T024/T025 (matrix creation)
- **CRITICAL**: T055 exploratory model does NOT automatically satisfy SC-001/SC-002 unless explicitly validated
- **CRITICAL**: T016b implements the mandatory fallback to condition-level aggregation if sample-level pairing fails but aggregated n >= 28; otherwise E-PAIRING aborts.
- **SUPERSEDED**: T057 superseded by T057a/b/c; T063/T064 superseded by T057b/T057c (removed from list)
- **SUPERSEDED**: T004a removed (redundant with T001)
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

## Phase 0: Data Discovery & Acquisition (MANDATORY BLOCKER)

**Purpose**: Verify dataset availability, download specific verified datasets, and enforce strict pairing abort.

**⚠️ ABORT CRITERIA**: If no verified plant omics datasets are found or pairing < 95%, project halts with E-DATASET or E-PAIRING.

- [ ] T001 [US1] [FR-001] Download gene expression matrices from GEO for **specific verified IDs**: GSE21857 (*Arabidopsis*) and GSE167633 (*Solanum*). **Output: `data/raw/geo_expression_matrix.csv`. MUST fail loudly if download fails; NO synthetic fallback.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/data_download.py`)

- [ ] T002 [US1] [FR-002] Download metabolite data from Metabolomics Workbench for **specific verified ID**: ST002565. **Output: `data/raw/metabolite_matrix.csv`. MUST fail loudly if download fails; NO synthetic fallback.**

- [ ] T003 [US1] [SC-004] [Depends: T001, T002] Verify checksums for all downloaded files (T001, T002) and store in `data/raw/checksums.json`. **Abort with E-DATASET if <99% of requested experiment IDs match (SC-004).**

- [ ] T004 [US1] [FR-002] [Depends: T003] Pair samples by biological sample ID (`biosample_id`). Log mismatches to `logs/data_pairing.json` (Schema: JSON array with `sample_id`, `reason`). **Input: CSVs from T001, T002.**

- [ ] T005 [US1] [FR-009] [SC-005] [Depends: T003] **Abort with E-PAIRING** if pairing rate < 95% (FR-009, SC-005). **This check operates on ACTUAL downloaded data.**

- [ ] T006 [US1] [Plan-T006] Create `PairedSampleIndex` artifact (list of valid sample IDs) and save to `data/processed/paired_samples.csv`.

- [ ] T007 [US1] [Plan-T007] Perform post-verification check: Ensure *every* sample in `PairedSampleIndex` has both expression and metabolite data. If any mismatch remains, exclude and log.

- [ ] T008 [US1] [SC-001] Perform power analysis on the final paired set using G*Power (F-test, effect size 0.5, alpha 0.05, power 0.8). **Abort with E-POWER if N < 40 (Minimum Viable N for SC-001).** **Output: `logs/power_analysis_report.json` with fields: N, power, effect_size, alpha, test_type.**

- [ ] T009 [US1] [FR-001] Create `research.md` with dataset citations and availability status for Phase 0. **Output: `docs/research.md`.**

- [ ] T010 [US1] [Constitution-II] [Depends: T009] Parse `spec.md` for deferred citations and create `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/assumption_resolution_log.md`. **Output schema: JSON array with {assumption_id, citation, status}. Must pass before proceeding to Phase 1.**

- [ ] T011 [P] [US1] [Plan-T011] Contract test for GEO download in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/test_geo_download.py`

- [ ] T012 [P] [US1] [Plan-T012] Contract test for Metabolomics Workbench download in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/test_metabolomics_download.py`

- [ ] T013 [P] [US1] [Plan-T013] Integration test for end-to-end data pairing in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/integration/test_data_pairing.py`

**Checkpoint**: Phase 0 complete - datasets verified, paired, and power analysis passed OR project aborted.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T014 [Plan-T014] Create project structure with exact directories: `projects/PROJ-503-predicting-plant-defense-compound-produc/code/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/data/raw/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/data/processed/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/data/paired/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/outputs/models/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/integration/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/unit/`

- [ ] T015 [US1] [Plan-T015] [SC-006] Initialize Python project with requirements.txt at `projects/[PROJECT-ID]/code/requirements.txt` (pandas, numpy, scikit-learn, scipy, requests, pyyaml, biopython, statsmodels, pytest, pycombat)

- [ ] T016 [US1] [Plan-T016] Configure linting and formatting: Create `projects/PROJ-503-predicting-plant-defense-compound-produc/.flake8` and `projects/PROJ-503-predicting-plant-defense-compound-produc/pyproject.toml` with black configuration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T017 [P] [Plan-T017] Implement logging logic: Create utility functions to write to `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/data_pairing.json` (on mismatch) and `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/feature_filtering.csv` (on zero-variance filter) per spec.md edge cases. **Acceptance: Logs must be JSON/CSV valid and contain required fields. Function signature: `log_mismatch(sample_id, reason)` and `log_filter(gene_id, variance)`.**

- [ ] T018 [P] [Plan-T018] Setup environment configuration management: Create `projects/PROJ-503-predicting-plant-defense-compound-produc/data/sources.yaml` for dataset version traceability

- [ ] T019 [P] [Plan-T019] Create base data model classes (ExpressionMatrix, MetaboliteMatrix, FeatureSet, ModelArtifact) in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/models/`. **Define classes with explicit attributes for WIDE FORMAT: `ExpressionMatrix` (Rows=genes, Columns=samples, values=TPM), `MetaboliteMatrix` (Rows=metabolites, Columns=samples, values=log-conc). Include `__init__`, `to_csv`, `from_csv` methods. Data types: numpy.float64 for values, str for IDs. Validation: ensure columns are numeric and rows are unique.**

- [ ] T020 [P] [FR-008] [Plan-T020] Implement error handling framework with E-DATASET, E-PAIRING, E-TIMEOUT, and E-POWER error codes per plan.md. **Acceptance: Exception classes defined (e.g., `class E_PAIRING(Exception)`) and raised correctly in unit tests. Must enforce FR-008 abort logic.**

- [ ] T021 [P] [FR-008] [Plan-T021] Setup CI resource monitoring: Implement runtime timer in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/main.py` that logs elapsed CPU time and raises E-TIMEOUT if >4h per FR-008. **Note: This timer will be moved to Phase 5 to track cumulative time.**

- [ ] T022 [P] [Plan-T022] Create SHA-256 checksum validation utility for data integrity (SC-004). **Acceptance: Utility function `validate_checksum(file_path, expected_hash)` validates file checksums against a provided manifest.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - End‑to‑end data acquisition & pairing (Priority: P1) 🎯 MVP

**Goal**: Obtain paired dataset of gene‑expression profiles and defense‑metabolite concentrations for Arabidopsis and Solanum samples under herbivore stress

**Independent Test**: Run the data‑download module on specified GEO series IDs and Metabolomics Workbench experiment IDs and verify that every expression sample has a matching metabolite record from the same biological sample.

### Tests for User Story 1 (REQUIRED per spec.md Independent Test) ⚠️
*(Moved to Phase 0 for early validation)*

### Implementation for User Story 1

- [ ] T023 [US1] [Plan-T023] Implement sample-level pairing logic using biological sample identifiers (biosample_id column) (FR-002). **Algorithm: Exact match on biosample_id. Input: CSVs from T001/T002. Output: `data/paired/paired_index.csv`. Handle: Log mismatches to `logs/data_pairing.json`.**

- [ ] T024 [US1] [Plan-T024] Implement validation to halt with E-PAIRING if <95% samples have matched pairs (FR-009, SC-005). **MUST precede T025/T026.**

- [ ] T025 [US1] [Plan-T025] Create expression CSV with normalized TPM/FPKM values for each sample. **Output: `data/processed/expression_matrix.csv`. Schema: WIDE FORMAT {gene_id, sample_1, sample_2, ...}. Conditional on T024 passing.**

- [ ] T026 [US1] [Constitution-III] [Plan-T026] Create metabolite CSV with log‑transformed concentrations aligned by experimental sample identifier (US-1 acceptance scenario 2). **Output: `data/processed/metabolite_matrix.csv`. Logic: log2 transform. Handle zeros/negatives by adding small epsilon. Schema: WIDE FORMAT {metabolite_id, sample_1, sample_2, ...}.** Conditional on T024 passing.

- [ ] T027 [US1] Log mismatches to `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/data_pairing.json` with fields {sample_id, expression_source, metabolite_source, reason: "no_sample_level_pair"} (edge case handling)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Feature selection & preprocessing (Priority: P2)

**Goal**: Isolate expression features belonging to known defense‑biosynthetic pathways and ensure both expression and metabolite matrices are properly normalized before modelling

**Independent Test**: Execute the feature‑selection module and confirm that the resulting feature matrix contains only genes whose KEGG IDs map to terpenoid, alkaloid, or phenylpropanoid pathways.

### Tests for User Story 2 (REQUIRED per spec.md Independent Test) ⚠️

- [ ] T028 [P] [US2] [Plan-T028] Contract test for KEGG pathway mapping in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/test_kegg_mapping.py`
- [ ] T029 [P] [US2] [Plan-T029] Integration test for feature selection pipeline in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/integration/test_feature_selection.py`

### Implementation for User Story 2

- [ ] T030 [P] [US2] [FR-003] Implement expression normalization to TPM/FPKM in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py` (FR-003)
- [ ] T031 [P] [US2] [FR-003] Implement metabolite log‑transformation in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py` (FR-003)
- [ ] T032 [US2] [FR-004] Implement KEGG pathway ID mapping for defense biosynthetic genes (terpenoid, alkaloid, phenylpropanoid) (FR-004). **Input: KEGG API or local JSON. Output: `data/processed/kegg_mapping.json`. Handle: Log unmapped genes.**
- [ ] T033 [US2] Create FeatureSet output matrix containing only pathway-mapped genes (US-2 acceptance scenario 1)
- [ ] T034 [US2] [FR-003] Implement zero‑variance gene filtering (variance < 1e-10) in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py` (FR-003)
- [ ] T035 [US2] Log zero-variance genes to `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/feature_filtering.csv` with columns gene_id, variance, reason: "zero_variance". **Append a summary row with the total count of removed genes.** (edge case handling)
- [ ] T036 [US2] [FR-010] Implement species-specific z-score normalization in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py` (FR-010). **Input: Raw matrix from T033. After T033.**
- [ ] T037 [US2] [FR-010] Implement ComBat batch correction for cross-species expression scale differences (FR-010)
- [ ] T038 [US2] Implement ortholog fallback for unannotated Solanum genes using Arabidopsis reference. **Threshold: Default 60% sequence identity (unless overridden by T055). Log substitutions.** (edge case handling)
- [ ] T039 [US2] Document ortholog substitutions in `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/edge_cases.md` with original gene ID, substituted gene ID, and sequence identity percentage
- [ ] T040 [US2] Verify ≥75% of known defense pathway genes retained per species (SC-006)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive modelling & evaluation (Priority: P3)

**Goal**: Train a Ridge Regression model to predict defense‑metabolite abundance from the selected gene‑expression features and assess performance using cross-validation and permutation testing

**Independent Test**: Run the modelling script on the paired dataset and verify that it reports RMSE, Pearson r, and a permutation‑test p‑value for each metabolite.

### Tests for User Story 3 (REQUIRED per spec.md Independent Test) ⚠️

- [ ] T041 [P] [US3] [Plan-T041] Contract test for Ridge Regression model training in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/test_ridge_model.py`
- [ ] T042 [P] [US3] [Plan-T042] Contract test for permutation testing in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/test_permutation_test.py`
- [ ] T043 [P] [US3] [Plan-T043] Integration test for end-to-end modeling pipeline in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/integration/test_modeling_pipeline.py`

### Implementation for User Story 3

- [ ] T044 [US3] [FR-005] Implement outer k-fold cross-validation split with constraint of **maintaining paired samples** (Plan T031). **Output: Fold indices.**
- [ ] T045 [US3] [FR-005] [SC-001] [T044 MUST precede T045] Implement species-specific Ridge Regression model training **with nested 5-fold cross-validation** in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/modeling.py` (FR-005). **Output: `outputs/models/ridge_species_A_model.pkl`. k=5 fold. Seed: Set random_state. Input: Fold indices from T044. Sub-step: Perform INNER 5-fold CV for alpha tuning within each OUTER fold.**
- [ ] T046 [US3] [SC-001] Report mean RMSE and Pearson r across outer folds for each metabolite (SC-001). **Input: Output from T045.**
- [ ] T047 [US3] [FR-006] [FR-007] Implement max-T permutation test with 1 000 iterations in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/evaluation.py` (FR-006). **Output: `outputs/metrics/permutation_pvalues.csv`. n_iter=1000. random_state. Method: Max statistic across metabolites per permutation.** **Depends on T045.**
- [ ] T048 [US3] [FR-006] Report two‑sided p‑value ≤ 0.05 for metabolites showing true predictive signal (US-3 acceptance scenario 2) (FR-006). **Input: Raw p-values from T047.**
- [ ] T049 [US3] [FR-007] Apply Bonferroni correction across all metabolites tested (FR-007). **Input: Output from T048.**
- [ ] T050 [US3] [SC-001] Verify Pearson r ≥ 0.5 for metabolite with highest correlation across 5‑fold CV (SC-001)
- [ ] T051 [US3] [SC-002] Verify **Bonferroni-corrected** p‑value ≤ 0.05 for metabolite with highest correlation (SC-002). **Input: Output from T049.**
- [ ] T052 [US3] [FR-008] Log runtime and resource usage; abort if CPU time exceeds a predefined computational budget (FR-008). **Track cumulative time via global timer in main.py that reads from logs/runtime_summary.json accumulated across phases.**
- [ ] T053 [US3] Serialize ModelArtifact (coefficients and evaluation metrics) to `projects/PROJ-503-predicting-plant-defense-compound-produc/outputs/models/`
- [ ] T054 [US3] [Plan-T054] Implement VIF collinearity diagnostics and create `projects/PROJ-503-predicting-plant-defense-compound-produc/outputs/vif_diagnostics.csv` with columns gene_id, vif_score, threshold_exceeded. **Threshold: VIF > 5.0 (per plan.md T054 correction).** (multicollinearity handling assumption)
- [ ] T055 [US3] [FR-010] [Depends: T036, T037] **Mandatory**: Train cross-species model (FR-010): Create `projects/PROJ-503-predicting-plant-defense-compound-produc/outputs/models/cross_species_ridge.pkl`. **Mandatory requirement (not exploratory). Input: Data after T036/T037 (z-score + ComBat). Model: Single Ridge instance trained on combined, batch-corrected data. Output schema: {gene_id, coefficient}.**
- [ ] T056 [US3] [Plan-T024] **Mandatory**: Evaluate species‑holdout generalization (train on A, test on S; train on S, test on A). If holdout fails, discard cross-species model. (Plan T040)
- [ ] T057 [US3] [Plan-T024] Validate that model predictions are not driven by species identity (e.g., train a null model with only species as a predictor) (Plan T024). **Output: `outputs/metrics/species_null_model_results.csv`.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T058a [P] [Constitution-I] Create `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/quickstart.md` with E2E pipeline instructions
- [ ] T058b [P] [Plan-T058b] Update `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/data-model.md` with schema definitions for ExpressionMatrix, MetaboliteMatrix, FeatureSet, ModelArtifact
- [ ] T058c [P] [Plan-T058c] Create `projects/PROJ-503-predicting-plant-defense-compound-produc/contracts/` directory with module specifications

- [ ] T059a [P] [Plan-T059a] Run linting and formatting: Execute `black --check` and `flake8`; fix all violations.
- [ ] T059b [P] [Plan-T059b] Update `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/refactoring_log.md` with changes made.

- [ ] T060a [P] [Plan-T060a] Profile pipeline: Run `cProfile`; identify bottlenecks.
- [ ] T060b [P] [Plan-T060b] Optimize bottlenecks: Optimize data loading and model training.
- [ ] T060c [P] [SC-003] Verify E2E runtime: Run `tests/integration/test_e2e_runtime.py` to verify E2E runtime <4h (SC-003).

- [ ] T061 [P] [Constitution-I] Create unit tests with ≥80% line coverage: `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/unit/test_data_download.py`, `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/unit/test_preprocessing.py`, `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/unit/test_modeling.py`

- [ ] T063 [P] [Constitution-I] Run quickstart.md validation: Execute quickstart.md instructions on fresh environment; verify all steps complete without error; document in `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/quickstart_validation.md`

- [ ] T064 [US3] [Constitution-V] Commit all artifacts; tag release with content hash version. (Plan T053)

- [ ] T065 [US3] [Plan-T025] Generate final consolidated report with all metrics, logs, and artifacts (Plan T025). **Output: `docs/final_report.md`.**

**Note on Security**: Security checks (e.g., pip-audit) are optional and not required for FR/SC compliance. They may be performed at the team's discretion but are not part of the mandated task list.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Data Discovery)**: Must complete BEFORE Phase 1 (Setup) - MANDATORY BLOCKER. **No other phase can proceed until Phase 0 verifies data availability.**
- **Setup (Phase 1)**: Depends on Phase 0 completion - No dependencies on other stories
- **Foundational (Phase 2)**: Depends on Phase 0 and Phase 1 completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion AND Phase 0 verification
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

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
- Phase 0 tasks T001-T002 can run in parallel (GEO download, Metabolomics download)
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
Task: "Download gene expression matrices from GEO (GSE21857, GSE167633)"
Task: "Download metabolite data from Metabolomics Workbench (ST002565)"
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

1. Complete Phase 0: Data Discovery
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 → Datasets verified OR project aborted
2. Complete Setup + Foundational → Foundation ready
3. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 together
2. Once Phase 0 is done:
 - Team completes Setup + Foundational together
3. Once Foundational is done AND Phase 0 verifies datasets:
 - Developer A: User Story 1 (data acquisition)
 - Developer B: User Story 2 (preprocessing & feature selection)
 - Developer C: User Story 3 (modeling & evaluation)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: Phase 0 Data Discovery MUST complete successfully before any data acquisition tasks (T001-T027) can proceed
- **CRITICAL**: All tasks must run on free CPU-only CI (2 CPU cores, ~7 GB RAM, ~14 GB disk, ≤4 hours) per FR-008 and SC-003
- **CRITICAL**: Do NOT use 8-bit/4-bit quantization, CUDA, or large LLMs - use scikit-learn Ridge Regression only
- **CRITICAL**: All paths use full repo path: `projects/PROJ-503-predicting-plant-defense-compound-produc/`
- **CRITICAL**: T008 (Power Analysis) and T010 (Citation Resolution) enforce mandatory abort on failure
- **CRITICAL**: T055 (Cross-Species Model) is a MANDATORY requirement, not exploratory
- **CRITICAL**: T044 (Outer Split) MUST precede T045 (Ridge Training); T045 is NOT parallel ([P] removed)
- **CRITICAL**: T003 (Checksums) is in Phase 0, depends on T001/T002
- **CRITICAL**: T038 and T054 have default thresholds (60%, VIF>5.0) but depend on T010 for override
- **CRITICAL**: T010 depends on T009 for research.md input
- **CRITICAL**: Data loaders MUST fail loudly; NO synthetic fallback allowed on download failure.
- **CRITICAL**: Data models (T019, T025, T026) MUST use WIDE FORMAT (Rows=genes/metabolites, Columns=samples) as per spec.md Key Entities.
- **CRITICAL**: T021 (CI resource monitoring) has been moved to Phase 5 to track cumulative time correctly.
- **CRITICAL**: T064 and T064b have been merged into a single task T064.
- **CRITICAL**: T062 (Security Report) has been removed as it was not authorized by the plan or spec.
- **CRITICAL**: T058a (quickstart.md) has been moved from Phase 6 to Phase 1 to align with plan requirements.
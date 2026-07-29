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

## Phase 0: Data Discovery (MANDATORY BLOCKER)

**Purpose**: Verify dataset availability before proceeding to any other phase.

**⚠️ ABORT CRITERIA**: If no verified plant omics datasets are found, project halts with E-DATASET.

- [ ] T011 [P] [US1] Search GEO for Arabidopsis herbivore-stress series with explicit treatment annotations (e.g., GSE12345 placeholder). **Output: `logs/candidate_geo_ids_at.json` containing list of candidate GEO Series IDs.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/data_download.py`)

- [ ] T012 [P] [US1] Search GEO for Solanum herbivore-stress series with explicit treatment annotations (e.g., GSE67890 placeholder). **Output: `logs/candidate_geo_ids_solanum.json` containing list of candidate GEO Series IDs.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/data_download.py`)

- [ ] T013 [P] [US1] Search Metabolomics Workbench for defense metabolite experiments (terpenoids, alkaloids, phenylpropanoids) (e.g., MWST12345 placeholder). **Output: `logs/candidate_mw_ids.json` containing list of candidate Study IDs.**

- [ ] T014 [US1] Verify sample-level pairing feasibility (≥95% match rate per FR-009) using metadata comparison. **Input: `logs/candidate_geo_ids_at.json`, `logs/candidate_geo_ids_solanum.json`, `logs/candidate_mw_ids.json`. Algorithm: Compare biosample_id across sources. Output: `logs/pairing_feasibility.json` with fields {pairing_rate, total_samples, matched_samples}. ABORT with E-PAIRING if rate < 0.95. NO fallback to condition-level aggregation.**

- [ ] T014b [P] [US1] Generate SHA-256 checksums for downloaded files (once available) and store in `data/raw/checksums.json`. **Input: Raw files from T011/T012/T013 (post-download). Output: `data/raw/checksums.json`.**

- [ ] T015 [US1] Construct `PairedSampleIndex` artifact and run power analysis. **Input: Feasibility data from T014. Output: `data/processed/paired_samples.csv` (PairedSampleIndex) and `logs/power_analysis.log`. ABORT with E-POWER if n<28.**

- [ ] T016 [US1] Enforce ≥95% pairing rate; if below, abort with E-PAIRING and write detailed JSON to `logs/data_pairing.json`. **NO fallback to condition-level aggregation.**

- [ ] T017 [US1] Create `research.md` with dataset citations and availability status for Phase 0. **Output: `docs/research.md`.**

- [ ] T017b [US1] Log instrument validation status: Check downloaded Metabolomics Workbench datasets for LC-MS calibration curve documentation. **Log findings to `logs/instrument_validation.log`. Do NOT abort.** (Spec Assumption: Instrument validation - deferred)

- [ ] T018a [US1] Log power analysis results (required n=28, available n, achieved power) to `logs/power_analysis.log`.

- [ ] T018b [P] [US1] Contract test for GEO download in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/test_geo_download.py`

- [ ] T019 [P] [US1] Contract test for Metabolomics Workbench download in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/test_metabolomics_download.py`

- [ ] T020 [P] [US1] Integration test for end-to-end data pairing in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/integration/test_data_pairing.py`

**Checkpoint**: Phase 0 complete - datasets verified OR project aborted with E-DATASET

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure with exact directories: `projects/PROJ-503-predicting-plant-defense-compound-produc/code/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/data/raw/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/data/processed/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/data/paired/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/outputs/models/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/integration/`, `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/unit/`

- [X] T002 Initialize Python project with requirements.txt at `projects/PROJ-503-predicting-plant-defense-compound-produc/code/requirements.txt` (pandas, numpy, scikit-learn, scipy, requests, pyyaml, biopython, statsmodels, pytest)

- [ ] T003 [P] Configure linting and formatting: Create `projects/PROJ-503-predicting-plant-defense-compound-produc/.flake8` and `projects/PROJ-503-predicting-plant-defense-compound-produc/pyproject.toml` with black configuration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement logging logic: Create utility functions to write to `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/data_pairing.json` (on mismatch) and `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/feature_filtering.csv` (on zero-variance filter) per spec.md edge cases. **Acceptance: Logs must be JSON/CSV valid and contain required fields. Function signature: `log_mismatch(sample_id, reason)` and `log_filter(gene_id, variance)`.**

- [X] T005 [P] Setup environment configuration management: Create `projects/PROJ-503-predicting-plant-defense-compound-produc/data/sources.yaml` for dataset version traceability

- [ ] T006 [P] Create base data model classes (ExpressionMatrix, MetaboliteMatrix, FeatureSet, ModelArtifact) in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/models/`. **Define classes with explicit attributes: `ExpressionMatrix` (gene_id, sample_id, value), `MetaboliteMatrix` (metabolite_id, sample_id, value). Include `__init__`, `to_csv`, `from_csv` methods. Schema must define column names including 'biosample_id'.**

- [ ] T007 [P] Implement error handling framework with E-DATASET, E-PAIRING, E-TIMEOUT, and E-POWER error codes per plan.md. **Acceptance: Exception classes defined (e.g., `class E_PAIRING(Exception)`) and raised correctly in unit tests. Must enforce FR-008 abort logic.**

- [X] T008 Setup CI resource monitoring: Implement runtime timer in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/main.py` that logs elapsed CPU time and raises E-TIMEOUT if >4h per FR-008

- [ ] T010 [P] Create SHA-256 checksum validation utility for data integrity (SC-004). **Acceptance: Utility function `validate_checksum(file_path, expected_hash)` validates file checksums against a provided manifest.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - End‑to‑end data acquisition & pairing (Priority: P1) 🎯 MVP

**Goal**: Obtain paired dataset of gene‑expression profiles and defense‑metabolite concentrations for Arabidopsis and Solanum samples under herbivore stress

**Independent Test**: Run the data‑download module on specified GEO series IDs and Metabolomics Workbench experiment IDs and verify that every expression sample has a matching metabolite record from the same biological sample.

### Tests for User Story 1 (REQUIRED per spec.md Independent Test) ⚠️
*(Moved to Phase 0 for early validation)*

### Implementation for User Story 1

- [ ] T021 [P] [US1] Implement GEO expression matrix downloader in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/data_download.py` (FR-001). **Output: `data/raw/geo_expression_matrix.csv`. Schema: {gene_id, sample_id, biosample_id, value}. Logic: Normalize to TPM if raw counts provided.**

- [ ] T022 [P] [US1] Implement Metabolomics Workbench metabolite retriever in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/data_download.py` (FR-002). **Output: `data/raw/metabolite_matrix.csv`. Schema: {metabolite_id, sample_id, biosample_id, value}.**

- [ ] T028 [P] [US1] Verify downloaded files match expected SHA-256 checksums for ≥99% of requested IDs (SC-004). **Source: `data/raw/checksums.json` (from T014b). Logic: Abort if <99% match.**

- [ ] T023 [US1] Implement sample-level pairing logic using biological sample identifiers (biosample_id column) (FR-002). **Algorithm: Exact match on biosample_id. Input: CSVs from T021/T022. Output: `data/paired/paired_index.csv`. Handle: Log mismatches to `logs/data_pairing.json`.**

- [ ] T027 [US1] Implement validation to halt with E-PAIRING if <95% samples have matched pairs (FR-009, SC-005). **MUST precede T024/T025.**

- [ ] T023b [US1] Verify [deferred] pairing of *selected* samples: Assert that every sample in `data/paired/paired_index.csv` (after T027) has a valid match. **Input: `data/paired/paired_index.csv`. Output: `data/paired/selected_samples.csv`. [Depends on T023, T027].**

- [ ] T024 [US1] Create expression CSV with normalized TPM/FPKM values for each sample. **Output: `data/processed/expression_matrix.csv`. Schema: {gene_id, sample_id, value}. Conditional on T027 passing.**

- [ ] T025 [US1] Create metabolite CSV with log‑transformed concentrations aligned by experimental sample identifier (US-1 acceptance scenario 2). **Output: `data/processed/metabolite_matrix.csv`. Logic: log2 transform. Handle zeros/negatives by adding small epsilon.** Conditional on T027 passing.

- [ ] T026 [US1] Log mismatches to `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/data_pairing.json` with fields {sample_id, expression_source, metabolite_source, reason: "no_sample_level_pair"} (edge case handling)

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
- [ ] T035 [US2] Implement KEGG pathway ID mapping for defense biosynthetic genes (terpenoid, alkaloid, phenylpropanoid) (FR-004). **Input: KEGG API or local JSON. Output: `data/processed/kegg_mapping.json`. Handle: Log unmapped genes.**
- [ ] T036 [US2] Create FeatureSet output matrix containing only pathway-mapped genes (US-2 acceptance scenario 1)
- [ ] T033 [US2] Implement zero‑variance gene filtering (variance < 1e-10) in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py` (FR-003)
- [ ] T034 [US2] Log zero-variance genes to `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/feature_filtering.csv` with columns gene_id, variance, reason: "zero_variance". **Append a summary row with the total count of removed genes.** (edge case handling)
- [ ] T040a [US2] **Mandatory PCA**: If features (p) > 2 * samples (n), reduce to top components. **Output: `data/processed/pca_reduced_matrix.csv`.** Log components to `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/pca_summary.csv` (Plan T025). **Implementation: Use sklearn.decomposition.PCA, retain components explaining ≥95% variance.** Conditional on `data/paired/selected_samples.csv` (from T023b).
- [ ] T040b [US2] Implement species-specific z-score normalization in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py` (FR-010). **Input: Raw matrix from T036. After T036.**
- [ ] T040c [US2] Implement ComBat batch correction for cross-species expression scale differences (FR-010)
- [ ] T037 [US2] Implement ortholog fallback for unannotated Solanum genes using Arabidopsis reference. **Threshold: Default 60% sequence identity (unless overridden by T065). Log substitutions.** (edge case handling)
- [ ] T038 [US2] Document ortholog substitutions in `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/edge_cases.md` with original gene ID, substituted gene ID, and sequence identity percentage
- [ ] T039 [US2] Verify ≥75% of known defense pathway genes retained per species (SC-006)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive modelling & evaluation (Priority: P3)

**Goal**: Train a Ridge Regression model to predict defense‑metabolite abundance from the selected gene‑expression features and assess performance using cross‑validation and permutation testing

**Independent Test**: Run the modelling script on the paired dataset and verify that it reports RMSE, Pearson r, and a permutation‑test p‑value for each metabolite.

### Tests for User Story 3 (REQUIRED per spec.md Independent Test) ⚠️

- [ ] T042a [P] [US3] Contract test for Ridge Regression model training in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/test_ridge_model.py`
- [ ] T043 [P] [US3] Contract test for permutation testing in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/test_permutation_test.py`
- [ ] T044 [P] [US3] Integration test for end-to-end modeling pipeline in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/integration/test_modeling_pipeline.py`

### Implementation for User Story 3

- [ ] T045b [US3] Implement outer k-fold cross-validation split with constraint of **maintaining paired samples** (Plan T031). **Output: Fold indices.**
- [ ] T045 [US3] Implement species-specific Ridge Regression model training **with nested k-fold cross-validation** in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/modeling.py` (FR-005). **Output: `outputs/models/ridge_species_A_model.pkl`. k=5 fold. Seed: Set random_state. Input: Fold indices from T045b. Sub-step: Perform inner cross-validation (grid search) for Ridge alpha within each outer fold.**
- [ ] T047 [US3] Implement permutation test with 1 000 iterations in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/evaluation.py` (FR-006). **Output: `outputs/metrics/permutation_pvalues.csv`. n_iter=1000. random_state.** **Depends on T045.**
- [ ] T048 [US3] Report two‑sided p‑value ≤ 0.05 for metabolites showing true predictive signal (US-3 acceptance scenario 2) (FR-006). **Input: Raw p-values from T047.**
- [ ] T049 [US3] Apply Bonferroni correction across all metabolites tested (FR-007). **Input: Output from T048.**
- [ ] T050 [US3] Verify Pearson r ≥ 0.5 for metabolite with highest correlation across 5‑fold CV (SC-001)
- [ ] T051 [US3] Verify **Bonferroni-corrected** p‑value ≤ 0.05 for metabolite with highest correlation (SC-002). **Input: Output from T049.**
- [ ] T052 [US3] Log runtime and resource usage; abort if CPU time exceeds a predefined computational budget (FR-008)
- [ ] T053 [US3] Serialize ModelArtifact (coefficients and evaluation metrics) to `projects/PROJ-503-predicting-plant-defense-compound-produc/outputs/models/`
- [ ] T054 [US3] Implement VIF collinearity diagnostics and create `projects/PROJ-503-predicting-plant-defense-compound-produc/outputs/vif_diagnostics.csv` with columns gene_id, vif_score, threshold_exceeded. **Threshold: VIF > 10 (default, unless overridden by T065).** (multicollinearity handling assumption)
- [ ] T055 [US3] Create exploratory cross-species model: Create `projects/PROJ-503-predicting-plant-defense-compound-produc/outputs/models/cross_species_model.pkl` **only if paired samples ≥50**; otherwise log E-SAMPLESIZE. (FR-010, Plan T039)
- [ ] T056 [US3] **Mandatory**: Evaluate species‑holdout generalization (train on A, test on S; train on S, test on A). If holdout fails, discard cross-species model. (Plan T040)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T057a [P] Create `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/quickstart.md` with E2E pipeline instructions
- [ ] T057b [P] Update `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/data-model.md` with schema definitions for ExpressionMatrix, MetaboliteMatrix, FeatureSet, ModelArtifact
- [ ] T057c [P] Create `projects/PROJ-503-predicting-plant-defense-compound-produc/contracts/` directory with module specifications

- [ ] T058a [P] Run linting and formatting: Execute `black --check` and `flake8`; fix all violations.
- [ ] T058b [P] Update `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/refactoring_log.md` with changes made.

- [ ] T059a [P] Profile pipeline: Run `cProfile`; identify bottlenecks.
- [ ] T059b [P] Optimize bottlenecks: Optimize data loading and model training.
- [ ] T059c [P] Verify E2E runtime: Run `tests/integration/test_e2e_runtime.py` to verify E2E runtime <4h (SC-003).

- [ ] T060 [P] Create unit tests with ≥80% line coverage: `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/unit/test_data_download.py`, `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/unit/test_preprocessing.py`, `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/unit/test_modeling.py`

- [ ] T061 Security hardening: Run pip-audit or safety check; create `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/security_report.md` with vulnerability findings and remediation status

- [ ] T062 Run quickstart.md validation: Execute quickstart.md instructions on fresh environment; verify all steps complete without error; document in `projects/PROJ-predicting-plant-defense-compound-produc/docs/quickstart_validation.md`

- [ ] T063 [US3] Commit all artifacts; tag release with content hash version. (Plan T053)

- [ ] T063b [US3] Tag release with content hash version. (Plan T053 - Split from T063 for clarity)

- [ ] T065 [US3] Verify all assumptions in spec.md have deferred citations resolved: Parse spec.md assumptions for [deferred: citation required] markers; confirm each has corresponding entry in research.md; create `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/assumption_resolution_log.md`. **Search Strategy: Use Google Scholar/NCBI with keywords from assumption text (e.g., "Arabidopsis herbivore stress GEO", "Metabolomics Workbench LC-MS calibration"). [Depends on T017 for research.md input].**

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
- **CRITICAL**: Phase 0 Data Discovery MUST complete successfully before any data acquisition tasks (T021-T028) can proceed
- **CRITICAL**: All tasks must run on free CPU-only CI (CPU cores, ~7 GB RAM, A substantial disk capacity is required., NO GPU, ≤4 hours) per FR-008 and SC-003
- **CRITICAL**: Do NOT use 8-bit/4-bit quantization, CUDA, or large LLMs - use scikit-learn Ridge Regression only
- **CRITICAL**: All paths use full repo path: `projects/PROJ-503-predicting-plant-defense-compound-produc/`
- **CRITICAL**: T015 (power analysis) and T018a (logging) enforce mandatory abort on power analysis failure (n<28) AFTER data discovery
- **CRITICAL**: T027 (pairing validation) MUST precede T024/T025 (matrix creation)
- **CRITICAL**: T055 exploratory model does NOT automatically satisfy SC-001/SC-002 unless explicitly validated
- **CRITICAL**: T014/T016 strictly enforce E-PAIRING abort if pairing < 95% (NO fallback)
- **CRITICAL**: T045b (Outer k-fold) MUST precede T045 (Ridge training); T045 is NOT parallel ([P] removed)
- **CRITICAL**: T023b ([deferred] pairing check) depends on T023 and T027 (Removed [deferred] label, now mandatory)
- **CRITICAL**: T014b (Checksums) is in Phase 0, depends on T011/T012/T013
- **CRITICAL**: T037 and T054 have default thresholds (60%, VIF>10) but depend on T065 for override
- **CRITICAL**: T065 depends on T017 for research.md input
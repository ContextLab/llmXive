# Tasks: Identifying Predictive Biomarkers of Chemotherapy Response in Public Cancer Datasets

**Input**: Design documents from `/specs/001-chemo-biomarker-discovery/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
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

- [ ] T001 Create project structure per `plan.md` (code/, data/, results/, tests/)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scikit-learn, rpy2, biopython, requests, scipy, psutil)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/config.py`: Define paths, random seeds, FDR thresholds, CPU/memory limits, and `MAX_VARIANCE_GENES`
- [ ] T005 [P] Implement `code/utils.py`: Logging setup, checksum generation (`checksums.json`), and timeout watchdog (5h limit)
- [ ] T006 [P] Create schema definitions in `specs/001-chemo-biomarker-discovery/contracts/` (dataset.schema.yaml, model_output.schema.yaml, meta_analysis.schema.yaml)
- [ ] T007 Implement `code/__init__.py` and basic `code/main.py` orchestrator skeleton
- [ ] T008 Setup `pytest` configuration and contract test harness for YAML schema validation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download TCGA/GEO data, verify response labels (Data Feasibility Gate), harmonize IDs, normalize data, and split into discovery/training sets.

**Independent Test**: Run acquisition on a subset of 2 cancer types; verify `data/processed/` contains ≥100 samples per type, harmonized HGNC symbols, variance-stabilized values, and distinct discovery/training splits.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`
- [ ] T011 [P] [US1] Integration test for end-to-end download, normalization, and splitting on 2 tumor types in `tests/integration/test_acquisition.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data_acquisition.py`: Download TCGA HTSeq-Counts & clinical via HuggingFace mirror for **≥3 tumor types** (FR-001). **Requirement**: Initial download MUST target ≥3 types before any filtering.
- [ ] T013 [US1] Implement `code/data_acquisition.py`: Download GEO datasets (GSE25055, GSE42752) via HuggingFace mirror (FR-002). **Requirement**: Ensure at least 2 GEO datasets with response labels are acquired.
- [ ] T014 [US1] Implement **Data Feasibility Gate** in `code/data_acquisition.py`: Verify response labels (RECIST/CR/PR); exclude tumor types lacking labels; **halt if <2 tumor types remain**; **write `data/feasibility_gate_status.json`** with `status` (halted/passed) and `reason` (e.g., "insufficient_types") upon execution (FR-001, FR-002, Data Feasibility Gate).
- [ ] T014.5 [US1] Implement `code/preprocessing.py`: **Split data** for each tumor type into a `discovery_set` (for gene selection) and `training_set` (for model fitting) with a substantial majority/minority split (e.g., 70/30). **Output**: Save distinct CSV/Parquet files to `data/processed/{tumor_type}_discovery_set.csv` and `data/processed/{tumor_type}_training_set.csv` (FR-013).
- [ ] T015 [US1] Implement `code/preprocessing.py`: Harmonize Ensembl/Entrez to HGNC symbols using `mygene`/`biomaRt`; filter if coverage <95% (FR-003).
- [ ] T016 [US1] Implement `code/preprocessing.py`: Filter low-expression genes (CPM < 1 in >80% samples) (FR-004).
- [ ] T017 [US1] Implement `code/preprocessing.py`: Apply DESeq2 VST for RNA-seq (via `rpy2`) and log2 transform for Microarray (FR-004).
- [ ] T018 [US1] Implement `code/preprocessing.py`: **Cross-Platform Alignment**: 
    1. If both TCGA (RNA-seq) and GEO (Microarray) data are present, apply **Quantile Normalization** to align GEO data to TCGA distribution.
    2. If RNA-seq batch effects are detected (e.g., via PCA clustering by batch) within the TCGA data, apply **ComBat-seq** as an alternative for RNA-seq specific batch correction (FR-014).
- [ ] T019 [US1] Write raw data checksums to `data/checksums.json` immediately upon download (Data Hygiene).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Cross-Cancer Biomarker Identification (Priority: P2)

**Goal**: Define the logic for dynamic gene panel selection within the Nested CV loop. (Note: Static pre-computation of the panel is removed to prevent data leakage; tasks here define the selection logic functions).

**Independent Test**: Verify the selection logic (intersection/union) can be executed on a small sample of discovery sets.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Unit test for Stouffer's meta-analysis calculation in `tests/unit/test_meta_analysis.py`
- [ ] T021 [P] [US2] Integration test for DE and panel selection logic on 3 tumor types (simulated) in `tests/integration/test_biomarker_discovery.py`

### Implementation for User Story 2 (Logic Definition)

- [ ] T024 [US2] Implement `code/meta_analysis.py`: Define function to compute intersection of significant genes across ≥2 tumor types (FR-006).
- [ ] T025 [US2] Implement `code/meta_analysis.py`: Define function to fallback to union of top-ranked genes (≤50) if intersection is empty; **ensure this function writes `fallback_reason: "intersection_empty"` to `results/summary.md`** (FR-006).
- [ ] T026 [US2] Implement `code/meta_analysis.py`: Define function to compute Stouffer's meta-analysis p-values and rank genes (FR-006).
- [ ] T027 [US2] Implement `code/meta_analysis.py`: Define function to limit analysis to top `MAX_VARIANCE_GENES` (from `code/config.py`) most variable genes. **Logic**: Calculate variance across all samples, sort descending, and select top N where N = `config.MAX_VARIANCE_GENES` (Plan: Gene Limit).
- [ ] T028 [US2] Implement `code/meta_analysis.py`: Save **candidate** gene panel logic to `results/meta_analysis/gene_panel_logic.json` (metadata only, not the final panel) for traceability (FR-006).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (logic defined)

---

## Phase 5: User Story 3 - Predictive Model Training and Validation (Priority: P3)

**Goal**: Build tumor-type-specific models, perform nested CV with internal feature selection, external validation, and statistical significance testing.

**Independent Test**: Train tumor-specific models; run 5-fold nested CV on training set; validate on ≥2 GEO datasets; verify AUC ≥0.75 and calibration.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Contract test for model output schema in `tests/contract/test_model_schema.py`
- [ ] T030 [P] [US3] Integration test for full modeling and validation pipeline in `tests/integration/test_modeling.py`

### Implementation for User Story 3

- [ ] T022 [US3] Implement `code/differential_expression.py`: Wrap DESeq2 Wald test via `rpy2` (FDR < 0.05, |log2FC| > 1.0) **on the discovery_set** (FR-005). **Note**: This function is executed *inside* the inner loop of the Nested CV (T032) on the `discovery_set` data.
- [ ] T023 [US3] Implement `code/differential_expression.py`: Execute DE **on the discovery_set** (from T014.5) to generate candidate significant genes **within the CV fold** (FR-005). **Note**: This task provides the function used in the inner loop.
- [ ] T031 [US3] Implement `code/modeling.py`: Build **Tumor-type-specific** Elastic-Net Logistic Regression models using the gene panel selected dynamically in the CV loop (FR-007). **Requirement**: Train one model per tumor type on the `training_set`. Do NOT pool data.
- [ ] T032 [US3] Implement `code/modeling.py`: Perform **Nested Cross-Validation** on the **training_set** with **Internal Feature Selection** (re-run DESeq2 via T022/T023 on `discovery_set` folds within the inner loop) (FR-007, Plan: Nested CV). **Logic**: Use `meta_analysis` functions (T024-T027) to select the gene panel *inside* the inner loop.
- [ ] T033 [US3] Implement `code/modeling.py`: Train **final models** for each tumor type on the full **training_set** using the validated gene panel derived from the CV process (Plan: Tumor-specific Models).
- [ ] T033.5 [US3] Implement `code/modeling.py`: Implement **Leave-One-Cancer-Type-Out (LOO)** validation on the tumor-type-specific models; halt if <2 tumor types remain; **write `results/loo_validation_status.json`** with `status` and `reason` if halted (FR-008).
- [ ] T034 [US3] Implement `code/validation.py`: Compute ROC-AUC, Precision-Recall, and Calibration Curves (deciles) (FR-009, SC-001).
- [ ] T035 [US3] Implement `code/validation.py`: Apply Bonferroni correction for multiple hypothesis testing (FR-010, SC-002).
- [ ] T036 [US3] Implement `code/validation.py`: Perform DeLong's test against clinical covariates-only baseline (FR-011).
- [ ] T037 [US3] Implement `code/validation.py`: Handle class imbalance: **use stratified k-fold for ALL cases**; apply cost-sensitive learning **only if** responder ratio <20% (Edge Cases).
- [ ] T038 [US3] Implement `code/validation.py`: Generate calibration plots and flag underpowered deciles (n < 20) (FR-009).
- [ ] T039 [US3] Implement `code/main.py`: Enforce runtime timeout and memory limit using `psutil` and watchdog; **write `results/runtime_metrics.json`** with `timeout_triggered` and `peak_memory_mb` (FR-012, SC-004, SC-005).
- [ ] T040 [US3] Generate `results/summary.md` with final metrics, panel size, validation results, and fallback flags (FR-006, FR-009).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Documentation updates in `specs/001-chemo-biomarker-discovery/quickstart.md`
- [ ] T042 Code cleanup and refactoring
- [ ] T043 Performance optimization (sequential processing of tumor types to save RAM) (Plan: Sequential Processing)
- [ ] T044 [P] Additional unit tests in `tests/unit/`
- [ ] T045 Run `quickstart.md` validation to ensure full pipeline execution on CPU-only runner

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 data output (specifically `discovery_set`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US2 logic and US1 `training_set`

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data acquisition before preprocessing
- Preprocessing before splitting (T014.5)
- Splitting before Differential Expression (T022/T023)
- Differential Expression before meta-analysis
- Meta-analysis before modeling
- Modeling before validation

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/contract/test_data_schema.py"
Task: "Integration test for end-to-end download, normalization, and splitting in tests/integration/test_acquisition.py"

# Launch parallel implementation tasks:
Task: "Implement data acquisition for TCGA in code/data_acquisition.py"
Task: "Implement data acquisition for GEO in code/data_acquisition.py"
Task: "Implement ID harmonization and splitting in code/preprocessing.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (including Split T014.5)
4. **STOP and VALIDATE**: Test User Story 1 independently (Data Feasibility Gate, Normalization, Splitting)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Candidate Gene Panel Logic)
4. Add User Story 3 → Test independently → Deploy/Demo (Tumor-specific Models & Validation)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Data Pipeline & Splitting)
   - Developer B: User Story 2 (Biomarker Discovery Logic on Discovery Set)
   - Developer C: User Story 3 (Modeling on Training Set)
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
- **CPU Constraint**: All tasks must be implementable on a limited number of CPU cores, a constrained amount of RAM, and no GPU.
- **Data Integrity**: Never fabricate data; use real TCGA/GEO sources via verified mirrors.
- **FR-013 Compliance**: Strict separation of discovery (gene selection) and training (model fitting) sets is mandatory.
- **FR-007 Compliance**: Models must be tumor-type-specific, not pooled.
- **FR-014 Compliance**: Quantile Normalization for cross-platform; ComBat-seq available for RNA-seq batch effects.
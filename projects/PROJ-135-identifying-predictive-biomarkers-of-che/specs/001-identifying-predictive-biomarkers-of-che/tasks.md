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

- [X] T001a [P] Create project directory structure: `src/`, `data/raw/`, `data/processed/`, `results/`, `results/meta_analysis/`, `tests/`, `specs/001-chemo-biomarker-discovery/contracts/`, `state/`
- [X] T001b [P] Initialize `.gitignore` (exclude `data/raw/*`, `__pycache__`, `.env`) and `README.md`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scikit-learn, rpy2, biopython, requests, scipy, psutil)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/config.py`: Define paths, random seeds, FDR thresholds, CPU/memory limits, and `MAX_VARIANCE_GENES`
- [X] T005 [P] Implement `src/utils.py`: Logging setup, checksum generation, and timeout watchdog (h limit)
- [X] T006 [P] Create schema definitions in `specs/001-chemo-biomarker-discovery/contracts/` (dataset.schema.yaml, model_output.schema.yaml, meta_analysis.schema.yaml)
- [X] T007 Implement `src/__init__.py` and basic `src/main.py` orchestrator skeleton
- [X] T008 Setup `pytest` configuration and contract test harness for YAML schema validation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download TCGA/GEO data, verify response labels (Data Feasibility Gate), harmonize IDs, normalize data, and split into discovery/training sets.

**Independent Test**: Run acquisition on a subset of 2 cancer types; verify `data/processed/` contains ≥100 samples per type, harmonized HGNC symbols, variance-stabilized values, and distinct discovery/training splits.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`
- [ ] T011 [P] [US1] Integration test for end-to-end download, normalization, and splitting on 2 tumor types in `tests/integration/test_acquisition.py` <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [ ] T012 [US1] Implement `src/data_acquisition.py`: Download TCGA RNA-seq HTSeq-Counts and clinical metadata for **≥3 tumor types** via TCGAbiolinks (FR-001). **Requirement**: Dynamically discover available tumor types in the repository that have sufficient sample size and response annotations; select the first 3 valid types found. Do NOT hardcode specific types.
- [ ] T013 [US1] Implement `src/data_acquisition.py`: Download GEO datasets via GEOquery (FR-002). **Requirement**:
 1. If a dataset file cannot be fetched, log an error and exclude it.
 2. If a dataset exists but lacks response labels (RECIST/CR/PR), **skip that specific dataset**, log a warning, and exclude it from further processing.
 3. Proceed to the Feasibility Gate (T014) with the list of successfully downloaded and labeled datasets.
- [ ] T014 [US1] Implement **Data Feasibility Gate** in `src/data_acquisition.py`:
 1. **TCGA Gate**: If the count of valid TCGA tumor types is **< 3**, **Terminate execution** with exit code 1 and write `data/feasibility_gate.json` with `status: "halted"` and `reason: "insufficient_tcga_types"`.
 2. **GEO Gate**: If the count of valid GEO datasets (downloaded AND with response labels) is **< 2**, **Terminate execution** with exit code 1 and write `data/feasibility_gate.json` with `status: "halted"` and `reason: "insufficient_geo_datasets"`.
 3. **Proceed**: If TCGA >= 3 AND GEO >= 2, write `data/feasibility_gate.json` with `status: "ready"`.
- [ ] T015 [US1] Implement `src/preprocessing.py`: Harmonize Ensembl/Entrez to HGNC symbols using `mygene`/`biomaRt`; filter if coverage <95% (FR-003).
- [ ] T016 [US1] Implement `src/preprocessing.py`: Filter low-expression genes (CPM < 1 in >80% samples) (FR-004).
- [ ] T017 [US1] Implement `src/preprocessing.py`: **Cross-Platform Alignment & Batch Correction** (Strict Order):
 1. **Step 1 (RNA-seq Only)**: Apply **ComBat-seq** (via `rpy2`/`sva`) on **raw count data** for TCGA samples to correct for batch effects within RNA-seq data.
 2. **Step 2 (All Data)**: Apply **DESeq2 Variance-Stabilizing Transformation (VST)** to **ALL** data (TCGA RNA-seq counts and GEO Microarray log2-intensity) to ensure a single source of truth (FR-004, Plan T016).
 3. **Step 3 (Cross-Platform)**: If both TCGA and GEO data are present, apply **Quantile Matching** on the **VST-normalized data** to align GEO microarray distributions with TCGA RNA-seq distributions (FR-014). **Note**: Do NOT apply ComBat-seq to VST data.
 4. **Fallback**: If Quantile Matching fails, log a warning and proceed with uncorrected VST data, flagging the limitation in `results/summary.md`.
- [ ] T019 [US1] Implement **Data Hygiene Checksums**: Write checksums for all raw files in `data/raw/` **only** to `state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml` immediately upon download (Constitution III, Plan T012). **Do NOT write to multiple locations.**
- [ ] T020 [US1] Implement `src/preprocessing.py`: **Split data** for each tumor type into a `discovery_set` (for gene selection) and `training_set` (for model fitting) with a **stratified split maintaining the original class distribution** (FR-013, Plan T020). **Output**: Save distinct CSV/Parquet files to `data/processed/{tumor_type}_discovery_set.csv` and `data/processed/{tumor_type}_training_set.csv`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Cross-Cancer Biomarker Identification (Priority: P2)

**Goal**: Perform static differential expression on the full discovery set to generate a fixed gene panel, then meta-analyze across tumor types.

**Independent Test**: Verify the selection logic (intersection/union) can be executed on a small sample of discovery sets.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for Stouffer's meta-analysis calculation in `tests/unit/test_meta_analysis.py`
- [X] T022 [P] [US2] Integration test for DE and panel selection logic on 3 tumor types (simulated) in `tests/integration/test_biomarker_discovery.py`

### Implementation for User Story 2

- [ ] T023 [US2] Implement `src/differential_expression.py`: Wrap DESeq2 Wald test via `rpy2` (FDR < 0.05, |log2FC| > 1.0) **on the full discovery_set** (FR-005, Plan T022). **Note**: This is a STATIC run on the full discovery set, NOT inside the CV loop.
- [ ] T024 [US2] Implement `src/differential_expression.py`: Execute DE **on the full discovery_set** to generate candidate significant genes **once per tumor type** (FR-005).
- [ ] T025 [US2] Implement `src/meta_analysis.py`: Define function to compute intersection of significant genes across ≥2 tumor types (FR-006).
- [ ] T026 [US2] Implement `src/meta_analysis.py`: Define function to fallback to union of top-ranked genes (≤50) if intersection is empty; **ensure this function writes `fallback_reason: "intersection_empty"` to `results/summary.md`** (FR-006).
- [ ] T027 [US2] Implement `src/meta_analysis.py`: Define function to compute Stouffer's meta-analysis p-values and rank genes (FR-006).
- [ ] T028 [US2] Implement `src/meta_analysis.py`: Save **the final selected gene panel** (post-intersection/union/fallback) to `results/meta_analysis/gene_panel.json` (conforms to `contracts/gene_panel.schema.yaml`) (FR-006, Plan T028). **Do NOT save only logic**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (logic defined and panel generated)

---

## Phase 5: User Story 3 - Predictive Model Training and Validation (Priority: P3)

**Goal**: Build tumor-type-specific models using the fixed gene panel, perform nested CV, external validation, and statistical significance testing.

**Independent Test**: Train tumor-specific models; run k-fold nested CV on training set; validate on ≥2 GEO datasets; verify AUC ≥0.75 and calibration.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Contract test for model output schema in `tests/contract/test_model_schema.py`
- [ ] T030 [P] [US3] Integration test for full modeling and validation pipeline in `tests/integration/test_modeling.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement `src/modeling.py`: Build **Tumor-type-specific** Elastic-Net Logistic Regression models using the **fixed gene panel** derived from Phase 2 (FR-007). **Requirement**: Train one model per tumor type on the `training_set`. Do NOT pool data.
- [ ] T032 [US3] Implement `src/modeling.py`: Perform **Nested Cross-Validation** on the **training_set** (FR-007). **Logic**: **Load the fixed gene panel from `results/meta_analysis/gene_panel.json` (T028) BEFORE the CV loop begins**. **DO NOT perform any gene selection or panel generation logic inside the nested CV loop**. Use the fixed panel for all folds to prevent data leakage (FR-013).
- [ ] T033 [US3] Implement `src/modeling.py`: Train **final models** for each tumor type on the full **training_set** using the validated gene panel derived from the CV process (Plan: Tumor-specific Models).
- [ ] T033.5 [US3] Implement **LOO Validation Gate** in `src/modeling.py`:
 1. **Pre-Check**: Count total tumor types available (N).
 2. **Halt Condition**: If **(N - 1) < 2**, **Terminate execution** with exit code 1 and write `data/feasibility_gate.json` (`status: "halted"`, `reason: "insufficient_loo_types"`) because LOO would leave < 2 types (FR-008, Spec Assumptions).
 3. **Proceed Condition**: If **(N - 1) >= 2**, proceed with LOO validation.
 4. **Graceful Degradation**: If GEO datasets are missing but TCGA types ≥3, proceed with internal LOO validation (N-1) and log the limitation.
- [ ] T034 [US3] Implement `src/validation.py`: Compute ROC-AUC, Precision-Recall, and Calibration Curves (deciles) (FR-009, SC-001).
- [ ] T035a [US3] Implement `src/validation.py`: **Bonferroni Correction for Meta-Analysis**: Apply correction where `m` = **number of genes in the final meta-analyzed panel** (size of `results/meta_analysis/gene_panel.json`) (FR-010).
- [ ] T035b [US3] Implement `src/validation.py`: **Bonferroni Correction for DeLong's Test**: Apply correction where `m` = number of model comparisons (FR-010). **Output**: Adjusted p-values must be < 0.01.
- [ ] T036 [US3] Implement `src/validation.py`: Perform DeLong's test against clinical covariates-only baseline (FR-011).
- [ ] T037 [US3] Implement `src/validation.py`: Handle class imbalance: **use stratified k-fold for ALL cases**; apply cost-sensitive learning **only if** responder ratio <20% (Edge Cases).
- [ ] T038 [US3] Implement `src/validation.py`: Generate calibration plots and flag underpowered deciles (n < 20) (FR-009).
- [ ] T039 [US3] Implement `src/main.py`: Enforce runtime timeout and memory limit using `psutil` and watchdog; **write `results/runtime_metrics.json`** with `timeout_triggered` and `peak_memory_mb` (FR-012, SC-004, SC-005).
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
- Preprocessing before splitting (T020)
- Splitting before Differential Expression (T023/T024)
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
Task: "Implement data acquisition for TCGA in src/data_acquisition.py"
Task: "Implement data acquisition for GEO in src/data_acquisition.py"
Task: "Implement ID harmonization and splitting in src/preprocessing.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (including Split T020)
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
- **FR-013 Compliance**: Strict separation of discovery (gene selection) and training (model fitting) sets is mandatory. DE is performed ONCE on the full discovery set.
- **FR-007 Compliance**: Models must be tumor-type-specific, not pooled.
- **FR-014 Compliance**: ComBat-seq on counts pre-VST; Quantile Matching on VST for cross-platform alignment.
- **FR-008 Compliance**: LOO validation must halt if (N-1) < 2; proceed if (N-1) >= 2.
- **FR-010 Compliance**: Distinct Bonferroni correction logic for meta-analysis (m=final panel size) vs DeLong's test (m=comparisons).
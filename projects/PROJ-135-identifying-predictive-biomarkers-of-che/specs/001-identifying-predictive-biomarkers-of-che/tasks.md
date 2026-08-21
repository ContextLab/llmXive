---
description: "Task list for feature implementation: Identifying Predictive Biomarkers of Chemotherapy Response in Public Cancer Datasets"
---

# Tasks: Identifying Predictive Biomarkers of Chemotherapy Response in Public Cancer Datasets

**Input**: Design documents from `/specs/001-chemo-biomarker-discovery/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
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
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scikit-learn, rpy2, biopython, requests, scipy, psutil, sva)
- [X] T003 [P] Configure linting (ruff) and formatting (black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/config.py`: Define paths, random seeds, FDR thresholds, CPU/memory limits, `MAX_VARIANCE_GENES`, and `GEO_IDS` (default: `['GSE25055', 'GSE42752']`). Added clarification that this config supports FR‑001/FR‑002 checks.
- [X] T005 [P] Implement `src/utils.py`: Logging setup, checksum generation, and timeout watchdog (h limit)
- [ ] T006 [Foundational] Implement schema files and checksums. **Logic**:
  1. **Define Content**: Define the following YAML content for the schemas in memory based on Spec Key Entities:
     - `dataset.schema.yaml`: Fields: `sample_id` (string), `tumor_type` (string), `response_label` (string), `expression_vector` (array of floats).
     - `model_output.schema.yaml`: Fields: `cancer_type` (string), `alpha` (float), `lambda` (float), `coefficients` (object), `cross_val_auc` (float).
     - `gene_panel.schema.yaml`: Fields: `gene_symbol` (string), `meta_p_value` (float), `log2FC_mean` (float), `selected` (boolean).
  2. **Write Files**: Save the defined YAML content to `specs/001-chemo-biomarker-discovery/contracts/` (`dataset.schema.yaml`, `model_output.schema.yaml`, `gene_panel.schema.yaml`).
  3. **Compute Checksums**: Compute SHA256 for each schema file and write to `state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml` in `artifact_hashes` map. **Constraint**: This task runs sequentially (write then checksum).
- [X] T007 Implement `src/__init__.py` and basic `src/main.py` orchestrator skeleton
- [X] T008 Setup `pytest` configuration and contract test harness for YAML schema validation
- [ ] T009 [Foundational] Implement `src/utils.py`: **Runtime Monitoring and Enforcement**. **Logic**:
  1. **Define Exception**: Define class `ResourceLimitExceeded(Exception)` in `src/utils.py` with message format: "Resource limit exceeded: [type] limit [value] exceeded. Per FR-012, SC-004, SC-005."
  2. **Implement Context Manager**: Create a context manager or decorator that tracks CPU time and memory usage (RSS) for any function it wraps.
  3. **Enforce Limits**: If usage exceeds `MAX_CPU_HOURS` (6) or `MAX_RAM_GB` (7), raise a `ResourceLimitExceeded` exception.
  4. **Docker Enforcement**: If R processes are spawned via Docker, ensure `docker run` includes flags `--cpus=<capped_cores> --memory=<capped_ram>g`.
  5. **Watchdog**: Implement `scripts/watchdog.sh` script to monitor Docker container resource usage and kill the container if limits are exceeded. **Path**: `scripts/watchdog.sh`.
  6. **Resource Detection & Capping**: At runtime, detect available CPU cores (`nproc`) and RAM (`free -g`). Calculate capped values as the minimum of detected resources and safe thresholds. Use these caps for Docker flags to enforce FR-012 regardless of runner capacity.
  7. **Integration**: Integrate this into the main orchestrator to enforce SC-004 and SC-005. **Requirement**: This task MUST run sequentially after T004 and T005 to ensure global state is initialized correctly.
  8. **Logging**: Log warnings using the format "Warning: Resource usage approaching limit: [type] [current] / [max]" when usage exceeds a substantial majority threshold.
 **Requirements**: FR-012, SC-004, SC-005.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download TCGA/GEO data, verify response labels (Data Feasibility Gate), harmonize IDs, normalize data, and split into discovery/training sets.

**Independent Test**: Run acquisition on a subset of cancer types; verify `data/processed/` contains ≥100 samples per type, harmonized HGNC symbols, variance‑stabilized values, and distinct discovery/training splits. **Note**: This test is only valid if the Data Feasibility Gate (T014) passes (i.e., ≥3 TCGA types and ≥2 valid GEO datasets). If the gate fails, the test is considered "Not Applicable" for that run configuration.

### Implementation for User Story 1

- [X] T012 [US1] Implement `src/data_acquisition.py`: **TCGA Download, Sample Mapping, and Checksum**. *(Logic unchanged)*
- [X] T013 [US1] Implement `src/data_acquisition.py`: **GEO Download and Sample Mapping**. *(Logic unchanged)*
- [X] T014 [US1] **Data Feasibility Gate**: Implement `src/data_acquisition.py`. *(Logic unchanged)*
- [X] T011 [US1] Integration test for Feasibility Gate logic in `tests/integration/test_feasibility_gate.py`. **Update**: This test MUST include a case where the gate fails (insufficient data) to verify the halting mechanism works correctly. *(Logic unchanged)*
- [X] T017a [US1] Implement `src/preprocessing.py`: **Filter low‑expression genes (CPM < 1 in > 80% samples)**. **Update**: Explicitly state that missing data in GEO datasets will be handled via complete case analysis (row removal), with no imputation. *(Logic unchanged)*
- [X] T017b [US1] Implement `src/preprocessing.py`: **Apply DESeq2 VST** via rpy2. *(Logic unchanged)*
- [X] T017c [US1] Implement `src/preprocessing.py`: **Harmonize Gene Identifiers** (Ensembl/Entrez → HGNC). *(Logic unchanged)*
- [X] T017d [US1] Implement `src/preprocessing.py`: **Normalization Failure Handling**.  
  1. After attempting VST on each dataset, if a dataset cannot be re‑normalized (e.g., incompatible format), log a warning `"Normalization failed for {dataset_id}: {reason}"` and update `data/normalization_status.json` with status `"failed"` for that dataset.  
  2. If *all* datasets fail, raise a `RuntimeError` and halt execution with exit code 1.  
  3. Successful normalizations are recorded with status `"success"` in the same JSON file.  
  4. This satisfies US‑1 Edge Case 3 (datasets that cannot be re‑normalized are excluded with a logged warning) and ensures a clear halt when no data remain.
- [X] T016 [US1] **Batch Correction**: Implement `src/preprocessing.py` to align platforms (FR‑014). **Update**: ComBat-seq is the ONLY primary method; Quantile Matching is ONLY a fallback if ComBat-seq fails on discrete data. Ensure splitting (T020) logic is finalized before batch correction to prevent leakage. *(Logic unchanged)*
- [ ] T020 [US1] Implement `src/preprocessing.py`: **Split data** for each tumor type into `discovery_set` and `training_set` with stratified class distribution (FR‑013). **Update**: 
  1. Ensure splitting occurs BEFORE any batch correction or cross-tumor operations to prevent data leakage.
  2. Include a step to monitor RAM usage during the split operation and raise `ResourceLimitExceeded` if limits are breached (SC-005).
  3. Verify that the split maintains distinct discovery and training sets for each tumor type as required by FR-013. *(Logic unchanged)*

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Cross-Cancer Biomarker Identification (Priority: P2)

**Goal**: Perform differential expression analysis on the full discovery set, identify cross‑tumor biomarkers using Stouffer's method, and generate a fixed gene panel.

**Independent Test**: Verify the selection logic (intersection/union) can be executed on a small sample of discovery sets.

### Tests for User Story 2 (OPTIONAL)

- [X] T021 [P] [US2] Unit test for Stouffer's meta‑analysis calculation in `tests/unit/test_meta_analysis.py`
- [X] T022 [P] [US2] Integration test for LOO‑Blind DE and panel selection logic on 3 tumor types (simulated) in `tests/integration/test_biomarker_discovery.py`

### Implementation for User Story 2

- [ ] T023a [US2] **Implement Per‑Tumor‑Type DE Execution** (R script). *(Logic unchanged)*
- [ ] T023b [US2] **Implement Aggregation**. **Update**: Specify a strategy for resolving gene naming conflicts (e.g., using HGNC symbols as the canonical key and aggregating by gene symbol). *(Logic unchanged, with added note on duplicate gene handling)*
- [ ] T024b [US2] **Implement Stouffer's Meta‑Analysis**.  
  1. Compute combined p‑values using `scipy.stats.combine_pvalues(..., method='stouffer')`.  
  2. Write results to `results/meta_analysis/stouffer_meta.csv`.  
  3. Write `m_meta` (number of genes in final panel) to `results/meta_analysis/bonferroni_correction.json` for later use.  
  4. **Dependency**: Runs after T023b.
- [ ] T024a [US2] **Generate Static Gene Panel: Intersection/Union Logic**.  
  1. Load DE results and Stouffer meta‑p‑values (produced by T024b).  
  2. Compute intersection of significant genes (FDR < 0.05, |log2FC| > 1.0) across ≥2 tumor types.  
  3. If intersection empty, fallback to union of top‑ranked genes (≤50) and set `fallback_reason: "intersection_empty"` in `results/meta_analysis/panel_status.json`.  
  4. Rank genes by descending mean log2FC then ascending meta‑p‑value.  
  5. Limit final panel to ≤50 genes.  
  6. Output to `results/meta_analysis/gene_panel.json`.  
  7. **Dependency**: Runs after T024b.
- [ ] T024c [US2] **Finalize Gene Panel**. *(Logic unchanged)*
- [ ] T023d – (resolved in plan; no task needed)

**Checkpoint**: User Stories 1 and 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Model Training and Validation (Priority: P3)

**Goal**: Build tumor‑type‑specific models using the fixed gene panel, perform nested CV, external validation, and statistical significance testing.

### Tests for User Story 3 (MANDATORY)

- [ ] T044a [US3] Unit test for `train_model` edge cases in `tests/unit/test_modeling.py`. *(Logic unchanged)*
- [ ] T044b [US3] Unit test for `nested_cv` parameter search and leakage prevention in `tests/unit/test_modeling.py`. *(Logic unchanged)*
- [ ] T044c [US3] Unit test for `loo_validation` pre‑check and loop logic in `tests/unit/test_modeling.py`. *(Logic unchanged)*
- [X] T029 [P] [US3] Contract test for model output schema in `tests/contract/test_model_schema.py`
- [X] T030 [P] [US3] Integration test for full modeling and validation pipeline in `tests/integration/test_modeling.py`

### Implementation for User Story 3

- [ ] T033 [US3] **LOO Validation Pre‑Check**. *(Logic unchanged)*
- [ ] T031a [US3] **Model Initialization**. *(Logic unchanged)*
- [ ] T031b [US3] **Execute Nested Cross‑Validation**. *(Logic unchanged)*
- [ ] T031c [US3] **Persist Model**. *(Logic unchanged)*
- [ ] T035 [US3] **Implement LOO Re‑training Logic**. *(Logic unchanged)*
- [ ] T036 [US3] **Implement LOO Evaluation and Save**. **Update**: Define the 'poor generalizability' threshold as a performance drop > 0.10 in AUC. *(Logic unchanged)*
- [ ] T037 [US3] **External GEO Validation**. **Update**: Explicitly require validation on ≥2 independent GEO cohorts (Constitution Principle VI). *(Logic unchanged)*
- [ ] T038 [US3] **Compute ROC‑AUC, Precision‑PR, and Calibration Curves**. *(Logic unchanged)*
- [ ] T039a [US3] **Baseline Model Training and Persistence**. **Update**: Explicitly state that the baseline model must be trained using ONLY clinical covariates (e.g., age, stage), excluding any gene expression data.  
  1. Load only clinical covariates (e.g., age, stage) from processed GEO validation sets.  
  2. Train logistic regression **without** expression features.  
  3. Save baseline model to `results/baseline_model.pkl` and metrics to `results/baseline_metrics.json`.  
  4. If covariates missing, log warning and set metrics to `null` for that cohort.  
  **Requirement**: Explicitly demonstrates FR‑010 usage of clinical‑only baseline.
- [ ] T039 [US3] **DeLong's Test**.  
  1. Load model AUCs and baseline AUCs.  
  2. Perform DeLong's test (e.g., via `pROC::roc.test`).  
  3. Read `m_delong` from `results/meta_analysis/bonferroni_correction.json` (produced by T041).  
  4. Apply Bonferroni correction using `m = m_delong`; adjusted p‑value must be < 0.01 (FR‑010).  
  5. Record adjusted p‑value in `results/deLong_results.json`.  
  **Dependency**: Runs after T039a.
- [ ] T040 [US3] **Handle Class Imbalance**. *(Logic unchanged)*
- [ ] T041 [US3] **Bonferroni Correction**. **Update**: Explicitly detail the two distinct Bonferroni scopes (meta-analysis vs DeLong).  
  1. **Pre‑Check**: Verify `results/meta_analysis/gene_panel.json` exists and contains a non‑empty `selected` list. Halt if missing.  
  2. **Meta‑Analysis Scope**: Count `m_meta` as the number of genes in the final panel (read from gene_panel.json).  
  3. **DeLong Scope**: Count `m_delong` as the number of valid model‑vs‑baseline comparisons (i.e., number of tumor types with converged models and available baseline metrics).  
  4. Write both `m_meta` and `m_delong` to `results/meta_analysis/bonferroni_correction.json`.  
  5. Apply Bonferroni correction to meta‑analysis p‑values (using `m_meta`) and to DeLong test p‑values (using `m_delong`). Adjusted p‑values must be < 0.01.  
  6. Record adjusted meta‑p‑values in `results/meta_analysis/gene_panel.json` (add field `adjusted_p`).  
  7. Record adjusted DeLong p‑values in `results/deLong_results.json`.  
  **Dependency**: Runs after T039 (so that raw DeLong p‑values are available) and before T042/T043 summary generation.
- [ ] T042 [US3] **Summary Merge Logic**. *(Logic unchanged)*
- [ ] T043 [US3] **Final Summary Generation**. *(Logic unchanged)*

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 [P] Documentation updates in `specs/001-chemo-biomarker-discovery/quickstart.md`
- [ ] T045 Code cleanup and refactoring
- [ ] T046 Run `quickstart.md` validation to ensure full pipeline execution on CPU‑only runner

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion – BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed) or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) – No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) – Requires US1 data output (`discovery_set`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) – Requires US2 logic and US1 `training_set`

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data acquisition before preprocessing
- Preprocessing before splitting (T020)
- Splitting before Differential Expression (T023)
- Differential Expression before meta‑analysis
- Meta‑analysis before modeling
- Modeling before validation

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CPU Constraint**: All tasks must be implementable on a limited number of CPU cores, a constrained amount of RAM, and no GPU.
- **Data Integrity**: Never fabricate data; use real TCGA/GEO sources via verified mirrors. **Fallback to verified mock data only if real API fails verification**.
- **FR‑013 Compliance**: Strict separation of discovery (gene selection) and training (model fitting) sets is mandatory. DE is performed ONCE on the full discovery set (or N‑1 subset for LOO).
- **FR‑007 Compliance**: Models must be tumor‑type‑specific, not pooled.
- **FR‑014 Compliance**: **ComBat‑seq** (for discrete count data) is the primary method for batch correction; **fallback to Quantile Matching** if ComBat‑seq fails (only if data types allow); **do NOT use ComBat** (continuous) as the primary method.
- **FR‑008 Compliance**: LOO validation must halt if the dataset drops to a minimal number of types where LOO is invalid. The task logic must explicitly raise an error and exit.
- **FR‑010 Compliance**: Distinct Bonferroni correction logic for meta‑analysis (m = **number of genes in the final panel**) vs DeLong's test (m = comparisons). Ensure both are correctly calculated and applied.
- **FR‑006 Compliance**: The fallback to union of top‑ranked genes must be explicitly triggered only when the intersection is empty, and the reason must be logged in `results/meta_analysis/panel_status.json`.
- **FR‑001/002 Compliance**: Ensure all data downloads are verified against the expected checksums and that missing response labels cause the pipeline to skip the offending dataset instead of halting entirely unless there's insufficient data.
- **TEST_MODE**: Set `TEST_MODE=True` environment variable to allow the pipeline to proceed with fewer than 3 TCGA types or 2 GEO datasets for Independent Testing purposes.
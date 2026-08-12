---
description: "Task list template for feature implementation"
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

- [X] T004 Implement `src/config.py`: Define paths, random seeds, FDR thresholds, CPU/memory limits, `MAX_VARIANCE_GENES`, and `GEO_IDS` (default: `['GSE25055', 'GSE42752']`).
- [X] T005 [P] Implement `src/utils.py`: Logging setup, checksum generation, and timeout watchdog (h limit)
- [ ] T006a [P] [US1] Define schema content: Write the YAML content for `dataset.schema.yaml`, `model_output.schema.yaml`, and `meta_analysis.schema.yaml` in memory, ensuring fields match Key Entities (Sample, GenePanel, Model) in spec.md.
- [ ] T006b [P] [US1] Write schema files: Save the defined YAML content to `specs/001-chemo-biomarker-discovery/contracts/` (dataset.schema.yaml, model_output.schema.yaml, meta_analysis.schema.yaml).
- [ ] T006c [P] [US1] Compute checksums: Compute SHA256 for each schema file and write to `state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml` in `artifact_hashes` map. **Constraint**: This task MUST run after T006b.
- [X] T007 Implement `src/__init__.py` and basic `src/main.py` orchestrator skeleton
- [X] T008 Setup `pytest` configuration and contract test harness for YAML schema validation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download TCGA/GEO data, verify response labels (Data Feasibility Gate), harmonize IDs, normalize data, and split into discovery/training sets.

**Independent Test**: Run acquisition on a subset of cancer types; verify `data/processed/` contains ≥100 samples per type, harmonized HGNC symbols, variance-stabilized values, and distinct discovery/training splits. **Note**: This test is only valid if the Data Feasibility Gate (T014) passes (i.e., ≥3 TCGA types and ≥2 valid GEO datasets are available). If the gate fails, the test is considered "Not Applicable" for that run configuration.

### Implementation for User Story 1

- [ ] T012a [P] [US1] Implement `src/data_acquisition.py`: Implement TCGA query logic. Query TCGA API for all projects with RNA-seq data, sort by sample count, and select a representative subset of available types (if tied, select alphabetically by project ID). Output the list of selected project IDs.
- [ ] T012b [P] [US1] Implement `src/data_acquisition.py`: Implement TCGA download and checksum logic. Download RNA-seq HTSeq-Counts and clinical metadata for the selected types to `data/raw/`. Compute SHA256 checksum only after successful download and verification.
- [ ] T012c [P] [US1] Implement atomic state update. Write checksums to `state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml` in `artifact_hashes` map only for successful downloads.
- [ ] T013 [P] [US1] Implement `src/data_acquisition.py`: Download GEO datasets via GEOquery (FR‑002). **Algorithm**:
 1. Load `GEO_IDS` from `src/config.py` (expected format: list of strings, e.g., `['GSE25055', 'GSE42752']`).
 2. Initialize `valid_geo_count = 0`.
 3. Iterate through configured GEO IDs.
 4. If a dataset file cannot be fetched, log an error, skip the file, and **DO NOT** write a checksum to the state file.
 5. If a dataset exists but lacks response labels (RECIST/CR/PR), **skip that specific dataset**, log a warning, **do not increment `valid_geo_count`**, and **continue** to the next dataset.
 6. **Checksum**: Compute SHA256 for each successfully downloaded and **verified** GEO file and append to `state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml` **only after verification is complete**.
 7. After iterating, check if `valid_geo_count` < 2. **This is a hard constraint derived from Spec Edge Cases**: If `valid_geo_count` < 2, **halt with exit code 1** and write `data/feasibility_gate.json` with `status: "halted"`, `reason: "insufficient_geo_datasets"`.
 8. Proceed to the Feasibility Gate (T014) using the **updated** `valid_geo_count` variable.
- [ ] T014 [P] [US1] **Data Feasibility Gate**: Implement `src/data_acquisition.py`.
 1. **TCGA Gate**: If the count of valid TCGA tumor types is **< 3**, **Terminate execution** with exit code 1 and write `data/feasibility_gate.json` with `status: "halted"`, `reason: "insufficient_tcga_types"`.
 2. **GEO Gate**: If the `valid_geo_count` (datasets with labels) is **< 2**, **Terminate execution** with exit code 1 and write `data/feasibility_gate.json` with `status: "halted"` and `reason: "insufficient_geo_datasets"`. **Clarification**: This is a hard failure; the pipeline does NOT proceed to internal validation if GEO < 2, as this violates the Independent Test requirement for US-1 and US-3. The Independent Test is only valid if the gate passes.
 3. **Proceed**: If TCGA ≥ 3 **AND** `valid_geo_count` ≥ 2, write `data/feasibility_gate.json` with `status: "ready"`.
 4. **Logging**: Explicitly **log a warning if total download size > 5 GB** as specified in Spec FR‑001 before proceeding.
 5. **Exit**: **Explicitly exit with code 1** immediately after writing the halted JSON if any gate fails.
- [ ] T014a [P] [US1] **Harmonize**: Implement `src/preprocessing.py`: Harmonize gene identifiers from Ensembl/Entrez to HGNC symbols with ≥95% gene coverage retained (FR‑003). **Output**: Save harmonized matrix to `data/processed/`. **Dependency**: Runs after T012c/T013 (Download).
- [ ] T017a [P] [US1] Implement `src/preprocessing.py`: **Filter** low‑expression genes (CPM < 1 in > 80% samples) (FR‑004). **Output**: Save filtered matrix. **Dependency**: Runs after T014a (Harmonization).
- [ ] T017b [P] [US1] Implement `src/preprocessing.py`: **Apply DESeq2 Variance‑Stabilizing Transformation (VST)** via rpy2 (FR‑004) on the filtered matrix. **Output**: Save VST matrix. **Dependency**: Runs after T017a.
- [ ] T017c [P] [US1] Implement `src/preprocessing.py`: **Save** the VST-normalized matrix to `data/processed/`. **Dependency**: Runs after T017b.
- [ ] T016 [P] [US1] **Batch Correction**: Implement `src/preprocessing.py` to align platforms (FR‑014). **Logic**:
 1. **Step 1**: **Create** `results/summary.md` if it does not exist.
 2. **Step 2**: Attempt to apply **ComBat** (via `rpy2`/`sva`) on the combined VST-normalized matrix (TCGA + GEO). **Note**: This task runs **after T017c** (VST Normalization) and **before T020** (Split).
 3. **Step 3**: If ComBat fails (e.g., due to batch size constraints), **attempt** Quantile Matching as a fallback using `sklearn.preprocessing.quantile_transform`.
 4. **Step 4**: If **both** Combat and Quantile Matching fail, **halt** the pipeline with a clear error message.
 5. **Requirement**: **Do NOT** use ComBat-seq. **Plan Override**: This task complies with Plan Phase 1 which mandates ComBat (continuous) over ComBat-seq, overriding Spec FR-014. **Reference**: See Plan.md Phase 1.
 6. **Logging & Documentation**: Record `batch_correction_method: "ComBat"` or `batch_correction_method: "Quantile_Matching"` in `results/summary.md` upon success. **Mandatory**: Write `override_note: "ComBat used instead of ComBat-seq per Plan Phase 1"` to `results/summary.md` to satisfy Constitution Principle IV (SSoT).
- [ ] T020 [P] [US1] Implement `src/preprocessing.py`: **Split data** for each tumor type into a `discovery_set` (for gene selection) and `training_set` (for model fitting) with a **stratified split maintaining the original class distribution** (FR‑013, Plan T020). **Output**: Save distinct CSV/Parquet files to `data/processed/{tumor_type}_discovery_set.csv` and `data/processed/{tumor_type}_training_set.csv`. **Dependency**: This task runs **after T016** (Batch Correction) to ensure split data is batch-corrected.
- [ ] T011 [P] [US1] Integration test for Feasibility Gate logic in `tests/integration/test_feasibility_gate.py`. **Requirement**: **Assert** that T014 writes `data/feasibility_gate.json` correctly in two specific scenarios: 1) **TCGA < 3**: Write `status: "halted"`, `reason: "insufficient_tcga_types"`. 2) **GEO < 2** (regardless of TCGA count): Write `status: "halted"`, `reason: "insufficient_geo_datasets"` and **halt execution**. **Logical Dependency**: T014 (implementation of the gate logic). **Clarification**: This test asserts that the pipeline DOES NOT proceed if GEO < 2, ensuring full compliance with the Independent Test requirement. The Independent Test is only valid if the gate passes. **Mocking**: Use mocked data files to simulate the TCGA < 3 and GEO < 2 scenarios to allow the test to run independently of network availability. The test must mock the creation of `data/feasibility_gate.json` to verify the file content and exit code. **Note**: This is a negative test case; the positive test case (running on a valid subset) is covered by the Independent Test in the spec.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Cross-Cancer Biomarker Identification (Priority: P2)

**Goal**: Perform differential expression analysis dynamically per LOO iteration, identify cross-tumor biomarkers using REML, and generate a fixed gene panel.

**Independent Test**: Verify the selection logic (intersection/union) can be executed on a small sample of discovery sets.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for REML meta-analysis calculation in `tests/unit/test_meta_analysis.py`
- [X] T022 [P] [US2] Integration test for LOO-Blind DE and panel selection logic on 3 tumor types (simulated) in `tests/integration/test_biomarker_discovery.py`

### Implementation for User Story 2

- [ ] T023a [US2] **Implement LOO Subsetting Logic**: In `src/biomarker_discovery.py`, implement a function to programmatically construct the list of all other tumor types (N-1) for a given held-out type `T`. **Constraint**: **DO NOT** include the held-out type `T` in this analysis to prevent data leakage. **Output**: Return list of file paths for the N-1 discovery sets. **Dependency**: Runs after T020 (Split). **Note**: This is a Plan-Defined Protocol refining Spec FR-006.
- [ ] T023b [US2] **Implement DE Analysis**: In `src/biomarker_discovery.py`, implement the DESeq2 Wald test execution on the N-1 subset provided by T023a (FDR < 0.05, |log2FC| > 1.0). **Dependency**: Runs after T023a. **Note**: This is a Plan-Defined Protocol refining Spec FR-006.
- [ ] T023c [US2] **Save DE Results**: In `src/biomarker_discovery.py`, save DE results to `data/processed/loo_iteration_{TUMOR_TYPE}_de_results.csv` where `TUMOR_TYPE` is the exact string from the dataset metadata. **Error Handling**: If the input type is missing, log a critical error and skip this iteration. **Dependency**: Runs after T023b.
- [ ] T023d [US2] **Orchestrate LOO Loop**: In `src/biomarker_discovery.py`, implement the main loop that iterates through all tumor types, calls T023a, T023b, and T023d for each, and ensures all iterations complete before aggregation. **Dependency**: Runs after T020 (Split). **Note**: This task orchestrates the full LOO process.
- [ ] T024c [US2] **Aggregate LOO Results & Execute Panel Selection**. **Logic**:
 1. **Collect**: Scan `data/processed/` for all files matching `loo_iteration_{TUMOR_TYPE}_de_results.csv`. **Sorting**: Sort files alphabetically by tumor type to ensure deterministic aggregation. **Pre-check**: If no files match, halt with error. **Dependency**: Runs after T023d (Orchestrator) completes all iterations.
 2. **Aggregate**: Load all collected files into a single list of significant genes per iteration. **Merge** these results into a consolidated file `data/processed/loo_aggregated_results.csv` to ensure data lineage.
 3. **Intersect**: Compute the intersection of significant genes across the aggregated results (≥2 tumor types).
 4. **Fallback**: If intersection is empty, compute the union of top-ranked genes (≤50).
 5. **Output**: Generate the final gene panel list and pass it to T025/T026 logic. **Requirement**: This task MUST execute the intersection logic and produce the final list before T025/T026 are called. **Dependency**: Runs after T023c.
- [ ] T025 [US2] Implement `src/meta_analysis.py`: Define function to compute intersection of significant genes across ≥2 tumor types (FR‑006). **Context**: This operates on the **aggregated results** from T024c, implementing the "LOO-Blind" interpretation of the Spec's "intersection across types" requirement.
- [ ] T026 [US2] Implement `src/meta_analysis.py`: Define function to fallback to **union of top‑ranked genes (≤50)** if intersection is empty; **must write `fallback_reason: "intersection_empty"` to `results/summary.md`** as a hard requirement (FR‑006).
- [ ] T027 [US2] Implement `src/meta_analysis.py`: Define function to compute **Random-Effects Meta-Analysis (REML)** p-values and rank genes. **Requirement**: **Explicitly implement REML** (e.g., using `metafor` or `statsmodels`) to account for correlation between tumor types. **Override Note**: This overrides Spec FR-006's mention of Stouffer's method to comply with Plan Constraints and Constitution Principle VII (Statistical Rigor). **Plan Reference**: See Plan Phase 2. **Documentation**: **MUST write `override_note: "REML used instead of Stouffer's per Plan Phase 2"` to `results/summary.md`** as a primary completion criterion (not a sub-task). **Input**: P-values and effect sizes from T023c (LOO-Blind results) aggregated by T024c. **Output**: Combined p-values and ranked gene list.
- [ ] T028 [US2] Implement `src/meta_analysis.py`: Save **the final selected gene panel** (post‑intersection/union/fallback) to `results/meta_analysis/gene_panel.json` (conforms to `contracts/gene_panel.schema.yaml`) (FR‑006, Plan T028). **Requirement**: Ensure `gene_panel.json` includes the `fallback_reason` flag if T026 was triggered.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Model Training and Validation (Priority: P3)

**Goal**: Build tumor‑type‑specific models using the fixed gene panel, perform nested CV, external validation, and statistical significance testing.

**Independent Test**: Train tumor‑specific models; run k‑fold nested CV on training set; validate on ≥2 GEO datasets; verify AUC ≥0.75 and calibration.

### Tests for User Story 3 (MANDATORY) ⚠️

- [ ] T029 [P] [US3] Contract test for model output schema in `tests/contract/test_model_schema.py`. **Requirement**: Verify that model output conforms to `model_output.schema.yaml` including all required fields. **Dependency**: T006c (Schema generation).
- [X] T030 [P] [US3] Integration test for full modeling and validation pipeline in `tests/integration/test_modeling.py`. **Requirement**: Use a small subset of `data/processed/` to verify end‑to‑end training, LOO, and external validation logic.
- [ ] T044a [P] [US3] Unit test for `train_model` edge cases in `tests/unit/test_modeling.py`. **Requirement**: Create fixtures for empty input and class imbalance, and implement `test_train_model_handles_edge_cases` covering empty input, class imbalance, and class-weighted metrics assertions. **Dependency**: T031 (Model Training). **Placement**: Must run BEFORE T031.
- [ ] T044b [P] [US3] Unit test for `nested_cv` parameter search and leakage prevention in `tests/unit/test_modeling.py`. **Requirement**: Create fixtures for CV input and leakage check, and implement `test_nested_cv_edge_cases` covering optimal parameter selection and data leakage prevention assertions. **Dependency**: T032 (Nested CV). **Placement**: Must run BEFORE T032.
- [ ] T044c [P] [US3] Unit test for `loo_validation` pre-check and loop logic in `tests/unit/test_modeling.py`. **Requirement**: Create fixtures for LOO small input and normal input, and implement `test_loo_validation_edge_cases` covering insufficient types halting and correct iteration assertions. **Dependency**: T033 (LOO Pre-check). **Placement**: Must run BEFORE T033.

### Implementation for User Story 3

- [ ] T033 [US3] **LOO Validation Pre-Check**: Implement `src/validation.py`.
 1. **Pre-Check**: Count distinct tumor types (N) present in the loaded training sets. **If N < 3**, **Terminate execution immediately** with exit code 1, **raise a RuntimeError with a clear message "LOO validation requires at least 3 tumor types; found N types"**, and write `data/feasibility_gate.json` (`status: "halted"`, `reason: "insufficient_loo_types"`). This ensures that after hold‑out, at least 2 types remain (N‑1 ≥ 2).
 2. **Input Check**: Verify that `data/processed/` contains `*_discovery_set.csv` and `*_batch_corrected.csv` files for all expected tumor types. If missing, halt with error "Missing required input files for LOO validation".
 3. **Output**: If N ≥ 3, proceed to T034.
- [ ] T031a [US3] Implement `src/modeling.py`: **Load and Validate Gene Panel**. Load `results/meta_analysis/gene_panel.json` (T028) before training. **Dependency**: T028.
- [ ] T031b [US3] Implement `src/modeling.py`: **Initialize Elastic-Net Model**. Set up the model architecture. **Dependency**: T031a.
- [ ] T031c [US3] Implement `src/modeling.py`: **Train Tumor‑type‑specific** Elastic‑Net Logistic Regression models using the **fixed gene panel** derived from Phase 2 (FR‑007). **Requirement**: Train one model per tumor type on the **full `training_set`** (not N-1 subsets). Do NOT pool data. **Dependency**: T031b.
- [ ] T032 [US3] Implement `src/modeling.py`: Perform **Nested Cross-Validation** on the **training_set** (FR‑007). **Logic**: **Load the fixed gene panel from `results/meta_analysis/gene_panel.json` (T028) BEFORE the CV loop begins**. **DO NOT** perform any gene selection or panel generation logic inside the nested CV loop. Use the fixed panel for all folds to prevent data leakage (FR‑013). **Dependency**: T028.
- [ ] T034 [US3] **Implement LOO Loop**: Implement `src/validation.py`.
 1. **Pre-Check**: Verify that `results/meta_analysis/gene_panel.json` exists and is non-empty. If missing, raise a clear error and halt.
 2. **Loop**: For each tumor type `T`:
 - **Subset**: Select data from all other tumor types (N-1).
 - **Re-train**: **Re-train** the elastic-net model on the N-1 types using the **fixed gene panel** from `results/meta_analysis/gene_panel.json`. **Do NOT** reuse models from T031 to avoid data leakage. This is a **validation loop**, distinct from the primary training in T031. **Explicitly state**: "This is a validation-only re-training distinct from T031".
 - **Test**: Evaluate on the held-out type `T`.
 - **Save**: **Save** LOO-specific models and metrics to `results/loo_iteration_{T}_metrics.json`.
 3. **Output**: Aggregate results across all LOO iterations.
- [ ] T035 [US3] Implement `src/validation.py`: **External GEO Validation**.
 1. **Read Method**: **Read** the batch correction method (e.g., "ComBat" or "Quantile_Matching") from `results/summary.md` using the key `batch_correction_method`. **Error Handling**: If the key is missing, raise an error.
 2. **Re-normalize**: Re-normalize each external GEO dataset to the TCGA VST scale.
 3. **Re-apply Correction**: **Re-apply** the recorded batch-correction method to align the new GEO data against the TCGA reference. **Clarification**: If the initial T016 run included GEO data, this step projects the new data into the existing latent space using the fitted ComBat parameters (or re-fits if necessary).
 4. **Validate**: Apply the trained per-type model (from T031) and compute ROC-AUC.
 5. **Fallback**: If no GEO datasets are available, set `external_validation_status: "skipped"` in `results/summary.md`.
- [ ] T036 [US3] Implement `src/validation.py`: Compute ROC‑AUC, Precision‑PR, and Calibration Curves (deciles) (FR‑009). For deciles with ≥20 samples, ensure deviation ≤ ±10%; otherwise report CI and flag as 'underpowered'.
- [ ] T037 [US3] Implement `src/validation.py`: Perform DeLong's test against clinical covariates‑only baseline (FR‑011).
- [ ] T038 [US3] Implement `src/validation.py`: Handle class imbalance: **use stratified k‑fold for ALL cases**; apply cost-sensitive learning **only if** responder ratio <20% (Edge Cases). **Reporting**: **Explicitly report** class-weighted performance metrics (e.g., balanced accuracy) in `results/summary.md` or `results/runtime_metrics.json`.
- [ ] T039 [US3] Implement `src/validation.py`: **Bonferroni Correction** (Single Source of Truth):
 1. **Pre‑Check**: Verify that `results/meta_analysis/gene_panel.json` exists and contains a non‑empty `selected` list. **If missing or empty, raise an error and halt**.
 2. **Scope Verification**: To verify discovery scope, **read and aggregate** all `data/processed/loo_iteration_{T}_de_results.csv` files generated by T023c. Calculate the total unique genes tested in the discovery phase from these files if needed for logging. **Pre-check**: If files are missing or empty, halt with error.
 3. **Meta‑Analysis**: Read `results/meta_analysis/gene_panel.json`. Calculate `m_meta` as the **number of genes in the final selected panel** (i.e., `len(selected_genes_in_panel)`). **Clarification**: This applies Bonferroni to the p-values of the genes *within the final panel*, consistent with the Plan's interpretation of "meta-analysis significance".
 4. **DeLong's Test**: Calculate `m_delong = number of model comparisons`. Apply correction where `m = m_delong`.
 5. **Threshold**: Adjusted p‑value must be < 0.01 (FR‑010). **Explicitly implement both distinct m calculations**, ensuring `m_meta` is derived from the final panel size regardless of whether it came from intersection or union.
- [ ] T040 [US3] Implement `src/main.py`: Enforce runtime timeout and memory limit using `psutil` and watchdog; **write `results/runtime_metrics.json`** with `timeout_triggered` and `peak_memory_mb` (FR‑012, SC‑004, SC‑005). **Enforcement**: **Kill the process and exit with a non-zero code if memory usage exceeds a defined threshold**; do not just report the violation.
- [ ] T041 [US3] Implement `src/main.py`: Generate `results/summary.md` with final metrics, panel size, validation results, and fallback flags (FR‑006, FR‑009). **Requirement**: **Check if `results/summary.md` exists**. **If it does not exist**, create it with default empty flags. **If it exists**, read existing flags (e.g., `fallback_reason`, `override_note`) from T016/T026/T027. **Merge** these with the new metrics. **Do NOT** overwrite without merging.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Documentation updates in `specs/001-chemo-biomarker-discovery/quickstart.md`
- [ ] T043 Code cleanup and refactoring
- [ ] T044 Performance optimization (sequential processing of tumor types to save RAM) (Plan: Sequential Processing)
- [ ] T046 Run `quickstart.md` validation to ensure full pipeline execution on CPU‑only runner

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

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/contract/test_data_schema.py"
Task: "Integration test for Feasibility Gate logic in tests/integration/test_feasibility_gate.py"

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
4. Add User Story 3 → Test independently → Deploy/Demo (Tumor‑specific Models & Validation)
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
- Avoid: vague tasks, same file conflicts, cross‑story dependencies that break independence
- **CPU Constraint**: All tasks must be implementable on a limited number of CPU cores, a constrained amount of RAM, and no GPU.
- **Data Integrity**: Never fabricate data; use real TCGA/GEO sources via verified mirrors. **Fallback to verified mock data only if real API fails verification**.
- **FR‑013 Compliance**: Strict separation of discovery (gene selection) and training (model fitting) sets is mandatory. DE is performed ONCE on the full discovery set (or N-1 subset for LOO).
- **FR‑007 Compliance**: Models must be tumor‑type‑specific, not pooled.
- **FR‑014 Compliance**: **ComBat** (for continuous VST data) is the primary method for batch correction; **fallback to Quantile Matching** if ComBat fails; **do NOT use ComBat-seq**.
- **FR‑008 Compliance**: LOO validation must halt if the dataset drops to a minimal number of types where LOO is invalid. The task logic must explicitly raise an error and exit.
- **FR‑010 Compliance**: Distinct Bonferroni correction logic for meta‑analysis (m = **number of genes in the final panel**) vs DeLong's test (m = comparisons). Ensure both are correctly calculated and applied.
- **FR‑006 Compliance**: The fallback to union of top-ranked genes must be explicitly triggered only when the intersection is empty, and the reason must be logged in `results/summary.md`.
- **FR‑001/002 Compliance**: Ensure all data downloads are verified against the expected checksums and that missing response labels cause the specific dataset to be skipped, not the entire pipeline, unless the minimum thresholds are not met. **Pipeline must halt if <2 valid GEO datasets exist**.
- **FR‑012 Compliance**: Ensure all tasks are optimized for the CPU-only GitHub Actions runner constraints (≤6h, ≤7GB RAM) by using streaming, chunked processing, and separate R processes where necessary. **Enforce** limits by killing the process if exceeded.
- **Meta-Analysis Method**: Use **Random-Effects Meta-Analysis (REML)** for cross-tumor integration as mandated by the Plan and Constitution, overriding Spec FR-006's mention of Stouffer's method. **Document** this override in `results/summary.md`.
- **LOO Pre-Check**: T033 MUST run before T031/T032 to ensure 'fail fast' logic.
- **External GEO Validation**: T034 MUST read the batch correction method from `results/summary.md` and re-apply it to new GEO data.
- **Bonferroni Scope**: T038 MUST aggregate `loo_iteration` files for scope verification, not rely on deprecated static files.
- **Summary Preservation**: T041 MUST read existing `results/summary.md` to preserve fallback flags.
- **Test Ordering**: Tests (T044a-c) MUST be placed BEFORE their corresponding implementation tasks (T031, T032, T034) in Phase 5.
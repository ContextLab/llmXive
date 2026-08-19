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

- [X] T004 Implement `src/config.py`: Define paths, random seeds, FDR thresholds, CPU/memory limits, `MAX_VARIANCE_GENES`, and `GEO_IDS` (default: `['GSE25055', 'GSE42752']`).
- [X] T005 [P] Implement `src/utils.py`: Logging setup, checksum generation, and timeout watchdog (h limit)
- [ ] T006 [Foundational] Implement schema files and checksums. **Logic**:
 1. **Define Content**: Define the following YAML content for the schemas in memory based on Spec Key Entities:
    - `dataset.schema.yaml`: Fields: `sample_id` (string), `tumor_type` (string), `response_label` (string), `expression_vector` (array of floats).
    - `model_output.schema.yaml`: Fields: `cancer_type` (string), `alpha` (float), `lambda` (float), `coefficients` (object), `cross_val_auc` (float).
    - `meta_analysis.schema.yaml`: Fields: `gene_symbol` (string), `meta_p_value` (float), `log2FC_mean` (float), `selected` (boolean).
 2. **Write Files**: Save the defined YAML content to `specs/001-chemo-biomarker-discovery/contracts/` (dataset.schema.yaml, model_output.schema.yaml, meta_analysis.schema.yaml).
 3. **Compute Checksums**: Compute SHA256 for each schema file and write to `state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml` in `artifact_hashes` map. **Constraint**: This task runs sequentially (write then checksum).
- [X] T007 Implement `src/__init__.py` and basic `src/main.py` orchestrator skeleton
- [X] T008 Setup `pytest` configuration and contract test harness for YAML schema validation
- [ ] T009 [Foundational] Implement `src/utils.py`: **Runtime Monitoring and Enforcement**. **Logic**:
 1. **Define Exception**: Define class `ResourceLimitExceeded(Exception)` in `src/utils.py` with message format: "Resource limit exceeded: [type] limit [value] exceeded. Per FR-012, SC-004, SC-005."
 2. **Implement Context Manager**: Create a context manager or decorator that tracks CPU time and memory usage (RSS) for any function it wraps.
 3. **Enforce Limits**: If usage exceeds `MAX_CPU_HOURS` (6) or `MAX_RAM_GB` (7), raise a `ResourceLimitExceeded` exception.
 4. **Docker Enforcement**: If R processes are spawned via Docker, ensure `docker run` includes flags `--cpus=2 --memory=7g` to enforce limits at the container level.
 5. **Watchdog**: Implement `watchdog.sh` script to monitor Docker container resource usage and kill the container if limits are exceeded.
 6. **Integration**: Integrate this into the main orchestrator to enforce SC-004 and SC-005. **Requirement**: This task MUST run sequentially after T004 and T005 to ensure global state is initialized correctly.
 7. **Logging**: Log warnings using the format "Warning: Resource usage approaching limit: [type] [current] / [max]" when usage exceeds 80%.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download TCGA/GEO data, verify response labels (Data Feasibility Gate), harmonize IDs, normalize data, and split into discovery/training sets.

**Independent Test**: Run acquisition on a subset of cancer types; verify `data/processed/` contains ≥100 samples per type, harmonized HGNC symbols, variance-stabilized values, and distinct discovery/training splits. **Note**: This test is only valid if the Data Feasibility Gate (T014) passes (i.e., ≥3 TCGA types and ≥2 valid GEO datasets are available). If the gate fails, the test is considered "Not Applicable" for that run configuration.

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `src/data_acquisition.py`: **TCGA Download, Sample Mapping, and Checksum**. **Logic**:
 1. **Check Mode**: Check for `TEST_MODE` environment variable. If `TEST_MODE=True`, allow proceeding with fewer than 3 types. If `TEST_MODE=False` (default), enforce the ≥3 type constraint in T014.
 2. **Select Types**: Query TCGA API using `TCGAbiolinks::GDCquery()` and `GDCprepare()`. Sort by sample count descending, then alphabetically. If `TEST_MODE=True` and <3 types are found, select all available.
 3. **Download**: Download RNA-seq HTSeq-Counts and clinical metadata for the selected types to `data/raw/`.
 4. **Sample Entity Mapping**: Parse raw data and create a `Sample` entity for each patient with attributes: `sample_id`, `tumor_type`, `response_label`, `expression_vector`. **Output**: Save mapped samples to `data/processed/tcga_samples.json`.
 5. **Checksum**: Compute SHA256 checksum only after successful download and verification.
 6. **State Update**: Write checksums to `state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml` in `artifact_hashes` map only for successful downloads.
 7. **Error Handling**: If `TEST_MODE=False` and <3 types are found, **log an error** but **DO NOT halt**. Write `data/feasibility_gate.json` with `status: "pending_tcga_check"`, `reason: "insufficient_tcga_types_found"`, `count: N`. Halt only if T014 determines it.
- [ ] T013 [P] [US1] Implement `src/data_acquisition.py`: **GEO Download and Sample Mapping**. **Algorithm**:
 1. Load `GEO_IDS` from `src/config.py`.
 2. Initialize `valid_geo_count = 0`.
 3. Iterate through configured GEO IDs.
 4. If a dataset file cannot be fetched, log an error, skip the file, and **DO NOT** write a checksum to the state file.
 5. If a dataset exists but lacks response labels (RECIST/CR/PR), **skip that specific dataset**, log a warning (e.g., "Skipping GSE...: missing response labels"), **do not increment `valid_geo_count`**, and **continue** to the next dataset.
 6. **Sample Entity Mapping**: For valid datasets, parse raw data and create a `Sample` entity for each patient with attributes: `sample_id`, `tumor_type`, `response_label`, `expression_vector`. **Output**: Save mapped samples to `data/processed/geo_samples.json`.
 7. **Checksum**: Compute SHA256 for each successfully downloaded and **verified** GEO file and append to `state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml` **only after verification is complete**.
 8. After iterating, check if `valid_geo_count` < 2. **Check Mode**: If `TEST_MODE=True`, allow proceeding. If `TEST_MODE=False` and `valid_geo_count` < 2, **log an error** but **DO NOT halt**. Write `data/feasibility_gate.json` with `status: "pending_geo_check"`, `reason: "insufficient_geo_datasets"`, `count: valid_geo_count`. Halt only if T014 determines it.
 9. Proceed to the Feasibility Gate (T014) using the **updated** `valid_geo_count` variable.
- [ ] T014 [P] [US1] **Data Feasibility Gate**: Implement `src/data_acquisition.py`.
 1. **TCGA Gate**: Read `data/feasibility_gate.json`. If `TEST_MODE=False` and the count of valid TCGA tumor types is **< 3**, **Terminate execution** with exit code 1 and write `data/feasibility_gate.json` with `status: "halted"`, `reason: "insufficient_tcga_types"`.
 2. **GEO Gate**: Read `data/feasibility_gate.json`. If `TEST_MODE=False` and `valid_geo_count` (datasets with labels) is **< 2**, **Terminate execution** with exit code 1 and write `data/feasibility_gate.json` with `status: "halted"` and `reason: "insufficient_geo_datasets"`.
 3. **Proceed**: If (TCGA ≥ 3 OR `TEST_MODE=True`) AND (valid_geo_count ≥ 2 OR `TEST_MODE=True`), write `data/feasibility_gate.json` with `status: "ready"`.
 4. **Logging**: Explicitly **log a warning if total download size > 5 GB** as specified in Spec FR‑001 before proceeding.
 5. **Exit**: **Explicitly exit with code 1** immediately after writing the halted JSON if any gate fails.
 6. **Dependency**: **Orchestrator must wait for T012 and T013 to complete before starting T014**.
- [ ] T017a [P] [US1] Implement `src/preprocessing.py`: **Filter** low‑expression genes (CPM < 1 in > 80% samples) (FR‑004). **Output**: Save filtered matrix. **Dependency**: Runs after T014 (Gate).
- [ ] T017b [P] [US1] Implement `src/preprocessing.py`: **Apply DESeq2 Variance‑Stabilizing Transformation (VST)** via rpy2 (FR‑004) on the filtered matrix. **Output**: Save VST matrix. **Dependency**: Runs after T017a.
- [ ] T017d [P] [US1] Implement `src/preprocessing.py`: **Normalization Failure Handling**. **Logic**:
 1. **Detect**: Check if any dataset failed to re-normalize to VST (e.g., incompatible format, missing data, wrong data types).
 2. **Log**: Log a warning for each excluded dataset: "Dataset {id} excluded due to normalization failure."
 3. **Update Artifact**: Update `data/processed/normalization_status.json` with excluded dataset IDs and reasons.
 4. **Proceed**: Continue with remaining datasets. If all datasets fail, halt with error.
- [ ] T016 [P] [US1] **Batch Correction**: Implement `src/preprocessing.py` to align platforms (FR‑014). **Logic**:
 1. **Step 1**: **Initialize** `results/summary.md` if it does not exist. This file will be appended to by later tasks.
 2. **Step 2**: **Primary Method**: Attempt to apply **ComBat-seq** (via `rpy2`/`sva::ComBat_seq`) on the combined VST-normalized matrix (TCGA + GEO). **Note**: This task runs **after T017b** (VST Normalization) and **before T020** (Split).
 3. **Step 3**: If ComBat-seq fails (e.g., due to batch size constraints), **attempt** Quantile Matching as a fallback using `sklearn.preprocessing.quantile_transform`.
 4. **Step 4**: If **both** ComBat-seq and Quantile Matching fail, **halt** the pipeline with a clear error message.
 5. **Requirement**: **Use ComBat-seq as the primary method** as mandated by Spec FR-014. **Logging & Documentation**: Record `batch_correction_method: "ComBat_seq"` or `batch_correction_method: "Quantile_Matching"` in `results/summary.md` upon success. **Mandatory**: Write `override_note: "ComBat_seq used as primary method per Spec FR-014"` to `results/summary.md` to satisfy Constitution Principle IV (SSoT). **Output**: Save batch correction parameters to `results/batch_correction_config.json` immediately upon success.
- [ ] T020 [P] [US1] Implement `src/preprocessing.py`: **Split data** for each tumor type into a `discovery_set` (for gene selection) and `training_set` (for model fitting) with a **stratified split maintaining the original class distribution** (FR‑013, Plan T020). **Output**: Save distinct CSV/Parquet files to `data/processed/{tumor_type}_discovery_set.csv` and `data/processed/{tumor_type}_training_set.csv`. **Dependency**: This task runs **after T016** (Batch Correction) to ensure split data is batch-corrected.
- [ ] T011 [P] [US1] Integration test for Feasibility Gate logic in `tests/integration/test_feasibility_gate.py`. **Requirement**: **Assert** that T014 writes `data/feasibility_gate.json` correctly in two specific scenarios: 1) **TCGA < 3**: Write `status: "halted"`, `reason: "insufficient_tcga_types"`. 2) **GEO < 2** (regardless of TCGA count): Write `status: "halted"` and **halt execution**. **Logical Dependency**: T014 (implementation of the gate logic). **Clarification**: This is a negative test case; the positive test case (running on a valid subset) is covered by the Independent Test in the spec.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Cross-Cancer Biomarker Identification (Priority: P2)

**Goal**: Perform differential expression analysis on the full discovery set, identify cross-tumor biomarkers using Stouffer's method, and generate a fixed gene panel.

**Independent Test**: Verify the selection logic (intersection/union) can be executed on a small sample of discovery sets.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for Stouffer's meta-analysis calculation in `tests/unit/test_meta_analysis.py`
- [X] T022 [P] [US2] Integration test for LOO-Blind DE and panel selection logic on 3 tumor types (simulated) in `tests/integration/test_biomarker_discovery.py`

### Implementation for User Story 2

- [ ] T023 [US2] **Implement Per-Tumor-Type DE on Full Discovery Set**. In `src/biomarker_discovery.py`:
 1. **Load Data**: Iterate through all tumor types. For each type $T$, load `data/processed/{T}_discovery_set.csv`.
 2. **DE Analysis**: Execute the DESeq2 Wald test on the **full discovery set** for each tumor type (FDR < 0.05, |log2FC| > 1.0). **Input**: Construct DESeqDataSet from `data/processed/{tumor_type}_discovery_set.csv` using R code.
 3. **Save**: Save DE results to `data/processed/{tumor_type}_de_results.csv`.
 4. **Error Handling**: If a tumor type has < 10 samples, skip DE for that type and log a warning.
 5. **Aggregation**: After all iterations, scan `data/processed/` for all `{tumor_type}_de_results.csv` files, sort them alphabetically, and merge results into `data/processed/static_aggregated_results.csv`. **Note**: This task produces the input for T024.
- [ ] T024 [US2] **Generate Static Gene Panel**. **Logic**:
 1. **Collect**: Load `data/processed/static_aggregated_results.csv`.
 2. **Intersect**: Compute the intersection of significant genes across ≥2 tumor types using thresholds **FDR < 0.05** and **|log2FC| > 1.0**.
 3. **Fallback**: If intersection is empty, compute the union of all significant genes. **Rank** genes by descending mean log2FC, then ascending meta p-value (calculated on the full set), then select a representative subset. **Requirement**: **Must write `fallback_reason: "intersection_empty"` to `results/meta_analysis/panel_status.json`** as a hard requirement (FR‑006).
 4. **Meta-Analysis**: Compute **Stouffer's meta-analysis** p-values using **`scipy.stats.combine_pvalues`** (method='stouffer') on the aggregated p-values. **Requirement**: **Explicitly implement Stouffer's method** to comply with Spec FR-006. **Documentation**: **MUST write `override_note: "Stouffer's method used as per Spec FR-006"` to `results/meta_analysis/panel_status.json`**.
 5. **Output**: Generate the final gene panel list and save to `results/meta_analysis/gene_panel.json` (conforms to `contracts/gene_panel.schema.yaml`). **Requirement**: Ensure `gene_panel.json` includes the `fallback_reason` flag if the fallback logic was triggered. **Output**: Also save `results/meta_analysis/panel_status.json` with `fallback_reason` and `override_note`.
- [ ] T025 [US2] **Remove**: This task has been merged into T024.
- [ ] T026 [US2] **Remove**: This task has been merged into T024.
- [ ] T027 [US2] **Remove**: This task has been merged into T024.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Model Training and Validation (Priority: P3)

**Goal**: Build tumor‑type‑specific models using the fixed gene panel, perform nested CV, external validation, and statistical significance testing.

**Independent Test**: Train tumor‑type‑specific models; run k‑fold nested CV on training set; validate on ≥2 GEO datasets; verify AUC ≥0.75 and calibration.

### Tests for User Story 3 (MANDATORY) ⚠️

- [ ] T029 [P] [US3] Contract test for model output schema in `tests/contract/test_model_schema.py`. **Requirement**: Verify that model output conforms to `model_output.schema.yaml` including all required fields. **Dependency**: T006 (Schema generation).
- [X] T030 [P] [US3] Integration test for full modeling and validation pipeline in `tests/integration/test_modeling.py`. **Requirement**: Use a small subset of `data/processed/` to verify end‑to‑end training, LOO, and external validation logic.
- [ ] T044a [US3] Unit test for `train_model` edge cases in `tests/unit/test_modeling.py`. **Requirement**: Create fixtures for empty input and class imbalance, and implement `test_train_model_handles_edge_cases` covering empty input, class imbalance, and class-weighted metrics assertions. **Dependency**: Runs after T031 (Model Training). **Placement**: Must run AFTER T031.
- [ ] T044b [US3] Unit test for `nested_cv` parameter search and leakage prevention in `tests/unit/test_modeling.py`. **Requirement**: Create fixtures for CV input and leakage check, and implement `test_nested_cv_edge_cases` covering optimal parameter selection and data leakage prevention assertions. **Dependency**: Runs after T032 (Nested CV). **Placement**: Must run AFTER T032.
- [ ] T044c [US3] Unit test for `loo_validation` pre-check and loop logic in `tests/unit/test_modeling.py`. **Requirement**: Create fixtures for LOO small input and normal input, and implement `test_loo_validation_edge_cases` covering insufficient types halting and correct iteration assertions. **Dependency**: Runs after T033 (LOO Pre-check). **Placement**: Must run AFTER T033.

### Implementation for User Story 3

- [ ] T033 [US3] **LOO Validation Pre-Check**: Implement `src/validation.py`.
 1. **Pre-Check**: Count distinct tumor types (N) present in the loaded training sets. **If N < 3**, **Terminate execution immediately** with exit code 1, **raise a RuntimeError with a clear message "LOO validation requires at least 3 tumor types; found N types"**, and write `data/feasibility_gate.json` (`status: "halted"`, `reason: "insufficient_loo_types"`). This ensures that after hold‑out, at least 2 types remain (N‑1 ≥ 2).
 2. **Input Check**: Verify that `data/processed/` contains `*_discovery_set.csv` and `*_batch_corrected.csv` files for all expected tumor types. If missing, halt with error "Missing required input files for LOO validation".
 3. **Output**: If N ≥ 3, proceed to T035.
- [ ] T031 [US3] **Implement tumor-type-specific Elastic-Net model training**: In `src/modeling.py`:
 1. **Load and Validate Gene Panel**: Load `results/meta_analysis/gene_panel.json` (T024) before training. **Dependency**: T024 (Static Panel Generation). **Constraint**: **DO NOT** perform any gene selection or panel generation logic inside the nested CV loop. Use the fixed panel for all folds to prevent data leakage (FR‑013).
 2. **Initialize Elastic-Net Model**: Set up the model architecture.
 3. **Train**: Train one model per tumor type on the **full `training_set`** (not N-1 subsets). Do NOT pool data.
 4. **Nested CV**: Perform **Nested Cross-Validation** on the **training_set** (FR‑007). **Logic**: **Load the fixed gene panel from `results/meta_analysis/gene_panel.json` (T024) BEFORE the CV loop begins**. **DO NOT** perform any gene selection or panel generation logic inside the nested CV loop. Use the fixed panel for all folds to prevent data leakage (FR‑013). **Hyperparameters**: Use `alpha=[0.1, 0.5, 0.9]` and `lambda=[0.01, 0.1, 1.0]` with 5-fold outer CV.
 5. **Persist**: **Extract and save the `cross_val_auc` metric** into the Model artifact in `results/models/` (conforming to `model_output.schema.yaml`). **Dependency**: T032 (Nested CV).
- [ ] T032 [US3] **Nested Cross-Validation and Metric Extraction**: In `src/modeling.py`, implement the nested CV loop.
 1. **Run Nested CV**: Execute the nested CV loop for each tumor type.
 2. **Extract Metric**: **Explicitly extract the `cross_val_auc` metric** from the inner/outer loop results.
 3. **Persist**: Save the extracted `cross_val_auc` to the Model artifact in `results/models/` (conforming to `model_output.schema.yaml`). **Output**: The `Model` entity with `cross_val_auc` populated. **Dependency**: Runs after T031 (initialization).
- [ ] T035 [US3] **Implement LOO Re-training Logic**: In `src/validation.py`, implement the core loop for Leave-One-Cancer-Type-Out validation. For each tumor type $T_i$:
 1. **Load Static Panel**: Load `results/meta_analysis/gene_panel.json` (T024). **DO NOT** perform DE or meta-analysis.
 2. **Subset**: Load N-1 training sets (excluding $T_i$). **Filter** to include ONLY samples labeled as 'training_set'.
 3. **Sample Check**: If a tumor type has < 10 samples, skip DE for that type and log a warning (Note: This check is primarily for DE, but if a training set is too small, log a warning and skip model training for that type).
 4. **Train**: Train Elastic-Net on N-1 training sets using the **static gene panel**.
 5. **Evaluate**: Predict on $T_i$ validation set (training set of $T_i$). **Output**: Save LOO validation results to `results/loo_validation_results.json`. **Dependency**: Runs after T033.
- [ ] T036 [US3] **Implement LOO Evaluation and Save**: In `src/validation.py`, aggregate results from T035. Compute **Performance Drop** = (Internal CV AUC) - (LOO AUC). If Drop > 0.10, flag as poor generalizability. Save results to `results/loo_validation_results.json`. **Dependency**: Runs after T035.
- [ ] T037 [US3] Implement `src/validation.py`: **External GEO Validation**.
 1. **Pre-Check**: Verify that `data/raw/` contains `GSE25055` and `GSE42752` (or other configured GEO IDs). If missing, **halt with error** "Required GEO datasets for external validation are missing".
 2. **Read Method**: **Read** the batch correction method (e.g., "ComBat_seq" or "Quantile_Matching") from `results/batch_correction_config.json` (T016). **Error Handling**: If the file is missing, **re-fit on combined TCGA reference** or **halt with error** if parameters are unavailable.
 3. **Re-normalize**: Re-normalize each external GEO dataset to the TCGA VST scale.
 4. **Re-apply Correction**: **Re-apply** the recorded batch-correction method to align the new GEO data against the TCGA reference. **Clarification**: If the initial T016 run included GEO data, this step projects the new data into the existing latent space using the fitted ComBat parameters (or re-fits if necessary). **Fallback**: If saved parameters are missing, re-fit on combined TCGA reference.
 5. **Validate**: Apply the trained per-type model (from T031) and compute ROC-AUC.
 6. **Fallback**: If no GEO datasets are available, set `external_validation_status: "skipped"` in `results/summary.md`.
- [ ] T038 [US3] Implement `src/validation.py`: Compute ROC‑AUC, Precision‑PR, and Calibration Curves (deciles) (FR‑009). For deciles with ≥20 samples, ensure deviation ≤ ±10%; otherwise report CI and flag as 'underpowered'.
- [ ] T039a [US3] Implement `src/validation.py`: **Baseline Model Training and Persistence**. **Logic**:
 1. **Load Covariates**: Load clinical covariates (age, stage, etc.) for the validation sets from `data/processed/tcga_samples.json` or GEO metadata. **Error Handling**: If covariates are missing for a GEO dataset, **report N/A for that cohort** and skip baseline training for that specific dataset, logging the reason "Covariates missing for {cohort}".
 2. **Train**: Train a logistic regression model using **only** clinical covariates (no gene expression).
 3. **Predict**: Generate predictions on the validation sets.
 4. **Save**: Save baseline model to `results/baseline_model.pkl` and metrics to `results/baseline_metrics.json`. **Dependency**: Runs before T039.
- [ ] T039 [US3] Implement `src/validation.py`: Perform DeLong's test against clinical covariates‑only baseline (FR‑011). **Dependency**: T039a. **Error Handling**: If baseline metrics are N/A for a cohort (from T039a), **skip DeLong's test for that cohort and log the reason**.
- [ ] T040 [US3] Implement `src/validation.py`: Handle class imbalance: **use stratified k‑fold for ALL cases**; apply cost-sensitive learning **only if** responder ratio <20% (Edge Cases). **Reporting**: **Explicitly report** class-weighted performance metrics, specifically **balanced accuracy**, in `results/summary.md` or `results/runtime_metrics.json`. **Requirement**: If cost-sensitive learning is applied, the report MUST include the balanced accuracy metric.
- [ ] T041 [US3] Implement `src/validation.py`: **Bonferroni Correction** (Single Source of Truth):
 1. **Pre‑Check**: Verify that `results/meta_analysis/gene_panel.json` exists and contains a non‑empty `selected` list. **If missing or empty, raise an error and halt**.
 2. **Scope Verification**: To verify discovery scope, **read and aggregate** all `data/processed/{tumor_type}_de_results.csv` files generated by T023. Calculate the total unique genes tested in the discovery phase from these files if needed for logging. **Pre-check**: If files are missing or empty, halt with error.
 3. **Meta‑Analysis**: Read `results/meta_analysis/gene_panel.json`. Calculate `m_meta` as the **number of genes in the final selected panel** (i.e., `len(selected_genes_in_panel)`). **Clarification**: This applies Bonferroni to the p-values of the genes *within the final panel*, consistent with the Plan's interpretation of "meta-analysis significance".
 4. **DeLong's Test**: Calculate `m_delong = number of tumor types for which a model was trained and validated`. Apply correction where `m = m_delong`.
 5. **Threshold**: Adjusted p‑value must be < 0.01 (FR‑010). **Explicitly implement both distinct m calculations**, ensuring `m_meta` is derived from the final panel size regardless of whether it came from intersection or union.
- [ ] T042 [US3] Implement `src/validation.py`: **Summary Merge Logic**. Implement a function to read existing flags (e.g., `fallback_reason`, `override_note`, `batch_correction_method`) from `results/summary.md` (if it exists) and **merge** them with new metrics. **Dependency**: Runs after T041. **Note**: This task does NOT overwrite; it appends/updates specific keys.
- [ ] T043 [US3] Implement `src/validation.py`: **Final Summary Generation**. Generate `results/summary.md` with final metrics, panel size, validation results, and fallback flags (FR‑006, FR‑009). **Requirement**: **Check if `results/summary.md` exists**. **If it does not exist**, create it with default empty flags. **If it exists**, read existing flags from T016/T024/T042. **Merge** these with the new metrics. **Do NOT** overwrite without merging. **Dependency**: Runs after T042.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 [P] Documentation updates in `specs/001-chemo-biomarker-discovery/quickstart.md`
- [ ] T045 Code cleanup and refactoring
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

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Constraint**: All tasks must be implementable on a limited number of CPU cores, a constrained amount of RAM, and no GPU.
- **Data Integrity**: Never fabricate data; use real TCGA/GEO sources via verified mirrors. **Fallback to verified mock data only if real API fails verification**.
- **FR‑013 Compliance**: Strict separation of discovery (gene selection) and training (model fitting) sets is mandatory. DE is performed ONCE on the full discovery set (or N-1 subset for LOO).
- **FR‑007 Compliance**: Models must be tumor‑type‑specific, not pooled.
- **FR‑014 Compliance**: **ComBat-seq** (for discrete count data) is the primary method for batch correction; **fallback to Quantile Matching** if ComBat-seq fails; **do NOT use ComBat** (continuous) as the primary method.
- **FR‑008 Compliance**: LOO validation must halt if the dataset drops to a minimal number of types where LOO is invalid. The task logic must explicitly raise an error and exit.
- **FR‑010 Compliance**: Distinct Bonferroni correction logic for meta-analysis (m = **number of genes in the final panel**) vs DeLong's test (m = comparisons). Ensure both are correctly calculated and applied.
- **FR‑006 Compliance**: The fallback to union of top-ranked genes must be explicitly triggered only when the intersection is empty, and the reason must be logged in `results/meta_analysis/panel_status.json`.
- **FR‑001/002 Compliance**: Ensure all data downloads are verified against the expected checksums and that missing response labels cause the pipeline to skip the offending dataset instead of halting entirely unless there's insufficient data.
- **TEST_MODE**: Set `TEST_MODE=True` environment variable to allow the pipeline to proceed with fewer than 3 TCGA types or 2 GEO datasets for Independent Testing purposes.
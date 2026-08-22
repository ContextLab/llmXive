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
- [X] T005a [Foundational] Implement `src/utils.py`: **Resource Detection**. **Logic**:
 1. **Define Exception**: Define class `ResourceWarning` (not exception) in `src/utils.py` with message format: "Warning: Resource usage approaching limit: [type] [current] / [max]. Per FR-012, SC-004, SC-005."
 2. **Implement Detection**: Create a function `detect_resources()` that reads `/proc/cgroup` and environment variables (`DOCKER_CPUS`, `DOCKER_MEMORY`) to detect available CPU cores and RAM (GB) inside a Docker container. If not in Docker, fallback to `multiprocessing.cpu_count()` and `psutil.virtual_memory().total`.
 3. **Calculate Caps**: Calculate capped values as the minimum of detected resources and safe thresholds (time, storage) as mandated by FR-012, SC-004, and SC-005.
 4. **Integration**: Return these capped values for use by the Docker orchestrator. **Requirement**: This task MUST run sequentially after T004 to ensure global state is initialized correctly.
 5. **Logging**: Log warnings using the format "Warning: Resource usage approaching limit: [type] [current] / [max]" when usage exceeds a substantial majority threshold.
 **Requirements**: FR-012, SC-004, SC-005.
- [X] T005b [Foundational] Implement `src/utils.py`: **Docker Enforcement**. **Logic**:
 1. **Implement Wrapper**: Create a function `build_docker_run_cmd(image, volume, cpus, memory)` that constructs the `docker run` command with `--cpus=<capped_cores>` and `--memory=<capped_ram>g` flags.
 2. **Error Handling**: If `cpus` or `memory` are not provided, default to the values from `detect_resources()`.
 3. **Integration**: Integrate this into the main orchestrator to enforce SC-004 and SC-005 by passing these flags when invoking R containers.
 4. **Constraint**: Do NOT raise a hard-stop exception for resource limits; rely on the runner's native OOM/timeout handling. Instead, log warnings and cap resources.
 **Requirements**: FR-012, SC-004, SC-005.
- [X] T006 [Foundational] Implement schema files and checksums. **Logic**:
 1. **Define Content**: Define the following YAML content for the schemas in memory based on Spec Key Entities:
 - `dataset.schema.yaml`: Fields: `sample_id` (string), `tumor_type` (string), `response_label` (string), `expression_vector` (array of floats).
 - `model_output.schema.yaml`: Fields: `cancer_type` (string), `alpha` (float), `lambda` (float), `coefficients` (object), `cross_val_auc` (float).
 - `gene_panel.schema.yaml`: Fields: `gene_symbol` (string), `meta_p_value` (float), `log2FC_mean` (float), `selected` (boolean).
 2. **Write Files**: Save the defined YAML content to `specs/001-chemo-biomarker-discovery/contracts/` (`dataset.schema.yaml`, `model_output.schema.yaml`, `gene_panel.schema.yaml`).
 3. **Compute Checksums**: Compute SHA256 for each schema file and write to `state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml` in `artifact_hashes` map. **Constraint**: This task runs sequentially (write then checksum).
- [X] T006_1 [Foundational] Implement `aggregate_significance_resolved.schema.yaml`. **Logic**:
 1. **Define Content**: Define a YAML schema for `aggregate_significance_resolved.json` with fields: `gene_symbol` (string), `tumor_type` (string), `p_value` (float).
 2. **Write File**: Save to `specs/001-chemo-biomarker-discovery/contracts/`.
 3. **Compute Checksum**: Compute SHA256 and update `state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml`.
 4. **Dependency**: Runs after T006.
- [X] T007a [P] [Foundational] Implement `src/main.py`: **Entry Point**. **Logic**:
 1. **Define Entry**: Implement `if __name__ == '__main__':` block that calls `run_pipeline()`.
 2. **Argument Parsing**: Use `argparse` to accept optional `--config` and `--test-mode` flags.
 3. **Error Handling**: Catch any unhandled exceptions and log them to `logs/error.log` before exiting.
 **Requirements**: FR-012.
- [X] T007b [P] [Foundational] Implement `src/main.py`: **Orchestrator Function**. **Logic**:
 1. **Define Function**: Implement `def run_pipeline(config_path: str, test_mode: bool = False) -> bool:`.
 2. **Logic**: Load config, execute data acquisition, preprocessing, DE, meta-analysis, modeling, and validation in sequence.
 3. **Return**: Return `True` if successful, `False` otherwise.
 **Requirements**: FR-012.
- [X] T008 Setup `pytest` configuration and contract test harness for YAML schema validation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download TCGA/GEO data, verify response labels (Data Feasibility Gate), harmonize IDs, normalize data, and split into discovery/training sets.

**Independent Test**: Run acquisition on a subset of cancer types; verify `data/processed/` contains ≥100 samples per type, harmonized HGNC symbols, variance‑stable values, and distinct discovery/training splits. **Note**: This test is only valid if the Data Feasibility Gate (T014) passes (i.e., ≥3 TCGA types and ≥2 valid GEO datasets). If the gate fails, the test is considered "Not Applicable" for that run configuration.

### Implementation for User Story 1

- [X] T012a [US1] [P] Implement `src/scripts/run_tcga_download.R`: **TCGA R Script with Filtering**. **Logic**:
 1. **Input**: TCGA project IDs (from config).
 2. **Logic**: Use `TCGAbiolinks` R package to download RNA-seq HTSeq-Counts and clinical metadata within the Dockerized R environment.
 3. **Filtering**: Explicitly filter for tumor types with ≥3 available types and ≥50 samples each. If <3 types are found, log a warning and return the available types.
 4. **Output**: Write raw counts and metadata to `data/raw/` and `results/validation_status.json` with the list of available types.
 5. **Constraint**: This task MUST run before T014.
 **Requirements**: FR-001.
- [X] T013a [US1] [P] Implement `src/scripts/run_geo_download.R`: **GEO R Script with Filtering**. **Logic**:
 1. **Input**: GEO accession numbers (from config).
 2. **Logic**: Use `GEOquery` to download expression data and clinical metadata.
 3. **Filtering**: Explicitly filter for datasets with response annotations. If <2 datasets are found, log a warning and return the available datasets.
 4. **Output**: Write raw data to `data/raw/`.
 5. **Constraint**: This task MUST run before T014.
 **Requirements**: FR-002.
- [X] T014 [US1] **Data Feasibility Gate**: Implement `src/data_acquisition.py`. **Update**: Explicitly mandate that if the gate fails (insufficient data), the script MUST log a warning and proceed with the available data if ≥2 valid GEO and ≥3 TCGA types are present; otherwise, it MUST log a critical error and exit with code 1. **No exception raising**; rely on log-based failure.
- [X] T011 [US1] Integration test for Feasibility Gate logic in `tests/integration/test_feasibility_gate.py`. **Update**: This test MUST include a case where the gate fails (insufficient data) to verify the logging and halting mechanism works correctly. *(Logic unchanged)*
- [X] T017b [US1] Implement `src/preprocessing.py`: **Apply DESeq2 VST** via rpy2. **Update**: Explicitly mandate that the output file for each tumor type is named `{tumor_type}_discovery_vst.csv` and note that this initial output is the **raw DESeq2 matrix format** (genes as rows, samples as columns, or vice versa depending on R version), requiring explicit transposition to ensure consistent wide format. This ensures compatibility with T017b_1. *(Logic updated)*
- [X] T017b_1 [US1] Implement `src/preprocessing.py`: **Transpose VST Output**. **Logic**:
 1. **Input**: Raw DESeq2 matrix format output from T017b.
 2. **Logic**: Explicitly transpose the matrix so that **Rows = Genes** and **Columns = Samples** (wide format).
 3. **Output**: Write `{tumor_type}_discovery_vst.csv` in wide format.
 4. **Constraint**: This task MUST run after T017b and before T023a.
 **Requirements**: FR-003, FR-005.
- [X] T017a [US1] Implement `src/preprocessing.py`: **Filter low‑expression genes (CPM < 1 in > 80% samples)**. **Update**: Explicitly state that missing data in GEO datasets will be handled via complete case analysis (row removal), with no imputation. *(Logic unchanged)*
- [X] T017c [US1] Implement `src/preprocessing.py`: **Harmonize Gene Identifiers** (Ensembl/Entrez → HGNC). *(Logic unchanged)*
- [X] T017d [US1] Implement `src/preprocessing.py`: **Normalization Failure Handling**.
 1. After attempting VST on each dataset, if a dataset cannot be re‑normalized (e.g., incompatible format), log a warning `"Normalization failed for {dataset_id}: {reason}"` and update `data/normalization_status.json` with status `"failed"` for that dataset.
 2. If *all* datasets fail, raise a `RuntimeError` and halt execution with exit code 1.
 3. Successful normalizations are recorded with status `"success"` in the same JSON file.
 4. This satisfies US‑1 Edge Case 3 (datasets that cannot be re‑normalized are excluded with a logged warning) and ensures a clear halt when no data remain.
- [X] T016 [US1] **Batch Correction**: Implement `src/preprocessing.py` to align platforms (FR‑014). **Update**: ComBat-seq is the ONLY primary method; Quantile Matching is ONLY a fallback if ComBat-seq fails on discrete data. Ensure splitting (T020) logic is finalized before batch correction to prevent leakage. **Halt Condition**: If both ComBat-seq and Quantile Matching fail for a dataset, exclude the dataset with a warning. If the number of valid datasets drops below the required minimum (FR-002), halt execution. *(Logic updated)*
- [X] T020 [US1] Implement `src/preprocessing.py`: **Split data** for each tumor type into `discovery_set` and `training_set` with stratified class distribution (FR‑013). **Update**:
 1. Ensure splitting occurs BEFORE any batch correction or cross-tumor operations to prevent data leakage.
 2. Include a step to monitor RAM usage during the split operation and log a warning if limits are breached (SC-005).
 3. Verify that the split maintains distinct discovery and training sets for each tumor type as required by FR-013.
 4. **Output Schema**: Explicitly generate `{tumor_type}_discovery_vst.csv` and `{tumor_type}_discovery_metadata.csv` to match the input schema of T023a. *(Logic updated)*

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Cross-Cancer Biomarker Identification (Priority: P2)

**Goal**: Perform differential expression analysis on the full discovery set, identify cross‑tumor biomarkers using Stouffer's method, and generate a fixed gene panel.

**Independent Test**: Verify the selection logic (intersection/union) can be executed on a small sample of discovery sets.

### Tests for User Story 2 (OPTIONAL)

- [X] T021 [P] [US2] Unit test for Stouffer's meta‑analysis calculation in `tests/unit/test_meta_analysis.py`
- [X] T022 [P] [US2] Integration test for LOO‑Blind DE and panel selection logic on 3 tumor types (simulated) in `tests/integration/test_biomarker_discovery.py`

### Implementation for User Story 2

- [X] T023a [US2] **Implement Python Orchestrator Wrapper for DE**. **Logic**:
 1. **Input**: `{tumor_type}_discovery_vst.csv` from T020.
 2. **Logic**: Construct the `docker run` command to invoke `run_deseq2.R` (T023a_1).
 3. **Validation**: Verify input file exists and matches schema before invoking.
 4. **Error Handling**: If the R script exits with non-zero status, log stderr and raise `RuntimeError`. No synthetic fallback.
 5. **Verification**: Immediately after execution, verify the output contains only genes with `padj < 0.05` and `|log2FC| > 1.0`. If invalid, halt and log error.
 6. **Constraint**: This task MUST run after T020.
 **Requirements**: FR-005.
- [X] T023a_1 [US2] **Implement R Script for DE Analysis**. **Logic**:
 1. **Create File**: `src/scripts/run_deseq2.R`.
 2. **Input Schema**: Wide format CSV (Rows=Genes, Cols=Samples).
 3. **DESeq2 Logic**: Load counts, construct DESeqDataSet, run `DESeq()`, extract results with `lfcThreshold = 1.0` and `altHypothesis = "greaterAbs"`. **Pin DESeq version to 1.40.0 or later via renv lockfile in Docker context**.
 4. **Output**: Write `{tumor_type}_de_results.csv` with columns: `gene_symbol`, `log2FoldChange`, `pvalue`, `padj`.
 5. **Constraint**: This task MUST run after T020.
 **Requirements**: FR-005.
- [X] T023a_2 [US2] **DE Threshold Verification**. **Logic**:
 1. **Input**: `{tumor_type}_de_results.csv` from T023a_1.
 2. **Logic**: Verify that the R script output contains only genes with `padj < 0.05` and `|log2FC| > 1.0`.
 3. **Action**: If the output contains genes outside these thresholds, log a critical error and halt.
 4. **Dependency**: Runs after T023a_1.
 **Requirements**: FR-005.
- [X] T023b [US2] **Aggregate DE Results**.
 1. Load DE results from all tumor types in `results/de/`.
 2. Aggregate significant genes (FDR < 0.05, |log2FC| > 1.0) across types.
 3. Output a unified list of significant genes per tumor type to `results/de/aggregate_significance.json`.
 4. **Output Schema**: The file MUST contain a dictionary: `{gene_symbol: {tumor_type: p_value}}` to support Stouffer's method. *(Logic updated)*
- [X] T023b_1 [US2] **Resolve Naming Conflicts and Format for Meta-Analysis**.
 1. Load `results/de/aggregate_significance.json` from T023b.
 2. **HGNC Validation**: Use `biopython` or a local HGNC mapping file to validate gene symbols. Invalid symbols are dropped.
 3. **Action**: Log dropped symbols.
 4. Structure the data into a dictionary: `{gene_symbol: {tumor_type: p_value}}`.
 5. Output the resolved and structured data to `results/de/aggregate_significance_resolved.json`.
 6. **Dependency**: Runs after T023b.
 **Requirements**: FR-003.
- [X] T023b_2 [US2] **Output Final Aggregated Data**.
 1. Validate `results/de/aggregate_significance_resolved.json` against `aggregate_significance_resolved.schema.yaml` (defined in T006_1).
 2. Log summary of aggregated genes.
 3. **Dependency**: Runs after T023b_1 and T006_1. *(New Task)*
- [X] T023c [US2] **Generate Union Fallback Logic**.
 1. Check if the intersection of significant genes across ≥2 tumor types is empty.
 2. If empty, compute the union of top-ranked genes (≤50) based on descending mean log2FC then ascending meta-p-value.
 3. Set `fallback_reason: "intersection_empty"` in `results/meta_analysis/panel_status.json`.
 4. Output the union list to `results/meta_analysis/union_fallback.json`.
 5. **Dependency**: Runs after T023b_2.
- [X] T023c_2 [US2] **Output Union Fallback**.
 1. Validate `results/meta_analysis/union_fallback.json`.
 2. **Dependency**: Runs after T023c. *(New Task)*
- [X] T024a [US2] **Implement Stouffer's Meta‑Analysis**.
 1. Compute combined p‑values using `scipy.stats.combine_pvalues(..., method='stouffer')`.
 2. Input: P-values for each gene across tumor types from `results/de/aggregate_significance_resolved.json` (output of T023b_1).
 3. Output: `results/meta_analysis/stouffer_meta.csv` with gene symbols and combined p-values.
 4. Write `m_meta` (number of genes in final panel) to `results/meta_analysis/bonferroni_correction.json` for later use.
 5. **Dependency**: Runs after T023b_2.
- [X] T024b_1 [US2] **Compute Intersection**.
 1. Load DE results and Stouffer meta‑p‑values.
 2. Compute intersection of significant genes (FDR < 0.05, |log2FC| > 1.0) across ≥2 tumor types.
 3. Output intersection list to `results/meta_analysis/intersection.json`.
 4. **Dependency**: Runs after T024a. *(New Task)*
- [X] T024b_2 [US2] **Compute Fallback Union**.
 1. Load `results/meta_analysis/union_fallback.json` from T023c_2.
 2. If intersection is empty, select this union list as the fallback.
 3. **Dependency**: Runs after T024b_1 and T023c_2. *(New Task)*
- [X] T024b_3 [US2] **Rank and Write Gene Panel**.
 1. Load the final gene list (either intersection or fallback union).
 2. Rank genes by descending mean log2FC then ascending meta‑p‑value.
 3. Limit final panel to ≤50 genes.
 4. Output to `results/meta_analysis/gene_panel.json`.
 5. **Dependency**: Runs after T024b_2. *(New Task)*
- [X] T024c [US2] **Finalize Gene Panel**.
 1. Validate `results/meta_analysis/gene_panel.json` against `specs/.../gene_panel.schema.yaml`.
 2. Log summary of panel size and fallback status.
 3. Ensure `results/meta_analysis/bonferroni_correction.json` is updated with the final `m_meta` count.

**Checkpoint**: User Stories 1 and 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Model Training and Validation (Priority: P3)

**Goal**: Build tumor‑type‑specific models using the fixed gene panel, perform nested CV, external validation, and statistical significance testing.

### Tests for User Story 3 (MANDATORY)

- [X] T044a [US3] Unit test for `train_model` edge cases in `tests/unit/test_modeling.py`. *(Logic unchanged)*
- [X] T044b [US3] Unit test for `nested_cv` parameter search and leakage prevention in `tests/unit/test_modeling.py`. *(Logic unchanged)*
- [X] T044c [US3] Unit test for `loo_validation` pre‑check and loop logic in `tests/unit/test_modeling.py`. *(Logic unchanged)*
- [X] T029 [P] [US3] Contract test for model output schema in `tests/contract/test_model_schema.py`
- [X] T030 [P] [US3] Integration test for full modeling and validation pipeline in `tests/integration/test_modeling.py`

### Implementation for User Story 3

- [X] T033 [US3] **LOO Validation Pre‑Check**.
 1. Read `data/processed/` to count available tumor types.
 2. Verify ≥2 tumor types remain if one is left out (FR-008).
 3. If count < 2, raise `ResourceLimitExceeded` or custom `LOOInvalidError` and halt.
 4. Log validation status to `results/validation_status.json`.
- [X] T031a [US3] **Model Initialization**.
 1. Load `results/meta_analysis/gene_panel.json` to extract the fixed gene list.
 2. Initialize `src/model_training.py` with Elastic-Net (Logistic Regression) using `scikit-learn`.
 3. Configure nested CV parameters (inner loop for alpha/lamba, outer loop for evaluation).
- [X] T031b [US3] **Execute Nested Cross‑Validation**.
 1. For each tumor type, split `training_set` (from T020) into outer folds.
 2. Run inner CV to select optimal `alpha` and `lambda`.
 3. Train final model on full `training_set` with selected parameters.
 4. **Dependency**: Runs after T020.
- [X] T031b_1 [US3] **Metric Computation and Persistence**.
 1. Compute ROC-AUC, Precision-Recall, and calibration metrics for the outer folds of T031b.
 2. Save metrics to `results/models/{tumor_type}_cv_metrics.json`.
 3. **Dependency**: Runs after T031b. *(New Task)*
- [X] T031c [US3] **Persist Model**.
 1. Serialize trained models using `joblib` to `results/models/{tumor_type}_model.pkl`.
 2. Include metadata (gene panel, parameters, CV AUC) in the pickle.
- [X] T035a [US3] **Implement LOO Loop Controller**. **Logic**:
 1. **Entity Mapping**: Explicitly implement the `LOO Loop Controller` entity as described in the plan's 'Resolution of Unresolved Concerns'.
 2. **Iteration**: Iterate through each tumor type, excluding it from the training pool.
 3. **State Management**: Maintain a state file `results/loo_state.json` with schema: `{excluded_type: str, training_pool: list[str], status: str}`. Update this file after each iteration.
 4. **Re-training**: Retrain the Elastic-Net model on the remaining tumor types' `training_set`. Re-optimize alpha/lamba on the reduced dataset.
 5. **Dependency**: Runs after T031b and T033.
 **Requirements**: FR-008.
- [X] T036 [US3] **Implement LOO Evaluation and Save**. **Update**: Define 'poor generalizability' based on statistical rigor.
 1. Evaluate LOO retrained models on the held-out tumor type's `discovery_set` (or external GEO if available).
 2. Calculate AUC drop compared to the model trained on all data.
 3. Calculate the 95% CI for the performance drop using **`scipy.stats.ttest_rel`** for paired t-test and **`pingouin`** for non-parametric bootstrap (`n_boot=1000`, `random_state=42`).
 4. If the CI does not include 0 and the drop is significant, flag as "poor generalizability".
 5. **Metric**: Explicitly calculate and store the `performance_drop` value (AUC_train - AUC_LOO) in `results/loo_summary.json` as the primary metric for SC-003.
 6. Log results and update `results/summary.md` draft.
 **Requirements**: FR-008, SC-003.
- [X] T037 [US3] **External GEO Validation**. **Update**: Explicitly require validation on ≥2 *additional* independent GEO cohorts (Constitution Principle VI). **Clarification**: These cohorts can be drawn from the same pool of downloaded GEO datasets (T013a) if they are distinct from those used in T031b, or from external sources. The total count of valid GEO datasets must be ≥2, not necessarily 4. If the minimum 2 datasets are used for training/LOO, log a warning and skip external validation.
 1. Load external GEO datasets from `data/processed/` (post-normalization).
 2. **Leakage Check**: Verify that the dataset IDs in these cohorts are distinct from those used in T013 (Acquisition) and T031b (Training). If overlap is detected, exclude the dataset and log a warning.
 3. Apply the trained models (from T031c) to these datasets.
 4. Compute ROC-AUC, Precision-Recall, and calibration metrics for each cohort.
 5. Save results to `results/validation/external_geo_metrics.json`.
 **Requirements**: FR-002, FR-008.
- [X] T038 [US3] **Compute ROC‑AUC, Precision‑PR, and Calibration Curves**.
 1. Generate calibration curves for all models (LOO and External).
 2. Ensure deciles with <20 samples are flagged as "underpowered" per spec.
 3. Save plots to `results/plots/` and metrics to `results/metrics/`.
- [X] T039b [US3] **Clinical Covariate Extraction**. **Logic**:
 1. Load raw clinical metadata from `data/raw/`.
 2. Extract, clean, and format clinical covariates (age, stage) into a matrix compatible with the baseline model.
 3. **Cleaning Logic**: Impute missing age with median age; impute missing stage with mode. Drop samples with missing response labels.
 4. **Output**: Save to `data/processed/clinical_covariates.csv` with columns: `sample_id`, `age`, `stage`, `response_label`.
 5. **Requirement**: This task ensures FR‑011 can be executed by providing the necessary input data.
 **Dependency**: Runs after T013a.
- [X] T039a [US3] **Baseline Model Training and Persistence**. **Update**: Explicitly state that the baseline model must be trained using ONLY clinical covariates (e.g., age, stage), excluding any gene expression data. **Critical**: Ensure the baseline model is trained and evaluated on the **exact same sample IDs** as the gene-panel model (T031b) to satisfy DeLong's test pairing requirement. **Logic**:
 1. Load only clinical covariates (e.g., age, stage) from `data/processed/clinical_covariates.csv`.
 2. **Sample ID Alignment**: Load the list of sample IDs used in T031b and filter the clinical covariates to match exactly.
 3. Train logistic regression **without** expression features.
 4. Save baseline model to `results/baseline_model.pkl` and metrics to `results/baseline_metrics.json`.
 5. If covariates missing, log warning and set metrics to `null` for that cohort.
 **Requirement**: Explicitly demonstrates FR‑010 usage of clinical‑only baseline.
 **Dependency**: Runs after T039b and T031b.
- [X] T039_1_1 [US3] **Implement DeLong R Script**. **Logic**:
 1. **Create File**: `src/scripts/run_delong.R`.
 2. **Input**: Paired sample data (gene-panel predictions and baseline predictions for the same samples).
 3. **Logic**: Use `pROC::roc.test` to compute DeLong's test p-value.
 4. **Output**: Write `results/deLong_raw.json` with raw p-values.
 5. **Constraint**: This task MUST run after T039a and T031b.
 **Requirements**: FR-011.
- [X] T039_1_2 [US3] **DeLong Orchestrator**. **Logic**:
 1. **Input**: Model predictions from T031b and T039a.
 2. **Logic**: Explicitly match sample IDs between the gene-panel model and baseline model to ensure pairing.
 3. **Action**: Pass the paired data to `run_delong.R` (T039_1_1).
 4. **Dependency**: Runs after T039a and T031b.
 **Requirements**: FR-011.
- [X] T039_2 [US3] **Apply Bonferroni to DeLong Results**.
 1. Read `m_delong` from `results/meta_analysis/bonferroni_correction.json`.
 2. Apply Bonferroni correction to the raw p-values obtained in T039_1_2.
 3. Record adjusted p-value in `results/deLong_results.json`.
 **Dependency**: Runs after T039_1_2. *(New Task)*
- [X] T039_3 [US3] **Record Final DeLong Results**.
 1. Validate `results/deLong_results.json`.
 2. Log summary of statistical significance.
 3. **Dependency**: Runs after T039_2. *(New Task)*
- [X] T040 [US3] **Handle Class Imbalance**.
 1. Implement stratified k-fold CV in all modeling steps.
 2. If responder ratio < 20%, apply cost-sensitive learning (class weights) in `src/model_training.py`.
 3. Report balanced accuracy alongside AUC in all metric files.
- [X] T041a [US3] **Calculate Bonferroni Counts**.
 1. **Pre‑Check**: Verify `results/meta_analysis/gene_panel.json` exists and contains a non‑empty `selected` list. Halt if missing.
 2. **Meta‑Analysis Scope**: Count `m_meta` as the number of genes in the final panel (read from gene_panel.json).
 3. **DeLong Scope**: Count `m_delong` as the number of tumor types that **successfully converged** in T031b_1 and have valid baseline metrics. **Exclude any failed types** from this count.
 4. Write both `m_meta` and `m_delong` to `results/meta_analysis/bonferroni_correction.json`.
 5. **Dependency**: Runs after T031b_1.
- [X] T041b [US3] **Write Bonferroni Correction File**.
 1. Read `m_meta` and `m_delong` from `results/meta_analysis/bonferroni_correction.json`.
 2. Ensure the file is written before T039 executes.
- [X] T041c [US3] **Apply Bonferroni Correction**.
 1. Apply Bonferroni correction to meta‑analysis p‑values (using `m_meta`) and to DeLong test p‑values (using `m_delong`). Adjusted p‑values must be < 0.01.
 2. Record adjusted meta‑p‑values in `results/meta_analysis/gene_panel.json` (add field `adjusted_p`).
 3. **Dependency**: Runs after T041a.
- [X] T042 [US3] **Summary Merge Logic**.
 1. Read existing `results/summary.md` (if any) and merge with new LOO and External validation results.
 2. Ensure all flags (e.g., "intersection_empty", "poor generalizability") are propagated.
 3. Save merged summary to `results/summary.md`.
- [X] T043 [US3] **Final Summary Generation**.
 1. Generate the final `results/summary.md` with all metrics, limitations, and Bonferroni-adjusted significance.
 2. Ensure all success criteria (SC-001 to SC-006) are addressed with measured values.
 3. Validate against `results/summary.schema.yaml` if defined.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T044 [P] Documentation updates in `specs/001-chemo-biomarker-discovery/quickstart.md`
- [X] T045 Code cleanup and refactoring
- [X] T046 Run `quickstart.md` validation to ensure full pipeline execution on CPU‑only runner

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
- Splitting before Differential Expression (T023a)
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
- **FR‑014 Compliance**: **ComBat‑seq** (for discrete count data) is the primary method for batch correction; **fallback to Quantile Matching** if ComBat‑seq fails (only if data types allow); **do NOT use ComBat** (continuous) as the primary method. If both fail, halt or exclude dataset.
- **FR‑008 Compliance**: LOO validation must halt if the dataset drops to a minimal number of types where LOO is invalid. The task logic must explicitly raise an error and exit.
- **FR‑010 Compliance**: Distinct Bonferroni correction logic for meta‑analysis (m = **number of genes in the final panel**) vs DeLong's test (m = **number of successfully converged comparisons**). Ensure both are correctly calculated and applied.
- **FR‑006 Compliance**: The fallback to union of top‑ranked genes must be explicitly triggered only when the intersection is empty, and the reason must be logged in `results/meta_analysis/panel_status.json`.
- **FR‑001/002 Compliance**: Ensure all data downloads are verified against the expected checksums and that missing response labels cause the pipeline to skip the offending dataset instead of halting entirely unless there's insufficient data.
- **TEST_MODE**: Set `TEST_MODE=True` environment variable to allow the pipeline to proceed with fewer than a sufficient number of TCGA types or multiple GEO datasets for Independent Testing purposes.
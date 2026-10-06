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

- [X] T004 [P] [Foundational] Implement `src/config.py`: Define paths, random seeds, FDR thresholds, CPU/memory limits, `MAX_VARIANCE_GENES`, and `GEO_IDS` (default: `['GSE25055', 'GSE42752']`). Added clarification that this config supports FR‑001/FR‑002 checks.
- [X] T006 [P] [Foundational] Implement schema files and checksums. **Logic**:
 1. **Define Content**: Define the following YAML content for the schemas in memory based on Spec Key Entities:
 - `dataset.schema.yaml`: Fields: `sample_id` (string), `tumor_type` (string), `response_label` (string), `expression_vector` (array of floats).
 - `model_output.schema.yaml`: Fields: `cancer_type` (string), `alpha` (float), `lambda` (float), `coefficients` (object), `cross_val_auc` (float).
 - `gene_panel.schema.yaml`: Fields: `gene_symbol` (string), `meta_p_value` (float), `log2FC_mean` (float), `selected` (boolean).
 2. **Write Files**: Save the defined YAML content to `specs/001-chemo-biomarker-discovery/contracts/`.
 3. **Compute Checksums**: Compute SHA256 for each schema file and write to `state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml` `artifact_hashes` map.
 4. **Atomic Step**: Immediately after writing checksums, update the `updated_at` timestamp in `state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml` to the current UTC time.
 **Constraint**: This task runs sequentially (write then checksum then update).
- [X] T006_1 [US1] [Sequential] [Foundational] Implement `aggregate_significance_resolved.schema.yaml`. **Logic**:
 1. **Define Content**: Define a YAML schema for `aggregate_significance_resolved.json` with fields: `gene_symbol` (string), `tumor_type` (string), `p_value` (float), `log2FC_mean` (float), `meta_p_value` (float). **Note**: Includes `log2FC_mean` and `meta_p_value` to satisfy FR-006 and GenePanel entity requirements.
 2. **Write File**: Save to `specs/001-chemo-biomarker-discovery/contracts/`.
 3. **Compute Checksum**: Compute SHA256 and update `state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml`.
 4. **Atomic Step**: Immediately after writing checksums, update the `updated_at` timestamp in `state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml` to the current UTC time.
 **Requirements**: FR-003.
- [X] T007a [US1] [Foundational] Implement `src/main.py`: **Entry Point**. **Logic**:
 1. **Define Entry**: Implement `if __name__ == '__main__':` block that calls `run_pipeline()`.
 2. **Argument Parsing**: Use `argparse` to accept optional `--config` and `--test-mode` flags.
 3. **Error Handling**: Catch any unhandled exceptions and log them to `logs/error.log` before exiting.
 **Requirements**: FR-012.
- [X] T007b [US1] [Foundational] Implement `src/main.py`: **Orchestrator Function**. **Logic**:
 1. **Define Function**: Implement `def run_pipeline(config_path: str, test_mode: bool = False) -> bool:`.
 2. **Logic**: Load config, execute data acquisition, preprocessing, DE, meta-analysis, modeling, and validation in sequence.
 3. **Dependency**: Runs after T005a and T005b.
 **Requirements**: FR-012.
- [X] T008 [US1] [Foundational] Setup `pytest` configuration and contract test harness for YAML schema validation

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
 4. **Output**: Write raw counts and metadata to `data/raw/` and the system logs a warning if total size > 5 GB, but proceeds with execution.
 5. **Constraint**: This task MUST run before T014.
 **Requirements**: FR-001.
- [X] T013a [US1] [P] [Sequential] Implement `src/scripts/run_geo_download.R`: **GEO R Script with Strict Validation and Graceful Degradation**. **Logic**:
 1. **Input**: GEO accession numbers (from config).
 2. **Loop**: Iterate through each GEO ID in the list.
 3. **Fetch & Validate**: Attempt to download expression data and clinical metadata using `GEOquery`.
 4. **Skip Logic**: If a dataset fails to download or lacks valid response annotations:
 - Log a warning: `"Skipping GEO ID {id}: {reason}"`.
 - Do NOT halt execution.
 - Add to a `failed_datasets` list.
 5. **Aggregate**: After processing ALL requested IDs, check the count of `valid_datasets`.
 6. **Final Halt**: If `len(valid_datasets) < 2`, log a CRITICAL error and exit with code 1. Otherwise, proceed.
 7. **Output**: Write raw data to `data/raw/` for valid datasets.
 8. **Dependency**: Runs after T012a (for parallel download capability) but logic ensures all IDs are processed before the final check.
 **Requirements**: FR-002.
- [X] T014_1 [US1] [P] **Data Feasibility Gate**: Create `src/data_acquisition.py` skeleton.
 **Logic**: Create the file `src/data_acquisition.py` with an empty `check_feasibility_gate` function stub.
 **Requirements**: FR-001, FR-002.
- [X] T014_2 [US1] [P] **Data Feasibility Gate**: Implement `check_feasibility_gate()` function.
 **Logic**: Implement `def check_feasibility_gate() -> bool:` in `src/data_acquisition.py`. **Pre-Check**: Verify existence of output files from T012a and T013a. Load results from T012a and T013a. Verify ≥3 TCGA types and ≥2 GEO datasets. Return `True` if valid, `False` otherwise.
 **Dependency**: Runs after T012a and T013a.
 **Requirements**: FR-001, FR-002.
- [X] T014_3 [US1] [P] **Data Feasibility Gate**: Implement logging and halting logic.
 **Logic**: Integrate `check_feasibility_gate()` into the main pipeline. If `False`, log a critical error and exit with code 1. If `True`, proceed.
 **Dependency**: Runs after T014_2.
 **Requirements**: FR-001, FR-002.
- [X] T011 [US1] Integration test for Feasibility Gate logic in `tests/integration/test_feasibility_gate.py`. **Update**: This test MUST include a case where the gate fails (insufficient data) to verify the logging and halting mechanism works correctly. *(Logic unchanged)*
- [X] T017b [US1] [P] [Foundational] Implement `src/scripts/run_preprocessing.R`: **Apply DESeq2 VST, Transpose, Two-Pass Split, and Stream**. **Update**: This task now consolidates all heavy data processing within the R container. **Logic**:
 1. **Input**: Raw count matrices from T012a/T013a.
 2. **Platform-Specific Preprocessing**:
 - **CRITICAL**: If input is microarray (GEO), apply RMA normalization or equivalent platform-specific preprocessing BEFORE VST.
 - If input is RNA-seq (TCGA), proceed directly to VST.
 3. **VST**: Apply DESeq2 variance-stabilizing transformation.
 4. **Transpose**: Explicitly transpose the matrix so that **Rows = Genes** and **Columns = Samples** using `t()` or `data.table::transpose()`.
 5. **Two-Pass Split**:
 - **Pass 1**: Stream the data in chunks using `data.table::fread(..., chunkSize=...)`. For each chunk, count the number of responders and non-responders. Accumulate global counts.
 - **Pass 2**: Stream again. For each sample, assign to `discovery_set` or `training_set` based on the stratified split ratio (majority/minority) using the accumulated counts to ensure exact stratification without loading the full matrix into RAM. Verify that the training set contains at least 50 responders and 50 non-responders. If not, log a warning but proceed.
 6. **Write**: Write `{tumor_type}_discovery_vst.csv`, `{tumor_type}_training_vst.csv`, `{tumor_type}_discovery_metadata.csv`, and `{tumor_type}_training_metadata.csv` incrementally. **These exact filenames are mandatory for downstream tasks.**
 7. **Output**: Write the split files in wide format to `data/processed/`. **Crucially, the `discovery_set` output is specifically designated for Differential Expression analysis (T023a) to prevent data leakage.**
 8. **Constraint**: This task MUST run after T012a/T013a and before T023a. **All heavy data processing occurs within the R container** to satisfy the Plan's Dockerized R Environment mandate.
 **Requirements**: FR-003, FR-004, FR-012, FR-013.
- [X] T017a [US1] [P] [Foundational] Implement `src/scripts/run_preprocessing.R`: **Filter low‑expression genes (CPM < 1 in > 80% samples)**. **Update**: Explicitly state that missing data in GEO datasets will be handled via complete case analysis (row removal), with no imputation. *(Logic unchanged - moved to R)*
 **Requirements**: FR-004.
- [X] T017c [US1] [P] [Foundational] Implement `src/scripts/run_preprocessing.R`: **Harmonize Gene Identifiers** (Ensembl/Entrez → HGNC). *(Logic unchanged - moved to R)*
 **Requirements**: FR-003.
- [X] T017d [US1] [P] [Foundational] Implement `src/scripts/run_preprocessing.R`: **Normalization Failure Handling**.
 1. After attempting VST on each dataset, if a dataset cannot be re‑normalized (e.g., incompatible format), log a warning `"Normalization failed for {dataset_id}: {reason}"` and update `data/normalization_status.json` with status `"failed"` for that dataset.
 2. If *all* datasets fail, raise a `RuntimeError` and halt execution with exit code 1.
 3. Successful normalizations are recorded with status `"success"` in the same JSON file.
 4. This satisfies US‑1 Edge Case 3 (datasets that cannot be re‑normalized are excluded with a logged warning) and ensures a clear halt when no data remain.
 **Requirements**: FR-004.
- [X] T016 [US1] [P] [Foundational] **Batch Correction**: Implement `src/scripts/run_preprocessing.R` to align platforms (FR‑014). **Update**: ComBat-seq is the ONLY primary method for **within-platform** normalization of TCGA RNA-seq count data. **Quantile Matching** (or ComBat on VST data) is the primary method for **cross-platform alignment** between TCGA (RNA-seq) and GEO (Microarray) data.
 **Logic**:
 1. **Within-Platform**: Apply ComBat-seq to TCGA count data to normalize within the TCGA cohort.
 2. **Cross-Platform**: Apply Quantile Matching (or ComBat on VST-transformed data) to align the GEO microarray data distribution with the TCGA RNA-seq distribution.
 3. **Fallback**: If ComBat-seq fails on discrete data, use Quantile Matching. If Quantile Matching fails, exclude the dataset with a warning.
 4. **Halt Condition**: If both methods fail for a dataset, exclude the dataset. If the number of valid datasets drops below the required minimum (FR-002), halt execution.
 **Requirements**: FR-014.

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Cross-Cancer Biomarker Identification (Priority: P2)

**Goal**: Perform differential expression analysis on the full discovery set, identify cross‑tumor biomarkers using Stouffer's method, and generate a fixed gene panel.

**Independent Test**: Verify the selection logic (intersection/union) can be executed on a small sample of discovery sets.

### Tests for User Story 2 (OPTIONAL)

- [X] T021 [P] [US2] Unit test for Stouffer's meta‑analysis calculation in `tests/unit/test_meta_analysis.py`
- [X] T022 [P] [US2] Integration test for LOO‑Blind DE and panel selection logic on 3 tumor types (simulated) in `tests/integration/test_biomarker_discovery.py`

### Implementation for User Story 2

- [X] T023a [US2] **Implement R Script for DE Analysis**. **Logic**:
 1. **Create File**: `src/scripts/run_deseq2.R`.
 2. **Input**: Wide format CSV (Rows=Genes, Cols=Samples).
 3. **DESeq2 Logic**: Load counts, construct DESeqDataSet, run `DESeq()`, extract results with `lfcThreshold = 1.0` and `altHypothesis = "greaterAbs"`. **Pin a recent stable release of DESeq via renv lockfile in Docker context.**
 4. **Output**: Write `{tumor_type}_de_results.csv` with columns: `gene_symbol`, `log2FoldChange`, `pvalue`, `padj`.
 5. **Constraint**: This task MUST run before T023a. **Must complete before T023a executes.**
 **Requirements**: FR-005.
- [X] T023b [US2] **Aggregate DE Results**.
 1. Load DE results from all tumor types in `results/de/`.
 2. Aggregate significant genes (FDR < 0.05, |log2FC| > 1.0) across types.
 3. Output a unified list of significant genes per tumor type to `results/de/aggregate_significance.json`.
 4. **Output Schema**: The file MUST contain a dictionary: `{gene_symbol: {tumor_type: p_value}}` to support Stouffer's method. *(Logic updated)*
- [X] T023b_1 [US2] **Resolve Naming Conflicts, Format, and Validate**.
 1. Load `results/de/aggregate_significance.json` from T023b.
 2. **HGNC Validation**: Use `biopython` or a local HGNC mapping file to validate gene symbols. Invalid symbols are dropped.
 3. **Action**: Log dropped symbols.
 4. Structure the data into a dictionary: `{gene_symbol: {tumor_type: p_value}}`.
 5. Output the resolved and structured data to `results/de/aggregate_significance_resolved.json`.
 6. **Validation**: Validate `results/de/aggregate_significance_resolved.json` against `aggregate_significance_resolved.schema.yaml`.
 7. **Dependency**: Runs after T023b.
 **Requirements**: FR-003.
- [X] T024b_1 [US2] **Compute Intersection, Fallback, and Rank Panel**. **Logic**:
 1. **Input**: `results/de/aggregate_significance_resolved.json`.
 2. **Compute Intersection**: Identify genes significant across >=2 tumor types.
 3. **Fallback**: If the intersection is empty, compute the union of top-ranked genes (<=50).
 4. **Rank**: Rank genes based on descending mean log2FC and ascending meta-p-value.
 5. **Output**: Write the final gene panel to `results/meta_analysis/gene_panel.json`.
 **Requirements**: FR-006.

- [X] T024c [US2] **Validate Gene Panel**.
 1. **Validate**: Validate `results/meta_analysis/gene_panel.json` against `specs/.../gene_panel.schema.yaml`.
 2. **Log**: Log summary of panel size and fallback status.
 3. **Dependency**: Runs after T024b_1.
 **Requirements**: FR-006.
- [X] T024d [US2] **Calculate Bonferroni Counts**.
 1. **Pre‑Check**: Verify `results/meta_analysis/gene_panel.json` exists and contains a non‑empty `selected` list.
 2. **Meta‑Analysis Scope**: Calculate `m_meta` as the number of genes in the final panel.
 3. **Output**: Write `m_meta` to `results/meta_analysis/bonferroni_correction.json`.
 4. **Dependency**: Runs after T024c.
 **Requirements**: FR-010.

**Checkpoint**: User Stories 1 and 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Model Training and Validation (Priority: P3)

**Goal**: Build tumor‑type‑specific models using the fixed gene panel, perform nested CV, external validation, and statistical significance testing.

### Tests for User Story 3 (MANDATORY)

- [X] T044a [US3] Unit test for `train_model` edge cases in `tests/unit/test_modeling.py`. *(Logic unchanged)*
- [X] T044b [US3] Unit test for nested CV parameter search and leakage prevention in `tests/unit/test_modeling.py`. *(Logic unchanged)*
- [X] T044c [US3] Unit test for `loo_validation` pre‑check and loop logic in `tests/unit/test_modeling.py`. *(Logic unchanged)*
- [X] T029 [P] [US3] Contract test for model output schema in `tests/contract/test_model_schema.py`
- [X] T030 [P] [US3] Integration test for full modeling and validation pipeline in `tests/integration/test_modeling.py`

### Implementation for User Story 3

- [X] T033_1 [US3] **Implement LOO Loop Controller**. **Logic**:
 1. **Entity Mapping**: Explicitly implement the `LOO Loop Controller` entity as described in the plan's 'Resolution of Unresolved Concerns'.
 2. **Iteration**: Iterate through each tumor type, excluding it from the training pool.
 3. **State Management**: Maintain a state file `results/loo_state.json` with schema: `{excluded_type: str, training_pool: list[str], status: str}`. Update this file after each iteration.
 4. **Re-training**: Retrain the Elastic-Net model on the remaining tumor types' `training_set`. Re-optimize alpha/lamba on the reduced dataset.
 5. **Dependency**: Runs after T031b and T033_3.
 **Requirements**: FR-008.
- [X] T035a [US3] **Implement LOO Loop Controller**. **Logic**:
 1. **Entity Mapping**: Explicitly implement the `LOO Loop Controller` entity as described in the plan's 'Resolution of Unresolved Concerns'.
 2. **Iteration**: Iterate through each tumor type, excluding it from the training pool.
 3. **State Management**: Maintain a state file `results/loo_state.json` with schema: `{excluded_type: str, training_pool: list[str], status: str}`. Update this file after each iteration.
 4. **Re-training**: Retrain the Elastic-Net model on the remaining tumor types' `training_set`. Re-optimize alpha/lamba on the reduced dataset.
 5. **Dependency**: Runs after T031b and T033_3.
 **Requirements**: FR-008.
- [X] T036 [US3] **External Validation Evaluation**. **Update**: Define 'poor generalizability' based on statistical rigor.
 1. Evaluate the model trained on the internal training set (T031b) on the *external* GEO validation cohorts (T037).
 2. Calculate AUC drop compared to the model trained on all data (internal training set).
 3. **Metric**: Explicitly calculate and store the `performance_drop` value (AUC_internal - AUC_external) in `results/loo_summary.json` as the primary metric for SC-003.
 4. Calculate the 95% CI for the performance drop using **`scipy.stats.ttest_rel`** for paired t-test and **`pingouin`** for non-parametric bootstrap (`n_boot=1000`, `random_state=42`).
 5. If the CI does not include the null value and the drop is significant, flag as "poor generalizability".
 6. Log results and update `results/summary.md` draft.
 7. **Output Artifact**: Save `results/loo_summary.json` (JSON object) with keys: `performance_drop` (float), `ci_95` (list of 2 floats), and `status` (string).
 **Requirements**: FR-008, SC-003.
- [X] T037 [US3] **External GEO Validation**. **Update**: External validation uses **≥2 distinct independent GEO cohorts** drawn from the datasets acquired in T013a. If the initial 2 datasets are used for discovery/training, these cohorts must be **held-out subsets** of the same datasets or distinct datasets if the initial download included more than 2. **Constraint**: Do NOT require "additional" datasets beyond the ≥2 mandated by FR-002. If the initial 2 are used for training/LOO, the system MUST halt with Exit Code 2 and generate a `results/validation/validation_skipped.json` artifact explaining the insufficiency.
 1. Load external GEO datasets from `data/processed/`.
 2. **Leakage Check**: Verify that the dataset IDs in these cohorts are distinct from those used in T013 (Acquisition) and T031b (Training). If overlap is detected, exclude the dataset and log a warning.
 3. Apply the trained models (from T031c) to these datasets.
 4. Compute ROC-AUC, Precision-Recall, and calibration metrics for each cohort.
 5. **SC-001 Verification**: Explicitly compare the computed ROC-AUC against the target threshold of **≥0.75**. Generate a `pass/fail` status for each cohort and record it in `results/validation/external_geo_metrics.json`.
 6. **Halt Condition**: If insufficient cohorts are available for external validation (i.e., <2 valid external cohorts remain after splitting), generate `results/validation/validation_skipped.json` with a detailed explanation and **halt execution with Exit Code 2**. **Do NOT skip validation or proceed with warnings only.**
 **Requirements**: FR-002, FR-008, SC-001.
- [X] T038 [US3] **Compute ROC‑AUC, Precision‑PR, and Calibration Curves**.
 1. Generate calibration curves for all models (LOO and External).
 2. Ensure deciles with <20 samples are flagged as "underpowered" per spec.
 3. Save plots to `results/plots/` and metrics to `results/metrics/`.
- [X] T039a [US3] **Baseline Model Training**.
 1. Load `results/meta_analysis/gene_panel.json` to extract the fixed gene list.
 2. Initialize `src/model_training.py` with Elastic-Net (Logistic Regression) using `scikit-learn`.
 3. Configure nested CV parameters (inner loop for alpha/lamba, outer loop for evaluation).
- [X] T039b [US3] **Execute Nested Cross‑Validation**.
 1. For each tumor type, split `training_set` (from T017b) into outer folds.
 2. Run inner CV to select optimal `alpha` and `lambda`.
 3. Train final model on full `training_set` with selected parameters.
 4. **Dependency**: Runs after T017b.
- [X] T039_1_1 [US3] **DeLong Test R Script**.
 1. **Create File**: `src/scripts/run_delong.R`.
 2. **Dependency**: **MUST** ensure `pROC` package is installed in the Dockerfile and `renv` lockfile. **Explicitly install `pROC` before running.**
 3. **Input**: Paired sample data (gene-panel predictions and baseline predictions for the same samples).
 4. **Logic**: Use `pROC::roc.test` to compute DeLong's test p-value.
 5. **Output**: Write `results/deLong_raw.json` with raw p-values.
 6. **Constraint**: This task MUST run after T039a and T039b. **Must complete after T039a and T039b.**
 **Requirements**: FR-011.
- [X] T039_1_2 [US3] **DeLong Orchestrator**.
 1. **Input**: Model predictions from T031b and T039a.
 2. **Logic**: Explicitly match sample IDs between the gene-panel model and baseline model to ensure pairing.
 3. **Action**: Pass the paired data to `run_delong.R` (T039_1_1).
 4. **Dependency**: Runs after T039a and T039b.
 **Requirements**: FR-011.
- [X] T039_2 [US3] **Apply Bonferroni Correction**.
 1. **Read**: Read `m_meta` and `m_delong` from `results/meta_analysis/bonferroni_correction.json`.
 2. **Apply**: Apply Bonferroni correction to the Stouffer meta-analysis p-values (from `results/meta_analysis/stouffer_meta.csv`) using `m_meta`. Calculate adjusted p-values as `p_adjusted = p_raw * m_meta`.
 3. **Apply**: Apply Bonferroni correction to the DeLong test p-values (from `results/deLong_raw.json`) using `m_delong`. Calculate adjusted p-values as `p_adjusted = p_raw * m_delong`.
 4. **Output**: Record the adjusted meta‑p‑values in `results/meta_analysis/gene_panel.json` (add field `adjusted_p`) and the adjusted DeLong results in `results/deLong_results.json`.
 5. **Dependency**: Runs after T039_1_2.
 **Requirements**: FR-010.
- [X] T040 [US3] **Handle Class Imbalance**.
 1. In `src/model_training.py`, explicitly calculate the responder ratio for each tumor type.
 2. If the ratio is < 20%, automatically enable `class_weight='balanced'` in the Logistic Regression model.
 3. Log the class weights used and the resulting balanced accuracy in `results/models/{tumor_type}_cv_metrics.json`.
 **Requirements**: US-3 Edge Case 4.
- [X] T041a [US3] **Calculate Bonferroni Counts**.
 1. **Pre‑Check**: Verify `results/meta_analysis/gene_panel.json` exists and contains a non‑empty `selected` list.
 2. **Meta‑Analysis Scope**: Calculate `m_meta` as the number of genes in the final panel.
 3. **DeLong Scope**: Calculate `m_delong` as the total number of planned tumor-type comparisons.
 4. **Output**: Write `m_meta` and `m_delong` to `results/meta_analysis/bonferroni_correction.json`.
 5. **Dependency**: Runs after T024c and T031b.
 **Requirements**: FR-010.
- [X] T041b [US3] **Write Bonferroni Correction File**.
 1. Read `m_meta` and `m_delong` from `results/meta_analysis/bonferroni_correction.json`.
 2. Write the values to the file.
- [X] T041c [US3] **Apply Bonferroni Correction**.
 1. Apply Bonferroni correction to the Stouffer meta-analysis p-values and DeLong test p-values.
 2. Verify that the adjusted p-values meet the significance threshold.
 3. Output the adjusted p-values to the appropriate files.
 4. **Dependency**: Runs after T041a.
 **Requirements**: FR-010.
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

## Phase 7: Final Verification & Reporting

**Purpose**: Ensure all analysis findings are fully resolved and the pipeline is ready for final execution.

- [X] T052 [P] **Verify Streaming Implementation**. **Logic**:
 1. Execute a dry-run of `src/scripts/run_preprocessing.R` on a large simulated dataset to verify that memory usage stays below 7 GB.
 2. Confirm that `data.table::fread` chunking is active and statistics are accumulated correctly.
 3. Log memory usage profile to `results/memory_profile.json`.
 **Requirements**: FR-012, SC-005.
- [X] T053 [P] **Verify Strict Data Loading Failures**. **Logic**:
 1. Attempt to download a non-existent GEO dataset ID.
 2. Confirm that the pipeline raises a `RuntimeError` and exits with code 1.
 3. Verify that no synthetic data is generated or used.
 **Requirements**: Data Hygiene Rule.
- [X] T047 [P] **Implement Streaming Data Loader for Large Datasets (R-Native)**. **Logic**:
 1. Modify `src/scripts/run_preprocessing.R` and `src/scripts/run_tcga_download.R` to use `data.table::fread(..., chunkSize=...)` and `BiocParallel` for chunked processing of TCGA/GEO sources when file size estimates exceed 2GB.
 2. Implement chunked processing to compute VST and filtering without loading the full matrix into RAM.
 3. Ensure the streaming iterator accumulates statistics online (mean, variance) for normalization.
 4. **Constraint**: Must handle the real data stream using R-native methods (TCGAbiolinks/GEOquery); no synthetic fallbacks.
 **Requirements**: FR-012, SC-005.
- [X] T048 [P] **Enforce Strict Data Loading Failures**. **Logic**:
 1. Remove any `try/except` blocks in `src/scripts/run_tcga_download.R` or `run_geo_download.R` that fall back to `generate_synthetic_*()` or `mock_*()`.
 2. Ensure that if a real download fails, the script raises a `RuntimeError` with a clear message and exits.
 3. Add a pre-flight check that verifies the existence of the target URL/package before attempting download.
 **Requirements**: Data Hygiene Rule.
- [X] T049 [P] **Validate Meta-Analysis Statistical Power**. **Logic**:
 1. In `src/meta_analysis.py`, compute the effective sample size for the meta-analysis.
 2. If the combined sample size for any gene across tumor types is < 50, **FLAG** the gene as "underpowered" in `results/meta_analysis/panel_status.json`.
 3. **DO NOT EXCLUDE** underpowered genes from the final panel unless explicitly overridden by a configuration flag. The Intersection/Union fallback logic (FR-006) MUST proceed regardless of this flag.
 **Requirements**: SC-006, FR-006.
- [X] T050 [P] **Implement Robust Class Imbalance Handling**. **Logic**:
 1. In `src/model_training.py`, explicitly calculate the responder ratio for each tumor type.
 2. If the ratio is < 20%, apply cost-sensitive learning (class weights) in `src/model_training.py`.
 3. Log the class weights used and the resulting balanced accuracy in `results/models/{tumor_type}_cv_metrics.json`.
 **Requirements**: US-3 Edge Case 4.
- [X] T051 [P] **Add DeLong Power Analysis**. **Logic**:
 1. In `src/validation.py`, before running DeLong's test, check if the number of samples in the held-out set is sufficient for the test (n > 20).
 2. If n < 20, **DO NOT SKIP** the test logic. Instead, run the test but **FLAG** the result as "underpowered" with a status of "underpowered" and a warning.
 3. Record the result in `results/deLong_results.json`.
 4. **Dependency**: Runs after T039a and T031b.
 **Requirements**: FR-011.

---
description: "Task list template for feature implementation"
---

# Tasks: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

**Input**: Design documents from `/specs/001-circadian-metabolic-correlation/`
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
 - Feature requirements from plan.md (functional requirements, success criteria)
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

- [X] T001a Create directory structure: `projects/PROJ-110-investigating-the-correlation-between-ci/`, `code/`, `data/`, `tests/`, `docs/`
- [X] T001b Create initial empty files: `code/__init__.py`, `tests/__init__.py`, `README.md`, `.gitignore`
- [X] T002 Initialize Python project with dependencies (`pandas`, `numpy`, `scipy`, `scikit-learn`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`) in `requirements.txt`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data directory structure (`data/raw`, `data/processed`) and `contracts/` schema definitions
- [X] T005 [P] Implement base logging infrastructure in `code/utils/logging.py` with file and console handlers
- [X] T006 Create base configuration manager in `code/utils/config.py` to load environment variables and project paths
- [X] T007 Implement data hash utility in `code/utils/hashing.py` for `state/projects/PROJ-110-...yaml` updates
- [X] T008 Setup pytest configuration in `pytest.ini` and create `tests/conftest.py` for fixtures
- [ ] T012 [P] [Foundational] Define the core circadian gene list constant in `code/data/config.py`.
  - **Content**: List of core clock genes with specific isoforms: `PER1`, `PER2`, `PER3`, `CRY1`, `CRY2`, `BMAL1` (ARNTL), `CLOCK`, `NR1D1`, `RORA` (mapped from spec's `RORα`).
  - **Output**: A constant `CORE_CIRCADIAN_GENES` accessible to the loader.
  - **Depends on**: T006 (Config Manager).

- [ ] T053 [P] [Foundational] Add a reproducibility utility `code/utils/random_seed.py` that sets a global NumPy, Python, and scikit‑learn seed from a config entry (`random_seed: 42`). All downstream scripts must import this module first to guarantee deterministic results.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 0: Data Ingestion & Verification

**Purpose**: Download, verify, and filter data. This phase MUST complete before any analysis or classification.

**⚠️ CRITICAL**: T009a (Schema Inspection) MUST precede T010 (Download). T010 MUST precede T011 (Verify Columns) and T013b (Filter Genes).

- [ ] T009a [US1] Implement `inspect_gtex_schema` in `code/data/downloader.py` to verify variable presence BEFORE downloading.
  - **Logic**: Use `datasets.load_dataset(..., streaming=True)` to peek at the schema of the GTEx v8 dataset (without downloading the full file).
  - **Verification**: Check for the presence of required columns: `bmi`, `fasting_glucose`, `triglycerides`, `hdl`, `systolic_bp`, `diastolic_bp`, `pmi`, `time_of_death`.
  - **Output**: Write `data/processed/schema_inspection.json` with `status="verified"` or `status="missing_columns"` and a list of missing columns.
  - **Constraint**: If any required column is missing, the task MUST log a CRITICAL error and **halt execution** (do not proceed to download). This enforces the "Data Availability Strategy".
  - **Depends on**: T004 (Data Directory Setup), T006 (Config).

- [ ] T010 [US1] Implement `download_gtex_data` in `code/data/downloader.py` to download GTEx v8 RNA‑seq TPM matrix and Phenotype file.
  - **Source**: Read the dataset ID and file paths from `code/config.yaml` (key: `datasets.gtex.source`). Do NOT hardcode the URL.
  - **Verification**: Verify the source against the "Verified Datasets" block in `research.md` (or `config.yaml` if verified there). If the source is not verified, raise an error.
  - **Output**: Write `data/raw/gtex_v8_tpm_matrix.csv` and `data/raw/gtex_v8_phenotype.csv`.
  - **Verification**: Check file existence and row count > 0. Raise error if files are missing or empty.
  - **Constraint**: Do not use synthetic data. If download fails, raise an exception.
  - **Depends on**: T009a (Schema Inspection passed), T004 (Data Directory Setup), T006 (Config).

- [ ] T011 [US1] Implement column verification gate in `code/data/downloader.py` to check for BMI, Glucose, BP, TG, HDL.
  - **Logic**: If any required column is missing (should not happen if T009a passed, but as a safety check):
    1. Log a CRITICAL error.
    2. **DO NOT** attempt to fetch TCGA data as a fallback (per FR‑001).
    3. Write `data/processed/data_availability_gate.json` with `status="Exploratory - Missing Columns"` and list missing columns.
    4. **HALT** execution.
  - If all columns present: Proceed.
  - **Depends on**: T010 (Data Loading).

- [ ] T013 [US1] Implement `filter_core_genes` in `code/data/downloader.py` using the constant from T012.
  - **Logic**: Filter the loaded expression matrix to retain ONLY the core circadian genes.
  - **Output**: Write filtered matrix to `data/processed/core_genes_matrix.csv`.
  - **Depends on**: T010 (Data Loading), T012 (Gene List).

- [ ] T051 [US1] Implement `log_transform_expression` in `code/data/preprocess.py` to add a pseudocount of 1 to TPM values and compute `log2(TPM + 1)`.  
  - **Input**: `data/processed/core_genes_matrix.csv` (output of T013).  
  - **Output**: `data/processed/core_genes_log2_matrix.csv`.  
  - **Rationale**: Guarantees no NaN values for zero‑count genes (FR‑007 edge‑case).  
  - **Depends on**: T013.

- [ ] T014 [US1] Implement `classify_metabolic_status` in `code/data/classifier.py` applying strict ATP‑III thresholds (≥3 of 5).  
  - **Logic**: Classify donors as "MetS" or "Control" based on BMI, Glucose, BP, TG, HDL. Exclude samples with missing/invalid data. Log exclusions.  
  - **Output**:  
    1. Write `data/processed/baseline_labels.csv` (sample_id, label, criteria_count).  
    2. **CRITICAL**: Write `data/processed/filtered_phenotype.csv` containing ONLY the samples that passed the missing‑data exclusion. This file is required for T042 (Sensitivity Analysis) to ensure the "same cohort" assumption.  
  - **Depends on**: T010 (Data Loading), T011 (Column Verification). **DO NOT depend on T013**.

- [ ] T015 [US1] Implement `run_power_analysis` in `code/data/classifier.py` to calculate N and statistical power.  
  - **Logic**:  
    1. Count complete cases (N) after applying strict listwise exclusion for missing values in the 5 clinical variables (output of T014).  
    2. Perform formal power analysis based on **expected effect size (Cohen's d = 0.5)**, **alpha = 0.05**, and observed N.  
    3. **Constraint**: If Power < 0.8 (N < 100):  
       - **DO NOT** attempt to fetch TCGA data (per FR‑001).  
       - Write `data/processed/feasibility_report.json` with `status="Exploratory - Low Power"`, `power=<value>`, `N=<count>`.  
       - **DO NOT HALT**: Continue execution in "Exploratory Mode" as per FR‑001.  
    4. If Power ≥ 0.8: Write `data/processed/feasibility_report.json` with `status="Feasible"`.  
  - **Depends on**: T014 (Classification output required for N count), T010, T011. **DO NOT depend on T013**.

**Checkpoint**: Data ingestion complete - classification and power analysis ready

---

## Phase 3: User Story 1 - Define Metabolic Syndrome Status from Clinical Variables (Priority: P1) 🎯 MVP

**Goal**: Classify GTEx donors as "MetS" or "Control" based on ATP‑III criteria and handle missing data.

**Independent Test**: Can be fully tested by running the classification script on a known subset of GTEx data and verifying that the output matches manual calculation of ATP‑III criteria for those specific samples.

### Tests for User Story 1 (Mandatory) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T009 [P] [US1] Add `tests/unit/test_classifier.py::test_atp_iii_classifies_metabolic_syndrome` to verify multiple criteria = MetS.
  - **Fixture**: Use a synthetic fixture with hardcoded values (e.g., BMI=32, Glu=110, TG=160) to verify deterministic classification.
- [ ] T016 [P] [US1] Add `tests/unit/test_classifier.py::test_excludes_missing_data` to verify samples with null/NaN values are excluded and logged.
- [ ] T017 [P] [US1] Add `tests/unit/test_classifier.py::test_boundary_conditions` to verify strict thresholds (e.g., BMI=29.9 vs 30.0).

### Implementation for User Story 1

- [ ] T018 [US1] Implement `calculate_classification_proportion` in `code/data/classifier.py` to compute SC‑001.  
  - **Logic**: Calculate (Number of Classified Donors) / (Total Donors with Data).  
  - **Output**: Write `data/processed/classification_proportion.json` with `proportion=<value>`, `total_donors=<N>`, `classified_donors=<M>`.  
  - **Depends on**: T014.

- [ ] T019 [US1] Implement missing data handling in `code/data/classifier.py` to exclude samples with null/NaN/invalid values and log exclusions.  
  - **Note**: This is part of T014 logic but isolated here for testing clarity.

- [ ] T020 [US1] Implement `store_baseline_labels` in `code/data/classifier.py` to write baseline classifications to `data/processed/baseline_labels.csv`.  
  - **Output**: CSV file with `sample_id`, `label`, `criteria_count`.  
  - **Depends on**: T014.

- [ ] T042 [US1] Implement `run_sensitivity_analysis` in `code/main.py` to vary ATP‑III thresholds by ±5 % (SC‑005).  
  - **Logic**:  
    1. Read `data/processed/filtered_phenotype.csv` (from T014) to ensure the **exact same cohort** is used as the baseline.  
    2. Re‑classify samples with varied thresholds. **Definition**: Apply a **relative change** of ±5 % to each threshold value (e.g., BMI ≥ 30 * 1.05 = 31.5, or 30 * 0.95 = 28.5).  
    3. Compare baseline vs. varied labels.  
    4. **Calculate** the percentage of re‑classified samples.  
    5. **Calculate** the robustness metrics: "Classification Agreement Rate" (percentage of samples with same label) and "Delta in Prevalence" (difference in MetS rate).  
    6. Write comparison results to `data/processed/sensitivity_analysis.csv` (columns: sample_id, baseline_label, varied_label, reclassified).  
    7. Write robustness metrics to `data/processed/sensitivity_metric.json` to satisfy SC‑005.  
  - **Depends on**: T014 (for `filtered_phenotype.csv`), T010, T011. **DO NOT depend on T020**.

- [ ] T054 [US1] Add a unit test `tests/unit/test_sensitivity.py::test_agreement_rate` that verifies the agreement‑rate calculation on a small synthetic cohort.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Perform Differential Expression Analysis on Core Circadian Genes (Priority: P2)

**Goal**: Compare expression levels of core circadian genes between MetS and Control groups using non‑parametric tests and FDR correction.

**Independent Test**: Can be fully tested by executing the statistical analysis pipeline on the pre‑processed data and verifying that the output includes a table of p‑values, adjusted p‑values (FDR), and effect sizes for each gene.

### Tests for User Story 2 (Mandatory) ⚠️

- [ ] T021 [P] [US2] Add `tests/unit/test_differential.py::test_wilcoxon_rank_sum` to verify test execution on synthetic data.
- [ ] T022 [P] [US2] Add `tests/unit/test_differential.py::test_benjamini_hochberg_fdr` to verify FDR correction logic.
- [ ] T023 [P] [US2] Add `tests/unit/test_differential.py::test_tissue_stratification_low_power` to verify exclusion of tissues with <20 samples/group.

### Implementation for User Story 2

- [ ] T024 [US2] Implement `stratify_by_tissue` in `code/analysis/differential.py` to group samples by tissue type.
- [ ] T024b [US2] Implement `filter_underpowered_tissues` in `code/analysis/differential.py` to exclude tissues with <20 samples per group.  
  - **Logic**:  
    1. Count samples per tissue per group (MetS vs Control) from the output of T014.  
    2. Identify tissues where count < 20 for either group.  
    3. Log a WARNING to stderr for each excluded tissue.  
    4. Return a filtered list of valid tissues.  
  - **Output**: Write `data/processed/excluded_tissues.json` with list of excluded tissues and reasons.  
  - **Constraint**: This task MUST run BEFORE T025. T025 MUST only receive the filtered list of valid tissues.  
  - **Depends on**: T014 (Classification), T024 (Stratification).

- [ ] T025 [US2] Implement `run_wilcoxon_tests` in `code/analysis/differential.py` to perform Wilcoxon rank‑sum tests for each gene per tissue.  
  - **Input**: Filtered list of valid tissues from T024b.  
  - **Constraint**: Do NOT run tests on tissues excluded by T024b.  
  - **Depends on**: T024b.

- [ ] T026 [US2] Implement `apply_fdr_correction` in `code/analysis/differential.py` using Benjamini‑Hochberg procedure on **DE p‑values only**.  
  - **Input**: Raw p‑values from T029 (Differential Expression).  
  - **Output**: Adjusted p‑values (FDR) for DE tests.  
  - **Constraint**: This task handles ONLY Differential Expression FDR. Correlation FDR is handled by T050.  
  - **Depends on**: T029.

- [ ] T027 [US2] Implement `compute_effect_sizes` in `code/analysis/differential.py` to calculate Cohen’s d (or an equivalent) for each gene‑tissue comparison.

- [ ] T055 [US2] Add a unit test `tests/unit/test_effect_size.py::test_cohens_d_calculation` to guarantee correct effect‑size computation.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: Sensitivity Analysis & Correlation (Priority: P2/P3)

**Purpose**: Perform correlation analysis (FR‑007) and Sensitivity Analysis (Phase 5) before final reporting.

- [ ] T028 [US2] Implement normality check (Shapiro‑Wilk) in `code/analysis/correlation.py` to select correlation method.  
  - **Logic**:  
    1. Perform Shapiro‑Wilk test on the distribution of the variables (gene expression and continuous trait) for each gene‑trait pair.  
    2. If p > 0.05, use Pearson; otherwise, use Spearman.  
    3. Log the chosen method for each gene‑trait pair.  
  - **Output**: Write `data/processed/correlation_method_flags.json` with `{ "gene_trait_pair": "method" }`.  
  - **Depends on**: T014, T013. **DO NOT depend on T026**.

- [ ] T029 [US2] Implement `generate_correlation_analysis` in `code/analysis/correlation.py` to compute Spearman/Pearson correlations with continuous traits (FR‑007).  
  - **Logic**: Compute correlations for ALL core circadian genes against continuous traits (BMI, Glucose, TG, HDL, BP) using the method determined by T028.  
  - **Output**: Return a DataFrame with columns `[gene, trait, r, p_raw]`. **Do NOT include significance flags here**; those are added after FDR correction.  
  - **Depends on**: T014, T013, T028.

- [ ] T050 [US2] Implement `apply_correlation_fdr` in `code/analysis/correlation.py` to apply independent Benjamini‑Hochberg FDR to correlation p‑values.  
  - **Input**: Raw p‑values from T029 (Correlation).  
  - **Output**: Adjusted p‑values (FDR) for correlation tests.  
  - **Constraint**: This task MUST apply FDR **independently** from the DE FDR (T026).  
  - **Depends on**: T029.

- [ ] T030 [US2] Implement `plot_scatter_significant` in `code/viz/plots.py` to generate scatter plots for significant correlations (FR‑007).  
  - **Output**: Write `docs/correlation_scatter_*.png` for each significant gene‑trait pair.  
  - **Depends on**: T029, T028, T050.

- [ ] T056 [US2] Add a unit test `tests/unit/test_correlation_method.py::test_method_selection` that checks Pearson is chosen only when Shapiro‑Wilk p > 0.05 on synthetic normal data.

**Checkpoint**: Correlation analysis complete

---

## Phase 6: User Story 3 - Build Predictive Logistic Regression Model with Covariates (Priority: P3)

**Goal**: Fit a multivariate logistic regression model predicting MetS status using gene expression and covariates, evaluated via cross‑validation.

**Independent Test**: Can be fully tested by training the model on a training split, evaluating on a validation split, and verifying that the Area Under the Curve (AUC) and confidence intervals are calculated and reported.

### Tests for User Story 3 (Mandatory) ⚠️

- [ ] T031 [P] [US3] Add `tests/unit/test_modeling.py::test_logistic_regression_training_auc` to verify model training and AUC calculation.
- [ ] T032 [P] [US3] Add `tests/unit/test_modeling.py::test_cross_validation_loop` to verify k‑fold cross‑validation.
- [ ] T033 [P] [US3] Add `tests/unit/test_modeling.py::test_odds_ratio_extraction_collinearity` to verify OR extraction and VIF check.

### Implementation for User Story 3

- [ ] T034 [US3] Implement `prepare_model_features` in `code/analysis/modeling.py` to encode categorical variables (Tissue, Sex) and scale features.
- [ ] T035 [US3] Implement `train_logistic_regression` in `code/analysis/modeling.py` fitting `MetS ~ Gene_Expression + Age + Sex + Tissue + PMI + Time_of_Death`.  
  - **Constraint**: MUST include `PMI` and `Time_of_Death` as covariates as per FR‑005.  
  - **Output**: Trained model object.  
  - **Depends on**: T014, T034.

- [ ] T052 [US3] Implement robust handling of missing `time_of_death` in `code/analysis/modeling.py`.  
  - **Logic**: If `time_of_death` is missing for a sample, exclude that sample from the logistic regression (log a WARNING). No imputation is performed to avoid introducing bias.  
  - **Depends on**: T014.

- [ ] T036 [US3] Implement `run_cross_validation` in `code/analysis/modeling.py` performing k‑fold CV and calculating mean AUC with 95 % confidence intervals.
- [ ] T037 [US3] Implement `extract_odds_ratios` in `code/analysis/modeling.py` to compute OR, SE, and p‑values for predictors (Gene Expression + Covariates).  
  - **Output**: Write `data/processed/odds_ratios_main.csv` with ORs for genes and covariates.  
  - **Depends on**: T035.

- [ ] T047 [US3] Implement `extract_trait_odds_ratios` in `code/analysis/modeling.py` to run separate models for individual metabolic traits.  
  - **Logic**:  
    1. For each metabolic trait (BMI, Glucose, TG, HDL, BP), fit a separate logistic regression model: `MetS ~ Gene_Expression + Age + Sex + Tissue + PMI + Time_of_Death + Trait`.  
    2. Extract the Odds Ratio for the specific trait variable.  
    3. Write results to `data/processed/odds_ratios_traits.csv`.  
  - **Constraint**: This task specifically addresses FR‑009 to distinguish prediction targets.  
  - **Depends on**: T014, T034.

- [ ] T038 [US3] Implement `check_collinearity` in `code/analysis/modeling.py` to calculate VIF and flag issues if VIF > 5 (FR‑005).  
  - **Output**: Write `data/processed/collinearity_report.json` with VIF values and flags.  
  - **Depends on**: T035.

- [ ] T039 [US3] Implement `plot_roc_curve` in `code/viz/plots.py` to visualize model performance (FR‑008).  
  - **Output**: Write `docs/roc_curve.png`.  
  - **Depends on**: T036.

- [ ] T040 [US3] Implement `generate_heatmap` in `code/viz/plots.py` to visualize gene expression patterns across MetS/Control groups (FR‑008).  
  - **Output**: Write `docs/heatmap.png`.  
  - **Depends on**: T025, T026.

- [ ] T057 [US3] Add a unit test `tests/unit/test_vif.py::test_vif_threshold` that verifies the VIF calculation flags a predictor when VIF > 5 on a synthetic collinear dataset.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Reporting & Versioning (Polish)

**Purpose**: Finalize results, generate reports, and update state hashes.

- [ ] T041 [P] Implement `write_results_to_csv` in `code/main.py` to save processed data and results to `data/processed/`.
- [ ] T043 [P] Implement `compute_content_hashes` in `code/main.py` to hash `data/processed/` artifacts.
- [ ] T044 [P] Implement `update_state_hash` in `code/main.py` to write hashes to `state/projects/PROJ-110-...yaml`.
- [ ] T045 [P] Generate final diagnostic report in `docs/report.md` summarizing SC‑001 through SC‑005 outcomes.  
  - **Requirement**: Must explicitly include the "Classification Agreement Rate" metric from T042 as the primary evidence for SC‑005.  
  - **Depends on**: T042, T018, T026, T036, T047.
- [ ] T058 [P] Extend `docs/report.md` to include a table of significant DE genes (FDR < 0.05) to satisfy SC‑002, and a table of significant correlations (FDR < 0.05) to satisfy SC‑004.
- [ ] T059 [P] Add a summary section in `docs/report.md` reporting the average AUC and its 95 % CI (SC‑003) together with a baseline random‑classifier reference (AUC = 0.5).
- [ ] T046 [P] Run end‑to‑end integration test in `tests/integration/test_pipeline.py` to verify full pipeline execution on sample data.
- [ ] T060 [P] Add a CI step in the GitHub Actions workflow to assert that no GPU devices are requested (`torch.cuda.is_available()` must be `False`) to guarantee CPU‑only execution.

**Checkpoint**: All polishing tasks complete; the project is ready for final review and execution.

---

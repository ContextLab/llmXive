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
- [X] T003 Configure linting (flake8/black) and formatting tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data directory structure (`data/raw`, `data/processed`) and `contracts/` schema definitions
- [X] T005 Implement base logging infrastructure in `code/utils/logging.py` with file and console handlers
- [X] T006 Create base configuration manager in `code/utils/config.py` to load environment variables and project paths
- [X] T007 Implement data hash utility in `code/utils/hashing.py` for `state/projects/PROJ-110-...yaml` updates
- [X] T008 Setup pytest configuration in `pytest.ini` and create `tests/conftest.py` for fixtures
- [X] T012 Define the core circadian gene list constant in `code/data/config.py`.
   - **Content**: List of core clock genes with specific isoforms: `PER1`, `PER2`, `PER3`, `CRY1`, `CRY2`, `BMAL1` (ARNTL), `CLOCK`, `NR1D1`, `RORA`.
   - **Output**: A constant `CORE_CIRCADIAN_GENES` accessible to the loader.
   - **Depends on**: T006 (Config Manager). *(Removed `[P]` tag to reflect dependency)*
- [X] T053 Add a reproducibility utility `code/utils/random_seed.py` that sets a global NumPy, Python, and scikit‑learn seed from a config entry (`random_seed: 42`). All downstream scripts must import this module first to guarantee deterministic results.
- [X] T063 Create `contracts/dataset.schema.yaml` defining the expected columns and types for the GTEx input dataset.
- [X] T064 Create `contracts/classification.schema.yaml` defining the structure of the classification CSV (`sample_id`, `label`, `criteria_count`).
- [X] T065 Create `contracts/model.schema.yaml` defining logistic regression model outputs (coefficients, odds ratios, confidence intervals, AUC).
- [X] T066 Create `contracts/output.schema.yaml` defining the final aggregated results schema (summary tables, figures, metrics).
- [X] T067 Author `quickstart.md` with step‑by‑step usage instructions for the pipeline.
- [X] T070 Document the **Donor** entity (attributes, relationships) in `data-model.md`.
- [X] T071 Document the **GeneExpression** entity in `data-model.md`.
- [X] T072 Document the **MetabolicStatus** entity in `data-model.md`.
- [X] T068 Compute SHA‑256 checksums for all raw GTEx files (`data/raw/gtex_v8_tpm_matrix.csv`, `data/raw/gtex_v8_phenotype.csv`) and write `data/raw/checksums.json`.
- [X] T069 Record the raw data checksums in the project state YAML (`state/projects/PROJ-110-...yaml` under `artifact_hashes`).

---

## Phase 0: Data Ingestion & Verification

**Purpose**: Download, verify, and filter data. This phase MUST complete before any analysis or classification.

**⚠️ CRITICAL**: T009a (Schema Inspection) MUST precede T010 (Download). T010 MUST precede T011 (Verify Columns) and T013b (Filter Genes).

- [X] T009a Implement `inspect_gtex_schema` in `code/data/downloader.py` to verify variable presence BEFORE downloading.
 - **Logic**: Use `datasets.load_dataset(..., streaming=True)` to peek at the schema of the GTEx v8 dataset (without downloading the full file).
 - **Verification**: Check for the presence of required columns: `bmi`, `fasting_glucose`, `triglycerides`, `hdl`, `systolic_bp`, `diastolic_bp`, `pmi`, `time_of_death`.
 - **Output**: Write `data/processed/schema_inspection.json` with `status="verified"` or `status="missing_columns"` and a list of missing columns.
 - **Constraint**: If any required column is missing, the task MUST log a CRITICAL error and **halt execution** (do not proceed to download). This enforces the "Data Availability Strategy".
 - **Depends on**: T004 (Data Directory Setup), T006 (Config).

- [X] T010 Implement `download_gtex_data` in `code/data/downloader.py` to download GTEx v8 RNA‑seq TPM matrix and Phenotype file.
 - **Source**: Read the dataset ID and file paths from `code/config.yaml` (key: `datasets.gtex.source`). Do NOT hardcode the URL.
 - **Verification**: Verify the source against the "Verified Datasets" block in `research.md` (or `config.yaml` if verified there). If the source is not verified, raise an error.
 - **Output**: Write `data/raw/gtex_v8_tpm_matrix.csv` and `data/raw/gtex_v8_phenotype.csv`.
 - **Verification**: Check file existence and row count > 0. Raise error if files are missing or empty.
 - **Constraint**: Do not use synthetic data. If download fails, raise an exception.
 - **Depends on**: T009a (Schema Inspection passed), T004 (Data Directory Setup), T006 (Config).

- [X] T011 Implement column verification gate in `code/data/downloader.py` to check for BMI, Glucose, BP, TG, HDL.
 - **Logic**:
 1. If any required column is missing (should not happen if T009a passed, but as a safety check):
 - Log a CRITICAL warning.
 - **DO NOT** halt execution.
 - Write `data/processed/data_availability_gate.json` with `status="Exploratory - Missing Columns"` and list missing columns.
 - Proceed to the next step, but the analysis will be limited to available columns (if any).
 2. If all columns present: Proceed.
 - **Constraint**: This task MUST NOT halt the pipeline if columns are missing; it must log and proceed, allowing the downstream classification (T014) to handle missing data per-sample.
 - **Depends on**: T010 (Data Loading).

- [X] T013 Implement `filter_core_genes` in `code/data/downloader.py` using the constant from T012.
 - **Logic**: Filter the loaded expression matrix to retain ONLY the core circadian genes.
 - **Output**: Write filtered matrix to `data/processed/core_genes_matrix.csv`.
 - **Depends on**: T010 (Data Loading), T012 (Gene List).

- [X] T051 Implement `log_transform_expression` in `code/data/preprocess.py` to add a pseudocount of 1 to TPM values and compute `log2(TPM + 1)`.
 - **Input**: `data/processed/core_genes_matrix.csv` (output of T013).
 - **Output**: `data/processed/core_genes_log2_matrix.csv`.
 - **Rationale**: Guarantees no NaN values for zero‑count genes (FR‑007 edge‑case).
 - **Depends on**: T013.

**Checkpoint**: Data ingestion complete - ready for classification

---

## Phase 3: User Story 1 - Define Metabolic Syndrome Status from Clinical Variables (Priority: P1) 🎯 MVP

**Goal**: Classify GTEx donors as "MetS" or "Control" based on ATP‑III criteria and handle missing data.

**Independent Test**: Can be fully tested by running the classification script on a known subset of GTEx data and verifying that the output matches manual calculation of ATP‑III criteria for those specific samples.

### Implementation for User Story 1

- [X] T014 Implement `classify_metabolic_status` in `code/data/classifier.py` applying strict ATP‑III thresholds (≥3 of 5).
 - **Logic**: Classify donors as "MetS" or "Control" based on BMI, Glucose, BP, TG, HDL. Exclude samples with missing/invalid data. Log exclusions.
 - **Output**:
   1. Write `data/processed/baseline_labels.csv` (columns: `sample_id`, `label`, `criteria_count`).
   2. Write `data/processed/filtered_phenotype.csv` containing ONLY the samples that passed the missing‑data exclusion (required for downstream sensitivity analysis).
 - **Depends on**: T010 (Data Loading), T011 (Column Verification). **DO NOT depend on T013**.

- [X] T015 Implement `run_power_analysis` in `code/data/classifier.py`.
 - **Logic**:
   1. Count complete cases (N) after listwise exclusion for the five clinical variables (output of T014).
   2. Use `statsmodels.stats.power.TTestIndPower` with effect size = 0.5, alpha = 0.05 to compute achieved power.
   3. If Power < 0.8 (N < 100), write `study_status=exploratory` to `code/config.yaml` and log: `"Insufficient GTEx sample size (N < 100) for robust power; study limited to exploratory analysis"`.
   4. Write `data/processed/feasibility_report.json` with fields `status`, `power`, `N`.
 - **Depends on**: T014, T010, T011.
 - **Test**: T080 verifies correct power calculation and status flagging.

- [X] T018 Implement `calculate_classification_proportion` in `code/data/classifier.py` to compute SC‑001.
 - **Logic**: Calculate (Number of Classified Donors) / (Total Donors with Data).
 - **Output**: Write `data/processed/classification_proportion.json` with `proportion`, `total_donors`, `classified_donors`.
 - **Depends on**: T014.

- [X] T042 Implement `run_sensitivity_analysis` in `code/main.py` to vary ATP‑III thresholds by ±5 %.
 - **Logic**:
   1. Read `data/processed/filtered_phenotype.csv` to ensure the exact same cohort.
   2. Apply ±5 % relative change to each ATP‑III threshold and re‑classify.
   3. Compute agreement rate = proportion of samples retaining the original label.
   4. **Enforce** agreement rate ≥ 0.90; if not, raise a `RuntimeError` and halt the pipeline (fulfills SC‑005).
   5. Write `data/processed/sensitivity_analysis.csv` (sample_id, baseline_label, varied_label, reclassified).
   6. Write `data/processed/sensitivity_metric.json` with `agreement_rate`, `delta_prevalence`.
 - **Depends on**: T014, T010, T011.
 - **Test**: T082 checks that the ≥ 90 % threshold is enforced.

- [X] T054 Add a unit test `tests/unit/test_sensitivity.py::test_agreement_rate` that verifies the agreement‑rate calculation on a small synthetic cohort.

- [X] T009 Add `tests/unit/test_classifier.py::test_atp_iii_classifies_metabolic_syndrome` to verify multiple criteria = MetS.
 - **Fixture**: Use a synthetic fixture with hardcoded values (e.g., BMI=32, Glu=110, TG=160) to verify deterministic classification.

- [X] T016 Add `tests/unit/test_classifier.py::test_excludes_missing_data` to verify samples with null/NaN values are excluded and logged.

- [X] T017 Add `tests/unit/test_classifier.py::test_boundary_conditions` to verify strict thresholds (e.g., BMI=29.9 vs 30.0).

- [X] T073 Add `tests/unit/test_write_outputs.py::test_baseline_labels_schema` to verify `baseline_labels.csv` has correct columns and that files from T041 exist.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Perform Differential Expression Analysis on Core Circadian Genes (Priority: P2)

**Goal**: Compare expression levels of core circadian genes between MetS and Control groups using non‑parametric tests and FDR correction.

**Independent Test**: Can be fully tested by executing the statistical analysis pipeline on the pre‑processed data and verifying that the output includes a table of p-values, adjusted p-values (FDR), and effect sizes for each gene.

### Tests for User Story 2 (Mandatory) ⚠️

- [X] T021 Add `tests/unit/test_differential.py::test_wilcoxon_rank_sum` to verify test execution on synthetic data.
- [X] T022 Add `tests/unit/test_differential.py::test_benjamini_hochberg_fdr` to verify FDR correction logic.
- [X] T023 Add `tests/unit/test_differential.py::test_tissue_stratification_low_power` to verify exclusion of tissues with <20 samples/group.

### Implementation for User Story 2

- [X] T024 Implement `stratify_by_tissue` in `code/analysis/differential.py` to group samples by tissue type.
- [X] T024b Implement `filter_underpowered_tissues` in `code/analysis/differential.py` to exclude tissues with <20 samples per group.
 - **Logic**:
   1. Count samples per tissue per group (MetS vs Control) from the output of T014.
   2. Identify tissues where count < 20 for either group.
   3. Log a WARNING to stderr for each excluded tissue.
   4. Return a filtered list of valid tissues.
 - **Output**: Write `data/processed/excluded_tissues.json` with list of excluded tissues and reasons.
 - **Constraint**: This task MUST run BEFORE T025. T025 MUST only receive the filtered list of valid tissues.
 - **Depends on**: T014 (Classification), T024 (Stratification).

- [X] T025 Implement `run_wilcoxon_tests` in `code/analysis/differential.py` to perform Wilcoxon rank‑sum tests for each gene per tissue.
 - **Input**: Filtered list of valid tissues from T024b.
 - **Constraint**: Do NOT run tests on tissues excluded by T024b.
 - **Depends on**: T024b.

- [X] T027 Implement `compute_effect_sizes` in `code/analysis/differential.py` to calculate Cohen’s d (or an equivalent) for each gene‑tissue comparison.

- [X] T055 Add a unit test `tests/unit/test_effect_size.py::test_cohens_d_calculation` to guarantee correct effect‑size computation.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: Sensitivity Analysis & Correlation (Priority: P2/P3)

**Purpose**: Perform correlation analysis (FR‑007), apply FDR corrections, and generate visualizations for US2.

- [X] T028 Implement normality check (Shapiro‑Wilk) in `code/analysis/correlation.py` to select correlation method.
 - **Logic**:
   1. Perform Shapiro‑Wilk test on the distribution of the variables (gene expression and continuous trait) for each gene‑trait pair.
   2. If p > 0.05, use Pearson; otherwise, use Spearman.
   3. Log the chosen method for each gene‑trait pair.
 - **Output**: Write `data/processed/correlation_method_flags.json` with `{ "gene_trait_pair": "method" }`.
 - **Depends on**: T014, T013. **Do NOT depend on T026**.

- [X] T029 Implement `generate_correlation_analysis` in `code/analysis/correlation.py` to compute Spearman/Pearson correlations with continuous traits (FR‑007).
 - **Logic**: Compute correlations for ALL core circadian genes against continuous traits (BMI, Glucose, TG, HDL, BP) using the method determined by T028.
 - **Output**: Return a DataFrame with columns `[gene, trait, r, p_raw]`. **Do NOT include significance flags here**; those are added after FDR correction.
 - **Depends on**: T014, T013, T028.

- [X] T050 Implement `apply_correlation_fdr` in `code/analysis/correlation.py` to apply independent Benjamini‑Hochberg FDR to correlation p-values.
 - **Input**: Raw p-values from T029 (Correlation).
 - **Constraint**: **MUST aggregate all p-values across ALL gene‑trait pairs into a single list before applying correction.** This ensures the "independent" global correction required by FR‑007.
 - **Output**: Adjusted p-values (FDR) for correlation tests.
 - **Depends on**: T029.

- [X] T026 Implement `apply_fdr_correction` in `code/analysis/differential.py` using Benjamini‑Hochberg procedure on **DE p-values only**.
 - **Input**: Raw p-values from T025 (Wilcoxon).
 - **Constraint**: **MUST collect all p-values from ALL tissues into a single list before applying correction.** This ensures "global" FDR as required by FR‑004.
 - **Output**: Adjusted p-values (FDR) for DE tests.
 - **Depends on**: T025.

- [X] T030 Implement `plot_scatter_significant` in `code/viz/plots.py` to generate scatter plots for significant correlations (FR‑007).
 - **Output**: Write `docs/correlation_scatter_*.png` for each significant gene‑trait pair.
 - **Depends on**: T029, T028, T050.

- [X] T040 Implement `generate_heatmap` in `code/viz/plots.py` to visualize gene expression patterns across MetS/Control groups (FR‑008).
 - **Output**: Write `docs/heatmap.png`.
 - **Depends on**: T025, T026.

- [X] T056 Add a unit test `tests/unit/test_correlation_method.py::test_method_selection` that checks Pearson is chosen only when Shapiro‑Wilk p > 0.05 on synthetic normal data.

**Checkpoint**: Correlation analysis and DE FDR complete

---

## Phase 6: User Story 3 - Build Predictive Logistic Regression Model with Covariates (Priority: P3)

**Goal**: Fit a multivariate logistic regression model predicting MetS status using gene expression and covariates, evaluated via cross-validation.

**Independent Test**: Can be fully tested by training the model on a training split, evaluating on a validation split, and verifying that the Area Under the Curve (AUC) and confidence intervals are calculated and reported.

### Tests for User Story 3 (Mandatory) ⚠️

- [X] T031 Add `tests/unit/test_modeling.py::test_logistic_regression_training_auc` to verify model training and AUC calculation.
- [X] T032 Add `tests/unit/test_modeling.py::test_cross_validation_loop` to verify k‑fold cross‑validation.
- [X] T033 Add `tests/unit/test_modeling.py::test_odds_ratio_extraction_collinearity` to verify OR extraction and VIF check.

### Implementation for User Story 3

- [X] T034 Implement `prepare_model_features` in `code/analysis/modeling.py` to encode categorical variables (Tissue, Sex) and scale features.
- [X] T035 Implement `train_logistic_regression` in `code/analysis/modeling.py` fitting `MetS ~ Gene_Expression + Age + Sex + Tissue + PMI + Time_of_Death`.
 - **Constraint**: MUST include `PMI` and `Time_of_Death` as covariates as per FR‑005.
 - **Output**: Trained model object.
 - **Depends on**: T014, T034.

- [X] T052 Implement robust handling of missing `time_of_death` in `code/analysis/modeling.py`.
 - **Logic**: If `time_of_death` is missing for a sample:
   1. **Use `PMI` (Post-Mortem Interval) as a proxy** for the missing `time_of_death` value.
   2. Log a WARNING indicating the substitution was made.
   3. Do NOT exclude the sample unless `PMI` is also missing.
 - **Depends on**: T014.

- [X] T061 Implement `train_severity_score_model` in `code/analysis/modeling.py` to fit a model where the outcome is the **continuous severity score** (sum of 5 ATP‑III criteria).
 - **Logic**: Fit `Severity_Score ~ Gene_Expression + Age + Sex + Tissue + PMI + Time_of_Death`.
 - **Output**: Trained model object and results (coefficients, p-values) for the severity score outcome.
 - **Rationale**: Satisfies FR-005 requirement for an alternative outcome variable (continuous severity score).
 - **Depends on**: T014, T034.

- [X] T036 Implement `run_cross_validation` in `code/analysis/modeling.py` performing k‑fold CV and calculating mean AUC with 95 % confidence intervals.
- [X] T037 Implement `extract_odds_ratios` in `code/analysis/modeling.py` to compute OR, SE, and p‑values for predictors (Gene Expression + Covariates).
 - **Output**: Write `data/processed/odds_ratios_main.csv` with ORs for genes and covariates.
 - **Depends on**: T035.

- [X] T047 Implement `extract_trait_odds_ratios` in `code/analysis/modeling.py` to run separate models for individual metabolic traits.
 - **Logic**:
   1. For each metabolic trait (BMI, Glucose, TG, HDL, BP), fit a separate logistic regression model: `MetS ~ Gene_Expression + Age + Sex + Tissue + PMI + Time_of_Death + Trait`.
   2. Extract the Odds Ratio for the specific trait variable.
   3. Write results to `data/processed/odds_ratios_traits.csv`.
 - **Constraint**: This task specifically addresses FR‑009 to distinguish prediction targets.
 - **Depends on**: T014, T034.

- [X] T038 Implement `check_collinearity` in `code/analysis/modeling.py` to calculate VIF and flag issues if VIF > 5 (FR‑005).
 - **Output**: Write `data/processed/collinearity_report.json` with VIF values and flags.
 - **Depends on**: T035.
 - **Test**: T081 validates that predictors with VIF > 5 are correctly flagged.

- [X] T039 Implement `plot_roc_curve` in `code/viz/plots.py` to visualize model performance (FR‑008).
 - **Output**: Write `docs/roc_curve.png`.
 - **Depends on**: T036.

- [X] T057 Add a unit test `tests/unit/test_vif.py::test_vif_threshold` that verifies the VIF calculation flags a predictor when VIF > 5 on a synthetic collinear dataset.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Reporting & Versioning (Polish)

**Purpose**: Finalize results, generate reports, and update state hashes.

- [X] T041 Implement `write_processed_outputs` in `code/main.py` to save:
   - `baseline_labels.csv` (columns: `sample_id`, `label`, `criteria_count`)
   - `classification_proportion.json`
   - `feasibility_report.json`
   - `sensitivity_metric.json`
   - `odds_ratios_main.csv`
   - `odds_ratios_traits.csv`
   - `collinearity_report.json`
   - `hashes.json` (generated by T043b)
   - All files are written to `data/processed/`.
 - **Verification**: Unit test T073 (added earlier) asserts file existence and schema compliance.

- [X] T043a Compute SHA‑256 hashes for every file in `data/processed/` and write `data/processed/hashes.json`.
- [X] T043b Write the hash manifest (`hashes.json`) to disk.
- [X] T044a Load the project state YAML (`state/projects/PROJ-110-...yaml`).
- [X] T044b Update the `artifact_hashes` map with the new hashes from `hashes.json`.
- [X] T044c Write the updated YAML back to disk.
- [X] T045a Generate SC‑001 paragraph (classification proportion) and write to `docs/report.md`.
- [X] T045b Generate SC‑002 table of significant DE genes (FDR < 0.05) and append to `docs/report.md`.
- [X] T045c Generate SC‑003 summary (average AUC with 95 % CI) and append to `docs/report.md`.
- [X] T045d Generate SC‑004 table of significant correlations (FDR < 0.05) and append to `docs/report.md`.
- [X] T045e Generate SC‑005 metric paragraph (Classification Agreement Rate) and append to `docs/report.md`.
- [X] T076 Add a unit test `tests/unit/test_report_sections.py::test_all_sc_sections_present` to verify that each SC paragraph/table exists in `docs/report.md`.

- [X] T058a Generate markdown table of DE genes with columns `gene`, `tissue`, `log2FC`, `p_raw`, `p_adj`, `significant` and insert into `docs/report.md`.
- [X] T058b Generate markdown table of significant gene‑trait correlations with columns `gene`, `trait`, `r`, `p_raw`, `p_adj`, `significant` and insert into `docs/report.md`.
- [X] T077 Add a unit test `tests/unit/test_report_tables.py::test_de_and_corr_tables_format` to verify table structure.

- [X] T059a Compute average AUC and 95 % confidence interval from cross‑validation results and write to `data/processed/auc_summary.json`.
- [X] T059b Insert the AUC summary paragraph (including baseline AUC = 0.5 reference) into `docs/report.md`.
- [X] T078 Add a unit test `tests/unit/test_auc_section.py::test_auc_paragraph_exists` to confirm the AUC section is present.

- [X] T060a Edit `.github/workflows/ci.yml` to add a step that runs a Python script checking `torch.cuda.is_available()`. The step must fail the job if a GPU is detected.
- [X] T060b Add unit test `tests/unit/test_cpu_only.py::test_no_cuda` that asserts `torch.cuda.is_available()` is False.
- [X] T079 Ensure the CI workflow includes the new step and that the test suite fails if a GPU is inadvertently used.

- [X] T041 (already covered) – see Phase 7.
- [X] T043 (already covered) – see Phase 7.
- [X] T044 (already covered) – see Phase 7.
- [X] T045 (already covered) – see Phase 7.
- [X] T058 (already covered) – see Phase 7.
- [X] T059 (already covered) – see Phase 7.

- [X] T046 Run end‑to‑end integration test in `tests/integration/test_pipeline.py` to verify full pipeline execution on sample data.

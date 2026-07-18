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

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 0: Data Ingestion & Verification

**Purpose**: Download, verify, and filter data. This phase MUST complete before any analysis or classification.

**⚠️ CRITICAL**: T010 (Load GTEx) MUST precede T011 (Verify Columns) and T013b (Filter Genes).

- [ ] T010 [US1] Implement `download_gtex_data` in `code/data/downloader.py` to download GTEx v8 RNA-seq TPM matrix and Phenotype file.
  - **Source**: Download from HuggingFace dataset `genetics/gtex_v8` (specific files: `RNA-seq TPM matrix` and `Phenotype data`).
  - **Output**: Write `data/raw/gtex_v8_tpm_matrix.csv` and `data/raw/gtex_v8_phenotype.csv`.
  - **Verification**: Check file existence and row count > 0. Raise error if files are missing or empty.
  - **Constraint**: Do not use synthetic data. If download fails, raise an exception.
  - **Depends on**: T004 (Data Directory Setup).

- [ ] T011 [US1] Implement column verification gate in `code/data/downloader.py` to check for BMI, Glucose, BP, TG, HDL.
  - **Logic**: If any required column is missing:
    1. Log a warning.
    2. Attempt to fetch TCGA phenotype data as a fallback source from HuggingFace dataset `biostars/tcga_mets_phenotype_v1`.
    3. If TCGA fallback fails, write `data/processed/data_availability_gate.json` with `status="Exploratory - Insufficient Phenotype Data"`.
    4. **Continue execution** with available data (do not exit/halt).
  - If all columns present: Proceed.
  - **Depends on**: T010 (Data Loading).

- [ ] T012 [US1] Define the core circadian gene list constant in `code/data/config.py`.
  - **Content**: List of core clock genes with specific isoforms: `PER1`, `PER2`, `PER3`, `CRY1`, `CRY2`, `BMAL1` (ARNTL), `CLOCK`, `NR1D1`, `RORA`.
  - **Output**: A constant `CORE_CIRCADIAN_GENES` accessible to the loader.
  - **Depends on**: T010 (Data Loading).

- [ ] T013 [US1] Implement `filter_core_genes` in `code/data/downloader.py` using the constant from T012.
  - **Logic**: Filter the loaded expression matrix to retain ONLY the core circadian genes.
  - **Output**: Write filtered matrix to `data/processed/core_genes_matrix.csv`.
  - **Depends on**: T010 (Data Loading), T012 (Gene List).

- [ ] T014 [US1] Implement `classify_metabolic_status` in `code/data/classifier.py` applying strict ATP-III thresholds (≥3 of 5).
  - **Logic**: Classify donors as "MetS" or "Control" based on BMI, Glucose, BP, TG, HDL. Exclude samples with missing/invalid data. Log exclusions.
  - **Output**: Write `data/processed/baseline_labels.csv`.
  - **Depends on**: T011 (Column Verification), T013 (Gene Filtering).

- [ ] T015 [US1] Implement `run_power_analysis` in `code/data/classifier.py` to calculate N and statistical power.
  - **Logic**:
    1. Count complete cases (N) after applying strict listwise exclusion for missing values in the 5 clinical variables (output of T014).
    2. Perform formal power analysis based on **expected effect size (Cohen's d = 0.5)**, **alpha = 0.05**, and observed N.
    3. **Constraint**: If Power < 0.8 (N < 100):
      - **Attempt to fetch TCGA data** from HuggingFace dataset `biostars/tcga_mets_phenotype_v1` to supplement the cohort (per FR-001).
      - If TCGA data is successfully fetched and combined, recalculate power.
      - If TCGA is unavailable or combined N is still < 100:
        - Write `data/processed/feasibility_report.json` with `status="Exploratory - Low Power"`, `power=<value>`, `N=<count>`.
        - **DO NOT HALT**: Continue execution in "Exploratory Mode" as per FR-001.
    4. If Power >= 0.8:
      - Write `data/processed/feasibility_report.json` with `status="Feasible"`.
      - Proceed to downstream analysis.
  - **Depends on**: T014 (Classification output required for N count), T010, T011, T013.

**Checkpoint**: Data ingestion complete - classification and power analysis ready

---

## Phase 3: User Story 1 - Define Metabolic Syndrome Status from Clinical Variables (Priority: P1) 🎯 MVP

**Goal**: Classify GTEx donors as "MetS" or "Control" based on ATP-III criteria and handle missing data.

**Independent Test**: Can be fully tested by running the classification script on a known subset of GTEx data and verifying that the output matches manual calculation of ATP-III criteria for those specific samples.

### Tests for User Story 1 (Mandatory) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T009 [P] [US1] Add `tests/unit/test_classifier.py::test_atp_iii_classifies_metabolic_syndrome` to verify multiple criteria = MetS.
  - **Fixture**: Use a synthetic fixture with hardcoded values (e.g., BMI=32, Glu=110, TG=160) to verify deterministic classification.
- [ ] T016 [P] [US1] Add `tests/unit/test_classifier.py::test_excludes_missing_data` to verify samples with null/NaN values are excluded and logged.
- [ ] T017 [P] [US1] Add `tests/unit/test_classifier.py::test_boundary_conditions` to verify strict thresholds (e.g., BMI=29.9 vs 30.0).

### Implementation for User Story 1

- [ ] T018 [US1] Implement `calculate_classification_proportion` in `code/data/classifier.py` to compute SC-001.
  - **Logic**: Calculate (Number of Classified Donors) / (Total Donors with Data).
  - **Output**: Write `data/processed/classification_proportion.json` with `proportion=<value>`, `total_donors=<N>`, `classified_donors=<M>`.
  - **Depends on**: T014.

- [ ] T019 [US1] Implement missing data handling in `code/data/classifier.py` to exclude samples with null/NaN/invalid values and log exclusions.
  - **Note**: This is part of T014 logic but isolated here for testing clarity.

- [ ] T020 [US1] Implement `store_baseline_labels` in `code/data/classifier.py` to write baseline classifications to `data/processed/baseline_labels.csv`.
  - **Output**: CSV file with `sample_id`, `label`, `criteria_count`.
  - **Depends on**: T014.

- [ ] T042 [US1] Implement `run_sensitivity_analysis` in `code/main.py` to vary ATP-III thresholds by ±5% (SC-005).
  - **Logic**:
    1. Read `data/processed/baseline_labels.csv` (from T020).
    2. Re-classify samples with varied thresholds (e.g., BMI >= 30 * 1.05 = 31.5, or 30 * 0.95 = 28.5). **Definition**: relative change.
    3. Compare baseline vs. varied labels.
    4. **Calculate** the percentage of reclassified samples.
    5. **Calculate** the robustness metrics: "Classification Agreement Rate" (percentage of samples with same label) and "Delta in Prevalence" (difference in MetS rate).
    6. Write comparison results to `data/processed/sensitivity_analysis.csv` (columns: sample_id, baseline_label, varied_label, reclassified).
    7. Write robustness metrics to `data/processed/sensitivity_metric.json` to satisfy SC-005.
  - **Depends on**: T014, T020.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Perform Differential Expression Analysis on Core Circadian Genes (Priority: P2)

**Goal**: Compare expression levels of core circadian genes between MetS and Control groups using non-parametric tests and FDR correction.

**Independent Test**: Can be fully tested by executing the statistical analysis pipeline on the pre-processed data and verifying that the output includes a table of p-values, adjusted p-values (FDR), and effect sizes for each gene.

### Tests for User Story 2 (Mandatory) ⚠️

- [ ] T021 [P] [US2] Add `tests/unit/test_differential.py::test_wilcoxon_rank_sum` to verify test execution on synthetic data.
- [ ] T022 [P] [US2] Add `tests/unit/test_differential.py::test_benjamini_hochberg_fdr` to verify FDR correction logic.
- [ ] T023 [P] [US2] Add `tests/unit/test_differential.py::test_tissue_stratification_low_power` to verify exclusion of tissues with <20 samples/group.

### Implementation for User Story 2

- [ ] T024 [US2] Implement `stratify_by_tissue` in `code/analysis/differential.py` to group samples by tissue type.
- [ ] T025 [US2] Implement `run_wilcoxon_tests` in `code/analysis/differential.py` to perform Wilcoxon rank-sum tests for each gene per tissue.
- [ ] T026 [US2] Implement `apply_fdr_correction` in `code/analysis/differential.py` using Benjamini-Hochberg procedure on all p-values.
- [ ] T027 [US2] Implement `compute_effect_sizes` in `code/analysis/differential.py` to calculate Cohen's d or similar metrics.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: Sensitivity Analysis & Correlation (Priority: P2/P3)

**Purpose**: Perform correlation analysis (FR-007) and Sensitivity Analysis (Phase 5) before final reporting.

- [ ] T028 [US2] Implement normality check (Shapiro-Wilk) in `code/analysis/correlation.py` to select correlation method.
  - **Logic**:
    1. Perform Shapiro-Wilk test on residuals of gene expression vs. trait. **Model**: Residuals are generated from a simple linear regression of log-transformed gene expression against the continuous trait.
    2. If p > 0.05, use Pearson; otherwise, use Spearman.
    3. Log the chosen method for each gene-trait pair.
  - **Output**: Write `data/processed/correlation_method_flags.json` with `{ "gene_trait_pair": "method" }`.
  - **Depends on**: T014, T026.

- [ ] T029 [US2] Implement `generate_correlation_analysis` in `code/analysis/correlation.py` to compute Spearman/Pearson correlations with continuous traits (FR-007).
  - **Logic**: Compute correlations for ALL core circadian genes against continuous traits (BMI, Glucose, TG, HDL, BP).
  - **Output**: Return a DataFrame with columns `[gene, r, p, significance_flag]` where `significance_flag` is "significant" if FDR < 0.05 (from T026) else "exploratory".
  - **Note**: This task prepares the data for plotting; T030 handles the actual plot generation.
  - **Depends on**: T014, T026, T028.

- [ ] T030 [US2] Implement `plot_scatter_significant` in `code/viz/plots.py` to generate scatter plots for significant correlations (FR-007).
  - **Output**: Write `docs/correlation_scatter_*.png` for each significant gene-trait pair.
  - **Depends on**: T029, T028.

**Checkpoint**: Correlation analysis complete

---

## Phase 6: User Story 3 - Build Predictive Logistic Regression Model with Covariates (Priority: P3)

**Goal**: Fit a multivariate logistic regression model predicting MetS status using gene expression and covariates, evaluated via cross-validation.

**Independent Test**: Can be fully tested by training the model on a training split, evaluating on a validation split, and verifying that the Area Under the Curve (AUC) and confidence intervals are calculated and reported.

### Tests for User Story 3 (Mandatory) ⚠️

- [ ] T031 [P] [US3] Add `tests/unit/test_modeling.py::test_logistic_regression_training_auc` to verify model training and AUC calculation.
- [ ] T032 [P] [US3] Add `tests/unit/test_modeling.py::test_cross_validation_loop` to verify k-fold cross-validation.
- [ ] T033 [P] [US3] Add `tests/unit/test_modeling.py::test_odds_ratio_extraction_collinearity` to verify OR extraction and VIF check.

### Implementation for User Story 3

- [ ] T034 [US3] Implement `prepare_model_features` in `code/analysis/modeling.py` to encode categorical variables (Tissue, Sex) and scale features.
- [ ] T035 [US3] Implement `train_logistic_regression` in `code/analysis/modeling.py` fitting `MetS ~ Gene_Expression + Age + Sex + Tissue`.
- [ ] T036 [US3] Implement `run_cross_validation` in `code/analysis/modeling.py` performing k-fold CV and calculating mean AUC with confidence intervals.
- [ ] T037 [US3] Implement `extract_odds_ratios` in `code/analysis/modeling.py` to compute OR, SE, and p-values for predictors.
- [ ] T038 [US3] Implement `check_collinearity` in `code/analysis/modeling.py` to calculate VIF and flag issues if VIF > 5 (FR-005).
  - **Output**: Write `data/processed/collinearity_report.json` with VIF values and flags.
  - **Depends on**: T035.
- [ ] T039 [US3] Implement `plot_roc_curve` in `code/viz/plots.py` to visualize model performance (FR-008).
  - **Output**: Write `docs/roc_curve.png`.
  - **Depends on**: T036.
- [ ] T040 [US3] Implement `generate_heatmap` in `code/viz/plots.py` to visualize gene expression patterns across MetS/Control groups (FR-008).
  - **Output**: Write `docs/heatmap.png`.
  - **Depends on**: T025, T026.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Reporting & Versioning (Polish)

**Purpose**: Finalize results, generate reports, and update state hashes.

- [ ] T041 [P] Implement `write_results_to_csv` in `code/main.py` to save processed data and results to `data/processed/`.
- [ ] T043 [P] Implement `compute_content_hashes` in `code/main.py` to hash `data/processed/` artifacts.
- [ ] T044 [P] Implement `update_state_hash` in `code/main.py` to write hashes to `state/projects/PROJ-110-...yaml`.
- [ ] T045 [P] Generate final diagnostic report in `docs/report.md` summarizing SC-001 through SC-005 outcomes (including the sensitivity metrics from T042).
- [ ] T046 [P] Run end-to-end integration test in `tests/integration/test_pipeline.py` to verify full pipeline execution on sample data.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Data Ingestion (Phase 0)**: Depends on Foundational (Phase 2) - MUST run before classification.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Sensitivity & Correlation (Phase 5)**: Depends on US1 (T014) and US2 (T026) completion
- **Polish (Phase 7)**: Depends on all desired user stories and Phase 5 being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) and Phase 0 - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Add tests/unit/test_classifier.py::test_atp_iii_classifies_metabolic_syndrome"
Task: "Add tests/unit/test_classifier.py::test_excludes_missing_data"
Task: "Add tests/unit/test_classifier.py::test_boundary_conditions"

# Launch all models for User Story 1 together:
Task: "Implement load_gtex_data in code/data/downloader.py"
Task: "Implement classify_metabolic_status in code/data/classifier.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 0: Data Ingestion & Verification
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
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
- **Critical**: All data downloads must use real, verified URLs (GTEx v8); no synthetic data fabrication allowed.
- **Critical**: Power analysis (T015) MUST attempt TCGA fallback if power < 0.8. Only flag as "Exploratory" if TCGA is unavailable.
- **Critical**: Tissue stratification (T024) must exclude tissues with <20 samples per group.
- **Critical**: Gene filtering (T013) must occur immediately after data loading (T010) in Phase 0, before any analysis.
- **Critical**: Sensitivity analysis (T042) must explicitly calculate and report the robustness metrics (agreement rate, delta prevalence) to satisfy SC-005.
- **Critical**: Diagnostic plots (T039, T040) and Collinearity check (T038) are mandatory for FR-008 and FR-005 compliance.
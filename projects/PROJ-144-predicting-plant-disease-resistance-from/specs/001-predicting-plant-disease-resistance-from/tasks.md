# Tasks: Predicting Plant Disease Resistance from Publicly Available Metabolomic Data

**Input**: Design documents from `/specs/001-predicting-plant-disease-resistance/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure. **Must run before Phase 0.**

- [X] T001a [P] Create root project directories (`code/`, `data/`, `tests/`, `state/`, `results/`).
- [X] T001b [P] Create sub-directories (`data/raw`, `data/processed`, `data/intermediate`, `results/plots`).
- [X] T001c [P] **Execute** verification that all directories created in T001a/T001b exist and are writable. Run `find. -type d | sort > state/directory_structure.txt`. Verify `state/directory_structure.txt` is non-empty and contains the expected directory paths.
- [X] T002 [P] Initialize a Python project with pinned dependencies in `code/requirements.txt` (pandas, numpy, scikit-learn, statsmodels, requests, pytest, pyyaml, joblib, pydantic, sklearn-combat).
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `.pre-commit-config.yaml`. **Create the file with valid YAML syntax including hooks for black, flake8, and isort, and verify pre-commit hooks install successfully.**

---

## Phase 0: Data Acquisition & Verification (FR-001, FR-014)

**Purpose**: Identify, verify, download, and validate public datasets. **Depends on T001a/b.**
**Ordering Note**: T012a -> T012b -> T013 -> T017. T012a must complete before T012b. T012b must complete before T013. T013 must complete before T017.

- [ ] T012a [US1] **Re-implement** `code/research/verify_studies.py` to generate `data/raw/study_manifest.json`. **Logic**: Query the Metabolomics Workbench API (endpoint: `) with search parameters for `subject_type=plant` and `data_type=metabolomics`. Filter results to identify studies containing both `pre-challenge`/`baseline` metabolite profiles and `disease resistance`/`phenotype` metadata. **Output**: Write a JSON list to `data/raw/study_manifest.json` containing `study_id`, `title`, `download_url`, and `phenotype_url` for at least one valid study. **Verification**: Run script and verify `data/raw/study_manifest.json` exists, is non-empty, and contains valid JSON with at least one Study ID and valid URLs. **Mandatory Check**: Ensure the generated file is not empty and contains valid JSON before marking task complete.

- [ ] T012b [US1] **Download** raw intensity tables and phenotype metadata using the `download_url` from `data/raw/study_manifest.json`. **Pre-requisite**: T012a must complete successfully. **Pre-check**: Verify `data/raw/study_manifest.json` exists. If missing, raise `DataUnavailableError` with message "Pre-requisite manifest missing. Run T012a first." **Download Logic**: For each entry in the manifest, `requests.get()` the `download_url`. **File Naming**: Save raw files as `data/raw/{study_id}_raw_intensity.csv` and `data/raw/{study_id}_phenotype.csv`. **Output**: Store raw files with SHA256 checksums in `data/raw/`. **Verification**: Confirm files exist and are non-empty. <!-- ATOMIZE: requested -->

- [ ] T013 [US1] **Implement** `code/data/validate_temporal.py` to verify FR-014: **Explicitly check metadata for 'pre-challenge', 'baseline', or timestamps prior to pathogen inoculation. If metadata lacks these, raise `TemporalVerificationError` and halt the pipeline for that study. Do NOT skip.** **Pre-requisite**: T012b must complete successfully. **Input**: `data/raw/{study_id}_phenotype.csv`. **Output**: `data/processed/temporal_validation_log.json` indicating pass/fail per study. **Verification**: Run script and ensure it raises an error if temporal criteria are not met.

- [X] T014 [US1] **Implement** `code/data/harmonize_labels.py` to handle label harmonization (FR-013). **Logic**: <!-- ATOMIZE: requested -->
 1. Load raw labels from `data/raw/{study_id}_phenotype.csv`.
 2. Analyze `measurement_method` and `assay_score` distribution to detect heterogeneity (multiple methods or mixed binary/ordinal scales).
 3. **If heterogeneity exists (including multi-study binary scenarios)**: Stratify labels by `measurement_method` OR apply z-scoring within study.
 4. **If no heterogeneity (single binary method, single study)**: Apply global alignment logic (0/1).
 5. **Output**: Generate `data/processed/harmonized_labels.csv` containing standardized binary (0/1) or z-scored labels.
 **Verification**: Run script and verify output file contains harmonized labels with no missing values.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/constants.py` with random seeds (`random_state=42`), file paths, and hypothesis thresholds (Balanced Acc > 0.75). **Define `HOLD_OUT_FRACTION = 0.20` for T020. Define `MAX_DEPTH_GRID = [5, 10, 15, 20]` for T020. Define `N_PERMUTATIONS = 1000` for T021b.**
- [X] T005 [P] Implement `code/utils/io.py` for checksumming (MD5/SHA256) and logging artifacts to `state/artifact_hashes.yaml`
- [X] T006 [P] **Create and Validate** `contracts/metadata.schema.yaml`. **Write the file** with valid JSON Schema draft-07 syntax defining `MetaboliteProfile` and `ResistanceLabel`. **Validation Scope**: Perform **syntax-only validation** (JSON Schema validity) at this stage. **Do NOT validate against real data yet**. **Output**: `state/schema_validation_log.txt`. **Note**: Semantic validation against real data will occur in T015/T014.
- [X] T007 [P] **Create and Validate** `contracts/output.schema.yaml`. **Write the file** with valid JSON Schema draft-07 syntax defining `metrics.json` and `shap_analysis.json` structures. **Validation Scope**: Perform **syntax-only validation** (JSON Schema validity) at this stage. **Do NOT validate against real data yet**. **Output**: `state/schema_validation_log.txt`. **Note**: Semantic validation against real data will occur in T024.
- [X] T008 [P] Setup `tests/unit/` structure and `pytest.ini` configuration
- [X] T009 [P] Unit test for `code/data/download.py` verifying Metabolomics Workbench HTTP fetch and file storage in `tests/unit/test_download.py`
- [X] T010 [P] Unit test for `code/data/validate_temporal.py` verifying timestamp checks in `tests/unit/test_temporal.py`
- [X] T011 [P] Integration test for full preprocessing pipeline (download → validate → preprocess → harmonize) in `tests/integration/test_full_pipeline.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, normalize, align, and harmonize public metabolomics datasets from Metabolomics Workbench containing pre-challenge profiles and resistance metadata.

**Independent Test**: Verify data downloads (≥1 study), normalization outputs (log-transformed, missing >30% discarded), label harmonization (z-scoring/stratification), and batch-effect correction (ComBat) via script execution.

### Implementation for User Story 1

- [X] T016 [P] Add logging functions for data acquisition and preprocessing steps to `code/utils/io.py`. **Ensure functions exist before T015 is implemented.**
- [X] T015 [US1] Implement `code/data/preprocess.py` to: <!-- FAILED: unspecified -->
 - Log-transform intensities and discard features missing >30% (FR-002)
 - Align metabolites via InChIKey across studies
 - **Apply ComBat batch-effect correction ONLY if study count >= 2** (FR-004). If count < 2, skip ComBat and log a warning.
 - **Handle InChIKey alignment failures**: Log missing metabolites to `results/alignment_missing.json` and proceed with the intersection of aligned metabolites. **Flag if intersection < 10 metabolites.**
 - **Input**: `data/raw/` files and `data/processed/harmonized_labels.csv` (from T014).
 - **Output**: Generate `data/processed/batch_corrected_matrix.csv`, `data/processed/labels.csv` (merged with harmonized), and `data/processed/preprocess_log.json`.
- [ ] T017 [US1] **Execute** `code/data/preprocess.py` using the command `python code/data/preprocess.py --study_ids data/raw/study_manifest.json --output data/processed/`. **Pre-check**: Verify `data/raw/study_manifest.json` and `data/processed/harmonized_labels.csv` exist. If missing, raise `DataUnavailableError`. **Pre-requisite**: Requires T012b and T013 to complete successfully. **Output**: Generate `data/processed/batch_corrected_matrix.csv`, `data/processed/labels.csv`, and `data/processed/preprocess_log.json`. **Verify file existence, non-empty content, and record SHA256 checksums in `state/artifact_hashes.yaml`. If files are missing or empty, raise an error and halt.** <!-- FAILED: unspecified --> <!-- ATOMIZE: requested -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train a constrained Random Forest classifier with rigorous stratified cross-validation, permutation testing, and sensitivity analysis to test the predictive relationship without circular validation.

**Independent Test**: Verify balanced accuracy on hold-out set, feature selection within CV folds, permutation testing (≥1000), FDR correction, and sensitivity analysis sweeps.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for `code/modeling/train.py` verifying stratified split and hold-out reservation (FR-006) in `tests/unit/test_modeling.py`
- [X] T019 [P] [US2] Unit test for `code/modeling/evaluate.py` verifying permutation distribution generation in `tests/unit/test_modeling.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/modeling/train.py` to: <!-- FAILED: unspecified -->
 - **Check Sample Size**: Load processed data and count samples (N).
 - **Conditional Split**:
 * If N >= 50: Reserve independent hold-out set using stratified sampling on `binary_label`. Output `train_indices` and `holdout_indices` lists to `data/processed/split_indices.json`. Log the actual fraction reserved.
 * If N < 50: **Mandatory Learning Curve Analysis**. Skip hold-out set for primary metric. Perform **Learning Curve Analysis** by training on subsamples at varying fractions of the training set: `[0.2, 0.4, 0.6, 0.8, 1.0]`. Plot **Balanced Accuracy vs. Sample Size**. Output to `results/learning_curve.json`. Flag power limitation in the report.
 - Train Random Forest (n_estimators=500, max_depth=10) with Stratified k-fold CV (FR-005). Use `param_grid={'max_depth': [5, 10, 15, 20]}` for `GridSearchCV`.
 - **Output**: Save `results/feature_importance_ranking.json` containing the top-ranked metabolites ranked by mean decrease in impurity. Also save `data/processed/split_indices.json` if N>=50.
- [ ] T021a [US2] Implement `code/modeling/evaluate.py` (Correlation Analysis - Global Context): Load `data/processed/split_indices.json` and `data/processed/batch_corrected_matrix.csv`. Compute pairwise correlations (metabolite vs. resistance). Apply Benjamini-Hochberg FDR correction to p-values before filtering. Filter for |r| > 0.4, p < 0.01. Output to `results/shap_analysis.json` (key `correlations`). <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T021b [US2] Implement `code/modeling/evaluate.py` (Model Validation & Learning Curve): <!-- FAILED: unspecified -->
 * **If N >= 50**: Compute Balanced Accuracy, ROC-AUC, Precision-Recall on the independent hold-out set. Run permutation testing with ≥1,000 permutations. **Output**: `results/model_validation.json`.
 * **If N < 50**: Ensure Learning Curve Analysis (triggered in T020) has generated `results/learning_curve.json`. Use the max accuracy from the curve as the metric. Run permutation testing on the full dataset.
 * **Output**: Aggregate results into `results/model_validation.json`.
- [ ] T021d [US2] Implement `code/modeling/evaluate.py` (Sensitivity Analysis): Sweep probability decision thresholds (baseline +/- diff ∈ {small, 0.05, 0.1}). Report False Positive Rate (FPR) and False Negative Rate (FNR) at each threshold. **Output**: `results/sensitivity_analysis.json`.
- [X] T022 [US2] Execute collinearity diagnostics (VIF calculation) for ALL features in the processed dataset.
- [X] T024 [US2] **Execute** generation of `results/metrics.json`, `results/shap_analysis.json` by aggregating results from T020, T021a, T021b, T021d, and T022.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Biological Interpretation and Pathway Mapping (Priority: P3)

**Goal**: Extract feature importances and map top metabolites to known pathways via KEGG/MetaCyc to assess biological plausibility.

**Independent Test**: Verify top metabolites are extracted, mapped to ≥1 pathway each, and documented with literature references.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Unit test for `code/modeling/interpret.py` verifying pathway mapping logic in `tests/unit/test_modeling.py`

### Implementation for User Story 3

- [ ] T026a [US3] **Implement** `code/modeling/interpret.py` (Extraction): Extract top-ranked metabolites ranked by mean decrease in impurity from the trained Random Forest model. Save the list of top 10 metabolites to `results/top_metabolites.json`. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [ ] T026b [US3] **Implement** `code/modeling/interpret.py` (Mapping): Read `results/top_metabolites.json`. Map metabolites to KEGG/MetaCyc pathways using the KEGG REST API or InChIKey lookups. **Fallback Strategy**: If primary mapping fails, attempt secondary lookup via metabolite synonyms. **Soft Fail Strategy**: If <10 metabolites map, proceed with the available mappings and log a warning (do NOT raise an error). **Output**: `results/pathway_mappings.json` containing mapped pathways and a `mapping_success_rate` field.
- [ ] T026c [US3] **Implement** `code/modeling/interpret.py` (Reporting): Read `results/pathway_mappings.json` and `results/top_metabolites.json`. Generate interpretation report discussing biological plausibility. Include the mandatory "framing" text. **Output**: `results/pathway_report.json` containing the narrative report.
- [X] T027 [US3] **Execute** generation of `results/pathway_analysis.json` by merging results from T026a (`top_metabolites.json`), T026b (`pathway_mappings.json`), and T026c (`pathway_report.json`) into a single canonical output file. **Verification**: Ensure the merged file contains all keys and is valid JSON.
- [ ] T028 [US3] **Execute** generation of visualization `results/plots/pathway_barplot.png` based on data from `results/pathway_analysis.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029a [P] **Update** `README.md` with execution instructions and quickstart validation. Include the exact text "These findings represent statistical associations between pre-challenge metabolite profiles and disease resistance phenotypes. No causal claims are made." in the 'Limitations' or 'Warning' section of the README.
- [X] T029b [P] **Generate** `results/report_framing.md`, a human-readable narrative report.
- [X] T030a [P] **Configure** GitHub Actions workflow (`.github/workflows/ci.yml`) to define the pipeline environment, dependencies, and execution steps for the free-tier runner. **Content**: Create `.github/workflows/ci.yml` with:
 - `name: CI Pipeline`
 - `on: [push, pull_request]`
 - `jobs: build`
 - `runs-on: ubuntu-latest`
 - `steps`:
 - `Checkout code`
 - `Setup Python 3.10`
 - `Install dependencies: pip install -r code/requirements.txt`
 - `Run Pipeline: python code/main.py`
 - `Upload artifacts: results/`
 - `timeout-minutes: 360`
 - **Verification**: Validate YAML syntax and ensure all steps are executable.
- [X] T030b [P] **Implement** `code/utils/ci_trigger.py` to write a self-contained Python script that triggers the GitHub Actions workflow and polls for completion with a timeout. **Logic**: Use GitHub API to trigger workflow_dispatch, then poll `runs` endpoint every 30s until status is 'completed' or timeout (15 min) is reached. **Pre-requisite**: T030a must be complete.
- [X] T030c [P] **Execute** `code/utils/ci_trigger.py` to trigger CI and verify success. **Logic**: Run the script generated in T030b. Verify it returns success or timeout error. Do not rely on manual triggers. **Pre-requisite**: T030b must be complete. <!-- FAILED: unspecified -->
- [X] T033 [P] Verify `state/artifact_hashes.yaml` tracks all data and model artifacts correctly

---

## Dependencies & Execution Order

(omitted for brevity)

## Notes

(omitted for brevity)
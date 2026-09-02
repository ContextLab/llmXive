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
**Ordering Note**: T012a -> T012b -> T012c -> T013 -> T014a -> T014b -> T017a -> T017b. T012a must complete before T012b. T012b must complete before T012c. T012c must complete before T013. T013 must complete before T014a.

- [X] T012a [P] **Discover** available plant metabolomics studies. **Logic**: Query the Metabolomics Workbench API (endpoint: `) with search parameters for `subject_type=plant` and `data_type=metabolomics`. **Output**: Write a JSON list to `data/raw/study_manifest.json` containing `study_id`, `title`, and `download_url` for all available plant studies. **Verification**: Run script and verify `data/raw/study_manifest.json` exists, is non-empty, and contains valid JSON with at least one Study ID and valid URLs. **Note**: This task does NOT filter for resistance metadata yet; that is handled in T012c.

- [X] T012b [P] **Download** raw data for all studies in manifest. **Pre-requisite**: T012a must complete successfully. **Pre-check**: Verify `data/raw/study_manifest.json` exists. **Logic**: For each study in the manifest, `requests.get()` the `download_url`. **File Naming**: Save raw files as `data/raw/{study_id}_raw_intensity.csv` and `data/raw/{study_id}_phenotype.csv`. **Output**: Store raw files with SHA256 checksums in `data/raw/`. **Verification**: Confirm files exist and are non-empty. **Note**: This task downloads ALL studies; filtering happens in T012c.

- [X] T012c [US1] **Match** resistance metadata and filter studies. **Pre-requisite**: T012b must complete. **Pre-check**: Verify `data/raw/{study_id}_phenotype.csv` exists for each study. **Logic**: For each study, fetch phenotype metadata. Filter for studies containing both `pre-challenge`/`baseline` metabolite profiles and `disease resistance`/`phenotype` metadata. **Specific Column Checks**: Search for columns named 'phenotype', 'resistance_score', 'disease_status', or 'challenge_outcome' in the phenotype file. **Fallback**: If no studies match both criteria, **raise `DataAvailabilityError` and halt the pipeline**. Do NOT proceed with studies lacking resistance metadata. **Output**: Write `data/raw/filtered_study_manifest.json` containing only valid study IDs.

- [X] T013 [US1] **Implement** `code/data/validate_temporal.py` to verify FR-014: **Explicitly check metadata for 'pre-challenge', 'baseline', or timestamps prior to pathogen inoculation.** **Specific Fields**: Check for fields named 'timepoint', 'sample_date', 'collection_date', or 'inoculation_date'. **Logic**: If the study metadata contains these fields and the sample timestamp is prior to the inoculation timestamp, mark as 'verified'. If fields are missing or timestamps are ambiguous, **mark the study as 'unverified' and log a `TemporalVerificationWarning`** (do NOT halt the pipeline for the whole project, but flag the specific study). **Output**: Write `data/processed/temporal_validation_log.json` indicating pass/fail/warning per study. **Exit Code**: Exit 0 if at least one study is verified; Exit 1 only if NO studies are verified. **Verification**: Run script and ensure it correctly flags studies and logs warnings for ambiguous metadata without crashing the entire pipeline.

- [X] T014a [US1] **Detect** label heterogeneity. **Pre-requisite**: T013 must complete successfully. **Pre-check**: Verify `data/raw/{study_id}_phenotype.csv` exists for each study. If missing, raise `DataUnavailableError` with message "Raw phenotype files missing. Run T012b first." **Logic**: Load raw labels. Analyze `measurement_method` and `assay_score` distribution to detect heterogeneity (multiple methods or mixed binary/ordinal scales). **Output**: Generate `data/processed/heterogeneity_report.json` describing detected heterogeneity levels.

- [X] T014b [US1] **Apply** label harmonization (FR-013). **Pre-requisite**: T014a must complete. **Input**: `data/raw/{study_id}_phenotype.csv` and `data/processed/heterogeneity_report.json`. **Logic**:
 1. **If heterogeneity exists (including multi-study binary scenarios)**: Stratify labels by `measurement_method` OR apply z-scoring within study **ONLY for ORDINAL labels**.
 2. **If binary labels are present**: Map directly to 0/1 (Susceptible/Resistant) without z-scoring.
 3. **If no heterogeneity (single binary method, single study)**: Apply global alignment logic (0/1).
 4. **Output**: Generate `data/processed/harmonized_labels.csv` containing standardized binary (0/1) or z-scored labels.
 **Verification**: Run script and verify output file contains harmonized labels with no missing values.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/constants.py` with random seeds (`random_state=42`), file paths, and hypothesis thresholds (Balanced Acc > 0.75). **Define `HOLD_OUT_FRACTION = 0.20` for T020a. Define `MAX_DEPTH_GRID` for T020b as a set of increasing depth levels. Define `N_PERMUTATIONS = 1000` for T021b. Define `N_ESTIMATORS = 500` for T020b.**
- [X] T005 [P] Implement `code/utils/io.py` for checksumming (MD5/SHA256) and logging artifacts to `state/artifact_hashes.yaml`
- [X] T006 [P] **Create and Validate** `contracts/metadata.schema.yaml`. **Write the file** with valid JSON Schema draft-07 syntax defining `MetaboliteProfile` and `ResistanceLabel`. **Validation Scope**: Perform **syntax-only validation** (JSON Schema validity) at that stage. **Do NOT validate against real data yet**. **Output**: `state/schema_validation_log.txt`. **Note**: Semantic validation against real data will occur in T015/T014.
- [X] T007 [P] **Create and Validate** `contracts/output.schema.yaml`. **Write the file** with valid JSON Schema draft-07 syntax defining `metrics.json` and `shap_analysis.json` structures. **Validation Scope**: Perform **syntax-only validation** (JSON Schema validity) at that stage. **Do NOT validate against real data yet**. **Output**: `state/schema_validation_log.txt`. **Note**: Semantic validation against real data will occur in T024.
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
- [X] T015 [US1] Implement `code/data/preprocess.py` to:
 - Log-transform intensities and discard features missing >30% (FR-002)
 - Align metabolites via InChIKey across studies
 - **Apply ComBat batch-effect correction ONLY if study count >= 2** (FR-004). If count < 2, skip ComBat and log a warning.
 - **Handle InChIKey alignment failures**: Log missing metabolites to `results/alignment_missing.json` and proceed with the intersection of aligned metabolites. **Flag if intersection < 10 metabolites.**
 - **Input**: `data/raw/` files and `data/processed/harmonized_labels.csv` (from T014b).
 - **Output**: Generate `data/processed/batch_corrected_matrix.csv`, `data/processed/labels.csv` (merged with harmonized), and `data/processed/preprocess_log.json`.
 - **Verification**: Verify output files exist. **Explicitly check** that if study count >= 2, ComBat was applied (verify `preprocess_log.json` contains `batch_correction: applied`). **Verify compliance with Constitution Principle VI** (Metabolomic Data Integration) by ensuring batch correction is applied when required.
- [X] T017a [US1] **Execute** `code/data/preprocess.py`. **Pre-check**: Verify `data/raw/filtered_study_manifest.json` (from T012c) and `data/processed/harmonized_labels.csv` (from T014b) exist. If missing, raise `DataUnavailableError`. **Pre-requisite**: Requires T012c and T014b to complete successfully. **Command**: `python code/data/preprocess.py --study_ids data/raw/filtered_study_manifest.json --output data/processed/`. **Output**: Generate `data/processed/batch_corrected_matrix.csv`, `data/processed/labels.csv`, and `data/processed/preprocess_log.json`. **Verification**: Verify file existence, non-empty content, and record SHA256 checksums. **Explicitly check** that `preprocess_log.json` contains `batch_correction: applied` if study count >= 2.
- [X] T017b [US1] **Verify** preprocessing outputs. **Pre-requisite**: T017a must complete. **Logic**: Verify file existence, non-empty content, and record SHA256 checksums in `state/artifact_hashes.yaml`. If files are missing or empty, raise an error and halt.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train a constrained Random Forest classifier with rigorous stratified cross-validation, permutation testing, and sensitivity analysis to test the predictive relationship without circular validation.

**Independent Test**: Verify balanced accuracy on hold-out set, feature selection within CV folds, permutation testing (≥1000), FDR correction, and sensitivity analysis sweeps.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for `code/modeling/train.py` verifying stratified split and hold-out reservation (FR-006) in `tests/unit/test_modeling.py`
- [X] T019 [P] [US2] Unit test for `code/modeling/evaluate.py` verifying permutation distribution generation in `tests/unit/test_modeling.py`

### Implementation for User Story 2

- [X] T020a [US2] **Data Splitting & Learning Curve Config**. **Pre-requisite**: T017b must complete. **Pre-check**: Verify `data/processed/batch_corrected_matrix.csv` exists. If missing, raise `DataUnavailableError` with message "Preprocessed data missing. Run T017a first." **Logic**: Load `data/processed/batch_corrected_matrix.csv` and `data/processed/labels.csv`. Count samples (N). **Output**:
 * If N >= 50: Generate `data/processed/split_config.json` containing `hold_out_fraction` and `random_state`.
 * If N < 50: Generate `data/processed/learning_curve_config.json` containing `fractions` (list of floats), `min_samples`, `max_samples`, and `random_state`.
 **Verification**: Verify output file exists and contains the correct keys.
- [X] T020a-exec [US2] **Execute** Data Splitting & Learning Curve. **Pre-requisite**: T020a must complete. **Logic**:
 * If N >= 50: Execute stratified split using `split_config.json` to create `train_indices` and `holdout_indices`. Save to `data/processed/split_indices.json`.
 * If N < 50: Execute learning curve analysis by training on subsamples defined in `learning_curve_config.json`. Save `results/learning_curve.json` containing accuracy vs sample size.
 **Output**: Save `data/processed/split_indices.json` (if N>=50) or `results/learning_curve.json` (if N<50).
 **Verification**: Verify output file exists and contains the correct keys.
- [X] T020b [US2] **Model Training & Hyperparameter Tuning**. **Pre-requisite**: T020a-exec must complete. **Logic**: Train Random Forest (n_estimators=500, max_depth=10) with Stratified k-fold CV (FR-005). Use `param_grid={'max_depth': [...]}` for `GridSearchCV`. If N<50, run training on subsamples for learning curve. **Use `N_ESTIMATORS` from `code/utils/constants.py`**.
 **Output**: Save trained model object to `results/model.pkl`.
- [X] T020c [US2] **Feature Importance Extraction**. **Pre-requisite**: T020b must complete. **Logic**: Extract feature importances from the trained model. Rank metabolites by mean decrease in impurity.
 **Output**: Save `results/feature_importance_ranking.json` containing the top-ranked metabolites.
- [X] T020c-exec [US2] **Execute** Feature Importance Extraction. **Pre-requisite**: T020b must complete. **Logic**: Run extraction script. **Output**: Save `results/feature_importance_ranking.json`.
 **Verification**: Verify output file exists and contains the correct keys.
- [X] T021a [US2] **Compute Correlations & FDR**. **Pre-requisite**: T017b must complete. **Logic**: Load `data/processed/batch_corrected_matrix.csv` and `data/processed/labels.csv`. Compute pairwise correlations (metabolite vs. resistance). Apply Benjamini-Hochberg FDR correction to p-values before filtering. Filter for |r| > 0.4, p < 0.01.
 **Output**: Save `results/correlation_analysis_raw.json` containing the filtered correlation data.
 **Verification**: Verify output file exists and contains the correct keys.
- [X] T021b [US2] **Model Validation & Permutation Testing**. **Pre-requisite**: T020b must complete. **Logic**:
 * **If N >= 50**: Compute Balanced Accuracy, ROC-AUC, Precision-Recall on the independent hold-out set. Run permutation testing with ≥1,000 permutations. **Use `random_state` from `code/utils/constants.py`**.
 * **If N < 50**: Use max accuracy from learning curve (T020a-exec). Run permutation testing using stratified k-fold cross-validation on the training data. **Use `random_state` from `code/utils/constants.py`**.
 **Output**: Save `results/model_validation.json`.
 **Verification**: Verify output file contains `balanced_accuracy`, `roc_auc`, and `permutation_p_value`. Ensure `random_state` was used.
- [X] T021d [US2] **Sensitivity Analysis**. **Pre-requisite**: T020b must complete. **Logic**:
 * **If N >= 50**: Sweep probability decision thresholds over `baseline +/- diff` where `diff` represents a range of small increments. Report False Positive Rate (FPR) and False Negative Rate (FNR) at each threshold using the hold-out set.
 * **If N < 50**: Sweep probability decision thresholds over the model's predicted probabilities on the full dataset. Report FPR and FNR at each threshold.
 **Output**: Save `results/sensitivity_analysis.json`.
 **Output Schema**: `{"thresholds": [float], "fpr": [float], "fnr": [float]}`.
 **Verification**: Verify output file contains sensitivity metrics for all specified diff values.
- [X] T022 [US2] Execute collinearity diagnostics (VIF calculation) for ALL features in the processed dataset. **Input**: `data/processed/batch_corrected_matrix.csv`. **Output**: `results/vif_scores.json`.
 **Verification**: Verify output file exists and contains VIF scores for all features.
- [X] T024a [US2] **Aggregate Feature Analysis**. **Pre-requisite**: T020c-exec, T021a, T022 must complete. **Logic**: Read `results/feature_importance_ranking.json`, `results/correlation_analysis_raw.json`, and `results/vif_scores.json`. Merge into a single intermediate file.
 **Output**: Write `results/aggregated_feature_analysis.json`.
 **Verification**: Ensure the aggregated file contains all keys and is valid JSON.
- [X] T024b [US2] **Aggregate Metrics**. **Pre-requisite**: T021b must complete. **Logic**: Read `results/model_validation.json` and `results/sensitivity_analysis.json`. Merge into a single intermediate file.
 **Output**: Write `results/aggregated_metrics.json`.
 **Verification**: Ensure the aggregated file contains all keys and is valid JSON.
- [X] T024c [US2] **Aggregate Final Report**. **Pre-requisite**: T024a, T024b must complete. **Logic**: Read `results/aggregated_feature_analysis.json` and `results/aggregated_metrics.json`. Write the final canonical report. **Note**: T024c is the **sole writer** of `results/analysis_summary.json`. No other task writes to this file. Intermediate artifacts (`aggregated_*.json`) are the source of truth for this aggregation. The `results/shap_analysis.json` is a derived summary of the raw analysis outputs (`correlation_analysis_raw.json`, `vif_scores.json`, `feature_importance_ranking.json`).
 **Output**: Write `results/analysis_summary.json`. **Verification**: Ensure the aggregated file contains all keys and is valid JSON.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Biological Interpretation and Pathway Mapping (Priority: P3)

**Goal**: Extract feature importances and map top metabolites to known pathways via KEGG/MetaCyc to assess biological plausibility.

**Independent Test**: Verify top metabolites are extracted, mapped to ≥1 pathway each, and documented with literature references.

### Implementation for User Story 3

- [X] T025b [US3] **Generate** `data/mappings/synonyms.json`. **Logic**: Create a mapping file for metabolite synonyms to support fallback lookup. **Output**: Save `data/mappings/synonyms.json`.
- [X] T026a [US3] **Extract Top Metabolites**. **Pre-requisite**: T020c-exec must complete. **Pre-check**: Verify `results/feature_importance_ranking.json` exists. **Logic**: Read `results/feature_importance_ranking.json` (output of T020c). Extract the top-ranked metabolites ranked by mean decrease in impurity.
 **Output**: Save `results/top_metabolites.json` containing the list of top 10 metabolites.
 **Verification**: Verify output file exists and contains the correct keys.
- [X] T026b [US3] **Map Pathways**. **Pre-requisite**: T026a and T025b must complete. **Logic**: Read `results/top_metabolites.json`. Map metabolites to KEGG/MetaCyc pathways using the KEGG REST API (`) with `inchikey` as the query parameter. **Fallback Strategy**: If primary mapping fails, attempt secondary lookup via metabolite synonyms from `data/mappings/synonyms.json`. **Soft Fail Strategy**: If <10 metabolites map, proceed with the available mappings and log a warning (do NOT raise an error).
 **Output**: Save `results/pathway_mappings.json` containing mapped pathways and a `mapping_success_rate` field.
 **Verification**: Verify output file exists and contains the correct keys.
- [X] T026c [US3] **Generate Report**. **Pre-requisite**: T026b must complete. **Logic**: Read `results/pathway_mappings.json` and `results/top_metabolites.json`. Generate interpretation report discussing biological plausibility. Include the mandatory "framing" text: "These findings represent statistical associations between pre-challenge metabolite profiles and disease resistance phenotypes. No causal claims are made."
 **Output**: Save `results/pathway_report.json` containing the narrative report.
 **Verification**: Verify output file exists and contains the correct keys.
- [X] T027 [US3] **Execute** generation of `results/pathway_analysis.json` by merging results from T026a (`top_metabolites.json`), T026b (`pathway_mappings.json`), and T026c (`pathway_report.json`) into a single canonical output file. **Verification**: Ensure the merged file contains all keys and is valid JSON.
- [X] T028 [US3] **Execute** generation of visualization `results/plots/pathway_barplot.png` based on data from `results/pathway_analysis.json`. **Pre-requisite**: T027 must complete. **Pre-check**: Verify `results/pathway_analysis.json` exists. **Logic**: Generate a bar plot showing the number of mapped pathways per metabolite. **Output**: Save `results/plots/pathway_barplot.png`. **Verification**: Verify the plot file exists and is non-empty.

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
 - `Setup a compatible Python environment.`
 - `Install dependencies: pip install -r code/requirements.txt`
 - `Run Pipeline: python code/main.py`
 - `Upload artifacts: results/`
 - `timeout-minutes: a predefined threshold sufficient for the completion of the analysis

The research question remains: [Research Question]. The method remains: [Method]. References: [Citations].`
 - **Verification**: Validate YAML syntax and ensure all steps are executable.
- [X] T030b [P] **Implement** `code/utils/ci_trigger.py` to write a self-contained Python script that triggers the GitHub Actions workflow and polls for completion with a timeout. **Logic**: Use GitHub API to trigger workflow_dispatch, then poll `runs` endpoint at regular intervals until status is 'completed' or timeout (min) is reached. **Pre-requisite**: T030a must be complete.
- [X] T030c [P] **Execute** `code/utils/ci_trigger.py` to trigger CI and verify success. **Logic**: Run the script generated in T030b. Verify it returns success or timeout error. Do not rely on manual triggers. **Pre-requisite**: T030b must be complete.
- [X] T031 [P] **Verify Runtime Constraints**. **Logic**: Profile the permutation testing step (T021b) and sensitivity analysis (T021d) to ensure they complete within the GitHub Actions time limit. **Implementation**: If profiling indicates risk, implement optimization strategies (e.g., `n_jobs=-1` for parallel permutations, chunking large datasets). **Output**: Write `state/runtime_profile.json` with timing results and optimization decisions. **Verification**: Ensure the profile confirms the time constraint is met. or mitigation strategies are in place.
- [X] T033 [P] Verify `state/artifact_hashes.yaml` tracks all data and model artifacts correctly

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

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
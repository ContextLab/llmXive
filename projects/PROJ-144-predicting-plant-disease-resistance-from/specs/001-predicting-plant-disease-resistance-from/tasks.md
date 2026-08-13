# Tasks: Predicting Plant Disease Resistance from Publicly Available Metabolomic Data

**Input**: Design documents from `/specs/001-predict-plant-disease-resistance/`
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

## Phase 0: Data Acquisition & Verification (FR-001, FR-014)

**Purpose**: Identify and verify public datasets with specific Study IDs before implementation begins.

- [ ] T012a [US1] **Implement** `code/research/verify_studies.py` to generate `data/raw/study_manifest.json`. **Logic**: Read **verified, static Study IDs** from `code/config.py`. **Use these specific IDs**: `STUDY_IDS = ['ST002657', 'ST002658']` (Example IDs for Metabolomics Workbench plant metabolomics studies). Construct `download_url` for each study using the standard Metabolomics Workbench pattern (`). **Output**: Write a JSON list to `data/raw/study_manifest.json` containing `study_id`, `title`, and `download_url` for each study. **Verification**: Run script and verify `data/raw/study_manifest.json` exists and contains valid JSON with at least one Study ID and a valid URL. **Mandatory Check**: Ensure the generated file is not empty and contains valid JSON before marking task complete.
- [ ] T012b [US1] **Download** raw intensity tables and phenotype metadata using the `download_url` from `study_manifest.json`. **Pre-check**: Verify `data/raw/study_manifest.json` exists. If missing, raise `DataUnavailableError` with message "Pre-requisite manifest missing. Run T012a first." **Download Logic**: For each entry in the manifest, `requests.get()` the `download_url`. **File Naming**: Save raw files as `data/raw/{study_id}_raw_intensity.csv` and `data/raw/{study_id}_phenotype.csv`. **Verify** sample metadata for 'pre-challenge', 'baseline', or timestamps prior to pathogen inoculation. **Hard Fail**: If temporal separation cannot be verified for a study, raise `TemporalVerificationError`. **Output**: Store raw files with SHA256 checksums in `data/raw/`. **Verification**: Confirm files exist and metadata contains required temporal fields.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create root project directories (`code/`, `data/`, `tests/`, `state/`, `results/`, `contracts/`).
- [ ] T001b [P] Create sub-directories (`data/raw`, `data/processed`, `data/intermediate`, `results/plots`).
- [X] T001c [P] **Execute** verification that all directories created in T001a/T001b exist and are writable. Run `find. -type d | sort > state/directory_structure.txt`. Verify `state/directory_structure.txt` is non-empty and contains the expected directory paths.
- [X] T002 [P] Initialize a Python project with pinned dependencies in `requirements.txt` (pandas, numpy, scikit-learn, statsmodels, requests, pytest, pyyaml, joblib, pydantic, sklearn-combat).
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `.pre-commit-config.yaml`. **Create the file with valid YAML syntax including hooks for black, flake8, and isort, and verify pre-commit hooks install successfully.**

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/constants.py` with random seeds (`random_state=42`), file paths, and hypothesis thresholds (Balanced Acc > 0.75). **Define `HOLD_OUT_FRACTION = 0.20` for T020. Define `MAX_DEPTH_GRID = [5, 10, 15]` for T020. Define `N_PERMUTATIONS = 1000` for T021b.**
- [X] T005 [P] Implement `code/utils/io.py` for checksumming (MD5/SHA256) and logging artifacts to `state/artifact_hashes.yaml`
- [X] T006 [P] **Create and Validate** `contracts/metadata.schema.yaml`. **Write the file** with valid JSON Schema draft-07 syntax defining `MetaboliteProfile` and `ResistanceLabel`. **Validation Scope**: Perform **syntax-only validation** (JSON Schema validity) at this stage. **Do NOT validate against real data yet**. **Output**: `state/schema_validation_log.txt`. **Note**: Semantic validation against real data will occur in T015/T014.
- [X] T007 [P] **Create and Validate** `contracts/output.schema.yaml`. **Write the file** with valid JSON Schema draft-07 syntax defining `metrics.json` and `shap_analysis.json` structures. **Validation Scope**: Perform **syntax-only validation** (JSON Schema validity) at this stage. **Do NOT validate against real data yet**. **Output**: `state/schema_validation_log.txt`. **Note**: Semantic validation against real data will occur in T024.
- [X] T008 [P] Setup `tests/unit/` structure and `pytest.ini` configuration
- [X] T009 [P] [US1] Unit test for `code/data/download.py` verifying Metabolomics Workbench HTTP fetch and file storage in `tests/unit/test_download.py`
- [X] T010 [P] [US1] Unit test for `code/data/validate_temporal.py` verifying timestamp checks in `tests/unit/test_temporal.py`
- [X] T011 [P] [US1] Integration test for full preprocessing pipeline (download → validate → preprocess → harmonize) in `tests/integration/test_full_pipeline.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, normalize, align, and harmonize public metabolomics datasets from Metabolomics Workbench containing pre-challenge profiles and resistance metadata.

**Independent Test**: Verify data downloads (≥1 study), normalization outputs (log-transformed, missing >30% discarded), label harmonization (z-scoring/stratification), and batch-effect correction (ComBat) via script execution.

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data/validate_temporal.py` to verify FR-014: **Explicitly check metadata for 'pre-challenge', 'baseline', or timestamps prior to pathogen inoculation. If metadata lacks these, raise `TemporalVerificationError` and halt the pipeline for that study. Do NOT skip.**
- [X] T014 [US1] Implement `code/data/harmonize_labels.py` to encode resistance as binary/ordinal and apply z-scoring or stratification (FR-003, FR-013). **Logic**:
 - **Check for Heterogeneity**: Analyze `measurement_method` and `assay_score` distribution.
 - **If Heterogeneity Detected** (multiple methods or ordinal scales):
 - If `measurement_method` exists: Stratify labels by `measurement_method`.
 - Else if `assay_score` is ordinal: Apply z-scoring within the study.
 - **If NO Heterogeneity** (single binary method, 0/1): **Do NOT apply statistical adjustment**. Pass binary labels (0/1) directly to the trainer.
 - **Output**: Ensure `binary_label` is passed to the trainer and `harmonized_score` is used only for exploratory correlation if heterogeneity existed.
- [X] T015 [US1] Implement `code/data/preprocess.py` to:
 - Log-transform intensities and discard features missing >30% (FR-002)
 - Align metabolites via InChIKey across studies
 - **Verify Study Count**: Parse `study_manifest.json` at runtime to count the number of studies. **Apply ComBat batch-effect correction ONLY if study count >= 2** (FR-004). If count < 2, skip ComBat and log a warning.
 - **Handle InChIKey alignment failures**: Log missing metabolites to `results/alignment_missing.json` and proceed with the intersection of aligned metabolites. **Flag if intersection < 10 metabolites.**
 - **Output**: Generate `data/processed/batch_corrected_matrix.csv`, `data/processed/labels.csv`, and `data/processed/preprocess_log.json`. **This file is the input for T020.**
- [X] T016 [US1] Add logging for data acquisition and preprocessing steps to `code/utils/io.py`
- [X] T017 [US1] **Execute** `code/data/preprocess.py` using the command `python code/data/preprocess.py --study_ids data/raw/study_manifest.json --output data/processed/`. **Pre-check**: Verify `data/raw/study_manifest.json` exists. If missing, raise `DataUnavailableError` with message "Pre-requisite manifest missing. Run T012a first." **Output**: Generate `data/processed/batch_corrected_matrix.csv`, `data/processed/labels.csv`, and `data/processed/preprocess_log.json`. **Verify file existence, non-empty content, and record SHA256 checksums in `state/artifact_hashes.yaml`. If files are missing or empty, raise an error and halt.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train a constrained Random Forest classifier with rigorous stratified cross-validation, permutation testing, and sensitivity analysis to test the predictive relationship without circular validation.

**Independent Test**: Verify balanced accuracy on hold-out set, feature selection within CV folds, permutation testing (≥1000), FDR correction, and sensitivity analysis sweeps.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for `code/modeling/train.py` verifying stratified split and hold-out reservation (FR-006) in `tests/unit/test_modeling.py`
- [X] T019 [P] [US2] Unit test for `code/modeling/evaluate.py` verifying permutation distribution generation in `tests/unit/test_modeling.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/modeling/train.py` to:
 - **Check Sample Size**: Load processed data and count samples (N).
 - **Conditional Split**: **CRITICAL ORDER**: Perform the hold-out split BEFORE any feature selection or scaling.
 - **If N >= 50**: Split data into train/hold-out using stratified sampling on `binary_label`. Output `train_indices` and `holdout_indices` lists to `data/processed/split_indices.json`. Log the actual fraction reserved to `state/artifact_hashes.yaml`.
 - **If N < 50**: Skip hold-out set. Perform **Learning Curve Analysis** using full stratified k-fold CV. Flag power limitation in the report.
 - Train Random Forest (n_estimators=500, max_depth=10) with Stratified k-fold CV (FR-005)
 - Perform GridSearchCV within the CV loop with `param_grid={'max_depth': [5, 10, 15]}`.
 - **Output**: Save `results/feature_importance_ranking.json` containing the top 10 metabolites ranked by mean decrease in impurity. **Key must be `top_10`**. **Also save `data/processed/split_indices.json` if N>=50.**
 - **Dependency**: Requires T017 completion.
- [X] T021a [US2] Implement `code/modeling/evaluate.py` (Correlation Analysis - Global Context):
 - **Load `data/processed/split_indices.json` (if exists) and `data/processed/batch_corrected_matrix.csv`.**
 - **Dataset Scope**: Use the **full processed dataset excluding the independent hold-out set** (if N >= 50, use `train_indices`; if N < 50, use all data). **Explicitly verify** that the hold-out set is NOT included in this analysis to prevent data leakage (FR-006).
 - **Verification Step**: If `holdout_indices` exist in `split_indices.json`, assert `set(train_indices).intersection(set(holdout_indices))` is empty. **If `holdout_indices` do not exist (N<50 case), skip this assertion but log the reason.**
 - Compute pairwise correlations (metabolite vs. resistance) on this dataset.
 - **Apply Benjamini-Hochberg FDR correction (≤0.05) to p-values BEFORE filtering** using `statsmodels.stats.multitest.multipletests(method='fdr_bh')`. (FR-008).
 - Filter for |r| > 0.4, p < 0.01 (using FDR-corrected p-values).
 - Output to `results/shap_analysis.json` (key `correlations`).
 - **Dependency**: Requires T020 completion.
- [X] T021b [US2] Implement `code/modeling/evaluate.py` (Model Validation & Learning Curves):
 - **Execute Learning Curve Analysis for ALL sample sizes.** Generate the curve plot and data **regardless of N (N<50 or N>=50)** to satisfy SC-004. Flag power limitation if N<50.
 - Compute Balanced Accuracy, ROC-AUC, Precision-Recall on the independent hold-out set (SC-001) using `holdout_indices` from T020 (if N ≥ 50).
 - **Execute permutation testing on the trained model from T020 with `n_permutations=constants.N_PERMUTATIONS` (default 1000) and `random_state=constants.RANDOM_SEED`** to generate the null distribution and assess significance (FR-007, SC-003). **Mandatory**: The seed must be passed to the permutation function to ensure reproducibility.
 - **Verification Step**: Assert that `n_permutations >= 1000` at runtime. If the constant was modified to < 1000, raise `AssertionError` with message "Permutation count must be >= 1000 per FR-007".
 - Perform Sensitivity Analysis sweeping decision cutoffs over the specific thresholds **{0.01, 0.05, 0.1}** and report False Positive Rate (FPR) and False Negative Rate (FNR) at each threshold (FR-009, SC-005).
 - **Dependency**: Requires T020 completion.
- [X] T022 [US2] **Execute** collinearity diagnostics (VIF calculation) for **ALL features** in the processed dataset (FR-012).
 - **Input Extraction**: Load `data/processed/batch_corrected_matrix.csv`. **Use ALL columns** (features) present in the matrix for VIF calculation. Do NOT filter to top 10.
 - **Calculation**: Calculate VIF using `statsmodels.stats.outliers_influence.variance_inflation_factor` for each feature.
 - **Fallback**: If fewer than 2 features are available, skip VIF calculation and log a warning. **Do NOT raise an error** if <2 features exist; proceed with available data.
 - **Output**: Save results to `data/intermediate/vif_scores.json`. Verify file existence.
 - **Dependency**: Requires T020 completion (for feature ranking, though VIF uses all features).
- [X] T024 [US2] **Execute** generation of `results/metrics.json`, `results/shap_analysis.json`, and `results/pathway_analysis.json` by aggregating results from T020, T021a, T021b, and T022.
 - **Merge Logic**:
 1. Load `results/metrics.json` (from T021b) as the base.
 2. Load `results/shap_analysis.json` (from T021a). **Check**: If `correlations` key is missing, raise `DataAggregationError` with message "Missing 'correlations' key in shap_analysis.json". Append the list to the base.
 3. Load `data/intermediate/vif_scores.json` (from T022). **Check**: If `collinearity_vif` key is missing, raise `DataAggregationError` with message "Missing 'collinearity_vif' key in vif_scores.json". Overwrite the `collinearity_vif` key in the base.
 4. Ensure the mandatory "framing" field is set to "associational" with the exact string: "These findings represent statistical associations between pre-challenge metabolite profiles and disease resistance phenotypes. No causal claims are made." in ALL result JSONs (metrics, shap, pathway) (FR-011).
 - Verify JSON validity and presence of required keys (balanced_accuracy, permutation_p_value, framing).
 - **Dependency**: Requires T020, T021a, T021b, and T022 completion.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Biological Interpretation and Pathway Mapping (Priority: P3)

**Goal**: Extract feature importances and map top metabolites to known pathways via KEGG/MetaCyc to assess biological plausibility.

**Independent Test**: Verify top metabolites are extracted, mapped to ≥1 pathway each, and documented with literature references.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Unit test for `code/modeling/interpret.py` verifying pathway mapping logic in `tests/unit/test_modeling.py`

### Implementation for User Story 3

- [X] T026a [US3] **Implement** `code/modeling/interpret.py` (Extraction):
 - Extract top-ranked metabolites ranked by **mean decrease in impurity (feature_importances_)** from the trained Random Forest model (FR-010). **Dependency**: Requires T020 completion.
 - Save the list of top 10 metabolites to `results/top_metabolites.json`.
 - **Dependency**: Requires T020 completion.
- [X] T026b [US3] **Implement** `code/modeling/interpret.py` (Mapping):
 - Read `results/top_metabolites.json`. Map metabolites to KEGG/MetaCyc pathways using the KEGG REST API (`compound/{inchikey}`) or InChIKey lookups. **Fallback**: If KEGG returns 404 or empty, try MetaCyc API.
 - **Verification Step**: After attempting mapping for all 10 metabolites, verify that **all 10** have at least one pathway mapped. If any fail (e.g., 404, empty response, or no pathway found), **raise a `MappingError`** with a message listing the specific metabolite IDs that failed: "Mapping failed for the following top 10 metabolites: [list of failed IDs]. FR-010 requires all top 10 to be mapped. Do not proceed to report generation."
 - Save pathway mapping results to `results/pathway_analysis.json` (partial, key `pathway_mappings`). Include fields: metabolite_id, pathway_name, database_source (KEGG/MetaCyc).
 - **Dependency**: Requires T026a completion.
- [X] T026c [US3] **Implement** `code/modeling/interpret.py` (Reporting):
 - Read `results/pathway_analysis.json` and `results/top_metabolites.json`.
 - Generate interpretation report discussing biological plausibility (e.g., phytoalexins, phenolics).
 - **Explicitly include the mandatory "framing" text in the narrative report**: "These findings represent statistical associations between pre-challenge metabolite profiles and disease resistance phenotypes. No causal claims are made."
 - Save the narrative report to `results/pathway_analysis.json` (key `narrative_report`).
 - **Dependency**: Requires T026b completion.
- [X] T027 [US3] **Execute** generation of `results/pathway_analysis.json` by merging results from T026a, T026b, T026c. Ensure the "framing" field is set to "associational" with the exact string: "These findings represent statistical associations between pre-challenge metabolite profiles and disease resistance phenotypes. No causal claims are made."
- [X] T028 [US3] **Execute** generation of visualization `results/plots/pathway_barplot.png` using `matplotlib` (via `seaborn`) based on data from `results/pathway_analysis.json`. **Input**: Read `results/pathway_analysis.json` (which includes the narrative from T026c). **Plot**: The most prominent pathways by frequency/importance. **Output**: Save as PNG with high resolution. Verify file existence and non-empty content.
 - **Dependency**: Requires T026c completion.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029a [P] **Update** `README.md` with execution instructions and `quickstart.md` validation. **MANDATORY FRAMING**: Include the exact text "These findings represent statistical associations between pre-challenge metabolite profiles and disease resistance phenotypes. No causal claims are made." in the 'Limitations' or 'Warning' section of the README to satisfy FR-011 for primary entry-point documentation. **Verification**: Confirm file exists and contains the mandatory framing text.
- [X] T029b [P] **Generate** `results/report_framing.md`, a human-readable narrative report. **Template**:
 ```markdown
 # Project Report: Predicting Plant Disease Resistance

 ## Key Findings
 [Summarize balanced accuracy, ROC-AUC, and significant metabolites from metrics.json and shap_analysis.json]

 ## Associational Framing
 These findings represent statistical associations between pre-challenge metabolite profiles and disease resistance phenotypes. No causal claims are made.

 ## Limitations
 [List sample size limitations, dataset heterogeneity, etc.]
 ```
 **Content**: Summarize key findings and explicitly state the associational nature of the results as required by FR-011. **Verification**: Confirm file exists and contains the mandatory framing text.
- [ ] T030a [P] **Configure** GitHub Actions workflow (`.github/workflows/ci.yml`) to define the pipeline environment, dependencies, and execution steps for the free-tier runner.
- [ ] T030b [P] **Configure** GitHub Actions workflow (`.github/workflows/ci.yml`) to define the pipeline environment, dependencies, and execution steps for the free-tier runner. **Verification**: Validate YAML syntax.
- [ ] T030c [P] **Trigger** the full pipeline integration test on GitHub Actions free-tier. **Action**: Manually trigger or schedule the workflow run. **Verification**: Confirm the run starts successfully.
- [ ] T030d [P] **Parse** logs for resource usage (verify ≤6h runtime, ≤7GB RAM) from the GitHub Actions run triggered in T030c. **Action**: Extract logs and verify constraints. **Verification**: Confirm constraints are met.
- [ ] T031a [P] **Fix flake8 errors** in `code/data/download.py` and `code/data/preprocess.py`. **Verification**: Run `flake8` and confirm 0 errors.
- [ ] T031b [P] **Apply black formatting** to `code/modeling/train.py` and `code/modeling/evaluate.py`. **Verification**: Run `black --check` and confirm 0 diffs.
- [ ] T031c [P] **Fix isort issues** in all Python files. **Verification**: Run `isort --check` and confirm 0 diffs.
- [X] T033 [P] Verify `state/artifact_hashes.yaml` tracks all data and model artifacts correctly
- [ ] T034 [P] **Implement** `code/utils/streaming.py` to handle large dataset processing via chunked iteration if `data/processed` exceeds RAM limits. **Logic**: Use `datasets.load_dataset(..., streaming=True)` or `pandas.read_csv(chunksize=...)` to process data in batches. **Fallback**: If streaming is not applicable, define a strict random sample size (e.g., 1000 rows) with a fixed seed and log the limitation. **Constraint**: NEVER fall back to synthetic data generation.
- [ ] T035 [P] **Add** error handling in `code/data/download.py` to ensure a `DataUnavailableError` is raised if the Metabolomics Workbench fetch fails, preventing any silent fallback to mock data. **Verification**: Unit test `test_download_failure_raises_error` confirms no synthetic data is generated on network failure.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Data IDs)**: No dependencies - can start immediately
- **Setup (Phase 1)**: Depends on Phase 0 completion (requires study IDs)
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (requires processed data from T017)
- **User Story 3 (P3)**: Depends on US2 completion (requires trained model and metrics)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (or data loaders before processing scripts)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (if dependencies allow)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for download.py in tests/unit/test_download.py"
Task: "Unit test for temporal validation in tests/unit/test_temporal.py"

# Launch all data scripts for User Story 1 together (if independent):
Task: "Implement download.py"
Task: "Implement harmonize_labels.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Data IDs
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently (data pipeline works)
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Modeling added)
4. Add User Story 3 → Test independently → Deploy/Demo (Interpretation added)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Modeling - can start once data schema is defined)
 - Developer C: User Story 3 (Interpretation - can start once model schema is defined)
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
- **Critical Constraint**: All tasks must run on CPU-only CI (limited cores, constrained RAM). No GPU/CUDA, no 8-bit/4-bit quantization, no deep learning. Use `scikit-learn` Random Forest only.
- **Data Integrity**: Do not fabricate data. Use real Metabolomics Workbench datasets. If data is unavailable, halt with "Data Unavailable" error.
- **Execution Order**: Ensure T012a/b (Generate Manifest) completes before T017. Ensure T017 (Generate processed data) completes BEFORE T020. Ensure T020 (Split) completes BEFORE T021a/T021b. Ensure T022 (VIF) completes BEFORE T024. Ensure T026a (Extraction) completes BEFORE T026b/T026c.
- **Deadlock Warning**: T017 depends on T012a/b. If T012a/b fails to produce `study_manifest.json`, T017 will fail. Verify T012a/b output before proceeding to T017.
- **Reproducibility**: All random seeds must be pinned in `code/config.py` and passed to all stochastic functions (permutation, splits, training).
- **Streaming Requirement**: If dataset size approaches memory limits, T034 must be executed to ensure chunked processing. Synthetic data is strictly prohibited.
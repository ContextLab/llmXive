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

- [ ] T012a [US1] **Implement** `code/research/verify_studies.py` to query the Metabolomics Workbench API for public studies containing 'plant disease' and 'metabolomics'. **Output**: A Python script that accepts no arguments and writes a list of valid Study IDs and their metadata to `data/raw/study_manifest.json`. **Verification**: Run script and verify `data/raw/study_manifest.json` exists and contains valid JSON with Study IDs.
- [ ] T012b [US1] **Download** raw intensity tables and phenotype metadata for the Study ID(s) from `study_manifest.json` to `data/raw/`. **Verify** sample metadata for 'pre-challenge', 'baseline', or timestamps prior to pathogen inoculation. **Hard Fail**: If temporal separation cannot be verified for a study, raise `TemporalVerificationError`. **Output**: Store raw files with SHA256 checksums in `data/raw/`. **Verification**: Confirm files exist and metadata contains required temporal fields.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create root project directories (`code/`, `data/`, `tests/`, `state/`, `results/`, `contracts/`).
- [ ] T001b [P] Create sub-directories (`data/raw`, `data/processed`, `data/intermediate`, `results/plots`).
- [ ] T001c [P] **Execute** verification that all directories created in T001a/T001b exist and are writable. Run `ls -R` and capture output to `state/directory_structure.txt`.
- [X] T002 [P] Initialize a Python project with pinned dependencies in `requirements.txt` (pandas, numpy, scikit-learn, statsmodels, requests, pytest, pyyaml, joblib, pydantic, sklearn-combat).
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `.pre-commit-config.yaml`. **Create the file with valid YAML syntax including hooks for black, flake8, and isort, and verify pre-commit hooks install successfully.**

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/constants.py` with random seeds (`random_state=42`), file paths, and hypothesis thresholds (Balanced Acc > 0.75). **Define `HOLD_OUT_FRACTION = 0.20` for T020. Define `MAX_DEPTH_GRID = [5, 10, 15]` for T020.**
- [X] T005 [P] Implement `code/utils/io.py` for checksumming (MD5/SHA256) and logging artifacts to `state/artifact_hashes.yaml`
- [ ] T006a [P] Create `contracts/metadata.schema.yaml` defining `MetaboliteProfile` and `ResistanceLabel` schemas. **Write the file with the following content:**
 ```yaml
 $schema: http://json-schema.org/draft-07/schema#
 type: object
 properties:
 MetaboliteProfile:
 type: object
 properties:
 sample_id: {type: string}
 InChIKey: {type: string}
 normalized_intensity: {type: number}
 study_id: {type: string}
 required: [sample_id, InChIKey, normalized_intensity]
 ResistanceLabel:
 type: object
 properties:
 germplasm_id: {type: string}
 assay_score: {type: number}
 measurement_method: {type: string}
 harmonized_score: {type: number}
 required: [germplasm_id, assay_score, harmonized_score]
 ```
- [ ] T006b [P] **Execute** validation of `contracts/metadata.schema.yaml` using `jsonschema` or `yamllint` to ensure schema validity. **Output**: `state/schema_validation_log.txt`.
- [ ] T007a [P] Create `contracts/output.schema.yaml` defining `metrics.json` and `shap_analysis.json` structures. **Write the file with the following content:**
 ```yaml
 $schema: http://json-schema.org/draft-07/schema#
 type: object
 properties:
 metrics:
 type: object
 properties:
 balanced_accuracy: {type: number}
 roc_auc: {type: number}
 permutation_p_value: {type: number}
 framing: {type: string}
 required: [balanced_accuracy, roc_auc, permutation_p_value, framing]
 shap_analysis:
 type: object
 properties:
 top_features:
 type: array
 items:
 type: object
 properties:
 feature_name: {type: string}
 shap_value: {type: number}
 required: [feature_name, shap_value]
 collinearity_vif:
 type: array
 items:
 type: object
 properties:
 feature_name: {type: string}
 vif_value: {type: number}
 required: [feature_name, vif_value]
 framing: {type: string}
 required: [top_features, framing]
 ```
- [ ] T007b [P] **Execute** validation of `contracts/output.schema.yaml` using `jsonschema` or `yamllint` to ensure schema validity. **Output**: `state/schema_validation_log.txt`.
- [ ] T008 [P] Setup `tests/unit/` structure and `pytest.ini` configuration
- [ ] T012c [P] **Implement** `code/utils/exceptions.py` defining `TemporalVerificationError` and `DataUnavailableError` classes. **Verification**: Import check in `code/data/validate_temporal.py` succeeds (stub file allowed for verification).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, normalize, align, and harmonize public metabolomics datasets from Metabolomics Workbench containing pre-challenge profiles and resistance metadata.

**Independent Test**: Verify data downloads (≥1 study), normalization outputs (log-transformed, missing >30% discarded), label harmonization (z-scoring), and batch-effect correction (ComBat) via script execution.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for `code/data/download.py` verifying Metabolomics Workbench HTTP fetch and file storage in `tests/unit/test_download.py`
- [X] T010 [P] [US1] Unit test for `code/data/validate_temporal.py` verifying timestamp checks in `tests/unit/test_temporal.py`
- [X] T011 [P] [US1] Integration test for full preprocessing pipeline (download → validate → preprocess → harmonize) in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data/validate_temporal.py` to verify FR-014: **Explicitly check metadata for 'pre-challenge', 'baseline', or timestamps prior to pathogen inoculation. If metadata lacks these, raise `TemporalVerificationError` and halt the pipeline for that study. Do NOT skip.**
- [X] T014 [US1] Implement `code/data/harmonize_labels.py` to encode resistance as binary/ordinal and apply z-scoring or stratification (FR-003, FR-013). **Ensure `binary_label` is passed to the trainer and `harmonized_score` is used ONLY for exploratory correlation. For binary labels, map directly to 0/1. For ordinal, apply z-scoring within study.**
- [X] T015 [US1] Implement `code/data/preprocess.py` to:
 - Log-transform intensities and discard features missing >30% (FR-002)
 - Align metabolites via InChIKey across studies
 - **Verify Study Count**: Parse `study_manifest.json` at runtime to count the number of studies. **Apply ComBat batch-effect correction ONLY if study count >= 2** (FR-004). If count < 2, skip ComBat and log a warning.
 - **Handle InChIKey alignment failures**: Log missing metabolites to `results/alignment_missing.json` and proceed with the intersection of aligned metabolites. **Flag if intersection < 10 metabolites.**
 - **Output**: Generate `data/processed/batch_corrected_matrix.csv`, `data/processed/labels.csv`, and `data/processed/preprocess_log.json` (recording discarded feature counts and ComBat status).
- [ ] T016 [US1] Add logging for data acquisition and preprocessing steps to `code/utils/io.py`
- [ ] T017 [US1] **Execute** `code/data/preprocess.py` using the command `python code/data/preprocess.py --study_ids data/raw/study_manifest.json --output data/processed/` to generate `data/processed/batch_corrected_matrix.csv`, `data/processed/labels.csv`, and `data/processed/preprocess_log.json`. **Verify file existence, non-empty content, and record SHA256 checksums in `state/artifact_hashes.yaml`. If files are missing or empty, raise an error and halt.**

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
 - **Conditional Split**:
   - **If N >= 50**: Split data into train/hold-out using stratified sampling on `binary_label` BEFORE any feature selection or scaling. Output `train_indices` and `holdout_indices` lists to `data/processed/split_indices.json`. Log the actual fraction reserved to `state/artifact_hashes.yaml`.
   - **If N < 50**: Skip hold-out set. Perform **Learning Curve Analysis** using full stratified 5-fold CV. Flag power limitation in the report.
 - Train Random Forest (n_estimators=500, max_depth=10) with Stratified k-fold CV (FR-005)
 - Perform GridSearchCV within the CV loop with `param_grid={'max_depth': [low, medium, high]}` (tunable up to 20, referencing T004 constants)
 - **Output**: Save `results/feature_importance_ranking.json` containing the top 10 metabolites ranked by mean decrease in impurity.
 - **Dependency**: Requires T017 completion.
- [X] T021a [US2] Implement `code/modeling/evaluate.py` (Correlation Analysis - Training Subset):
 - **Load `data/processed/split_indices.json`**. Filter the input matrix to **ONLY the training subset** using `train_indices` from T020. Justification: Restricted to training subset to prevent data leakage per FR-006 and Constitution Principle VII.
 - Compute pairwise correlations (metabolite vs. resistance) on the **training data only**.
 - **Apply Benjamini-Hochberg FDR correction (≤0.05) to p-values BEFORE filtering** using `statsmodels.stats.multitest.multipletests(method='fdr_bh')`. (FR-008, SC-002).
 - Filter for |r| > 0.4, p < 0.01 (using FDR-corrected p-values).
 - Output to `results/shap_analysis.json` (partial, key `training_correlations`).
 - **Note**: This task computes correlations on the training subset to prevent leakage. It does NOT satisfy SC-002 global context; see T021c for that.
 - **Dependency**: Requires T020 completion (for split indices).
- [X] T021c [US2] Implement `code/modeling/evaluate.py` (Correlation Analysis - Global Context):
 - **Load the full processed dataset** (excluding the hold-out set if N >= 50, or full set if N < 50).
 - Compute pairwise correlations (metabolite vs. resistance) on the **full dataset context** as required by SC-002 and FR-008.
 - **Apply Benjamini-Hochberg FDR correction (≤0.05) to p-values BEFORE filtering**.
 - Filter for |r| > 0.4, p < 0.01.
 - Output to `results/shap_analysis.json` (key `global_correlations`), merging with existing data from T021a.
 - **Dependency**: Requires T020 completion.
- [X] T021b [US2] Implement `code/modeling/evaluate.py` (Model Validation):
 - **Execute Learning Curve Analysis for ALL sample sizes.** If N < 50, generate the curve plot, flag power limitation in the report, and skip hold-out set. If N ≥ 50, generate the curve and proceed with hold-out set. **This satisfies SC-004 for all cases.**
 - Compute Balanced Accuracy, ROC-AUC, Precision-Recall on the independent hold-out set (SC-001) using `holdout_indices` from T020 (if N ≥ 50).
 - **Execute permutation testing on the trained model from T020 with exactly n_permutations=1000 to generate the null distribution and assess significance (FR-007, SC-003).**
 - Perform Sensitivity Analysis sweeping decision cutoffs over the specific thresholds **{0.01, 0.05, 0.1}** and report False Positive Rate (FPR) and False Negative Rate (FNR) at each threshold (FR-009, SC-005).
 - **Dependency**: Requires T020 and T021a completion.
- [ ] T022 [US2] **Execute** collinearity diagnostics (VIF calculation) for **top 10 metabolites** identified by feature importance in T020 using `statsmodels.stats.outliers_influence.variance_inflation_factor`. **Drop intercept column before VIF calculation. Input matrix must be (n_samples, n_features) without target column.**
 - **Fallback**: If VIF calculation fails (e.g., insufficient features, singular matrix) or returns empty, **log a warning** and save `data/intermediate/vif_scores.json` with an empty array or null values. **Do NOT halt the pipeline.**
 - Flag VIF > 5 and save results to `data/intermediate/vif_scores.json` (Mandatory per FR-012). Verify file existence.
 - **Dependency**: Requires T020 completion (for feature ranking).
- [ ] T024 [US2] **Execute** generation of `results/metrics.json`, `results/shap_analysis.json`, and `results/pathway_analysis.json` by aggregating results from T021a, T021b, and T022.
 - **Merge Logic**: Read VIF scores from `data/intermediate/vif_scores.json`. Merge correlation data from T021a (`training_correlations`) and T021c (`global_correlations`) into `results/shap_analysis.json`. If VIF data is missing or empty, set `collinearity_vif` to an empty array and log a warning.
 - Include the mandatory "framing" field set to "associational" with the exact string: "These results represent associations, not causation" in ALL result JSONs (metrics, shap, pathway) (FR-011).
 - Verify JSON validity and presence of required keys (balanced_accuracy, permutation_p_value, framing).
 - **Dependency**: Requires T020, T021a, T021b, T021c, and T022 completion.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Biological Interpretation and Pathway Mapping (Priority: P3)

**Goal**: Extract feature importances and map top metabolites to known pathways via KEGG/MetaCyc to assess biological plausibility.

**Independent Test**: Verify top metabolites are extracted, mapped to ≥1 pathway each, and documented with literature references.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Unit test for `code/modeling/interpret.py` verifying pathway mapping logic in `tests/unit/test_modeling.py`

### Implementation for User Story 3

- [ ] T026a [US3] **Implement** `code/modeling/interpret.py` (Extraction):
 - Extract top-ranked metabolites ranked by **mean decrease in impurity (feature_importances_)** from the trained Random Forest model (FR-010).
 - Save the list of top 10 metabolites to `results/top_metabolites.json`.
 - **Dependency**: Requires T020 completion.
- [ ] T026b [US3] **Implement** `code/modeling/interpret.py` (Mapping):
 - Read `results/top_metabolites.json`. Map metabolites to KEGG/MetaCyc pathways using the KEGG REST API (`compound/{inchikey}`) or InChIKey lookups. **Fallback**: If KEGG returns 404 or empty, try MetaCyc API.
 - Save pathway mapping results to `results/pathway_analysis.json` (partial, key `pathway_mappings`). Include fields: metabolite_id, pathway_name, database_source (KEGG/MetaCyc).
 - **Dependency**: Requires T026a completion.
- [ ] T026c [US3] **Implement** `code/modeling/interpret.py` (Reporting):
 - Read `results/pathway_analysis.json` and `results/top_metabolites.json`.
 - Generate interpretation report discussing biological plausibility (e.g., phytoalexins, phenolics).
 - **Explicitly include the mandatory "framing" text in the narrative report**: "These findings represent statistical associations between pre-challenge metabolite profiles and disease resistance phenotypes. No causal claims are made."
 - Save the narrative report to `results/pathway_analysis.json` (key `narrative_report`).
 - **Dependency**: Requires T026b completion.
- [ ] T027 [US3] **Execute** generation of `results/pathway_analysis.json` by merging results from T026a, T026b, T026c. Ensure the "framing" field is set to "associational" with the exact string: "These results represent associations, not causation" (FR-011).
- [ ] T028 [US3] **Execute** generation of visualization `results/plots/pathway_barplot.png` using `matplotlib` (via `seaborn`) based on data from `results/pathway_analysis.json`. **Plot the most prominent pathways by frequency/importance. Save as PNG with high resolution. Verify file existence and non-empty content.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029a [P] Update `README.md` with execution instructions and `quickstart.md` validation
- [ ] T029b [P] **Generate** `results/report_framing.md`, a human-readable narrative report that explicitly converts the "framing" JSON data from `results/metrics.json`, `results/shap_analysis.json`, and `results/pathway_analysis.json` into a cohesive text document. **Content**: Summarize key findings and explicitly state the associational nature of the results as required by FR-011. **Verification**: Confirm file exists and contains the mandatory framing text.
- [ ] T030a [P] **Configure** GitHub Actions workflow (`.github/workflows/ci.yml`) to define the pipeline environment, dependencies, and execution steps for the free-tier runner.
- [ ] T030b [P] **Execute** the full pipeline integration test on GitHub Actions free-tier (verify ≤6h runtime, ≤7GB RAM) using the configured workflow.
- [ ] T031 [P] Code cleanup and refactoring based on linting feedback
- [ ] T033 [P] Verify `state/artifact_hashes.yaml` tracks all data and model artifacts correctly

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
- **Execution Order**: Ensure T012 (Verify IDs) completes before T013/T014/T015. Ensure T017 (Generate processed data) completes before T020. Ensure T021a (Training Correlations) runs after T020 (Split) but can run in parallel with T020 (Train) logic where possible. Ensure T022 (VIF), T024 (Logging), and T026 (Interpret) are executed in sequence to produce final artifacts.
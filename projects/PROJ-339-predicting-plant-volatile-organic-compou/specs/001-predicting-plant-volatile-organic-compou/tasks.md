# Tasks: Predicting Plant VOC Emission Profiles from Genomic and Environmental Data

**Input**: Design documents from `/specs/001-predict-voc-profiles/`
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

- [X] T001a [P] Create project directories: `code/`, `tests/`, `data/raw/`, `data/processed/`, `data/results/`, `data/models/`, `data/reference/`, `specs/`
- [X] T001b [P] Create `requirements.txt` with dependencies: `scikit-learn`, `pandas`, `numpy`, `shap`, `requests`, `biopython`, `pyyaml`, `memory-profiler`
- [X] T001c [P] Create `.gitignore` to exclude `data/`, `__pycache__`, `*.pyc`, `*.pkl`
- [X] T001d [P] Create `.env.example` with placeholder keys for data paths and seeds

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils/hashing.py` for content checksumming of artifacts
- [X] T005a [P] Create `code/generators/synthetic_data.py` as the canonical source for mock data (checksummed).
 - **Function**: `generate_synthetic_arabidopsis(n_samples=100, seed=42)`
 - **Schema Requirements**: Must output a DataFrame with columns: `sample_id`, `gene_expression` (dict or wide format), `temperature` (float, Normal dist), `light_intensity` (float, Uniform dist), `co2_level` (float, Normal dist), `treatment` (categorical), `voc_concentration` (float).
 - **Output**: `data/raw/synthetic_arabidopsis_v1.csv`
 - **Note**: This generator is for local unit testing and development validation ONLY. It MUST NOT be used as a fallback for real data ingestion in the production pipeline.
- [X] T005b [P] Create `data/reference/terpene_synthase_ids.csv` defining the canonical list of known terpene synthase gene families (e.g., TPS-a, TPS-b subfamilies) with gene IDs and descriptions. This is the reference for FR-008.
- [X] T006 [P] Implement `code/utils/validation.py` for replicate checks and data type validation
- [X] T007 [P] Create base data schemas in `specs/001-predict-voc-profiles/contracts/dataset.schema.yaml` defining Sample, GenomicFeature, EnvironmentalFeature, and VOCProfile entities.
 - **Schema Requirements**: Must explicitly include fields: `temperature` (float), `light_intensity` (float), `co2_level` (float), `treatment` (string), `sample_id` (string).
- [X] T008 [P] Configure environment variable management for data paths and seeds in `code/utils/config.py`.
- [X] T009 [P] Implement `code/utils/imputation.py` for median/KNN strategies (to be used ONLY inside CV loop).
- [X] T009a [P] Implement `code/utils/imputation.py` function `fit_impute_cv(train_df, val_df)` that fits imputation on `train_df` and applies to both. (Refactored from T022a).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest paired RNA-seq and VOC data (REAL ONLY), normalize to TPM, handle missing values, and merge by exact sample pairing.

**Independent Test**: The pipeline executes on a sample subset (or synthetic data for local testing ONLY), producing a single merged CSV with ≥50 rows, normalized transcript counts, and valid VOC targets.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data ingestion output schema in `tests/test_ingest.py`
- [X] T011 [US1] Integration test for merge logic in `tests/test_merge.py` (Defines contract for T015c; no dependency on T015c completion)

### Implementation for User Story 1

- [X] T012 [US1] Orchestrate data ingestion: Run T012a. If T012a returns zero valid paired samples, the pipeline MUST FAIL HARD with a descriptive error. Do NOT trigger synthetic data generation. The existence of real data is a strict requirement of FR-001. (Depends on T012a; T005a is for local testing ONLY, not pipeline fallback).
- [X] T012a [US1] Implement `code/01_ingest.py` function `fetch_ncbi_data()`.
 - **Logic**: Query NCBI GEO and Metabolomics Workbench for *Arabidopsis thaliana* stress studies using search strings "Arabidopsis thaliana" AND ("VOC" OR "volatile") AND "RNA-seq" AND "stress".
 - **Output**: `data/raw/ncbi_query_results.json`. **Schema**: A list of objects: `[{"accession_id": "GSE...", "study_type": "RNA-seq", "sample_count": 10, "metadata_url": "..." },...]`.
 - **Return**: List of valid accession IDs or empty list if no results. If the list is empty, raise a `DataNotFoundError` to halt the pipeline. (No dependency on T005a; T012 handles the failure path).
- [X] T012b [US1] Implement `code/01_ingest.py` function `log_real_data_status()`.
 - **Logic**: Record the status of real data acquisition. If real data is found, log success. If T012a fails, log the error and the reason for pipeline termination. Output: `data/results/compliance_log.json`. (Depends on T012 execution path).
- [X] T015a [US1] Implement `code/02_merge.py` function `filter_environmental(data)` to exclude samples missing 'temperature' OR 'light_intensity' ONLY (FR-012).
 - **Output**: `data/raw/filtered_env_data.csv`. (Depends on T012 completion).
 - **Constraint**: Do NOT filter on 'CO2_level' in this step. 'CO2_level' is optional per FR-012.
- [X] T015b [US1] Implement `code/02_merge.py` function `filter_replicates(data)` to exclude conditions with <3 biological replicates (FR-011).
 - **Output**: `data/raw/filtered_replicates_data.csv`. (Depends on T015a completion).
- [X] T015c [US1] Implement `code/02_merge.py` function `join_data(genomic_df, voc_df)` to join genomic and VOC data ONLY on exact sample ID match.
 - **Output**: `data/raw/joined_data.csv`. (Depends on T015b completion).
- [X] T015d [US1] (OPTIONAL) Implement `code/02_merge.py` function `filter_co2(data)` to exclude samples missing 'CO2_level' if explicitly requested via config.
 - **Output**: `data/raw/filtered_co2_data.csv`. (Depends on T015c; NOT required for FR-012. Default is to SKIP this filter).
- [X] T014 [US1] Implement TPM normalization in `code/01_ingest.py` for the filtered dataset.
 - **Note**: This task ONLY normalizes transcript counts to TPM. It does NOT perform imputation. Missing genomic values are preserved as NaN for CV-internal imputation.
 - **Output**: `data/processed/normalized_data.csv`. (Depends on T015c completion; T015d is optional).
- [X] T016a [US1] Implement aggregation of gene expression into gene-level features (no aggregation) for interpretation.
 - **Output**: `data/processed/gene_level_features.csv`. (Depends on T014 completion; used for T031).
- [X] T016b [US1] Implement aggregation of gene expression into pathway-level features (e.g., TPS families) to reduce dimensionality for the model.
 - **Output**: `data/processed/pathway_aggregated_features.csv`. (Depends on T014 completion).
- [ ] T017 [US1] Ensure output CSV `data/processed/merged_dataset.csv` has correct types and no non-numeric entries. Generate validation report at `data/results/data_validation_report.json`. (Depends on T016b completion).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Model Training and Evaluation (Priority: P2)

**Goal**: Train a Random Forest Regressor on CPU, perform Nested k-Fold CV, and report R²/RMSE with associational disclaimers.

**Independent Test**: The training script runs on CPU within 6 hours, outputs `data/results/model_metrics.json` with R², RMSE, and a trained model artifact.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for model metrics JSON schema in `tests/test_model.py`
- [X] T022a [US2] Integration test for cross-validation loop in `tests/test_model.py` (Depends on T021 completion; verifies imputation leakage prevention).

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/03_train.py` using scikit-learn Random Forest Regressor (CPU only, no GPU/quantization).
- [X] T021 [US2] Implement **Nested k-Fold Cross-Validation** (inner loop for tuning, outer loop for evaluation) in `code/03_train.py` as the primary strategy for FR-005.
 - **Logic**: Load `data/processed/merged_dataset.csv`. Perform outer CV split. For each training fold, call T009a to impute. Fit model.
 - **Output**: Per-fold model artifacts and per-fold feature importance rankings (top 20) saved to `data/results/cv_fold_rankings.json`. (Depends on T020, T017, T009a).
- [ ] T023 [US2] Calculate and report R² and RMSE metrics in `data/results/model_metrics.json`. (Depends on T021 completion).
- [X] T024 [US2] Save trained model artifact to `data/models/random_forest.pkl`. (Depends on T020 completion).
- [ ] T025 [US2] Inject associational disclaimer ("Findings are associational due to observational data") into `data/results/model_metrics.json` and `data/results/interpretation_report.json`. Verify via `tests/test_model.py`. (Depends on T024 completion).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Biological Interpretation (Priority: P3)

**Goal**: Calculate permutation importance, generate SHAP plots, and validate against known gene families with statistical corrections.

**Independent Test**: The analysis script produces a ranked feature list, SHAP summary plot, and overlap statistics for terpene synthase families.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Contract test for interpretation output schema in `tests/test_interpret.py`
- [X] T027 [US3] Integration test for SHAP generation in `tests/test_interpret.py` (Depends on T029 completion)

### Implementation for User Story 3

- [X] T028 [US3] Implement permutation feature importance calculation in `code/04_interpret.py`, generating raw importance scores. (Depends on T024 completion).
- [X] T028a [US3] Implement `code/04_interpret.py` function `generate_permutation_pvalues(model, data)` to generate p-values for feature importance via permutation testing (FR-010). If permutation testing is not feasible, use bootstrap resampling to generate null distribution.
 - **Output**: `data/results/feature_importance_pvalues_raw.json`. (Depends on T024 completion).
- [X] T029 [US3] Generate SHAP value visualizations and save to `data/results/shap_summary.png`. (Depends on T024 completion).
- [X] T030 [US3] Apply Benjamini-Hochberg correction to p-values from T028a (permutation/bootstrap test) and save corrected values to `data/results/feature_importance_pvalues_corrected.json` (FR-010). (Depends on T028a completion).
- [X] T031 [US3] Implement overlap statistics calculation against known terpene synthase gene families (FR-008).
 - **Logic**: Load `data/reference/terpene_synthase_ids.csv` (from T005b) and `data/processed/gene_level_features.csv` (from T016a). Map the model's top pathway features (from T021) back to their constituent genes using the pathway definition. Calculate the proportion of these specific genes overlapping with the known list.
 - **Output**: `data/results/overlap_statistics.json`. (Depends on T028, T016a, T005b).
- [X] T032 [US3] Generate final JSON report in `data/results/interpretation_report.json` with disclaimers and FDR values.
- [X] T033 [US3] Validate stability of feature importance rankings across CV folds.
 - **Logic**: Load per-fold rankings from `data/results/cv_fold_rankings.json` (T021 output). Calculate **Kendall's Tau correlation** between all pairs of fold rankings for ALL features with non-zero importance (or top N where N = min(50, total_features)). Compute the mean Tau.
 - **Output**: `data/results/stability_metrics.json` containing `mean_tau` and `std_tau`. (Depends on T021, T024).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034a [P] Documentation updates in `quickstart.md` (Add full pipeline execution command and synthetic data generation command for local testing).
- [X] T034b [P] Documentation updates in `research.md` (Add data availability status and real data acquisition log entry).
- [X] T035 Run `ruff check` and `black --check` on `code/`, save output to `data/results/lint_report.txt`.
- [X] T036 Run `memory_profiler` on the full pipeline, record peak RAM usage in `data/results/perf_metrics.json` (ensure <6GB).
- [X] T037 [P] Additional unit tests for edge cases (missing data, <50 samples) in `tests/unit/`
- [X] T038 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

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
Task: "Contract test for data ingestion output schema in tests/test_ingest.py"
Task: "Integration test for merge logic in tests/test_merge.py"

# Launch all models for User Story 1 together:
Task: "Implement code/01_ingest.py"
Task: "Implement code/utils/imputation.py"
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
- **Critical Constraint**: All data tasks must use real URLs; synthetic data is ONLY for local unit testing and MUST NOT be used as a fallback for the production pipeline.
- **Critical Constraint**: All model training must be CPU-only; no GPU, no 8-bit/4-bit quantization.
- **Critical Constraint**: Imputation MUST be performed inside the CV loop (T009a) to prevent leakage. T014 must NOT impute.
- **Critical Constraint**: T015a MUST filter raw data for missing 'temperature' and 'light intensity' ONLY (FR-012). CO2 filtering is optional (T015d).
- **Critical Constraint**: T016a (gene-level) must be used for T031 overlap calculation; T016b (pathway) is for modeling only.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T039 Reconcile run-book vs implementation for `code/main.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/main.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.

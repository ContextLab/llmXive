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

- [ ] T007a [P] [Foundational] Implement `specs/001-predict-voc-profiles/contracts/dataset.schema.yaml`. Define schema objects: 'Sample', 'GenomicFeature', 'EnvironmentalFeature', 'VOCProfile'. **Verification**: Validate schema against a dummy CSV using `pydantic` or `jsonschema`.
- [X] T008a [P] [Foundational] Configure environment variable management by creating `code/utils/config.py` and defining variables: `DATA_PATH`, `RANDOM_SEED`, `MODEL_PATH`. **Verification**: Script loads `.env` and raises error if missing keys.
- [X] T004 [Foundational] Implement `code/utils/hashing.py` for content checksumming of artifacts. **Verification**: Hash of a test file matches expected value.
- [ ] T005 [Foundational] Implement `code/generators/synthetic_data.py` as the canonical source for mock data (checksummed). Must output `data/raw/synthetic_arabidopsis_v1.csv`. **Dependency**: T007a (schema), T008a (env config). **Verification**: Output matches schema defined in T007a.
- [ ] T005b [Foundational] Implement schema validation logic in `code/generators/synthetic_data.py` or a helper script to verify that the synthetic data schema matches the real-world schema of NCBI GEO and Metabolomics Workbench (as defined in T007a). **Verification**: Script runs against synthetic output and a reference schema loaded from `data/reference/real_world_schema.json`, passing only if structures align.
- [X] T006 [P] [Foundational] Implement `code/utils/validation.py` for replicate checks and data type validation. **Verification**: Unit tests for `check_replicates` and `validate_types`.
- [X] T009a [Foundational] Implement `code/utils/imputation.py` with **median imputation as the default strategy**. **Verification**: Unit tests for median imputation logic on dummy data. **Note**: Median is the defined strategy for the final pipeline run per FR-002.
- [X] T009b [Foundational] Implement `code/utils/imputation.py` with **KNN imputation as an optional strategy**. **Verification**: Unit tests for KNN imputation logic on dummy data.

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

- [ ] T012 [US1] Implement `code/01_ingest.py` to query NCBI GEO and Metabolomics Workbench for *Arabidopsis thaliana* stress studies using search strings "Arabidopsis thaliana" AND ("VOC" OR "volatile") AND "RNA-seq" AND "stress". Log results to `data/raw/query_log.json`. **Primary Deliverable**: Ingest real paired data if available. **Critical Constraint**: If the query returns fewer than 50 valid paired samples, the script MUST **automatically invoke** `code/generators/synthetic_data.py` (T005) to generate synthetic data. Do NOT raise a `DataUnavailableError` or require manual flags. Synthetic data generation is automatic upon real data failure. (Depends on T007a, T008a, T005, T005b)
- [X] T015b [US1] Implement environmental metadata filter in `code/02_merge.py`. **Logic**: **Exclude samples where ANY of the following are missing**: 'temperature', 'light intensity', OR 'CO2 level' (FR-012). (Depends on T009a)
- [X] T015a [US1] Implement replicate check logic in `code/02_merge.py`. **Logic**: Filter out experimental conditions with <3 biological replicates (FR-011). (Depends on T015b)
- [X] T014 [US1] Implement TPM normalization and missing value imputation in `code/01_ingest.py`. **Note**: Imputation applies to non-critical fields; critical environmental fields (temp, light, CO2) are handled by T015b exclusion logic. Uses default strategy from T009a. (Depends on T015a)
- [ ] T017a [US1] Implement validation logic in `code/02_merge.py` to enforce types and generate `data/results/data_validation_report.json`. Ensure output CSV `data/processed/merged_dataset.csv` has correct types and no non-numeric entries. (Depends on T014)
- [ ] T017b [US1] [Remediation] Explicitly generate `data/results/data_validation_report.json` with keys: `total_samples`, `excluded_samples`, `missing_values_imputed`, `validation_status`. **Verification**: File exists and contains valid JSON. (Depends on T017a)
- [ ] T016a [US1] (Optional) Implement aggregation of gene expression into pathway-level features (e.g., mean TPM per TPS family) to reduce dimensionality. Output column naming: `tps_family_X_mean`. **Condition**: Only if raw feature count > 100. (Depends on T017a)
- [ ] T016b [US1] [Remediation] Implement raw feature overlap calculation against known terpene synthase families (FR-008) using raw features. **Source**: Load reference list from `data/reference/tps_families.csv`. **Metric**: Calculate Jaccard index of top-ranked features vs reference list. (Depends on T017a)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Model Training and Evaluation (Priority: P2)

**Goal**: Train a Random Forest Regressor on CPU, perform Nested k-Fold CV, and report R²/RMSE with associational disclaimers.

**Independent Test**: The training script runs on CPU within 6 hours, outputs `data/results/model_metrics.json` with R², RMSE, and a trained model artifact.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for model metrics JSON schema in `tests/test_model.py`
- [X] T019 [US2] Integration test for cross-validation loop in `tests/test_model.py` (Depends on T021 completion)

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/03_train.py` using scikit-learn Random Forest Regressor (CPU only, no GPU/quantization). (Depends on T017a)
- [ ] T022a [US2] [Remediation] Refactor `code/03_train.py` to use `sklearn.pipeline.Pipeline` with `ColumnTransformer` for imputation. **Logic**: Ensure imputation parameters are fitted ONLY on training folds. (Depends on T020)
- [ ] T022b [US2] [Remediation] Implement `ColumnTransformer` configuration in T022a to handle numeric and categorical columns separately. (Depends on T022a)
- [ ] T022c [US2] [Remediation] Implement nested cross-validation loop structure in `code/03_train.py` (inner loop for tuning, outer for evaluation) to prevent data leakage. (Depends on T022b)
- [ ] T021 [US2] Implement **Nested k-Fold Cross-Validation** (inner loop for tuning, outer loop for evaluation) in `code/03_train.py` as the primary strategy for FR-005. (Depends on T022c)
- [ ] T023a [US2] Calculate R² and RMSE metrics in `code/03_train.py`. (Depends on T021)
- [ ] T023b [US2] [Remediation] Write metrics to `data/results/model_metrics.json` with keys: `r2_score`, `rmse`, `baseline_r2`. **Verification**: File exists and contains valid JSON. (Depends on T023a)
- [ ] T024a [US2] [Remediation] Save trained model artifact to `data/models/random_forest.pkl`. **Verification**: File exists and can be loaded. (Depends on T021)
- [ ] T025a [US2] [Remediation] Inject associational disclaimer ("Findings are associational due to observational data") into **all** JSON outputs: `model_metrics.json`, `interpretation_report.json`, `data_validation_report.json`, and `stability_metrics.json`. Verify via `tests/test_model.py`. (Depends on T024a, T017b, T033a)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Biological Interpretation (Priority: P3)

**Goal**: Calculate permutation importance, generate SHAP plots, and validate against known gene families with statistical corrections.

**Independent Test**: The analysis script produces a ranked feature list, SHAP summary plot, and overlap statistics for terpene synthase families.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Contract test for interpretation output schema in `tests/test_interpret.py`
- [X] T027 [US3] Integration test for SHAP generation in `tests/test_interpret.py` (Depends on T028a completion)

### Implementation for User Story 3

- [ ] T028a [US3] Implement permutation feature importance calculation in `code/_interpret.py` using 1000 permutations to generate p-values. Output file: `data/results/feature_importance_pvalues.json`. (Depends on T024a)
- [ ] T030 [US3] Apply Benjamini-Hochberg correction to p-values from T028a (permutation test) and **calculate the resulting False Discovery Rate (FDR) value**. Save corrected values and FDR metric to `data/results/feature_importance_pvalues_corrected.json` (FR-010, SC-005). **Deliverable**: Must include a key `fdr_threshold` in the output JSON representing the calculated FDR value. (Depends on T028a)
- [ ] T031a [US3] [Remediation] Implement overlap statistics calculation against known terpene synthase gene families (FR-008) using raw features. **Source**: Load reference list from `data/reference/tps_families.csv`. **Metric**: Calculate Jaccard index of top-ranked features vs reference list. (Depends on T024a)
- [ ] T031b [US3] [Remediation] Explicitly generate `data/results/overlap_statistics.json` with keys: `top_features`, `reference_features`, `jaccard_index`, `p_value`. **Verification**: File exists and contains valid JSON. (Depends on T031a)
- [ ] T029 [US3] Generate SHAP value visualizations and save to `data/results/shap_summary.png`. (Depends on T024a)
- [ ] T033a [US3] [Remediation] Validate stability of feature importance rankings across CV folds by generating `data/results/stability_metrics.json`. **Metric**: **Spearman correlation of ranks** across 5 folds. **Verification**: File exists and contains valid JSON. (Depends on T024a)
- [ ] T032a [US3] [Remediation] Generate final JSON report in `code/05_report.py` at `data/results/interpretation_report.json`. **Keys**: `disclaimer`, `fdr_values`, `top_features`, `overlap_stats`, `shap_summary_path`, `stability_metrics_path`. **Verification**: File exists and contains valid JSON. (Depends on T030, T031b, T029, T033a)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034a [P] Update `quickstart.md` with synthetic data generation command and full pipeline execution command.
- [ ] T034b [P] Update `research.md` with data availability status.
- [ ] T035 Run `ruff check` and `black --check` on `code/`, save output to `data/results/lint_report.txt`.
- [ ] T036 Create `code/utils/perf_monitor.py` to wrap the pipeline execution, capture peak RAM, and write to `data/results/perf_metrics.json` (ensure <6GB).
- [ ] T037 [P] Additional unit tests for edge cases in `tests/unit/`. **Functions**: `test_missing_data_handling` (asserts exclusion), `test_insufficient_samples` (asserts warning).
- [ ] T038 Run `bash quickstart.sh` and verify exit code 0 and all artifacts generated.

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
- **Critical Constraint**: All data tasks must use real URLs or the canonical synthetic generator; no fake/hardcoded data values.
- **Critical Constraint**: All model training must be CPU-only; no GPU, no 8-bit/4-bit quantization.
- **Critical Constraint**: Data ingestion MUST automatically fallback to synthetic data if real data is missing; no manual flags or silent failures.
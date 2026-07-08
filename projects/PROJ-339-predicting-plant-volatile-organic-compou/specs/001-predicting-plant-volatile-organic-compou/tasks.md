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

- [ ] T001a [P] Create project directories: `code/`, `tests/`, `data/raw/`, `data/processed/`, `data/results/`, `data/models/`, `specs/`
- [ ] T001b [P] Create `requirements.txt` with dependencies: `scikit-learn`, `pandas`, `numpy`, `shap`, `requests`, `biopython`, `pyyaml`, `memory-profiler`
- [ ] T001c [P] Create `.gitignore` to exclude `data/`, `__pycache__`, `*.pyc`, `*.pkl`
- [ ] T001d [P] Create `.env.example` with placeholder keys for data paths and seeds

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/utils/hashing.py` for content checksumming of artifacts
- [ ] T005 [P] Create `code/generators/synthetic_data.py` as the canonical source for mock data (checksummed). Must output `data/raw/synthetic_arabidopsis_v1.csv`.
- [ ] T006 [P] Implement `code/utils/validation.py` for replicate checks and data type validation
- [ ] T007 Create base data schemas in `specs/001-predict-voc-profiles/contracts/dataset.schema.yaml`
- [ ] T008 Configure environment variable management for data paths and seeds
- [ ] T009 Implement `code/utils/imputation.py` for median/KNN strategies

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest paired RNA-seq and VOC data (real or synthetic), normalize to TPM, handle missing values, and merge by exact sample pairing.

**Independent Test**: The pipeline executes on a sample subset (or synthetic data), producing a single merged CSV with ≥50 rows, normalized transcript counts, and valid VOC targets.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for data ingestion output schema in `tests/test_ingest.py`
- [ ] T011 [US1] Integration test for merge logic in `tests/test_merge.py` (Defines contract for T015; no dependency on T015 completion)

### Implementation for User Story 1

- [ ] T012 [US1] Query NCBI GEO and Metabolomics Workbench for *Arabidopsis thaliana* stress studies using search strings "Arabidopsis thaliana" AND ("VOC" OR "volatile") AND "RNA-seq" AND "stress". Log results to `data/raw/query_log.json`. **If** `data/raw/query_log.json` is empty or contains no valid paired samples, immediately trigger T005 to generate synthetic data.
- [ ] T014 [US1] Implement TPM normalization and missing value imputation in `code/01_ingest.py`. **Note**: Imputation applies to non-critical fields; critical environmental fields (temp, light) are handled by T015 exclusion logic. (Depends on T012/T005 completion)
- [ ] T015 [US1] Implement `code/02_merge.py` to join genomic and VOC data ONLY on exact sample ID match. **Logic**: 1) Exclude conditions with <3 biological replicates (FR-011). 2) Exclude samples missing continuous environmental metadata for 'temperature' or 'light intensity' (FR-012). 3) Merge remaining data. (Depends on T014 completion; excludes data before imputation obscures missingness)
- [ ] T016 [US1] Implement aggregation of gene expression into pathway-level features (e.g., TPS families) to reduce dimensionality for the model. (Depends on T015 completion)
- [ ] T017 [US1] Ensure output CSV `data/processed/merged_dataset.csv` has correct types and no non-numeric entries. Generate validation report at `data/results/data_validation_report.json`. (Depends on T016 completion)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Model Training and Evaluation (Priority: P2)

**Goal**: Train a Random Forest Regressor on CPU, perform Nested k-Fold CV, and report R²/RMSE with associational disclaimers.

**Independent Test**: The training script runs on CPU within 6 hours, outputs `data/results/model_metrics.json` with R², RMSE, and a trained model artifact.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for model metrics JSON schema in `tests/test_model.py`
- [ ] T019 [US2] Integration test for cross-validation loop in `tests/test_model.py` (Depends on T024 completion)

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/03_train.py` using scikit-learn Random Forest Regressor (CPU only, no GPU/quantization).
- [ ] T021 [US2] Implement **Nested k-Fold Cross-Validation** (inner loop for tuning, outer loop for evaluation) in `code/03_train.py` as the primary strategy for FR-005.
- [ ] T022 [US2] Ensure imputation parameters are fitted ONLY on training folds to prevent leakage. (Depends on T020, T021)
- [ ] T023 [US2] Calculate and report R² and RMSE metrics in `data/results/model_metrics.json`.
- [ ] T024 [US2] Save trained model artifact to `data/models/random_forest.pkl`. (Depends on T020 completion)
- [ ] T025 [US2] Inject associational disclaimer ("Findings are associational due to observational data") into `data/results/model_metrics.json` and `data/results/interpretation_report.json`. Verify via `tests/test_model.py`. (Depends on T024 completion)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Biological Interpretation (Priority: P3)

**Goal**: Calculate permutation importance, generate SHAP plots, and validate against known gene families with statistical corrections.

**Independent Test**: The analysis script produces a ranked feature list, SHAP summary plot, and overlap statistics for terpene synthase families.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Contract test for interpretation output schema in `tests/test_interpret.py`
- [ ] T027 [US3] Integration test for SHAP generation in `tests/test_interpret.py` (Depends on T033 completion)

### Implementation for User Story 3

- [ ] T028 [US3] Implement permutation feature importance calculation in `code/04_interpret.py`, generating p-values. (Depends on T024 completion)
- [ ] T029 [US3] Generate SHAP value visualizations and save to `data/results/shap_summary.png`. (Depends on T024 completion)
- [ ] T030 [US3] Apply Benjamini-Hochberg correction to p-values from T028 (permutation test) and save corrected values to `data/results/feature_importance_pvalues.json` (FR-010).
- [ ] T031 [US3] Implement overlap statistics calculation against known terpene synthase gene families (FR-008) using the aggregated pathway features from T016.
- [ ] T032 [US3] Generate final JSON report in `data/results/interpretation_report.json` with disclaimers and FDR values.
- [ ] T033 [US3] Validate stability of feature importance rankings across CV folds by generating `data/results/stability_metrics.json` containing the standard deviation of feature ranks (SC-004). (Depends on T024 completion)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `quickstart.md` (include synthetic data generation command and full pipeline execution command) and `research.md` (update with data availability status).
- [ ] T035 Run `ruff check` and `black --check` on `code/`, save output to `data/results/lint_report.txt`.
- [ ] T036 Run `memory_profiler` on the full pipeline, record peak RAM usage in `data/results/perf_metrics.json` (ensure <6GB).
- [ ] T037 [P] Additional unit tests for edge cases (missing data, <50 samples) in `tests/unit/`
- [ ] T038 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
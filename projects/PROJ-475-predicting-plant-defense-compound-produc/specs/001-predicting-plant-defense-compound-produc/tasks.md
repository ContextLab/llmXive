# Tasks: Predicting Plant Defense Compound Production from Public Genomic and Environmental Data

**Input**: Design documents from `/specs/001-predicting-plant-defense-compounds/`
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

- [X] T001 Create project structure per implementation plan (`code/`, `data/raw/`, `data/processed/`, `specs/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (scikit-learn, pandas, numpy, cyvcf2, requests, pyyaml, scipy, pytest)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `data/schema/manifest.schema.yaml` schema definition and implement checksum utility function `code/utils/io.py` (function `compute_checksum`)
- [X] T005 [P] Implement configuration loader in `code/config.py` (seeds, paths, hyperparameters, verified URLs)
- [X] T006 [P] Setup base logging infrastructure in `code/utils/logging.py`
- [X] T007 Create `code/data/__init__.py` and `code/models/__init__.py` package structures
- [X] T008 Implement disk space checker in `code/utils/io.py` (FR-001): function `check_disk_space(estimated_size)` MUST raise `DiskSpaceError` if available space < 1.5 * estimated_size
- [X] T009 [US1] Implement `code/data/mock_generator.py` to generate deterministic mock genomic, environmental, and compound data for CI runs. **Constraint**: MUST be invoked ONLY if verified URLs are missing or unreachable. **Priority**: Real data fetch is the primary path; mock generation is a strict fallback ONLY when real sources are unreachable. **Verification**: Run ingestion script with no API keys set; verify mock data is generated and no network calls are made. **Output**: `data/raw/mock_genomic.vcf`, `data/raw/mock_env.csv`, `data/raw/mock_compounds.json`. **Provenance**: MUST update `data/manifest.yaml` with generator script path and seed.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Validation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Assemble a unified dataset by downloading/generating genomic, environmental, and compound data, then validate completeness.

**Independent Test**: Run ingestion script against a small, known subset; verify output CSV has non-null `population_id`, `env_id`, `compound_id` and matches schema.

### Implementation for User Story 1

- [ ] T010 [US1] Implement `code/data/ingestion.py` to fetch Genomic VCF data. **Logic**: Check `config.verified_urls['genomic']`. If valid URL exists AND is in 'Verified datasets' block, download VCF to `data/raw/genomic.vcf`; else, invoke T009 mock generator to write `data/raw/mock_genomic.vcf`. **Pre-check**: Call T008 to verify disk space > 1.5 * estimated_size. **Verification**: Verify `data/raw/genomic.vcf` (or mock) exists and passes VCF header validation. **Provenance**: Update `data/manifest.yaml` with source path. <!-- FAILED: unspecified -->
- [ ] T011 [US1] Implement `code/data/ingestion.py` to fetch Environmental CSV data. **Logic**: Check `config.verified_urls['env']`. If valid URL exists AND is in 'Verified datasets' block, download CSV to `data/raw/env_data.csv`; else, invoke T009 mock generator to write `data/raw/mock_env.csv`. **Verification**: Verify `data/raw/env_data.csv` (or mock) exists and contains required columns: `population_id`, `lat`, `lon`, `temp`, `precip`, `ph`. **Provenance**: Update `data/manifest.yaml`.
- [ ] T012 [US1] Implement `code/data/ingestion.py` to fetch Defense Compound JSON data. **Logic**: Check `config.verified_urls['compound']`. If valid URL exists AND is in 'Verified datasets' block, download JSON to `data/raw/compound_data.json`; else, invoke T009 mock generator to write `data/raw/mock_compounds.json`. **Verification**: Verify `data/raw/compound_data.json` (or mock) exists and contains required keys: `population_id`, `compound_name`, `concentration`. **Provenance**: Update `data/manifest.yaml`.
- [ ] T013 [US1] Implement `code/data/validation.py` to merge the three raw modalities (`data/raw/genomic.vcf`, `data/raw/env_data.csv`, `data/raw/compound_data.json`) into a single intermediate file. **Input**: data/raw/genomic.vcf (T010), data/raw/env_data.csv (T011), data/raw/compound_data.json (T012). **Logic**: Perform inner join on `population_id`. Preserve `source_study` column from compound data. **Output**: `data/processed/merged_raw.csv`. Log populations missing any modality to `logs/exclusions.log`.
- [ ] T014 [US1] Implement `code/data/validation.py` to calculate retention percentage and enforce SC-001. **Input**: `data/processed/merged_raw.csv` (output of T013) and the original list of population IDs (N_initial). **Logic**: Calculate retention = (N_final / N_initial) * 100 where N_final is row count in `merged_raw.csv`. **Constraint**: Threshold MUST be 80%. **Action**: If retention < 80%, raise `SystemExit` with error code `E-DATA-INSUFFICIENT` and message "Retention below 80% (Threshold SC-001)". **Verification**: Verify pipeline halts if retention < 80%. <!-- FAILED: unspecified -->
- [ ] T015 [US1] Implement `code/data/validation.py` to perform Listwise Deletion (FR-003) on the merged dataset. **Input**: `data/processed/merged_raw.csv` (output of T013). **Logic**: For any row with missing Genomic, Env, or Compound data, exclude the row. Log exclusion decisions to `logs/exclusions.log`. **Output**: `data/processed/final_cleaned.csv`. **Verification**: Verify `data/processed/final_cleaned.csv` contains no nulls in key columns.
- [X] T016 [US1] Write unit tests for ingestion logic in `code/tests/test_ingestion.py`. **Specific Tests**: `test_ingest_fails_on_missing_url` (verifies mock fallback), `test_ingest_validates_vcf_header`, `test_ingest_validates_csv_schema`. <!-- FAILED: unspecified -->
- [X] T017 [US1] Write integration test for validation pipeline in `code/tests/test_validation.py`. **Specific Tests**: `test_merge_preserves_population_ids`, `test_listwise_deletion_removes_nulls`, `test_retention_check_fails_below_80_percent` (verifies `E-DATA-INSUFFICIENT`). <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Feature Engineering and Model Training (Priority: P2)

**Goal**: Transform raw variants into diversity metrics, aggregate environmental variables, and train a regularized regression model.

**Independent Test**: Run on synthetic dataset; verify model recovers signal (R² > 0.5) and CV scores are consistent.

### Implementation for User Story 2

- [~] T018 [P] [US2] Implement `code/data/preprocessing.py` to parse raw VCF (`data/raw/genomic.vcf` or `mock_genomic.vcf`) into a variant table. **Input**: `data/raw/genomic.vcf` (T010). **Output**: `data/processed/variant_table.csv`. **Function**: `parse_vcf_to_table(vcf_path)`. <!-- FAILED: unspecified -->
- [~] T019 [US2] Implement `code/data/preprocessing.py` to calculate genomic diversity metrics (heterozygosity, nucleotide diversity) per FR-004. **Input**: `data/processed/variant_table.csv` (output of T018). **Output**: `data/processed/diversity_metrics.csv`. **Function**: `calculate_diversity_metrics(df)`.
- [~] T020 [US2] Implement `code/data/preprocessing.py` to aggregate all data to population level (FR-009) and calculate VIF for collinearity check; explicitly flag and log predictors with VIF > 5 as required by Spec Assumption 6. **Input**: `data/processed/diversity_metrics.csv` (T019), `data/processed/final_cleaned.csv` (T015). **Output**: `data/processed/features_vif.csv`. **Function**: `calculate_vif_and_aggregate(df)`. <!-- FAILED: unspecified -->
- [~] T021 [US2] Implement `code/models/training.py` to check N count for CV strategy (5-fold if N≥30, LOOCV if N<30) per FR-005. **Input**: `data/processed/final_cleaned.csv` (T015). **Output**: `data/processed/cv_strategy.json` (contains `cv_type` and `n`). **Function**: `determine_cv_strategy(df)`.
- [~] T022 [US2] Implement `code/models/training.py` to check `unique_studies >= N-1` condition; if met, exclude 'source_study' covariate and use global Z-score per FR-010. **Input**: `data/processed/final_cleaned.csv` (T015). **Output**: `data/processed/covariate_config.json` (contains `use_source_study`, `normalization_type`). **Function**: `determine_covariate_strategy(df)`. <!-- FAILED: unspecified -->
- [~] T023 [US2] Implement `code/data/preprocessing.py` to apply normalization based on T021 and T022 outputs. **Input**: `data/processed/final_cleaned.csv` (T015), `data/processed/cv_strategy.json` (T021), `data/processed/covariate_config.json` (T022). **Output**: `data/processed/features_normalized.csv`. **Function**: `apply_normalization(df, config)`. <!-- FAILED: unspecified -->
- [~] T024 [US2] Implement `code/models/training.py` to train LASSO/Ridge model with `scikit-learn` using selected CV strategy. **Input**: `data/processed/features_normalized.csv` (T023). **Output**: `results/model.pkl`. **Function**: `train_model(df)`. <!-- FAILED: unspecified -->
- [~] T025 [US2] Implement `code/data/preprocessing.py` to detect 'model instability' and perform conditional removal of predictors as per Assumption 6. **Input**: `data/processed/features_vif.csv` (T020), `data/processed/features_normalized.csv` (T023). **Logic**: Flag predictors with VIF > 5; ONLY remove if model training (T024) fails with `SingularMatrixError`; retrain with removed features. **Output**: `data/processed/stable_features.csv`. **Function**: `select_stable_features(vif_df, features_df)`. <!-- FAILED: unspecified -->
- [X] T026 [US2] Write unit tests for feature engineering in `code/tests/test_preprocessing.py` (verify metrics calculation). <!-- FAILED: unspecified -->
- [X] T027 [US2] Write unit tests for model training logic in `code/tests/test_models.py` (verify CV switch and covariate logic).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

**Goal**: Verify model power via permutation tests and ensure robustness via sensitivity analysis.

**Independent Test**: Run permutation test on randomized outcome; verify p-value > 0.05. Verify sensitivity report shows stability.

### Implementation for User Story 3

- [X] T028 [P] [US3] Implement `code/models/evaluation.py` to execute permutation test (n=1000) and generate null distribution per FR-006. <!-- FAILED: unspecified -->
- [X] T029 [US3] Implement `code/models/evaluation.py` to calculate p-value comparing observed R² against null distribution (SC-002, SC-003).
- [~] T030 [US3] Implement `code/models/evaluation.py` to perform sensitivity analysis by sweeping the regularization parameter (alpha) over the set {0.01, 0.05, 0.1} per FR-007. **Output**: `results/stability_report.json`. **Output**: Stability report showing feature selection variation across the sweep. <!-- FAILED: unspecified -->
- [X] T031 [US3] Implement `code/utils/stats.py` to calculate Jaccard index for feature selection stability across the sweep (SC-004).
- [X] T032 [US3] Implement `code/utils/stats.py` to apply Benjamini-Hochberg correction to predictor p-values per FR-008.
- [X] T033 [US3] Implement `code/main.py` to orchestrate the full pipeline: Ingestion → Validation → Feature Eng → Training → Evaluation; explicitly include Constitution Principle V (Versioning Discipline) requirement to update `state/PROJ-475-predicting-plant-defense-compound-produc.yaml` key `updated_at` with current timestamp and update `artifact_hashes` map with content hashes upon completion. <!-- FAILED: unspecified -->
- [X] T034 [US3] Write unit tests for permutation test logic in `code/tests/test_stats.py` (verify null distribution generation).
- [X] T035 [US3] Write unit tests for BH correction and Jaccard index in `code/tests/test_stats.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T036 [P] Update `README.md` with setup instructions and `docs/api.md` with module documentation
- [X] T037 Refactor `code/data/ingestion.py` for DRY principle and `code/utils/stats.py` for type hinting
- [X] T038 Optimize `code/data/preprocessing.py` to stream VCF using `cyvcf2` to ensure memory usage < 7GB
- [ ] T039 [P] Run `quickstart.md` validation
- [ ] T040 Ensure `data/manifest.yaml` is updated with all generated artifacts and checksums

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (`data/processed/final_cleaned.csv`)
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
Task: "Contract test for ingestion in code/tests/test_ingestion.py"
Task: "Integration test for validation in code/tests/test_validation.py"

# Launch all models for User Story 1 together:
Task: "Implement ingestion logic in code/data/ingestion.py"
Task: "Implement validation logic in code/data/validation.py"
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
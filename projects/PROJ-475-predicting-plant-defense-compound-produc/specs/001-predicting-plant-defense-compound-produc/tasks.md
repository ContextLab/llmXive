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
- [X] T009 [US1] Implement `code/data/mock_generator.py` to generate deterministic mock genomic, environmental, and compound data for CI runs, explicitly removing the need for API keys and satisfying the 'no manual key injection' constraint (replaces API key management). **Dependency**: Must be completed before T011-T013. <!-- FAILED: unspecified -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Validation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Assemble a unified dataset by downloading/generating genomic, environmental, and compound data, then validate completeness.

**Independent Test**: Run ingestion script against a small, known subset; verify output CSV has non-null `population_id`, `env_id`, `compound_id` and matches schema.

### Implementation for User Story 1

- [X] T010 [US1] Implement `code/data/ingestion.py` to fetch VCF data from verified NCBI SRA URL OR generate mock data (replaces T010 fetch logic); explicitly enforce verified URL check before fallback to mock to preserve FR-001 constraint. **Output**: `data/raw/genomic_vcf.json`. **Logic**: If `config.verified_urls['genomic']` exists, fetch; else call `mock_generator`. **Post-check**: Call T008 to verify disk usage after fetch/generate. <!-- FAILED: unspecified -->
- [X] T011 [US1] Implement `code/data/ingestion.py` to fetch environmental metadata from verified WorldClim/GBIF URL OR generate mock data; explicitly enforce verified URL check before fallback to mock to preserve FR-002 constraint. **Output**: `data/raw/env_data.json`. **Logic**: If `config.verified_urls['env']` exists, fetch; else call `mock_generator`. **Post-check**: Call T008 to verify disk usage after fetch/generate. <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T012 [US1] Implement `code/data/ingestion.py` to fetch defense compound profiles from verified ChemBank/PhenolExplorer URL OR generate mock data; explicitly enforce verified URL check before fallback to mock to preserve FR-003 constraint. **Output**: `data/raw/compound_data.json`. **Logic**: If `config.verified_urls['compound']` exists, fetch; else call `mock_generator`. **Post-check**: Call T008 to verify disk usage after fetch/generate.
- [X] T013 [US1] Implement `code/data/validation.py` to merge datasets and perform listwise deletion for missing modalities (FR-003)
- [X] T014 [US1] Implement `code/data/validation.py` to calculate and report retention percentage (SC-001) and log exclusion warnings. **Logic**: Aggregate exclusion counts from T015/T016. If retention < 80%, raise `SystemExit` with error code `E-DATA-INSUFFICIENT`.
- [X] T015 [US1] Implement `code/data/preprocessing.py` to handle missing genotype imputation (mean) OR exclude population if missingness > 20% (Edge Case); explicitly mandate logging the exclusion decision to satisfy Constitution Principle VI. **Logic**: Per-population check. If > 20%, exclude row. Output: update `data/processed/filtered.csv` and log to `code/utils/logging.py`. <!-- FAILED: unspecified -->
- [X] T016 [US1] Implement `code/data/preprocessing.py` to handle missing environmental metadata (flag/exclude) per Edge Cases
- [X] T017 [US1] Write unit tests for ingestion logic in `code/tests/test_ingestion.py` (mocked downloads) <!-- FAILED: unspecified -->
- [X] T018 [US1] Write integration test for validation pipeline in `code/tests/test_validation.py` (verify listwise deletion)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Feature Engineering and Model Training (Priority: P2)

**Goal**: Transform raw variants into diversity metrics, aggregate environmental variables, and train a regularized regression model.

**Independent Test**: Run on synthetic dataset; verify model recovers signal (R² > 0.5) and CV scores are consistent.

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `code/data/preprocessing.py` to calculate genomic diversity metrics (heterozygosity, nucleotide diversity) per FR-004
- [ ] T020 [US2] Implement `code/data/preprocessing.py` to aggregate all data to population level (FR-009) and calculate VIF for collinearity check; explicitly flag and log predictors with VIF > 5 as required by Spec Assumption 6. **Output**: `data/processed/features_vif.csv`.
- [X] T021 [US2] Implement `code/data/preprocessing.py` to aggregate environmental variables per population and normalize; explicitly implement conditional logic: if `unique_studies >= N-1` (determined in T020), use global Z-score and exclude 'source_study' covariate; else use per-study Z-score (FR-010, FR-011). **Function**: `apply_normalization(df, unique_studies_count)`.
- [X] T022 [US2] Implement `code/models/training.py` to load data and check N count for CV strategy (5-fold if N≥30, LOOCV if N<30) per FR-005
- [X] T023 [US2] Implement `code/models/training.py` to check `unique_studies >= N-1` condition; if met, exclude 'source_study' covariate and use global Z-score per FR-010
- [X] T024 [US2] Implement `code/models/training.py` to train LASSO/Ridge model with `scikit-learn` using selected CV strategy
- [X] T025 [US2] Implement `code/models/training.py` to extract top 10 predictors by absolute coefficient magnitude
- [X] T026 [US2] Implement `code/data/preprocessing.py` to detect 'model instability' (e.g., VIF > 10 or singular matrix) and perform conditional removal of predictors as per Assumption 6. **Output**: Updated feature set for training.
- [X] T027 [US2] Write unit tests for feature engineering in `code/tests/test_preprocessing.py` (verify metrics calculation)
- [X] T028 [US2] Write unit tests for model training logic in `code/tests/test_models.py` (verify CV switch and covariate logic)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

**Goal**: Verify model power via permutation tests and ensure robustness via sensitivity analysis.

**Independent Test**: Run permutation test on randomized outcome; verify p-value > 0.05. Verify sensitivity report shows stability.

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `code/models/evaluation.py` to execute permutation test (n=1000) and generate null distribution per FR-006
- [X] T030 [US3] Implement `code/models/evaluation.py` to calculate p-value comparing observed R² against null distribution (SC-002, SC-003)
- [X] T031 [US3] Implement `code/models/evaluation.py` to perform sensitivity analysis sweeping alpha values across a range of small significance levels per FR-007
- [X] T032 [US3] Implement `code/utils/stats.py` to calculate Jaccard index for feature selection stability across the sweep (SC-004)
- [X] T033 [US3] Implement `code/utils/stats.py` to apply Benjamini-Hochberg correction to predictor p-values per FR-008
- [~] T034 [US3] Implement `code/main.py` to orchestrate the full pipeline: Ingestion → Validation → Feature Eng → Training → Evaluation; explicitly include Constitution Principle V requirement to update `state/PROJ-475-predicting-plant-defense-compound-produc.yaml` key `updated_at` with current timestamp upon completion. **Dependency**: Must run after T019, T028, T033.
- [X] T035 [US3] Write unit tests for permutation test logic in `code/tests/test_stats.py` (verify null distribution generation)
- [X] T036 [US3] Write unit tests for BH correction and Jaccard index in `code/tests/test_stats.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Update `README.md` with setup instructions and `docs/api.md` with module documentation
- [~] T038 Refactor `code/data/ingestion.py` for DRY principle and `code/utils/stats.py` for type hinting <!-- ATOMIZE: requested --> <!-- FAILED: unspecified -->
- [X] T039 Optimize `code/data/preprocessing.py` to stream VCF using `cyvcf2` to ensure memory usage < 7GB
- [X] T040 [P] Run `quickstart.md` validation
- [X] T041 Ensure `data/manifest.yaml` is updated with all generated artifacts and checksums

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

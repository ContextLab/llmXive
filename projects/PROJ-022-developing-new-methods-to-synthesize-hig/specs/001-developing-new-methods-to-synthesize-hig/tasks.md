# Tasks: Developing New Methods to Synthesize High-Performance Membranes using Sustainable Materials

**Input**: Design documents from `/specs/001-sustainable-membrane-synthesis/`
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

**Purpose**: Project initialization, basic structure, and creation of validation infrastructure required for later phases.

- [ ] T001a [P] Create directory structure: `code/`, `data/raw`, `data/processed`, `data/reports`, `tests/`, `artifacts/` at the repository root.
- [X] T001b [P] Create `requirements.txt` pinning `rdkit==2023.9.5`, `scikit-learn==1.3.2`, `pandas==2.1.4`, `numpy==1.26.2`, `pyyaml==6.0.1`, `datasets==2.14.6`
- [ ] T001c [P] Create `.gitignore` rules for `data/raw/*`, `data/processed/*`, `*.pkl`, `__pycache__`, `*.log`
- [X] T002a [P] Create `code/utils/data_hygiene_check.py` to verify checksums for `data/raw` and ensure no in-place modifications in `data/processed` (Required for T045).
- [X] T002b [P] Create `code/utils/traceability_matrix.py` to generate `artifacts/traceability_matrix.json` linking stats to code/data rows (Required for T046).
- [ ] T002c [P] Create `code/utils/versioning_audit.py` to validate `state.yaml` artifact hashes (Required for T047).
- [X] T002d [P] Create `code/utils/descriptor_reproducibility_check.py` to re-calculate descriptors and verify bitwise equality (Required for T048).
- [X] T002e [P] Create `code/utils/statistical_rigor_final_check.py` to validate Mann-Whitney U test and power analysis reports (Required for T049).
- [X] T002f [P] Initialize `state/projects/PROJ-022-developing-new-methods-to-synthesize-hig.yaml` with `artifact_hashes` map and `current_stage` field (Required for T047).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 [P] Setup `data/raw` and `data/processed` directories with `.gitignore` rules for large files
- [ ] T005 [P] Implement `utils/logging_config.py` for structured logging across pipeline stages
- [X] T006a [P] [FR-001] Create `code/utils/constants.py` with unit conversion factors (Barrer, LMH/bar) and random seed=42
- [X] T006b [P] [FR-006] Create `code/ingestion/calculate_imputation_values.py` to dynamically calculate polymer-class averages from the aggregated dataset (`data/processed/standardized_polymers.csv`) and output them to `data/processed/imputation_values.json`. **Definition**: The script MUST calculate mean permeability/selectivity per polymer class ('cellulose', 'chitosan', 'lignin', 'polyimide') from the current dataset. [UNRESOLVED-CLAIM: c_02ae1d7b — status=not_enough_info] **Constraint**: The script MUST NOT use hardcoded static values; it MUST derive values from the data to ensure Data Hygiene.
- [X] T007 Create base `PolymerRecord` dataclass in `code/ingestion/models.py`
- [X] T008 Configure error handling infrastructure with custom `DataInsufficientError` in `code/utils/errors.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Aggregation and Standardization (Priority: P1) 🎯 MVP

**Goal**: Aggregate sparse literature data, standardize units to Barrer, and handle missing data via imputation or halting.

**Independent Test**: The pipeline can be tested by running the ingestion script against a mock CSV of a representative set of literature entries and verifying the output dataframe contains standardized units, imputed values, and a valid count of non-null performance records.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for unit conversion in `tests/contract/test_standardize_units.py`
- [X] T010 [P] [US1] Integration test for missing data halting logic in `tests/integration/test_missing_data_flow.py`

### Implementation for User Story 1

- [X] T011a [US1] Implement `code/ingestion/manual_extraction.py` to parse structured CSV from manual literature review (FR-001 source 3)
- [X] T011b [US1] [Rev-01] Implement `code/ingestion/automated_fetch.py` to fetch real data from three distinct sources: arXiv (query: "membrane OR polymer"), OpenPolymer (HuggingFace dataset ID: `openpolymer/v1`), and manual extraction (FR-001 requirement). **Safety**: Remove any `try/except` blocks that fallback to `generate_synthetic_data()`; ensure the script raises `ConnectionError` or `DataInsufficientError` immediately if a real source fails to fetch (Constitution: "Loader must fail loudly"). **Conflict Resolution**: Include logic to detect and exclude entries with conflicting performance metrics for the same polymer (high variance) before aggregation.
- [X] T012 [US1] [FR-006] Implement `code/ingestion/handle_missing_data.py` with logic:
 1. Calculate missing percentage for **critical variables** (defined in data-model.md as those required for model training, e.g., permeability, selectivity, VdW volume).
 2. If missing > 20%: Generate `data/reports/missing_data_report.json`, emit error code `ERR_DATA_INSUFFICIENT`, and halt execution immediately.
 3. If [deferred] <= missing <= 20%: Generate `data/reports/clarification_flag.json`, trigger imputation using polymer-class averages (using the dictionary from T006b).
 4. If missing < 5%: Proceed without imputation.
- [X] T013 [US1] Create `code/ingestion/load_literature_data.py` to merge manual and automated sources into a unified dataframe
- [X] T014b [US1] [FR-009, SC-003] Create `code/ingestion/curate_known_bio_membranes.py` to create `data/raw/known_high_performance.csv` by filtering the aggregated literature sources (arXiv/OpenPolymer) for entries explicitly identified as **literature-reported** high-performance bio-membranes. **Constraint**: This task does NOT create a proxy baseline; it enforces the strict requirement to validate the existence of >=10 known high-performance bio-membranes from the aggregated literature dataset (Plan Phase 1, Step 3). **Filter Logic**: Scan entries where `keywords` (case-insensitive) contains 'high-performance' OR 'record-breaking' OR `title` (case-insensitive) contains 'high-performance'. **Note**: These entries must be from verified experimental sources in the literature, not just claims. **Dependency**: [Requires: T011b].
- [X] T014 [US1] Implement validation step in `code/ingestion/validate_dataset.py` to: 1) count valid records (must be ≥30), 2) Verify >= 10 known high-performance bio-membranes exist by checking the `data/raw/known_high_performance.csv` file generated in T014b (strict count validation gate per Plan Phase 1, Step 3), and 3) confirm consistency with T012's missing data flags. **Note**: Do not generate `missing_data_report.json` here; that is handled by T012.
- [X] T015 [US1] [FR-002] Add logic to handle "high variance" entries (coefficient of variation > 0.5 for same polymer metrics) by **excluding** them from the primary training set OR applying a **variance-weighted loss** strategy, as per spec Edge Cases. The implementation must choose the strategy based on data availability and log the choice. **Dependency**: [Requires: T014].
- [X] T016 [US1] Generate `data/processed/standardized_polymers.csv` with standardized units and imputed values

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Feature Engineering and Model Training (Priority: P2)

**Goal**: Generate molecular descriptors using RDKit and train a CPU-tractable Random Forest/Gradient Boosting regressor.

**Independent Test**: The training module can be tested by running on the standardized dataset from US-1 and verifying the model outputs a feature importance ranking and a cross-validated R² score ≥ 0.1.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for RDKit descriptor calculation in `tests/unit/test_descriptors.py`
- [X] T018 [P] [US2] Integration test for model training runtime fallback in `tests/integration/test_training_runtime.py`

### Implementation for User Story 2

- [X] T019 [US2] Implement `code/features/calculate_descriptors.py` to compute VdW volume, H-bond counts, and MW using RDKit (handle parse failures gracefully). **Note**: If FFV is requested but experimental density is missing, log a warning and skip FFV calculation for that record; do not attempt to calculate it from SMILES alone.
- [X] T020 [US2] [FR-011] Implement `code/features/feature_selection.py` to perform dimensionality reduction. **Option Selection**: The implementer may choose **either** Recursive Feature Elimination (RFE) **or** Principal Component Analysis (PCA) as permitted by FR-011.
 - If RFE is chosen: Retain a minimal subset of features to mitigate overfitting.
 - If PCA is chosen: Retain components explaining > 95% variance, but **cap the number of components at 10** to prevent overfitting in the small-N regime (Plan: "small-N vs High-Dimensionality").
 **Constraint**: Do not use all descriptors without reduction.
- [X] T021 [US2] [FR-003] Implement `code/modeling/train_model.py` with Random Forest (initial max_depth=10, n_estimators=100). **Implementation Detail**: Wrap training in a `time` context manager. If **per-attempt** elapsed time > 3600s (60-minute target), raise `RuntimeExceededError` with `new_depth=6` to trigger the outer retry loop. If the second attempt (depth=6) exceeds 3600s, raise `RuntimeExceededError` with `new_depth=4`. **Global Limit**: Implement a global runtime guard. If the *cumulative* time of all retries exceeds 6 hours (SC-004), halt execution, emit error code `ERR_RUNTIME_EXCEEDED`, and generate `data/reports/runtime_exceeded_report.json`. **Traceability**: Use fallback depths (6, then 4) as explicitly resolved in `plan.md` Complexity Tracking. **Artifact**: Log the fallback decision and runtime metrics to `data/reports/runtime_fallback_log.json`. **Pre-training**: Log sample size (N) and confirm it matches the power analysis assumptions (N≥30) based on **T014's** prior validation. Do NOT perform the validation check here; rely on T014's success.
- [X] T022 [US2] Implement `code/modeling/cross_validate.py` to run stratified k-fold CV and report R² and MAE
- [X] T023 [US2] [FR-008] Add categorical encoding for 'synthesis method' in the feature matrix
- [X] T024 [US2] Save trained model artifact to `artifacts/model.pkl`
- [X] T025 [US2] [FR-007] Add explicit disclaimer in model metadata that findings are associational, not causal
- [X] T026 [US2] Save feature matrix to `data/processed/feature_matrix.csv`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Candidate Screening and Statistical Validation (Priority: P3)

**Goal**: Screen a virtual library of sustainable candidates, rank them, and statistically compare against *experimental* petrochemical benchmarks.

**Independent Test**: The screening module can be tested by providing a known set of "high-performance" and "low-performance" dummy candidates and verifying the ranking order matches the the expected performance distribution.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Contract test for statistical test output format in `tests/contract/test_statistical_test.py`
- [X] T028 [P] [US3] Integration test for power analysis report generation in `tests/integration/test_power_analysis.py`

### Implementation for User Story 3

**⚠️ PREREQUISITE**: Phase 4 (Model Training) MUST be complete. T024 (`artifacts/model.pkl`) is a hard dependency for T029c and T030.

- [X] T029e [US3] [FR-002] Create `code/screening/templates.py` containing the base SMILES templates and R-group expansion logic for cellulose, chitosan, and lignin derivatives required by T029a.
- [X] T029a [US3] [Rev-04] Implement `code/screening/generate_bio_candidates.py` to generate a diverse set of unique sustainable candidate SMILES from cellulose, chitosan, and lignin templates. **Algorithm**: Use `code/screening/templates.py` (created in T029e) to expand R-groups deterministically (seed=42) by enumerating R-groups from a defined set of substituents to satisfy SC-002 (ensure sufficient statistical power for ranking). Ensure reproducibility.
- [X] T029b [US3] Implement `code/screening/generate_petro_benchmarks.py` to generate a set of petrochemical benchmark SMILES from polyimide and polysulfone base templates using deterministic template expansion (seed=42)
- [X] T029d [US3] [FR-005] Create `code/screening/acquire_experimental_benchmarks.py` to load or manually curate the experimental petrochemical benchmark dataset into `data/raw/experimental_petro_benchmarks.csv`. **Source**: Populate this file from verified literature sources (manual extraction or verified literature review) containing experimental permeability/selectivity values for petrochemical benchmarks. **Constraint**: This dataset must contain real experimental measurements, not model predictions, to satisfy FR-005.
- [X] T029c [US3] [FR-001, FR-005] Implement `code/screening/generate_predicted_benchmarks.py` to generate `data/processed/predicted_benchmarks.csv`. **Action**: Load the petrochemical SMILES from T029b, run them through the trained model (**T024**) to generate *predicted* permeability and selectivity values. **Purpose**: Create the control distribution for the Mann-Whitney U test (Predicted vs. Predicted) if experimental data is unavailable, but primarily to compare against the experimental benchmarks in T029d. **Dependency**: [Requires: T024].
- [X] T030 [US3] [FR-005] Implement `code/screening/rank_candidates.py` to predict performance for bio-candidates using the trained model (**T024**) and load **experimental** petrochemical benchmark values (from T029d) to generate the control distribution for comparison. **Dependency**: [Requires: T024, T029c].
- [X] T031 [US3] [FR-005] Implement `code/screening/statistical_test.py` to run Mann-Whitney U test comparing the *predicted* bio-candidate distribution (from T030) against the **experimental** petrochemical benchmark distribution (from T029d). **Output**: Generate `data/reports/statistical_test_results.json` containing the p-value and effect size. **Constraint**: This task validates the model's ability to discriminate bio-candidates from real experimental benchmarks. **Note**: If experimental data is missing, document the limitation in the report referencing FR-009 (Future Work).
- [X] T032 [US3] [FR-009] Implement `code/screening/generate_validation_protocol.py` to generate `validation_protocol.md`. **Content**: This document must explicitly state that experimental validation of the top 3 predicted candidates is a *future work* requirement (FR-009) and outline the specific experimental protocols required to obtain ground truth data. It serves as a hand-off artifact for future experimental teams, not a validation gate for the current computational phase.
- [X] T033 [US3] Implement `code/screening/power_analysis.py` to calculate detectable effect size for N=30 (power=0.8, alpha=0.05) and generate `data/reports/power_analysis_report.json`
- [X] T034 [US3] Generate `data/reports/screening_results.json` with ranked candidates and p-values
- [X] T035 [US3] [FR-009] Create `candidate_recommendation_report.md` listing top candidates for *future* experimental validation (fulfilling FR-009 requirement artifact), including a validation status flag indicating the requirement is pending

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Future Work (Priority: P4)

**Goal**: Compile final results and validate citations.

- [X] T036 [US3] Implement `code/reporting/generate_final_report.py` to aggregate feature importance, statistical tests, and candidate lists
- [X] T037 [US3] [Const-II] Implement `validate_citations.py` to re-check all references in `candidate_recommendation_report.md` and `data/reports/final_report.md` against primary sources by running `python code/reporting/validate_citations.py` and checking Title-token-overlap (Constitution Principle II)
- [X] T038 [P] Run end-to-end pipeline validation script `code/main_pipeline.py` to verify a bounded runtime limit on a multi-core CPU

---

## Phase 7: Revision & Compliance Fixes (Priority: P1)

**Goal**: Address specific reviewer concerns regarding data integrity, statistical rigor, and execution safety.

**Note**: Per project assumptions (spec.md/plan.md), datasets fit within 7GB RAM; streaming loaders are NOT required.

- [X] T041 [US2] [Rev-Stats] Update `code/modeling/cross_validate.py` to explicitly log the power analysis assumptions (N=30) and the detectable effect size before training, ensuring the model training is not proceeding on an underpowered dataset without a warning flag.
- [X] T042 [US3] [Rev-Stats] Update `code/screening/statistical_test.py` to include a "Power Analysis Report" generation step that explicitly states the limitations of the N=30 sample size for detecting medium/small effects, as required by FR-010 and SC-003.
- [X] T043 [US3] [Rev-Data] Implement `code/screening/validate_candidate_library.py` to ensure the generated virtual library (T029a) contains at least 50 unique, chemically valid SMILES strings and logs a warning if the diversity metric falls below a threshold.
- [X] T044 [US1] [Rev-Data] **Removed**: Redundant with T015.

---

## Phase 8: Final Compliance & Artifact Locking (Priority: P1)

**Goal**: Ensure all constitutional principles are met before final hand-off and lock all artifacts to prevent drift.

- [ ] T045 [P] [Const-III] Run `code/utils/data_hygiene_check.py` (created in T002a) to verify checksums for all files in `data/raw` match their recorded hashes and that no files in `data/processed` were modified in-place.
- [ ] T046 [P] [Const-IV] Run `code/utils/traceability_matrix.py` (created in T002b) to generate `artifacts/traceability_matrix.json` linking every statistic in `data/reports/` to the specific code line and input row that produced it.
- [ ] T047 [P] [Const-V] Run `code/utils/versioning_audit.py` (created in T002c) to ensure all artifact hashes in `state.yaml` are current and no stale review records exist.
- [ ] T048 [P] [Const-VI] Run `code/utils/descriptor_reproducibility_check.py` (created in T002d) to re-calculate a random subset of descriptors and verify bitwise equality with `data/processed/feature_matrix.csv`.
- [ ] T049 [P] [Const-VII] Run `code/utils/statistical_rigor_final_check.py` (created in T002e) to confirm the Mann-Whitney U test was performed on predicted distributions only and that the power analysis report is attached to the final results.
- [ ] T050 [P] Lock `artifacts/` directory permissions (read-only) and generate `FINAL_RELEASE_NOTES.md` confirming all constitutional gates passed.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Data Integrity**: Integrated into Phases 3, 4, and 5 (T011b, T021, T029a). No separate phase required.
- **Compliance Locking (Phase 8)**: Depends on completion of all previous phases and revision tasks.
- **Execution Safety (Phase 9)**: **Removed**: Tasks T051-T053 were removed as they represented scope creep.

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
- Safety tasks (T011b, T021, T029a) are integrated into their respective phases and can be executed in parallel with other tasks in those phases.
- Revision tasks (Phase 7) can be executed in parallel with each other, but depend on the completion of the core phases they address.
- Compliance tasks (Phase 8) can be executed in parallel as they are independent verification steps on the final artifacts.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for unit conversion in tests/contract/test_standardize_units.py"
Task: "Integration test for missing data halting logic in tests/integration/test_missing_data_flow.py"

# Launch all models for User Story 1 together:
Task: "Create base PolymerRecord dataclass in code/ingestion/models.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (including integrated safety checks)
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
- **Critical**: Safety checks (T011b, T021, T029a) are integrated into their respective phases to ensure data integrity and execution safety from the start.
- **Critical**: Streaming logic is NOT implemented as per project assumptions (datasets fit in GB RAM).
- **Critical**: Revision tasks (Phase 7) are mandatory to address specific reviewer concerns regarding data integrity, statistical rigor, and execution safety before final deployment.
- **Critical**: T029c and T030 require T024 (model.pkl) to be complete.
- **Critical**: T031 and T032 explicitly distinguish between computational validation of model discrimination and the future work requirement of experimental validation (FR-009).
- **Critical**: Phase 8 tasks are mandatory to lock artifacts and ensure constitutional compliance before final release.
- **Critical**: T002a-T002f create the necessary infrastructure scripts and state files required by Phase 8 tasks T045-T050.
- **Critical**: Phase 9 tasks (T051-T053) have been removed as they represented scope creep not authorized by the Spec or Plan.
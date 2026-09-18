# Tasks: Exploring the Correlation Between Crystal Structure and Thermal Conductivity in Perovskites

**Input**: Design documents from `/specs/001-correlation-perovskites/`
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

- [ ] T001 Create project structure with exact directory tree: src/, tests/, data/raw/, data/cleaned/, data/results/, figures/, contracts/
- [X] T002 Initialize Python project with requirements.txt at repository root (pymatgen==2023.9.1 [UNRESOLVED-CLAIM: c_2f78f30a — status=not_enough_info], pandas==2.2.2 [UNRESOLVED-CLAIM: c_fd762eba — status=not_enough_info], numpy==1.26.4 [UNRESOLVED-CLAIM: c_668708ca — status=not_enough_info], scikit-learn==1.5.0 [UNRESOLVED-CLAIM: c_049c6881 — status=not_enough_info], statsmodels==0.14.2 [UNRESOLVED-CLAIM: c_888778cd — status=not_enough_info], {{claim:c_18b3772d}} (pi, https://en.wikipedia.org/wiki/Pi), seaborn==0.13.2 [UNRESOLVED-CLAIM: c_06808731 — status=not_enough_info], requests==2.32.3 [UNRESOLVED-CLAIM: c_6008bf37 — status=not_enough_info], tqdm==4.66.5 [UNRESOLVED-CLAIM: c_ede4c8fc — status=not_enough_info], pytest)
- [X] T003 [P] Configure linting and formatting: create.flake8 (max-line-length=88, extend-ignore=E203) and pyproject.toml (black settings)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **This phase also resolves governance conflicts before data ingestion.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Setup environment configuration management for API keys at `src/config/env.py`. MUST define `MP_API_KEY` as a required variable. Script MUST exit with code 0 if key is present, and code 1 with error message "MP_API_KEY not set" if missing. (FR-001)
- [ ] T005 [P] Create `contracts/merged_perovskite.schema.yaml` defining the CSV schema. Schema MUST include fields: `structure_id`, `thermal_conductivity`, `source_reference`, `chemistry_class`, `temperature`, `tilting_angle`, `bond_length_variance`, `tolerance_factor`, `unit_cell_volume`. (FR-002, FR-010)
- [X] T006 [P] Setup SHA-256 checksum tracking for raw data files to `state/projects/PROJ-035-exploring-the-correlation-between-crysta.yaml` under the `artifact_hashes` map (Constitution III).
- [X] T007 [P] Create base validation utilities at `src/utils/validation.py` with function signatures: `calculate_vif(df, predictors)`, `scan_causal_language(text)`, `setup_logger(name, level)`. Input/Output contracts MUST be defined in docstrings. (FR-007, FR-008)
- [ ] T008 [P] Implement deterministic seed handling (--seed argument) in exact modules: src/ingest/, src/cleaning/, src/descriptors/, src/analysis/, src/utils/ with explicit random_state=42 [UNRESOLVED-CLAIM: c_5c6fdd64 — status=not_enough_info] in all random operations.
- [X] T009 [P] [Foundational] Implement full `src/utils/validation.py` module including `calculate_vif` (VIF > 5 exclusion logic [UNRESOLVED-CLAIM: c_854fcb58 — status=not_enough_info]), `scan_causal_language` (prohibited keywords check), and `setup_logger`. MUST be self-contained and importable. (FR-007, FR-008)
- [X] T010 [P] [US1] Implement schema validation for citation metadata in `src/utils/citation_schema.py` to ensure required fields (title, authors, year, doi) exist in any future citation entry. This is a PRE-VALIDATION step (Constitution II).
- [X] T016b [P] [Foundational] Implement `src/cleaning/temperature_normalize.py` with the Slack (1979) formula: `k(T) = k_ref * (T_ref / T)^1.0`. MUST accept `--seed` and be callable as a utility function by T016. (FR-013)
- [ ] T038 [P] Document Constitution VII vs FR-010 conflict in `research.md` and flag for spec amendment. Tags: `Constitution VII`, `Conflict`. (FR-010, Constitution VII)
- [ ] T041 [P] [Foundational] **Verify** that Constitution VII has been amended (or alignment documented in research.md) to align with FR-010 (peer-reviewed literature only). Script MUST check for the presence of the amendment or documented resolution before T014b runs. If not found, exit with error "Constitution VII not aligned with FR-010". (FR-010, Constitution VII)
- [ ] T024 [P] [US2] Implement `src/utils/sensitivity.py` for p-value threshold sensitivity analysis across varying significance levels. This utility MUST be importable by T023. (FR-009)
- [ ] T005b [P] [Foundational] Implement `src/utils/metadata.py` to generate `data/metadata.yaml` recording the exact dataset version (API query date, repository release tag) for thermal conductivity sources, satisfying Constitution VII. (FR-010, Constitution VII)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion & Cleaning Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download perovskite crystal structures from Materials Project API and merge with thermal conductivity values from peer-reviewed literature/NIST (NOT Materials Project thermal endpoint), filtering for valid ABX₃ stoichiometry and removing entries with missing data. **Order: Fetch -> Validate -> Normalize -> Merge.**

**Independent Test**: Execute data ingestion script and verify output CSV contains ≥ 50 rows with no null values in thermal_conductivity or structure_id columns

**Acceptance Scenarios**:

1. **Given** the Materials Project API is accessible, **When** the script filters for ABX₃ stoichiometry, **Then** only entries matching the perovskite formula are retained.
2. **Given** a merged dataset of structures and thermal properties, **When** entries with missing thermal conductivity are identified, **Then** the resulting dataframe has ≥50 rows after filtering (SC-001).

**TDD Execution Note**: All test tasks below are written to FAIL first, then implementation follows.

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `src/ingest/fetch_structures.py` for Materials Project API download with ABX₃ filtering, exponential backoff (limited number of retries), error handling (FR-001), and explicit `--seed` argument handling (random_state=42 [UNRESOLVED-CLAIM: c_5c6fdd64 — status=not_enough_info]) for deterministic retries.
- [ ] T014b [P] [US1] Implement `src/ingest/fetch_thermal.py` to load thermal conductivity values **exclusively** from NIST Materials Data Repository (via `huggingface_hub` or specific NIST URL) or verified peer-reviewed literature CSVs. MUST fail loudly (exit code 1) if source is unreachable or invalid; NO synthetic fallback allowed. **MUST depend on T041 (Constitution alignment check) and T005b (metadata generation).** Output to `data/raw/thermal_raw.csv`. (FR-010)
- [ ] T014 [US1] Implement `src/cleaning/provenance_validator.py` to verify peer-reviewed/NIST `source_reference` for each entry using regex for DOI (10.\d{4}/.*/.), PMID (10.\d{4}/\d+), and NIST ID (NIST-[A-Z0-9]+). Output `data/cleaned/provenance_report.json` with pass/fail counts. Exit with code 1 if any entry lacks valid provenance. **MUST depend on T007 (base validation utilities).** (FR-010)
- [ ] T016 [US1] Invoke `src/cleaning/temperature_normalize.py` (T016b) to normalize all thermal conductivity measurements to 300K ± 10K using Slack (1979) formula. **Explicitly identify entries with 'unknown' temperature and discard them before normalization.** Write normalized data to `data/cleaned/normalized_thermal.csv`. (FR-013)
- [ ] T015 [US1] Implement `src/cleaning/clean_merge.py` to merge structures (T013) with thermal data (T014b, T014), validate provenance (T014), apply temperature normalization (T016), remove nulls, validate geometry, enforce minimum 50 compositions, and add error handling for insufficient samples with message 'Insufficient samples: N < 50'. **MUST depend on T005 (schema), T014b, T014, and T016 completion.** (FR-002, FR-010, SC-001)
- [ ] T011 [US1] Contract test for `merged_perovskite.schema.yaml` in `tests/contract/test_schema.py`
- [X] T012 [US1] Integration test for full data ingestion pipeline in `tests/integration/test_full_pipeline.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Structural Descriptor Calculation & Correlation Analysis (Priority: P2)

**Goal**: Compute crystallographic distortion metrics (octahedral tilting angles, bond-length variance, tolerance factor) using pymatgen and perform statistical correlation analysis stratified by perovskite chemistry class

**Independent Test**: Run correlation module on cleaned, stratified dataset and verify output includes correlation matrix with p-values for all defined descriptors within each chemistry class

**TDD Execution Note**: All test tasks below are written to FAIL first, then implementation follows.

### Tests for User Story 2

- [X] T018 [US2] Unit test for descriptor calculation in `tests/unit/test_descriptors.py`
- [ ] T019 [US2] Unit test for correlation analysis in `tests/unit/test_analysis.py`
- [ ] T020 [US2] Unit test for sensitivity analysis in `tests/unit/test_sensitivity.py` verifying p-value sweep output includes results for {0.01, 0.05, 0.1} (FR-009)

### Implementation for User Story 2

- [ ] T021 [US2] Implement `src/descriptors/compute_descriptors.py` for octahedral tilting angles (using `pymatgen.analysis.local_env.OctahedralSiteSymmetryFinder` and custom geometric calculation), bond-length variance, tolerance factor (using `pymatgen.analysis.structure_prediction.ToleranceFactor`), **and unit cell volume**. Must accept `--seed` for any stochastic geometry checks. **Output all descriptors to `data/descriptors.csv` as required columns.** (FR-003)
- [ ] T022 [US2] Implement `src/analysis/stratify.py` for stratification by perovskite chemistry class (oxide, halide, nitride). **MUST be completed before T023.** (FR-014)
- [ ] T023 [US2] Implement `src/analysis/correlation.py` for Pearson and Spearman correlation with multiple-comparison correction using the **Bonferroni** method explicitly. This module MUST import sensitivity sweep logic from `src/utils/sensitivity.py` (T024) and consume stratified output from T022. **MUST NOT be marked [P] as it depends on T022.** Must accept `--seed`. (FR-004, FR-009, FR-014)
- [ ] T025 [US2] Add error handling for insufficient sample size after cleaning in `src/cleaning/clean_merge.py` with message 'Insufficient samples: N < 50' (if not already done in T015)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Regression Modeling & Validation (Priority: P3)

**Goal**: Fit a multiple linear regression model using scikit-learn with K-fold cross-validation, evaluate performance on a held-out test set, report R² and RMSE, and generate scatter plots with confidence intervals

**Independent Test**: Execute modeling script on pre-processed dataset and verify output includes (i) cross-validated performance metrics, (ii) R² > 0.5 on the held-out test set (SC-003), (iii) RMSE value, (iv) a feature-importance report, and (v) the required scatter plots

**TDD Execution Note**: All test tasks below are written to FAIL first, then implementation follows.

### Tests for User Story 3

- [ ] T026 [US3] Contract test for regression output schema in `tests/contract/test_regression_schema.py`
- [ ] T027 [US3] Integration test for full modeling pipeline in `tests/integration/test_regression.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement `src/analysis/regression.py` with two functions: `fit_model()` for 5-fold CV (FR-005) and `evaluate_test()` for held-out test evaluation with R², RMSE, feature importance, and explicit SC-003 R² > 0.5 pass/fail verification. The A standard train/test split will be employed to evaluate model performance. MUST be stratified by the 'chemistry_class' column (FR-014), use random_state=42 [UNRESOLVED-CLAIM: c_5c6fdd64 — status=not_enough_info], and accept `--seed` argument (FR-006, SC-003)
- [ ] T029 [US3] Extend `src/utils/validation.py` (T007, T009) with `scan_causal_language(text)` function that fails pipeline on prohibited keywords {cause, leads to, driven by, effect of, result of} (FR-007)
- [ ] T030 [US3] Implement `src/analysis/visualize.py` for scatter plot generation for top-k correlated descriptors with % CI bands (FR-012)
- [ ] T031 [US3] **Verify** citation "Smith et al., Advanced Materials, (), 2101234" using Reference-Validator Agent. **If verification fails, halt pipeline with error "Citation Smith et al. () verification failed; cannot justify R² > 0.5 target".** If verified, generate R² > 0.5 performance target justification citing Smith et al. to `data/results/final_report.md` under section header `## R² Target Justification` (FR-015, SC-003)
- [ ] T032 [US3] Generate feature importance report (coefficients magnitude or permutation importance) to `data/results/feature_importance.csv` (FR-011)
- [ ] T033 [US3] Save all figures as high-resolution PNG files (minimum 300 DPI) to `figures/` directory (FR-012)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Profile pipeline with cProfile and document bottlenecks in `docs/performance.md`
- [ ] T035 [P] Documentation updates: `docs/quickstart.md` (setup instructions) and `docs/api.md` (function documentation) with content requirements
- [ ] T036 [P] Additional unit tests for edge cases in `tests/unit/test_edge_cases.py` covering: API rate limits, invalid geometry, insufficient samples, collinearity detection
- [ ] T037 [P] Run constitution check and document any remaining conflicts in `research.md`
- [ ] T010b [P] [US3] Execute Reference-Validator Agent on `final_report.md` citations (Slack 1979, Smith et al. 2021) to verify content accuracy per Constitution II (FR-015). This runs AFTER T031 generates the report.
- [ ] T039 [US3] Execute Reference-Validator Agent on `final_report.md` citations before publication (Constitution II)
- [ ] T040 [P] Generate content hashes for ALL artifacts (raw data, cleaned data, descriptors, figures, reports) and update `state/projects/PROJ-035-exploring-the-correlation-between-crysta.yaml` `artifact_hashes` (Constitution V)

**Checkpoint**: Project ready for research review and publication

---

## Phase 7: Execution & Verification (Post-Implementation)

**Purpose**: Final validation steps to ensure the pipeline runs end-to-end and meets all success criteria before research review.

- [ ] T042 [US1] Execute full data ingestion pipeline by running `python src/main.py --stage ingest` and verify output `data/cleaned/merged_perovskite.csv` contains ≥50 rows with no nulls (SC-001). Log execution time and resource usage.
- [ ] T043 [US2] Execute descriptor computation and correlation analysis (T021, T022, T023, T024) on the cleaned dataset. Verify `data/results/correlation_matrix.json` exists, contains keys `stratified_results` and **`corrected_p_values`** (FR-004, FR-014).
- [ ] T044 [US3] Execute regression modeling and visualization (T028, T030, T031, T032, T033). Verify `data/results/model_metrics.json` reports R² > 0.5 (SC-003) and `figures/` contains 300 DPI plots with 95% CI (FR-012).
- [ ] T045 [US3] Run final causal-language scan on `data/results/final_report.md` using `src/utils/validation.py` (T029) to ensure no prohibited keywords exist (FR-007).
- [ ] T046 [US2] Verify VIF exclusion logic in `src/utils/validation.py` (T009) by inspecting `data/results/vif_report.json` and confirming all included predictors have VIF < 5 (SC-004).
- [ ] T047 [US2] Verify sensitivity analysis output in `data/results/sensitivity_analysis.json` confirms headline rates vary across p-value thresholds and explicitly contains keys **`0.01`**, **`0.05`**, and **`0.1`** (FR-009).
- [ ] T048 [US1] Confirm `src/ingest/fetch_thermal.py` (T014b) loads exclusively from peer-reviewed/NIST sources and fails loudly (exit code 1) if provenance validation (T014) fails, with no synthetic fallback (FR-010).
- [ ] T049 [US3] Validate that the final report explicitly cites Smith et al. (n.d.) for the R² > 0.5 target in `data/results/final_report.md` (FR-015).

**Checkpoint**: Pipeline fully executed, all success criteria met, and artifacts ready for publication.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **User Story 2 (P2)**: Depends on US1 cleaned data for descriptor computation
 - **User Story 3 (P3)**: Depends on US2 computed descriptors for regression modeling
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Execution & Verification (Phase 7)**: Depends on all implementation tasks (Phase 3-6) being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 cleaned data - cannot run in parallel with US1
- **User Story 3 (P3)**: Depends on US2 computed descriptors - cannot run in parallel with US2

### Within Each User Story

- Tests MUST be written to FAIL before implementation (TDD approach)
- Data ingestion before merging before cleaning
- Descriptor computation before correlation analysis
- Correlation analysis before regression modeling
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- T013, T014, T016b can run in parallel (independent data sources/utilities)
- Once Foundational phase completes, tests for each user story can run in parallel
- Different user stories CANNOT be worked on in parallel due to data-flow dependencies

### Resource Constraints

- **RAM**: ~7 GB (aligned with spec.md Assumptions)
- **CPU**: 2 cores (GitHub Actions free tier)
- **Disk**: ~14 GB
- **No GPU**: All tasks must run on CPU-only hardware
- **Time limit**: Entire pipeline ≤ 6 hours

### Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (after implementation):
Task: "Contract test for merged_perovskite.schema.yaml in tests/contract/test_schema.py"
Task: "Integration test for full data ingestion pipeline in tests/integration/test_full_pipeline.py"

# Launch all ingestion tasks for User Story 1 together (T013, T014, T014b have [P] tag):
Task: "Implement fetch_structures.py for Materials Project API download with ABX₃ filtering (FR-001)"
Task: "Implement provenance_validator.py to verify source references (FR-010)"
# Note: T014b depends on T041, so it runs after T041 completes.
```

---

## Parallel Example: User Story 2

```bash
# Launch all tests for User Story 2 together (after implementation):
Task: "Unit test for descriptor calculation in tests/unit/test_descriptors.py"
Task: "Unit test for correlation analysis in tests/unit/test_analysis.py"
Task: "Unit test for sensitivity analysis in tests/unit/test_sensitivity.py"

# Launch descriptor and correlation tasks:
Task: "Implement compute_descriptors.py for octahedral tilting angles, bond-length variance, tolerance factor, unit cell volume (FR-003)"
Task: "Implement stratification by perovskite chemistry class (oxide, halide, nitride) (FR-014)"
# Note: T023 (correlation) must run AFTER T022 (stratify) and T024 (sensitivity).
```

---

## Parallel Example: User Story 3

```bash
# Launch all tests for User Story 3 together (after implementation):
Task: "Contract test for regression output schema in tests/contract/test_regression_schema.py"
Task: "Integration test for full modeling pipeline in tests/integration/test_regression.py"

# Launch modeling and visualization tasks:
Task: "Implement regression.py for multiple linear regression with 5-fold CV and held-out test evaluation (FR-005, FR-006)"
Task: "Implement causal-language check scanner for prohibited keywords (FR-007)"
Task: "Implement scatter plot generation for top-3 correlated descriptors with 95% CI bands (FR-012)"
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
3. Add User Story 2 → Test independently → Deploy/Demo (requires US1 data)
4. Add User Story 3 → Test independently → Deploy/Demo (requires US2 descriptors)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (data ingestion)
 - Developer B: Tests for User Story 1
3. After US1 complete:
 - Developer A: User Story 2 (descriptors + correlation)
 - Developer B: Tests for User Story 2
4. After US2 complete:
 - Developer A: User Story 3 (regression + validation)
 - Developer B: Tests for User Story 3
5. Stories complete and integrate sequentially due to data-flow dependencies

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD approach)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Constraint**: All tasks must run on CPU-only CI (2 cores, ~7 GB RAM, ≤6 h) - no GPU, no 8-bit/4-bit quantization, no large LLMs
- **RAM Consistency**: ~7 GB RAM (aligned with spec.md Assumptions, not 5 GB)
- **Data Flow**: T013/T014/T016 must complete before T015; T021 must complete before T023; T022 must complete before T023; T023 must complete before T028; T028 must complete before T043/T044; T041 must complete before T014b; T005 must complete before T015; T007 must complete before T014.
- **FR Mapping**: All 15 functional requirements (FR-001 through FR-015) are explicitly addressed in task descriptions
- **Constitution Conflict**: T038 documents the Constitution VII vs FR-010 conflict; T041 verifies the amendment/alignment.
- **File Scope**: T007 creates base `src/utils/validation.py`; T009 implements the full module including VIF and causal checks.
- **Task ID Uniqueness**: All T### IDs are unique (T010 split into T010a and T010b; T014b added for thermal fetch; T042-T049 = Execution Phase; T016b added for normalization; T009 unified from T009a/b; T005b added for metadata; T031b merged into T031).
- **Execution Verification**: Phase 7 tasks (T042-T049) are mandatory final checks to ensure the pipeline produces valid, real results before publication.
- **Implementation Status**: All implementation tasks (T013-T016, T021-T025, T028-T033) are currently `[ ]` (pending) and must be implemented before Phase 7 execution.
# Tasks: Fairness Metric Divergence Analysis

**Input**: Design documents from `/specs/001-fairness-metric-divergence-analysis/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `logs/`, `tests/` at repository root
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

- [ ] T001 Create project structure per implementation plan (code/, data/raw/, data/processed/, data/analysis/, logs/, tests/, state/)
- [ ] T002 Initialize Python 3.11 project with requirements.txt (scikit-learn, statsmodels, pandas, numpy, scipy, requests, hashlib)
- [ ] T003 [P] Configure linting and formatting tools (black, flake8, isort)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create data-model.py with Dataset, Model, FairnessMetric, DatasetCharacteristic entities
- [ ] T005 [P] Setup logging infrastructure (logs/exclusion.log with dataset_id and missing_variable_name format)
- [ ] T006 [P] Create utils/metrics.py with fairness metric formula implementations (docstrings with LaTeX math notation)
- [ ] T007 [P] Create utils/dataset_loaders.py with URL-based dataset fetchers (UCI Adult, COMPAS, Bank Marketing, German Credit, Law School)
- [ ] T008 [P] Create utils/validators.py for checksum verification (SHA-256) and variable presence validation
- [ ] T009 Create state/projects/PROJ-099-statistical-analysis-of-algorithmic-fair.yaml with project metadata

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download multiple public datasets containing binary protected attributes and outcomes, preprocess to extract fairness-relevant features, ensure all required variables present, sample to ≤100k rows

**Independent Test**: Can be fully tested by verifying that all target datasets are downloaded, contain required columns, and are within size constraints (≤100k rows, <500MB each), delivering a validated dataset repository

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for dataset download in tests/contract/test_dataset_download.py
- [ ] T011 [P] [US1] Integration test for preprocessing pipeline in tests/integration/test_preprocessing.py
- [ ] T012 [P] [US1] Unit test for checksum verification in tests/unit/test_checksum.py
- [ ] T013 [P] [US1] Unit test for variable presence validation in tests/unit/test_variable_validation.py

### Implementation for User Story 1

- [ ] T014 [US1] Implement 01_data_acquisition.py for downloading UCI Adult, COMPAS, Bank Marketing, German Credit, Law School datasets via HTTP/HTTPS
- [ ] T014a [US1] Implement seed pinning (random_state=42) throughout 01_data_acquisition.py for all stratified operations and sampling (Constitution Principle I reproducibility requirement)
- [ ] T015 [US1] Implement SHA-256 checksum verification in 01_data_acquisition.py by calling utils/validators.py functions from T008 (FR-001)
- [ ] T016 [US1] Implement 02_preprocessing.py for extracting binary protected attributes (gender=0/1, race=0/1) and binary outcomes
- [ ] T016a [US1] Implement seed pinning (random_state=42) throughout 02_preprocessing.py for all stratified sampling operations (Constitution Principle I reproducibility requirement)
- [ ] T017 [US1] Implement stratified sampling to ≤100k rows per dataset in 02_preprocessing.py (FR-002)
- [ ] T018 [US1] Implement exclusion logging to logs/exclusion.log with dataset_id and missing_variable_name for datasets lacking required variables (FR-002)
- [ ] T019 [US1] Store preprocessed datasets in data/processed/ with checksums recorded
- [ ] T053a [US1] Add disclaimer "Findings are associational only; no causal claims are made." to all US1 console output and log messages (FR-008)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Fairness Metric Computation (Priority: P2)

**Goal**: Train multiple baseline models per dataset and compute multiple fairness metrics (demographic parity difference, equalized odds difference, predictive parity, calibration within groups, disparate impact ratio, false positive rate disparity)

**Independent Test**: Can be fully tested by running the metric computation pipeline on a single dataset and verifying all relevant metrics are calculated for each model, delivering a metrics matrix

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Contract test for model training in tests/contract/test_model_training.py
- [ ] T022 [P] [US2] Integration test for fairness metric computation in tests/integration/test_fairness_metrics.py
- [ ] T023 [P] [US2] Unit test for demographic parity difference formula in tests/unit/test_demographic_parity.py
- [ ] T024 [P] [US2] Unit test for equalized odds difference formula in tests/unit/test_equalized_odds.py

### Implementation for User Story 2

- [ ] T025 [US2] Implement 03_model_training.py with A stratified train/test split and random seed pinning (random_state=42) (FR-003)
- [ ] T026 [US2] Implement Logistic Regression, Random Forest, Gradient Boosting model training with CPU-only execution in 03_model_training.py
- [ ] T027 [US2] Save trained models to data/processed/models/ with model_id, model_type, dataset_id metadata
- [ ] T028 [P] [US2] Implement 04_fairness_metrics.py with all 6+ metrics: demographic parity difference, equalized odds difference, predictive parity, calibration within groups, disparate impact ratio, false positive rate disparity
- [ ] T029 [US2] Document fairness metric formulas in utils/metrics.py docstrings (from T006) with LaTeX math notation and citation references to Appendix A (FR-004, SC-002)
- [ ] T030 [US2] Store metrics in data/analysis/metrics.csv with model_id, dataset_id, protected_attribute, metric_name, metric_value (FR-004)
- [ ] T031 [US2] Add traceability: pair each metric value with model identifier, dataset identifier, and protected attribute (FR-004)
- [ ] T031a [US2] Implement validation for class imbalance ratios >10:1 in 04_fairness_metrics.py and apply stratified balancing before metric calculation (edge case handling)
- [ ] T053b [US2] Add disclaimer "Findings are associational only; no causal claims are made." to all US2 console output and metric report headers (FR-008)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlation Analysis and Predictive Modeling (Priority: P3)

**Goal**: Compute pairwise correlations between all metric pairs, fit fixed-effects regression models to predict discrepancies from dataset characteristics, perform bootstrap resampling for confidence intervals

**Independent Test**: Can be fully tested by running the analysis pipeline on existing metric outputs and verifying correlation matrices, regression coefficients, and bootstrap confidence intervals are generated, delivering the final research artifacts

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Contract test for correlation analysis in tests/contract/test_correlation_analysis.py
- [ ] T033 [P] [US3] Integration test for regression analysis in tests/integration/test_regression_analysis.py
- [ ] T034 [P] [US3] Unit test for Benjamini-Hochberg FDR correction in tests/unit/test_fdr_correction.py
- [ ] T035 [P] [US3] Unit test for bootstrap resampling in tests/unit/test_bootstrap.py

### Implementation for User Story 3

- [ ] T036 [P] [US3] Implement 05_correlation_analysis.py for Pearson and Spearman correlations between all metric pairs (≥15 pairs for 6 metrics) (FR-005)
- [ ] T037 [US3] Implement Benjamini-Hochberg FDR correction (α=0.05) for multiple-comparison adjustment (FR-005, SC-004)
- [ ] T037a [US3] Document correlation effect sizes (r values with Cohen's interpretation thresholds: small=0.1, medium=0.3, large=0.5) in correlations.csv and console output (Constitution Principle VII statistical rigor)
- [ ] T038 [US3] Store correlations in data/analysis/correlations.csv with p-values and q-values (FR-005)
- [ ] T039 [US3] Document mathematical dependencies in 05_correlation_analysis.py code comments AND correlations.csv metadata (exclusion_reason field) for DP-difference vs DI-ratio pair exclusion (plan.md Phase 3 Step 3)
- [ ] T039a [US3] Implement explicit exclusion of DP-difference vs DI-ratio correlation pairs due to theoretical mathematical dependency (plan.md Phase 3 Step 3)
- [ ] T040 [P] [US3] Implement 06_regression_analysis.py for OLS regression with dataset characteristics (feature dimensionality, class imbalance ratio) as predictors (FR-006)
- [ ] T040a [US3] Document OLS vs fixed-effects regression deviation from spec FR-006 with formal change justification referencing plan.md Phase 4 note on n=5 dataset limitation and power constraints (constraint preservation)
- [ ] T041 [US3] Apply VIF diagnostics and exclude predictors with VIF > 5 in 06_regression_analysis.py (FR-006)
- [ ] T042 [US3] Document effect sizes (Cohen's f², R², adjusted R²) and acknowledge n=5 dataset limitation in regression output (regression_results.csv columns AND console summary) (Constitution Principle VII statistical rigor, FR-006)
- [ ] T043 [US3] Include interpretation note acknowledging theoretical relationship between base rate difference and demographic parity difference per Constitution Principle VII in regression output console summary AND regression_results.csv interpretation_notes column (FR-006)
- [ ] T044 [US3] Store results in data/analysis/regression_results.csv with regression coefficients and VIF diagnostics (FR-006)
- [ ] T045 [P] [US3] Implement 07_bootstrap_analysis.py for bootstrap resampling (n=1000, reducible to n=500) (FR-007)
- [ ] T046 [US3] Compute confidence intervals for all correlation coefficients via bootstrap (FR-007, SC-003)
- [ ] T047 [US3] Log bootstrap iteration count and any reductions to logs/exclusion.log as computational constraint (FR-007)
- [ ] T048 [US3] Store bootstrap results in data/analysis/bootstrap_results.csv (FR-007)
- [ ] T049 [P] [US3] Implement 08_metric_guidance.py for associational guidance mapping (FR-009)
- [ ] T049a [US3] Document FR-009 terminology shift from "metric selection guidance" to "associational guidance" with FR-008 associational framing compliance rationale (spec.md FR-009 requirement)
- [ ] T050 [US3] Generate data/analysis/guidance.csv with associational mappings between dataset characteristics and metric values (FR-009)
- [ ] T051 [US3] Use associational language only: "associations between dataset characteristics and metric values" (NOT "recommended metrics") (FR-009)
- [ ] T052 [US3] Include explicit FR-008 disclaimer in guidance output (FR-008, FR-009)
- [ ] T053c [US3] Add disclaimer "Findings are associational only; no causal claims are made." to all US3 console output, correlation/regression reports, and guidance output (FR-008)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Associational Framing (Cross-Cutting Refinement) (Priority: P1)

**Purpose**: Ensure all outputs frame findings as associational only, no causal claims (FR-008 distributed throughout US1-US3; this phase is for summary verification)

**Independent Test**: Verify all reports and console output include disclaimer text: "Findings are associational only; no causal claims are made."

### Implementation for Associational Framing Verification

- [ ] T054 [US3] Review all documentation files (code/*.py, docs/*.md, data/analysis/*.csv) for prescriptive language and replace with associational framing; create verification checklist in tests/contract/test_framing_verification.py (FR-008)
- [ ] T055 [US3] Cross-reference FR-008 in FR-009 guidance output (FR-008, FR-009)
- [ ] T056 [US3] Document associational framing in module-level docstrings of all 0X_*.py files and FR-008 references in each script's output generation section (FR-008)

---

## Phase 7: Bootstrap Monitoring & Performance (Priority: P2)

**Purpose**: Ensure bootstrap analysis completes within 6-hour GHA job window with proactive iteration reduction

**Independent Test**: Verify bootstrap iterations adjust from 1000 to 500 at 5.5-hour threshold without timeout

### Implementation for Bootstrap Monitoring

- [ ] T059 [P] Performance optimization for bootstrap resampling within 6-hour GHA job window
- [ ] T059a [US3] Implement time-based iteration monitoring in 07_bootstrap_analysis.py with early termination at a predetermined duration; reduce iterations proactively based on elapsed time (FR-007, 6-hour constraint)

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T057 [P] Documentation updates in code/ and data/ with README explaining pipeline execution order
- [ ] T058 Code cleanup and refactoring across all modules: remove duplicate code, standardize error handling patterns, ensure consistent logging calls across all modules
- [ ] T060 [P] Additional unit tests in tests/unit/ for edge cases (missing variables, class imbalance >10:1, multicollinearity)
- [ ] T061 [P] Security hardening for dataset download URLs (validate against canonical sources): whitelist domains (archive.ics.uci.edu, github.com/numenta, datasets.load_dataset) with HTTP 200 status check and SHA-256 verification
- [ ] T062 [P] Run quickstart.md validation to verify end-to-end pipeline execution; if validation fails, log error to logs/quickstart_errors.log and generate diagnostic report in data/analysis/quickstart_diagnostic.json
- [ ] T063 [P] Verify all FR/SC coverage matrix items are implemented: generate FR/SC coverage matrix programmatically from code comments and test assertions, output to data/analysis/fr_sc_coverage.json
- [ ] T064 [P] Document power analysis limitations (n=15 observations, minimum detectable R²≈0.45) in research.md (SC-005)
- [ ] T064a [P] Create research.md in Phase 0 if not exists, then document power analysis limitations as referenced by plan.md Phase 0
- [ ] T065 [P] Verify dataset URLs are stable and accessible (UCI Adult, COMPAS, Bank Marketing, German Credit, Law School): curl test with HTTP status code check, record results in data/analysis/url_verification.csv with status codes and response times
- [ ] T066 [P] Add error handling for non-convergence in regression models with fallback to reduced predictor set in 06_regression_analysis.py (try/except around model.fit())

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data availability (preprocessed datasets required for model training)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 metrics availability (fairness metrics required for correlation/regression analysis)

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

### Data Flow Dependencies (CRITICAL)

- **T014-T019 (US1)**: Must complete before **T025-T031 (US2)** - datasets required for model training
- **T025-T031 (US2)**: Must complete before **T036-T052 (US3)** - fairness metrics required for analysis
- **T036-T039 (Correlation)**: Must complete before **T045-T048 (Bootstrap)** - correlations required for bootstrap CIs
- **T040-T044 (Regression)**: Independent of correlation but depends on US2 metrics

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset download in tests/contract/test_dataset_download.py"
Task: "Integration test for preprocessing pipeline in tests/integration/test_preprocessing.py"

# Launch all models for User Story 1 together:
Task: "Implement 01_data_acquisition.py for downloading UCI Adult, COMPAS, Bank Marketing, German Credit, Law School datasets via HTTP/HTTPS"
Task: "Implement seed pinning (random_state=42) throughout 01_data_acquisition.py for all stratified operations"
Task: "Implement 02_preprocessing.py for extracting binary protected attributes (gender=0/1, race=0/1) and binary outcomes"
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
   - Developer A: User Story 1 (Dataset Acquisition)
   - Developer B: User Story 2 (Fairness Metrics) - can start once US1 data available
   - Developer C: User Story 3 (Analysis) - can start once US2 metrics available
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
- **CPU-ONLY**: All tasks must run on CPU-only CI (limited cores, modest RAM, modest disk, NO GPU)
- **Dataset URLs**: Use real, reachable URLs (NAB CSVs, UCI, ucimlrepo, datasets.load_dataset)
- **Data Flow**: Tasks producing data must complete before tasks consuming that data
- **6-Hour Limit**: Bootstrap iterations may reduce from 1000 to 500 if time-constrained (log reduction)
- **Seed Pinning**: Constitution Principle I requires random_state=42 throughout code/ for reproducibility
- **Effect Sizes**: Constitution Principle VII requires Cohen's f², R², adjusted R² for regression and r values with interpretation for correlations
- **Associational Framing**: FR-008 disclaimer required in all outputs; no causal claims permitted
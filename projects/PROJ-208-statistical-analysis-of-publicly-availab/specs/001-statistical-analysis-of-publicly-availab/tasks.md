---
description: "Task list template for feature implementation"
---

# Tasks: Statistical Analysis of GitHub Issue Resolution Times

**Input**: Design documents from `/specs/001-github-issue-resolution/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/` at repository root
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

- [X] T001a [P] Create code/ directory at repository root
- [X] T001b [P] Create data/ directory at repository root with subdirectories: raw/, processed/, figures/
- [X] T001c [P] Create tests/ directory at repository root with subdirectories: contract/, integration/, unit/
- [X] T001d [P] Create state/ directory at repository root
- [X] T002 Initialize Python 3.11 project with pinned CPU-tractable dependencies in requirements.txt at projects/PROJ-208-statistical-analysis-of-publicly-availab/code/ (requests, pandas, numpy, scipy, statsmodels, pymer4, matplotlib, seaborn, pyyaml)
- [X] T003 [P] Configure linting and formatting tools: create ruff.toml and pyproject.toml config files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create configuration manager in code/utils/config.py (random seeds, paths, thresholds)
- [X] T005 [P] Implement GitHub API client with rate limit handling, exponential backoff, and explicit **wait ≥60 seconds** before resuming upon rate limit hits in code/utils/api_client.py (FR-001, US-1)
- [X] T006 [P] Setup schema validators against contracts/ in code/utils/validators.py (SC-001)
- [X] T027 [P] Create documentation: data-model.md (entity definitions), contracts/ (schema YAML files), AND quickstart.md (end-to-end run instructions) per plan.md Phase 1 outputs
- [X] T039 [P] Implement Reference-Validator Agent with explicit integration points (artifact write, Advancement-Evaluator, transition gate) and blocking logic for the `research_review` → `research_accepted` transition (Constitution Principle II)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Collection and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically collect closed issue data from multiple GitHub repositories and produce a clean, analysis-ready dataset with computed resolution times.

**Independent Test**: Run collection pipeline on a fixed set of repositories; verify output CSV contains ≥1000 issues with non-missing resolution times and all required feature columns (US1 acceptance scenario 1).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T007 [P] [US1] Contract test for dataset schema in tests/contract/test_dataset_schema.py
- [X] T008 [P] [US1] Integration test for API fetch with rate limit simulation in tests/integration/test_api_fetch.py

### Implementation for User Story 1

- [X] T047 [US1] Implement **Streaming Data Loader** in `code/data/loader.py` using `datasets.load_dataset(..., streaming=True)` to process the full real dataset in chunks, ensuring memory usage stays <7GB while avoiding synthetic sampling unless the full stream is impossible (Plan Phase 0, Constitution Principle II)

#### HuggingFace Loader (Atomic Steps)
- [ ] T009a-1 [US1] Implement **Schema Validator** for HuggingFace dataset in `code/data/validators_hf.py` to check `created_at`, `closed_at`, `labels`, `assignee`, `comments_count` presence and types (FR-001).
- [ ] T009a-2 [US1] Implement **HuggingFace Fetcher** in `code/data/loader_hf.py` to fetch `akhousker/github-issues` with `streaming=True` and error handling (FR-001).
- [ ] T009a-3 [US1] Implement **HF Writer** in `code/data/loader_hf.py` to write validated data to `data/raw/github_issues_raw_hf.parquet` (Plan Phase 0).

#### GitHub API Fallback Loader (Atomic Steps)
- [ ] T009b-1 [US1] Define **Curated Repository List** in `code/data/config.py` with a list of high-star repositories across ≥5 languages (Plan Phase 0.5).
- [ ] T009b-2 [US1] Implement **Dynamic Discovery** in `code/data/discovery.py` to search GitHub API for top-starred repos by language if the curated list is insufficient to reach a sufficient number of unique repos (FR-001).
- [ ] T009b-3 [US1] Implement **API Fetcher** in `code/data/loader_api.py` to collect closed issues (`state=closed`, `since=2020-01-01`) from the combined list (curated + discovered) with rate limit handling (FR-001).
- [ ] T009b-4 [US1] Implement **API Validator** in `code/data/validators_api.py` to validate fetched API data against `contracts/dataset.schema.yaml` (FR-001).

#### Data Source Orchestrator (Atomic Steps)
- [ ] T009c-1 [US1] Implement **HF Check Logic** in `code/collect/orchestrator.py` to verify HF dataset availability and validity (Plan Phase 0.5).
- [ ] T009c-2 [US1] Implement **API Fallback Trigger** in `code/collect/orchestrator.py` to invoke API fetch ONLY if HF is unavailable or invalid (Plan Phase 0.5).
- [ ] T009c-3 [US1] Implement **Merge Logic** in `code/collect/orchestrator.py` to merge HF and API data if both are used, ensuring unique repo count ≥100 (FR-001). **Dependency**: Must wait for output files from T009a-3 and T009b-4.
- [ ] T009c-4 [US1] Implement **Fatal Error Handler** in `code/collect/orchestrator.py` to raise a FATAL ERROR ONLY if HF is invalid AND API fallback (including discovery) fails to reach a sufficient number of unique repos (≥100) (FR-001).

- [X] T009d [US1] Implement **Fallback Strategy Documentation** in `docs/fallback_strategy.md` detailing the escalation path if the hard stop on the repository count (T009c) is triggered, including manual repository list expansion procedures (FR-001). **Dependency**: T009c.
- [X] T045 [US1] Implement **Repository Metadata Enrichment** script in `code/collect/enrich_metadata.py` to fetch `language`, `star_count`, and `contributor_count` for repositories in the dataset via GitHub API; Output to `data/processed/repo_metadata.json` with schema `{repo_id, language, star_count, contributor_count}` and merge `language` into the main dataset (Plan Phase 0.5, FR-001). **Dependency**: Must complete before T010.
- [X] T010 [US1] Implement preprocessing script in `code/collect/preprocess.py` to compute resolution_time_hours and exclude invalid issues (FR-002, FR-003). **Dependency**: T045.
- [ ] T011 [US1] Save cleaned dataset to `data/processed/cleaned_issues.csv` with checksum AND validate ≥95% completeness threshold per SC-001 by checking that columns `created_at`, `closed_at`, `labels`, `assignee`, and `comments_count` contain **non-null and non-empty values** for ≥95% of rows using `code/utils/validators.py` (defined in T006); Output validation report to `data/logs/completeness_report.json` (SC-001). **Note**: 'language' is explicitly EXCLUDED from this specific check to prevent false negatives from enrichment failures.
- [ ] T012 [US1] Add logging for excluded issues (negative resolution time, missing timestamps) to `data/logs/preprocessing.log` in JSON format (FR-003)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Descriptive Distribution Analysis (Priority: P2)

**Goal**: Generate empirical cumulative distribution plots and fit parametric distribution models (log-normal, Weibull).

**Independent Test**: Run distribution analysis on cleaned dataset; verify ECDF plots generated and fit quality metrics reported.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T013 [P] [US2] Unit test for log-transform handling of zero values in tests/unit/test_transforms.py
- [X] T014 [P] [US2] Integration test for distribution fitting output format in tests/integration/test_distributions.py

### Implementation for User Story 2

- [ ] T017a-1 [US2] Implement **IQR Quartile Calculation** in `code/data/cleaner.py` to calculate Q1 and Q3 on the global dataset of resolution times (FR-002, US-2).
- [ ] T017a-2 [US2] Implement **IQR Calculation** in `code/data/cleaner.py` to compute IQR = Q3 - Q1 (FR-002, US-2).
- [ ] T017a-3 [US2] Implement **IQR Flagging Logic** in `code/data/cleaner.py` to flag outliers using the standard interquartile range method (Q3 + 1.5*IQR) as the **sole** detection mechanism (FR-002, US-2).
- [X] T015 [P] [US2] Implement ECDF plot generation in `code/analysis/distribution_fitting.py` (x-axis log scale) (FR-002)
- [X] T016a [US2] Fit log-normal model using scipy.stats MLE, report KS statistic, p-value, and AIC (FR-002, US-2)
- [X] T016b [US2] Fit Weibull model using scipy.stats MLE, report KS statistic, p-value, and AIC (FR-002, US-2)
- [ ] T017 [US2] Detect and report extreme outliers using **IQR method (Q3 + 1.5*IQR)** as defined in Spec US-2 Acceptance Scenario 3; Report the **number of outliers** and their **percentage of the total dataset**; Output to `data/processed/outlier_report.json` (FR-002, US-2, Plan Phase 2). **Dependency**: Requires T017a-3.
- [X] T018 [US2] Save figures to `data/figures/` and results to `data/processed/distribution_metrics.json` (SC-002)

**Checkpoint**: At this point, At least User Story 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Hypothesis Testing and Regression Modeling (Priority: P3)

**Goal**: Execute ANOVA/Kruskal-Wallis tests, apply Holm-Bonferroni correction, and fit linear mixed-effects model.

**Independent Test**: Run hypothesis testing suite; verify p-values with effect sizes and confidence intervals reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US3] Contract test for analysis output schema in tests/contract/test_analysis_schema.py
- [X] T020 [P] [US3] Integration test for mixed-effects model convergence in tests/integration/test_mixed_effects.py

### Implementation for User Story 3

- [X] T021 [P] [US3] Implement Kruskal-Wallis test for programming language groups with **Holm-Bonferroni correction** for independent tests AND **Westfall-Young permutation** for label dependency (Plan Phase 2, FR-004, US-3); Output to `code/analysis/hypothesis_testing.py` (FR-004, US-3). **Note**: Westfall-Young is a primary deliverable per Plan.md.
- [X] T022 [P] [US3] Fit linear mixed-effects model with random intercepts for repository in `code/analysis/mixed_effects_model.py` (FR-005)
- [X] T023 [US3] Implement **-fold Stratified Cross-Validation by repository size** in `code/analysis/modeling.py` to generate MAE and R² metrics with standard deviation across folds (SC-004, US-3)
- [X] T024 [US3] Calculate VIF from full model design matrix, flag collinearity (VIF≥5), and enforce descriptive language for joint relationship (not independent effects) in `code/diagnostics/collinearity.py` (FR-006)

#### Sensitivity Analysis (Atomic Steps)
- [ ] T025a-1 [US3] Implement **Parametric Bootstrap Resampling** in `code/analysis/sensitivity.py` with `n_resamples=1000`, `random_state=42`, resampling Kruskal-Wallis statistics and LME coefficients (FR-007).
- [ ] T025a-2 [US3] Implement **Stability Proportion Calculation** in `code/analysis/sensitivity.py` to compute the proportion of significant resamples for each threshold within a range of conventional significance levels including 0.05 and 0.1 (FR-007).
- [ ] T025a-3 [US3] Write intermediate bootstrap samples to `data/processed/bootstrap_samples.pkl` (FR-007).
- [ ] T025b-1 [US3] Implement **Threshold Iteration Loop** in `code/analysis/sensitivity.py` to aggregate stability metrics across thresholds (FR-007).
- [ ] T025b-2 [US3] Implement **Intermediate Aggregation** in `code/analysis/sensitivity.py` to collect stability metrics (FR-007).
- [ ] T025b-3 [US3] Write intermediate results to `data/processed/sensitivity_sweep.json` (FR-007).
- [ ] T025c [US3] Generate **final stability proportion report** in `data/processed/sensitivity_report.json` with explicit schema: `{0.01: <float>, 0.05: <float>, 0.1: <float>}` representing the **proportion of bootstrap resamples significant** for each threshold (FR-007). **Dependency**: Requires T025b-3. **Note**: This is the definitive output; T025a outputs intermediate data. <!-- FAILED: unspecified -->

- [X] T026 [US3] Enforce "associational" or "correlational" language in all result text generation in `code/analysis/results.py` (FR-008)
- [X] T049 [US3] Update `code/analysis/mixed_effects_model.py` to implement **Dimensionality Reduction** for categorical variables: group labels with <1% frequency into an "Other" category before one-hot encoding to prevent singular matrices in VIF calculation (Plan Phase 2, FR-006)

#### Collinearity Report (Atomic Steps)
- [ ] T056-1 [US3] Implement **VIF Metric Extraction** in `code/diagnostics/collinearity.py` to extract VIF values from T024 output (FR-006).
- [ ] T056-2 [US3] Implement **Human-Readable Summary Formatting** in `code/diagnostics/collinearity.py` to list predictors with VIF≥5 and correlated pairs (FR-006).
- [ ] T056-3 [US3] Implement **Associational Language Injection** in `code/diagnostics/collinearity.py` to ensure all text in the report explicitly states "associational" or "correlational" (FR-008). **Dependency**: Requires T056-2.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Documentation, Validation & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, constitutional compliance, and final validation

- [X] T028 [P] Code cleanup and refactoring: run ruff check (zero warnings)
- [X] T042 [P] Achieve pytest coverage ≥80% with coverage report
- [X] T029 [P] Configure GitHub Actions workflow for CI (standard CPU allocation, sufficient RAM, h timeout) AND validate actual runtime stays within ≤6h constraint (FR-009, FR-010)
- [X] T030 [P] Run quickstart.md validation to ensure end-to-end reproducibility (SC-005)
- [X] T033 [P] Generate content hashes for all artifacts in data/, code/, state/ (Constitution Principle V)
- [X] T031 [P] Update state/projects/PROJ-208-statistical-analysis-of-publicly-availab.yaml with artifact hashes and updated_at timestamp (ISO 8601 format) on artifact changes (Constitution Principle V)
- [X] T032 [P] Validate reproducibility by re-running code/ against data/ on fresh GitHub Actions runner with identical outputs = matching checksums (Constitution Principle I)
- [X] T034 [P] Enforce reproducibility: verify code re-run produces identical outputs with checksums for data/, code/, state/ artifacts (Constitution Principle I)
- [X] T035 [P] Validate temporal data integrity: ensure timestamps from GitHub API stored unchanged AND record deterministic timezone script version in code/VERSION.txt (Constitution Principle VI)
- [X] T036 [P] Validate reproducible feature engineering: verify feature extraction scripts produce identical outputs AND explicitly declare API fields they read (Constitution Principle VII)
- [X] T037 [P] Validate data hygiene: verify checksums and run Repository-Hygiene Agent for PII scan (Constitution Principle III)
- [X] T038 [P] Run Repository-Hygiene Agent for PII scan enforcement in CI workflow with checkpoint verification (Constitution Principle III)
- [X] T040 [P] Validate single-source-of-truth traceability: verify all figures/statistics trace to exactly one data row and code block (Constitution Principle IV)
- [X] T041 [P] Validate all result text contains "associational" or "correlational" phrases per FR-008
- [X] T043 [P] **Execute** Reference-Validator Agent on all artifacts generated in Phases 3-5 (citations, data, code) as a blocking gate before `research_accepted` transition (Constitution Principle II)

**Checkpoint**: All constitutional principles validated, documentation complete, CI configured

---

## Phase 7: Revision & Gap Resolution (Addressing Analysis Findings)

**Purpose**: Address specific gaps identified during the analysis phase regarding data sourcing robustness, metadata enrichment, and statistical rigor.

**Note**: Tasks T045, T047, T049, T050, T052 have been moved to earlier phases to align with the plan. T055 was removed as the logic is now handled by T009c-4. T056 was split into atomic steps.

### Implementation for Revision Gaps

- [X] T053 [US1] Implement unit test in `tests/unit/test_fallback.py` to verify that the **GitHub API fallback** in T009c triggers correctly when HuggingFace dataset is unavailable (Plan Phase 0.5)
- [X] T054 [US3] Implement unit test in `tests/unit/test_hypothesis.py` to verify that **Holm-Bonferroni correction** is applied in T021 (Plan Phase 2)

**Checkpoint**: All identified analysis gaps and revision concerns addressed.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T027 (data-model.md, contracts/, quickstart.md) MUST precede T009-T026 (schema validation and entity definitions)
 - T039 (Reference-Validator Agent) MUST be in Phase 2 to enable checkpoint validation throughout research
 - T043 (Execute Reference-Validator) MUST be in Phase 6 to run after artifact generation
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (Phase 3)**: Must complete before US2 and US3 (data dependency)
 - **US2 (Phase 4)**: Requires cleaned dataset from US1 (Phase 3)
 - **US3 (Phase 5)**: Requires cleaned dataset from US1 (Phase 3)
- **Revision (Phase 7)**: Depends on completion of Phase 3-5 to address specific gaps found in analysis
- **Documentation & Validation (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires data output from US1 (Phase 3)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires data output from US1 (Phase 3)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- API Client/Utils before Collection
- Collection before Preprocessing
- Preprocessing before Analysis
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US2 and US3 can start in parallel (if team capacity allows), but both depend on US1 data
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (once data is ready)
- T016a and T016b share code/analysis/distribution_fitting.py; they can run in parallel if implemented as separate functions. **Note**: T016a and T016b are parallel *with each other*, but both must complete before T018 (Save results).
- T015 and T016a/T016b share code; T016a/T016b cannot run before T015 if they share the same file instance, but logically T015 (ECDF) and T016 (Fitting) are distinct steps.

### Ordering Notes

- T033 (generate hashes) MUST precede T031 (update state YAML with hashes)
- T027 (data-model.md, contracts/, quickstart.md) MUST be in Phase 2 to precede consumer tasks (T009-T026)
- T039 (Reference-Validator Agent) MUST be in Phase 2 to enable checkpoint validation throughout research
- T043 (Execute Reference-Validator) MUST be in Phase 6 to run after all artifacts are generated
- T011 (Save dataset) MUST precede T015-T026 (Analysis tasks)
- T016a/T016b (Fitting) MUST precede T018 (Save results)
- T023 (5-fold Stratified CV) MUST precede final model validation
- **T018 (Save figures) MUST precede T044 (Figure caption validation)** (Note: T044 removed)
- **T017 (Outlier detection) MUST precede T018 (Save results)**
- **T022 (Model fit) MUST precede T023 (5-fold Stratified CV)**
- **T045 (Metadata Enrichment) MUST precede T010 (Preprocessing)** to ensure 'language' is available for preprocessing. T045 MUST also precede T009c merge logic if the API fallback is used, ensuring the merged output contains 'language'.
- **T009c (Orchestrator) MUST precede T010 (Preprocessing)** to ensure data is fetched before cleaning.
- **T009a/T009b (Loaders) are conditional paths managed by T009c**, not parallel peers.
- **T009c (Orchestrator) depends on T009a and T009b completion** to avoid race conditions. Specifically, T009c must wait for the **output files** (`data/raw/github_issues_raw_hf.parquet`, `data/raw/github_issues_raw_api.parquet`) to be written by T009a and T009b.
- **T025c depends on T025b completion** to ensure report accuracy.
- **T056 (Collinearity Report) depends on T024 (VIF Calculation)** to ensure the report uses the calculated metrics.
- **T009d (Fallback Strategy Documentation) depends on T009c (Orchestrator)** to ensure the documentation reflects the final implementation.
- **T011 (Validation) does NOT depend on T045 (Enrichment)** as 'language' is excluded from the check.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset schema in tests/contract/test_dataset_schema.py"
Task: "Integration test for API fetch with rate limit simulation in tests/integration/test_api_fetch.py"

# Launch implementation for User Story 1:
Task: "Implement HF loader in code/data/loader_hf.py"
Task: "Implement API loader in code/data/loader_api.py"
Task: "Implement orchestrator in code/collect/orchestrator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify ≥1000 issues, valid resolution times, ≥95% completeness)
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Distribution Analysis) [Waits for US1 data from Phase 3]
 - Developer C: User Story 3 (Modeling) [Waits for US1 data from Phase 3]
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
- **Constraint**: All analysis must run on a standard CPU, sufficient memory GitHub Actions runner (no GPU, no 8-bit quantization)
- **Constraint**: Sensitivity analysis must calculate and report stability proportion (FR-007)
- **Constraint**: All result text must include "associational" or "correlational" (FR-008)
- **Constraint**: VIF≥5 must flag collinearity AND describe joint relationship as descriptive (FR-006)
- **Constraint**: Runtime must validate ≤6h completion (FR-009)
- **Constraint**: Dataset completeness must validate ≥95% threshold (SC-001)
- **Constraint**: Repository collection must enforce ≥100 minimum (FR-001)
- **Constraint**: Rate limit handling must wait ≥60 seconds (US-1)
- **Constraint**: Distribution fitting must cover BOTH log-normal and Weibull (US-2)
- **Constraint**: Outlier detection must use **IQR method (Q3 + 1.5*IQR)** as defined in Spec US-2 (overrides Plan's MAD mention) (US-2)
- **Constraint**: 5-fold Stratified CV by repository size must generate MAE/R² (SC-004)
- **Constraint**: Sensitivity thresholds must be set at {0.01, 0.05, 0.1} (FR-007)
- **Constraint**: Reference-Validator Agent must execute before research_accepted (Constitution II)
- **Constraint**: Data loader MUST raise a fatal exception ONLY if BOTH HuggingFace dataset and GitHub API fallback (including dynamic discovery) fail to meet the ≥100 repository requirement; the API fallback is the approved mechanism for HF failure, not a hard exit (T009c).
- **Constraint**: Metadata enrichment (language) is REQUIRED for hypothesis testing (Plan Phase 0.5) and must be present in the cleaned dataset (T010).
- **Constraint**: Holm-Bonferroni is primary for hypothesis tests; Westfall-Young is a primary deliverable per Plan.md (FR-004).
- **Constraint**: Dimensionality reduction (<1% frequency grouping) is REQUIRED for VIF calculation (Plan Phase 2).
- **Constraint**: Parametric Bootstrap is chosen for sensitivity analysis based on log-normal/Weibull distribution fit results from T016 (Plan Phase 2).
- **Constitutional Compliance**: All principles must be validated in Phase 6
- **Constitutional Compliance**: Reference-Validator Agent must verify three checkpoints (Principle II)
- **Constitutional Compliance**: Repository-Hygiene Agent must be used for PII scans (Principle III)
- **Constitutional Compliance**: All figures/statistics must trace to single data row and code block (Principle IV)
- **Constitutional Compliance**: updated_at timestamp must update on artifact changes (Principle V)
- **Constitutional Compliance**: Timezone script version must be recorded (Principle VI)
- **Constitutional Compliance**: Feature extraction scripts must declare API fields (Principle VII)
- **Scope Clarification**: FR-008 mandates "associational" or "correlational" language for "result text (including JSON reports and console logs)". This requirement DOES NOT apply to figure captions or titles. Task T044 was removed to align with this scope.
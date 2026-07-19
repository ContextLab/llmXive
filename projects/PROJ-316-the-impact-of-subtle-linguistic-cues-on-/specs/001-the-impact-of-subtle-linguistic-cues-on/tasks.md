# Tasks: The Impact of Subtle Linguistic Cues on Perceived Authenticity in AI Chatbots

**Input**: Design documents from `/specs/001-impact-of-subtle-linguistic-cues/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase -1: Setup (Blocking Prerequisites)

**Purpose**: Project initialization, directory structure, and linting. **These tasks MUST be complete before any code implementation.**

- [ ] T002 [P] Create project directory structure. **Deliverable**: Create the following directories: `src/`, `src/extraction/`, `src/analysis/`, `src/utils/`, `tests/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `data/raw/`, `data/processed/`, `data/results/`, `contracts/`. Create empty `__init__.py` files in all `src/` and `tests/` subfolders. **Note**: This task is a blocking prerequisite for all code tasks.
- [ ] T004 [P] Configure linting and formatting. **Deliverable**: Create `.flake8` config file and `pyproject.toml` (or `setup.cfg`) with `black` configuration. **Note**: This task is a blocking prerequisite for all code tasks.

## Phase -2: Power Analysis (Prerequisite Gate)

**Purpose**: Determine required sample size (N) for the regression model to achieve power ≥ 0.8 (FR-011) before any annotation or analysis begins.

- [X] T000 [Phase-2] Implement and run power analysis script. **Deliverable**: Create `data/results/power_analysis_results.yaml` containing the required sample size N based on assumed effect size (f²) from literature. **Gate**: If required N > annotation budget, flag project as underpowered. **Dependency**: Must complete before Phase 0.

---

## Phase 0: Data Acquisition & Annotation (Blocking Prerequisites)

**Purpose**: Secure human authenticity ratings and validate the hedge lexicon required by FR-001, FR-010, FR-011. This phase MUST complete before Phase 1 or Phase 2 tasks can execute valid data loaders.

**⚠️ CRITICAL**: No downstream analysis (US2, US3) can proceed without verified `data/processed/ratings.csv` and passed lexicon validation.

- [X] T001a [Phase0] Verify availability of public dataset with human authenticity ratings. **Deliverable**: Create `data/raw/dataset_verification_report.md` containing: (1) Decision (Found/Not Found), (2) Source URL if found, (3) Sample size estimate, (4) If not found, confirmation of proceeding to annotation protocol. **Note**: If no dataset is found, document the decision to proceed to T001b.
- [X] T001b [Phase0] Define and document the manual annotation protocol. **Deliverable**: Create `data/raw/annotation_instructions.md` containing: (1) Likert scale definitions (1-5 Authenticity), (2) Instruction script for raters, (3) Sample items demonstrating the rating criteria. **Note**: Instructions must focus strictly on "Perceived Authenticity" as defined in spec.md.
- [ ] T001c [Phase0] [US1] Generate a "Gold Standard" subset of 50 annotated turns. **Deliverable**: Create `data/processed/gold_standard_50.csv` with columns `conversation_id`, `text_content`, `authenticity_score`, `rater_id`, and `timestamp`. **Execution**: If a public dataset is not found, use a simple CSV-based manual entry script (to be created in `src/utils/annotation_tool.py` in T002) to annotate 50 randomly selected turns from the raw corpus. **Constitution Requirement**: Store the full rater metadata (scale, instructions, inter-rater reliability) in `data/raw/rater_metadata.json` as per Constitution Principle VII. **Failure Path**: If inter-rater reliability (Cohen's Kappa) < 0.6, flag the dataset and halt.
- [ ] T001d [Phase0] [US1] [FR-010] Execute pragmatic validation of the hedge lexicon on the Gold Standard. **Deliverable**: Run the extraction logic on `data/processed/gold_standard_50.csv`. Calculate precision = (Lexicon Matches ∩ Human Matches) / Lexicon Matches. **Input**: 'Human Matches' are derived from the `gold_labels` column (manually annotated) in the 50-turn subset. **Gate**: If precision < 0.8, flag dataset for manual review in `data/results/lexicon_validation_results.yaml`. **Dependency**: Must complete after T001c (Gold Standard generation). <!-- FAILED: unspecified -->
- [X] T001e [Removed] **Note**: Task T001e ("Noise Measurement") was removed as it is not authorized by spec.md.

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Dependencies**: Phase 0 (T001c) must complete first.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete AND Phase 0 has produced `data/processed/gold_standard_50.csv` and `data/processed/ratings.csv`.

- [ ] T005 [P] [US1] Implement `src/utils/io.py`. **Deliverable**: Implement functions `fetch_text()` (returns DataFrame), `load_ratings()` (returns DataFrame), and `validate_schemas()` (raises exception if schema mismatched). **Specifics**: `validate_schemas()` MUST load `contracts/extracted_features.schema.yaml` and perform strict validation (no missing columns, correct types). **Note**: This task strictly depends on Phase 0 completion (T001c) and must halt if `ratings.csv` is missing.
- [ ] T005a [P] [US1] Implement Input Validation Logic (FR-006). **Deliverable**: Create `src/utils/validation.py` containing `validate_input_columns(df, required_cols)` which checks for 'text_content' and 'authenticity_score' columns. **Logic**: Raise a clear `ValueError` if columns are missing or mismatched, as mandated by FR-006.
- [ ] T006 [P] [US1] Create `src/config.py` to manage random seeds (default value) and runtime limits (CPU-only, bounded timeout).
- [ ] T007 [P] [US1] Implement `src/utils/edge_case_handler.py` to detect empty/short texts (<5 words) and missing ratings. **Deliverable**: If missing ratings are detected, the handler MUST perform **listwise deletion** (drop rows with NaN authenticity_score), log the count of dropped rows, and report the final sample size. **Note**: This task aligns with FR-007 and Edge Cases; it MUST NOT trigger a pipeline HALT.

---

## Phase 2: User Story 1 - Automated Linguistic Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Extract quantitative metrics (pronoun count, hedge count, valence) from raw conversation text.

**Independent Test**: A researcher runs the extraction script on a provided JSONL file of dummy conversations and receives a CSV output with exactly the spec-defined columns (`first_person_count`, `hedge_count`, `hedge_ratio`, `sentiment_score`) populated with numeric values, verified by spot-checking against manual counts.

### Implementation for User Story 1

- [ ] T009 [P] [US1] Implement `src/extraction/pronoun_extractor.py` using `nltk` (POS tagging) to calculate `first_person_count`. **Specifics**: Use NLTK POS tags 'PRP' (personal pronoun) and 'PRP$' (possessive pronoun). Count occurrences of: I, me, my, mine, we, us, our, ours. **Input**: `data/raw/conversations.jsonl`. **Output**: Intermediate count data. <!-- FAILED: unspecified -->
- [ ] T010 [P] [US1] Implement `src/extraction/hedge_extractor.py` using `NLTK` and the predefined 15-word hedge lexicon to calculate `hedge_count` and `hedge_ratio`. **Specifics**: The lexicon is: ["maybe", "perhaps", "possibly", "probably", "likely", "unlikely", "seem", "seems", "appear", "appears", "believe", "think", "guess", "suppose", "assume"]. **Input**: `data/raw/conversations.jsonl`. **Output**: Intermediate count data.
- [ ] T011 [P] [US1] Implement `src/extraction/sentiment_analyzer.py` using `vaderSentiment` (v3.3.2) to calculate `sentiment_score` (composite score -1.0 to 1.0). **Input**: `data/raw/conversations.jsonl`. **Output**: Intermediate score data.
- [ ] T012 [US1] Implement `src/main.py` (extraction mode). **Deliverable**: Add `--mode extraction` CLI argument, orchestrate T009-T011, handle edge cases (T007), and output `data/processed/features.csv` with columns `conversation_id`, `first_person_count`, `hedge_count`, `hedge_ratio`, `sentiment_score`. **Explicit Requirement**: The final CSV MUST include the `hedge_ratio` column as mandated by FR-008. **Dependency Note**: This task must wait for the completion of T005 (io.py implementation) and T009-T011 (modules). It does NOT depend on T001c (ratings) as extraction only requires raw text.
- [ ] T014 [US1] Write unit tests in `tests/unit/test_extraction.py` verifying metric calculations against manual spot-checks (US-1 Acceptance 1-3).

---

## Phase 3: User Story 2 - Associational Correlation Analysis (Priority: P2)

**Goal**: Compute Pearson and Spearman correlations between linguistic features and human authenticity ratings, with multiple-comparison correction.

**Independent Test**: A researcher runs the analysis module on the extracted CSV and a ratings CSV, generating a correlation matrix and scatter plots with p-values and effect sizes, strictly labeled as "associated with".

### Implementation for User Story 2

- [ ] T015 [P] [US2] Implement `src/analysis/correlation.py` to compute Pearson and Spearman coefficients between linguistic features (`first_person_count`, `hedge_count`, `sentiment_score`) and `authenticity_score` (FR-002). **Note**: Uses the single 'authenticity_score' as defined in spec.md.
- [ ] T016 [P] [US2] Implement Benjamini-Hochberg multiple-comparison correction in `src/analysis/correlation.py` (SC-004, FR-004).
- [ ] T017 [US2] Implement `src/main.py` (correlation mode) to merge `features.csv` and `ratings.csv`, handle missing ratings (FR-007), and output `data/derived/correlation_results.csv`.
- [ ] T018 [US2] Generate scatter plots (matplotlib/seaborn) for selected features. **Deliverable**: Create `data/derived/scatter_hedge_vs_authenticity.png` and `data/derived/scatter_pronoun_vs_authenticity.png` with clear "Association, not Causation" labels.
- [ ] T019 [US2] Write unit tests in `tests/unit/test_correlation.py` verifying p-values and effect sizes against known synthetic datasets.
- [ ] T020 [US2] Write integration test in `tests/integration/test_correlation_pipeline.py` ensuring the "association only" disclaimer is present in all outputs (FR-004).
- [X] T020a [US2] [Removed] **Note**: Task T020a ("Noise Measurement") was removed as it is not authorized by spec.md.
- [X] T020b [US2] [Removed] **Note**: Task T020b ("Dual-Outcome Correlation") was removed as it contradicts spec.md FR-001/FR-003.

---

## Phase 4: User Story 3 - Multivariate Regression with Controls (Priority: P3)

**Goal**: Fit a multiple linear regression model predicting authenticity from linguistic features, controlling for length/turn count, with VIF and non-linearity diagnostics.

**Independent Test**: A researcher executes the regression script and receives a summary table showing coefficients, standard errors, p-values, adjusted R², and VIF reports.

### Implementation for User Story 3

- [ ] T021 [US3] Implement `src/analysis/regression.py` to fit multiple linear regression. **Logic**: 1) Calculate VIF for all predictors; if VIF > 5, exclude the predictor with the highest VIF and log the specific excluded variable. 2) Test for non-linear relationships (quadratic terms for `hedge_count` and interaction terms `hedge_count` × `sentiment_score`) as per FR-009. **Inclusion Criteria**: Include non-linear terms if p < 0.10 (exploratory) or if AIC improves. 3) Run regression with linguistic features as predictors and conversation length/turn count as covariates (FR-003). **Note**: Outcome variable is strictly 'authenticity_score' per spec.md.
- [ ] T022 [US3] Implement `src/main.py` (regression mode) to orchestrate T021, calculate adjusted R² and AIC, and output `data/derived/regression_results.csv`. **Dependency**: T021 must complete first.
- [ ] T023 [US3] Generate diagnostic plots (residuals, VIF bar chart) for the regression model. **Note**: This task is for diagnostic plots (residuals/VIF) only, not the feature importance bar chart required by FR-005.
- [ ] T024 [US3] Write unit tests in `tests/unit/test_regression.py` verifying VIF calculation, exclusion logic, and adjusted R² logic.
- [ ] T025 [US3] Write integration test in `tests/integration/test_regression_pipeline.py` ensuring model constraints (VIF < 5, p < 0.05) are met.
- [ ] T026 [US3] Implement `src/analysis/sensitivity.py` to perform the **leave-one-out sensitivity analysis** (SC-003). **Logic**: Iterate through the 15-word hedge lexicon; for each iteration, remove one word, re-run the regression model (T021), and record the change in Adjusted R² and the significance (p < 0.05) of the remaining hedge count. **Deliverable**: Output `data/results/sensitivity_analysis.csv` and a `data/results/sensitivity_stability_report.md` summarizing the robustness of the findings. **Intermediate**: Save intermediate results to `data/results/sensitivity_iteration_*.csv` for each iteration.
- [X] T027 [Removed] **Note**: Task T027 (replacing 'authenticity' with 'trust') was removed as it contradicts spec.md FR-001.
- [X] T028 [US3] [Removed] **Note**: Task T028 ("Dual-Outcome Regression") was removed as it contradicts spec.md FR-001/FR-003.
- [X] T028b [US3] [Removed] **Note**: Task T028b ("Dual-Outcome Regression") was removed as it contradicts spec.md FR-001/FR-003.

---

## Phase 5: Visualization & Reporting (Priority: P3)

**Goal**: Generate publication-quality plots and the statistical summary report required by FR-005 and Plan Phase 6.

- [ ] T033 [P] [US3] Implement `src/analysis/visualize.py` to generate the **bar chart of feature importance coefficients** required by FR-005. **Deliverable**: Create `data/results/feature_importance_bar.png`. **Note**: This is distinct from T023 (diagnostic plots).
- [ ] T034 [P] [US3] Implement `src/analysis/report.py` to generate the **statistical summary report**. **Deliverable**: Create `data/results/report.md` with the following structure: 1. Executive Summary, 2. Methodology, 3. Results (Adjusted R², Coefficients, P-values), 4. Sensitivity Analysis, 5. Conclusion (Association, not Causation). **Note**: This task fulfills Plan Phase 6 and FR-005 reporting requirements.
- [ ] T035 [US3] Integrate visualization and report generation into `src/main.py` (report mode). **Deliverable**: Add `--mode report` CLI argument to orchestrate T033 and T034.
- [X] T035a [US3] [Removed] **Note**: Task T035a (Operational Definitions for Dual-Self) was removed as it is not required by spec.md.
- [X] T035b [US3] [Removed] **Note**: Task T035b (Noise Analysis) was removed as it is not required by spec.md.
- [X] T036 [US3] [Removed] **Note**: Task T036 (Operational Definitions for Dual-Self) was removed as it is not required by spec.md.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Documentation updates in `docs/` (including operational definitions). **Note**: T028 previously covered report generation; that responsibility is now in T034.
- [ ] T030 Code cleanup and refactoring to ensure modularity
- [ ] T031 [P] Run full pipeline validation on a sample of conversations (as per SC-005) to verify runtime constraint. **Deliverable**: Record execution time in `data/derived/performance_metrics.json`.
- [ ] T032 [P] Final verification that all outputs include the mandatory disclaimer: "These results indicate association, not causation." (FR-004)
- [X] T033 [Removed] **Note**: Task T032 (Noise Report) was removed as it is not required by spec.md.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase -2 (Power Analysis)**: No dependencies - can start immediately. **MUST complete before Phase 0.**
- **Phase 0 (Data Acquisition)**: Depends on Phase -2. **MUST complete before Phase 1.**
- **Phase -1 (Setup)**: No dependencies - can start immediately.
- **Phase 1 (Foundational)**: Depends on Setup (Phase -1) AND Phase 0 completion (requires `data/processed/gold_standard_50.csv`). BLOCKS all user stories.
- **User Stories (Phase 2-4)**: All depend on Foundational phase completion.
 - **Phase 2 (US1)**: Must complete before Phase 3 and 4 (data generation).
 - **Phase 3 (US2)**: Depends on Phase 2 (features) and Phase 0 (ratings).
 - **Phase 4 (US3)**: Depends on Phase 2 (features) and Phase 3 (correlation insights).
- **Phase 5 (Visualization/Reporting)**: Depends on Phase 4 (Regression results).
- **Polish (Final Phase)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories.
- **User Story 2 (P2)**: Depends on US1 (features) and Phase 0 (ratings).
- **User Story 3 (P3)**: Depends on US1 (features) and US2 (correlation context).

### Within Each User Story

- Models/Extractors (T009-T011) before orchestration (T012).
- Tests (T014, T019, T024) should be written first (TDD) and fail before implementation.

### Parallel Opportunities

- T009, T010, T011 (Extraction modules) can run in parallel.
- T015, T016 (Correlation logic) can run in parallel with T021 (Regression logic) if data is available, provided T021 includes VIF/non-linearity checks.
- T001a, T001b (Data acquisition) can run in parallel with Phase -1 (Setup).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase -2: Power Analysis.
2. Complete Phase -1: Setup.
3. Complete Phase 0: Data Acquisition (secure ratings, validate lexicon).
4. Complete Phase 1: Foundational (loaders).
5. Complete Phase 2: User Story 1 (Extraction).
6. **STOP and VALIDATE**: Test extraction on dummy data (T014).
7. Verify `features.csv` is generated correctly with spec-compliant columns.

### Incremental Delivery

1. Complete Phase -2 + Setup + Phase 0 + Foundational → Foundation ready.
2. Add User Story 1 → Test independently → `features.csv` ready.
3. Add User Story 2 → Test independently → Correlation results ready.
4. Add User Story 3 → Test independently → Regression and Sensitivity results ready.
5. Add Phase 5 → Generate reports and plots.
6. Polish & Report.

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase -2 + Setup + Phase 0 + Foundational together.
2. Once Foundational is done:
 - Developer A: User Story 1 (Extraction)
 - Developer B: User Story 2 (Correlation)
 - Developer C: User Story 3 (Regression + Sensitivity)
3. Team: Phase 5 (Visualization/Reporting).
4. Integrate and validate.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- **Critical Constraint**: No statistical analysis (US2/US3) proceeds without verified human authenticity ratings (FR-009) and passed lexicon validation (FR-010). If `ratings.csv` is missing or lexicon validation fails, the pipeline must halt gracefully.
- **Data Integrity**: All tasks must use real data from verified sources (HuggingFace) or explicitly defined annotation protocols. No synthetic/fake data generation for input.
- **Verification**: Verify tests fail before implementing. Commit after each task or logical group.
- **Review Resolution**: Tasks have been updated to strictly align with spec.md FR-001, FR-003, FR-009, FR-010, FR-011, and SC-003. Scope creep (Dual-Self, Noise Measurement, Trust Metrics) has been removed.
- **Spec Alignment**: All tasks now strictly use 'authenticity_score' as the outcome variable.
- **New Reviewer Concerns Addressed**:
 - **Circular Dependency**: Resolved by splitting T001c (Gold Set) and T001d (Validation).
 - **Scope Creep**: Removed all 'Experiencing/Remembering' and 'Noise' tasks.
 - **Edge Cases**: Updated T007 to implement listwise deletion.
 - **Executability**: Added specific lexicon, POS tags, and schema paths to tasks.
 - **Stability Report**: Added to T026 to satisfy SC-003.
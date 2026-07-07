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

## Phase 0: Data Acquisition & Annotation (Blocking Prerequisites)

**Purpose**: Secure human authenticity ratings required by FR-009 and SC-006. This phase MUST complete before Phase 1 or Phase 2 tasks can execute valid data loaders.

**⚠️ CRITICAL**: No downstream analysis (US2, US3) can proceed without verified `data/processed/ratings.csv`.

- [X] T001a [Phase0] Verify availability of public dataset with human authenticity ratings; if none exists, proceed to T001b. **Deliverable**: Create `data/raw/dataset_verification_report.md` documenting the decision and source URL.
- [X] T001b [Phase0] Define and document the manual annotation protocol: Create `data/raw/annotation_instructions.md` containing the Likert scale definitions (1-5 Authenticity) and the script template for the annotation interface.
- [X] T001c [US2] [Phase0] Execute annotation or fetch rated dataset, calculate Krippendorff's alpha (target ≥ 0.7), and generate `data/processed/ratings.csv` with columns `conversation_id`, `authenticity_score`, and `rater_id`. Save reliability metrics to `data/derived/reliability_metrics.json`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T002 Create project structure per implementation plan. **Deliverable**: Create directories `src/`, `tests/`, `data/raw`, `data/processed`, `data/derived`, `code/`. Create empty `__init__.py` files in all `src/` subfolders.
- [X] T003 Initialize Python 3.11 project with `requirements.txt`. **Deliverable**: Create `code/requirements.txt` containing pinned versions of `spaCy==3.5.0`, `nltk==3.8.0`, `vaderSentiment==3.3.2`, `pandas`, `scikit-learn`, `statsmodels`, `scipy`, `matplotlib`, `seaborn`, `krippendorff`.
- [ ] T004 [P] Configure linting (flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete AND Phase 0 has produced `data/processed/ratings.csv`.

- [ ] T005 [P] Setup data directory structure (`data/raw`, `data/processed`, `data/derived`)
- [ ] T006 [Phase2] Implement `src/utils/data_loader.py`. **Deliverable**: Implement functions `fetch_text()` (returns DataFrame), `load_ratings()` (returns DataFrame), and `validate_schemas()` (raises exception if `ratings.csv` is missing or schema mismatched). **Note**: This task depends on Phase 0 completion (T001c) and must halt if `ratings.csv` is missing.
- [~] T007 [P] Create `src/config.py` to manage random seeds (default value) and runtime limits (CPU-only, bounded timeout)
- [~] T008 [P] Implement `src/utils/edge_case_handler.py` to detect empty/short texts (<5 words) and missing ratings, logging exclusions per FR-006/FR-007
- [~] T009 [P] Setup `tests/unit/` and `tests/integration/` directories with `pytest` configuration

---

## Phase 3: User Story 1 - Automated Linguistic Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Extract quantitative metrics (pronoun rate, hedge density, valence) from raw conversation text.

**Independent Test**: A researcher runs the extraction script on a provided JSONL file of dummy conversations and receives a CSV output with exactly 3 new columns populated with numeric values, verified by spot-checking against manual counts.

### Implementation for User Story 1

- [~] T010 [P] [US1] Implement `src/extraction/pronoun_extractor.py` using `spaCy` (`en_core_web_sm` v3.5) to calculate `pronoun_rate` (first-person pronouns / total words)
- [~] T011 [P] [US1] Implement `src/extraction/hedge_extractor.py` using `NLTK` and a predefined hedge lexicon to calculate `hedge_density`
- [~] T012 [P] [US1] Implement `src/extraction/sentiment_analyzer.py` using `vaderSentiment` (v3.3.2) to calculate `valence_score` (-1.0 to 1.0)
- [~] T013 [US1] Implement `src/main.py` (extraction mode). **Deliverable**: Add `--mode extraction` CLI argument, orchestrate T010-T012, handle edge cases (T008), and output `data/processed/features.csv` with columns `conversation_id`, `pronoun_rate`, `hedge_density`, `valence_score`. **Dependency Note**: This task must wait for the completion of T006 (data_loader implementation) before execution to ensure data loading functions are available.
- [~] T014 [US1] Add validation logic to `src/main.py` (extraction mode) to detect extreme skewness (Shapiro-Wilk). **Deliverable**: Write `data/derived/extraction_flags.json` containing keys: `feature_name`, `p_value`, `is_skewed`, `suggested_transformation` per FR-008.
- [~] T015 [US1] Write unit tests in `tests/unit/test_extraction.py` verifying metric calculations against manual spot-checks (US-1 Acceptance 1-3)

---

## Phase 4: User Story 2 - Associational Correlation Analysis (Priority: P2)

**Goal**: Compute Pearson and Spearman correlations between linguistic features and human authenticity ratings, with multiple-comparison correction.

**Independent Test**: A researcher runs the analysis module on the extracted CSV and a ratings CSV, generating a correlation matrix and scatter plots with p-values and effect sizes, strictly labeled as "associated with".

### Implementation for User Story 2

- [~] T016 [P] [US2] Implement `src/analysis/correlation.py` to compute Pearson and Spearman coefficients between linguistic features and `authenticity_score` (FR-002)
- [~] T017 [P] [US2] Implement Benjamini-Hochberg multiple-comparison correction in `src/analysis/correlation.py` (SC-004)
- [~] T018 [US2] Implement `src/main.py` (correlation mode) to merge `features.csv` and `ratings.csv`, handle missing ratings (FR-007), and output `data/derived/correlation_results.csv` <!-- ATOMIZE: requested -->
- [~] T019 [US2] Generate scatter plots (matplotlib/seaborn) for selected features. **Deliverable**: Create `data/derived/scatter_hedge_vs_authenticity.png` and `data/derived/scatter_pronoun_vs_authenticity.png` with clear "Association, not Causation" labels. <!-- FAILED: unspecified -->
- [~] T020 [US2] Implement `src/utils/rating_validator.py` to calculate Krippendorff's alpha (target ≥ 0.7) for inter-rater reliability (FR-009, SC-006). **Deliverable**: Write alpha value to `data/derived/reliability_metrics.json`.
- [~] T021 [US2] Write unit tests in `tests/unit/test_correlation.py` verifying p-values and effect sizes against known synthetic datasets
- [~] T022 [US2] Write integration test in `tests/integration/test_correlation_pipeline.py` ensuring the "association only" disclaimer is present in all outputs (FR-004)

---

## Phase 5: User Story 3 - Multivariate Regression with Controls (Priority: P3)

**Goal**: Fit a multiple linear regression model predicting authenticity from linguistic features, controlling for length/turn count, with VIF and non-linearity diagnostics.

**Independent Test**: A researcher executes the regression script and receives a summary table showing coefficients, standard errors, p-values, adjusted R², and VIF reports.

### Implementation for User Story 3

- [ ] T023 [P] [US3] Implement `src/analysis/regression.py` to fit multiple linear regression with linguistic features as predictors and conversation length/turn count as covariates (FR-003)
- [ ] T024 [P] [US3] Implement VIF calculation in `src/analysis/regression.py` to detect multicollinearity (FR-005, SC-003)
- [ ] T025 [P] [US3] Implement non-linearity testing (quadratic terms/splines) in `src/analysis/regression.py` (FR-010)
- [ ] T026 [US3] Implement `src/main.py` (regression mode) to orchestrate T023-T025, calculate adjusted R² and AIC, and output `data/derived/regression_results.csv`
- [ ] T027 [US3] Generate diagnostic plots (residuals, VIF bar chart) for the regression model
- [ ] T028 [US3] Write unit tests in `tests/unit/test_regression.py` verifying VIF calculation and adjusted R² logic
- [ ] T029 [US3] Write integration test in `tests/integration/test_regression_pipeline.py` ensuring model constraints (VIF < 5, p < 0.05) are met

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `docs/` (including operational definitions)
- [ ] T031 Code cleanup and refactoring to ensure modularity
- [ ] T032 [P] Run full pipeline validation on a sample of conversations (as per SC-005) to verify -hour runtime constraint. **Deliverable**: Record execution time in `data/derived/performance_metrics.json`.
- [ ] T033 [P] Final verification that all outputs include the mandatory disclaimer: "These results indicate association, not causation." (FR-004)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Data Acquisition)**: No dependencies - can start immediately. **MUST complete before Phase 2.**
- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) AND Phase 0 completion (requires `data/processed/ratings.csv`). BLOCKS all user stories.
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion.
 - **Phase 3 (US1)**: Must complete before Phase 4 and 5 (data generation).
 - **Phase 4 (US2)**: Depends on Phase 3 (features) and Phase 0 (ratings).
 - **Phase 5 (US3)**: Depends on Phase 4 (correlation insights) and Phase 3.
- **Polish (Final Phase)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories.
- **User Story 2 (P2)**: Depends on US1 (features) and Phase 0 (ratings).
- **User Story 3 (P3)**: Depends on US1 (features) and US2 (correlation context).

### Within Each User Story

- Models/Extractors (T010-T012) before orchestration (T013).
- Tests (T015, T021, T028) should be written first (TDD) and fail before implementation.

### Parallel Opportunities

- T010, T011, T012 (Extraction modules) can run in parallel.
- T016, T017 (Correlation logic) can run in parallel with T023-T025 (Regression logic) if data is available.
- T001a, T001b (Data acquisition) can run in parallel with Phase 1 (Setup).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 0: Data Acquisition (secure ratings).
3. Complete Phase 2: Foundational (loaders).
4. Complete Phase 3: User Story 1 (Extraction).
5. **STOP and VALIDATE**: Test extraction on dummy data (T015).
6. Verify `features.csv` is generated correctly.

### Incremental Delivery

1. Complete Setup + Phase 0 + Foundational → Foundation ready.
2. Add User Story 1 → Test independently → `features.csv` ready.
3. Add User Story 2 → Test independently → Correlation results ready.
4. Add User Story 3 → Test independently → Regression results ready.
5. Polish & Report.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Phase 0 + Foundational together.
2. Once Foundational is done:
 - Developer A: User Story 1 (Extraction)
 - Developer B: User Story 2 (Correlation)
 - Developer C: User Story 3 (Regression)
3. Integrate and validate.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- **Critical Constraint**: No statistical analysis (US2/US3) proceeds without verified human authenticity ratings (FR-009). If `ratings.csv` is missing, the pipeline must halt gracefully.
- **Data Integrity**: All tasks must use real data from verified sources (HuggingFace) or explicitly defined annotation protocols. No synthetic/fake data generation for input.
- **Verification**: Verify tests fail before implementing. Commit after each task or logical group.
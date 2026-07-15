# Tasks: The Impact of Narrative Perspective on Empathy and Moral Judgement

**Input**: Design documents from `/specs/001-narrative-perspective-empathy/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (directories: `code/`, `data/`, `tests/`, `artifacts/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (spaCy, scikit-learn, pandas, numpy, matplotlib, statsmodels, langdetect, pyyaml, requests)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` for paths, seeds (`np.random.seed(42)`), and hyperparameters
- [X] T005 [P] Implement `code/utils.py` function `scan_for_pii(text)` to detect PII; this logic is intended to be invoked by the CI Repository-Hygiene Agent as a blocking gate (Constitution Principle III)
- [ ] T006 [P] Implement `code/utils.py` function `compute_artifact_hash(file_path)` for versioning; this logic is intended to be invoked by the Advancement-Evaluator Agent (Constitution Principle V)
- [X] T007 [P] Implement `code/data_loader.py` to fetch real external datasets (OSF, Moral Foundations Twitter, Project Gutenberg) via verified URLs
- [X] T008 Create base data models (`StoryDocument`, `ReaderResponse`) in `code/models.py`
- [~] T009 Setup CI environment configuration for GitHub Actions (CPU-only, 7GB RAM limit)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Perspective Feature Extraction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically extract narrative perspective markers (pronoun density, focalization cues) from a corpus of public short stories.

**Independent Test**: The pipeline can be tested by processing a small, manually annotated sample of 10 stories and verifying that the computed "first-person density" scores correlate ≥ 0.8 with human annotations of perspective type.

### Tests for User Story 1

- [~] T010 [US1] Validation test: Process a manually annotated gold-standard subset of **50 stories** and verify that the computed "first-person density" scores correlate ≥ 0.8 with human annotations, satisfying SC-001. <!-- ATOMIZE: requested -->
- [X] T011 [P] [US1] Unit test for language detection and skipping non-English text in `tests/test_extraction.py` (logic verification on small sample)
- [X] T012 [P] [US1] Integration test for full pipeline on a sample of 10 stories in `tests/integration/test_extraction_flow.py`

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/extraction.py` function `calculate_pronoun_density(text)` using spaCy (FR-001)
- [X] T014 [US1] Implement `code/extraction.py` function `calculate_narrator_distance_score(text)` (FR-001)
- [X] T015 [US1] Implement `code/extraction.py` function `extract_perspective_features(file_path)` handling edge cases (<50 words, mixed language)
- [~] T016 [US1] Create `code/main.py` entry point to run extraction on the `data/raw/` corpus and output JSON records to `data/processed/perspective_features.json`
- [~] T017 [US1] Add validation logic to flag "neutral/omniscient" texts where `pronoun_density_1st` is 0.0
- [ ] T018 [US1] Add logging for extraction quality warnings (e.g., "data_quality_insufficient")

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Pilot Validation: Text Similarity Matching Logic (Priority: P2)

**Goal**: Validate the text-similarity matching algorithm by aligning processed stories with a "gold standard" set of story-judgement pairs.

**Independent Test**: The matching logic can be tested by running it against a "gold standard" subset of 50 manually annotated story-judgement pairs, verifying a precision ≥ 0.9.

### Tests for User Story 2

- [ ] T019 [P] [US2] Unit test for TF-IDF vector construction excluding pronouns in `tests/test_matching.py` (FR-008)
- [ ] T020 [P] [US2] Unit test for cosine similarity calculation and tie-breaking logic in `tests/test_matching.py`
- [ ] T021 [P] [US2] Integration test for matching on the 50-item gold standard set in `tests/integration/test_matching_flow.py`

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement `code/matching.py` function `build_tfidf_vectors(stories, exclude_pronouns=True)` (FR-002, FR-008)
- [ ] T023 [US2] Implement `code/matching.py` function `find_top_matches(query_vector, candidate_vectors, k=3)`
- [ ] T024 [US2] Implement `code/matching.py` function `apply_sensitivity_analysis(thresholds=[0.25, 0.30, 0.35, 0.40])` (FR-006). **Output Requirement**: Must generate a report detailing how the sample size and headline correlation coefficient vary across these thresholds to satisfy SC-003. **Validation**: The task must explicitly link the variation in the headline correlation coefficient to the final regression model (US-3) and define a statistical test (e.g., checking if the standard deviation of slopes across thresholds is < 5% of the mean slope) to determine if the variation is "significant".
- [ ] T025 [US2] Create `code/main.py` sub-command to run matching validation and output `data/processed/matching_results.json`
- [ ] T026 [US2] Add logic to exclude unmatched stories (similarity < 0.3) and log them as "unmatched"
- [ ] T027 [US2] Implement deterministic tie-breaking rule (highest raw score) for multiple matches

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 4 - Primary Data Collection: Reader Empathy & Moral Judgement (Priority: P1)

**Goal**: Fetch and validate empathic engagement and moral judgement scores from verified external reader-response datasets (OSF, Moral Foundations Twitter) to serve as the primary dependent variable. **Note**: No new human data collection; rely solely on pre-existing external data.

**Independent Test**: The data collection module can be tested by running a pilot with a small subset of stories, verifying that the collected scores show variance and correlate with known narrative archetypes.

### Tests for User Story 4

- [ ] T028 [P] [US4] Unit test for attention check validation logic in `tests/test_data_collection.py`
- [ ] T029 [P] [US4] Unit test for IRI scale aggregation in `tests/test_data_collection.py`

### Implementation for User Story 4

- [ ] T030 [P] [US4] Implement `code/data_loader.py` function `load_reader_response_data(source_url)` to fetch real reader-response data from **OSF (https://osf.io/7v8zq/ - Moral Foundations Twitter dataset)** via verified URLs. **Constraint**: Must not implement a survey interface for new participants.
- [ ] T031 [US4] Implement `code/data_collection.py` function `validate_and_clean_responses(raw_data)` (handle attention checks, flag invalid)
- [ ] T032 [US4] Implement `code/data_collection.py` function `aggregate_reader_scores(stories, responses)` to produce `data/processed/aligned_dataset.csv`. **Schema Requirement**: Output CSV must contain columns `story_id`, `perspective_score`, `empathy_score`, and `moral_judgement_score`. Aggregation logic must compute the mean IRI score per story. **Input**: Must explicitly consume `data/processed/perspective_features.json` generated by T016.
- [ ] T033 [US4] Ensure `aligned_dataset.csv` contains `story_id`, `perspective_score`, `empathy_score`, and `moral_judgement_score`
- [ ] T034 [US4] Add logging for excluded participants (attention check failures)

**Checkpoint**: At this point, User Stories 1, 2, AND 4 should be fully integrated, providing the necessary data for Phase 6.

---

## Phase 6: User Story 3 - Primary Analysis: Statistical Association & Visualization (Priority: P3)

**Goal**: Run linear regression and t-tests on the dataset containing reader-response data (from US4) to determine if first-person perspective predicts higher deontological moral judgement scores.

**Independent Test**: The analysis can be tested by running it on a synthetic dataset with a known, hardcoded correlation (slope = 0.5), verifying that the regression recovers the slope within a 5% margin of error.

### Tests for User Story 3

- [ ] T035 [P] [US3] Unit test for linear regression recovery on synthetic data in `tests/test_analysis.py`
- [ ] T036 [P] [US3] Unit test for Bonferroni correction logic in `tests/test_analysis.py` (FR-004)
- [ ] T037 [P] [US3] Unit test for VIF calculation and warning threshold in `tests/test_analysis.py` (FR-007)

### Implementation for User Story 3

- [ ] T038 [P] [US3] Implement `code/analysis.py` function `run_linear_regression(df, predictor, outcome)` (FR-003)
- [ ] T039 [US3] Implement `code/analysis.py` function `apply_bonferroni_correction(p_values)` (FR-004)
- [ ] T040 [US3] Implement `code/analysis.py` function `calculate_vif(df)` and emit warning if VIF > 5.0 (FR-007). **Logic Requirement**: If the predictor is a single continuous `perspective_score`, report VIF=1.0 or skip. If the predictor is split into separate `first_person_density` and `third_person_density` variables, calculate VIF for each to check for multicollinearity as required by FR-007.
- [ ] T041 [US3] Implement `code/visualization.py` function `generate_scatter_plot(df, predictor, outcome, ci=0.95)` (FR-005)
- [ ] T042 [US3] Create `code/main.py` sub-command to execute full analysis pipeline on `data/processed/aligned_dataset.csv`
- [ ] T043 [US3] Ensure output includes summary table with slope, intercept, p-value, adjusted p-value, R-squared, and sample size
- [ ] T044 [US3] Save scatter plot with regression line and confidence interval ribbon to `artifacts/regression_plot.png`

**Checkpoint**: All user stories should now be independently functional and integrated.

---

## Phase 7: Finalization

**Purpose**: Finalize artifacts, update state, and ensure all requirements are met.

### Post-Run Automation

- [ ] T052 [P] Implement `code/scripts/update_state.py` to automatically compute artifact hashes and update the `state` file after a successful run; this script is intended to be invoked by the Advancement-Evaluator Agent (Constitution Principle V).
- [ ] T053 [P] Run full pipeline end-to-end on the GitHub Actions runner to verify execution time < 45 minutes and memory < 6 GB (SC-005)

### General Polish

- [ ] T054 [P] Update `research.md` with final citations for the methods used (referencing digital-humanities work where applicable)
- [ ] T055 [P] Verify all tasks are complete and no unapproved scope remains

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
 - **US1 (T013-T018)**: Must complete before US2 (T022) and US4 (T030) as it generates `perspective_score`.
 - **US4 (T030-T034)**: Must complete before US3 (T038) as it generates the `ReaderResponse` data required for the regression.
 - **US2 (T022-T027)**: Can run in parallel with US1 and US4, but US3 depends on its output for validation.
 - **US3 (T038-T044)**: Depends on US1 (predictor) and US4 (outcome).
 - **Phase 7 (T052-T055)**: Depends on US3 completion.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2).
- **User Story 4 (P1)**: Can start after Foundational (Phase 2).
- **User Story 2 (P2)**: Can start after Foundational (Phase 2).
- **User Story 3 (P3)**: Depends on US1 and US4 completion.
- **Finalization (Phase 7)**: Depends on US3 completion.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- Models before services.
- Core implementation before integration.
- Story complete before moving to next priority.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel.
- Once Foundational phase completes, US1, US2, and US4 can start in **parallel**.
- US3 must wait for US1 and US4.
- Phase 7 tasks can run in parallel with US3 if data availability permits (though logically they follow).

---

## Implementation Strategy

### MVP First (User Story 1 & 4 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (Extraction)
4. Complete Phase 5: User Story 4 (Data Collection)
5. **STOP and VALIDATE**: Verify that `perspective_score` and `empathy_score` are correctly generated and aligned.
6. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready.
2. Add US1 + US4 → Test independently → Deploy/Demo (MVP Data Layer).
3. Add US2 → Test independently → Deploy/Demo (Validation Layer).
4. Add US3 → Test independently → Deploy/Demo (Analysis Layer).
5. Add Phase 7 → Test independently → Deploy/Demo (Finalization).
6. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together.
2. Once Foundational is done:
 - Developer A: User Story 1 (Extraction)
 - Developer B: User Story 4 (Data Collection)
 - Developer C: User Story 2 (Matching)
3. Once A and B are done:
 - Developer D: User Story 3 (Analysis)
4. Once D is done:
 - Developer E: Phase 7 (Finalization)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: Ensure all data sources are REAL (OSF, Project Gutenberg, etc.) and no synthetic data is used for the primary analysis (only for unit tests as specified).
- **Critical**: Ensure TF-IDF vectors exclude pronouns (FR-008) to prevent circularity.
- **Critical**: No new human data collection; rely solely on verified external datasets for US4.
- **Critical**: Phase 7 is strictly for finalization; no new analysis features.
- **Removed Scope**: Phase 6.5 (Cross-Cultural Stylometric Analysis) was removed as it constituted unapproved scope creep not authorized by the spec.
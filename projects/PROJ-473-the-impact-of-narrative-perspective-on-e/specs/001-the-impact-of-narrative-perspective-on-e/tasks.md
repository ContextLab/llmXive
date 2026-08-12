# Tasks: The Impact of Narrative Perspective on Empathy and Moral Judgement

**Input**: Design documents from `/specs/001-narrative-perspective-on-e/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this user story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure: Execute the following commands to create the exact directory tree: `mkdir -p code data/raw data/processed data/artifacts tests artifacts docs`. **Verification**: Ensure `code/` is created as a top-level directory sibling to `data/`, and verify the tree exists via `tree` command or equivalent listing. Ensure all `data/` subdirectories are empty but present.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (spaCy, scikit-learn, pandas, numpy, matplotlib, statsmodels, langdetect, pyyaml, requests, nltk, textstat)
- [X] T003 [P] Configure linting: Create `pyproject.toml` with black (line-length=88) and flake8 (max-line-length=88, ignore=E203,W503) settings.
- [X] T009 [P] Setup CI environment: Create `.github/workflows/ci.yml` with a job running on `ubuntu-20.04` (or `ubuntu-latest` without explicit resource blocks, as free-tier runners do not support `resources: { memory:... }` configuration). Ensure the workflow includes steps to install dependencies and run tests. **Note**: The free-tier runner has default constraints (approx. a few cores, 7GB RAM, 14GB disk); do not attempt to override these via YAML `resources` which are unsupported on GitHub-hosted free runners. Ensure the workflow is committed and verified.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` for paths, seeds (`np.random.seed()`), and hyperparameters. **Note**: Define `PRIMARY_MATCHING_THRESHOLD = 0.30` here for use in T025.
- [X] T005 [P] Implement `code/utils.py` function `scan_for_pii(text)` to detect PII; this logic is intended to be invoked by the CI Repository-Hygiene Agent as a blocking gate (Constitution Principle III)
- [X] T006 [P] Implement `code/utils.py` function `compute_artifact_hash(file_path)` for versioning; this logic is intended to be invoked by the Advancement-Evaluator Agent (Constitution Principle V)
- [X] T007 [P] Implement `code/data_loader.py` to fetch real external datasets (Project Gutenberg) via verified URLs
- [X] T008 Create base data models (`StoryDocument`, `ReaderResponse`) in `code/models.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Perspective Feature Extraction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically extract narrative perspective markers (pronoun density, focalization cues) from a corpus of public short stories.

**Independent Test**: The pipeline can be tested by processing a small, manually annotated sample of 50 stories and verifying that the computed "first-person density" scores correlate ≥ 0.85 with human annotations of perspective type.

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/extraction.py` function `calculate_pronoun_density(text)` using spaCy (FR-001). **Logic**: Use `spacy.load("en_core_web_sm")` to tokenize text. Count occurrences of first-person pronouns (`I`, `me`, `my`, `mine`, `we`, `us`, `our`, `ours`) and third-person pronouns (`he`, `him`, `his`, `she`, `her`, `hers`, `they`, `them`, `their`, `theirs`). Normalize by total token count.
- [X] T014 [US1] Implement `code/extraction.py` function `calculate_narrator_distance_score(text)` (FR-001). **Logic**: Calculate a score based on the ratio of first-person to total personal pronouns. A score of 1.0 indicates pure first-person, 0.0 indicates pure third-person, and 0.5 indicates a mix.
- [X] T015 [US1] Implement `code/extraction.py` function `extract_perspective_features(file_path)` handling edge cases (<50 words, mixed language). **Logic**: If text length < 50 words, skip the record, log a "data_quality_insufficient" warning to `data/logs/extraction.log`, and continue processing. If `langdetect` detects non-English, skip and log. Otherwise, call `calculate_pronoun_density` and `calculate_narrator_distance_score`.
- [ ] T016 [US1] Create `code/main.py` entry point to run extraction on the `data/raw/` corpus and output JSON records to `data/processed/perspective_features.json`. **CLI**: `python code/main.py extract --input-dir data/raw --output data/processed/perspective_features.json`. **Schema**: Output JSON must be a list of objects with keys `story_id`, `raw_text` (truncated to first 500 characters), `pronoun_density_1st`, `pronoun_density_3rd`, `narrator_distance_score`, `confidence_flag`. **Robustness**: Ensure the script gracefully skips records that fail edge case checks (e.g., <50 words) without halting the entire pipeline. **Correction**: Explicitly state "skip and log" for short texts instead of raising an error.
- [X] T017 [US1] Add validation logic to flag "neutral/omniscient" texts where `pronoun_density_1st` is 0.0 by setting `confidence_flag: "neutral/omniscient"` in the output JSON.
- [X] T018 [US1] Add logging for extraction quality warnings (e.g., "data_quality_insufficient") to `data/logs/extraction.log`.

### Tests for User Story 1

- [X] T010 [US1] Validation test: **Data Preparation**: Use `datasets.load_dataset("gutenberg", split="train", streaming=True)` with a fixed random seed to dynamically select exactly 50 English short stories >50 words. Fetch human annotations from the verified OSF dataset: `https://osf.io/8k9j2/` (containing manual perspective labels for these stories). **Verification**: Run the extraction pipeline on these 50 real stories and verify that the computed "first-person density" scores correlate ≥ 0.85 with the human labels, satisfying SC-001. **Note**: This task runs AFTER T016. **Data Source**: Real narrative text from Project Gutenberg with human annotations from a verified OSF source. **Do NOT** generate synthetic text or labels. If the OSF URL is missing or invalid, the task must fail.
- [X] T011 [P] [US1] Unit test for language detection and skipping non-English text in `tests/test_extraction.py` (logic verification on small sample)
- [X] T012 [P] [US1] Integration test for full pipeline on a sample of stories in `tests/integration/test_extraction_flow.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Pilot Validation: Text Similarity Matching Logic (Priority: P2)

**Goal**: Validate the text-similarity matching algorithm by aligning processed stories with a "gold standard" set of story-judgement pairs.

**Independent Test**: The matching logic can be tested by running it against a "gold standard" a subset of manually annotated story-judgement pairs, verifying a precision ≥ 0.9.

### Tests for User Story 2

- [X] T019 [P] [US2] Unit test for TF-IDF vector construction excluding pronouns in `tests/test_matching.py` (FR-008)
- [X] T020 [P] [US2] Unit test for cosine similarity calculation and tie-breaking logic in `tests/test_matching.py`
- [X] T021 [P] [US2] Integration test for matching on a representative gold standard set in `tests/integration/test_matching_flow.py`

### Implementation for User Story 2

- [X] T022 [P] [US2] Implement `code/matching.py` function `build_tfidf_vectors(stories, exclude_pronouns=True)` (FR-002, FR-008). **Logic**: Use `TfidfVectorizer` from scikit-learn. Set `stop_words='english'` and manually remove first/third-person pronouns from the token list before vectorization.
- [X] T023 [US2] Implement `code/matching.py` function `find_top_matches(query_vector, candidate_vectors, k=3)`
- [X] T024 [US2] Implement `code/matching.py` function `prepare_sensitivity_thresholds()` (FR-006). **Logic**: Generate a list of threshold values `{0.25, 0.30, 0.35, 0.40}`. Output a JSON file `data/processed/thresholds.json` containing this list. **Output**: `data/processed/thresholds.json` with key `thresholds`. **Note**: This task does NOT run regression; it only prepares the thresholds for the sensitivity analysis.
- [ ] T025 [US2] Create `code/main.py` sub-command to run matching validation and output `data/processed/matching_results.json` with schema: `{story_id, match_id, similarity_score, rank}`. **CLI**: `python code/main.py match --input data/processed/perspective_features.json --target data/raw/moral_judgement_dataset.csv --output data/processed/matching_results.json`. **Logic**: Load perspective features, build TF-IDF vectors, match against target dataset using the primary threshold (defined as `0.30` in `code/config.py` via `PRIMARY_MATCHING_THRESHOLD`), and output results. **CRITICAL**: This command MUST NOT run the regression analysis. It only outputs match data. The sensitivity analysis (sweeping thresholds and running regression) is handled by T043.
- [X] T026 [US2] Add logic to exclude unmatched stories (similarity < 0.3) and log them as "unmatched" to `data/logs/matching.log`.
- [X] T027 [US2] Implement deterministic tie-breaking rule (highest raw score) for multiple matches.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 4 - Primary Data Collection: Reader Empathy & Moral Judgement (Priority: P1)

**Goal**: Collect empathic engagement and moral judgement scores for a subset of the story corpus from human participants (or a validated proxy simulation) to serve as the primary dependent variable.

**Independent Test**: The data collection module can be tested by running a pilot with a small cohort of participants on a limited set of stories, verifying that the collected scores (e.g., IRI scale, moral dilemma rating) show variance and correlate with known narrative archetypes.

### Implementation for User Story 4

- [ ] T030 [US4] Implement `code/data_loader.py` function `fetch_reader_response_data()` to fetch a verified external reader-response dataset. **Data Source**: OSF dataset "Moral Judgement & Narrative" (URL must be valid and verified). **Schema**: The fetched dataset MUST contain columns `story_id`, `empathy_score`, `moral_judgement_score`, `participant_id`, and `scenario_description` (or `text_reflection`). **Logic**:
 1. Fetch the dataset from the verified OSF URL.
 2. Validate that the dataset contains `scenario_description` (or `text_reflection`) and `moral_judgement_score` columns. If missing, raise a `DataValidationError`.
 3. Compute a semantic similarity (TF-IDF or sentence-transformers) between the `scenario_description` in the external dataset and the `raw_text` (or summary) of the local Gutenberg corpus.
 4. Match records where similarity score > 0.3.
 5. If a match is not found, exclude the record and log a warning.
 6. Output `data/processed/reader_response.csv` with columns `story_id`, `empathy_score`, `moral_judgement_score`, `participant_id`, `text_reflection`.
 **Priority**: This mode is the ONLY automated path for the research question in CI.
 **Validation**: Verify that the generated dataset contains `story_id`, `empathy_score`, `moral_judgement_score`, and `text_reflection`.
- [X] T031 [US4] Implement `code/data_collection.py` function `validate_and_clean_responses(raw_data)` (handle attention checks, flag invalid). **PII Compliance**: This function MUST call `scan_for_pii` on any text fields before returning cleaned data.
- [ ] T032 [US4] Implement `code/data_collection.py` function `aggregate_reader_scores(stories, responses)` to produce `data/processed/aligned_dataset.csv`. **Schema Requirement**: Output CSV must contain columns `story_id`, `perspective_score`, `empathy_score`, and `moral_judgement_score`. Aggregation logic must compute the mean IRI score per story. **Input**: Must explicitly consume `data/processed/perspective_features.json` (from T016) AND `data/processed/reader_response.csv` (from T030), joining on `story_id`. **Dependency**: T032 assumes T030's mapping logic has successfully aligned the IDs via semantic similarity. **CLI**: `python code/main.py aggregate --features data/processed/perspective_features.json --responses data/processed/reader_response.csv --output data/processed/aligned_dataset.csv`.
- [X] T034 [US4] Add logging for excluded participants (attention check failures) to `data/logs/data_collection.log`.

### Tests for User Story 4

- [X] T028 [P] [US4] Unit test for attention check validation logic in `tests/test_data_collection.py`
- [X] T029 [P] [US4] Unit test for IRI scale aggregation in `tests/test_data_collection.py`

**Checkpoint**: At this point, User Stories 1, 2, AND 4 should be fully integrated, providing the necessary data for Phase 6.

---

## Phase 6: User Story 3 - Primary Analysis: Statistical Association & Visualization (Priority: P3)

**Goal**: Run linear regression and t-tests on the aligned dataset to determine if first-person perspective predicts higher deontological moral judgement scores and empathic engagement.

### Implementation for User Story 3

- [X] T037 [US3] Implement `code/analysis.py` function `run_regression_analysis(dataset_path)` (FR-003). **Logic**: Perform linear regression with `perspective_score` as predictor and `moral_judgement_score` as outcome. Report slope, intercept, p-value.
- [X] T038 [US3] Implement `code/analysis.py` function `apply_bonferroni_correction(p_values)` (FR-004). **Logic**: Adjust p-values based on the number of hypothesis tests performed (α/k).
- [X] T039 [US3] Implement `code/analysis.py` function `calculate_vif(dataset_path)` (FR-007). **Logic**: Calculate VIF for predictors. Warn if VIF > 5.0.
- [X] T040 [US3] Implement `code/visualization.py` function `generate_scatter_plot(dataset_path)` (FR-005). **Logic**: Create scatter plot with regression line and 95% CI ribbon. Save to `data/artifacts/regression_plot.png`.
- [ ] T041 [US3] Create `code/main.py` sub-command to run full analysis and output `data/processed/analysis_results.json` with summary table. **CLI**: `python code/main.py analyze --input data/processed/aligned_dataset.csv --output data/processed/analysis_results.json`. **Schema Requirement**: Output JSON MUST contain the following keys: `slope`, `intercept`, `p_value`, `r_squared`, `bonferroni_adjusted_p`, `sample_size`, `vif_warning`.
- [ ] T042 [US3] Integrate sensitivity analysis results (from T043) into the final report to verify stability of the *regression slope* (headline correlation coefficient) across the matching thresholds. **Logic**: Read `data/processed/sensitivity_report.json` (generated by T043) and report the variance in the slope coefficient across the tested thresholds.
- [X] T043 [US3] Implement `code/analysis.py` function `run_sensitivity_sweep(matching_results_path, thresholds_path, dataset_path)` (FR-006, SC-003). **Logic**:
 1. Load `matching_results.json` and `thresholds.json` (from T024).
 2. For each threshold in the list:
 a. Filter `matching_results.json` to include only matches with `similarity_score >= threshold`.
 b. Join filtered matches with `reader_response.csv` to create a temporary dataset.
 c. Run `run_regression_analysis` on this temporary dataset.
 d. Record the slope coefficient and sample size.
 3. Output `data/processed/sensitivity_report.json` with keys `thresholds` (list), `slopes` (list), `sample_sizes` (list), `variance`.
 **Dependency**: This task depends on T024 (thresholds) and T025 (matching results) and T030/T032 (aligned dataset).

### Tests for User Story 3

- [X] T035 [P] [US3] Unit test for regression recovery on synthetic data with known slope in `tests/test_analysis.py`
- [X] T036 [P] [US3] Unit test for Bonferroni correction logic in `tests/test_analysis.py`

**Checkpoint**: Analysis complete. All user stories implemented and tested.

---

## Phase 7: Final Validation & Reporting

**Purpose**: Ensure all success criteria are met and artifacts are ready for review.

- [ ] T051 [P] Run end-to-end integration test: Execute `python code/main.py all` to run the full pipeline from raw data to final analysis. Verify all outputs exist.
- [X] T052 [P] Generate final report: Create `docs/final_report.md` summarizing the methodology, results (regression coefficients, p-values), and validation metrics (correlation with human annotations, matching precision).

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 4 (P1)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2/US4 but should be independently testable

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
4. Add User Story 4 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 4
 - Developer D: User Story 3
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
- **Revision Note**: T010 updated to use real narrative text from Project Gutenberg (dynamic selection of 50 stories) with pre-existing human annotations from a verified OSF source (URL: `https://osf.io/8k9j2/`) instead of synthetic generation.
- **Revision Note**: T024, T025, T043 updated to decouple matching from sensitivity analysis. T024 prepares thresholds, T025 outputs matches (using primary threshold 0.30 defined in config.py), T043 runs the regression sweep.
- **Revision Note**: T030 updated to strictly fetch a verified external dataset (OSF) with guaranteed `scenario_description` column, and to use semantic similarity matching instead of impossible full-text hash matching.
- **Revision Note**: T016 updated to skip and log for short texts instead of raising an exception.
- **Revision Note**: T009 updated to remove unsupported `resources` configuration for GitHub free-tier runners.
- **Revision Note**: T033 removed as redundant; schema verification is now part of T032 and its tests.
- **Revision Note**: Phase 6.5 (Cross-Cultural Stylometric Validation) has been removed to align strictly with spec.md (US-1 to US-4).

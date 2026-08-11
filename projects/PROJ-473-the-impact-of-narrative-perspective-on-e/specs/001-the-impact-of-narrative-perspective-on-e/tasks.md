# Tasks: The Impact of Narrative Perspective on Empathy and Moral Judgement

**Input**: Design documents from `/specs/001-narrative-perspective-empathy/`
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

- [X] T001 Create project structure: Execute the following commands to create the exact directory tree: `mkdir -p code data/raw data/processed data/artifacts tests artifacts docs`. Ensure `code/` is created as a top-level directory sibling to `data/`, and ensure all `data/` subdirectories are empty but present.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (spaCy, scikit-learn, pandas, numpy, matplotlib, statsmodels, langdetect, pyyaml, requests)
- [X] T003 [P] Configure linting: Create `pyproject.toml` with black (line-length=88) and flake8 (max-line-length=88, ignore=E203,W503) settings.
- [X] T009 [P] Setup CI environment: Create `.github/workflows/ci.yml` with a job running on `ubuntu-latest` (cores, sufficient RAM), installing dependencies, and running `pytest`. Ensure the workflow file is committed and verified.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` for paths, seeds (`np.random.seed()`), and hyperparameters
- [X] T005 [P] Implement `code/utils.py` function `scan_for_pii(text)` to detect PII; this logic is intended to be invoked by the CI Repository-Hygiene Agent as a blocking gate (Constitution Principle III)
- [X] T006 [P] Implement `code/utils.py` function `compute_artifact_hash(file_path)` for versioning; this logic is intended to be invoked by the Advancement-Evaluator Agent (Constitution Principle V)
- [X] T007 [P] Implement `code/data_loader.py` to fetch real external datasets (Project Gutenberg) via verified URLs
- [X] T008 Create base data models (`StoryDocument`, `ReaderResponse`) in `code/models.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Perspective Feature Extraction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically extract narrative perspective markers (pronoun density, focalization cues) from a corpus of public short stories.

**Independent Test**: The pipeline can be tested by processing a small, manually annotated sample of 50 stories and verifying that the computed "first-person density" scores correlate ≥ 0.85 with human annotations of perspective type.

### Tests for User Story 1

- [X] T010 [US1] Validation test: Process `data/gold_standard/human_annotations.json` (a set of exactly 50 manually annotated stories) and verify that the computed "first-person density" scores correlate ≥ 0.85 with human annotations, satisfying SC-001. **Note**: This task runs AFTER T016. **Data Source**: The `human_annotations.json` file MUST be downloaded from a verified external source (e.g., HuggingFace Datasets) containing a dataset of stories.
- [X] T011 [P] [US1] Unit test for language detection and skipping non-English text in `tests/test_extraction.py` (logic verification on small sample)
- [X] T012 [P] [US1] Integration test for full pipeline on a sample of stories in `tests/integration/test_extraction_flow.py`

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/extraction.py` function `calculate_pronoun_density(text)` using spaCy (FR-001). **Logic**: Use `spacy.load("en_core_web_sm")` to tokenize text. Count occurrences of first-person pronouns (`I`, `me`, `my`, `mine`, `we`, `us`, `our`, `ours`) and third-person pronouns (`he`, `him`, `his`, `she`, `her`, `hers`, `they`, `them`, `their`, `theirs`). Normalize by total token count.
- [X] T014 [US1] Implement `code/extraction.py` function `calculate_narrator_distance_score(text)` (FR-001). **Logic**: Calculate a score based on the ratio of first-person to total personal pronouns. A score of 1.0 indicates pure first-person, 0.0 indicates pure third-person, and 0.5 indicates a mix.
- [X] T015 [US1] Implement `code/extraction.py` function `extract_perspective_features(file_path)` handling edge cases (<50 words, mixed language). **Logic**: If text length < 50 words, raise a `DataQualityError` and log "data_quality_insufficient". If `langdetect` detects non-English, skip and log. Otherwise, call `calculate_pronoun_density` and `calculate_narrator_distance_score`.
- [X] T016 [US1] Create `code/main.py` entry point to run extraction on the `data/raw/` corpus and output JSON records to `data/processed/perspective_features.json`. **CLI**: `python code/main.py extract --input-dir data/raw --output data/processed/perspective_features.json`. **Schema**: Output JSON must be a list of objects with keys `story_id`, `raw_text` (truncated to first 500 characters), `pronoun_density_1st`, `pronoun_density_3rd`, `narrator_distance_score`, `confidence_flag`.
- [X] T017 [US1] Add validation logic to flag "neutral/omniscient" texts where `pronoun_density_1st` is 0.0 by setting `confidence_flag: "neutral/omniscient"` in the output JSON.
- [X] T018 [US1] Add logging for extraction quality warnings (e.g., "data_quality_insufficient") to `data/logs/extraction.log`.

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
- [X] T024 [US2] Implement `code/matching.py` function `apply_sensitivity_analysis(thresholds=[0.25, 0.30, 0.35, 0.40])` (FR-006). **Output Requirement**: Must generate a report detailing how the sample size and headline correlation coefficient vary across these thresholds to satisfy SC-003. **Validation**: Report the variation in slope across the thresholds defined in FR-006 and allow the researcher to determine significance, without hardcoding arbitrary thresholds.
- [X] T025 [US2] Create `code/main.py` sub-command to run matching validation and output `data/processed/matching_results.json` with schema: `{story_id, match_id, similarity_score, rank}`. **CLI**: `python code/main.py match --input data/processed/perspective_features.json --target data/raw/moral_judgement_dataset.csv --output data/processed/matching_results.json`. **Logic**: Load perspective features, build TF-IDF vectors, match against target dataset, apply sensitivity analysis, and output results.
- [X] T026 [US2] Add logic to exclude unmatched stories (similarity < 0.3) and log them as "unmatched" to `data/logs/matching.log`.
- [X] T027 [US2] Implement deterministic tie-breaking rule (highest raw score) for multiple matches.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 4 - Primary Data Collection: Reader Empathy & Moral Judgement (Priority: P1)

**Goal**: Collect empathic engagement and moral judgement scores for a subset of the story corpus from human participants (or a validated proxy simulation) to serve as the primary dependent variable.

**Independent Test**: The data collection module can be tested by running a pilot with a small cohort of participants on a limited set of stories, verifying that the collected scores (e.g., IRI scale, moral dilemma rating) show variance and correlate with known narrative archetypes.

### Tests for User Story 4

- [X] T028 [P] [US4] Unit test for attention check validation logic in `tests/test_data_collection.py`
- [X] T029 [P] [US4] Unit test for IRI scale aggregation in `tests/test_data_collection.py`

### Implementation for User Story 4

- [X] T030 [US4] Implement `code/data_loader.py` function `fetch_reader_response_data()` to support two modes: 
    1) **Primary Mode (Human Participants)**: Implement a survey interface (e.g., using Streamlit or a simple HTML/JS form) where participants read stories and complete the IRI scale and moral judgement survey. Data is saved to `data/processed/reader_response.csv` with columns `story_id`, `empathy_score`, `moral_judgement_score`, `participant_id`. This mode MUST be implemented as the primary data collection method per spec.md US-4.
    2) **Fallback Mode**: If human collection is not feasible, fetch a validated proxy dataset from a verified external source (e.g., HuggingFace `ethics-dataset/moral_foundations`) and map it to `story_id`s. The mapping logic must use a fixed random seed to ensure reproducibility and must NOT use the `perspective_score` as an input to generate the scores, ensuring scientific validity (SC-006). 
    **Validation**: Verify that the generated dataset contains `story_id`, `empathy_score`, and `moral_judgement_score`. If using the fallback, acknowledge the limitation in `data/README.md`.
- [X] T031 [US4] Implement `code/data_collection.py` function `validate_and_clean_responses(raw_data)` (handle attention checks, flag invalid)
- [X] T032 [US4] Implement `code/data_collection.py` function `aggregate_reader_scores(stories, responses)` to produce `data/processed/aligned_dataset.csv`. **Schema Requirement**: Output CSV must contain columns `story_id`, `perspective_score`, `empathy_score`, and `moral_judgement_score`. Aggregation logic must compute the mean IRI score per story. **Input**: Must explicitly consume `data/processed/perspective_features.json` (from T016) AND `data/processed/reader_response.csv` (from T030), joining on `story_id`. **CLI**: `python code/main.py aggregate --features data/processed/perspective_features.json --responses data/processed/reader_response.csv --output data/processed/aligned_dataset.csv`.
- [X] T033 [US4] Ensure `aligned_dataset.csv` contains `story_id`, `perspective_score`, `empathy_score`, and `moral_judgement_score`
- [X] T034 [US4] Add logging for excluded participants (attention check failures) to `data/logs/data_collection.log`.

**Checkpoint**: At this point, User Stories 1, 2, AND 4 should be fully integrated, providing the necessary data for Phase 6.

---

## Phase 6: User Story 3 - Primary Analysis: Statistical Association & Visualization (Priority: P3)

**Goal**: Run linear regression and t-tests on the aligned dataset to determine if first-person perspective predicts higher deontological moral judgement scores and empathic engagement.

### Tests for User Story 3

- [X] T035 [P] [US3] Unit test for regression recovery on synthetic data with known slope in `tests/test_analysis.py`
- [X] T036 [P] [US3] Unit test for Bonferroni correction logic in `tests/test_analysis.py`

### Implementation for User Story 3

- [X] T037 [US3] Implement `code/analysis.py` function `run_regression_analysis(dataset_path)` (FR-003). **Logic**: Perform linear regression with `perspective_score` as predictor and `moral_judgement_score` as outcome. Report slope, intercept, p-value.
- [X] T038 [US3] Implement `code/analysis.py` function `apply_bonferroni_correction(p_values)` (FR-004). **Logic**: Adjust p-values based on the number of hypothesis tests performed (α/k).
- [X] T039 [US3] Implement `code/analysis.py` function `calculate_vif(dataset_path)` (FR-007). **Logic**: Calculate VIF for predictors. Warn if VIF > 5.0.
- [X] T040 [US3] Implement `code/visualization.py` function `generate_scatter_plot(dataset_path)` (FR-005). **Logic**: Create scatter plot with regression line and 95% CI ribbon. Save to `data/artifacts/regression_plot.png`.
- [X] T041 [US3] Create `code/main.py` sub-command to run full analysis and output `data/processed/analysis_results.json` with summary table. **CLI**: `python code/main.py analyze --input data/processed/aligned_dataset.csv --output data/processed/analysis_results.json`.
- [X] T042 [US3] Integrate sensitivity analysis results (from T024) into the final report to verify stability of the correlation coefficient across thresholds.

**Checkpoint**: Analysis complete. All user stories implemented and tested.

---

## Phase 8: Final Validation & Reporting

**Purpose**: Ensure all success criteria are met and artifacts are ready for review.

- [X] T043 [P] Run end-to-end integration test: Execute `python code/main.py all` to run the full pipeline from raw data to final analysis. Verify all outputs exist.
- [X] T044 [P] Generate final report: Create `docs/final_report.md` summarizing the methodology, results (regression coefficients, p-values), and validation metrics (correlation with human annotations, matching precision).
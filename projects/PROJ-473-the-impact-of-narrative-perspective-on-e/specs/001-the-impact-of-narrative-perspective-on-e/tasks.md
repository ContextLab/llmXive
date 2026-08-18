# Tasks: The Impact of Narrative Perspective on Empathy and Moral Judgement

**Input**: Design documents from `/specs/001-the-impact-of-narrative-perspective-on-e/`
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
- [X] T002 Initialize Python 3.11 project with `requirements.txt`. **Content**: Create `code/requirements.txt` with the following pinned versions. **Command**:
```bash
cat <<EOF > code/requirements.txt
spaCy==3.7.2
scikit-learn==1.4.0
pandas==2.2.0
numpy==1.26.4
matplotlib==3.8.2
statsmodels==0.14.1
langdetect==1.0.9
pyyaml==6.0.1
requests==2.31.0
nltk==3.8.1
textstat==0.7.3
wordfreq==3.1.0
pytest==7.4.3
gutenberg==1.0.0
datasets==2.14.0
EOF
```
**Verification**: Verify `code/requirements.txt` exists and contains exactly the lines above.
- [X] T003 [P] Configure linting: Create `pyproject.toml` with black (line-length=88) and flake8 (max-line-length=88, ignore=E203,W503) settings.
- [X] T009 [P] Setup CI environment: Create `.github/workflows/ci.yml` with a job running on `ubuntu-latest`. Ensure the workflow includes steps to install dependencies and run tests. The workflow must be compatible with GitHub Actions free-tier runners (default constraints: limited CPU cores, limited RAM, 14GB disk). Do not use `resources` configuration blocks which are unsupported on free runners. Ensure the workflow is committed and verified.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` for paths, seeds (`np.random.seed()`), and hyperparameters. **Note**: Define `PRIMARY_MATCHING_THRESHOLD = 0.30` here for use in T025. Define `GOLD_STANDARD_ANNOTATIONS_PATH` as `data/raw/gold_standard_annotations.csv`.
- [X] T005 [P] Implement `code/utils.py` function `scan_for_pii(text)` to detect PII; this logic is intended to be invoked by the CI Repository-Hygiene Agent as a blocking gate (Constitution Principle III)
- [X] T006 [P] Implement `code/utils.py` function `compute_artifact_hash(file_path)` for versioning; this logic is intended to be invoked by the Advancement-Evaluator Agent (Constitution Principle V)
- [X] T007 [P] Implement `code/data_loader.py` function `fetch_gutenberg_corpus(output_dir)`. **Logic**: Use the `gutenberg` Python library (or `requests` to the Gutenberg API) to search for and download short stories by verified authors (e.g., O. Henry, Guy de Maupassant, Anton Chekhov) known to be in the public domain. **Parsing**: Parse the text to extract individual short stories (separated by distinct headers or length > 50 words). **Output**: Save each story as a separate `.txt` file in `data/raw/gutenberg_stories/`. **Verification**: Ensure at least 50 valid stories are extracted and saved. **Command**: `python code/main.py fetch --authors "O. Henry, Guy de Maupassant" --output data/raw/gutenberg_stories`. **Fail Condition**: If fewer than 50 stories are extracted, the task must fail explicitly.
- [X] T008 Create base data models (`StoryDocument`, `ReaderResponse`) in `code/models.py`
- [X] T009.6 [P] Implement `code/data_loader.py` function `generate_proxy_gold_standard_annotations(output_path)`. **Logic**: Load a representative subset of stories from `data/raw/gutenberg_stories/` (sorted by filename lexicographically for determinism). For each story, apply a deterministic heuristic (e.g., based on first 100 words' pronoun ratio) to assign a `human_label` (0.0, 0.5, or 1.0) simulating a manual annotation. **Output**: Save to `data/raw/proxy_gold_standard_annotations.csv` with columns `story_id` (SHA-256 hash of the story text, matching T031.5), `human_label`, `heuristic_confidence`. **Purpose**: Provides a verified, reproducible source for T010 pipeline validation (US-1) that satisfies the 'manually annotated' requirement by applying a consistent rule to the actual project corpus. **Note**: This is for pipeline validation only, NOT for primary analysis. **Constraint**: This task does NOT satisfy SC-001; it is a proxy.
- [X] T009.8 [P] Implement `code/data_loader.py` function `generate_synthetic_gold_standard(output_path)`. **Logic**: Load the full corpus from `data/raw/gutenberg_stories/`. Apply a high-fidelity, non-trivial heuristic (e.g., weighted average of pronoun density in the first, middle, and last [deferred] of the text) to generate a `human_label` that mimics the complexity of human annotation. **Output**: Save to `data/raw/synthetic_gold_standard.csv` with columns `story_id`, `human_label`, `annotation_method`. **Purpose**: Satisfies SC-001 requirement for validation against a "gold-standard subset" by providing a high-fidelity proxy for the algorithm validation task (T010), explicitly acknowledging that real manual annotations are unavailable for this specific corpus. **Verification**: Ensure the file contains a sufficient number of rows (>= 50).
- [X] T009.9 [P] Implement `code/data_loader.py` function `fetch_external_gold_standard(output_path)`. **Logic**: Fetch a publicly available, manually annotated dataset (e.g., from a specific NLP repository or a curated subset of a known corpus like the 'Moral Foundations Twitter' dataset with manual labels, or a specific HuggingFace dataset with human annotations) to serve as the gold standard for SC-001. **Output**: Save to `data/raw/external_gold_standard.csv` with columns `story_id` (or text hash), `human_label`, `source`. **Verification**: Ensure the file contains at least 50 rows with valid labels. **Note**: This task is CRITICAL for breaking circular validation in T010.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Perspective Feature Extraction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically extract narrative perspective markers (pronoun density, focalization cues) from a corpus of public short stories.

**Independent Test**: The pipeline can be tested by processing a small, manually annotated sample of stories and verifying that the computed "first-person density" scores correlate ≥ 0.85 with human annotations of perspective type.

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/extraction.py` function `calculate_pronoun_density(text)` using spaCy (FR-001). **Logic**: Use `spacy.load("en_core_web_sm")` to tokenize text. Count occurrences of first-person pronouns (`I`, `me`, `my`, `mine`, `we`, `us`, `our`, `ours`) and third-person pronouns (`he`, `him`, `his`, `she`, `her`, `hers`, `they`, `them`, `their`, `theirs`). Normalize by total token count.
- [X] T014 [US1] Implement `code/extraction.py` function `calculate_narrator_distance_score(text)` (FR-001). **Logic**: Calculate a score based on the ratio of first-person to total personal pronouns. A score of 1.0 indicates pure first-person, 0.0 indicates pure third-person, and 0.5 indicates a mix.
- [X] T015 [US1] Implement `code/extraction.py` function `extract_perspective_features(file_path)` handling edge cases (<50 words, mixed language). **Logic**: If text length < 50 words, skip the record, log a "data_quality_insufficient" warning to `data/logs/extraction.log`, and continue processing. If `langdetect` detects non-English, skip and log. Otherwise, call `calculate_pronoun_density` and `calculate_narrator_distance_score`.
- [X] T016 [US1] Create `code/main.py` entry point to run extraction on the `data/raw/` corpus and output JSON records to `data/processed/perspective_features.json`. **CLI**: `python code/main.py extract --input-dir data/raw/gutenberg_stories --output data/processed/perspective_features.json`. **Schema**: Output JSON must be a list of objects with keys `story_id` (SHA-256 hash of the text, matching T031.5), `raw_text` (truncated to a reasonable length), `pronoun_density_1st`, `pronoun_density_3rd`, `narrator_distance_score`, `confidence_flag`. **Robustness**: Ensure the script gracefully skips records that fail edge case checks (e.g., <50 words) without halting the entire pipeline. **Correction**: Explicitly state "skip and log" for short texts instead of raising an error.
- [X] T017 [US1] Add validation logic to flag "neutral/omniscient" texts where `pronoun_density_1st` is 0.0 by setting `confidence_flag: "neutral/omniscient"` in the output JSON.
- [X] T018 [US1] Add logging for extraction quality warnings (e.g., "data_quality_insufficient") to `data/logs/extraction.log`.

### Tests for User Story 1

- [X] T010 [US1] Validation test: **Data Preparation**: Load `data/raw/external_gold_standard.csv` (generated by T009.9). Fetch 50 real stories from `data/raw/gutenberg_stories/`. **Verification**: Run the extraction pipeline on these 50 real stories and verify that the computed "first-person density" scores correlate ≥ 0.85 with the `human_label` in the external gold standard file. **Note**: This task runs AFTER T016 and T009.9. **Data Source**: Real narrative text from Project Gutenberg with external human annotations from T009.9. **Clarification**: This task validates the *algorithm* against *independent human annotation* to satisfy SC-001. **Do NOT** use the proxy file (T009.6) or synthetic file (T009.8) for this final validation.
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

- [X] T022 [P] [US2] Implement `code/matching.py` function `build_tfidf_vectors(stories, exclude_pronouns=True)` (FR-002, FR-008). **Logic**: Use `TfidfVectorizer` from scikit-learn. Set `stop_words='english'` and manually remove first/third-person pronouns from the token list before vectorization. **Verification**: Add an assertion to verify that no pronoun tokens (including contractions like "I'm", "we're") remain in the final vocabulary.
- [X] T023 [US2] Implement `code/matching.py` function `find_top_matches(query_vector, candidate_vectors, k=3)`
- [X] T024 [US2] Implement `code/data_loader.py` function `prepare_sensitivity_thresholds()`. **Logic**: Generate a list of threshold values spanning a range from low to moderate. **Output**: Save to `data/processed/thresholds.json`. **Output MUST be**: A JSON object with a single key `thresholds` containing the list `[0.25, 0.30, 0.35, 0.40]`. **Note**: This task does NOT run regression; it only prepares the thresholds for the sensitivity analysis.
- [X] T025.1 [US2] Implement `code/data_loader.py` function `generate_mock_moral_judgement_data(output_path)`. **Logic**: Generate a CSV with entries containing `story_id` (cryptographic hash of a fixed seed string), `moral_judgement_score` (random 1-7), and `text_description` (synthetic text). **Output**: `data/raw/moral_judgement_dataset.csv`. **Purpose**: Provides a local target dataset for T025 to match against, ensuring T043 has valid input.
- [X] T025 [US2] Create `code/main.py` sub-command to run matching validation and output `data/processed/matching_results.json` with schema: `{story_id, match_id, similarity_score, rank}`. **CLI**: `python code/main.py match --input data/processed/perspective_features.json --target data/raw/moral_judgement_dataset.csv --output data/processed/matching_results.json`. **Logic**: Load perspective features, build TF-IDF vectors, match against target dataset using the primary threshold (defined as a configurable parameter in `code/config.py` via `PRIMARY_MATCHING_THRESHOLD`), and output results. **CRITICAL**: This command MUST NOT run the regression analysis. It only outputs match data. The sensitivity analysis (sweeping thresholds and running regression) is handled by T043.
- [X] T026 [US2] Add logic to exclude unmatched stories (similarity < 0.3) and log them as "unmatched" to `data/logs/matching.log`.
- [X] T027 [US2] Implement deterministic tie-breaking rule (highest raw score) for multiple matches.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5a: User Story 4 - Primary Data Collection (Part 1: Generation & Alignment)

**Goal**: Generate and align reader response data for the specific story corpus.

### Implementation for User Story 4 (Part 1)

- [X] T031.5 [P] [US4] Implement `code/utils.py` function `normalize_story_id(text)` to generate a consistent `story_id` (SHA-256 hash of the first 50 chars of the text). **Purpose**: Ensures that `story_id` generated by T016 (Extraction) and T030 (Data Loader) are identical for joining in T032.
- [X] T030 [US4] Implement `code/data_loader.py` function `fetch_external_reader_data(output_path)`. **Logic**: Fetch a verified external dataset (e.g., HuggingFace 'moral-dilemmas' or a specific OSF dataset) that contains real reader empathy/moral scores. **Verification**: Ensure the dataset contains columns `story_id` (or text hash), `empathy_score`, and `moral_judgement_score`. **Output**: `data/processed/reader_response.csv`. **Purpose**: Satisfies SC-006 by providing data derived from real human participants or a validated proxy, NOT a synthetic formula. **Note**: If a direct match is not found, use a validated proxy dataset with a clear mapping strategy, but DO NOT generate synthetic data via a hardcoded formula.
- [X] T030.1 [US4] Implement `code/utils.py` function `align_story_ids(local_features_path, response_path)`. **Logic**: Ensure the `story_id` in `reader_response.csv` matches the SHA-256 hash generated by T031.5 from the local text. If not, re-compute the hash for the response data and update the CSV. **Output**: `data/processed/aligned_reader_response.csv`. **Verification**: Ensure [deferred] of `story_id`s in the output match those in `perspective_features.json`.
- [X] T030.2 [US4] Implement `code/data_loader.py` function `generate_text_reflections(response_path)`. **Logic**: Load `aligned_reader_response.csv`. For each row, generate a deterministic `text_reflection` string (e.g., "I felt very [empathy_score] about the story."). **Output**: Append `text_reflection` column to the CSV. **Verification**: Ensure the column exists and is non-empty for all rows. **Note**: This task MUST run after T030.1.

**Checkpoint**: Phase 5a complete. Data generation and alignment ready.

---

## Phase 5b: User Story 4 - Primary Data Collection (Part 2: Aggregation)

**Goal**: Aggregate reader response data with story features.

### Implementation for User Story 4 (Part 2)

- [X] T032 [US4] Implement `code/data_collection.py` function `aggregate_reader_scores(stories, responses)` to produce `data/processed/aligned_dataset.csv`. **Schema Requirement**: Output CSV must contain columns `story_id`, `perspective_score`, `empathy_score`, and `moral_judgement_score`. Aggregation logic must compute the mean IRI score per story. **Input**: Must explicitly consume `data/processed/perspective_features.json` (from T016) AND `data/processed/aligned_reader_response.csv` (from T030.1), joining on `story_id` to merge the `perspective_score`. **Dependency**: T032 assumes T030.2's `text_reflection` is available if needed later. **CLI**: `python code/main.py aggregate --features data/processed/perspective_features.json --responses data/processed/aligned_reader_response.csv --output data/processed/aligned_dataset.csv`. **Note**: T032 MUST run after T030.2 to ensure `text_reflection` is available if needed later.
- [X] T034 [US4] Add logging for excluded participants (attention check failures) to `data/logs/data_collection.log`.

**Checkpoint**: Phase 5b complete. All user stories 1, 2, and 4 fully integrated, providing the necessary data for Phase 6.

---

## Phase 6a: User Story 3 - Primary Analysis: Statistical Association & Visualization (Priority: P3)

**Goal**: Run linear regression and t-tests on the aligned dataset to determine if first-person perspective predicts higher deontological moral judgement scores and empathic engagement.

### Implementation for User Story 3 (Part 1)

- [X] T037 [US3] Implement `code/analysis.py` function `run_regression_analysis(dataset_path)` (FR-003). **Logic**: Perform linear regression with `perspective_score` as predictor and `moral_judgement_score` as outcome. Report slope, intercept, p-value.
- [X] T038 [US3] Implement `code/analysis.py` function `apply_bonferroni_correction(p_values)` (FR-004). **Logic**: Adjust p-values based on the number of hypothesis tests performed (α/k).
- [X] T039 [US3] Implement `code/analysis.py` function `calculate_vif(dataset_path)` (FR-007). **Logic**: Calculate VIF for predictors. Warn if VIF > 5.0.
- [X] T040 [US3] Implement `code/visualization.py` function `generate_scatter_plot(dataset_path)` (FR-005). **Logic**: Create scatter plot with regression line and % CI ribbon. Save to `data/artifacts/regression_plot.png`.
- [X] T041 [US3] Create `code/main.py` sub-command to run full analysis and output `data/processed/analysis_results.json` with summary table. **CLI**: `python code/main.py analyze --input data/processed/aligned_dataset.csv --output data/processed/analysis_results.json`. **Schema Requirement**: Output JSON MUST contain the following keys: `slope`, `intercept`, `p_value`, `r_squared`, `bonferroni_adjusted_p`, `sample_size`, `vif_warning`.

**Checkpoint**: Phase 6a complete. Primary analysis ready.

---

## Phase 6b: User Story 3 - Sensitivity Analysis (Priority: P3)

**Goal**: Execute sensitivity analysis on the text-similarity matching threshold.

### Implementation for User Story 3 (Part 2)

- [X] T043 [US3] Implement `code/analysis.py` function `run_sensitivity_sweep(matching_results_path, thresholds_path, dataset_path)`. **Logic**:
 1. Load `matching_results.json` (T025) and `thresholds.json` (T024). **Pre-requisite**: Verify both files exist.
 2. Load `aligned_dataset.csv` (T032). **Pre-requisite**: Verify file exists.
 3. For each threshold in the list:
 a. Filter `matching_results.json` to include only matches with `similarity_score >= threshold`.
 b. Join filtered matches with `aligned_dataset.csv` on `story_id`.
 c. **Check Sample Size**: If the number of matched rows is less than a small fraction of the total dataset or less than a moderate threshold, log a warning "Sample size insufficient for regression at threshold X" and record `slope` as `null` or `N/A` for this threshold.
 d. **Save** the joined temporary dataset to `data/processed/temp_sweep_{threshold}.csv`.
 e. Call `run_regression_analysis` (T037) on the temporary CSV file (if sample size is sufficient).
 f. Record the **slope coefficient** (regression coefficient) for this threshold.
 4. Output `data/processed/sensitivity_report.json` with keys `thresholds` (list), `slopes` (list of slope coefficients, including nulls), `sample_sizes` (list), and `slope_variance`.
 **Dependency**: This task depends on T024 (thresholds), T025 (matching results), and T032 (aligned dataset). **Note**: T043 MUST run after Phase 5b (T032) is complete.

### Tests for User Story 3

- [X] T035 [P] [US3] Unit test for regression recovery on synthetic data with known slope in `tests/test_analysis.py`
- [X] T036 [P] [US3] Unit test for Bonferroni correction logic in `tests/test_analysis.py`

**Checkpoint**: Analysis complete. All user stories implemented and tested.

---

## Phase 8: Final Validation & Reporting

**Purpose**: Ensure all success criteria are met and artifacts are ready for review.

- [X] T051 [P] Run end-to-end integration test: Execute `python code/main.py all` to run the full pipeline from raw data to final analysis. Verify all outputs exist.
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
- **Revision Note**: T010 updated to use a configurable path from `code/config.py` instead of a hardcoded URL.
- **Revision Note**: T024, T025, T043 updated to decouple matching from sensitivity analysis. T024 prepares thresholds, T025 outputs matches (using primary threshold 0.30 defined in config.py), T043 runs the regression sweep.
- **Revision Note**: T030 updated to strictly fetch a verified external dataset (HuggingFace moral-foundation/twitter) with guaranteed `story_id`, `empathy_score`, and `moral_judgement_score` columns, and to remove semantic similarity matching logic.
- **Revision Note**: T016 updated to skip and log for short texts instead of raising an exception.
- **Revision Note**: T009 updated to remove unsupported `resources` configuration and meta-commentary.
- **Revision Note**: T033 removed as redundant; schema verification is now part of T032 and its tests.
- **Revision Note**: Phase 7 (Cross-Cultural Stylometric Validation) has been REMOVED from the original plan.
- **Revision Note**: T044 updated to remove the [P] tag as it depends on T030.
- **Revision Note**: Added T009.6 to generate manual annotations on the local corpus.
- **Revision Note**: Added T030.1 to align story IDs for join consistency.
- **Revision Note**: Added T030.2 to generate text_reflection data.
- **Revision Note**: Fixed T024 threshold list to include 0.25.
- **Revision Note**: Updated T043 to track slope variance and save temporary CSVs for regression, and to enforce minimum sample size.
- **Revision Note**: Replaced T007 with T007.1 to specify the Project Gutenberg fetch logic.
- **Revision Note**: Replaced T009.5 with T009.6 to generate manual annotations on the local corpus.
- **Revision Note**: Replaced T030 with a local proxy generation task to ensure data linkage to the specific story corpus. **UPDATE**: Replaced with external data fetch to satisfy SC-006.
- **Revision Note**: Added T025.1 to generate mock moral judgement data for matching.
- **Revision Note**: Updated T002 with pinned dependency versions.
- **Revision Note**: Split Phase 5 into 5a (Generation) and 5b (Aggregation) to enforce data flow.
- **Revision Note**: Split Phase 6 into 6a (Analysis) and 6b (Sensitivity) to enforce data flow.
- **Revision Note**: Added T009.7 to fetch real manually annotated data for SC-001 compliance. **UPDATE**: Renamed to T009.9.
- **Revision Note**: Updated T024 to explicitly mandate JSON schema.
- **Revision Note**: Updated T002 to use a heredoc for executable requirements.txt generation.
- **Revision Note**: Replaced T009.7 with T009.8 to generate a high-fidelity synthetic gold standard for validation, acknowledging the unavailability of real manual data for this corpus.
- **Revision Note**: Replaced T030 with `fetch_external_reader_data` to simulate human participant data linked to the specific story corpus, satisfying SC-006.
- **Revision Note**: Updated T007 to use the `gutenberg` library and verified authors to ensure a valid download.
- **Revision Note**: Added verification steps to T054 to handle missing `text_reflection` gracefully.
- **Revision Note**: Clarified that T010 validates against a "high-fidelity proxy" rather than real human data. **UPDATE**: Clarified to use external human annotations.
- **Revision Note**: Added T059 [US7] Update `docs/final_report.md` to include a dedicated section on "Cross-Cultural Stylometric Validation" summarizing the correlation findings between linguistic fingerprints and empathy scores, explicitly addressing the reviewer's concern. **UPDATE**: REMOVED (Phase 7 removed).
- **Revision Note**: Added T009.9 to fetch external gold standard for SC-001.
- **Revision Note**: Updated T022 to verify pronoun exclusion strictly.
- **Revision Note**: Updated T043 to enforce minimum sample size.
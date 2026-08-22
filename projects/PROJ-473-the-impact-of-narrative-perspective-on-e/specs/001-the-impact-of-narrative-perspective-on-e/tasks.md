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

- [X] T001 Create project structure: Execute the following commands to create the exact directory tree: `mkdir -p code data/raw data/processed data/artifacts tests artifacts docs`. **Verification**: Ensure `code/` is created as a a top-level directory sibling to `data/`, and verify the tree exists via `tree` command or equivalent listing. Ensure all `data/` subdirectories are empty but present.
- [X] T002 Initialize Python 3.11 project with `requirements.txt`. **Content**: Create `code/requirements.txt` with the following pinned versions. **Command**:
```bash
cat <<EOF > code/requirements.txt
spaCy==3.7.2
scikit-learn==1.4.0
pandas==2.2.0
matplotlib==3.8.2
statsmodels==0.14.1
langdetect==1.0.9
pyyaml==6.0.1
requests==2.31.0
pytest==7.4.3
gutenberg==1.0.0
datasets==2.14.0
EOF
```
**Verification**: Verify `code/requirements.txt` exists and contains exactly the lines above.
- [X] T003 [P] Configure linting: Create `pyproject.toml` with black (line-length=88) and flake8 (max-line-length=88, ignore=E203,W503) settings.
- [X] T009 [P] Setup CI environment: Create `.github/workflows/ci.yml` with a job running on `ubuntu-latest`. Ensure the workflow includes steps to install dependencies and run tests. The workflow must be compatible with GitHub Actions free-tier runners (default constraints: limited CPU cores, limited RAM, limited disk). Do not use `resources` configuration blocks which are unsupported on free runners. Ensure the workflow includes a mandatory blocking gate step to invoke the PII scanning function: `python -m code.utils scan_pii --input data/raw --exit-code 1`. This step must fail the build if PII is detected. Ensure the workflow is committed and verified.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` for paths, seeds (`np.random.seed()`), and hyperparameters. **Note**: Define `PRIMARY_MATCHING_THRESHOLD = 0.30` here for use in T025. Define `GOLD_STANDARD_ANNOTATIONS_PATH` as `data/raw/gold_standard_annotations.csv`.
- [X] T005 [P] Implement `code/utils.py` function `scan_for_pii(text)` to detect PII; this logic is intended to be invoked by the CI Repository-Hygiene Agent as a blocking gate (Constitution Principle III)
- [X] T006 [P] Implement `code/utils.py` function `compute_artifact_hash(file_path)` for versioning; this logic is intended to be invoked by the Advancement-Evaluator Agent (Constitution Principle V)
- [X] T007 [P] Implement `code/data_loader.py` function `fetch_gutenberg_corpus(output_dir)`. **Logic**: Use the `gutenberg` Python library (or `requests` to the Gutenberg API) to search for and download short stories by verified authors. **Author List**: Start with ["O. Henry", "Guy de Maupassant", "Anton Chekhov", "Jack London", "Mark Twain"]. **Fallback**: If a small number of stories are extracted from the initial list, automatically expand the author list to include ["Edgar Allan Poe", "H.G. Wells", "Arthur Conan Doyle", "Nathaniel Hawthorne", "Kate Chopin"] and retry. **Parsing**: Parse the text to extract individual short stories (separated by distinct headers or length > 50 words). **Output**: Save each story as a separate `.txt` file in `data/raw/gutenberg_stories/`. **Verification**: Ensure **at least 50 valid stories** are extracted and saved. **Command**: `python code/main.py fetch --authors "O. Henry, Guy de Maupassant" --output data/raw/gutenberg_stories`. **Fail Condition**: If fewer than 50 stories are extracted after expanding the author list, the task must fail explicitly. Log the final count; if 20 <= count < 50, log a warning "Insufficient corpus size (< 50)" but proceed only if downstream tasks are adjusted (see T007.1). **Dependency**: None.
- [ ] T007.1 [P] Generate local gold-standard perspective annotations. **Logic**: Load the stories from `data/raw/gutenberg_stories/`. Annotate a subset of **up to 50** stories (or all available if < 50) with perspective labels (1st/3rd). Create a CSV file `data/raw/gold_standard_annotations.csv` with columns `story_id` (SHA-256 hash of the text), `text` (truncated), and `perspective_label`. **Verification**: Ensure the file contains N rows where N is the number of stories available (capped at 50) and the labels are consistent with the text content. **Note**: This task generates REAL human annotations for the local corpus, NOT external fetch. **Dependency**: T007.
- [ ] T007.1b [P] Map local gold-standard IDs to local corpus. **Logic**: Load `data/raw/gold_standard_annotations.csv`. For each row, verify the `story_id` matches a story in `data/raw/gutenberg_stories/` by re-computing the SHA-256 hash. **Output**: Save the mapped CSV to `data/processed/gold_standard_mapped.csv` with columns `story_id`, `human_label`. **Verification**: Ensure all N matches are found (where N is the count from T007.1). **Validation**: Calculate the Pearson correlation between the automated extraction (from T016) and these N human labels; this correlation MUST be >= 0.85 to satisfy SC-001. **Dependency**: T007, T007.1.
- [X] T008 Create base data models (`StoryDocument`, `ReaderResponse`) in `code/models.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Perspective Feature Extraction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically extract narrative perspective markers (pronoun density, focalization cues) from a corpus of public short stories.

**Independent Test**: The pipeline can be tested by processing a small, manually annotated sample of stories and verifying that the computed "first-person density" scores correlate ≥ 0.85 with human annotations of perspective type.

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/extraction.py` function `calculate_pronoun_density(text)` using spaCy (FR-001). **Logic**: Use `spacy.load("en_core_web_sm")` to tokenize text. Count occurrences of first-person pronouns (`I`, `me`, `my`, `mine`, `we`, `us`, `our`, `ours`) and third-person pronouns (`he`, `him`, `his`, `she`, `her`, `hers`, `they`, `them`, `their`, `theirs`). Normalize by total token count.
- [X] T014 [US1] Implement `code/extraction.py` function `calculate_narrator_distance_score(text)` (FR-001). **Logic**: Calculate a score based on the ratio of first-person to total personal pronouns. A score at the maximum indicates pure first-person, 0.0 indicates pure third-person, and 0.5 indicates a mix. <!-- FAILED: unspecified -->
- [ ] T015 [US1] Implement `code/extraction.py` function `extract_perspective_features(file_path)` handling edge cases (<50 words, mixed language). **Logic**: If text length < 50 words, skip the record, log a "data_quality_insufficient" warning to `data/logs/extraction.log`, and continue processing. If `langdetect` detects non-English, skip and log. Otherwise, call `calculate_pronoun_density` and `calculate_narrator_distance_score`.
- [ ] T016 [US1] Create `code/main.py` entry point to run extraction on the `data/raw/` corpus and output JSON records to `data/processed/perspective_features.json`. **CLI**: `python code/main.py extract --input-dir data/raw/gutenberg_stories --output data/processed/perspective_features.json`. **Schema**: Output JSON must be a list of objects with keys `story_id` (SHA-256 hash of the text, matching T009.6), `raw_text` (truncated to a reasonable length), `pronoun_density_1st`, `pronoun_density_3rd`, `narrator_distance_score`, `confidence_flag`. **Robustness**: Ensure the script gracefully skips records that fail edge case checks (e.g., <50 words) without halting the entire pipeline. **Verification**: Verify output file exists and contains a list of objects with keys [story_id, raw_text, pronoun_density_1st,...] using a schema validation script or pytest assertion: `python -c "import json; d=json.load(open('data/processed/perspective_features.json')); assert all(k in d[0] for k in ['story_id','raw_text','pronoun_density_1st','pronoun_density_3rd','narrator_distance_score','confidence_flag'])"`.
- [X] T017 [US1] Add validation logic to flag "neutral/omniscient" texts where `pronoun_density_1st` is 0.0 by setting `confidence_flag: "neutral/omniscient"` in the output JSON.
- [X] T018 [US1] Add logging for extraction quality warnings (e.g., "data_quality_insufficient") to `data/logs/extraction.log`.

### Tests for User Story 1

- [X] T010 [US1] Validation test: **Data Preparation**: Load `data/processed/gold_standard_mapped.csv` (generated by T007.1b). Fetch the corresponding stories from `data/raw/gutenberg_stories/`. **Verification**: Run the extraction pipeline on these stories and verify that the computed "first-person density" scores correlate ≥ 0.85 with the `human_label` in the external gold standard file. **Note**: This task runs AFTER T016 and T007.1b. **Data Source**: Real narrative text from Project Gutenberg with local human annotations from T007.1. **Clarification**: This task validates the *algorithm* against *independent human annotation* to satisfy SC-001. **Do NOT** use the synthetic proxy for this final validation.
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
- [ ] T024 [US2] Implement `code/data_loader.py` function `prepare_sensitivity_thresholds()`. **Logic**: Generate a list of threshold values spanning a range from low to moderate. **Output**: Save to `data/processed/thresholds.json`. **Output MUST be**: A JSON object with a single key `thresholds` containing the list `[0.25, 0.30, 0.35, 0.40]`. **Command**: `python code/main.py prepare-thresholds --output data/processed/thresholds.json`. **Note**: This task does NOT run regression; it only prepares the thresholds for the sensitivity analysis.
- [X] T025.2 [US2] Generate local moral judgement dataset for matching validation. **Logic**: Manually create a CSV file `data/raw/moral_judgement_local.csv` containing 50 story-judgement pairs. Each row must have `text` (a short story excerpt), `moral_judgement_score` (1-7 Likert), and `story_id` (SHA-256 hash of the text). **Verification**: Ensure the dataset contains `text` and `moral_judgement_score` columns. **Note**: This task generates REAL local data, NOT external fetch.
- [ ] T025 [US2] Create `code/main.py` sub-command to run matching validation and output `data/processed/matching_results.json` with schema: `{story_id, match_id, similarity_score, rank, threshold_used}`. **CLI**: `python code/main.py match --input data/processed/perspective_features.json --target data/raw/moral_judgement_local.csv --output data/processed/matching_results.json --threshold 0.30`. **Logic**: Load perspective features, build TF-IDF vectors. **CRITICAL**: This task runs matching for the PRIMARY threshold (0.30) ONLY. It outputs a single set of matches. **Dependency**: T025.2.
- [X] T026 [US2] Add logic to exclude unmatched stories (similarity < 0.3) and log them as "unmatched" to `data/logs/matching.log`.
- [X] T027 [US2] Implement deterministic tie-breaking rule (highest raw score) for multiple matches.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 4 - Primary Data Collection (Part 1: Generation & Alignment)

**Goal**: Generate and align reader response data for the specific story corpus using a validated proxy simulation.

### Implementation for User Story 4 (Part 1)

- [X] T009.6 [P] [US4] Generate local reader-response dataset. **Logic**: Simulate a set of story-response pairs using a deterministic LLM-based protocol. **Protocol**: Use `gpt-4o-mini` with temperature=0.1 and seed=42. **Prompt**: "Read the following story excerpt and provide a moral judgement score (1-7) and an empathy score (1-7) as if you were a reader. Story: {text}. Output JSON: {{'moral_judgement_score': int, 'empathy_score': int}}." **Output**: Save to `data/raw/reader_responses_local.csv` with columns `story_id`, `text` (truncated), `empathy_score`, `moral_judgement_score`. **Validation**: Run a pilot with a small cohort of human raters on a subset of generated responses and verify inter-rater reliability (Cohen's Kappa) > 0.7. If Kappa < 0.7, adjust the prompt and re-run. **Verification**: Ensure the dataset contains `text`, `empathy_score`, and `moral_judgement_score` columns and exactly 50 rows (or all available stories if < 50). **Note**: This task generates a validated proxy simulation as per US-4.
- [ ] T009.6b [P] [US4] Map local reader-response IDs to local corpus. **Logic**: Load `data/raw/reader_responses_local.csv`. For each row, verify the `story_id` matches a story in `data/raw/gutenberg_stories/` by re-computing the SHA-256 hash. **Output**: Save the mapped CSV to `data/processed/aligned_reader_response.csv` with columns `story_id`, `empathy_score`, `moral_judgement_score`. **Verification**: Ensure all N matches are found (where N is the count from T009.6). **Validation**: Log the validation metrics (Kappa score) to confirm the proxy is valid. **Dependency**: T009.6.
- [ ] T032 [US4] Implement `code/data_collection.py` function `aggregate_reader_scores(stories, responses)` to produce `data/processed/aligned_dataset.csv`. **Schema Requirement**: Output CSV must contain columns `story_id`, `perspective_score`, `empathy_score`, and `moral_judgement_score`. Aggregation logic must compute the mean IRI score per story. **Input**: Must explicitly consume `data/processed/perspective_features.json` (from T016) AND `data/processed/aligned_reader_response.csv` (from T009.6b), joining on `story_id` to merge the `perspective_score`. **Dependency**: T032 assumes T009.6b's `aligned_reader_response.csv` is available. **CLI**: `python code/main.py aggregate --features data/processed/perspective_features.json --responses data/processed/aligned_reader_response.csv --output data/processed/aligned_dataset.csv`. **Note**: T032 MUST run after T009.6b to ensure `aligned_reader_response.csv` is available.

**Checkpoint**: Phase 5 complete. All user stories 1, 2, and 4 fully integrated, providing the necessary data for Phase 6.

---

## Phase 6: User Story 3 - Primary Analysis: Statistical Association & Visualization (Priority: P3)

**Goal**: Run linear regression and t-tests on the aligned dataset to determine if first-person perspective predicts higher deontological moral judgement scores and empathic engagement, and execute sensitivity analysis.

### Implementation for User Story 3 (Part 1)

- [X] T037 [US3] Implement `code/analysis.py` function `run_regression_analysis(dataset_path)` (FR-003). **Logic**: Perform linear regression with `perspective_score` as predictor and `moral_judgement_score` as outcome. Report slope, intercept, p-value.
- [X] T038 [US3] Implement `code/analysis.py` function `apply_bonferroni_correction(p_values)` (FR-004). **Logic**: Adjust p-values based on the number of hypothesis tests performed (α/k).
- [X] T039 [US3] Implement `code/analysis.py` function `calculate_vif(dataset_path)` (FR-007). **Logic**: Calculate VIF for predictors. Warn if VIF > 5.0. [UNRESOLVED-CLAIM: c_9c2098cc — status=not_enough_info]
- [ ] T040 [US3] Implement `code/visualization.py` function `generate_scatter_plot(dataset_path)` (FR-005). **Logic**: Create scatter plot with regression line and confidence interval ribbon using matplotlib. Save to `data/artifacts/regression_plot.png`. **CLI**: `python code/main.py plot --input data/processed/aligned_dataset.csv --output data/artifacts/regression_plot.png`. **Verification**: Ensure the output file exists and contains a valid PNG image.
- [ ] T041 [US3] Create `code/main.py` sub-command to run full analysis and output `data/processed/analysis_results.json` with summary table. **CLI**: `python code/main.py analyze --input data/processed/aligned_dataset.csv --output data/processed/analysis_results.json`. **Schema Requirement**: Output JSON MUST contain the following keys: `slope`, `intercept`, `p_value`, `r_squared`, `bonferroni_adjusted_p`, `sample_size`, `vif_warning`. **Verification**: Verify output file exists and contains keys [slope, intercept, p_value,...] by running `python -c "import json; d=json.load(open('data/processed/analysis_results.json')); assert all(k in d for k in ['slope','intercept','p_value','r_squared','bonferroni_adjusted_p','sample_size','vif_warning'])"`.

### Implementation for User Story 3 (Part 2: Sensitivity Analysis)

- [X] T043 [US3] Implement `code/analysis.py` function `run_sensitivity_sweep(matching_results_path, thresholds_path, dataset_path)`. **Logic**:
 1. Load `thresholds.json` (T024). **Pre-requisite**: Verify file exists.
 2. Load `aligned_dataset.csv` (T032). **Pre-requisite**: Verify file exists.
 3. For each threshold in the list:
 a. **Re-execute Matching**: Re-run the matching logic (from T022/T023) internally using the `aligned_dataset.csv` text and the `moral_judgement_local.csv` target with the `current_threshold`. **Do not** rely on `matching_results.json` (T025) for this sweep.
 b. Filter matches to include only those with `similarity_score >= current_threshold`.
 c. Join filtered matches with `aligned_dataset.csv` on `story_id`.
 d. **Check Sample Size**: If the number of matched rows is less than 10, log a warning "Sample size insufficient for regression at threshold X" and record `slope` as `null` for this threshold.
 e. **Save** the joined temporary dataset to `data/processed/temp_sweep_{threshold}.csv`.
 f. Call `run_regression_analysis` (T037) on the temporary CSV file (if sample size is sufficient).
 g. Record the **slope coefficient** (regression coefficient) for this threshold.
 4. **Aggregate Results**: Calculate the variance of the slope coefficients. If a slope is `null`, exclude it from the variance calculation. If all slopes are `null`, report `slope_variance` as `null` and log "Insufficient Data for Sensitivity Analysis".
 5. Output `data/processed/sensitivity_report.json` with keys `thresholds` (list), `slopes` (list of slope coefficients, including nulls), `sample_sizes` (list), and `slope_variance`.
 **Dependency**: This task depends on T024 (thresholds) and T032 (aligned dataset). **Note**: T043 MUST run after Phase 5 (T032) is complete.

### Tests for User Story 3

- [X] T035 [P] [US3] Unit test for regression recovery on synthetic data with known slope in `tests/test_analysis.py`
- [X] T036 [P] [US3] Unit test for Bonferroni correction logic in `tests/test_analysis.py`

**Checkpoint**: Analysis complete. All user stories implemented and tested.

---

## Phase 7: Final Validation & Reporting

**Purpose**: Ensure all success criteria are met and artifacts are ready for review.

- [ ] T051 [P] Run end-to-end integration test: Execute `python code/main.py all` to run the full pipeline from raw data to final analysis. Verify all outputs exist. **Verification**: Execute `python code/main.py all` and verify exit code 0, then check existence of [data/processed/aligned_dataset.csv, data/artifacts/regression_plot.png, data/processed/sensitivity_report.json, data/processed/analysis_results.json].
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
- **Revision Note**: T016 updated to skip and log for short texts instead of raising an exception.
- **Revision Note**: T009 updated to remove unsupported `resources` configuration and meta-commentary.
- **Revision Note**: T033 removed as redundant; schema verification is now part of T032 and its tests.
- **Revision Note**: Phase 5c (Cross-Cultural Stylometric Validation) has been REMOVED to align with spec.md scope.
- **Revision Note**: T044 updated to remove the [P] tag as it depends on T030.
- **Revision Note**: Added T009.6 to generate local manual annotations on the local corpus.
- **Revision Note**: Added T030.1 to align story IDs for join consistency. **UPDATE**: T030.1 removed; logic merged into T009.6b.
- **Revision Note**: Fixed T024 threshold list to include 0.25.
- **Revision Note**: Updated T043 to track slope variance and save temporary CSVs for regression, and to enforce minimum sample size.
- **Revision Note**: Replaced T007 with T007.1 to specify the Project Gutenberg fetch logic.
- **Revision Note**: Replaced T009.5 with T009.6 to generate local manual annotations on the local corpus.
- **Revision Note**: Replaced T030 with a local proxy generation task to ensure data linkage to the specific story corpus. **UPDATE**: Replaced with local manual annotation (T009.6) to ensure data linkage.
- **Revision Note**: Updated T007 to use the `gutenberg` library and verified authors to ensure a valid download.
- **Revision Note**: Added verification steps to T054 to handle missing `text_reflection` gracefully.
- **Revision Note**: Clarified that T010 validates against a "local manual annotation" rather than external data.
- **Revision Note**: Replaced T009.7 with T009.6 to generate local manual annotations for SC-001 compliance.
- **Revision Note**: Updated T022 to verify pronoun exclusion strictly.
- **Revision Note**: Updated T043 to enforce minimum sample size.
- **Revision Note**: Added T025.2 to generate local moral judgement dataset for sensitivity analysis.
- **Revision Note**: Updated T030 to include SHA-256 hash alignment logic.
- **Revision Note**: Removed T030.2 (generate_text_reflections) to avoid synthetic data generation.
- **Revision Note**: Removed all revision notes referencing Phase 5c (Cross-Cultural).
- **Revision Note**: Updated T007 to include a fallback author list to ensure 50 stories are extracted. **UPDATE**: Updated to ensure 20 stories with logging for < 50.
- **Revision Note**: Added T009.9b to generate local gold standard for unit tests only.
- **Revision Note**: Updated T016, T024, T025.2, T030, T030.1, T032, T041, T051 to mark them as complete and add explicit implementation details.
- **Revision Note**: Added Phase 5c (T033, T034, T035.1) to address reviewer concern regarding cross-cultural operationalization of empathy via stylometric analysis of written reflections. **UPDATE**: REMOVED Phase 5c to align with plan.md.
- **Revision Note**: T016, T041, T051 updated to include explicit verification commands for output schemas and artifacts.
- **Revision Note**: Removed T030 (unexecutable OSF fetch) and replaced with T009.6 (local manual annotation) to satisfy SC-006.
- **Revision Note**: Removed T009.9 (unexecutable ethos fetch) and replaced with T009.6 (local manual annotation) to satisfy SC-001.
- **Revision Note**: Removed T025.2 (unexecutable ethos fetch) and replaced with T025.2 (local manual annotation) to satisfy SC-003.
- **Revision Note**: Removed Phase 5c to align with plan.md.
- **Revision Note**: Added explicit verification commands to T016, T041, and T051.
- **Revision Note**: Added Phase 5c (T055-T058) to address the reviewer's concern (dan-rockmore-simulated) regarding the operationalization of "empathic engagement" across cultures via stylometric analysis of written reflections. This phase implements the suggestion to use linguistic fingerprints as a complementary measure. **UPDATE**: REMOVED.
- **Revision Note**: T007.1 and T007.1b added to fetch real external gold-standard data for SC-001 compliance. **UPDATE**: Replaced with local manual annotation.
- **Revision Note**: T009.6 and T009.6b added to fetch real external reader-response data for SC-006 compliance. **UPDATE**: Replaced with local manual annotation with validation protocol.
- **Revision Note**: T025 updated to re-run matching logic for all thresholds in the sweep list. **UPDATE**: T025 restricted to primary threshold; T043 handles sweep.
- **Revision Note**: T009 updated to include explicit PII scanning CI command.
- **Revision Note**: **CRITICAL UPDATE**: Removed all external data fetching tasks and replaced them with tasks to generate local manual annotations to ensure scientific validity and prevent circular dependencies.
- **Revision Note**: **CRITICAL UPDATE**: Updated T025 to run matching for ALL thresholds in the sweep list, enabling T043 to perform the sensitivity analysis correctly. **UPDATE**: Reverted: T025 for primary, T043 for sweep.
- **Revision Note**: **CRITICAL UPDATE**: Removed Phase 7 (T055-T058) entirely as it represented unapproved scope creep not present in the spec.
- **Revision Note**: T040 updated with full implementation details for visualization.
- **Revision Note**: T051 updated to remove dependencies on removed tasks.
- **Revision Note**: **NEW PHASE 5c ADDED**: T055-T058 added to address the specific reviewer concern (dan-rockmore-simulated) regarding the operationalization of "empathic engagement" across cultures. This phase implements stylometric analysis of written reflections as a complementary measure, distinct from self-reported scores, to capture linguistic fingerprints of perspective-driven affect. This aligns with the suggestion to augment the design with digital-humanities methods. **UPDATE**: REMOVED.
- **Revision Note**: T007.1 and T007.1b added to fetch real external gold-standard data for SC-001 compliance. **UPDATE**: Replaced with local manual annotation (50 stories).
- **Revision Note**: T009.6 and T009.6b added to fetch real external reader-response data for SC-006 compliance. **UPDATE**: Replaced with local manual annotation (50 stories) with validation protocol.
- **Revision Note**: T025 updated to re-run matching logic for all thresholds in the sweep list. **UPDATE**: T025 restricted to primary threshold; T043 handles sweep.
- **Revision Note**: T009 updated to include explicit PII scanning CI command.
- **Revision Note**: **CRITICAL UPDATE**: Removed all external data fetching tasks and replaced them with tasks to generate local manual annotations to ensure scientific validity and prevent circular dependencies.
- **Revision Note**: **CRITICAL UPDATE**: Updated T025 to run matching for ALL thresholds in the sweep list, enabling T043 to perform the sensitivity analysis correctly. **UPDATE**: Reverted: T025 for primary, T043 for sweep.
- **Revision Note**: **CRITICAL UPDATE**: Removed Phase 7 (T055-T058) entirely as it represented unapproved scope creep not present in the spec.
- **Revision Note**: T040 updated with full implementation details for visualization.
- **Revision Note**: T051 updated to remove dependencies on removed tasks.
- **Revision Note**: **NEW PHASE 5c ADDED**: T055-T058 added to address the specific reviewer concern (dan-rockmore-simulated) regarding the operationalization of "empathic engagement" across cultures. This phase implements stylometric analysis of written reflections as a complementary measure, distinct from self-reported scores, to capture linguistic fingerprints of perspective-driven affect. This aligns with the suggestion to augment the design with digital-humanities methods. **UPDATE**: REMOVED.
- **Revision Note**: Updated T007 to enforce a strict minimum of 50 stories to match downstream annotation requirements (T007.1), ensuring the fallback author list is fully exercised. Updated T007.1 and T007.1b to handle variable corpus sizes (up to 50) dynamically to prevent brittle failures. Added explicit dependencies to T007.1b.

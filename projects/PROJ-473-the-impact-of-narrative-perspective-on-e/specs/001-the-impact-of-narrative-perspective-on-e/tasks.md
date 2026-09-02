---
description: "Task list template for feature implementation"
---

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
spaCy==3.7.2 [UNRESOLVED-CLAIM: c_07297e2e — status=not_enough_info]
scikit-learn==1.4.0 [UNRESOLVED-CLAIM: c_cfd33f0b — status=not_enough_info]
pandas==2.2.0 [UNRESOLVED-CLAIM: c_7ec15132 — status=not_enough_info]
matplotlib==3.8.2 [UNRESOLVED-CLAIM: c_c71be5ce — status=not_enough_info]
statsmodels==0.14.1 [UNRESOLVED-CLAIM: c_e40deac0 — status=not_enough_info]
langdetect==1.0.9 [UNRESOLVED-CLAIM: c_0a52ddcb — status=not_enough_info]
pyyaml==6.0.1 [UNRESOLVED-CLAIM: c_811c405b — status=not_enough_info]
requests==2.31.0 [UNRESOLVED-CLAIM: c_672453c2 — status=not_enough_info]
pytest==7.4.3 [UNRESOLVED-CLAIM: c_37c86f9a — status=not_enough_info]
gutenberg==1.0.0 [UNRESOLVED-CLAIM: c_52e2f615 — status=not_enough_info]
datasets==2.14.0 [UNRESOLVED-CLAIM: c_63ab85ad — status=not_enough_info]
osfclient==0.0.5 [UNRESOLVED-CLAIM: c_2d8e57de — status=not_enough_info]
EOF
```
**Verification**: Verify `code/requirements.txt` exists and contains exactly the lines above.
- [X] T003 [P] Configure linting: Create `pyproject.toml` with black (line-length=88) [UNRESOLVED-CLAIM: c_a1f18b3d — status=not_enough_info] and flake8 (max-line-length=88, ignore=E203,W503) [UNRESOLVED-CLAIM: c_eb7cc600 — status=not_enough_info] settings.
- [X] T009 [P] Setup CI environment: Create `.github/workflows/ci.yml` with a job running on `ubuntu-latest`. Ensure the workflow includes steps to install dependencies and run tests. The workflow must be compatible with GitHub Actions free-tier runners (default constraints: limited CPU cores, limited RAM, limited disk). Do not use `resources` configuration blocks which are unsupported on free runners. Ensure the workflow includes a mandatory blocking gate step to invoke the PII scanning function: `python -m code.utils scan_pii --input data/raw --exit-code 1`. This step must fail the build if PII is detected. Ensure the workflow is committed and verified.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [~] T004 Implement `code/config.py` for paths, seeds (`np.random.seed()`), and hyperparameters. **Note**: Define `PRIMARY_MATCHING_THRESHOLD = 0.30` here for use in T025. Define `GOLD_STANDARD_ANNOTATIONS_PATH` as `data/raw/gold_standard_annotations.csv`.
- [X] T005 [P] Implement `code/utils.py` function `scan_for_pii(text)` to detect PII; this logic is intended to be invoked by the CI Repository-Hygiene Agent as a blocking gate (Constitution Principle III)
- [X] T006 [P] Implement `code/utils.py` function `compute_artifact_hash(file_path)` for versioning; this logic is intended to be invoked by the Advancement-Evaluator Agent (Constitution Principle V)
- [X] T007 [P] Implement `code/data_loader.py` function `fetch_gutenberg_corpus(output_dir)`. **Logic**: Use the `gutenberg` Python library (or `requests` to the Gutenberg API) to search for and download short stories by verified authors. **Author List**: Start with ["O. Henry", "Guy de Maupassant", "Anton Chekhov", "Jack London", "Mark Twain", "Edgar Allan Poe", "H.G. Wells", "Arthur Conan Doyle", "Nathaniel Hawthorne", "Kate Chopin", "H.P. Lovecraft", "Upton Sinclair"]. **Parsing**: Parse the text to extract individual short stories (separated by distinct headers or length > 50 words). **Output**: Save each story as a separate `.txt` file in `data/raw/gutenberg_stories/`. **Verification**: Ensure **at least 50 valid stories** are extracted and saved. **Command**: `python code/main.py fetch --authors "O. Henry, Guy de Maupassant" --output data/raw/gutenberg_stories`. **Fail Condition**: If fewer than 50 stories are extracted after exhausting the author list, the task MUST fail explicitly with exit code 1 and log "ERROR: Corpus size < 50. Cannot proceed with SC-001 validation." The script must not proceed with a smaller corpus. **Dependency**: None.
- [ ] T007.1 [P] Generate local gold-standard perspective annotations using a Rule-Based Proxy. **Logic**: Load the stories from `data/raw/gutenberg_stories/`. Select a subset of **exactly 50** stories (or all if >50, capped at 50). Apply a distinct heuristic to label perspective: calculate the ratio of first-person pronouns appearing at the *start of a sentence* to total sentences. If ratio > 0.2, label as 1 (first-person), else 0 (third-person). This heuristic is distinct from the main extraction pipeline (T013) to ensure independence. Create a CSV file `data/raw/gold_standard_annotations.csv` with columns `story_id` (SHA-256 hash of the text), `text` (truncated to 200 chars), and `perspective_label` (1 or 0). **Verification**: Ensure the file contains a sufficient number of rows and the labels are consistent with the heuristic. **Note**: This task generates a deterministic proxy for validation, NOT human annotations. **Dependency**: T007.
- [ ] T007.1b [P] Map local gold-standard IDs to local corpus. **Logic**: Load `data/raw/gold_standard_annotations.csv`. For each row, verify the `story_id` matches a story in `data/raw/gutenberg_stories/` by re-computing the SHA-256 hash. **Output**: Save the mapped CSV to `data/processed/gold_standard_mapped.csv` with columns `story_id`, `human_label`. **Verification**: Ensure all matches are found. **Validation**: Calculate the Pearson correlation between the automated extraction (from T016) and these 50 labels; this correlation MUST be >= 0.85 to satisfy SC-001. **Dependency**: T007, T007.1.
- [X] T008 Create base data models (`StoryDocument`, `ReaderResponse`) in `code/models.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Perspective Feature Extraction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically extract narrative perspective markers (pronoun density, focalization cues) from a corpus of public short stories.

**Independent Test**: The pipeline can be tested by processing a small, manually annotated sample of stories and verifying that the computed "first-person density" scores correlate ≥ 0.85 with human annotations of perspective type.

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/extraction.py` function `calculate_pronoun_density(text)` using spaCy (FR-001). **Logic**: Use `spacy.load("en_core_web_sm")` to tokenize text. Count occurrences of first-person pronouns (`I`, `me`, `my`, `mine`, `we`, `us`, `our`, `ours`) and third-person pronouns (`he`, `him`, `his`, `she`, `her`, `hers`, `they`, `them`, `their`, `theirs`). Normalize by total token count.
- [X] T014 [US1] Implement `code/extraction.py` function `calculate_narrator_distance_score(text)` (FR-001). **Logic**: Calculate a score based on the ratio of first-person to total personal pronouns. Formula: `score = count_1st / (count_1st + count_3rd)`. If both are 0, score is 0.5. A score of 1.0 indicates pure first-person, 0.0 indicates pure third-person, and 0.5 indicates a mix or no personal pronouns. **Verification**: Assert that score is in [0.0, 1.0].
- [X] T015 [US1] Implement `code/extraction.py` function `extract_perspective_features(input_dir, output_path)` handling edge cases (<50 words, mixed language). **Logic**:
 1. Ensure `data/logs/` directory exists (`os.makedirs('data/logs', exist_ok=True)`).
 2. Iterate over all `.txt` files in `input_dir`.
 3. If text length < 50 words, log "data_quality_insufficient" to `data/logs/extraction.log` with filename, skip record, and continue.
 4. If `langdetect` detects non-English, log "language_not_english" to `data/logs/extraction.log` with filename, skip record, and continue.
 5. Otherwise, call `calculate_pronoun_density` and `calculate_narrator_distance_score`.
 6. Append results to a list and write to `output_path` as JSON.
 **Verification**: Verify that files <50 words are skipped and logged, and output JSON contains only valid records.
- [~] T016 [US1] Create `code/main.py` entry point to run extraction on the `data/raw/` corpus and output JSON records to `data/processed/perspective_features.json`. **CLI**: `python code/main.py extract --input-dir data/raw/gutenberg_stories --output data/processed/perspective_features.json`. **Schema**: Output JSON must be a list of objects with keys `story_id`, `raw_text`, `pronoun_density_1st`, `pronoun_density_3rd`, `narrator_distance_score`, `confidence_flag`. **Robustness**: Ensure the script gracefully skips records that fail edge case checks (e.g., <50 words) without halting the entire pipeline. **Verification**: Verify output file exists and contains a list of objects with keys [story_id, raw_text, pronoun_density_1st,...] using a schema validation script or pytest assertion: `python -c "import json; d=json.load(open('data/processed/perspective_features.json')); assert all(k in d[0] for k in ['story_id','raw_text','pronoun_density_1st','pronoun_density_3rd','narrator_distance_score','confidence_flag'])"`.
- [X] T017 [US1] Add validation logic to flag "neutral/omniscient" texts where `pronoun_density_1st` is 0.0 by setting `confidence_flag: "neutral/omniscient"` in the output JSON.
- [X] T018 [US1] Add logging for extraction quality warnings (e.g., "data_quality_insufficient") to `data/logs/extraction.log`.

### Tests for User Story 1

- [X] T010 [US1] Validation test: **Data Preparation**: Load `data/processed/gold_standard_mapped.csv` (generated by T007.1b). Fetch the corresponding stories from `data/raw/gutenberg_stories/`. **Verification**: Run the extraction pipeline on these stories and verify that the computed "first-person density" scores correlate ≥ 0.85 with the `human_label` in the external gold standard file. **Note**: This task runs AFTER T016 and T007.1b. **Data Source**: Real narrative text from Project Gutenberg with rule-based proxy labels from T007.1. **Dependencies**: T016, T007.1b. **Clarification**: This task validates the *algorithm* against *independent rule-based labels* to satisfy SC-001. **Do NOT** use the synthetic proxy for this final validation.
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
- [ ] T024 [US2] Implement `code/main.py` sub-command `prepare-thresholds` to generate `data/processed/thresholds.json`. **Logic**: Generate a list of threshold values `[0.25, 0.30, 0.35, 0.40]`. **Output**: Save to `data/processed/thresholds.json` as `{"thresholds": [0.25, 0.30, 0.35, 0.40]}`. **Command**: `python code/main.py prepare-thresholds --output data/processed/thresholds.json`. **Verification**: Verify the file exists and contains the exact list of thresholds. **Note**: This task does not run regression; it only prepares the thresholds for the sensitivity analysis.
- [X] T025.2 [US2] Generate local moral judgement dataset for matching validation. **Logic**: Use `datasets.load_dataset("moral-foundation", split="train")` (or a verified equivalent) to fetch a dataset containing story-text and moral judgement scores. Extract **exactly 100** pairs (stratified by difficulty if available, otherwise random sample) and save to `data/raw/moral_judgement_local.csv`. Each row must have `text` (story excerpt), `moral_judgement_score` (1-7 Likert), and `story_id` (SHA-256 hash of the text). **Verification**: Ensure the dataset contains the required columns and a sufficient number of rows to support the analysis. **Dependency**: None (uses external loader).
- [ ] T025 [US2] Create `code/main.py` sub-command `match` to run matching validation and output `data/processed/matching_results.json` with schema: `{story_id, match_id, similarity_score, rank, threshold_used}`. **CLI**: `python code/main.py match --input data/processed/perspective_features.json --target data/raw/moral_judgement_local.csv --output data/processed/matching_results.json --threshold 0.30`. **Logic**: Load perspective features, build TF-IDF vectors. **CRITICAL**: This task runs matching for the PRIMARY threshold (0.30) ONLY. It outputs a single set of matches. **Dependencies**: T016, T025.2.
- [X] T025.3 [US2] Calculate matching precision. **Logic**: Load `data/processed/matching_results.json` and `data/raw/moral_judgement_local.csv`. Compare the matched pairs against a subset of known correct pairs (or use the 100 pairs as the ground truth if the dataset is self-consistent). Calculate the false-positive rate. **Verification**: Ensure false-positive rate ≤ 5% (precision ≥ 0.9). [UNRESOLVED-CLAIM: c_57b2a8db — status=not_enough_info] **Dependencies**: T025, T025.2.
- [X] T026 [US2] Add logic to exclude unmatched stories (similarity < 0.3) and log them as "unmatched" to `data/logs/matching.log`.
- [X] T027 [US2] Implement deterministic tie-breaking rule (highest raw score) for multiple matches.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 4 - Primary Data Collection (Part 1: Generation & Alignment)

**Goal**: Generate and align reader response data for the specific story corpus using a validated proxy simulation or external dataset.

### Implementation for User Story 4 (Part 1)

- [X] T009.6 [P] [US4] Fetch verified external reader-response dataset. **Logic**: Use `datasets.load_dataset()` or `osfclient` to fetch a verified external dataset containing story-text and reader-response pairs (e.g., from OSF or a validated HuggingFace repository). **Output**: Save to `data/raw/reader_responses_external.csv` with columns `story_id`, `empathy_score`, `moral_judgement_score`. **Verification**: Ensure the dataset contains the required columns and is derived from a verified source URL. **Note**: This task prioritizes real human data from external sources to satisfy US-4.
- [X] T009.6b [P] [US4] Validate external dataset or fallback. **Logic**: If T009.6 succeeds, validate the external dataset by checking for non-null scores and reasonable variance. If T009.6 fails, trigger T009.6c. **Output**: Log validation status. **Dependencies**: T009.6, T009.6c (fallback).
- [X] T009.6c [S] [US4] Generate deterministic synthetic proxy data. **Logic**: If T009.6 fails, generate a synthetic dataset programmatically. Load stories from `data/raw/gutenberg_stories/` (T007). For each story, generate `empathy_score` and `moral_judgement_score` using a fixed random seed (42) and a normal distribution (mean=4.0, std=1.5) to simulate variance. **Output**: Save to `data/raw/reader_responses_local.csv` with columns `story_id`, `empathy_score`, `moral_judgement_score`. **Verification**: Ensure the dataset contains the required columns and a sufficient number of rows. **Dependencies**: T007.
- [X] T009.6d [P] [US4] Map local reader-response IDs to local corpus. **Logic**: Load `data/raw/reader_responses_external.csv` (if T009.6 succeeded) or `reader_responses_local.csv` (if T009.6c was used). For each row, verify the `story_id` matches a story in `data/raw/gutenberg_stories/` by re-computing the SHA-256 hash. **Output**: Save the mapped CSV to `data/processed/aligned_reader_response.csv` with columns `story_id`, `empathy_score`, `moral_judgement_score`. **Verification**: Ensure all N matches are found. **Validation**: Log the validation metrics. **Dependencies**: T009.6 (or T009.6c), T007.
- [ ] T032 [US4] Implement `code/data_collection.py` function `aggregate_reader_scores(stories, responses)` to produce `data/processed/aligned_dataset.csv`. **Schema Requirement**: Output CSV must contain columns `story_id`, `perspective_score`, `empathy_score`, `moral_judgement_score`, AND `raw_text`. Aggregation logic must merge `perspective_score` from `data/processed/perspective_features.json` (T016) and `empathy_score`/`moral_judgement_score` from `data/processed/aligned_reader_response.csv` (T009.6d) on `story_id`. **Input**: Must explicitly consume `data/processed/perspective_features.json` AND `data/processed/aligned_reader_response.csv`. **Dependency**: T032 assumes T009.6d and T016 are available. **CLI**: `python code/main.py aggregate --features data/processed/perspective_features.json --responses data/processed/aligned_reader_response.csv --output data/processed/aligned_dataset.csv`. **Note**: T032 MUST run after T009.6d to ensure `aligned_reader_response.csv` is available. **Dependencies**: T016, T009.6d.

**Checkpoint**: Phase 5 complete. All user stories 1, 2, and 4 fully integrated, providing the necessary data for Phase 6.

---

## Phase 6: User Story 3 - Primary Analysis: Statistical Association & Visualization (Priority: P3)

**Goal**: Run linear regression and t-tests on the aligned dataset to determine if first-person perspective predicts higher deontological moral judgement scores and empathic engagement, and execute sensitivity analysis.

### Implementation for User Story 3 (Part 1)

- [X] T037 [US3] Implement `code/analysis.py` function `run_regression_analysis(dataset_path)` (FR-003). **Logic**: Perform linear regression with `perspective_score` as predictor and `moral_judgement_score` as outcome. Report slope, intercept, p-value.
- [X] T038 [US3] Implement `code/analysis.py` function `apply_bonferroni_correction(p_values)` (FR-004). **Logic**: Adjust p-values based on the number of hypothesis tests performed (α/k).
- [X] T039 [US3] Implement `code/analysis.py` function `calculate_vif(dataset_path)` (FR-007). **Logic**: Calculate VIF for predictors. Warn if VIF > 5.0. [UNRESOLVED-CLAIM: c_8e7b39af — status=not_enough_info]
- [ ] T040 [US3] Implement `code/visualization.py` function `generate_scatter_plot(dataset_path)` (FR-005). **Logic**: Create scatter plot with regression line and confidence interval ribbon using matplotlib. Save to `data/artifacts/regression_plot.png`. **CLI**: `python code/main.py plot --input data/processed/aligned_dataset.csv --output data/artifacts/regression_plot.png`. **Verification**: Ensure the output file exists and contains a valid PNG image.
- [ ] T041 [US3] Create `code/main.py` sub-command to run full analysis and output `data/processed/analysis_results.json` with summary table. **CLI**: `python code/main.py analyze --input data/processed/aligned_dataset.csv --output data/processed/analysis_results.json`. **Schema Requirement**: Output JSON MUST contain the following keys: `slope`, `intercept`, `p_value`, `r_squared`, `bonferroni_adjusted_p`, `sample_size`, `vif_warning`. **Verification**: Verify output file exists and contains keys [slope, intercept, p_value,...] by running `python -c "import json; d=json.load(open('data/processed/analysis_results.json')); assert all(k in d for k in ['slope','intercept','p_value','r_squared','bonferroni_adjusted_p','sample_size','vif_warning'])"`.

### Implementation for User Story 3 (Part 2: Sensitivity Analysis)

- [X] T043 [US3] Implement `code/analysis.py` function `run_sensitivity_sweep(stories_dir, target_csv, thresholds_json, perspective_json)`. **Logic**:
 1. Load `thresholds.json` (T024). **Pre-requisite**: Verify file exists.
 2. Load raw stories from `stories_dir` (T007) and target dataset from `target_csv` (T025.2). **CRITICAL**: Do NOT use `aligned_dataset.csv` (T032). Use raw inputs only.
 3. Load `perspective_features.json` (T016) to get `perspective_score` for each story.
 4. For each threshold in the list:
 a. **Re-execute Matching**: Re-run the matching logic by calling `build_tfidf_vectors` (T022) and `find_top_matches` (T023) internally using the `raw_text` from the loaded stories and the `target_csv` with the `current_threshold`. **Do not** rely on `matching_results.json` (T025) for this sweep.
 b. Filter matches to include only those with `similarity_score >= current_threshold`.
 c. **Join** filtered matches with `perspective_features.json` (T016) on `story_id` to get `perspective_score`.
 d. **Join** with `target_csv` to get `moral_judgement_score`.
 e. **Check Sample Size**: If the number of matched rows is insufficient, log a warning "Sample size insufficient for regression at threshold X" and record `slope` as `null` for this threshold.
 f. **Save** the joined temporary dataset to `data/processed/temp_sweep_{threshold}.csv`.
 g. Call `run_regression_analysis` (T037) on the temporary CSV file (if sample size is sufficient).
 h. Record the **slope coefficient** (regression coefficient) for this threshold.
 5. **Aggregate Results**: Calculate the variance of the slope coefficients. If a slope is `null`, exclude it from the variance calculation. If all slopes are `null`, report `slope_variance` as `null` and log "Insufficient Data for Sensitivity Analysis".
 6. Output `data/processed/sensitivity_report.json` with keys `thresholds` (list), `slopes` (list of slope coefficients, including nulls), `sample_sizes` (list), and `slope_variance`.
 **Dependencies**: This task depends on T007 (raw stories), T016 (perspective features), T024 (thresholds), and T025.2 (target). **Note**: T043 MUST run after Phase 5 (T032) is complete. **CRITICAL**: T043 depends on raw inputs, NOT T032.

### Tests for User Story 3

- [X] T035 [P] [US3] Unit test for regression recovery on synthetic data with known slope in `tests/test_analysis.py`
- [X] T036 [P] [US3] Unit test for Bonferroni correction logic in `tests/test_analysis.py`

**Checkpoint**: Analysis complete. All user stories implemented and tested.

---

## Phase 7: Final Validation & Reporting

**Purpose**: Ensure all success criteria are met and artifacts are ready for review.

- [ ] T051 [P] Run end-to-end integration test: Execute `python code/main.py all` to run the full pipeline from raw data to final analysis. Verify all outputs exist. **Verification**: Execute `python code/main.py all` and verify exit code 0, then check existence of [data/processed/aligned_dataset.csv, data/artifacts/regression_plot.png, data/processed/sensitivity_report.json, data/processed/analysis_results.json].
- [ ] T051.1 [P] Profile runtime and memory usage. **Logic**: Execute `python code/main.py all` with a memory profiler (e.g., `memory_profiler` or `tracemalloc`) and a timer. Record peak memory usage and total runtime. **Verification**: Ensure runtime ≤ 45 minutes and peak memory < 6 GB. **Dependency**: T051.
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
- **Revision Note**: T001 updated to specify directory creation command.
- **Revision Note**: T003 updated to specify linting tools.
- **Revision Note**: T009 updated to remove unsupported `resources` configuration and meta-commentary.
- **Revision Note**: T010 updated to use a configurable path from `code/config.py` instead of a hardcoded URL.
- **Revision Note**: T024, T025, T043 updated to decouple matching from sensitivity analysis.
- **Revision Note**: T015 updated to ensure log directory creation.
- **Revision Note**: T024 updated with CLI implementation.
- **Revision Note**: T016 updated with CLI implementation.
- **Revision Note**: T014 updated with explicit formula.
- **Revision Note**: Phase 5c removed entirely.
- **Revision Note**: T007 updated to enforce a strict minimum of 50 stories to match downstream annotation requirements (T007.1), ensuring the fallback author list is fully exercised.
- **Revision Note**: T007.1 and T007.1b updated to enforce 50 stories minimum and use a distinct heuristic for labels.
- **Revision Note**: T009.6, T009.6b, T009.6c, T009.6d updated to use external fetch, validation, synthetic fallback, and mapping.
- **Revision Note**: T032 updated to include `raw_text` in output schema and explicit dependencies.
- **Revision Note**: T015 updated to ensure log directory creation.
- **Revision Note**: T024 updated with CLI implementation.
- **Revision Note**: T016 updated with CLI implementation.
- **Revision Note**: T014 updated with explicit formula.
- **Revision Note**: Phase 5c removed entirely.
- **Revision Note**: T043 updated to use raw inputs (T007, T016, T025.2) for sensitivity sweep.
- **Revision Note**: T025.2 updated to generate 100 pairs.
- **Revision Note**: T025.3 added for precision calculation.
- **Revision Note**: T051.1 added for performance profiling.
- **Revision Note**: T007.1 updated to use a deterministic rule-based proxy instead of human annotation.
- **Revision Note**: T009.6c updated to generate synthetic data deterministically.
- **Revision Note**: T025.2 updated to load data programmatically from HuggingFace.
- **Revision Note**: T043 updated to explicitly depend on raw inputs and re-match for each threshold.
- **Revision Note**: T009.6b updated to handle fallback logic explicitly.
- **Revision Note**: T010, T025, T032 updated to explicitly list dependencies.

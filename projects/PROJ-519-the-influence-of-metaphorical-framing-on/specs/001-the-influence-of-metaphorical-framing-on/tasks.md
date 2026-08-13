# Tasks: The Influence of Metaphorical Framing on Attitudes Towards Mental Health Treatment

**Input**: Design documents from `specs/001-metaphor-framing-attitudes/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

- [ ] T001a [P] Create `src/` and `tests/` directories at repository root
- [ ] T001b [P] Create `data/` directory structure (`raw`, `processed`, `derived`)
- [ ] T001c [P] Create `config/` directory
- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` containing pinned versions: pandas==2.1.0, numpy==1.24.3, scipy==1.11.4, statsmodels==0.14.0, scikit-learn==1.3.2, vaderSentiment==3.3.2, seaborn==0.13.0, matplotlib==3.8.0, pytest==7.4.2, requests==2.31.0, python-dotenv==1.0.0
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create data schema contracts in `specs/001-metaphor-framing-attitudes/contracts/` (experimental-data.schema.yaml, discourse-data.schema.yaml, statistical-result.schema.yaml)
- [ ] T005 [P] Setup data directory structure (`data/raw`, `data/processed`, `data/derived`) with `.gitkeep`
- [X] T006 Create `config/simulation_config.yaml` for pinned random seeds, synthetic data parameters (experimental only), and sampling thresholds (including `corpus_size` default=1000, `MAX_RUNTIME_SECONDS`, `SAMPLE_SIZE_FALLBACK`)
- [X] T007 Implement base logging and error handling in `src/__init__.py` and `src/utils/logger.py`
- [ ] T008 Setup environment configuration management (dotenv) for API keys (if needed) and paths
- [X] T015 [P] [US1] Create `src/data_models.py` defining `Participant` and `Vignette` entities (US1 Data Model)
- [X] T024 [P] [US2] Create `src/data_models.py` (append) defining `DiscoursePost` entity (US2 Data Model)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Experimental Vignette Exposure & Outcome Measurement (Priority: P1) 🎯 MVP

**Goal**: Implement the controlled vignette experiment to measure causal effects of metaphorical framing on stigma (CAMI) and help-seeking intent.

**Independent Test**: Run a batch of simulated participants through the three conditions, verifying that the correct vignette text is displayed for the assigned condition and that the resulting CAMI/Likert scores are recorded correctly in the dataset without text leakage.

### Tests for User Story 1

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. These are Test Implementation tasks.

- [X] T009 [P] [US1] [Test Implementation] Implement contract test for vignette text integrity (no framing leakage) in `tests/test_vignette_engine.py`
- [X] T010 [P] [US1] [Test Implementation] Implement integration test for full experimental flow (assignment -> exposure -> scoring) in `tests/test_experimental_flow.py`

### Implementation for User Story 1

- [X] T011 [US1] Create `src/vignette_engine.py` with FR-001: Generate three distinct vignette texts (Battle, Journey, Medical) with constant clinical details and varying metaphors
- [ ] T012 [US1] Implement `src/data_ingestion.py` (Experimental Module) for loading vignette templates from `data/raw/vignettes/`
- [ ] T013 [US1] Create `src/experiment_runner.py` to assign participants to conditions (Battle, Journey, Medical). **Input**: `data/raw/simulated_participants.csv` (if simulating) or `data/raw/survey_responses.json` (if real). **Output**: `data/processed/experimental_assignments.csv`
- [ ] T013b [US1] Implement `src/survey_interface.py` (or `src/data_collection.py`): Create the mechanism to administer the CAMI scale and help-seeking Likert scale to human participants immediately after vignette exposure (FR-002). This may involve integrating with Qualtrics/Prolific APIs or creating a local web interface. **Input**: `data/processed/experimental_assignments.csv`. **Output**: `data/raw/survey_responses.json`.
- [ ] T014 [US1] Implement `src/cami_scoring.py` to administer CAMI scale and help-seeking Likert scale immediately after exposure (FR-002). **Input**: `data/raw/survey_responses.json` (raw survey data). **Output**: `data/processed/cami_scores.csv`
- [ ] T014a [US1] Implement `src/data_ingestion.py` (Real Participant Loader): Create logic to load real participant data from `data/raw/survey_responses.json` (schema: participant_id, condition, raw_responses). This task ensures the system can handle actual survey data as required by FR-002 and US-1.
- [ ] T016 [US1] Implement data export logic to write raw experimental results to `data/processed/experimental_results.csv` with SHA-256 checksums saved to `data/processed/experimental_results.csv.sha256`
- [ ] T017 [US1] Add logic to flag attention check failures and identical responses for exclusion (Edge Case)
- [ ] T017a [US1] Implement `src/data_validation.py` to validate real participant data integrity before analysis (Edge Case).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Independent Discourse Analysis & Sentiment Correlation (Priority: P2)

**Goal**: Implement the methodological feasibility demonstration for the observational analysis using a REAL public mental health discourse corpus (per Spec Assumption) to validate pipeline logic (regex, VADER, robust regression). If real data is unavailable, the system MUST FAIL LOUDLY (no synthetic fallback).

**Independent Test**: Process a small, fixed sample of posts, verifying that posts containing "battle" are correctly identified, their VADER sentiment scores are computed, and a robust regression model (with Huber-White SEs) can be fitted to show the relationship between metaphor count and sentiment.

### Tests for User Story 2

- [ ] T018 [P] [US2] [Test Implementation] Contract test for metaphor keyword extraction regex in `tests/test_sentiment.py`
- [ ] T019 [P] [US2] [Test Implementation] Integration test for robust regression with Huber-White SEs in `tests/test_statistical_modeling.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Create `src/data_ingestion.py` (Corpus Acquirer): Implement the primary mechanism to acquire a REAL public mental health discourse corpus. **Logic**: 1. Attempt fetch from Pushshift API (or verified HuggingFace dataset). 2. If API fails, attempt download of a verified static corpus from `data/raw/static_corpus.json` (see T020b). 3. If both fail, raise a hard error (FAIL LOUDLY). **NO synthetic generation allowed**. **Output**: `data/raw/real_corpus.json`.
- [ ] T020b [P] [US2] Create `scripts/fetch_static_corpus.py`: A script to download a pre-scraped static corpus from a verified HuggingFace dataset (e.g., `mental_health_discourse` or equivalent) and save it to `data/raw/static_corpus.json`. **Logic**: 1. Attempt download from HuggingFace. 2. If download fails, raise a hard error (FAIL LOUDLY). **NO synthetic generation allowed**.
- [ ] T020a [P] [US2] Implement `src/data_ingestion.py` (Static Loader Module): Create a loader function that reads a static JSON/CSV file from `data/raw/static_corpus.json` if it exists. **Schema**: `text`, `upvotes`, `comments`, `author`, `timestamp`.
- [ ] T020c [US2] Implement `src/data_ingestion.py` (Static Corpus Validator): Create logic to validate that the static corpus file (`data/raw/static_corpus.json`) contains the required metaphor keywords and metadata. **Logic**: 1. Check for required columns. 2. Check for presence of at least one post containing each metaphor keyword. 3. If validation fails, raise a hard error (FAIL LOUDLY).
- [ ] T020 [US2] Implement `src/data_ingestion.py` (Main Loader): Create the primary data loader that orchestrates the fallback chain. **Logic**: 1. Attempt Real Fetch (T021). 2. If Real Fetch fails but static file exists (T020a), load static file. 3. If Real Fetch fails and static file missing, raise a hard error (FAIL LOUDLY).
- [ ] T021a [US2] Implement `src/data_ingestion.py` (Integration Logic): Add logic to the main data ingestion flow to trigger the real corpus acquirer (T021) if the real fetch fails AND the static file is missing, controlled by a `USE_REAL_DATA_ONLY` config flag (default True). This task ensures the fallback chain is correctly executed.
- [ ] T025a [US2] Implement chunked/streaming processing logic for large datasets to respect 7GB RAM limit (Assumption). **Input**: Raw corpus from T021/T020. **Output**: Streamed data chunks.
- [ ] T025b [US2] Implement sampling fallback logic: If streaming exceeds time limit (`MAX_RUNTIME_SECONDS` from `config/simulation_config.yaml`) or memory, automatically switch to a **stratified sample** of N rows (`SAMPLE_SIZE_FALLBACK` from config) based on metaphor keyword frequency to preserve distribution, and log the sampling rate.
- [ ] T022 [US2] Implement `src/sentiment_analysis.py` (FR-003, FR-004): Filter posts by metaphor keywords ("battle", "journey", "burden") using regex, compute VADER compound scores, and store metadata (upvotes, comments). **Input**: Streamed/sampled data from T025a/b.
- [ ] T023 [US2] Implement `src/statistical_modeling.py` (FR-006, FR-009): Execute robust linear regression (Huber-White SEs) modeling sentiment vs. metaphor frequency, controlling for post length/engagement. **Input**: Processed data from T022. **Output**: Include VIF check; if VIF ≥ 5, write 'HIGH' to a new column `vif_flag` in the results CSV and log a specific warning message.
- [ ] T026 [US2] Export processed discourse data and regression results to `data/derived/discourse_analysis_results.csv`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Inference & Visualization Generation (Priority: P3)

**Goal**: Transform raw data into interpretable scientific results (ANOVA, post-hoc corrections, visualizations).

**Independent Test**: Feed the system a pre-generated CSV of experimental scores, verifying that the ANOVA F-statistic and p-value are calculated correctly, that post-hoc tests apply Bonferroni correction, and that the resulting bar chart displays the three conditions with error bars.

### Implementation for User Story 3

- [ ] T027 [US3] Implement `src/statistical_modeling.py` (Experimental Module): Perform one-way ANOVA on experimental data (FR-005) to test for differences across conditions. **Input**: `data/processed/experimental_results.csv` (from T016).
- [ ] T028 [US3] Implement multiple-comparison correction (Bonferroni) for pairwise comparisons (Battle vs. Journey, Battle vs. Control, Journey vs. Control) (FR-008). Calculate adjusted alpha (e.g., a value consistent with the number of comparisons)..
- [ ] T028a [US3] Implement `src/statistical_modeling.py` (Config Writer): Calculate the adjusted alpha value using a standard Bonferroni correction factor. and write it to `data/derived/analysis_config.json` for use by T031.
- [ ] T029 [US3] Implement `src/visualization.py` (FR-007): Generate bar charts with error bars (CI) for ANOVA means.
- [ ] T030 [US3] Implement `src/visualization.py`: Generate scatter plot for discourse analysis (Metaphor Density vs. Sentiment) with fitted regression line.
- [ ] T031 [US3] Create `src/report_generator.py` to output a summary JSON/CSV containing F-statistic, p-values, adjusted alpha flags (SC-001, SC-003), regression coefficients (SC-002), and the `vif_flag` status (from T023). **Input**: Read `adjusted_alpha` from `data/derived/analysis_config.json`.
- [ ] T032 [US3] Ensure visualizations handle null results (p > 0.05) correctly without crashing (Edge Case)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `docs/` and `README.md`
- [ ] T034 Code cleanup and refactoring
- [ ] T035 Performance optimization: Ensure VADER and regression complete within 1 hour for 10k posts (SC-004)
- [ ] T036 [P] Run quickstart.md validation
- [ ] T037 Verify all data files are checksummed and raw/processed separation is maintained

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent pipeline, uses real data (or fails) as per Spec
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data outputs from US1 (ANOVA) and US2 (Regression)

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
# Launch all tests for User Story 1 together:
Task: "Implement contract test for vignette text integrity in tests/test_vignette_engine.py"
Task: "Implement integration test for full experimental flow in tests/test_experimental_flow.py"

# Launch implementation models and engine together:
Task: "Create src/vignette_engine.py"
Task: "Create src/data_models.py"
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
3. Add User Story 2 → Test independently → Deploy/Demo (Pipeline Validation with Real Data)
4. Add User Story 3 → Test independently → Deploy/Demo (Full Reporting)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Experimental Core)
 - Developer B: User Story 2 (Discourse Pipeline)
 - Developer C: User Story 3 (Stats & Viz)
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
- **Data Integrity**: The loader for US-2 (T021, T020) implements a strict fallback chain: Real Fetch (Fail Loudly if missing) -> Static File (if exists and validated) -> Hard Error. T020b, T020a, and T020c ensure the static path is functional and validated.
- **Compute Constraints**: All processing must fit within 7GB RAM; use streaming/chunking (T025a) and stratified sampling fallback (T025b) for large datasets.
- **Execution Order**: T027 (ANOVA) and T031 (Report Gen) MUST run AFTER T016 (Experimental Export) and T026 (Discourse Export) to ensure data availability.
- **Real Data Only**: No synthetic data is generated for US-2. If real data is unavailable, the system fails loudly.
- **Survey Interface**: T013b explicitly implements the mechanism for real human data collection, ensuring FR-002 is met for real participants.
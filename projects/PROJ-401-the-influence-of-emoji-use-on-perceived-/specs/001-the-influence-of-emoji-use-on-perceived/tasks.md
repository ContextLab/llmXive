# Tasks: The Influence of Emoji Use on Perceived Emotional Intensity in Text

**Input**: Design documents from `/specs/001-influence-of-emoji-on-intensity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are REQUIRED to ensure MVP integrity.

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

- [ ] T001a [P] Create `src/` directory structure (`src/data`, `src/analysis`, `src/utils`, `src/reports`)
- [ ] T001b [P] Create `tests/` directory structure (`tests/unit`, `tests/integration`, `tests/contract`)
- [ ] T001c [P] Create `data/` directory structure (`data/raw`, `data/processed`, `state`)
- [X] T002 [P] Initialize a Python project with dependencies: `ml-datasets`, `pandas`, `numpy`, `scipy`, `statsmodels`, `seaborn`, `emoji`, `tqdm`, `pytest`, `powerlaw` in `requirements.txt`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and pre-study validation that MUST be complete before ANY user story can be implemented. **Includes mandatory Power Analysis (FR-006) to determine minimum N BEFORE data loading.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This phase includes the mandatory Power Analysis required BEFORE data loading.

- [X] T004 [P] Implement `src/utils/io.py` with logging configuration, checksum verification helpers, and global random seed setting (`seed=42`)
- [X] T005 [P] Create `src/data/loaders.py` skeleton: Enforce "fail loud" policy for **raw text corpus** (must be real, no synthetic text fallback) AND **intensity scores**. The loader MUST raise `DataUnavailableError` immediately if `human_intensity_score` is missing. Do NOT return a status for a proxy path.
- [X] T006 [P] Setup `src/data/validation.py` to check for human-rated intensity scores in the loaded dataset
- [ ] T007 [P] Create base data contracts in `src/data/contracts/` defining `Message` (text, emoji metrics) and `AnalysisResult` schemas
- [ ] T008 [P] Configure directory structure for `data/raw/`, `data/processed/`, and `state/`
- [ ] T021 [P] [US2] Implement `src/analysis/power.py` to determine minimum sample size N required for **Cohen's f² ≥ 0.02, power=0.80, α=0.05**. **Output**: `state/power_analysis.yaml`. **Note**: This MUST run BEFORE data loading (T012) to validate dataset sufficiency. **Prerequisite**: T004, T007.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Verification, and Emoji Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Load a public text message corpus, verify `human_intensity_score` presence as a blocking gate, and extract objective emoji metrics.

**Independent Test**: Run the extraction script on a sample; verify output CSV contains `message_id`, `emoji_present` (bool), `emoji_count` (int), `emoji_types` (list of strings), with no missing values for valid records.

### Tests for User Story 1 (REQUIRED) ⚠️

- [X] T009 [P] [US1] Contract test for schema validation in `tests/contract/test_schema.py`
- [X] T010 [P] [US1] Unit test for emoji extraction logic (empty text, skin tone modifiers) in `tests/unit/test_extraction.py` <!-- ATOMIZE: requested -->
- [X] T016 [P] [US1] Unit test for `DataUnavailableError` raising in `tests/unit/test_loader_errors.py`
- [X] T017 [P] [US1] Integration test for report generation in `tests/integration/test_data_unavailable.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement data loader in `src/data/loaders.py` to fetch candidate datasets (starting with **`cmu/text_messages_v1`** or equivalent from the verified list). **MUST verify presence of `human_intensity_score` column immediately.**
 - **IF missing**: Raise `DataUnavailableError`, trigger T018 (Report Generation), and **HALT** the pipeline.
 - **IF present**: Proceed to T011.
 - **Prerequisite**: T021 (Power Analysis) must be complete to ensure we know the required N before loading.
- [X] T018 [US1] [P] Implement `src/reports/data_unavailable.py` to generate a formal "Data Unavailable" report detailing the missing modality (`human_intensity_score`), the dataset checked, and the reason for halting. **Triggered ONLY by T012 failure. This task replaces Phase 4.**
- [X] T011 [US1] [P] Implement `src/data/preprocessing.py` with `extract_emoji_features(text)` function using `emoji` library to handle Unicode normalization (base points) and skin tone modifiers. **Prerequisite: T012 must have completed successfully (data present).**
- [ ] T013 [US1] [P] Create pipeline step to join raw text with extracted features, handling edge cases (zero-length text, encoding errors) gracefully. **Prerequisite: T012 must have completed successfully (data present).**
- [ ] T014 [US1] [P] Save processed features to `data/processed/features.csv` with checksums recorded in `state/`. **Condition: Execute ONLY IF T012 succeeded (intensity score present). If T012 halted, skip this task.**
- [ ] T015 [US1] [P] Add logging for extraction errors and skipped records to ensure data hygiene

**Checkpoint**: If data is missing, the project terminates cleanly with a valid scientific report. If data is present, features are extracted and saved.

---

## Phase 4: User Story 2 - Sample Size Verification (Conditional)

**Goal**: Verify that the loaded dataset meets the minimum sample size requirement calculated in Phase 2.

**Independent Test**: Run verification on a valid dataset; verify `state/verification.yaml` contains the pass/fail status against the pre-calculated N.

### Tests for Verification (REQUIRED) ⚠️

- [ ] T020 [P] [US2] Unit test for verification logic in `tests/unit/test_power.py`

### Implementation for Verification

- [ ] T022 [US2] Compare actual N (from loaded data) against the required N (from `state/power_analysis.yaml` in Phase 2). **Flag "Power Limitation Warning"** if N < required N. **Output**: `state/verification.yaml`. **Prerequisite**: T014 (Data Extracted).

**Checkpoint**: Sample size validated. If underpowered, a warning is recorded but analysis may proceed with caveats.

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Compute correlation and regression (controlling for text length/punctuation), apply Bonferroni correction, and generate visualizations.

**Independent Test**: Run analysis on pre-generated dataset; verify report includes correlation matrix, regression table (Beta, p-values), adjusted p-values, and plot images.

### Tests for User Story 3 (REQUIRED) ⚠️

- [X] T023 [P] [US3] Unit test for Bonferroni correction logic in `tests/unit/test_stats.py`
- [X] T024 [P] [US3] Integration test for reproducibility (bit-for-bit match on re-run) in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [ ] T025 [US3] Implement `src/analysis/stats.py` with Pearson/Spearman correlation functions and linear regression (statsmodels) controlling for text length and punctuation.
 - **Regression Logic**: Use Lasso Regression **ONLY when 'EmojiType' is included as a predictor**.
 - **Alpha Selection**: Determine optimal alpha via **5-fold cross-validation** (Per Plan Phase 3, Task 3.3).
 - **Output**: Calculate and return the Standardized Regression Coefficient (Beta) as the primary effect size metric.
 - **Prerequisite**: T012 must have completed successfully (data present) AND T022 (Verification) must be complete.
- [ ] T026 [US3] Implement Bonferroni correction logic for multiple comparisons (emoji types) in `src/analysis/stats.py`
- [ ] T027 [US3] Implement visualization generation in `src/analysis/viz.py` (seaborn) for coefficient plots and intensity distributions
- [ ] T028 [US3] Create `src/main.py` to orchestrate the full pipeline: Load -> Extract -> (Halt if missing) -> Power Analysis -> Verify -> Analyze -> Report
- [ ] T029 [US3] Generate final `results.json` (containing statistics) and `report.md` (containing interpretation and effect sizes). **Do NOT generate PDF** to ensure bit-for-bit reproducibility (SC-004).

**Checkpoint**: All user stories should now be independently functional (conditional on data availability)

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Update `docs/` with quickstart instructions and data source citations
- [ ] T031 Code cleanup and refactoring to ensure modularity
- [ ] T032 Performance optimization to ensure runtime ≤ 300s for N=1000 and ≤ 0.3s per message for N < 1000
- [ ] T033 [P] Additional unit tests for edge cases (empty strings, non-standard emoji sequences)
- [ ] T034 [P] Run `quickstart.md` validation and verify all checksums

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Includes Power Analysis.**
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **Data Unavailable Reporting (Phase 3)**: Triggered by T012 failure (missing data)
- **User Story 2 (P2 - Verification)**: Can start after Foundational (Phase 2) AND successful data loading (Phase 3)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) AND successful data loading (Phase 3) AND Verification (Phase 4)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/Contracts before services/logic
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
Task: "Contract test for schema validation in tests/contract/test_schema.py"
Task: "Unit test for emoji extraction logic in tests/unit/test_extraction.py"

# Launch all models for User Story 1 together:
Task: "Implement src/data/preprocessing.py"
Task: "Implement src/data/loaders.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 + Data Unavailable Reporting)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Ingestion & Extraction)
4. **STOP and VALIDATE**: Test the pipeline on a dataset without `human_intensity_score` to ensure it halts and generates the report.
5. Deploy/demo the "Data Unavailable" finding if no valid data is found.

### Incremental Delivery (If Data Exists)

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. If data is available:
 - Add Phase 4 (Verification) → Test independently
 - Add Phase 5 (Statistical Analysis) → Test independently
 - Add Phase 6 (Polish)
4. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Ingestion)
 - Developer B: Phase 4 (Verification) - Conditional
 - Developer C: Phase 5 (Statistical Analysis) - Conditional
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: `src/data/loaders.py` must raise `DataUnavailableError` immediately if `human_intensity_score` is missing. NO proxy path.
- **CRITICAL**: Power analysis (T021) runs BEFORE data loading (Phase 2).
- **CRITICAL**: Lasso Regression (T025) uses **5-fold cross-validation** for alpha (Per Plan Phase 3, Task 3.3) ONLY when 'EmojiType' is included.
- **CRITICAL**: Performance (T032) must meet linear scaling constraint (≤ 0.3s/message).
- **CRITICAL**: Final output (T029) is `report.md` and `results.json` for reproducibility.
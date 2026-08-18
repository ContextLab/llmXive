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

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/`)
- [ ] T002 Initialize Python 3.11 project with dependencies: `ml-datasets`, `pandas`, `numpy`, `scipy`, `statsmodels`, `seaborn`, `emoji`, `tqdm`, `pytest` in `requirements.txt`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `src/utils.py` with logging configuration, checksum verification helpers, and global random seed setting (`seed=42`)
- [ ] T005 [P] Create `src/data/loaders.py` skeleton: Enforce "fail loud" policy for **raw text corpus** (must be real, no synthetic text fallback), but **do not** raise if intensity scores are missing; instead, return a status indicating `intensity_missing` to allow the orchestrator to trigger the proxy path (FR-002).
- [ ] T006 [P] Setup `src/data/validation.py` to check for human-rated intensity scores in the loaded dataset
- [ ] T007 [P] **Power Analysis Task**: Implement logic to determine minimum sample size N (targeting Cohen's f² ≥ 0.02, 80% power, α=0.05) and output N to `state/power_analysis.yaml`. This must run BEFORE proxy generation.
- [ ] T008 Create base data contracts in `src/data/contracts/` defining `Message` (text, emoji metrics) and `AnalysisResult` schemas
- [ ] T009 Configure directory structure for `data/raw/`, `data/processed/`, and `state/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Emoji Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Load a public text message corpus and programmatically extract objective emoji metrics (presence, count, type) for every record.

**Independent Test**: Run the extraction script on a sample; verify output CSV contains `message_id`, `emoji_present` (bool), `emoji_count` (int), `emoji_types` (list of strings), with no missing values for valid records.

### Tests for User Story 1 (REQUIRED) ⚠️

- [ ] T010 [P] [US1] Contract test for schema validation in `tests/contract/test_schema.py`
- [ ] T011 [P] [US1] Unit test for emoji extraction logic (empty text, skin tone modifiers) in `tests/unit/test_extraction.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `src/data/preprocessing.py` with `extract_emoji_features(text)` function using `emoji` library to handle Unicode normalization (base points) and skin tone modifiers
- [ ] T013 [US1] Implement data loader in `src/data/loaders.py` to fetch a **verified public text message corpus** (e.g., CMU Text Message Corpus or OpenML equivalent); ensure it raises on failure for the text corpus but allows missing intensity scores.
- [ ] T014 [US1] Create pipeline step to join raw text with extracted features, handling edge cases (zero-length text, encoding errors) gracefully
- [ ] T015 [US1] Save processed features to `data/processed/features.csv` with checksums recorded in `state/`
- [ ] T016 [US1] Add logging for extraction errors and skipped records to ensure data hygiene

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Emotional Intensity Rating Generation (Priority: P2)

**Goal**: Load human-rated intensity scores if available; otherwise, generate "synthetic proxy scores" (1-7 Likert) validated against a small human subset (N=20).

**Independent Test**: Execute rating module; verify output contains `intensity_score` (1-7) and a validation report comparing proxy to human subset.

### Tests for User Story 2 (REQUIRED) ⚠️

- [ ] T017 [P] [US2] Unit test for proxy generation stochasticity (noise parameter) in `tests/unit/test_proxy_gen.py`
- [ ] T018 [P] [US2] Integration test for proxy validity check (r ≥ 0.6 threshold) in `tests/integration/test_proxy_validation.py`

### Implementation for User Story 2

- [ ] T019 [US2] Implement `src/data/proxy_generator.py` with a stochastic, non-circular algorithm for generating 1-7 Likert scores; explicitly exclude text length/punctuation as predictors; **MUST accept N (from T007) as input** to determine sample size.
- [ ] T020 [US2] Implement `src/data/validation.py` logic to detect if human-rated data exists; if missing, trigger proxy generation (T019) and save `is_proxy=True` flag.
- [ ] T021 [US2] Implement "Proxy Validity Check": calculate correlation between synthetic proxy and held-out human subset (N=20); **if r < 0.6, raise `ProxyValidityError` to HALT the pipeline** and flag a critical limitation.
- [ ] T022 [US2] Merge intensity scores (human or proxy) with `features.csv` into `data/processed/analysis_dataset.csv`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Compute correlation and regression (controlling for text length/punctuation), apply Bonferroni correction, and generate visualizations.

**Independent Test**: Run analysis on pre-generated dataset; verify report includes correlation matrix, regression table (Beta, p-values), adjusted p-values, and plot images.

### Tests for User Story 3 (REQUIRED) ⚠️

- [ ] T023 [P] [US3] Unit test for Bonferroni correction logic in `tests/unit/test_stats.py`
- [ ] T024 [P] [US3] Integration test for reproducibility (bit-for-bit match on re-run) in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [ ] T025 [US3] Implement `src/analysis/stats.py` with Pearson/Spearman correlation functions and linear regression (statsmodels) controlling for text length and punctuation; **MUST output the Standardized Regression Coefficient (Beta) as the primary effect size metric** to satisfy FR-004 and SC-003. The task must explicitly calculate and return this standardized value, not just unstandardized coefficients.
- [ ] T026 [US3] Implement Bonferroni correction logic for multiple comparisons (emoji types) in `src/analysis/stats.py`
- [ ] T027 [US3] Implement visualization generation in `src/analysis/viz.py` (seaborn) for coefficient plots and intensity distributions
- [ ] T028 [US3] Create `src/main.py` to orchestrate the full pipeline: Load -> Extract -> Rate/Proxy -> Analyze -> Report
- [ ] T029 [US3] Generate final `analysis_results.csv` and `report.pdf` containing effect sizes (Standardized Beta) and significance levels

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Update `docs/` with quickstart instructions and data source citations
- [ ] T031 Code cleanup and refactoring to ensure modularity
- [ ] T032 Performance optimization to ensure < 5 minutes runtime for N=1000 messages
- [ ] T033 [P] Additional unit tests for edge cases (empty strings, non-standard emoji sequences)
- [ ] T034 Run `quickstart.md` validation and verify all checksums

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data loading logic from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on features (US1) and scores (US2)

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
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
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
- **CRITICAL**: `src/data/loaders.py` must raise on missing **raw text** but allow missing **intensity scores** to trigger the proxy path.
- **CRITICAL**: Proxy generation (US2) must be validated against human data (N=20) before proceeding to analysis (US3). If r < 0.6, the pipeline MUST halt.
- **CRITICAL**: Power analysis (T007) must run before proxy generation (T019) to determine N.
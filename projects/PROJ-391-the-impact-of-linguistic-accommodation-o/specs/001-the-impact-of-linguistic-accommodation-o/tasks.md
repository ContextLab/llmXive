# Tasks: The Impact of Linguistic Accommodation on Perceived Empathy in AI Assistants

**Input**: Design documents from `/specs/001-linguistic-accommodation-empathy/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `tests/`, `outputs/`, `outputs/figures/`, `outputs/reports/` at repository root (as per `plan.md` structure)
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

- [ ] T001a Create project directories: `code/`, `data/raw/`, `data/processed/`, `tests/`, `outputs/`, `outputs/figures/`, `outputs/reports/`
- [ ] T001b Create empty `__init__.py` files in `code/`, `tests/`, `tests/unit/`, `tests/integration/`, `tests/contract/`
- [ ] T002a Create virtualenv in `code/.venv` and activate it
- [ ] T002b Generate `code/requirements.txt` with pinned versions: `pandas`, `numpy`, `scikit-learn`, `scipy`, `nltk`, `matplotlib`, `seaborn`, `spacy`, `datasets`, `jsonschema`, `pyyaml`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [ ] T004 [P] Setup pytest configuration and `conftest.py` for fixtures (random seed pinning)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Implement `code/utils.py`: Unicode NFKC normalization function and text cleaning helpers (FR-008)
- [ ] T006 [P] Implement `code/utils.py`: Jaccard similarity helper for sets (lexical and POS)
- [ ] T007 [P] Implement `code/utils.py`: POS tagging and dependency parsing wrappers using `spacy`
- [ ] T008 Create `contracts/dataset.schema.yaml` defining the schema for processed dialogue pairs
- [ ] T009 Create `contracts/output.schema.yaml` defining the schema for statistical report outputs
- [ ] T010 [P] Implement `code/main.py` skeleton: Create `main()`, `load_config()`, and `run_pipeline()` stub functions with pipeline orchestration structure and contract validation hooks
- [ ] T011 [P] [FR-030] [Constitution] Implement `code/main.py` Reference-Validator gate logic: Call Reference-Validator Agent CLI with path to `research.md` to verify citations before analysis (Pipeline Step 1)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Load DailyDialog, normalize text, filter repetitions, and compute raw accommodation metrics (lexical overlap, syntactic similarity, sentence length variance).

**Independent Test**: Run `code/data_ingestion.py` on a sample of 100 dialogue pairs; verify output JSON/CSV contains `lexical_overlap`, `syntactic_similarity`, `sentence_length_variance`, `conversation_id` with no nulls in metric columns.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**
> **Depends on Phase 2 (T005-T007) completion**

- [ ] T012 [P] [US1] Unit test for NFKC normalization in `tests/unit/test_utils.py::test_nfk_normalization_handles_emoji` (Depends on Phase 2 completion)
- [ ] T013 [P] [US1] Unit test for Jaccard similarity calculation in `tests/unit/test_utils.py` (Depends on Phase 2 completion)
- [ ] T014 [P] [US1] Unit test for exact repetition filtering logic in `tests/unit/test_data_ingestion.py` (Depends on Phase 2 completion)
- [ ] T015 [P] [US1] Contract test for ingestion output schema in `tests/contract/test_ingestion_schema.py` (Depends on Phase 2 completion)

### Implementation for User Story 1

- [ ] T016 [US1] Implement `code/data_ingestion.py`: Download DailyDialog using `datasets.load_dataset("daily_dialog", split="test")` and cache to `data/raw/daily_dialog_test.parquet`
- [ ] T017 [US1] Implement `code/data_ingestion.py`: Load data, apply NFKC normalization (FR-008), and skip empty/non-text records
- [ ] T018 [US1] Implement `code/data_ingestion.py`: Filter records where AI response is exact repetition (Jaccard > 0.9)
- [ ] T019 [US1] Implement `code/data_ingestion.py`: Compute lexical overlap (Jaccard on tokens) and sentence length variance per pair
- [ ] T020 [US1] Implement `code/data_ingestion.py`: Compute syntactic similarity (Jaccard on POS tag sets) per pair
- [ ] T021 [US1] Implement `code/data_ingestion.py`: Save processed metrics to `data/processed/accommodation_metrics.csv`
- [ ] T022 [US1] Validate output against `contracts/dataset.schema.yaml` within the ingestion script

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Empathy Rating Extraction and Mapping (Priority: P2)

**Goal**: Extract or infer empathy ratings from dataset annotations using the defined emotion-to-Likert mapping rule and pair them with accommodation metrics.

**Independent Test**: Verify output dataset contains `empathy_rating` column paired with every `accommodation_score` row, matching the 1-5 Likert scale distribution and mapping rule.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US2] Unit test for emotion-to-Likert mapping logic in `tests/unit/test_empathy_mapping.py`
- [ ] T024 [P] [US2] Unit test for handling missing emotion labels in `tests/unit/test_empathy_mapping.py`
- [ ] T025 [P] [US2] Contract test for empathy mapping output schema in `tests/contract/test_empathy_schema.py`

### Implementation for User Story 2

- [ ] T026 [US2] Implement `code/empathy_mapping.py`: Load accommodation metrics from `data/processed/accommodation_metrics.csv` (Depends on T021 completion)
- [ ] T027 [US2] Implement `code/empathy_mapping.py`: Extract explicit empathy ratings if available in DailyDialog metadata
- [ ] T028 [US2] Implement `code/empathy_mapping.py`: Apply emotion-to-Likert mapping rule (Joy=5, Sadness=2, Anger=1, Fear=2, Surprise=4, Disgust=1, Neutral=3) for missing ratings
- [ ] T029 [US2] Implement `code/empathy_mapping.py`: Exclude records with no emotion label and log exclusion rate
- [ ] T030 [US2] Implement `code/empathy_mapping.py`: Save final paired dataset to `data/processed/final_dataset.csv`
- [ ] T031 [US2] Validate output against `contracts/dataset.schema.yaml`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Visualization (Priority: P3)

**Goal**: Perform correlation analysis, regression with controls, bootstrap resampling, sensitivity analysis, and generate visualizations.

**Independent Test**: Run `code/statistical_analysis.py`; verify report contains correlation coefficient, p-value, scatter plot, and bootstrap CI width < 0.01.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Unit test for bootstrap resampling loop logic in `tests/unit/test_statistical_analysis.py`
- [ ] T033 [P] [US3] Unit test for Bonferroni correction calculation in `tests/unit/test_statistical_analysis.py`
- [ ] T034 [P] [US3] Integration test for full pipeline end-to-end in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [ ] T034.4 [US3] [FR-007] Extract topic labels from the raw DailyDialog dataset (column `topic`) for regression control. **Output**: A list of topic labels aligned with `final_dataset.csv`. (Depends on T030 completion)
- [ ] T035.5 [US3] [FR-009] Define sampling strategy for sensitivity analysis: "If full dataset processing exceeds memory limits, sample n=5000 randomly with seed 42. Otherwise, use full dataset." **Output**: A markdown file `outputs/reports/sampling_strategy.md` documenting this strategy. (Depends on T030 completion)
- [ ] T035 [US3] Implement `code/sensitivity_analysis.py`: Compute dependency-parse-based metrics (Jaccard similarity of dependency relation sets, e.g., nsubj, obj) for the FULL dataset (or the pre-defined sample if the strategy applies) (FR-009) (Depends on T035.5 completion)
- [ ] T036 [US3] Implement `code/sensitivity_analysis.py`: Compare POS-based vs. Dependency-based metrics (FR-009)
- [ ] T037 [US3] Implement `code/statistical_analysis.py`: Perform Pearson and Spearman correlation tests (FR-004)
- [ ] T038 [US3] Implement `code/statistical_analysis.py`: Run regression controlling for conversation length and topic (dataset labels) (FR-007) (Depends on T034.4 completion)
- [ ] T039 [US3] Implement `code/statistical_analysis.py`: Implement iterative bootstrap resampling (min 1000, loop until CI width < 0.01). **Safety Break**: If CI width not <0.01 after 50,000 iterations, log a WARNING, record the current estimate, and proceed. **Output**: Save bootstrap distribution and final CI to `outputs/reports/bootstrap_results.json`. Function signature: `run_bootstrap_correlation(data, n_iter=1000, target_ci_width=0.01)` (FR-006)
- [ ] T040 [US3] Implement `code/statistical_analysis.py`: Apply Bonferroni correction for the four specific hypothesis tests: Pearson and Spearman on lexical overlap, and Pearson and Spearman on syntactic similarity (FR-005)
- [ ] T041 [US3] Implement `code/statistical_analysis.py`: Calculate effect sizes and interpret against Cohen's guidelines and Giles et al. baseline. **Output**: Write the interpretation to `outputs/reports/statistical_summary.json` under the key `effect_size_interpretation`. (FR-005)
- [ ] T042 [US3] Implement `code/statistical_analysis.py`: Generate scatter plot with regression line and % CI shading (FR-005)
- [ ] T043 [US3] Implement `code/statistical_analysis.py`: Generate final statistical report to `outputs/reports/statistical_summary.json`
- [ ] T044 [US3] Validate output against `contracts/output.schema.yaml`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Validation & Polish

**Purpose**: Final validation steps and documentation

- [ ] T045 [US2] [FR-010] Implement validation subset sampling and consistency check: Sample n=30 dialogue pairs randomly (stratified by emotion) from a public human-annotated subset of DailyDialog (or a standard benchmark subset). Apply a human rating protocol (e.g., via a crowdsourcing platform or structured manual review) to validate inferred empathy scores against human judgments. **Output**: Save agreement rate and confusion matrix to `outputs/reports/validation_summary.json`. (Depends on T030 completion)
- [ ] T046 [P] Update `quickstart.md` with instructions to run the full pipeline
- [ ] T047 [P] Add `README.md` with project overview and citation requirements
- [ ] T048 [P] Run full pipeline on a sample to verify reproducibility and seed pinning
- [ ] T049 [P] Verify all artifacts are checksummed and tracked in `state/projects/PROJ-391-the-impact-of-linguistic-accommodation-o.yaml`

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (metrics)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (paired dataset)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utils before services/scripts
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for NFKC normalization in tests/unit/test_utils.py::test_nfk_normalization_handles_emoji"
Task: "Unit test for Jaccard similarity calculation in tests/unit/test_utils.py"

# Launch all implementation for User Story 1 together (after tests fail):
Task: "Implement code/data_ingestion.py: Download DailyDialog"
Task: "Implement code/data_ingestion.py: Compute metrics"
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
- **CPU Constraint**: All tasks must run on a limited CPU allocation, 7GB RAM, no GPU. No heavy model loading or 8-bit quantization.
- **Data Constraint**: Use real DailyDialog data only. No synthetic data generation.
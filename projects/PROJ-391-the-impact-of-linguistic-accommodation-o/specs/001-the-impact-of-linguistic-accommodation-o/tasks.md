# Tasks: Linguistic Accommodation and Speaker Emotional Intensity in Human-Human Dialogue

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

 Tasks MUST be organized by user story so each story can:
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
- [X] T002b Generate `code/requirements.txt` with pinned versions: `pandas`, `numpy`, `scikit-learn`, `scipy`, `nltk`, `matplotlib`, `seaborn`, `spacy`, `datasets`, `jsonschema`, `pyyaml`, `scikit-posthocs`, `statsmodels`, `gensim`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [ ] T004 [P] Setup pytest configuration and `conftest.py` for fixtures (random seed pinning)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement `code/utils.py`: Unicode NFKC normalization function and text cleaning helpers (FR-008)
- [X] T006 [P] Implement `code/utils.py`: Jaccard similarity helper for sets (lexical and POS)
- [X] T007 [P] Implement `code/utils.py`: POS tagging and dependency parsing wrappers using `spacy`
- [ ] T008 Create `contracts/dataset.schema.yaml` defining the schema for processed dialogue pairs
- [ ] T009 Create `contracts/output.schema.yaml` defining the schema for statistical report outputs
- [ ] T010 [P] Implement `code/main.py` skeleton: Create `main()`, `load_config()`, and `run_pipeline()` stub functions with pipeline orchestration structure and contract validation hooks

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Load DailyDialog, normalize text, filter empty records, and compute raw accommodation metrics (lexical overlap, syntactic similarity, sentence length variance).

**Independent Test**: Run `code/data/ingestion.py` on a sample of dialogue pairs.; verify output JSON/CSV contains `lexical_overlap`, `syntactic_similarity`, `sentence_length_variance`, `conversation_id` with no nulls in metric columns.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**
> **Depends on Phase 2 (T005-T007) completion**

- [X] T012 [P] [US1] Unit test for NFKC normalization in `tests/unit/test_utils.py::test_nfk_normalization_handles_emoji` (Depends on Phase 2 completion)
- [X] T013 [P] [US1] Unit test for Jaccard similarity calculation in `tests/unit/test_utils.py` (Depends on Phase 2 completion)
- [ ] T014 [P] [US1] Unit test for empty record filtering in `tests/unit/test_data_ingestion.py` (Depends on Phase 2 completion)
- [X] T015 [P] [US1] Contract test for ingestion output schema in `tests/contract/test_ingestion_schema.py` (Depends on Phase 2 completion)

### Implementation for User Story 1

- [X] T016 [US1] Implement `code/data/ingestion.py`: Download **FULL** DailyDialog dataset (train, test, val splits) using `datasets.load_dataset("daily_dialog", split="test", streaming=True)` and save to `data/raw/daily_dialog_test.parquet`. (FR-008) **Note**: Use 'Speaker A' and 'Speaker B' terminology, not 'user/AI'.
- [X] T017 [US1] Implement `code/data/ingestion.py`: Load data, apply NFKC normalization (FR-008), and skip records where turn or partner turn is empty/non-text after normalization. **Note**: Do NOT filter based on similarity thresholds; keep all valid text records. (FR-008)
- [X] T019 [US1] Implement `code/data/ingestion.py`: Compute lexical overlap (Jaccard on tokens) and sentence length variance per pair between **Speaker A** and **Speaker B** turns. (FR-001)
- [X] T020 [US1] Implement `code/data/ingestion.py`: Compute syntactic similarity (Jaccard on POS tag sets) per pair. (FR-002)
- [X] T021 [US1] Implement `code/data/ingestion.py`: Save processed metrics to `data/processed/accommodation_metrics.csv`
- [ ] T022 [US1] Validate output against `contracts/dataset.schema.yaml` within the ingestion script

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Emotional Intensity Extraction and Mapping (Priority: P2)

**Goal**: Extract emotion labels from dataset annotations and map them to a numeric **Speaker Emotional Intensity** score (1-5) using the defined rule, ensuring every accommodation metric has a paired intensity score.

**Independent Test**: Verify output dataset contains `emotional_intensity` column paired with every `accommodation_score` row, matching the 1-5 Likert scale distribution and mapping rule. Output a distribution report.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US2] Unit test for emotion-to-intensity mapping logic in `tests/unit/test_emotion_mapping.py`
- [ ] T024 [P] [US2] Unit test for handling missing emotion labels in `tests/unit/test_emotion_mapping.py`
- [ ] T025 [P] [US2] Contract test for emotion mapping output schema in `tests/contract/test_emotion_schema.py`

### Implementation for User Story 2

- [ ] T026 [US2] Implement `code/analysis/emotion_mapping.py`: Load accommodation metrics from `data/processed/accommodation_metrics.csv` (Depends on T021 completion)
- [ ] T027 [US2] Implement `code/analysis/emotion_mapping.py`: Extract explicit emotion labels from DailyDialog metadata (FR-003)
- [ ] T028 [US2] Implement `code/analysis/emotion_mapping.py`: Apply emotion-to-intensity mapping rule (Joy=5, Sadness=2, Anger=1, Fear=2, Surprise=4, Disgust=1, Neutral=3) (FR-003)
- [ ] T029 [US2] Implement `code/analysis/emotion_mapping.py`: Exclude records with no emotion label and log exclusion rate
- [ ] T030 [US2] Implement `code/analysis/emotion_mapping.py`: Generate distribution report of mapped scores and save to `outputs/reports/emotion_distribution.json` (FR-010)
- [ ] T031 [US2] Save final paired dataset to `data/processed/final_dataset.csv`
- [ ] T032 [US2] Validate output against `contracts/dataset.schema.yaml`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Visualization (Priority: P3)

**Goal**: Perform correlation analysis, regression with controls, bootstrap resampling, sensitivity analysis, and generate visualizations.

**Independent Test**: Run `code/analysis/stats.py`; verify report contains correlation coefficient, p-value, scatter plot, and bootstrap CI width ≤ 0.05.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T033 [P] [US3] Unit test for bootstrap resampling loop logic in `tests/unit/test_stats.py`
- [ ] T034 [P] [US3] Unit test for Bonferroni correction calculation in `tests/unit/test_stats.py`
- [ ] T035 [P] [US3] Integration test for full pipeline end-to-end in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [ ] T036a [US3] [FR-007] Extract raw topic labels from the DailyDialog dataset (column `topic`) for regression control. **Note**: Spec FR-007 mentions 'LDA cluster ID', but DailyDialog provides explicit topic labels. This task uses the raw labels directly to avoid redundant clustering, aligning with the Plan's optimization. **Output**: A list of topic labels aligned with `final_dataset.csv`. (Depends on T031 completion)
- [ ] T038 [US3] Implement `code/analysis/sensitivity.py`: Compute dependency-parse-based metrics (Jaccard similarity of dependency relation sets) for the FULL dataset (or a defined sample if memory constrained). **Strategy**: If full dataset exceeds memory, sample n=5000 randomly with seed 42. (FR-009) (Depends on T031 completion)
- [ ] T039 [US3] Implement `code/analysis/sensitivity.py`: Compare POS-based vs. Dependency-based metrics (FR-009)
- [ ] T040 [US3] Implement `code/analysis/stats.py`: Perform Pearson and Spearman correlation tests (FR-004)
- [ ] T041 [US3] [FR-007] Run **Linear Regression** controlling for conversation length and **raw `topic` labels** (from T036a) as covariates. (Baseline comparison) (Depends on T036a completion)
- [ ] T041b [US3] [SC-004] Implement **Ordinal Logistic Regression (Proportional Odds Model)** using `statsmodels` or `scikit-posthocs`. Predict `emotional_intensity` (ordinal 1-5) using accommodation metrics as predictors and **raw `topic` labels** + conversation length as covariates. **Output**: Calculate and report **McFadden's Pseudo-R2** in `outputs/reports/statistical_summary.json`. (Depends on T036a completion)
- [ ] T042 [US3] Implement `code/analysis/stats.py`: Implement iterative bootstrap resampling (min 1000, loop until CI width ≤ 0.05 or max 5000 iterations). **Safety Break**: If CI width not ≤ 0.05 after 5000 iterations, log a WARNING, record the current estimate, and proceed. **Output**: Save bootstrap distribution and final CI to `outputs/reports/bootstrap_results.json`. Function signature: `run_bootstrap_correlation(data, n_iter=1000, target_ci_width=0.05, max_iter=5000)` (FR-006)
- [ ] T043 [US3] Implement `code/analysis/stats.py`: Apply Bonferroni correction for the four specific hypothesis tests: Pearson and Spearman on lexical overlap, and Pearson and Spearman on syntactic similarity (FR-005)
- [ ] T044 [US3] Implement `code/analysis/stats.py`: Calculate effect sizes and interpret against **Cohen's thresholds** (0.1 small, 0.3 medium, 0.5 large). **Output**: Write the interpretation to `outputs/reports/statistical_summary.json` under the key `effect_size_interpretation`. (FR-005, SC-003) **Note**: The 'Giles et al.' baseline was removed per Plan SC-003 override.
- [ ] T045 [US3] Implement `code/analysis/viz.py`: Generate scatter plot with regression line and confidence interval shading
- [ ] T046 [US3] Implement `code/analysis/stats.py`: Generate final statistical report to `outputs/reports/statistical_summary.json`
- [ ] T047 [US3] Validate output against `contracts/output.schema.yaml`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Validation & Polish

**Purpose**: Final validation steps and documentation

- [ ] T048a [US2] [FR-010] **Human Annotation Setup**: Select a stratified random sample of dialogues (n=50). Annotate with multiple raters for 'Emotional Intensity' using a multi-point Likert scale. Store results in `data/processed/validation_ground_truth.csv`. (Depends on T031 completion)
- [ ] T048b [US2] [FR-010] **Inter-Rater Reliability**: Calculate Krippendorff's Alpha on the **human ratings** from T048a to validate consistency. **Output**: Save the Alpha value to `outputs/reports/validation_summary.json`. (Depends on T048a completion)
- [ ] T048c [US2] [FR-010] **Validation Correlation**: Calculate correlation between the **mapped intensity scores** (from T028) and the **mean human ratings** (from T048a). **Output**: Save correlation coefficient and p-value to `outputs/reports/validation_summary.json`. (Depends on T048b completion)
- [ ] T048d [US2] [FR-010] **Literature Grounding**: Perform Chi-Square Goodness-of-Fit test comparing the observed distribution of mapped `emotional_intensity` scores in DailyDialog against a **theoretical uniform distribution**. **Output**: Save the Chi-Square statistic, p-value, and conclusion to `outputs/reports/validation_summary.json`. (Depends on T031 completion) **Note**: ISEAR distribution was not defined in Spec/Plan; using Uniform as a baseline for literature grounding.
- [ ] T049 [P] Update `quickstart.md` with instructions to run the full pipeline
- [ ] T050 [P] Add `README.md` with project overview and citation requirements
- [ ] T051 [P] Run full pipeline on a sample to verify reproducibility and seed pinning
- [ ] T052 [P] Verify all artifacts are checksummed and tracked in `state/projects/PROJ-391-the-impact-of-linguistic-accommodation-o.yaml`

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
Task: "Implement code/data/ingestion.py: Download DailyDialog"
Task: "Implement code/data/ingestion.py: Compute metrics"
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
- **CPU Constraint**: All tasks must run on a limited CPU allocation, constrained RAM, and no GPU.. No heavy model loading or 8-bit quantization.
- **Data Constraint**: Use real DailyDialog data only. No synthetic data generation. Use `streaming=True` for large datasets to stay within memory limits.
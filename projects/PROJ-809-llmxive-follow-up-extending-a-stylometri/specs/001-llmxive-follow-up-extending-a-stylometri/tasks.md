# Tasks: llmXive Follow-up: Extending "A Stylometric Application of Large Language Models"

**Input**: Design documents from `/specs/001-llmxive-followup/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Initialize project directory structure (`projects/PROJ-809-llmxive-follow-up-extending-a-stylometri/`) including `code/`, `data/` (raw, processed, hybrid), `artifacts/` (models, metrics), `contracts/`, `tests/` (unit, contract, integration), and `state/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement `code/utils.py` with deterministic logging, SHA-256 checksumming, and tokenization helpers (char-level, no punctuation)
- [X] T006 [P] Create `code/update_state.py` to manage Constitution Principle V (artifact hashing and state file updates to `state/PROJ-809-llmxive-followup.yaml`)
- [ ] T007 [P] Create base configuration loader for `contracts/` schemas and random seed management

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Corpus Construction and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download, filter, and preprocess the arXiv dataset into a balanced, author-labeled corpus.

**Independent Test**: The system can be tested by running the data ingestion script and verifying that the output directory contains exactly 20 author folders, each with ≥10 normalized text files, and that a summary log confirms the total count and author distribution.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for `data/processed/` schema in `tests/contract/test_corpus_schema.py`
- [ ] T010 [P] [US1] Integration test for data ingestion pipeline in `tests/integration/test_data_ingestion.py`

### Implementation for User Story 1

- [~] T011 [US1] Implement `code/data_ingestion.py` to download dataset 'arxiv' (split: train) filtered by categories [cs.CL, physics.gen-ph, q-bio.QM] and save to `data/raw/arxiv_subset.parquet`
- [~] T012 [US1] Implement filtering logic in `code/data_ingestion.py` to extract 20 distinct lead authors with ≥10 abstracts each (FR-001, FR-009)
- [~] T013 [US1] Implement author disambiguation and collision logging in `code/data_ingestion.py`: log warning if name appears >50 times (FR-009)
- [~] T013a [US1] Implement collision flagging: write `data/processed/collision_report.json` and update `state/PROJ-809-llmxive-followup.yaml` with manual_review flag for names appearing >50 times; raise fatal error if critical collision threshold is exceeded (FR-009)
- [~] T014 [US1] Implement preprocessing in `code/data_ingestion.py`: lowercase, remove punctuation, tokenization to character sequences (FR-002)
- [ ] T015 [US1] Implement stratified random sampling to select representative cohort if >20 authors qualify; raise fatal error with clear message if filtered dataset yields < 20 authors (FR-001, Edge Cases)
- [ ] T016 [US1] Write checksums of raw download and processed artifacts to `state/PROJ-809-llmxive-followup.yaml` (Constitution III & V)
- [ ] T017 [US1] Filter abstracts < 6 characters (max n-gram order) to ensure validity for all n=4,5,6 models; log count of excluded abstracts (FR-002, Edge Cases)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Character-Level N-gram Model Training and Perplexity Calculation (Priority: P2)

**Goal**: Train CPU-efficient n-gram models (n=4,5,6) with Kneser-Ney smoothing and generate the perplexity matrix.

**Independent Test**: The system can be tested by training a single author's model on a small subset and verifying that the computed perplexity for that author's own held-out text is significantly lower than the perplexity for a text from a different author.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for `artifacts/models/` schema in `tests/contract/test_model_schema.py`
- [ ] T019 [P] [US2] Integration test for perplexity calculation in `tests/integration/test_perplexity.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/model_training.py` to train character-level n-gram models (n=4, 5, 6) per author using sklearn CountVectorizer, saving to `artifacts/models/author_{id}_n{n}.pkl` (FR-003)
- [ ] T021 [US2] Implement Kneser-Ney smoothing in `code/model_training.py` to handle data sparsity for ALL models (n=4, 5, 6) (FR-011)
- [ ] T022 [US2] Implement /20 train/test split logic within `code/model_training.py`
- [ ] T023 [US2] Implement sparsity check logic in `code/model_training.py`: if n=6 sparsity > threshold, trigger fallback to n=5 for that author
- [ ] T023b [US2] Implement fallback logic: if n=6 fails sparsity check, train and save n=5 model to `artifacts/models/author_{id}_n5_fallback.pkl` to ensure a model is generated for every author (FR-003, FR-011)
- [ ] T024 [US2] Implement `code/evaluation.py` to compute perplexity matrix (cross-evaluation of all held-out abstracts against all models) and save to `artifacts/metrics/perplexity_matrix.csv` (FR-004)
- [ ] T025 [US2] Ensure all training and evaluation runs within CPU-only constraints (≤30s per author, ≤6GB RAM) (FR-008, SC-004)
- [ ] T026 [US2] Save trained models to `artifacts/models/` with content hashes
- [ ] T027 [US2] Implement sensitivity analysis: train and evaluate n=4, n=5, and n=6 models for all authors to generate performance metrics; save results to `artifacts/metrics/sensitivity_analysis.json` (FR-010, Plan)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Classification, Baseline Comparison, and Statistical Validation (Priority: P3)

**Goal**: Perform classification, compare against function-word baseline, and validate with synthetic hybrid abstracts.

**Independent Test**: The system can be tested by running the classification pipeline on the generated perplexity matrix and verifying that the output includes an accuracy score, a p-value from McNemar's test, and a degradation metric for hybrid texts.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for `results/` metrics schema in `tests/contract/test_metrics_schema.py`
- [ ] T042 [P] [US3] Integration test for statistical validation pipeline in `tests/integration/test_statistical_validation.py` (Renamed from T027 to avoid collision)

### Implementation for User Story 3

- [ ] T029 [US3] Implement classification logic in `code/evaluation.py` (min perplexity assignment) and calculate accuracy (FR-005, SC-001)
- [ ] T029a [US3] Calculate random chance baseline (1/20 = 5%) and report as distinct metric in results; verify if n-gram accuracy > 75% (SC-001)
- [ ] T030 [US3] Implement `code/baseline.py` to train function-word frequency Naive Bayes classifier (FR-006)
- [ ] T031 [US3] Implement McNemar's test in `code/evaluation.py` comparing n=5 model (pre-registered primary) vs. baseline (FR-006, SC-002)
- [ ] T032 [US3] Implement Bonferroni correction logic in `code/evaluation.py`: apply correction to the set of n-gram orders (n=4,5,6) when comparing against baseline for sensitivity analysis using metrics from `artifacts/metrics/sensitivity_analysis.json`; confirm primary test (T031) uses n=5 without correction (FR-010) (Requires T027)
- [ ] T033 [US3] Implement `code/robustness.py` to generate synthetic "hybrid" abstracts by swapping exactly one sentence between authors and save to `data/hybrid/` (FR-007)
- [ ] T034 [US3] Evaluate hybrid abstracts using the perplexity matrix artifact from T024, calculate accuracy drop, and verify if drop ≥ 20pp (SC-003) (Requires T024)
- [ ] T035 [US3] Implement tie-breaking rule (alphabetical author ID) for equal perplexity predictions (Edge Case)
- [ ] T036 [US3] Run `code/update_state.py` to finalize `state/PROJ-809-llmxive-followup.yaml` with all artifact hashes (Constitution V)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` and `quickstart.md`
- [ ] T038 Code cleanup and refactoring
- [ ] T039 Performance optimization (vectorization) to ensure total runtime ≤ 1.5 hours
- [ ] T040 [P] Additional unit tests in `tests/unit/`
- [ ] T041 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US1 data and US2 models

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data ingestion before model training
- Model training before evaluation
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
Task: "Contract test for data/processed/ schema in tests/contract/test_corpus_schema.py"
Task: "Integration test for data ingestion pipeline in tests/integration/test_data_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement data_ingestion.py to download arXiv subset"
Task: "Implement filtering logic for 20 distinct lead authors"
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
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Model Training)
 - Developer C: User Story 3 (Evaluation & Baseline)
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
- **CPU Constraint**: All n-gram training must be optimized for CPU-only execution (no CUDA/GPU).
- **Data Integrity**: No synthetic data generation for training inputs; only real arXiv data.
- **Statistical Rigor**: Bonferroni correction applied to sensitivity analysis of all orders; McNemar's test on paired binary outcomes for primary n=5 model.
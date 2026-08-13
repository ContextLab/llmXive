# Tasks: llmXive follow-up: extending "Cosmos 3: Omnimodal World Models for Physical AI"

**Input**: Design documents from `/specs/001-llmxive-gap/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/` at repository root (scripts, data, models, tests)
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

- [ ] T001a [P] Create directory structure: `code/scripts/`, `code/data/raw/`, `code/data/processed/`, `code/data/splits/`, `code/models/`, `code/tests/`
- [ ] T001b [P] Create `code/requirements.txt` with pinned versions for `datasets`, `transformers`, `scikit-learn`, `pandas`, `numpy`, `pytest`, `pyyaml`
- [ ] T001c [P] Initialize `.gitignore` to exclude `data/`, `models/`, `__pycache__/`, `*.pyc`

- [ ] T002 [P] Configure linting (flake8/black) and formatting tools in `code/.flake8` and `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 [P] Implement `code/scripts/download.py` to fetch `google-research/bridge-data` with `config='bridge_v2'` via `datasets.load_dataset` using `streaming=True`
- [ ] T004 [P] Implement `code/scripts/download.py` logic to filter for instances containing 'actions' field and save to `code/data/raw/bridge_samples.jsonl`; MUST fail loudly if fetch fails (no synthetic fallback)
- [ ] T005 [P] Define schema adaptation logic in `code/utils/schema_adapter.py` to handle Bridge Data's 'actions' field: explicitly calculate L2 norm of the **first 3 dimensions** of the action vector for FR-002 applicability
- [ ] T006 [P] Create `code/scripts/transform.py` skeleton with deterministic logical rules for target derivation (no parallel execution with T011)
- [ ] T007 [P] Setup logging infrastructure in `code/utils/logger.py` to track memory usage and execution time
- [ ] T008 [P] Configure environment configuration management (seeds, paths) in `code/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Transformation & Proxy Model Training (Priority: P1) 🎯 MVP

**Goal**: Transform continuous action vectors into discrete symbolic tokens and train a lightweight CPU-compatible proxy model to establish a baseline capability for symbolic reasoning.

**Independent Test**: Verify data transformation script produces a labeled CSV/JSONL file and proxy model training completes on CPU within 6 hours, consuming ≤ 7 GB RAM, outputting a model artifact and training logs.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for transformation logic in `code/tests/test_transform.py` (verify L2 norm of first 3 dims > 0.5 -> "constraint_violated")
- [ ] T010 [P] [US1] Integration test for download and transform pipeline in `code/tests/test_pipeline.py`

### Implementation for User Story 1

- [ ] T011 [US1] Implement `code/scripts/transform.py` to: 1) Compute L2 norm of the **first 3 dimensions** of the 'actions' vector from `code/data/raw/bridge_samples.jsonl`, 2) Apply >0.5 threshold to this norm for symbolic token ("constraint_satisfied" vs "constraint_violated"), 3) Generate continuous proxy target (normalized magnitude within the standard unit interval), 4) Save unified dataset to `code/data/processed/unified_dataset.jsonl`
- [ ] T012 [US1] Implement `code/scripts/train.py` to initialize and train TWO distinct DistilBERT models: 1) Hard Proxy (Classification head) for symbolic target, 2) Soft Proxy (Regression head) for continuous target. Save outputs to `code/models/proxy_hard/` and `code/models/proxy_soft/` respectively.
- [ ] T013 [US1] Implement `code/scripts/train.py` to train the Hard Proxy model on CPU, ensuring memory usage ≤ 7 GB RAM and training time ≤ 6 hours, outputting `code/models/proxy_hard/model.pt`
- [ ] T014 [US1] Implement `code/scripts/train.py` to train the Soft Proxy model on CPU, ensuring memory usage ≤ 7 GB RAM and training time ≤ 6 hours, outputting `code/models/proxy_soft/model.pt`
- [ ] T015 [US1] Add validation and error handling in `code/scripts/train.py` to fail loudly if real data fetch fails (no synthetic fallback)
- [ ] T016 [US1] Add logging for training progress, loss convergence, and resource usage in `code/scripts/train.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Comparative Performance Analysis (Priority: P2)

**Goal**: Compare the proxy model's performance on symbolic reasoning tasks against its performance on continuous control tasks to quantify the "modality gap".

**Independent Test**: Execute evaluation script that loads trained models, runs inference on both test sets, and outputs a statistical report comparing metrics with a p-value.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Unit test for statistical significance calculation in `code/tests/test_stats.py`

### Implementation for User Story 2

- [ ] T018 [US2] Create `code/scripts/evaluate.py` to load the trained Hard Proxy (T013) and Soft Proxy (T014) models and split predictions into symbolic and continuous domains
- [ ] T019 [US2] Implement `code/scripts/evaluate.py` to generate predictions on the symbolic test set (Classification head) and continuous test set (Regression head) using `code/data/processed/unified_dataset.jsonl`
- [ ] T020 [US2] Implement `code/scripts/evaluate.py` to calculate Brier Scores, Accuracy, F1-score, and AUC-ROC for both domains
- [ ] T021 [US2] Implement `code/scripts/evaluate.py` to perform a statistically appropriate test: Run Shapiro-Wilk test; if p > 0.05 use paired t-test, else Wilcoxon signed-rank, to determine significance of degradation (p < 0.05)
- [ ] T022 [US2] Generate the comparative performance report in `code/data/results/comparative_analysis.json` with side-by-side metrics and p-values
- [ ] T023 [US2] Add logic to explicitly validate the existence of a 'native continuous reward signal' in Bridge Data. If missing, calculate a proxy from 'normalized action magnitude' and document this derivation as the 'physics baseline' to satisfy SC-001 measurability. Explicitly state the magnitude of performance drop.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Error Analysis & Failure Mode Identification (Priority: P3)

**Goal**: Analyze misclassified samples to identify specific patterns in failure (Action Noise, Context Mismatch, etc.).

**Independent Test**: Run error analysis script on the test set, outputting a report categorizing misclassifications and visualizing correlations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Unit test for error categorization logic in `code/tests/test_analyze.py`

### Implementation for User Story 3

- [ ] T025 [US3] Create `code/scripts/analyze_errors.py` to load misclassified samples from the symbolic reasoning task (output of T018)
- [ ] T026 [US3] Implement `code/scripts/analyze_errors.py` to categorize errors into three failure modes using available features: "Action Noise" (proxy: high variance in action vectors for same text), "Context Mismatch" (proxy: low success probability in similar contexts), and "Label Ambiguity" (proxy: inconsistent labels for similar inputs) - derived from Bridge Data features. **DEPENDENCY: This task requires T020/T021 to be complete; do NOT mark as [P].**
- [ ] T027 [US3] Implement `code/scripts/analyze_errors.py` to correlate error types with specific logical constraints or visual conditions (using available metadata)
- [ ] T028 [US3] Generate the error analysis report in `code/data/results/error_analysis_report.md` with qualitative descriptions and quantitative summaries
- [ ] T029 [US3] Visualize correlations between input features and failure types in `code/data/results/error_visualizations.png`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Update `specs/001-llmxive-follow-up-extending-cosmos-3-omn/research.md` with Bridge Data pivot justification and schema adaptation notes (T005)
- [ ] T031 [P] Update `specs/001-llmxive-follow-up-extending-cosmos-3-omn/spec.md` Assumptions section to reflect Bridge Data as the source (replacing Cosmos 3)
- [ ] T032 Code cleanup and refactoring in `code/scripts/`
- [ ] T033 Performance optimization for data streaming in `code/scripts/download.py`
- [ ] T034 [P] Additional unit tests in `code/tests/`
- [ ] T035 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires trained models from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires misclassified samples from US1/US2

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
Task: "Unit test for transformation logic in code/tests/test_transform.py"
Task: "Integration test for download and transform pipeline in code/tests/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/scripts/transform.py to map continuous action vectors..."
Task: "Implement code/scripts/train.py to initialize DistilBERT..."
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
- **Data Hygiene**: Ensure `code/scripts/download.py` fails loudly if `google-research/bridge_data` is inaccessible; no synthetic fallbacks allowed.
- **Memory Constraints**: All data processing must use `streaming=True` to stay within 7 GB RAM limits.
- **Schema Adaptation**: Task T005 defines the logic to make FR-002's norm rule applicable to Bridge Data (L2 norm of first 3 dims).
- **Dual Model**: Task T012 implements two distinct models (Hard/Soft) to satisfy Plan.md's comparison requirement.
- **Baseline Approximation**: Task T023 explicitly documents the derivation of the 'physics baseline' if a native reward signal is missing.
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

- [ ] T001 [P] Create standard project directories (code/scripts, code/data/raw, code/data/processed, code/data/splits, code/models, code/tests, code/reports, code/utils) and ensure all contain `.gitkeep` files for version control persistence.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Create `code/requirements.txt` with pinned versions for `datasets`, `transformers`, `scikit-learn`, `pandas`, `numpy`, `pytest`, `pyyaml`
- [ ] T003 [P] Create `code/.gitignore` with the following exact content:
```
data/
models/
__pycache__/
*.pyc
.env
.DS_Store
```
- [X] T004 [P] Create `code/data/schema/action_schema.json` with the following exact content: `{"norm_threshold": 0.5, "text_keywords": ["Safety Constraint"], "composite_operator": "AND", "vector_dimensions": 3}`. This file defines the composite rule to be applied in T010.
- [X] T005 [P] Setup logging infrastructure in `code/utils/logger.py` to track memory usage and execution time
- [X] T006 [P] Configure environment configuration management (seeds, paths) in `code/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Transformation & Proxy Model Training (Priority: P1) 🎯 MVP

**Goal**: Transform continuous action vectors into discrete symbolic tokens and train a lightweight CPU-compatible proxy model to establish a baseline capability for symbolic reasoning.

**Independent Test**: Verify data transformation script produces a labeled CSV/JSONL file and proxy model training completes on CPU within 6 hours, consuming ≤ 7 GB RAM, outputting a model artifact and training logs.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T007 [P] [US1] Unit test for transformation logic in `code/tests/test_transform.py` (verify L2 norm of first 3 dims > 0.5 AND text context check -> "constraint_violated")
- [X] T008 [P] [US1] Integration test for download and transform pipeline in `code/tests/test_pipeline.py`

### Implementation for User Story 1

- [ ] T009 [US1] Implement `code/scripts/download.py` to fetch `bridge-to-worlds/bridge-data` via `datasets.load_dataset` using `streaming=True`, filter for instances containing 'actions' field, and save to `code/data/raw/bridge_samples.jsonl`. **MUST**: 1) Verify streaming capability by attempting to read the first record using `streaming=True`, 2) Fail loudly if fetch fails or streaming is unsupported (no synthetic fallback). <!-- FAILED: unspecified -->
- [ ] T010 [US1] Implement `code/scripts/transform.py` to: 1) Load the logical rule definition from `code/data/schema/action_schema.json` (created by T004), 2) Compute L2 norm of the **first 3 dimensions** of the 'actions' vector, 3) Apply the COMPOSITE rule: `norm > threshold` AND `text_description` contains the specific keyword "Safety Constraint" (from T004), 4) Label as "constraint_violated" if composite is true, else "constraint_satisfied", 5) Save unified dataset to `code/data/processed/unified_dataset.jsonl`. **Verification**: File exists and contains >0 rows. **DEPENDENCY: T009, T004**.
- [ ] T011a [US1] Implement `code/scripts/train.py` to initialize and train a single DistilBERT model (Hard Proxy) for symbolic target, ensuring memory usage ≤ 7 GB RAM and training time ≤ 6 hours. Include a memory monitor that logs to `code/logs/memory_profile.log` and fails if >7GB.
- [ ] T011b [US1] Verify model artifact `code/models/proxy_hard/model.pt` exists and `code/logs/memory_profile.log` exists after T011a execution. <!-- ATOMIZE: requested -->
- [X] T012 [US1] Add validation and error handling in `code/scripts/train.py` to fail loudly if real data fetch fails (no synthetic fallback)
- [X] T013 [US1] Add logging for training progress, loss convergence, and resource usage in `code/scripts/train.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Comparative Performance Analysis (Priority: P2)

**Goal**: Compare the proxy model's performance on symbolic reasoning tasks against its performance on continuous control tasks to quantify the "modality gap".

**Independent Test**: Execute evaluation script that loads trained models, runs inference on both test sets, and outputs a statistical report comparing metrics with a p-value.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T014 [P] [US2] Unit test for statistical significance calculation in `code/tests/test_stats.py`

### Implementation for User Story 2

- [X] T015 [US2] Create `code/scripts/evaluate.py` to load the trained Hard Proxy model (T011) and split predictions into symbolic and continuous domains
- [ ] T016b [US2] Implement metric calculation in `code/scripts/evaluate.py`: 1) Load the unified dataset, 2) Split into symbolic test set (label based on norm > 0.5 + text) and physical test set (label based on `physics_reward > 0.5` -> success/failure), 3) Run inference on both, 4) Calculate Brier Scores, Accuracy, F-score, and AUC-ROC for each domain, 5) **Output `code/data/results/raw_predictions.jsonl` containing `predicted_label`, `true_label`, `norm_value`, `keyword_match`, `model confidence` (float), AND `physical_label` (derived from physics_reward) for every sample**. **DEPENDENCY: T011b**.
- [ ] T016c [US2] Calculate Generalization Gap in `code/scripts/evaluate.py`: 1) Load `code/data/results/raw_predictions.jsonl` (output of T016b), 2) Compute `generalization_gap = AUC_Symbolic - AUC_Physics`, 3) Save `generalization_gap` value to `code/data/results/gap_metrics.json`. **DEPENDENCY: T016b**.
- [ ] T016d [US2] Implement Statistical Test Sequence in `code/scripts/evaluate.py`: 1) **Perform Shapiro-Wilk normality test** on the difference of metrics (Symbolic - Physical) from T016b, 2) **If normal, execute Paired t-test; else, execute Wilcoxon signed-rank test**, 3) **Output `p_value` and `is_significant` boolean**, 4) Perform **Bootstrap Confidence Interval** (with sufficient iterations for convergence) on the Generalization Gap (from T016c), 5) Output `code/data/results/comparative_analysis.json` containing side-by-side metrics, `p_value` (float), `is_significant` (boolean), `bootstrap_ci` (tuple), `normality_test_result` (Shapiro-Wilk statistic and p-value), and `physics_baseline_source`. If `physics_reward` is missing, abort with clear error. **DEPENDENCY: T016c**.
- [ ] T016e [US2] Implement `code/scripts/extract_errors.py` to load `code/data/results/raw_predictions.jsonl` (output of T016b), identify misclassified samples (where `predicted_label != true_label`), and save them to `code/data/processed/misclassified_samples.jsonl`. **MUST preserve all intermediate features (`norm_value`, `keyword_match`) and `model confidence` scores from the input file**. **DEPENDENCY: T016b**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Error Analysis & Failure Mode Identification (Priority: P3)

**Goal**: Analyze misclassified samples to identify specific patterns in failure (Action Noise, Context Mismatch, etc.).

**Independent Test**: Run error analysis script on the test set, outputting a report categorizing misclassifications and visualizing correlations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US3] Unit test for error categorization logic in `code/tests/test_analyze.py`

### Implementation for User Story 3

- [ ] T018 [US3] Create `code/scripts/analyze_errors.py` to load misclassified samples from `code/data/processed/misclassified_samples.jsonl` (output of T016e) and categorize errors into three failure modes using these specific heuristics:
 1) **Visual Ambiguity**: if model confidence < 0.6 (or observation data is missing/low quality).
 2) **Logical Complexity**: if `norm > 0.5` AND `keyword_match == False` (or vice versa).
 3) **Context Mismatch**: if `text_description` contains "Safety Constraint" AND `actions` vector is zero or contradicts the text.
 **DEPENDENCY: T016e**.
- [ ] T020 [US3] Generate the error analysis report in `code/data/results/error_analysis_report.md` with qualitative descriptions, quantitative summaries, and correlation analysis of error types with logical constraints or visual conditions. **DEPENDENCY: T018**.
- [ ] T021 [US3] Generate scatter plot in `code/data/results/error_visualizations.png`: X-axis = input feature magnitude (norm_value), Y-axis = error rate (1 - accuracy), grouped by failure mode. **DEPENDENCY: T018**.
- [ ] T022a [US3] **Calculate and report quantitative metrics for error categories**. Specifically: 1) Calculate `error_rate` and `confidence_distribution` (mean, std, min, max) for the **Visual Ambiguity** category, 2) Calculate `error_rate` for Logical Complexity and Context Mismatch, 3) Save these metrics to `code/data/results/error_metrics.json` with explicit keys: `visual_ambiguity_error_rate`, `visual_ambiguity_confidence_distribution`, `logical_complexity_error_rate`, `context_mismatch_error_rate`. **DEPENDENCY: T018**.
- [X] T022b [US3] Add unit tests for error categorization logic in `code/tests/test_analyze.py::test_categorize_visual_ambiguity` and `test_categorize_logical_complexity`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T023 [P] Update `specs/001-llmxive-follow-up-extending-cosmos-3-omn/research.md` with Bridge Data pivot justification and schema adaptation notes (T004). **DEPENDENCY: T010, T016d**.
- [~] T024 [P] Update `specs/001-llmxive-follow-up-extending-cosmos-3-omn/research.md` specifically in the "Data Source" and "Methodology" sections to explicitly state the pivot from Cosmos 3 to Bridge Data, including the rationale (availability) and the specific schema adaptation (L2 norm + text context). **DEPENDENCY: T010, T016d**.
- [ ] T025 [P] Implement performance optimization for data streaming in `code/scripts/download.py` and `code/scripts/transform.py`. **Success Criteria**: Peak memory usage must remain < 7GB during processing of the full dataset; Throughput must exceed a practical threshold for chunked reading.. Use `datasets.load_dataset(..., streaming=True)` and process in batches.
- [ ] T026 [P] Execute `bash code/scripts/quickstart.sh` (or equivalent) and verify exit code 0 and presence of all artifacts listed in spec.md Section 4.3.
- [ ] T027 [P] **Verify** `specs/001-llmxive-follow-up-extending-cosmos-3-omn/spec.md` Assumptions and Requirements sections to ensure they correctly reflect the data pivot from Cosmos 3 to Bridge dataset. **If spec.md is already correct, skip this task and log a verification pass.** **DEPENDENCY: T010, T016d**.

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
- **Data Hygiene**: Ensure `code/scripts/download.py` fails loudly if `bridge-to-worlds/bridge-data` is inaccessible; no synthetic fallbacks allowed.
- **Memory Constraints**: All data processing must use `streaming=True` to stay within 7 GB RAM limits.
- **Schema Adaptation**: Task T004 defines the exact JSON schema for the composite rule; T010 must load and apply it.
- **Single Model**: Task T011a implements a single Hard Proxy model to satisfy FR-003.
- **Baseline Validation**: Task T016b/T016d explicitly validates the existence of `physics_reward` and aborts if missing, satisfying SC-001.
- **Error Analysis**: Task T016e extracts raw misclassified samples from T016b's output; T018 depends on T016e.
- **Bootstrap CI & Statistical Test**: Task T016d explicitly implements the Shapiro-Wilk -> t-test/Wilcoxon sequence AND the Bootstrap Confidence Interval required by Plan.md Phase 3 T025 and FR-004.
- **Visual Ambiguity Metrics**: Task T022a explicitly calculates and reports `error_rate` and `confidence_distribution` for Visual Ambiguity to satisfy FR-005.
- **Confidence Preservation**: Task T016b explicitly outputs `model confidence` scores to ensure T016e and T018 have the required data.
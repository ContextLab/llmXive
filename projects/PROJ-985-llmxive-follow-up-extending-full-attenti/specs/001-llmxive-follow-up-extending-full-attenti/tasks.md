# Tasks: llmXive Follow-up: Extending "Full Attention Strikes Back"

**Input**: Design documents from `/specs/001-llmxive-static-sparsification/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Research Pipeline**: `code/data/`, `code/models/`, `code/evaluation/`, `code/lib/`
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure with exact directories: `code/`, `tests/`, `data/`, `code/lib/`, `code/data/`, `code/models/`, `code/evaluation/`, `data/results/`, `data/logs/`, `data/intermediate/`
- [X] T002 Initialize Python 3.11 project with `code/requirements.txt` containing **pinned versions** for all dependencies (transformers, torch, datasets, scikit-learn, spacy, kenlm, numpy, pandas) to ensure reproducibility
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 [P] Initialize pytest configuration and create empty test suite structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until T005 and T006 are complete. T007/T008 are optional for debugging but recommended and do NOT block T011/T012 execution.

- [ ] T005 Implement memory-efficient data loader in `code/lib/data_loader.py` that streams RULER dataset chunks, enforces GB RAM limit, and includes a **unit test asserting peak memory usage < 7GB on a synthetic Moderate-sized stream**; log memory profile to `data/logs/memory_profile.csv`
- [X] T006 Create base data entities (`TokenUnit`, `AttentionMap`, `StaticHeuristic`) in `code/lib/entities.py`
- [X] T007 [P] [Optional] Implement attention map visualization and debugging utilities in `code/lib/attention_utils.py`
- [X] T008 [P] [Optional] Setup logging infrastructure to track pipeline stages and memory usage in `code/lib/logging_config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ground Truth Extraction & Static Feature Computation (Priority: P1) 🎯 MVP

**Goal**: Generate parallel datasets of RTPurbo-selected tokens and static linguistic features for the RULER corpus subset.

**Independent Test**: Run the extraction pipeline on a representative document sample and verify the output CSV contains valid entropy, POS tags, and binary RTPurbo labels without GPU memory errors.

### Tests for User Story 1 (OPTIONAL)

- [X] T009 [P] [US1] Unit test for feature extraction logic in `tests/unit/test_feature_extraction.py`
- [X] T010 [P] [US1] Integration test for ground truth generation on small sample in `tests/integration/test_ground_truth.py`

### Implementation for User Story 1

- [X] T011 [US1] Implement RULER dataset downloader with streaming support in `code/data/download.py` (FR-001). **Constraint**: Must use `datasets.load_dataset(..., streaming=True)` and **fail loudly** if the real source is unreachable; **NO** synthetic fallbacks or mock data generation.
- [ ] T012 [US1] Implement frozen Llama-3-8B attention map generator and RTPurbo indexer in `code/data/extract_ground_truth.py` (FR-002). **Requirements**: Load model with `torch.no_grad()` and `requires_grad=False`; **verify model.requires_grad is False**; save attention maps to `data/intermediate/attention_maps.h5`. **Constraint**: Must use CPU-only quantization (e.g., low-bit) or strictly sampled subset to fit constrained RAM resources. **NO** external offloading to Kaggle or other runners.
- [X] T013 [US1] Implement static feature computation (Entropy, POS via spaCy, Position, KenLM perplexity) in `code/data/compute_features.py` (FR-003)
- [X] T014 [US1] Implement dataset merger to join ground truth labels (from T012) with static features (from T013) into `data/intermediate/merged_dataset.csv`
- [X] T015 [US1] Add edge case handling for ambiguous tokens (special chars, emojis) in `code/data/compute_features.py` (Edge Case 1)
- [ ] T016 [US1] Add anomaly detection for documents with zero RTPurbo tokens in `code/data/extract_ground_truth.py` (Edge Case 2). **Requirement**: Explicitly flag and **exclude them from the final statistical comparison** to prevent skewing results. **Output**: Log anomalies to `data/logs/anomalies.csv` and exclude rows from `merged_dataset.csv`. <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. **T014 must complete before T019 starts.**

---

## Phase 4: User Story 2 - Static Predictor Training & Heuristic Derivation (Priority: P2)

**Goal**: Train a CPU-based classifier to predict RTPurbo selection and derive a deterministic rule-based heuristic.

**Independent Test**: Train the model on a training split and evaluate on validation; verify the output includes a specific rule set and baseline accuracy metric.

### Tests for User Story 2 (OPTIONAL)

- [X] T017 [P] [US2] Unit test for rule derivation logic in `tests/unit/test_rule_derivation.py`
- [X] T018 [P] [US2] Integration test for training pipeline with 5 seeds in `tests/integration/test_training.py`

### Implementation for User Story 2

- [X] T019 [US2] Implement CPU-based classifier training (Decision Tree/Logistic Regression) with **independent random seeds** in `code/models/train_static.py` (FR-004). **Input**: `data/intermediate/merged_dataset.csv` (output of T014). **Output**: trained models saved to `data/intermediate/models/seeds/`.
- [ ] T019b [US2] Implement evaluation of the trained static models on the test set to generate **performance scores** (precision/recall) in `code/models/evaluate_static.py` (FR-004). **Output**: `data/intermediate/static_eval_scores.json`.
- [ ] T019c [US2] Implement aggregation logic to compute **mean and variance** of the static evaluation scores and save to `data/results/static_aggregated.json`. **Schema**: `{mean_metric, std_metric, n_seeds, seed_values: []}` (FR-004).
- [X] T020 [US2] Implement rule derivation logic to extract hard thresholds from model importance in `code/models/derive_rules.py` (FR-004)
- [X] T021 [US2] Implement static heuristic application script to reconstruct RTPurbo tokens using only rules in `code/models/apply_heuristic.py` (FR-004)
- [X] T022 [US2] Add metrics calculation (Precision/Recall) for static predictor against ground truth in `code/lib/metrics.py` (FR-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sparsification Evaluation & Statistical Comparison (Priority: P3)

**Goal**: Evaluate static-heuristic sparsification against baselines and perform statistical significance testing.

**Independent Test**: Run evaluation on test set and generate report with perplexity, exact match, and p-values comparing methods.

### Tests for User Story 3 (STRICT PREREQUISITE)

**⚠️ CRITICAL ORDERING**: T023 and T024 MUST be written and verified to fail before any implementation tasks (T025-T032) begin. These are NOT parallel tasks; they are sequential prerequisites to ensure the contract is defined before implementation.

- [X] T023 [US3] Contract test for statistical analysis output format in `tests/contract/test_stats_output.py`
- [ ] T024 [US3] Integration test for full baseline comparison in `tests/integration/test_baselines.py`

### Implementation for User Story 3

- [ ] T025 [US3] Implement full attention baseline runner in `code/evaluation/run_baselines.py` (FR-005)
- [ ] T026a [US3] Implement learned sparse (RTPurbo) baseline runner to **execute multiple independent random seeds** and save individual results to `data/intermediate/baseline_seeds/` (FR-008/FR-006)
- [ ] T026b [US3] Implement aggregation logic to compute **mean and variance** of the seed results from T026a and save to `data/results/baseline_aggregated.json`. **Schema**: `{mean_metric, std_metric, n_seeds, seed_values: []}` (FR-008).
- [ ] T027 [US3] Implement static heuristic sparsification runner in `code/evaluation/run_baselines.py` (FR-005). **Input**: Rules from T020. **Output**: Perplexity and Exact Match metrics to `data/results/static_metrics.json`.
- [ ] T029 [US3] Implement paired t-test/Wilcoxon test for statistical significance in `code/evaluation/stats_analysis.py` (FR-006). **Input**: Aggregated baselines (T026b) and Static aggregated results (T019c). **Requirement**: Must perform a **paired t-test on document-level performance differences** between Static (mean of multiple seeds) and Learned Sparse (mean of 5 seeds).
- [ ] T030 [US3] Generate final evaluation report at `data/results/final_report.md` containing: Perplexity, Exact Match, P-values, and Statistical Significance (SC-002, SC-004). **Required Sections**: Executive Summary, Methodology, Results Table, Statistical Significance.
- [ ] T031 [US3] Implement Falsifiability Check: Calculate the performance drop (Static vs Learned) and compare against the **<1% threshold** defined in Constitution Principle VI. Log the boolean result and the exact drop percentage to `data/results/metrics.csv`.
- [ ] T032 [US3] Implement pipeline timing instrumentation to log start/end timestamps to `data/results/timing_report.json`.
- [ ] T032b [US3] Implement post-execution check script that reads `timing_report.json` and asserts duration < 21600s (6 hours). Log result to `data/results/timing_report.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `quickstart.md` and `research.md`
- [ ] T034 Code cleanup and refactoring of data loading logic
- [ ] T035 Performance optimization for streaming pipeline
- [ ] T036 [P] Additional unit tests for edge cases in `tests/unit/`
- [ ] T037 Run quickstart.md validation to ensure reproducibility on free tier

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **T005/T006 block all user stories**
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (requires `data/intermediate/merged_dataset.csv` from T014)
- **User Story 3 (P3)**: Depends on US1 and US2 completion (requires derived rules and baselines)

### Within Each User Story

- **Test-Implementation Order**: For US3 specifically, T023 and T024 (Tests) are strict prerequisites. They must be written, run, and verified to fail before T025-T032 (Implementation) begin. This ensures the contract is defined before coding. For US1 and US2, tests are optional parallel tasks.
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- T007/T008 in Phase 2 can run in parallel with T005/T006 (but T005/T006 are critical path)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for US1 and US2 marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for feature extraction logic in tests/unit/test_feature_extraction.py"
Task: "Integration test for ground truth generation on small sample in tests/integration/test_ground_truth.py"

# Launch all implementation tasks for User Story 1 together:
Task: "Implement RULER dataset downloader with streaming support in code/data/download.py"
Task: "Implement static feature computation in code/data/compute_features.py"
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
 - Developer A: User Story 1 (Data Generation)
 - Developer B: User Story 2 (Model Training)
 - Developer C: User Story 3 (Evaluation)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (except US3 tests which are sequential)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Data Flow**: T012 -> T013 -> T014 -> T019 -> T019b -> T019c -> T020 -> T027 -> T029 -> T030
- **Data Integrity**: T011 must fail loudly on missing real data; T012 must run on CPU/Quantized; T016 must exclude anomalies.
- **Statistical Validity**: T029 depends on T019c (Static Eval Aggregation) and T026b (Learned Eval Aggregation).
- **Dependencies**:
 - T027 depends on T020 (Rules).
 - T029 depends on T019c, T026b, and T027 (for static metrics).
 - T030 depends on T029, T031, T032b.
 - **T025-T032 depend on T023 and T024 being written and failing.**
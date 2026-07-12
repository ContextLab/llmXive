# Tasks: llmXive Follow-up: Extending EnterpriseClawBench

**Input**: Design documents from `/specs/001-llmxive-extend-enterprisecrclawbench/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure: `mkdir -p src/features src/modeling src/intervention src/eval src/utils data/raw data/processed data/results data/models tests/unit tests/integration tests/contract`
- [ ] T002 Create `requirements.txt` with pinned versions: `torch-cpu`, `transformers`, `scikit-learn`, `pandas`, `networkx`, `statsmodels`, `pytest`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup data directory structure (`data/raw/`, `data/processed/`, `data/results/`)
- [ ] T004a [US1] [FR-001] Verify existence and integrity of initial success/failure ground truth labels in raw dataset before deriving secondary labels; Write validation report to `data/results/ground_truth_validation.json`
- [ ] T005 [P] Implement citation verification script in `src/utils/verify_citations.py` (Read citations from spec.md, query primary sources, write pass/fail status to `data/results/citation_report.json` as a list of objects with 'source', 'status', 'error_message')
- [ ] T006 [P] Create base configuration loader for paths and seeds in `src/config.py`
- [ ] T007 Implement memory and time monitoring utility in `src/utils/resource_monitor.py` (logs `/proc/self/status` RSS and wall-clock)
- [ ] T008 Setup artifact hashing utility in `src/utils/hash_artifacts.py`
- [ ] T009 [US1] Add tests/unit/test_features.py with function: `test_syntax_tree_depth_calculates_correctly`
- [ ] T009b [US1] Add tests/unit/test_features.py with function: `test_pragmatic_marker_identification_works`
- [ ] T010 [US1] Add tests/integration/test_extraction.py with function: `test_parser_handles_empty_file`
- [ ] T010b [US1] Add tests/integration/test_extraction.py with function: `test_parser_handles_large_file`
- [ ] T011 [P] Implement dataset fetcher in `src/utils/data_loader.py` to download EnterpriseClawBench from canonical source (NAB/UCI/GitHub) with checksum verification; save to `data/raw/`
- [ ] T013a [US1] Implement semantic proxy extractor in `src/features/extract.py` to extract error codes and failed function names; save to `data/processed/semantic_proxies.jsonl`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Syntactic & Pragmatic Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Parse raw EnterpriseClawBench logs to extract syntax tree depth, token frequency, and pragmatic markers for failure/success classification.

**Independent Test**: Run extraction on a small, manually verified subset and confirm output JSON contains correct feature vectors and labels.

### Implementation for User Story 1

- [ ] T012 [US1] Implement log parser in `src/features/extract.py` to read raw logs from `data/raw/`
- [ ] T013 [US1] Implement syntax tree depth calculator using `networkx` in `src/features/extract.py`
- [ ] T014 [US1] Implement token frequency distribution counter in `src/features/extract.py`
- [ ] T015 [US1] Implement pragmatic marker detector (error recovery, state transitions) in `src/features/extract.py`
- [ ] T016 [US1] Implement generator-based log parser in `src/features/extract.py` that yields chunks of 100MB to prevent memory overflow; verify peak RSS < 7GB in full pipeline
- [ ] T017 [US1] Generate `data/processed/features.jsonl` with labeled status (success/failure) and feature vectors
- [ ] T018 [US1] Perform Mann-Whitney U test on feature distributions (failed vs success) AND apply Bonferroni or Benjamini-Hochberg FDR correction; log results to `data/results/distinctiveness_stats.csv` with columns: 'feature', 'p_value', 'corrected_p_value', 'significant'

**Checkpoint**: Feature extraction complete; data ready for triplet construction.

---

## Phase 4: User Story 2 - Lightweight Adapter Training & Feasibility Prediction (Priority: P2)

**Goal**: Train a distilled T5-small model on feature triplets to predict "correction feasibility" (correctable vs. unfixable) within CPU constraints.

**Independent Test**: Verify loss convergence and binary classification accuracy >50% on held-out validation set without OOM.

### Implementation for User Story 2

- [ ] T021a [US2] Implement Semantic Outcome Oracle logic in `src/modeling/oracle.py` to derive "correctable" labels via rule-based logic: `correctable = (error_type in [syntax, token_mismatch] AND no_reasoning_gap)` where `no_reasoning_gap = absence of semantic error codes (e.g., 404, 500, ValueError)`; ensure logic excludes all US1 features (syntax depth, token freq) to maintain independence
- [ ] T021b [US2] Implement annotation workflow script in `src/modeling/oracle.py` to generate ground truth labels for "correctable" status
- [ ] T021c [US2] Execute Manual Expert Annotation workflow on a sample of traces to validate/expand rule-based labels if oracle is insufficient; save to `data/processed/manual_labels.jsonl`
- [ ] T021d [US2] Verify Oracle Independence: run correlation check between US1 features and oracle labels; fail if correlation > 0.1
- [ ] T019 [US2] Add tests/unit/test_modeling.py with function: `test_triplet_construction_logic` (depends on T021a)
- [ ] T019b [US2] Add tests/unit/test_modeling.py with function: `test_semantic_outcome_oracle_labels` (depends on T021a)
- [ ] T022 [US2] Implement triplet constructor in `src/modeling/dataset.py` linking failed traces to successful corrections using labels from T021a/T021c
- [ ] T023 [US2] Implement T5-small (≤60M params) model wrapper in `src/modeling/model.py` (CPU-only, default precision)
- [ ] T024 [US2] Implement training loop in `src/modeling/train.py` with memory monitoring (T007)
- [ ] T025 [US2] Implement fallback logic in `src/modeling/train.py`: if peak RSS > 6.5GB, skip training, log OOM to `data/results/fallback_log.txt`, and report null model baseline (accuracy=0.5) without heuristic rewrite
- [ ] T026 [US2] Save trained adapter weights to `data/models/adapter_feasibility.pth`
- [ ] T027 [US2] Evaluate model on validation set; log accuracy and confusion matrix to `data/results/feasibility_metrics.json`
- [ ] T030 [US2] Implement Adapter Policy Learner in `src/intervention/policy_learner.py` to fine-tune T5-small on (prompt, AST node diff string) pairs to learn a generalizable correction policy based on abstract fix representations (AST node diffs); **must explicitly verify** that the policy learns from abstract fix representations and not raw traces, and validate generalizability per FR-004
- [ ] T020 [US2] Add tests/integration/test_training.py with function: `test_loss_convergence` (depends on T024)
- [ ] T020b [US2] Add tests/integration/test_training.py with function: `test_accuracy_threshold` (depends on T024)

**Checkpoint**: Feasibility predictor and policy learner ready; can classify traces and apply corrections.

---

## Phase 5: User Story 3 - Artifact Delivery Score Evaluation (Priority: P3)

**Goal**: Evaluate the impact of the adapter + learned correction policy on the Artifact Delivery Score using a representative task set.

**Independent Test**: Run baseline and adapter-enhanced configurations on Lite set; compare scores with statistical significance (p < 0.05).

### Implementation for User Story 3

- [ ] T028 [US3] Add tests/contract/test_harness.py with function: `test_harness_runs_task`
- [ ] T028b [US3] Add tests/contract/test_harness.py with function: `test_harness_returns_score`
- [ ] T031 [US3] Implement Evaluation Harness in `src/eval/harness.py` to run tasks on `data/processed/lite_set.json`
- [ ] T032 [US3] Run Baseline Evaluation ("Model + Harness") and log scores to `data/results/baseline_scores.csv`
- [ ] T033 [US3] Run Adapter-Enhanced Evaluation ("Model + Adapter + Policy Learner + Harness") and log scores to `data/results/adapter_scores.csv`
- [ ] T034 [US3] Implement statistical analysis script in `src/eval/stats.py` to run **McNemar's Test** (if binary outcomes) as primary method per Plan Phase 4, with **Wilcoxon signed-rank** (if continuous) as fallback; output p-value to `data/results/stats_report.json` with schema: 'test_type', 'p_value', 'effect_size', 'conclusion'
- [ ] T034a [US3] Implement McNemar's Test for binary outcomes as primary method per Plan Phase 4
- [ ] T034b [US3] Implement Wilcoxon signed-rank test as fallback for continuous outcomes
- [ ] T035 [US3] Add resource monitoring wrapper to `src/eval/harness.py` that asserts peak RSS <= 7GB and runtime <= 6h, raising an error if violated; verify constraints for full evaluation run
- [ ] T036 [US3] Generate final report in `data/results/evaluation_report.md` including p-value and power analysis
- [ ] T029 [US3] Add tests/integration/test_evaluation.py with function: `test_baseline_vs_adapter`
- [ ] T029b [US3] Add tests/integration/test_evaluation.py with function: `test_statistical_significance`

**Checkpoint**: Evaluation complete; statistical significance established.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `README.md` and `docs/`
- [ ] T038 Code cleanup and refactoring
- [ ] T039 [P] Run `verify_citations.py` gate check
- [ ] T040 [P] Run `hash_artifacts.py` to update `state/`
- [ ] T041 Run quickstart.md validation

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
- **User Story 2 (P2)**: Depends on US1 completion (needs `data/processed/features.jsonl`)
- **User Story 3 (P3)**: Depends on US2 completion (needs trained adapter and policy learner logic)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utils before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All unit tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all unit tests for User Story 1 together:
Task: "Add tests/unit/test_features.py with functions: test_syntax_tree_depth_calculates_correctly, test_pragmatic_marker_identification_works"

# Launch all models for User Story 1 together:
Task: "Implement log parser in src/features/extract.py"
Task: "Implement syntax tree depth calculator using networkx in src/features/extract.py"
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
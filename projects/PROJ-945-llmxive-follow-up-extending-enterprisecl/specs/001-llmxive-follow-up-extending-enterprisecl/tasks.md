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
- [ ] T003b [P] [SPEC UPDATE] Update `spec.md` FR-003 to change requirement from "distilled T5-small" to "scikit-learn classifier (Random Forest or Logistic Regression)" to align with Plan and implementation; remove exclusion of Llama-3-8B as it is no longer relevant to the corrected scope. <!-- FAILED: unspecified -->

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T011 [P] Implement dataset fetcher in `src/utils/data_loader.py` to download EnterpriseClawBench from canonical source (NAB/UCI/GitHub) with checksum verification; save to `data/raw/`; **MUST raise exception on failure, no synthetic fallback**
- [ ] T004a [US1] [FR-001] Verify existence and integrity of initial success/failure ground truth labels in raw dataset (after T011); Write validation report to `data/results/ground_truth_validation.json` with schema: `{ 'status': 'pass|fail', 'issues': [], 'sample_size': int, 'pass_criteria': 'pass if >95% labels exist' }`
- [~] T005 [P] Implement citation verification script in `src/utils/verify_citations.py` (Read citations from spec.md using regex for '## References' block, query primary sources via DOI, write pass/fail status to `data/results/citation_report.json` as a list of objects with 'source', 'status', 'error_message')
- [~] T006 [P] Create base configuration loader for paths and seeds in `src/config.py`
- [~] T007 Implement memory and time monitoring utility in `src/utils/resource_monitor.py` (logs `/proc/self/status` RSS and wall-clock)
- [~] T008 Setup artifact hashing utility in `src/utils/hash_artifacts.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Syntactic & Pragmatic Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Parse raw EnterpriseClawBench logs to extract syntax tree depth, token frequency, and pragmatic markers for failure/success classification.

**Independent Test**: Run extraction on a small, manually verified subset and confirm output JSON contains correct feature vectors and labels.

### Implementation for User Story 1

- [~] T012 [US1] Implement log parser in `src/features/extract.py` to read raw logs from `data/raw/`
- [~] T013 [US1] Implement syntax tree depth calculator using `networkx` in `src/features/extract.py`
- [ ] T014 [US1] Implement token frequency distribution counter in `src/features/extract.py`
- [ ] T015 [US1] Implement pragmatic marker detector (error recovery, state transitions) in `src/features/extract.py`
- [ ] T016 [US1] Implement generator-based log parser in `src/features/extract.py` that yields chunks of substantial size to prevent memory overflow; verify peak RSS < 7GB in full pipeline
- [ ] T016b [US1] [FR-007] Invoke `resource_monitor.py` (T007) during T016 execution to explicitly log peak memory usage and verify streaming compliance; save log to `data/results/extraction_memory_log.json`; **Pass if peak RSS < 7GB, else FAIL**
- [ ] T017 [US1] Generate `data/processed/features.jsonl` with labeled status (success/failure) and feature vectors
- [ ] T018 [US1] Perform Mann-Whitney U test on feature distributions (failed vs success) AND apply FDR correction: **Use Benjamini-Hochberg if features > 10, else Bonferroni**; log results to `data/results/distinctiveness_stats.csv` with columns: 'feature', 'p_value', 'corrected_p_value', 'significant'
- [ ] T018b [US1] [SC-001] Generate `data/results/distinctiveness_report.md` containing visual plots (histograms/boxplots) and statistical evidence proving feature distinctiveness between failed and successful traces; **Depends on T018**
- [ ] T009-unit [US1] Add tests/unit/test_features.py with functions: `test_syntax_tree_depth_calculates_correctly`, `test_pragmatic_marker_identification_works`
- [ ] T010-int [US1] Add tests/integration/test_extraction.py with functions: `test_parser_handles_empty_file`, `test_parser_handles_large_file`

**Checkpoint**: Feature extraction complete; data ready for triplet construction.

---

## Phase 4: User Story 2 - Lightweight Adapter Training & Feasibility Prediction (Priority: P2)

**Goal**: Train a scikit-learn classifier on feature triplets to predict "correction feasibility" (correctable vs. unfixable) within CPU constraints.

**Independent Test**: Verify accuracy convergence and binary classification accuracy >50% on held-out validation set without OOM.

### Implementation for User Story 2

- [ ] T021a-1 [US2] [FR-002] [P] Derive error schema from raw logs in `data/raw/` to identify available error type fields; save schema to `data/processed/error_schema.json`
- [ ] T021a [US2] [FR-002] Implement Semantic Outcome Oracle logic in `src/modeling/oracle.py` using the derived schema (T021a-1) to derive "correctable" labels via rule-based logic: `correctable = (error_type in ['syntax', 'token_mismatch'] AND error_type not in ['semantic_error', 'reasoning_gap'])`; **DO NOT use hardcoded HTTP codes**; ensure logic excludes all US1 features to maintain independence
- [ ] T021b [US2] [FR-002] Implement Oracle Validation script in `src/modeling/oracle.py` to verify rule-based labels are deterministic and consistent on a small random sample (seeded) of the dataset; save validation report to `data/results/oracle_validation.json`
- [ ] T021d [US2] [FR-002] Verify Oracle Independence: run **Spearman** correlation check between US1 features and oracle labels **per-feature**; fail if correlation > 0.1 (p-value < 0.05); log results to `data/results/oracle_independence.json` with schema: `{ 'feature': str, 'correlation': float, 'p_value': float, 'independent': bool }`
- [ ] T021e [US2] [FR-002] Enforce Rule-Based Only: Assert that no manual labels exist in the dataset; if manual labels are found, raise an error and halt; log assertion to `data/results/rule_based_enforcement.json`
- [ ] T022 [US2] Implement triplet constructor in `src/modeling/dataset.py` linking failed traces to successful corrections using labels from T021a; save to `data/processed/triplets.jsonl`
- [ ] T029-model [US2] Add tests/unit/test_modeling.py with functions: `test_triplet_construction_logic`, `test_semantic_outcome_oracle_labels`
- [ ] T023-classifier [US2] [FR-003] Implement scikit-learn classifier (Random Forest or Logistic Regression) in `src/modeling/model.py` for feasibility prediction (CPU-only); **DO NOT use T5 for prediction**; save weights to `data/models/adapter_feasibility.pkl`
- [ ] T024 [US2] Implement training loop in `src/modeling/train.py` for scikit-learn classifier with memory monitoring (T007); **Save checkpoint every epoch**
- [ ] T025 [US2] [FR-007] Implement OOM fallback in `src/modeling/train.py`: if peak RSS > 6.5GB, load the **last successful checkpoint** (from T024), log OOM to `data/results/fallback_log.txt`, and report null model baseline (accuracy=0.5) without heuristic rewrite; **no dummy model needed**
- [ ] T025a [US2] [FR-004] Implement convergence fallback in `src/modeling/train.py`: if loss derivative > 1e-4 for 10 epochs, trigger **rule-based syntax correction script** (from T021a logic) to generate `fallback_predictions.jsonl`; log convergence failure to `data/results/convergence_log.txt`
- [ ] T026 [US2] Evaluate model on validation set; log accuracy and confusion matrix to `data/results/feasibility_metrics.json`
- [ ] T030-eval [US2] Add tests/integration/test_training.py with functions: `test_loss_convergence`, `test_accuracy_threshold`

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
- [ ] T033 [US3] Run Adapter-Enhanced Evaluation ("Model + Adapter + Harness") and log scores to `data/results/adapter_scores.csv`
- [ ] T034 [US3] [FR-005] Implement statistical analysis script in `src/eval/stats.py` with dynamic decision rule:
 1. Check if ADS is strictly binary (`set(ads) == {0, 1}`); if yes, use McNemar's test.
 2. If continuous, compute `differences = ads_adapter - ads_baseline`.
 3. Run Shapiro-Wilk test (alpha=0.05) on `differences`.
 4. If p > 0.05 (normal), use paired t-test; else use Wilcoxon signed-rank.
 Output p-value to `data/results/stats_report.json` with schema: `{'test_type': str, 'statistic': float, 'p_value': float, 'effect_size': float, 'conclusion': str}`
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
- [ ] T040 [P] Run `verify_citations.py` gate check
- [ ] T041 [P] Run `hash_artifacts.py` to update `state/`
- [ ] T042 Run quickstart.md validation

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
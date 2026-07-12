# Tasks: GateMem Gatekeeper Extension

**Input**: Design documents from `/specs/001-gatekeeper-memory-governance/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure: Execute `mkdir -p projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/{gatekeeper,metrics,analysis,data} projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/data/{raw,processed,logs} projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/tests/{unit,integration,contract} projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/paper projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/scripts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Initialize Python 3.11 project: Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/requirements.txt` containing pinned versions of `transformers`, `torch` (CPU), `scikit-learn`, `pandas`, `pytest`, `sentence-transformers`
- [ ] T002a [P] Create dependency verification script: Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/scripts/verify_deps.py` that parses `requirements.txt` and asserts absence of GPU libraries (bitsandbytes, CUDA) and validates CPU-only flags; output must be a log file `scripts/verify_deps.log`
- [ ] T002b [P] Profile DistilBERT model: Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/scripts/profile_model.py` that explicitly loads the frozen DistilBERT model in default precision on CPU, verifies no GPU allocation, and outputs a profile report to `data/logs/model_profile.json`
- [ ] T002c [P] Validate frozen model weights: Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/scripts/validate_model_weights.py` that loads the specific frozen DistilBERT weights used for intent classification, runs a forward pass on CPU, and confirms no GPU tensors or quantization libraries are required; output must be `data/logs/model_validation.json`
- [ ] T002d [P] Validate sentence-transformers compatibility: Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/scripts/validate_sentence_transformers.py` that verifies the specific sentence-transformers model variant selected for leakage detection is CPU-only and does not require quantization libraries; output must be `data/logs/sentence_transformers_validation.json`
- [~] T003 [P] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/`
- [~] T004 Implement data loader: Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/data/loader.py` with `fetch_gatemem()` function to download GateMem dataset from verified HuggingFace URL
- [~] T004a Implement data validation: Extend `loader.py` with `validate_fields()` function to check for `leak-target` and `role` fields in the dataset
- [~] T004c Implement fallback strategy: Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/data/loader.py` function `inject_fallback_data()` that, if `leak-target` is missing, switches to using existing `rule-log` fields in the dataset as ground truth (NO synthetic data generation); output must be a validated dataset file in `data/processed/`
- [~] T005 [P] Implement data preprocessing: Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/data/preprocess.py` with `clean_and_format()` function (Depends on T004 completion)
- [~] T006 [P] Setup in-memory deletion log structure and role definition parser in `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/gatekeeper/rules.py`
- [~] T007 Create base data models: Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/models.py` containing Pydantic/TypedDict definitions for Query, MemoryChunk, DeletionLog, EvaluationResult
- [~] T008 Configure logging: Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/logging_config.py` with error handling and random seed pinning; verify log file creation on run
- [~] T009 Setup environment config: Create `.env.example` and `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/config.py` with CPU-only validation logic; verify `Config` class raises error if CUDA detected
- [~] T023a [P] Define rubric: Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/contracts/rubric.yaml` containing the standardized LLM-as-a-Judge rubric text (Depends on T001)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Gatekeeper Pipeline Execution (Priority: P1) 🎯 MVP

**Goal**: Implement the pre-filtering gatekeeper module that intercepts queries, validates against rules/deletion logs, and passes authorized data to the retrieval engine.

**Independent Test**: Run a single query with an unauthorized role and a deleted target; verify the gatekeeper blocks retrieval before LLM execution.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T010 [P] [US1] Contract test for gatekeeper blocking unauthorized access in `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/tests/contract/test_gatekeeper.py`
- [~] T011 [P] [US1] Integration test for deletion log priority over role rules in `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [~] T012 [P] [US1] Implement frozen DistilBERT intent classifier in default precision (CPU-only) in `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/gatekeeper/classifier.py`
- [~] T013 [P] [US1] Implement deterministic rule engine (regex/logic) for deletion log enforcement in `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/gatekeeper/rules.py`
- [~] T014a [US1] Implement gatekeeper pipeline skeleton: Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/gatekeeper/pipeline.py` with `run_query()` function scaffold
- [ ] T014b [US1] Implement gatekeeper pipeline logic: Add `rule_check()`, `classify_intent()`, and timeout enforcement logic to `pipeline.py`; include a unit test in `tests/unit/test_pipeline.py` that triggers `TimeoutError` and logs the event to `data/logs/timeout.log`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantitative Metric Calculation (Priority: P2)

**Goal**: Calculate Access Control, Forgetting, and Utility scores by comparing gatekeeper outputs against GateMem ground-truth annotations.

**Independent Test**: Run evaluation on a fixed subset; verify output CSV contains non-null Access Control, Forgetting, and Utility scores.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for metric calculation formulas in `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/tests/contract/test_metrics.py`
- [ ] T019 [P] [US2] Integration test for leakage detection against ground truth in `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/tests/integration/test_leakage.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement Leakage Detector: Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/metrics/leakage_detector.py` with hybrid (Exact + Semantic) detection logic
- [ ] T023 [US2] Implement Utility Judge: Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/metrics/utility_judge.py` using the rubric from T023a to calculate Utility scores (0.0–1.0)
- [ ] T021 [US2] Implement Access Control score: Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/metrics/calculator.py` with `calculate_access_control()` function: `(1 - (empirical_leaks / total_unauthorized_attempts)) * 100`
- [ ] T022 [US2] Implement Forgetting score: Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/metrics/calculator.py` with `calculate_forgetting()` function: `(1 - (empirical_deleted_leaks / total_deleted_targets)) * 100`
- [ ] T023b [US2] Handle missing annotations: In `calculator.py`, implement logic to skip rows where `leak-target` is null, log count to `data/processed/metrics_summary.json` (key: `exclusion_count`), and return the count in the result dict
- [ ] T024 [US2] Generate output CSV: Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/metrics/calculator.py` function to write all three metrics to `data/processed/metrics.csv`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance & Cost Profiling (Priority: P3)

**Goal**: Perform statistical testing (permutation/Wilcoxon) and cost profiling (latency, RAM) to validate hypotheses and feasibility.

**Independent Test**: Run analysis on full test set; verify p-value < 0.05 for Access Control improvement and latency report within 6-hour limit.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Contract test for statistical significance thresholds in `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/tests/contract/test_stats.py`
- [ ] T027 [P] [US3] Integration test for cost profiling under load in `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/tests/integration/test_profiler.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement statistical analysis: Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/analysis/stats.py` with Permutation tests, Wilcoxon, Bootstrapping functions
- [ ] T029 [US3] Implement multiple-comparison correction: Add `apply_bonferroni()` and `apply_holm()` functions in `stats.py` for domain analysis
- [ ] T030a [US3] Implement sensitivity analysis (Semantic): Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/analysis/stats.py` function to sweep the semantic similarity threshold across a range of high values for the Leakage Detector, calculate FP/FN rates, and write the results to `data/processed/sensitivity_analysis.csv` (Depends on T020)
- [ ] T031 [US3] Implement cost profiler: Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/analysis/profiler.py` to track total inference latency and peak CPU memory usage; include logic to enforce a 6-hour timeout and fail the pipeline with a "Compute Exceeded" error if the limit is breached
- [ ] T032 [US3] Verify utility constraint: Add a function in `code/analysis/stats.py` that returns boolean and logs warning if `baseline_utility - new_utility > 0.10 * baseline_utility`; write result to `data/processed/utility_constraint_check.json`
- [ ] T034 [US3] Execute correction and output report: Run T029 logic on T028 output (domain-specific results), apply multiple-comparison correction, and write the corrected p-values to `data/processed/corrected_pvalues.csv`; this artifact serves as the primary evidence for SC-004
- [ ] T033 [US3] Generate final report: Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/analysis/profiler.py` function to output report with p-values, effect sizes, confidence intervals, and resource usage logs to `data/processed/final_analysis_report.md`; this report must reference the corrected p-values from `data/processed/corrected_pvalues.csv`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T035 [P] Update state: Update `state/projects/{PROJECT_ID}.yaml` with artifact hashes for `data/` and `code/` per Principle V (replace {PROJECT_ID} with actual project ID)
- [ ] T036 Code cleanup and refactoring in `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/`
- [ ] T037 Performance optimization to ensure full pipeline runs within 6 hours on 2-core CPU
- [ ] T038 [P] Run `quickstart.md` validation to ensure reproducibility
- [ ] T039 Generate final research paper draft: Create `projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/paper/draft.md` containing sections: Abstract, Methods, Results (with placeholders for metrics), Conclusion

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 to generate outputs
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US1 and US2 outputs for analysis

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
Task: "Contract test for gatekeeper blocking unauthorized access in tests/contract/test_gatekeeper.py"
Task: "Integration test for deletion log priority over role rules in tests/integration/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement frozen DistilBERT intent classifier in code/gatekeeper/classifier.py"
Task: "Implement deterministic rule engine in code/gatekeeper/rules.py"
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
- **CPU Constraint**: All tasks must run on a multi-core CPU with moderate RAM.. No GPU, no 8-bit/4-bit quantization.
- **Data Integrity**: Use real GateMem dataset only. No synthetic data fabrication.
# Tasks: Function-Aware FIM for Non-Code Domains

**Input**: Design documents from `/specs/001-fim-non-code-transfer/`
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
  
  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan: `mkdir -p code/data code/training code/evaluation code/utils code/tests data/raw/gsm8k data/raw/logiqa data/processed data/artifacts/results contracts/ docs/`
- [ ] T002 Initialize Python 3.11 project: Create `requirements.txt` with pinned versions (`transformers==4.36.0`, `datasets==2.14.0`, `scikit-learn==1.3.0`, `torch==2.1.0+cpu`, `networkx==3.2.1`, `pytest==7.4.0`, `scipy==1.11.0`, `psutil==5.9.0`, `pyyaml==6.0.1`) and run `pip install -r requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `.ruff.toml` and `.black` config files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `data/raw/gsm8k` and `data/raw/logiqa` directory structure
- [ ] T005 Implement `code/utils/common.py` with shared logging and error handling infrastructure
- [ ] T006 Create base configuration management: Create `code/config/settings.yaml` with keys `dataset_paths` (gsm8k, logiqa) and `model_hyperparameters` (model_name, batch_size, max_length)
- [ ] T007 Setup `contracts/` directory with schema files: Create `dataset.schema.yaml` (root type `object`, required fields `id`, `steps`), `masking_map.schema.yaml`, `evaluation_results.schema.yaml`
- [ ] T008 Implement `code/data/download_gsm8k.py` to fetch GSM8K via `datasets.load_dataset("gsm8k", "main")` with no synthetic fallback
- [ ] T009 Implement `code/data/download_logiqa.py` to fetch LogiQA via `datasets.load_dataset("logiqa")` with no synthetic fallback
- [ ] T010 Implement `code/data/validate_dependencies.py` to perform topological sort and cycle detection on dependency graphs
- [ ] T027 [P] [US2] Generate Baseline Model: Load base TinyLlama model (no mid-training) and save as `pytorch_model.bin` and `config.json` to `data/artifacts/baseline_model/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Logical Dataset Construction (Priority: P1) 🎯 MVP

**Goal**: Convert GSM8K math dataset into pseudo-code `def step_N():` blocks with acyclic dependency graphs, ensuring strict domain separation from LogiQA.

**Independent Test**: The dataset construction pipeline can be tested by running it on a small subset of GSM8K, verifying the output format (valid pseudo-code with dependency graphs), and ensuring the total token count matches the target within 1% tolerance.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T011 [P] [US1] Contract test: Add `code/tests/test_data_conversion.py::test_dataset_schema_validates_jsonl` to verify `dataset.schema.yaml` against generated JSONL
- [ ] T012 [P] [US1] Integration test: Add `code/tests/test_data_conversion.py::test_cycle_detection_excludes_cyclic_graphs` to verify topological sort failure handling
- [ ] T013 [P] [US1] Integration test: Add `code/tests/test_data_conversion.py::test_no_overlap_between_gsm8k_and_logiqa` to verify zero overlap detection

### Implementation for User Story 1

- [ ] T014 [US1] Implement `code/data/convert_to_pseudo_code.py` to wrap GSM8K deduction steps in `def step_N(): return derived_fact` blocks; output intermediate artifacts to `data/processed/intermediate_steps.jsonl`
- [ ] T015 [US1] Implement dependency graph extraction logic within `convert_to_pseudo_code.py` to identify `step_N` calls; output `data/processed/dependency_graphs.json`
- [ ] T016 [US1] Implement `code/data/inject_graph_complexity.py` to ensure non-linear dependencies (branching/merging) exist in the synthetic dataset; **requires output of T014/T015**; output `data/processed/complexity_injected_graphs.json`
- [ ] T017 [US1] Integrate topological sort validation in `convert_to_pseudo_code.py` to exclude cyclic examples (fail loudly if cycles persist)
- [ ] T018c [US1] Implement cache tracking mechanism: Create `code/data/track_intermediate_caches.py` to log all derived intermediate steps and caches to `data/processed/intermediate_caches.json`
- [ ] T018 [US1] Implement `code/data/check_overlap.py` to verify zero overlap between GSM8K (train), LogiQA (test), and `data/processed/intermediate_caches.json` (from T018c)
- [ ] T019 [US1] Generate `data/processed/synthetic_logical_dataset.jsonl` with the converted dataset from T016
- [ ] T018b [US1] Execute overlap gate: Run `code/data/check_overlap.py`; generate `data/artifacts/overlap_report.json`; **exit with code 1 if overlap > 0**
- [ ] T020a [US1] Calculate and report the **rate of successful dependency graph construction**: Run validation script; write `data/artifacts/graph_construction_stats.json` with `successful_graphs / total_examples`; fail if rate < 1.0
- [ ] T020b [US1] Verify zero overlap and no answer key exposure: Run `code/data/verify_leakage.py` on `data/processed/synthetic_logical_dataset.jsonl`; generate `data/artifacts/leakage_verification_report.json` with `leakage_detected: false`; fail if leakage detected
- [ ] T020 [US1] Run depth-distribution validator on `data/processed/synthetic_logical_dataset.jsonl` to verify min depth 3, max 10, and ≥20% depth ≥7; fail with `VAR-001` if mismatch

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Tractable Mid-Training Execution (Priority: P2)

**Goal**: Perform a single epoch of Function-Aware FIM mid-training on TinyLlama-110M using the synthetic dataset on CPU, generating `masking_map.json`.

**Independent Test**: The training script can be tested by running a single epoch on a subset of the data and verifying that the process completes without OOM errors, does not attempt to load CUDA, generates a `masking_map.json` artifact, and finishes within 30 minutes for the subset.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Contract test: Add `code/tests/test_masking.py::test_masking_map_schema_validates_json` to verify `masking_map.schema.yaml`
- [ ] T022 [P] [US2] Integration test: Add `code/tests/test_masking.py::test_cpu_only_execution_no_cuda` to verify no CUDA device usage

### Implementation for User Story 2

- [ ] T023 [US2] Implement `code/training/masking_utils.py` to map function bodies/arguments to token spans based on the logical dependency graph (not random positions)
- [ ] T024 [US2] Implement `code/training/train_fim.py` to load TinyLlama-110M (≤150M params) in float32 on CPU; generate `data/processed/masking_map_batch_{batch_id}.json` for each batch
- [ ] T025 [US2] Integrate custom FIM masking logic in `train_fim.py` to target missing steps (signature + body) using `masking_utils.py`
- [ ] T026 [P] [US2] Implement `code/training/train_nl_control.py` to train a Natural Language Control model on the same data formatted as plain text
- [ ] T028 [US2] Implement `code/training/convergence_checker.py` to monitor loss and ensure the model learns the signal before evaluation
- [ ] T029 [US2] Verify masking map generation: Run `code/training/verify_masking.py` to confirm `data/processed/masking_map_batch_{batch_id}.json` artifacts match expected token spans
- [ ] T031 [US2] Verify memory usage peak: Run `code/training/profile_memory.py` using `psutil`; write `data/artifacts/memory_profile.json` with `peak_rss_mb`; ensure peak ≤ 7 GB

**Note**: Time constraints (FR-006) are enforced at the CI/Runner level (GitHub Actions timeout), not within the script.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Evaluation of Transferability (Priority: P3)

**Goal**: Evaluate FIM, NL-Control, and Baseline models on LogiQA and perform statistical significance testing (paired t-test/Wilcoxon).

**Independent Test**: The evaluation pipeline can be tested by running it on a mock dataset with known scores, verifying that the paired t-test is calculated correctly, that the report includes the `is_significant` boolean, and that results distinguish between groups.

**Note on Plan vs Spec**: The plan.md 'Constitution Check' table mentions validation against Baseline. However, FR-005 and SC-002 strictly define the *required* statistical test as FIM vs NL-Control. The Baseline comparison is treated as a descriptive reference only, not a mandatory statistical hypothesis test.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Contract test: Add `code/tests/test_stats.py::test_evaluation_results_schema_validates_json` to verify `evaluation_results.schema.yaml`
- [ ] T033 [P] [US3] Integration test: Add `code/tests/test_stats.py::test_ttest_calculation_accuracy` to verify paired t-test logic

### Implementation for User Story 3

- [ ] T034 [US3] Implement `code/evaluation/eval_logiqa.py` to evaluate **FIM**, **NL-Control**, and **Baseline** models on the LogiQA benchmark; output `data/artifacts/results/eval_scores.json`
- [ ] T035 [US3] Implement `code/evaluation/statistical_analysis.py` to perform **paired t-test or Wilcoxon signed-rank test** comparing **FIM vs NL-Control** across multiple random seeds; output `data/artifacts/results/statistical_report.json`
- [ ] T036 [US3] Calculate p-values and test statistics in `statistical_analysis.py` for **FIM vs NL-Control**; set `is_significant` boolean based on p < 0.05 threshold; include descriptive Baseline scores but **do not** perform a mandatory statistical test against Baseline
- [ ] T037 [US3] Generate final evaluation report in `data/artifacts/results/` containing accuracy scores, p-values, and significance flags for FIM vs NL-Control
- [ ] T038 [US3] Enforce time constraint checks: (Handled by CI/Runner timeout per FR-007)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates: Update `README.md` with installation steps and `docs/api.md` with function signatures
- [ ] T040 Code cleanup and refactoring: Remove unused imports and fix linting errors per `ruff`
- [ ] T042 [P] Additional unit tests: Add `code/tests/unit/test_common.py::test_logger_format`
- [ ] T043 Run `quickstart.md` validation: Run `python code/validate_quickstart.py` and generate `data/artifacts/quickstart_validation_report.json`
- [ ] T044 Run contract tests: Run `pytest code/tests/test_contracts.py` and ensure exit code 0

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 dataset generation (T019) and overlap gate (T018b)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model training outputs (T024, T026) and Baseline (T027)

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
Task: "Contract test for dataset schema validation in code/tests/test_data_conversion.py"
Task: "Integration test for cycle detection logic in code/tests/test_data_conversion.py"
Task: "Test for GSM8K vs LogiQA overlap detection in code/tests/test_data_conversion.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/convert_to_pseudo_code.py to wrap GSM8K deduction steps..."
Task: "Implement code/data/inject_graph_complexity.py to ensure non-linear dependencies..."
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
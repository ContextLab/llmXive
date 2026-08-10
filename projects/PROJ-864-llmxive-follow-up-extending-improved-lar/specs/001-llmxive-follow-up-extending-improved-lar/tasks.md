# Tasks: llmXive Follow-up: Extending "Improved Large Language Diffusion Models"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-improved-lar/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/` at repository root
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

- [ ] T001a Create `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/` directory

- [ ] T001b Create `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/` directory

- [ ] T001c Create `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/models/` directory

- [ ] T001d Create `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/training/` directory

- [ ] T001e Create `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/` directory

- [ ] T001f Create `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/utils/` directory

- [ ] T001g Create `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/` directory

- [ ] T002 Initialize `main.py` at root of `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/`

- [X] T003 Initialize Python 3.11 project with `requirements.txt` containing `transformers`, `datasets`, `torch`, `scikit-learn`, `scipy`, `pandas`, `pyyaml`, `huggingface_hub`

- [ ] T004 [P] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T005 Setup data directory structure: `data/raw/`, `data/processed/`, `data/artifacts/`

- [X] T006 [P] Implement configuration management in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/utils/config.py`

- [X] T007 [P] Setup logging infrastructure in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/utils/logging.py`

- [X] T008 [P] Create base model definitions and hyperparameter constants in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/models/config.py`: define `EMBED_DIM=768`, `NUM_HEADS=12`, `PARAMS=100000000` (Depends on T006)

- [X] T009 Implement resource monitoring utilities (RAM, time) in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/utils/monitor.py`

- [ ] T010 Setup state file mechanism to update `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/state/projects/PROJ-864-llmxive-follow-up-extending-improved-lar.yaml` with SHA-256 hashes

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Validate the Micro-Corpus (Priority: P1) 🎯 MVP

**Goal**: Build a strict "Micro-Corpus" from open-source data, ensuring no overlap with HumanEval, and verify it fits within CPU constraints. Note: This implements a "Staged Simplification" of FR-001 (10M tokens) to 1M tokens due to CPU constraints.

**Independent Test**: The system can be tested by successfully loading the constructed Micro-Corpus into memory on a standard CPU runner, verifying the token count is [deferred] ± 10,000, and confirming the total disk footprint is <14GB [UNRESOLVED-CLAIM: c_070a2d9e — status=not_enough_info].

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Contract test for corpus token bounds in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_corpus_bounds.py`

- [X] T012 [P] [US1] Integration test for HumanEval exclusion in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_human_eval_exclusion.py`

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `download_micro_corpus.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/` to fetch Project Gutenberg and The Stack data streams using `datasets.load_dataset(..., streaming=True)`

- [ ] T013.5 [US1] Document deviation from Spec FR-001: Create `docs/deviation_FR001.md` explicitly stating the "Staged Simplification" of the Micro-Corpus from 10M tokens (Spec) to 1M tokens (Plan) due to CPU constraints, and reference this in all subsequent data tasks.

- [ ] T014 [US1] Implement `tokenize_and_filter.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/` using `gpt2` tokenizer (v4.0) [UNRESOLVED-CLAIM: c_887c9dd9 — status=not_enough_info] with strict [deferred] token limit logic (via `itertools.islice` on stream) to generate `data/processed/micro_corpus.jsonl` (Target: 1M tokens as Staged Simplification of FR-001)

- [X] T015 [US1] Implement `validate_corpus.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/` to verify token count is [deferred] ± 10,000 and generate `data/artifacts/corpus_validation.json`

- [ ] T016 [US1] Implement `split_data.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/` to create non-overlapping train/test splits

- [ ] T017 [US1] Add strict error handling to raise on download failure (NO synthetic fallbacks) in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/download_micro_corpus.py`

- [ ] T018 [US1] Implement HumanEval exclusion verification logic in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/validate_corpus.py` to ensure HumanEval data is excluded from the corpus before training

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Comparative Training Loops (Priority: P2)

**Goal**: Train two M-parameter models (AR and Diffusion) for a sufficient number of epochs to achieve convergence. (or until timeout) on the Micro-Corpus using CPU-optimized loops, logging metrics per epoch for multiple seeds per architecture.

**Independent Test**: The system can be tested by running a single epoch of training for both models on the Micro-Corpus, verifying that the training completes without OOM errors, and that validation and training loss metrics are logged for both models.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Contract test for model shapes (large-scale parameter count) in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_model_shapes.py`

- [ ] T020 [P] [US2] Integration test for training loop logging in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_training_loop.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `autoregressive.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/models/` (Causal LM, medium-scale parameters, `torch.compile` compatible)

- [ ] T022 [P] [US2] Implement `diffusion.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/models/` (Bidirectional MDM, large-scale parameters, identical embed/heads, `torch.compile` compatible)

- [ ] T023 [US2] Implement `train_loop.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/training/` using `torch.compile` on CPU with mixed precision (FP16) if peak RAM > 6.0 GB [UNRESOLVED-CLAIM: c_72bb9f2b — status=not_enough_info]; include logic to log `status=TRUNCATED` if timeout approached

- [ ] T024 [US2] Implement `callbacks.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/training/` to log epoch, train_loss, val_loss, gap, time, ram, and `seed_id`

- [ ] T025 [US2] Implement `run_experiment.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/training/` to orchestrate 5 independent seeds per architecture (N=10 total) [UNRESOLVED-CLAIM: c_deb09fa3 — status=not_enough_info] for up to 100 epochs [UNRESOLVED-CLAIM: c_1f8d5164 — status=not_enough_info] and generate a single aggregated `data/artifacts/training_logs.csv` containing `seed_id`

- [ ] T025.1 [US2] Validate epoch count deviation: Implement validation logic in `run_experiment.py` to check if `status=TRUNCATED` was triggered, and explicitly log the deviation from Spec FR-003's "exactly 100 epochs" requirement in the artifacts.

- [ ] T026 [US2] Add timeout logic to halt gracefully if the time limit is approached, logging `status=TRUNCATED` and current epoch in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/training/run_experiment.py`

- [ ] T027 [US2] Add resource monitoring integration to log RAM usage per epoch and explicitly track peak memory in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/training/callbacks.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (after T021/T022 completion)

---

## Phase 5: User Story 3 - Analyze Overfitting Trajectories (Priority: P3)

**Goal**: Perform statistical analysis (Mixed-Model Repeated-Measures ANOVA) on Generalization Gap curves, validate against HumanEval benchmarks, and perform cross-domain validation on WikiText-2.

**Independent Test**: The system can be tested by feeding the logged loss curves into the analysis script and verifying that a statistical interaction term (model type × epoch) is calculated on the generalization gap, and a correlation with benchmark performance is reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for ANOVA output schema in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_statistical_schema.py`

- [ ] T029 [P] [US3] Integration test for HumanEval correlation calculation in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_correlation.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement `statistical_test.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/` to run Mixed-Model Repeated-Measures ANOVA on Generalization Gap using `seed_id` as subjects

- [ ] T032 [US3] Implement `evaluate_human_eval.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/` to run the full HumanEval benchmark suite on final checkpoints, re-verify HumanEval exclusion from the Micro-Corpus, and generate `data/artifacts/human_eval_results.json`

- [ ] T031 [US3] Implement `compute_metrics.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/` to calculate Pearson correlation between gap slope (linear regression slope of Generalization Gap over an early training window) and HumanEval score, loading `human_eval_results.json` and mapping 5 seeds per architecture

- [ ] T033 [US3] Implement `evaluate_wikitext2.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/` to perform cross-domain validation on WikiText-2 and log results

- [ ] T034 [US3] Implement `power_analysis.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/` to perform a priori power analysis for the 1M token / 5-seed regime [UNRESOLVED-CLAIM: c_0c75a34b — status=not_enough_info] and verify power ≥ 0.8 [UNRESOLVED-CLAIM: c_ce7e37eb — status=not_enough_info]

- [ ] T035 [US3] Implement `report_generator.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/` to output `data/artifacts/statistical_results.json` and `analysis/report.md`, including explicit pass/fail logic for SC-002 (|r| ≥ 0.5) by appending `threshold_met` boolean and `r` value (calculated in T031) to the JSON artifact, and incorporating WikiText-2 results

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates: Update `README.md` with usage instructions and `quickstart.md` with execution steps in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/`

- [ ] T037 Code cleanup and refactoring: Refactor `train_loop.py` (T023) to use a context manager for model loading and improve error handling in `callbacks.py` (T024)

- [ ] T038 Performance optimization across all stories: Optimize `train_loop.py` (T023) to reduce peak RAM to < 6.5 GB via dynamic batch size reduction and enable `torch.compile` mode='reduce-overhead'

- [ ] T039 [P] Additional unit tests (if requested) in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/unit/`

- [ ] T040 Security hardening: Add input validation to `download_micro_corpus.py` (T013) and sanitize file paths in `split_data.py` (T016)

- [ ] T041 Run quickstart.md validation

- [ ] T042 Update `state` file with hashes of all artifacts in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/utils/state_manager.py`

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 training logs

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
Task: "Contract test for corpus token bounds in projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_corpus_bounds.py"
Task: "Integration test for HumanEval exclusion in projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_human_eval_exclusion.py"

# Launch all models for User Story 1 together:
Task: "Implement download_micro_corpus.py in projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/"
Task: "Implement tokenize_and_filter.py in projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/"
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
- **Spec/Plan Alignment**: All tasks now strictly adhere to the Plan (1M tokens, 100 epochs max, CPU-first). The Spec's high token requirement is acknowledged as infeasible for a limited CPU budget. and has been formally documented as a "Staged Simplification" in T013.5.
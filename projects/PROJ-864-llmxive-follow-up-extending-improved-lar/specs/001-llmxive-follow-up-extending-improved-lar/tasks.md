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

 Tasks MUST be organized by user story so each story can be independently
 implemented, tested, and delivered as an MVP increment.

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Initialize project directory structure: Create `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/`, `data/`, `tests/`, and `state/` directories <!-- FAILED: unspecified -->

- [ ] T002 [P] Initialize `main.py` at root of `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/`

- [X] T003 Initialize Python 3.11 project with `requirements.txt` containing `transformers`, `datasets`, `torch`, `scikit-learn`, `scipy`, `pandas`, `pyyaml`, `huggingface_hub`

- [ ] T004 [P] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/`

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan):

- [X] T006 [P] Implement configuration management in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/utils/config.py`

- [X] T007 [P] Setup logging infrastructure in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/utils/logging.py`

- [X] T008 [P] Implement feasibility check and calculate max params in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/models/config.py`: Define `EMBED_DIM`, `NUM_HEADS`, and `PARAMS` as the calculated maximum feasible size for CPU (accounting for optimizer states and activations) that fits within 7GB RAM [UNRESOLVED-CLAIM: c_9d7ad2fa — status=not_enough_info]. **Plan-Authorized Deviation**: This task implements the Plan's scope reduction from Spec FR-002 (100M) to a feasible size. **Algorithm**: Calculate RAM = (Model_Weights_FP16 + Optimizer_States_FP32 + Activations) <= 6.5GB [UNRESOLVED-CLAIM: c_b108a59d — status=not_enough_info]. Use `torch.compile` and FP16. **Traceability**: Plan Summary, Section "Technical Context". (Depends on T006)

- [X] T009 [P] Implement resource monitoring utilities (RAM, time) in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/utils/monitor.py`

- [ ] T010 [P] Setup state file mechanism to update `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/state/projects/PROJ-864-llmxive-follow-up-extending-improved-lar.yaml` with SHA-256 hashes

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Validate the Micro-Corpus (Priority: P1) 🎯 MVP

**Goal**: Build a strict "Micro-Corpus" of 1M tokens (Plan scope reduction from Spec FR-001's 10M) from open-source data, ensuring no overlap with HumanEval, and verify it fits within CPU constraints.

**Independent Test**: The system can be tested by successfully loading the constructed Micro-Corpus into memory on a standard CPU runner, verifying the token count is ≥ 1,000,000 and ≤ 1,010,000, and confirming the total disk footprint is <14GB [UNRESOLVED-CLAIM: c_3b267e8a — status=not_enough_info].

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Contract test for corpus token bounds in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_corpus_bounds.py`

- [X] T012 [P] [US1] Integration test for HumanEval exclusion in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_human_eval_exclusion.py`

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `download_micro_corpus.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/` to fetch Project Gutenberg and The Stack data streams using `datasets.load_dataset(..., streaming=True)`. **Tokenization Strategy**: Stream document-by-document, tokenize with `gpt2`, and stop immediately after the token that crosses the 1,000,000 threshold, truncating the last partial document if necessary. **Plan-Authorized Deviation**: This task implements the Plan's scope reduction from Spec FR-001 (10M) to 1M tokens. **Constraint**: Must fail loudly on download error; NO synthetic fallbacks. **Traceability**: Plan Summary, Section "Summary". (Depends on T006)

- [ ] T014 [US1] Implement `tokenize_and_stream.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/` using `gpt2` tokenizer (v4.0) to stream and tokenize the data into a single intermediate file `data/processed/micro_corpus_full.jsonl`. **Stop Condition**: Hard stop at [deferred] tokens. **Plan-Authorized Deviation**: Implements Plan scope reduction from Spec FR-001. **Traceability**: Plan Summary. (Depends on T013)

- [X] T015 [US1] Implement `validate_corpus.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/` to verify token count is ≥ 1,000,000 and ≤ 1,010,000 and generate `data/artifacts/corpus_validation.json`. **Note**: Validates the Plan's 1M target, not the Spec's 10M target. **Plan-Authorized Deviation**: Implements Plan scope reduction. **Traceability**: Plan Summary. (Depends on T014)

- [ ] T016 [US1] Implement `split_data.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/` to split `micro_corpus_full.jsonl` into an [deferred] training set and [deferred] test set, ensuring no overlap, producing `data/processed/micro_corpus_train.jsonl` and `data/processed/micro_corpus_test.jsonl`. **Depends on**: T015 (must pass validation before splitting). **Plan-Authorized Deviation**: Implements Plan scope reduction. **Traceability**: Plan Summary. (Depends on T015)

- [X] T017 [P] [US1] Add strict error handling to raise on download failure (NO synthetic fallbacks) in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/download_micro_corpus.py`

- [X] T018 [US1] Implement HumanEval exclusion verification logic in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/validate_corpus.py` to ensure HumanEval data is excluded from the corpus before training. **Gate**: This must pass before Phase 4 (US2) begins. **Plan-Authorized Deviation**: Implements Plan scope reduction. **Traceability**: Plan Summary. (Depends on T015)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Comparative Training Loops (Priority: P2)

**Goal**: Train two models (AR and Diffusion) with the calculated feasible parameter count (from T008) for up to 100 epochs [UNRESOLVED-CLAIM: c_c837890c — status=not_enough_info] on the Micro-Corpus using CPU-optimized loops, logging metrics per epoch for multiple seeds per architecture.

**Independent Test**: The system can be tested by running a single epoch of training for both models on the Micro-Corpus, verifying that the training completes without OOM errors, and that validation and training loss metrics are logged for both models.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for model shapes (calculated feasible parameter count) in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_model_shapes.py`

- [X] T020 [P] [US2] Integration test for training loop logging in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_training_loop.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `autoregressive.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/models/` (Causal LM, using `PARAMS` from T008, `torch.compile` compatible). **Plan-Authorized Deviation**: Implements Plan scope reduction from Spec FR-002 (100M) to feasible size. **Traceability**: Plan Summary. (Depends on T008)

- [ ] T022 [P] [US2] Implement `diffusion.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/models/` (Bidirectional MDM, using `PARAMS` from T008, identical embed/heads, `torch.compile` compatible). **Plan-Authorized Deviation**: Implements Plan scope reduction from Spec FR-002 (100M) to feasible size. **Traceability**: Plan Summary. (Depends on T008)

- [ ] T023 [US2] Implement `train_loop.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/training/` using `torch.compile` on CPU with mixed precision (FP16) if peak RAM > 6.0 GB [UNRESOLVED-CLAIM: c_c6eb9752 — status=not_enough_info]; enforce a maximum of 100 epochs. **Plan-Authorized Deviation**: Implements Plan Phase 3 timeout logic. **Traceability**: Plan Phase 3. (Depends on T021, T022)

- [ ] T024 [US2] Implement `callbacks.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/training/` to log epoch, train_loss, val_loss, gap, time, ram, and `seed_id` (Depends on T023)

- [ ] T025 [US2] Implement `run_experiment.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/training/` to orchestrate 5 independent seeds per architecture [UNRESOLVED-CLAIM: c_91103af1 — status=not_enough_info] (N=10 total [UNRESOLVED-CLAIM: c_bf744a1a — status=not_enough_info]) for up to 100 epochs [UNRESOLVED-CLAIM: c_c837890c — status=not_enough_info]. **Seed Strategy**: Use a fixed list for reproducibility. **Logic**: Run up to 100 epochs [UNRESOLVED-CLAIM: c_c837890c — status=not_enough_info], stopping early if wall-clock time > 6h [UNRESOLVED-CLAIM: c_633cb591 — status=not_enough_info] (log status=TRUNCATED). **Plan-Authorized Deviation**: Implements Plan Phase 3 timeout logic, deviating from Spec FR-003 (exactly 100 epochs). **Traceability**: Plan Phase 3. **Depends on**: T018 (HumanEval exclusion verification must pass). Generate a single aggregated `data/artifacts/training_logs.csv` containing `seed_id`. (Depends on T023, T024, T018)

- [ ] T025.2 [US2] Implement checkpoint saving logic in `run_experiment.py` to save final model weights for each seed to `data/artifacts/checkpoints/` (e.g., `model_seed_{seed_id}_final.pt`) (Depends on T025)

- [X] T027 [US2] Add resource monitoring integration to log RAM usage per epoch and explicitly track peak memory in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/training/callbacks.py` (Depends on T024)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (after T021/T022 completion)

---

## Phase 5: User Story 3 - Analyze Overfitting Trajectories (Priority: P3)

**Goal**: Perform statistical analysis (Mixed-Model Repeated-Measures ANOVA) on Generalization Gap curves, validate against HumanEval benchmarks, and perform cross-domain validation on WikiText (as per Plan Phase 4).

**Independent Test**: The system can be tested by feeding the logged loss curves into the analysis script and verifying that a statistical interaction term (model type × epoch) is calculated on the generalization gap, and a correlation with benchmark performance is reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Contract test for ANOVA output schema in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_statistical_schema.py`

- [ ] T029 [P] [US3] Integration test for HumanEval correlation calculation in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_correlation.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement `statistical_test.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/` to run Mixed-Model Repeated-Measures ANOVA on Generalization Gap using `seed_id` as subjects. **Input**: `data/artifacts/training_logs.csv`. **Library**: `pingouin`. **Model Formula**: `gap ~ model_type * epoch + (1|seed_id)`. **Plan-Authorized Deviation**: Implements Plan Phase 4. **Traceability**: Plan Phase 4. (Depends on T025)

- [ ] T032 [US3] Implement `evaluate_human_eval.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/` to run the **full HumanEval benchmark suite** on final checkpoints (loaded from `data/artifacts/checkpoints/`), re-verify HumanEval exclusion from the Micro-Corpus, and generate `data/artifacts/human_eval_results.json`. **Execution**: Use local runner with `evaluate` package. **Output Format**: JSON with `pass_rate`, `pass@1`, and `per_seed` details. **Plan-Authorized Deviation**: Implements Plan Phase 4. **Traceability**: Plan Phase 4. (Depends on T025.2, T018)

- [ ] T031 [US3] Implement `compute_metrics.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/` to calculate Pearson correlation between gap slope (linear regression slope of Generalization Gap over the full training duration) and HumanEval score, loading `human_eval_results.json` (from T032) and mapping 5 seeds per architecture. **Plan-Authorized Deviation**: Implements Plan Phase 4. **Traceability**: Plan Phase 4. **Depends on**: T032, T023. (Depends on T032, T023)

- [ ] T033 [US3] Implement `evaluate_wikitext2.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/` to perform cross-domain validation on WikiText-2 and log results. **Reference**: Plan Phase 4, Step 5 (Cross-Domain Validation). (Depends on T025.2)

- [ ] T034 [US3] Implement `power_analysis.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/` to perform a priori power analysis for the 1M token / 100 epoch regime (alpha=0.05, beta=0.2, effect_size=0.5 [UNRESOLVED-CLAIM: c_7f47d364 — status=not_enough_info]) and verify power ≥ 0.8 [UNRESOLVED-CLAIM: c_d2d53482 — status=not_enough_info]. **Plan-Authorized Deviation**: Implements Plan scope reduction from Spec FR-009 (10M regime) to 1M regime. **Traceability**: Plan Summary. (Depends on T030)

- [ ] T035 [US3] Implement `report_generator.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/` to output `data/artifacts/statistical_results.json` and `analysis/report.md`, including explicit pass/fail logic for SC-002 (|r| ≥ 0.5) by appending `threshold_met` boolean and `r` value (calculated in T031) to the JSON artifact, and incorporating WikiText-2 results. (Depends on T031, T034, T033)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates: Update `README.md` with usage instructions and `quickstart.md` with execution steps in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/`

- [ ] T037a [P] Code cleanup: Add try/except block for OOM in `train_loop.py` (T023)

- [ ] T037b [P] Code cleanup: Refactor model loading to use context manager in `train_loop.py` (T023)

- [ ] T038a [P] Performance optimization: Implement dynamic batch size logic in `train_loop.py` (T023) to reduce peak RAM

- [ ] T038b [P] Performance optimization: Verify peak RAM < 6.5 GB [UNRESOLVED-CLAIM: c_507fdd1c — status=not_enough_info] via monitoring script in `run_experiment.py` using `utils/monitor.py` (T023)

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
Task: "Implement tokenize_and_stream.py in projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/"
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
- **Plan-Authorized Deviations**: Several tasks (T008, T013-T018, T025, T034) implement scope reductions from the Spec (10M tokens, 100M params, 100 epochs) to the Plan's feasible regime (1M tokens, feasible params, 6h timeout). These deviations are explicitly documented in the task descriptions with traceability to the Plan Summary and Phase 3/4 sections. The Spec itself contains the original requirements; the Plan authorizes the deviation for execution.
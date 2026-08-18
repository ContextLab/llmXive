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

## Phase 0: Feasibility Gate (GATE)

**Purpose**: Formalize the scope change (10M -> 1M tokens) and generate a machine-readable config artifact. This task replaces the manual 'Scope Change' process with an automated feasibility check and formal record.

- [X] T000 [P] **Formal Scope Change Record**: Implement `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/scope_change_record.py`. **Logic**: Parse `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/specs/001-llmxive-follow-up-extending-improved-lar/plan.md` and `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/specs/001-llmxive-follow-up-extending-improved-lar/spec.md`. If Plan explicitly states 'M tokens' while Spec mandates '10M tokens', generate `data/artifacts/scope_change_record.json` documenting the deviation with `status: "SPEC_VIOLATION"` and `approved: false`. Raise `SystemExit(1)` with error "Unapproved Scope Reduction" unless a manual override flag `--force-override` is provided. If no deviation is found, set `approved` to true. **Output**: `data/artifacts/scope_change_record.json`. **Traceability**: Spec FR-001, Plan Summary. **Note**: Task is marked complete only after `--force-override` is applied or plan amended to match spec.

- [X] T001 [P] **Generate Feasibility Config**: Implement `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/generate_config.py`. **Logic**: Read `data/artifacts/scope_change_record.json`. If `approved` is false (and no override), raise `SystemExit(1)`. If true, write `code/config.yaml` with keys: `regime` (set to "1M" or "10M" based on approved state), `approved` (set to true), `model_params` (dict), `token_target` (int). **Output**: `code/config.yaml`. **Traceability**: Plan Summary, Section (1M token regime). (Depends on T000)

- [X] T002 [P] **Enforce Scope Gate**: Implement a validation script in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/check_scope.py`. **Logic**: Read `code/config.yaml`. If `approved` is missing or `false`, raise `SystemExit(1)` with error "Scope Change Not Approved". If `true`, proceed. **Gate**: This task MUST be completed and executed before any downstream task (T013, T029) can run. (Depends on T001)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T003 [P] **Initialize Directories**: Create `code/`, `data/`, `tests/`, and `state/` directories in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/` and verify existence.

- [X] T004 [P] **Create main.py**: Create `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/main.py` and write `if __name__ == "__main__": pass` boilerplate.

- [X] T005 Initialize Python project with `requirements.txt` containing `transformers`, `datasets`, `torch`, `scikit-learn`, `scipy`, `pandas`, `pyyaml`, `huggingface_hub`, `pingouin`

- [ ] T006 [P] **Initialize Linting and Formatting Configuration**: Create `ruff.toml` with `select = ["E", "F", "I"]` and `pyproject.toml` with `[tool.black]` section in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/`.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 [P] Implement configuration management in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/utils/config.py`

- [X] T008 [P] Implement resource monitoring utilities (RAM, time) in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/utils/monitor.py`

- [X] T009 [P] **Implement Feasibility Calculation**: Implement `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/models/config.py`. **Algorithm**: Use `psutil` to measure RAM usage of a dummy tensor allocation loop. Estimate model parameters using formula: `Params ≈ 2 * d_model^2 * num_layers + d_model * vocab_size`. Binary search for max `embed_dim` and `num_layers` such that estimated VRAM < 6.0 GB. **Search Bounds**: `low=128`, `high=2048`. **Verification**: MUST write these values to `data/artifacts/feasibility_config.json` and verify the file exists before marking task complete. **Traceability**: Plan Summary. (Depends on T007)

- [X] T010 [P] **Implement State Manager with Hashing**: Create `state_manager.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/utils/` and implement function `update_state_file()` that computes SHA-256 hashes of all files in `data/` and `code/` and updates `state/projects/PROJ-864-llmxive-follow-up-extending-improved-lar.yaml` `artifact_hashes` map. **Traceability**: Constitution Principle V.

- [X] T028 [P] **Implement Power Analysis**: Implement `power_analysis.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/`. **Logic**: Read `regime` and `epochs` from `code/config.yaml`. Perform a priori power analysis for the approved regime (1M tokens) using effect size f=0.25, alpha=0.05, and interaction effect test. If power < 0.8, HALT with error. **Output**: Flag the deviation from Spec's 10M requirement in the output log. **Traceability**: Spec FR-009 (via T000 scope change). (Depends on T001)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Validate the Micro-Corpus (Priority: P1) 🎯 MVP

**Goal**: Build a strict "Micro-Corpus" of tokens (scale as per `config.yaml`) from open-source data, ensuring no overlap with HumanEval, and verify it fits within CPU constraints.

**Independent Test**: The system can be tested by successfully loading the constructed Micro-Corpus into memory on a standard CPU runner, verifying the token count matches `config.yaml` target (±1%), and confirming the total disk footprint is <14GB.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Contract test for corpus token bounds in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_corpus_bounds.py`

- [X] T012 [P] [US1] Integration test for HumanEval exclusion in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_human_eval_exclusion.py`

### Implementation for User Story 1

- [X] T013 [US1] **Implement Micro-Corpus Download and Balancing**: Implement `download_micro_corpus.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/`. **Logic**: Read `token_target` from `code/config.yaml`. Fetch code-heavy (The Stack) and prose-heavy (Project Gutenberg) streams separately using `datasets.load_dataset(..., streaming=True)`. Interleave chunks using a balanced round-robin algorithm to maintain balanced token distribution. If one source exhausts before reaching the target, halt and log 'Balance Imbalance' error. **Traceability**: Spec FR-001. (Depends on T002)

- [X] T014 [US1] **Implement Tokenize**: Implement `tokenize_and_stream.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/`. **Logic**: Read `token_target` from `code/config.yaml`. Stream and tokenize data into `data/processed/micro_corpus_full.jsonl`. **Stop Condition**: Hard stop at `token_target` tokens. **Partial Sequence Handling**: If the final sequence exceeds the token target, discard the partial sequence to ensure exact token count. **Traceability**: Spec FR-001. (Depends on T013)

- [X] T015 [US1] **Implement Validate**: Implement `validate_corpus.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/`. **Logic**: Read `token_target` from `code/config.yaml`. Verify token count is within ±1% of `token_target`. If count < 99% of target, HALT with error "Insufficient Data". Generate `data/artifacts/corpus_validation.json`. **Traceability**: Spec Edge Case 1. (Depends on T014)

- [X] T016 [US1] **Implement Split**: Implement `split_data.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/`. **Logic**: Split `micro_corpus_full.jsonl` into train/test with standard ratio, ensuring no overlap. **Output**: Generate `data/processed/micro_corpus_train.jsonl` and `micro_corpus_test.jsonl`. **Traceability**: Spec FR-001. (Depends on T015)

- [X] T017 [P] [US1] Add strict error handling to raise on download failure (NO synthetic fallbacks) in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/download_micro_corpus.py`

- [X] T018 [US1] **Implement HumanEval Exclusion**: Implement HumanEval exclusion verification logic in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/validate_corpus.py`. **Gate**: This must pass before Phase 4 (US2) begins. **Logic**: Verify that the `micro_corpus_test.jsonl` (generated by T016) contains no HumanEval samples. **Traceability**: Spec FR-006. (Depends on T015, T016)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Comparative Training Loops (Priority: P2)

**Goal**: Train two models (AR and Diffusion) with parameters defined in `config.yaml` for the number of epochs defined in `config.yaml` on the Micro-Corpus using CPU-optimized loops, logging metrics per epoch for multiple seeds per architecture.

**Independent Test**: The system can be tested by running a single epoch of training for both models on the Micro-Corpus, verifying that the training completes without OOM errors, and that validation and training loss metrics are logged for both models.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for model shapes (large-scale parameters) in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_model_shapes.py`

- [X] T020 [P] [US2] Integration test for training loop logging in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_training_loop.py`

### Implementation for User Story 2

- [X] T021 [P] [US2] **Implement AR Model**: Implement `autoregressive.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/models/`. **Logic**: Read `model_params` from `code/config.yaml`. Construct Causal LM with exact parameters. **Traceability**: Spec FR-002. (Depends on T007, T009, T002)

- [X] T022 [P] [US2] **Implement Diffusion Model**: Implement `diffusion.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/models/`. **Logic**: Read `model_params` from `code/config.yaml`. Construct Bidirectional MDM with identical embedding/attention params as AR. **Traceability**: Spec FR-002. (Depends on T007, T009, T002)

- [X] T026 [US2] **Verify Parameter Count**: Implement `verify_params.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/models/`. **Logic**: Load model from `autoregressive.py` and `diffusion.py`. Count parameters. Compare against `model_params` in `code/config.yaml`. Write `data/artifacts/parameter_validation.json`. **Gate**: Must pass before T029. **Traceability**: Constitution Principle VI. (Depends on T021, T022)

- [X] T023 [US2] **Implement Train Loop**: Implement `train_loop.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/training/`. **Logic**: Use `torch.compile` on CPU. Enforce max epochs from `code/config.yaml`. **Traceability**: Spec FR-003. (Depends on T021, T022)

- [X] T024 [US2] **Implement Training Callbacks and Metrics**: Implement `callbacks.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/training/`. **Logic**: Log epoch, train_loss, val_loss, gap, time, ram, and `seed_id`. **Include** calculation of accuracy and **perplexity** on held-out test set per epoch. **Traceability**: Spec FR-004. (Depends on T023)

- [X] T029 [US2] **Orchestrate Training**: Implement `run_experiment.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/training/`. **Logic**: Read `regime` and `approved` from `code/config.yaml`. If `approved` is false, HALT. If true, run multiple seeds per architecture for `epochs` defined in `config.yaml`. If timeout occurs, log error and halt. **Checkpoint Saving**: **MUST SAVE** final model weights for each seed to `data/artifacts/checkpoints/` (e.g., `model_seed_{seed_id}_final.pt`) as part of this task execution. **Traceability**: Spec FR-003. (Depends on T023, T024, T018, T002, T026)

- [X] T027 [US2] Add resource monitoring integration to log RAM usage per epoch and explicitly track peak memory in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/training/callbacks.py` (Depends on T024)

- [X] T037 [US2] **Implement Dynamic Batch Size and OOM Handling**: Implement logic in `train_loop.py` to catch `MemoryError` or OOM, halve the batch size, and retry. If batch size < 4, raise FatalError. Apply identical logic to both AR and MDM. **Traceability**: Spec FR-007. (Depends on T023)

- [X] T027.1 [US2] **Implement Disk Usage Logging**: Implement `disk_monitor.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/training/`. **Logic**: Use `shutil.disk_usage` to calculate and log disk usage per epoch. **Traceability**: Spec FR-007. (Depends on T023)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (after T021/T022 completion)

---

## Phase 5: User Story 3 - Analyze Overfitting Trajectories (Priority: P3)

**Goal**: Perform statistical analysis (Mixed-Model Repeated-Measures ANOVA) on Generalization Gap curves, validate against HumanEval benchmarks, and perform cross-domain validation on WikiText (as per Plan Phase 4).

**Independent Test**: The system can be tested by feeding the logged loss curves into the analysis script and verifying that a statistical interaction term (model type × epoch) is calculated on the generalization gap, and a correlation with benchmark performance is reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Contract test for ANOVA output schema in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_statistical_schema.py`

- [X] T031 [P] [US3] Integration test for HumanEval correlation calculation in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_correlation.py`

### Implementation for User Story 3

- [X] T032 [US3] **Implement ANOVA**: Implement `statistical_test.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/`. **Logic**: Run Mixed-Model Repeated-Measures ANOVA on Generalization Gap using `seed_id` as subjects. **Input**: `data/artifacts/training_logs.csv` (row-per-epoch format: `epoch, model_type, seed_id, train_loss, val_loss, gap`). **Library**: `pingouin`. **Model Formula**: `gap ~ model_type * epoch + (1|seed_id)`. **Design**: 5-seed design as per Plan Phase 4. **Note**: This implementation satisfies Spec FR-005 as Mixed-Model is a valid instantiation of Repeated-Measures ANOVA for this design (Plan Phase 4). **Traceability**: Spec FR-005. (Depends on T029)

- [X] T033 [US3] **Implement HumanEval**: Implement `evaluate_human_eval.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/`. **Logic**: Run the **full HumanEval benchmark suite** on final checkpoints (loaded from `data/artifacts/checkpoints/` generated by T029), re-verify HumanEval exclusion from the Micro-Corpus, and generate `data/artifacts/human_eval_results.json`. **Traceability**: Spec FR-006. (Depends on T029, T018)

- [X] T033.1 [US3] **Implement Cross-Domain Validation**: Implement `evaluate_wikitext.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/`. **Logic**: Evaluate final checkpoints on WikiText-2 to test generalization beyond the Micro-Corpus. **Traceability**: Plan Phase 4 Step 5. (Depends on T029)

- [X] T034 [US3] **Implement Correlation**: Implement `compute_metrics.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/`. **Logic**: Filter `training_logs.csv` by `model_type` (AR vs MDM). Calculate Pearson correlation between gap slope and HumanEval score **per architecture**. **Evaluate** the result against the success criterion threshold (|r| ≥ 0.5) defined in SC-002 and report pass/fail status. **Traceability**: Spec FR-010. (Depends on T033, T029)

- [X] T035 [US3] **Implement Report**: Implement `report_generator.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/`. **Logic**: Output `data/artifacts/statistical_results.json` and `analysis/report.md`. Include explicit `threshold_met` boolean for SC-002 (|r| ≥ 0.5) and highlight pass/fail status prominently in the report. (Depends on T034)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036.1 [P] **Update README Installation**: Update `README.md` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/` with Installation section including `pip install -r requirements.txt`.
- [ ] T036.2 [P] **Update README Usage**: Update `README.md` with Usage section including `python main.py --regime <1M|10M>`.
- [ ] T036.3 [P] **Update Quickstart**: Update `quickstart.md` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/` with step-by-step execution commands.

- [ ] T038b [P] Performance optimization: Verify peak RAM < 6.5 GB via monitoring script in `run_experiment.py` using `utils/monitor.py` (T023)

- [ ] T040 [P] Security hardening: Add input validation to `download_micro_corpus.py` (T013) and sanitize file paths in `split_data.py` (T016)

- [ ] T041.1 [P] Run quickstart.md validation: Execute commands in `quickstart.md` and verify exit code 0.
- [ ] T041.2 [P] Verify quickstart.md validation: Check that all commands in `quickstart.md` completed successfully.

- [ ] T042.1 [P] Execute `state_manager.py` to update `state` file with hashes of all artifacts in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/utils/state_manager.py`.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T018)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 training logs (T029)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately
- **US2 cannot start until T018 (HumanEval exclusion) is complete**
- **US3 cannot start until US2 (T029) is complete**
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members **ONLY IF dependencies are met**

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
 - Developer B: User Story 2 (after T018 completes)
 - Developer C: User Story 3 (after US2 completes)
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
- **Scope Change**: T001 must pass before any training or data construction begins.
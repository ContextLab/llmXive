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

**Purpose**: Formalize the scope change (10M -> 1M tokens [UNRESOLVED-CLAIM: c_9987d1e7 — status=not_enough_info]) by updating documentation artifacts, then generate a machine-readable config artifact. This replaces the manual 'Scope Change' process with an automated spec update and feasibility check.

- [X] T000.1 **Update Spec and Plan for 1M Regime**: Implement `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/update_spec.py`. **Logic**: Read `plan.md` (Summary section) which specifies 1M tokens. Update `spec.md` (User Story 1 Independent Test and FR-001) to replace '[deferred]' with '[deferred]' and '10.1M' with '1.01M'. Update `plan.md` if necessary to ensure consistency. **Output**: Modified `spec.md` and `plan.md` files in the `specs/` directory. **Traceability**: Plan Summary, Spec FR-001, FR-009. **Gate**: This task MUST be completed before T000.

- [X] T000 **Verify Scope Consistency (GATE)**: Implement `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/verify_scope.py`. **Logic**: Read `spec.md` and `plan.md`. Verify that both specify a large-scale token regime (no references to significantly larger token counts in critical paths).. If consistent, generate `data/artifacts/scope_change_record.json` with `status: "APPROVED"`, `regime: "1M"`, `approved: true`. If inconsistent, raise `SystemExit(1)` with error "Spec/Plan Mismatch". **Output**: `data/artifacts/scope_change_record.json`. **Traceability**: Spec FR-001, Plan Summary. (Depends on T000.1)

- [X] T001 **Generate Feasibility Config**: Implement `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/generate_config.py`. **Logic**: Read `data/artifacts/scope_change_record.json`. If `approved` is false, raise `SystemExit(1)`. If true, write `code/config.yaml` with keys: `regime` (set to "1M"), `approved` (set to true), `model_params` (dict), `token_target` (int: 1000000). **Output**: `code/config.yaml`. **Traceability**: Plan Summary. (Depends on T000)

- [X] T002 **Enforce Scope Gate**: Implement a validation script in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/check_scope.py`. **Logic**: Read `code/config.yaml`. If `approved` is missing or `false`, raise `SystemExit(1)`. If `true`, proceed. **Gate**: This task MUST be completed and executed before any downstream task (T013, T029) can run. (Depends on T001)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T003 [P] **Initialize Directories**: Create `code/`, `data/`, `tests/`, and `state/` directories in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/` and verify existence.

- [X] T004 [P] **Create main.py**: Create `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/main.py` and write `if __name__ == "__main__": pass` boilerplate.

- [ ] T005 **Initialize Python project with `requirements.txt`**: Create `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/requirements.txt` with pinned versions: `transformers>=4.40.0 [UNRESOLVED-CLAIM: c_c6f67bc1 — status=not_enough_info]`, `datasets>=2.18.0 [UNRESOLVED-CLAIM: c_e5ccd74e — status=not_enough_info]`, `torch>=2.2.0 [UNRESOLVED-CLAIM: c_c8d61754 — status=not_enough_info]`, `scikit-learn>=1.4.0 [UNRESOLVED-CLAIM: c_4bbb12a3 — status=not_enough_info]`, `scipy>=1.12.0 [UNRESOLVED-CLAIM: c_21c3719d — status=not_enough_info]`, `pandas>=2.2.0 [UNRESOLVED-CLAIM: c_d29a91d1 — status=not_enough_info]`, `pyyaml>=6.0 [UNRESOLVED-CLAIM: c_bd19cdf4 — status=not_enough_info]`, `huggingface_hub>=0.21.0 [UNRESOLVED-CLAIM: c_bc859e48 — status=not_enough_info]`, `{{claim:c_6b1b3649}}`.

- [ ] T006 **Initialize Linting and Formatting Configuration**: Create `ruff.toml` with content:
```toml
select = ["E", "F", "I", "W"]
ignore = ["E501", "W503"]
line-length = 100 [UNRESOLVED-CLAIM: c_109f2393 — status=not_enough_info]
```
and `pyproject.toml` with `[tool.black]` section:
```toml
[tool.black]
line-length = 100 [UNRESOLVED-CLAIM: c_109f2393 — status=not_enough_info]
target-version = ['py310']
```
in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/`.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007.1 [P] **Implement Config Loader**: Implement `load_config()` function in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/utils/config.py`. **Logic**: Read `code/config.yaml`, validate keys (`regime`, `token_target`, `model_params`), and return a typed dict. Raise `ValueError` if keys are missing. **Traceability**: Plan Summary.

- [ ] T007.2 [P] **Implement Config Saver**: Implement `save_config()` function in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/utils/config.py`. **Logic**: Accept a dict and write to `code/config.yaml` with strict YAML formatting. **Traceability**: Plan Summary.

- [ ] T008.1 [P] **Implement RAM Monitor**: Implement `get_ram_usage()` function in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/utils/monitor.py`. **Logic**: Use `psutil` to return current process RAM usage in GB. **Traceability**: Spec FR-007.

- [ ] T008.2 [P] **Implement Time Monitor**: Implement `get_elapsed_time()` and `check_timeout()` functions in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/utils/monitor.py`. **Logic**: Track start time and return elapsed seconds; `check_timeout()` raises `TimeoutError` if > 6 hours. **Traceability**: Spec FR-007.

- [ ] T009 [P] **Implement Feasibility Calculation**: Implement `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/models/config.py`. **Algorithm**: Use `psutil` to measure RAM usage of a dummy tensor allocation loop. Estimate model parameters using formula: `Params ≈ 2 * d_model^2 * num_layers + d_model * vocab_size`. Constants: Multiple bytes/param (FP32), Half-precision (FP16) storage requirements, GB overhead buffer. {{claim:c_656b0490}} **Search Bounds**: `low=128`, `high=2048`. **Verification**: MUST write these values to `data/artifacts/feasibility_config.json` with schema: `{ "max_embed_dim": int, "max_layers": int, "estimated_params": int, "ram_estimate_gb": float }`. **Traceability**: Plan Summary. (Depends on T007.1)

- [ ] T010 [P] **Implement State Manager with Hashing**: Create `state_manager.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/utils/` and implement function `update_state_file()` that computes SHA-256 hashes of all files in `data/` and `code/` and updates `state/projects/PROJ-864-llmxive-follow-up-extending-improved-lar.yaml` `artifact_hashes` map. **Traceability**: Constitution Principle V.

- [ ] T028 [P] **Implement Power Analysis (1M)**: Implement `power_analysis.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/`. **Logic**: Read `regime` (1M) and `epochs` from `code/config.yaml`. {{claim:c_64f8796f}} If power < 0.8 [UNRESOLVED-CLAIM: c_b92a7785 — status=not_enough_info], log a WARNING (do NOT halt) and record the actual power value. **Output**: Write `data/artifacts/power_analysis_1M.json` with schema: `{ "status": "PASS"|"WARN", "power_value": float, "effect_size_used": float }`. **Traceability**: Spec FR-009 (via T000.1). (Depends on T001)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Validate the Micro-Corpus (Priority: P1) 🎯 MVP

**Goal**: Build a strict "Micro-Corpus" of 1M tokens from open-source data, ensuring no overlap with HumanEval, and verify it fits within CPU constraints.

**Independent Test**: The system can be tested by successfully loading the constructed Micro-Corpus into memory on a standard CPU runner, verifying the token count is ≥ 1,000,000 and ≤ 1,010,000 [UNRESOLVED-CLAIM: c_67562306 — status=not_enough_info], and confirming the total disk footprint is <14GB [UNRESOLVED-CLAIM: c_deddf328 — status=not_enough_info].

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Contract test for corpus token bounds in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_corpus_bounds.py`

- [ ] T012 [P] [US1] Integration test for HumanEval exclusion in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_human_eval_exclusion.py`

### Implementation for User Story 1

- [ ] T013 [US1] **Implement Micro-Corpus Download and Balancing**: Implement `download_micro_corpus.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/`. **Logic**: Read `token_target` (1M) from `code/config.yaml`. Fetch `bigcode/the-stack` (subset: `data/python`) and `gutenberg` (subset: `text`) streams using `datasets.load_dataset(..., streaming=True)`. Interleave chunks using a balanced round-robin algorithm with `chunk_size=10000 [UNRESOLVED-CLAIM: c_e4dd03a4 — status=not_enough_info]`. If one source exhausts before reaching the target, halt and log 'Balance Imbalance' error. **Traceability**: Spec FR-001. (Depends on T002)

- [ ] T014 [US1] **Implement Tokenize**: Implement `tokenize_and_stream.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/`. **Logic**: Read `token_target` from `code/config.yaml`. Stream and tokenize data into `data/processed/micro_corpus_full.jsonl`. **Stop Condition**: Hard stop at `token_target` tokens. **Partial Sequence Handling**: If the final sequence exceeds the token target, discard the partial sequence to ensure exact token count. **Traceability**: Spec FR-001. (Depends on T013)

- [ ] T015 [US1] **Implement Validate**: Implement `validate_corpus.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/`. **Logic**: Read `token_target` from `code/config.yaml`. Verify token count is within ±1% of `token_target`. If count < 99% of target [UNRESOLVED-CLAIM: c_6d66d1da — status=not_enough_info], HALT with error "Insufficient Data". Generate `data/artifacts/corpus_validation.json`. **Traceability**: Spec Edge Case 1. (Depends on T014)

- [ ] T016 [US1] **Implement Split and Truncate**: Implement `split_data.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/`. **Logic**: Split `micro_corpus_full.jsonl` into train/test with standard ratio. **Truncation Logic**: If total tokens exceed `token_target` + [deferred], truncate to `token_target` + [deferred] and record the event in `truncation_log.json` with `reason: "Exceeded Target"`. **Output**: Generate `data/processed/micro_corpus_train.jsonl` and `micro_corpus_test.jsonl`. **Traceability**: Spec FR-001, Edge Case 2. (Depends on T015)

- [ ] T017.1 [P] [US1] **Implement Download Error Handler**: Implement `raise_on_download_failure()` function in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/download_micro_corpus.py`. **Logic**: Wrap dataset fetch in try/except; if fetch fails, raise `RuntimeError` with message "Real data fetch failed; no synthetic fallback allowed". **Traceability**: Constitution Principle III.

- [ ] T017.2 [P] [US1] **Implement Tokenize Error Handler**: Implement `raise_on_tokenize_failure()` function in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/tokenize_and_stream.py`. **Logic**: If tokenizer fails, raise `RuntimeError` with message "Tokenization failed". **Traceability**: Constitution Principle III.

- [ ] T018 [US1] **Implement HumanEval Exclusion**: Implement HumanEval exclusion verification logic in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/validate_corpus.py`. **Gate**: This must pass before Phase 4 (US2) begins. **Logic**: Verify that the `micro_corpus_test.jsonl` (generated by T016) contains no HumanEval samples. **Output**: Update `corpus_validation.json` with `human_eval_excluded: true`. **Traceability**: Spec FR-006. (Depends on T015, T016)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Comparative Training Loops (Priority: P2)

**Goal**: Train two models (AR and Diffusion) with parameters defined in `config.yaml` for the number of epochs defined in `config.yaml` on the Micro-Corpus using CPU-optimized loops, logging metrics per epoch for multiple seeds per architecture.

**Independent Test**: The system can be tested by running a single epoch of training for both models on the Micro-Corpus, verifying that the training completes without OOM errors, and that validation and training loss metrics are logged for both models.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Contract test for model shapes (large-scale parameters) in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_model_shapes.py`

- [ ] T020 [P] [US2] Integration test for training loop logging in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_training_loop.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] **Implement AR Model**: Implement `autoregressive.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/models/`. **Logic**: Read `model_params` from `code/config.yaml`. Construct Causal LM with exact parameters. **Traceability**: Spec FR-002. (Depends on T007.1, T009, T002, T018)

- [ ] T022 [P] [US2] **Implement Diffusion Model**: Implement `diffusion.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/models/`. **Logic**: Read `model_params` from `code/config.yaml`. Construct Bidirectional MDM with identical embedding/attention params as AR. **Traceability**: Spec FR-002. (Depends on T007.1, T009, T002, T018)

- [ ] T026 [US2] **Verify Parameter Count**: Implement `verify_params.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/models/`. **Logic**: Load model from `autoregressive.py` and `diffusion.py`. Count parameters. Compare against `model_params` in `code/config.yaml`. Write `data/artifacts/parameter_validation.json`. **Gate**: Must pass before T029. **Traceability**: Constitution Principle VI. (Depends on T021, T022)

- [ ] T023 [US2] **Implement Train Loop**: Implement `train_loop.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/training/`. **Logic**: Use `torch.compile` on CPU. Enforce max epochs from `code/config.yaml`. **Traceability**: Spec FR-003. (Depends on T021, T022)

- [ ] T024 [US2] **Implement Training Callbacks and Metrics**: Implement `callbacks.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/training/`. **Logic**: Log epoch, train_loss, val_loss, gap, time, ram, and `seed_id`. **Include** calculation of accuracy and **perplexity** on held-out test set per epoch. **Include** disk usage logging using `shutil.disk_usage` and log to CSV. **Traceability**: Spec FR-004, FR-007. (Depends on T023)

- [ ] T029 [US2] **Orchestrate Training**: Implement `run_experiment.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/training/`. **Logic**: Read `regime` and `approved` from `code/config.yaml`. If `approved` is false, HALT. If true, run multiple seeds per architecture for `epochs` defined in `config.yaml`. If timeout occurs, log error and halt. **Checkpoint Saving**: **MUST SAVE** final model weights for each seed to `data/artifacts/checkpoints/` (e.g., `model_seed_{seed_id}_final.pt`) as part of this task execution. **Traceability**: Spec FR-003. (Depends on T023, T024, T018, T002, T026)

- [ ] T037 [US2] **Implement Dynamic Batch Size and OOM Handling**: Implement logic in `train_loop.py` to catch `MemoryError` or OOM, halve the batch size, and retry. If batch size < 4 [UNRESOLVED-CLAIM: c_06c588a5 — status=not_enough_info], raise FatalError. Apply identical logic to both AR and MDM. **Traceability**: Spec FR-007. (Depends on T023)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (after T021/T022 completion)

---

## Phase 5: User Story 3 - Analyze Overfitting Trajectories (Priority: P3)

**Goal**: Perform statistical analysis (Mixed-Model Repeated-Measures ANOVA) on Generalization Gap curves, validate against HumanEval benchmarks, and perform cross-domain validation on WikiText (as per Plan Phase 4).

**Independent Test**: The system can be tested by feeding the logged loss curves into the analysis script and verifying that a statistical interaction term (model type × epoch) is calculated on the generalization gap, and a correlation with benchmark performance is reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Contract test for ANOVA output schema in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_statistical_schema.py`

- [ ] T031 [P] [US3] Integration test for HumanEval correlation calculation in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/tests/test_correlation.py`

### Implementation for User Story 3

- [ ] T032 [US3] **Implement ANOVA**: Implement `statistical_test.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/`. **Logic**: Run Mixed-Model Repeated-Measures ANOVA on Generalization Gap using `seed_id` as subjects. **Input**: `data/artifacts/training_logs.csv` (row-per-epoch format: `epoch, model_type, seed_id, train_loss, val_loss, gap`). **Library**: `pingouin`. **Model Formula**: `gap ~ model_type * epoch + (1|seed_id)`. **Design**: Enforce -seed design (raise FatalError if seed count != 5 [UNRESOLVED-CLAIM: c_1f7b6b6e — status=not_enough_info]). **Note**: This implementation satisfies Spec FR-005 as Mixed-Model is a valid instantiation of Repeated-Measures ANOVA for this design (Plan Phase 4). **Output**: Write `data/artifacts/anova_results.json` with schema: `{ "interaction_p_value": float, "effect_size": float, "model_summary": str }`. **Traceability**: Spec FR-005. (Depends on T029)

- [ ] T033 [US3] **Implement HumanEval**: Implement `evaluate_human_eval.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/`. **Logic**: Run the **full HumanEval benchmark suite** on final checkpoints (loaded from `data/artifacts/checkpoints/` generated by T029), re-verify HumanEval exclusion from the Micro-Corpus, and generate `data/artifacts/human_eval_results.json`. **Traceability**: Spec FR-006. (Depends on T029, T018)

- [ ] T033.1 [US3] **Implement Cross-Domain Validation (WikiText-2)**: Implement `evaluate_wikitext.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/`. **Logic**: Download WikiText-2 dataset using `datasets.load_dataset("wikitext", "wikitext-2-raw-v1")`. Evaluate final checkpoints on this dataset. Log perplexity and accuracy. **Output**: Write `data/artifacts/wikitext_results.json`. **Traceability**: Plan Phase 4, Step 5. (Depends on T029)

- [ ] T034 [US3] **Implement Correlation**: Implement `compute_metrics.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/`. **Logic**: Filter `training_logs.csv` by `model_type` (AR vs MDM). Calculate Pearson correlation between gap slope and HumanEval score **per architecture**. **Calculate Difference**: Compute `delta_r = abs(r_AR - r_MDM)`. **Evaluate** the result against the success criterion threshold (|delta_r| ≥ 0.5 [UNRESOLVED-CLAIM: c_8b136eb4 — status=not_enough_info]) defined in SC-002 and report pass/fail status. **Traceability**: Spec FR-010, SC-002. (Depends on T033, T029)

- [ ] T035 [US3] **Implement Report**: Implement `report_generator.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/`. **Logic**: Output `data/artifacts/statistical_results.json` and `analysis/report.md`. Include explicit `threshold_met` boolean for SC-002 (|delta_r| ≥ 0.5 [UNRESOLVED-CLAIM: c_8b136eb4 — status=not_enough_info]) and highlight pass/fail status prominently in the report. Include WikiText-2 results. (Depends on T034, T033.1)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036.1 [P] **Update README Installation**: Update `README.md` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/` with Installation section including `pip install -r requirements.txt`.
- [ ] T036.2 [P] **Update README Usage**: Update `README.md` with Usage section including `python main.py`. **Logic**: Default to 1M regime as per config.
- [ ] T036.3 [P] **Update Quickstart**: Update `quickstart.md` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/` with step-by-step execution commands.

- [ ] T038b.1 [P] **Verify Peak RAM**: Implement `verify_ram.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/training/`. **Logic**: Read `training_logs.csv`, find max RAM value, assert < 6.5 GB [UNRESOLVED-CLAIM: c_def4460a — status=not_enough_info]. **Traceability**: Spec FR-007.

- [ ] T040.1 [P] **Input Validation**: Implement `validate_inputs.py` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/utils/`. **Logic**: Sanitize file paths and validate dataset URLs in `download_micro_corpus.py`. **Traceability**: Constitution Principle III.

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
- **Scope Change**: T000.1 must pass before T000, and T000 must pass before T001.
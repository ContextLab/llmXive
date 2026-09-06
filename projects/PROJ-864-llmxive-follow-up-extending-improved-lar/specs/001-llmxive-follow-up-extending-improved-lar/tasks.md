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

## Phase 0: Automated Conflict Resolution & Configuration

**Purpose**: Resolve the spec/plan token‑count conflict automatically, generate a reproducible configuration, and record the resolution without requiring manual review.

- [ ] T000_STRATEGY [P] **Resolve Spec/Plan Token Conflict & Generate Strategy**:
 Implement `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/resolve_strategy.py`.
 **Logic**:
 1. Parse `spec.md` to extract the token target from FR‑001 (expected 10M).
 2. Parse `plan.md` to extract the token target from the Summary (1M).
 3. Run the static RAM validator (T009) for both regimes to determine feasibility.
 4. If the plan regime (1M) is feasible and the spec regime (10M) is not, write `data/artifacts/conflict_resolution_strategy.json` with `chosen_regime: "1M"`, `override_reason: "Plan feasibility overrides Spec requirement"`, `spec_requirement: "10M"`, `plan_requirement: "1M"`, `status: "RESOLVED"`.
 5. If both are feasible, default to Spec (10M). If neither, raise `FatalError`.
 **Traceability**: Spec FR‑001, Plan Summary. **Gate**: Must succeed before T000_CONFIG.

- [ ] T000_CONFIG [P] **Generate Config from Resolution Strategy**:
 Implement `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/generate_config.py`.
 **Logic**:
 1. Read `data/artifacts/conflict_resolution_strategy.json`.
 2. If `status` is not "RESOLVED", raise `FatalError`.
 3. Write `code/config.yaml` with `regime: <chosen_regime>`, `approved: true`, and placeholder `model_params` (to be filled by T009).
 **Traceability**: T000_STRATEGY. (Depends on T000_STRATEGY)

- [X] T001 [P] **Verify Config Consistency**: Implement `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/data/verify_config.py`.
 **Logic**: Load `code/config.yaml`; ensure `regime` matches one of the allowed values (1M or 10M) and `approved` is true. Raise `SystemExit(1)` if not.
 **Traceability**: T000_CONFIG. (Depends on T000_CONFIG)

## Phase 1: Setup (Shared Infrastructure)

- [ ] T003 [P] **Initialize Directories**: Create `code/`, `data/`, `tests/`, and `state/` directories in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/` and verify existence.

- [X] T004 [P] **Create main.py**: Create `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/main.py` and write `if __name__ == "__main__": pass` boilerplate.

- [ ] T005 **Initialize Python project with `requirements.txt`**: Create `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/requirements.txt` with pinned versions: `transformers>=4.40.0`, `datasets>=2.18.0`, `torch>=2.2.0`, `scikit-learn>=1.4.0`, `scipy>=1.12.0`, `pandas>=2.2.0`, `pyyaml>=6.0`, `huggingface_hub>=0.21.0`, `pingouin>=0.5.0`, `psutil>=5.9.0`.

- [ ] T006 **Initialize Linting and Formatting Configuration**: Create `ruff.toml` and `pyproject.toml` as previously described.

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T007.1 [P] **Implement Config Loader**: Implement `load_config()` in `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/utils/config.py`. Reads `code/config.yaml`, validates keys (`regime`, `token_target`, `model_params`), returns typed dict. Raises `ValueError` on missing keys.

- [ ] T007.2 [P] **Implement Config Saver**: Implement `save_config()` in the same module; writes dict to `code/config.yaml` with strict YAML formatting.

- [ ] T008.1 [P] **Implement RAM Monitor**: Implement `get_ram_usage()` in `utils/monitor.py` using `psutil` (returns GB).

- [ ] T008.2 [P] **Implement Time Monitor**: Implement `get_elapsed_time()` and `check_timeout()` in `utils/monitor.py`; raise `TimeoutError` after 6 h.

- [ ] T009 **Static RAM Validator & Feasibility Calculator**: Implement `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/models/ram_validator.py`.
 **Logic**:
 1. Accept `regime` (token count) as input.
 2. Using fixed constants (FP16 = 2 bytes/param, FP32 = 4 bytes/param) and a target RAM budget of 7 GB, compute the maximum feasible `d_model` and `num_layers` that keep estimated RAM ≤ 7 GB for a model that can process the given token regime.
 3. Write results to `data/artifacts/feasibility_config.json` with fields `{ "max_embed_dim": int, "max_layers": int, "estimated_params": int, "ram_estimate_gb": float }`.
 4. Update `code/config.yaml` under `model_params` with the derived `d_model`, `num_layers`, and `vocab_size` (from tokenizer).
 **Gate**: Raises `FatalError` if the regime cannot be accommodated within RAM.
 **Traceability**: T001, Spec FR‑007.

- [ ] T010 **Implement State Manager with Hashing**: Create `state_manager.py` in `utils/`; computes SHA‑256 hashes of all files under `code/` and `data/`, updates `state/projects/PROJ-864-llmxive-follow-up-extending-improved-lar.yaml` `artifact_hashes`.

- [ ] T028 **Power Analysis for Approved Regime**: Implement `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/analysis/power_analysis.py`.
 **Logic**: Read `regime` and `token_target` from `config.yaml`; using a simple effect‑size assumption (e.g., Cohen's d = 0.5) compute statistical power for the planned multiple seeds per group. Write `data/artifacts/power_analysis.json` with `{ "status": "PASS", "power_value": float, "effect_size_used": float, "required_seeds": int }`. Raise `FatalError` if power < 0.8.
 **Traceability**: Spec FR‑009, Plan Summary (Feasible Regime).

- **Checkpoint**: Foundational tasks complete; user stories can now proceed.

## Phase 3: User Story 1 - Construct and Validate the Micro‑Corpus (Priority: P1) 🎯 MVP

- [ ] T011 [P] [US1] **Contract test for corpus token bounds** in `tests/test_corpus_bounds.py`.

- [ ] T012 [P] [US1] **Integration test for HumanEval exclusion** in `tests/test_human_eval_exclusion.py`.

- [ ] T013 [US1] **Implement Micro‑Corpus Download & Balancing**: `download_micro_corpus.py`.
 **Logic**:
 1. Read `token_target` from `config.yaml`.
 2. Stream `bigcode/the-stack` (python subset) and `gutenberg` (text) via `datasets.load_dataset(..., streaming=True)`.
 3. Interleave chunks round‑robin with `chunk_size=10 000`.
 4. Stop when cumulative token count reaches target; if a source exhausts early, log a warning but continue with remaining source.
 **Traceability**: Spec FR‑001 (balanced mix).

- [ ] T014 **Tokenize & Stream**: `tokenize_and_stream.py`.
 **Logic**: Stream raw text, tokenize with HuggingFace `gpt2` tokenizer, write tokenized examples to `data/processed/micro_corpus_full.jsonl` until the cumulative token count reaches `token_target`. Discard any partial sequence that would exceed the target.

- [ ] T014_VERIFY_BALANCE **Verify Logical vs Code Token Balance**: `verify_balance.py`.
 **Logic**: After tokenization, compute the proportion of tokens originating from code‑heavy sources vs logical prose sources (using the source metadata). Assert the ratio is within 10 % of 50/50; otherwise raise `RuntimeError` with a clear message.

- [ ] T015 **Validate Corpus Bounds**: `validate_corpus.py`.
 **Logic**: Ensure token count is within ±1 % of `token_target`. If below [deferred] of target, halt with "Insufficient Data". Generate `data/artifacts/corpus_validation.json` recording token count, pass/fail, and any truncation info.

- [ ] T016 **Split & Truncate**: `split_data.py`.
 **Logic**: Split `micro_corpus_full.jsonl` into train/test (90/10 split) ensuring no overlapping sequences. If total tokens exceed `token_target + 10 000`, truncate to that limit and log to `truncation_log.json` with reason "Exceeded Target". Output `micro_corpus_train.jsonl` and `micro_corpus_test.jsonl`.

- [ ] T017.1 **Download Error Handler**: Add `raise_on_download_failure()` in `download_micro_corpus.py` that raises `RuntimeError` on any fetch error (no synthetic fallback).

- [ ] T017.2 **Tokenize Error Handler**: Add `raise_on_tokenize_failure()` in `tokenize_and_stream.py` that raises `RuntimeError` on tokenizer failure.

- [ ] T018 **HumanEval Exclusion Verification**: Extend `validate_corpus.py` to cross‑check that none of the HumanEval benchmark samples appear in the test split; update `corpus_validation.json` with `human_eval_excluded: true`.

**Checkpoint**: US1 functional and testable.

## Phase 4: User Story 2 - Execute Comparative Training Loops (Priority: P2)

- [ ] T021 [P] [US2] **Implement Autoregressive Model**: `autoregressive.py`.
 **Logic**: Read shared `model_params` from `config.yaml`; construct a causal LM with those exact dimensions (identical embed dim, heads, layers to diffusion model).

- [ ] T022 [P] [US2] **Implement Diffusion Model**: `diffusion.py`.
 **Logic**: Read same `model_params`; construct bidirectional masked diffusion model matching embedding dimensions and attention heads.

- [ ] T026_VERIFY_MODEL_ARCH **Verify Identical Architecture**: `verify_model_arch.py`.
 **Logic**: Load both model classes, compare `d_model`, `num_layers`, `num_attention_heads`; also compare total parameter count. Write `data/artifacts/parameter_validation.json` with pass/fail and details. **Gate**: Must succeed before training.

- [ ] T023 **Implement Train Loop**: `train_loop.py`.
 **Logic**: Use `torch.compile` (CPU mode) with batch size from config; enforce max epochs from config; integrate RAM and time monitors.

- [ ] T024 **Implement Training Callbacks & Metrics**: `callbacks.py`.
 **Logic**: After each epoch, log `epoch`, `model_type`, `seed_id`, `train_loss`, `val_loss`, `gap` (`train_loss - val_loss`), `accuracy`, `perplexity`, elapsed time, RAM usage, and disk usage to `data/artifacts/training_logs.csv`. Ensure `accuracy` column is always written.

- [ ] T029 **Orchestrate Training**: `run_experiment.py`.
 **Logic**:
 1. Load config; abort if `approved` is false.
 2. For each architecture (AR, MDM) and each seed (5 seeds), invoke `train_loop.py`.
 3. After each run, verify that `training_logs.csv` contains an `accuracy` entry for every epoch; if missing, raise `FatalError`.
 4. Save final model checkpoint to `data/artifacts/checkpoints/model_{model_type}_seed_{seed_id}_final.pt`.

- [ ] T037 **Dynamic Batch‑Size OOM Handling**: Extend `train_loop.py` to catch OOM, halve batch size, retry; abort if batch size < 4.

**Checkpoint**: US2 ready.

## Phase 5: User Story 3 - Analyze Overfitting Trajectories (Priority: P3)

- [ ] T032 **Implement ANOVA**: `statistical_test.py`.
 **Logic**: Load `training_logs.csv`; run Mixed‑Model Repeated‑Measures ANOVA on `gap ~ model_type * epoch + (1|seed_id)` using `pingouin`. Require at least 3 seeds per group; warn if fewer. Output `data/artifacts/anova_results.json` with `interaction_p_value`, `effect_size`, `model_summary`.

- [ ] T033 **Implement HumanEval Evaluation**: `evaluate_human_eval.py`.
 **Logic**: Load final checkpoints, run full HumanEval suite, verify exclusion again, write `human_eval_results.json`.

- [ ] T033.1 **Cross‑Domain Validation (WikiText‑2) – Optional Extension**: `evaluate_wikitext.py`.
 **Logic**: Download WikiText‑2, evaluate checkpoints, write `wikitext_results.json`.
 **Note**: This task is optional; it can be skipped without affecting core MVP.

- [ ] T034 **Compute Correlation**: `compute_metrics.py`.
 **Logic**: For each architecture, compute the slope of the generalization gap over epochs, then calculate Pearson correlation with the final HumanEval score. Write results to `statistical_results.json` and include a boolean `threshold_met` indicating whether |r| ≥ 0.5 for each model.

- [ ] T035 **Generate Report**: `report_generator.py`.
 **Logic**: Consolidate ANOVA results, correlation outcomes, and (if present) WikiText results into `analysis/report.md`. Highlight pass/fail of SC‑002 (|r| ≥ 0.5) prominently.

**Checkpoint**: All user stories complete.

## Phase N: Polish & Cross‑Cutting Concerns

- [ ] T036.1 **Update README Installation**: Add `pip install -r requirements.txt` section.

- [ ] T036.2 **Update README Usage**: Add usage example `python main.py` (defaults to 1M regime).

- [ ] T036.3 **Update Quickstart**: Provide step‑by‑step commands covering conflict resolution, corpus construction, training, and analysis.

- [ ] T038b.1 **Verify Peak RAM**: `verify_ram.py` reads `training_logs.csv`, asserts max RAM < 6.5 GB.

- [ ] T040.1 **Input Validation**: `validate_inputs.py` sanitizes file paths and checks dataset URLs.

- [ ] T041 **Validate quickstart.md**: Execute commands in `quickstart.md`; ensure exit code 0.

- [ ] T042.1 **Update State Hashes**: Run `state_manager.py` to refresh `state/...yaml` artifact hashes.
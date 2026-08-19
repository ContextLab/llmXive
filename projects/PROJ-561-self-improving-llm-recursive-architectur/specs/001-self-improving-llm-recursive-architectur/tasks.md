# Tasks: Self-improving LLM: recursive architecture refinement and re‑training

**Input**: Design documents from `/specs/001-self-improving-llm-recursive-architectur/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Create project structure per implementation plan: directories `code/`, `data/raw/`, `data/processed/`, `results/`, `specs/`, `tests/`, `tests/unit/`, `tests/integration/` and `__init__.py` files. Verification: filesystem check.
- [ ] T008 [P] Create `config.py` with hyperparameters (lr=5e-5, bs=4, seed), constraints (PARAM_LIMIT=0.30), and path definitions. Verification: imports and asserts.

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T001a [P] Implement "Pre‑flight URL Verification" in `pipeline/loader.py` (`verify_urls(urls: List[str])`). Raises error on unreachable URLs. Verification test added.
- [ ] T001b [P] Implement "Data Download & Checksumming" (`download_and_checksum(dataset_name, dest_path)`). Writes SHA‑256 file. Verification test added.
- [ ] T005b [P] Implement exponential backoff wrapper (`exponential_backoff`) with initial delay of a moderate duration, max retries a predefined limit. Verification test added.
- [ ] T005a [P] Implement dataset loaders for OpenWebText, GSM8K, ARC‑Challenge, BoolQ with fail‑fast logic and streaming support. Uses backoff from T005b. Verification test added.
- [ ] T006 [P] Implement `pipeline/model.py` GPU‑disabled loader for GPT‑2 124M checkpoint. Verification: device check.
- [ ] T013 [P] Define `ModificationProposal` Pydantic schema. Verification test added.
- [ ] T014b [P] Implement `validate_schema(proposal)` using the schema. Verification test added.
- [ ] T059 [P] Implement External Oracle (`validate_external_oracle`) enforcing ≤30 % parameter increase and structural validity. Verification test added.
- [ ] T020 [P] Implement Distinctness Validator (`validate_distinctness`) ensuring Hamming distance ≥ 1 or >5 % param change against history. Verification test added.
- [ ] T007 [P] Implement paired bootstrap statistical testing and linear regression trend analysis (`run_bootstrap_and_regression`). Reads `NUM_RESAMPLES` from `config.py`. Verification test added.
- [ ] T009 [P] Implement structured JSON logging for cycles. Verification: log file creation.
- [ ] T010 [P] Implement benchmark evaluator for GSM8K, ARC‑Challenge, BoolQ. Verification test added.
- [ ] T017c [P] Implement FLOP counter (`calculate_flops`) using `torch.profiler`. Verification test added.
- [ ] T004 [P] Implement RAM monitoring (`check_ram_usage(limit_gb)`) that records peak RAM usage. Verification test added.
- [ ] T004a [P] Implement RAM feasibility check (`enforce_ram_limit`) that aborts pipeline if peak RAM > 7 GB (per SC‑005). Verification test added.
- [ ] T011 [P] Unit test `tests/unit/test_memory.py::test_check_ram_usage_logs_warning`. Verification ensured.
- [ ] T012 [P] Unit test `tests/unit/test_loader.py::test_exponential_backoff_initial_delay`. Verification ensured.
- [ ] T014c [P] Unit test `tests/unit/test_model.py::test_generate_proposal_excludes_benchmark_data`. Verification ensured.
- [ ] T037b [P] (Removed from Phase 2 – will be defined in Phase 3 where it is used).

## Phase 3: User Story 1 – Single Refinement Cycle (Priority P1)

- [ ] T002 [P] Implement Baseline Capability Check (`run_baseline_check`) that evaluates the unmodified model on all benchmarks and writes Cycle 0 metrics to `results/trajectory.json`. Verification integration test added.
- [ ] T015 [P] Implement `generate_proposal` that prompts the model, renders `templates/modification_proposal.j2`, and returns a validated `ModificationProposal`. Relies on T013, T014b, T059, T020. Verification test added.
- [ ] T016 [P] Implement `apply_modification` that creates a new model instance per proposal (layer_add, head_count_change, hidden_size_change, activation_change) and maps existing weights. Verification test added.
- [ ] T017a [P] Implement training loop `train_epoch` (AdamW, bs=4, lr=5e-5, 1 epoch) on OpenWebText subset. Verification test added.
- [ ] T017b [P] Integrate FLOP counting into training via `calculate_flops`. Verification test added.
- [ ] T018 [P] Implement evaluation logic for GSM8K, ARC‑Challenge, BoolQ, storing accuracies/ECE. Verification test added.
- [ ] T044 [P] Implement training retry logic: up to 2 retries per cycle; on failure log, increment cycle counter, and proceed with new proposal. Verification test added.
- [ ] T036 [P] Implement early‑stop based on performance degradation ≥5 % from baseline (uses `check_termination`). Verification test added.
- [ ] T037b [P] Implement Separation of Generative/Verification Logic in `generate_proposal` (no benchmark data in prompt). Verification test added (see T014c).
- [ ] T048 [P] Orchestrate a single refinement cycle: invoke proposal generation, validation, modification, training, FLOP counting, evaluation, statistical analysis, logging, and termination checks. Integration test added verifying `results/trajectory.json` contains entry for Cycle 1.

## Phase 4: User Story 2 – Three Refinement Cycles (Priority P2)

- [ ] T049 [P] Extend orchestrator to repeat the refinement loop for up to three attempted cycles, respecting retry and early‑stop rules. Verification integration test added.
- [ ] T050 [P] After all cycles, aggregate metrics into `results/trajectory.json` (cycle number, parameter count, benchmark scores, FLOPs, training time). Verification test added.
- [ ] T075 [P] Implement `update_state_file` to hash artifacts and record per‑cycle hashes in `state/...yaml`. Verification test added.
- [ ] T074 [P] Implement `record_resource_metrics` that writes peak RAM and total wall‑clock time to `results/trajectory.json` and `results/final_report.md`. Depends on T004a. Verification test added.

## Phase 5: User Story 3 – Resource‑Performance Trade‑off (Priority P3)

- [ ] T071 [P] Compute performance‑per‑FLOP and performance‑per‑hour metrics for each cycle and append to `results/trajectory.json`. Verification test added.
- [ ] T072 [P] Generate final report summarizing trade‑off analysis, including tables and compliance with SC‑005 targets. Verification test added.

## Documentation

- [ ] T086 [P] Generate `docs/review_synthesis.md` mapping reviewer concerns to resolved task IDs (e.g., T059 for External Oracle). Verification: file existence and content check.

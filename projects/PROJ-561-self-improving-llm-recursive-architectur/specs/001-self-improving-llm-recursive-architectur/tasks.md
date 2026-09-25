# Tasks: Self-improving LLM: recursive architecture refinement and re‑training

**Input**: Design documents from `/specs/001-self-imoving-llm-recursive-architectur/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

## Phase 0: Research Design & Documentation (Prerequisites)

**Note**: These tasks must be executed sequentially as they all modify the same artifact (`research.md`). The `research.md` file must exist before these tasks begin.

- [ ] T008a Define the "methodology" for determining the "deferred" parameter limit in `research.md`. The task must describe *how* the limit will be determined (e.g., "Research to determine MAX_PARAM_INCREASE_RATIO based on parameter efficiency curves and memory constraints") without setting a concrete value. The value remains [deferred] until research analysis is complete. Verification: `grep -q "methodology" research.md` and `grep -q "[deferred]" research.md`.
- [ ] T099 Update `research.md` with the "External Oracle" protocol definition. Explicitly state that the evaluation metric is an external, immutable oracle during each cycle (FR-021), ensuring benchmarks are held-out from the model's proposal generation process. Verification: `grep -q "External Oracle" research.md` and `grep -q "immutable" research.md`.
- [ ] T100 Update `research.md` to explicitly define the "External Validation Protocol" ensuring benchmarks are immutable and held-out from the model's proposal generation process. Verification: `grep -q "External Validation Protocol" research.md`.
- [ ] T101 Update `research.md` to explicitly define the operational definition of "lasting improvement" as persistence across at least two subsequent training cycles (Turing Review), distinct from single-epoch gains. Verification: `grep -q "lasting improvement" research.md`.
- [ ] T102 Update `research.md` to include a "Rollback Mechanism" specification: if performance drops below a threshold, the system MUST revert to the previous stable checkpoint. Verification: `grep -q "Rollback Mechanism" research.md`.
- [ ] T103 Update `research.md` with a "Scaling Law Analysis" section (West Review) defining the expected power-law decay of improvement gains (Δperformance vs. iteration count) and the thermodynamic bounds of recursion. Verification: `grep -q "Scaling Law" research.md`.
- [~] T104 Update `research.md` to address "Computational Irreducibility" (Wolfram Review): explicitly state that no closed-form prediction of improvement trajectories exists and that the methodology relies on empirical mining of the architecture rule space. Verification: `grep -q "Computational Irreducibility" research.md`.
- [~] T105 Update `research.md` to distinguish between "Recursive Improvement" (optimization) and "Recursive Adaptation" (evolutionary blind-spot navigation) per Krakauer Review, and define a metric for "stupidity" or error cost in changing environments. Verification: `grep -q "Recursive Adaptation" research.md`. <!-- FAILED: unspecified -->

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create project structure per implementation plan: directories `code/`, `code/tests/`, `code/tests/unit/`, `code/tests/integration/`, `data/raw/`, `data/processed/`, `results/`, `state/` and `__init__.py` files. Verification: run `python -c "import os; assert os.path.exists('code/tests/unit/__init__.py') and os.path.exists('data/raw') and os.path.exists('results') and os.path.exists('state')"`.
- [X] T008 [P] Create `config.py` with hyperparameters (lr=5e-5, bs=4, seed), constraints (MAX_PARAM_INCREASE_RATIO=0.30) [UNRESOLVED-CLAIM: c_54a13460 — status=not_enough_info], and path definitions. **Note**: If `research.md` defines a methodology for a different limit, this task must document the default (0.30) and the method to override it. Verification: imports and asserts.

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T001a [P] Implement "Pre‑flight URL Verification" in `utils/data_loader.py` (`verify_urls(urls: List[str])`). Raises error on unreachable URLs. Verification test added.
- [X] T001b [P] Implement "Data Download & Checksumming" (`download_and_checksum(dataset_name, dest_path)`). Writes SHA‑256 file. Verification test added.
- [X] T005b [P] Implement exponential backoff wrapper (`exponential_backoff`) with `initial_delay=30` seconds and `max_retries=5` [UNRESOLVED-CLAIM: c_e0a4f2a8 — status=not_enough_info]. Verification test added.
- [X] T005a [P] Implement dataset loaders for OpenWebText, GSMK, ARC‑Challenge, BoolQ with fail‑fast logic and streaming support. Uses backoff from T005b. Verification: ensure training and eval datasets are disjoint (no overlap in IDs/URLs) and generate `data/disjoint_check_report.json`.
- [X] T006 [P] Implement `models/loader.py` CPU-only loader for GPT checkpoint. Verification: device check (device='cpu').
- [X] T013 [P] Define `ModificationProposal` Pydantic schema. Verification test added.
- [X] T014b [P] Implement `validate_schema(proposal)` using the schema. Verification test added.
- [X] T059 [P] Implement External Oracle (`validate_external_oracle`) enforcing parameter limit from `research.md` (via config) and structural validity. Verification test added.
- [X] T020 [P] Implement Distinctness Validator (`validate_distinctness`) ensuring Hamming distance ≥ 1 or >5 % param change against history [UNRESOLVED-CLAIM: c_752d12e5 — status=not_enough_info]. Verification test added.
- [X] T007 [P] Implement paired bootstrap statistical testing (`run_bootstrap_test`). Default `NUM_RESAMPLES=1000 (1409.4317, https://arxiv.org/abs/1409.4317)` [UNRESOLVED-CLAIM: c_070b8cf4 — status=not_enough_info]. Verification test added.
- [X] T073 [P] Implement linear regression trend analysis (`run_regression_analysis`). Verification test added.
- [X] T009 [P] Implement structured JSON logging for cycles. Verification: log file creation.
- [X] T010 [P] Implement benchmark evaluator for GSM8K, ARC‑Challenge, BoolQ. Verification test added.
- [X] T017c [P] Implement FLOP counter (`calculate_flops`) using `torch.profiler`. Verification test added.
- [X] T004 [P] Implement RAM monitoring (`check_ram_usage(limit_gb)`) that records peak RAM usage. Verification test added.
- [X] T004a [P] Implement RAM feasibility check (`enforce_ram_limit`) that logs a warning and records the failure data point if peak RAM > 7 GB [UNRESOLVED-CLAIM: c_24226e12 — status=not_enough_info] (per SC‑005), but does NOT abort the pipeline. This allows SC-004 to measure trade-offs even in failure modes. Verification test added.
- [X] T011 [P] Unit test `tests/unit/test_memory.py::test_check_ram_usage_logs_warning`. Verification ensured.
- [X] T012 [P] Unit test `tests/unit/test_loader.py::test_exponential_backoff_initial_delay`. Verification ensured.
- [X] T014c [P] Unit test `tests/unit/test_model.py::test_generate_proposal_excludes_benchmark_data`. Verification ensured.
- [X] T002 [P] Implement Baseline Capability Check (`run_baseline_check`) that evaluates the unmodified model on all benchmarks and writes Cycle 0 metrics to `results/trajectory.json`. Verification integration test added. **Dependency**: Must complete before T048.

## Phase 3: User Story 1 – Single Refinement Cycle (Priority P1)

- [X] T015 [P] Implement `generate_proposal` that prompts the model, renders `templates/modification_proposal.j2`, and returns a validated `ModificationProposal`. **Constraint**: This task is strictly an orchestrator; it MUST accept callable validator functions (schema, oracle, distinctness) as arguments and delegate validation to them without re-implementing logic. Verification: Code review ensures no duplicate validation logic; unit test mocks Phase 2 functions and asserts T015 only calls them.
- [X] T016 [P] Implement `apply_modification` that creates a new model instance per proposal (layer_add, head_count_change, hidden_size_change, activation_change) and maps existing weights. Verification test added.
- [X] T017a [P] Implement training loop `train_epoch` (AdamW, bs=4, lr=5e-5, 1 epoch [UNRESOLVED-CLAIM: c_825f482e — status=not_enough_info]) on OpenWebText subset. Saves model to `results/cycle_N/model.pt`. Verification test added: `tests/unit/test_trainer.py::test_epoch_loss_convergence`.
- [X] T017b [P] Integrate FLOP counting into training via `calculate_flops`. Verification test added.
- [X] T018 [P] Implement evaluation logic for GSM8K, ARC‑Challenge, BoolQ, storing accuracies/ECE. Verification test added.
- [X] T044 [P] Implement training retry logic: up to 2 retries per cycle [UNRESOLVED-CLAIM: c_dcef8f2d — status=not_enough_info]; on 2nd failure, log failure, increment cycle counter, and proceed to next cycle with a NEW modification. Verification test added: `tests/unit/test_attempt_tracker.py::test_retry_fails_after_2_attempts`.
- [X] T036 [P] Implement early‑stop based on performance degradation ≥5 % from baseline [UNRESOLVED-CLAIM: c_626c72c2 — status=not_enough_info] (uses `check_termination`). Verification test added.
- [X] T048 [P] Orchestrate a single refinement cycle: invoke proposal generation (T015), validation, modification (T016), training (T017a/b), FLOP counting, evaluation (T018), statistical analysis (T007), linear regression (T073), logging, and termination checks. **Prerequisites**: T002 (Baseline) must be completed and metrics present in `results/trajectory.json` before execution. **Dependency**: Explicitly requires T002. Integration test added verifying `results/trajectory.json` contains entry for Cycle 0 before T048 runs.

## Phase 4: User Story 2 – Three Refinement Cycles (Priority P2)

- [X] T049 [P] Extend orchestrator to repeat the refinement loop for up to three attempted cycles [UNRESOLVED-CLAIM: c_a2af7c17 — status=not_enough_info], respecting retry and early‑stop rules. Verification integration test added.
- [X] T050 [P] After all cycles, aggregate metrics into `results/trajectory.json` (cycle number, parameter count, benchmark scores, FLOPs, training time). Verification test added.
- [X] T075 [P] Implement `update_state_file` to hash artifacts (model.pt, trajectory.json) and record per‑cycle hashes in `state/cycle_N.yaml`. Verification test added: verify hash in `state/cycle_N.yaml` matches artifact hash of `model.pt`.
- [X] T074 [P] Implement `record_resource_metrics` that writes peak RAM and total wall‑clock time to `results/trajectory.json` and `results/final_report.md`. Depends on T004a and T114. Runs sequentially after T050 to append resource metrics. Verification test added.

## Phase 5: User Story 3 – Resource‑Performance Trade‑off (Priority P3)

- [X] T071 [P] Compute performance‑per‑FLOP and performance‑per‑hour metrics for each cycle and append to `results/trajectory.json`. Verification test added.
- [X] T114 [P] Record peak RAM usage from T004 into `results/trajectory.json` and `results/final_report.md`. This task explicitly satisfies SC-005's requirement to measure and report peak RAM. Verification test added: `grep -q "peak_ram_gb" results/trajectory.json`.
- [X] T072 [P] Generate final report summarizing trade‑off analysis, including tables and compliance with SC-target metrics. Verification test added.

## Phase 6: Documentation & Philosophical Synthesis (Review Response)

**Purpose**: Address specific concerns from research-stage reviews regarding authority, fixed-points, scaling laws, and computational irreducibility. This phase generates the final research report linking experimental results to Success Criteria.

**Prerequisites**: Phase 0 tasks (T008a, T099-T105) must be completed to ensure definitions are in place.

- [X] T113 [P] Generate `docs/final_report.md` synthesizing the 3-cycle trajectory analysis, trade-off metrics, and compliance with SC-003 (Trajectory Persistence), SC-004 (Cost-Effectiveness), and SC-005 (Feasibility). Explicitly map findings to the original research question and address the "External Oracle" and "Fixed-Point" protocols defined in `research.md` (T099) and linked to FR-021. Verification: `grep -q "SC-003" docs/final_report.md` and `grep -q "SC-004" docs/final_report.md`.
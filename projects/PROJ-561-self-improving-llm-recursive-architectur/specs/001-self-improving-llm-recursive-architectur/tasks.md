# Tasks: Self-improving LLM: recursive architecture refinement and re‑training

**Input**: Design documents from `/specs/001-self-imoving-llm-recursive-architectur/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/ (research.md and final_report.md are generated artifacts)

## Phase 0: Research Design & Documentation (Prerequisites)

**Note**: These tasks must be executed sequentially. T000 creates the `research.md` artifact required by all subsequent tasks.

- [ ] T000 [P] Create `research.md` from scratch. This file MUST include the following sections:
 1. `## Methodology for Parameter Limit` (describing how the limit is determined, marking value as `[deferred]` until research analysis).
 2. `## External Oracle Protocol` (defining the immutable evaluation metric).
 3. `## Philosophical & Operational Definitions` (covering Source of Authority, Fixed-Point, Scaling Laws, Computational Irreducibility, Recursive Adaptation, Overfitting, Minimality Search, Thermodynamic Bounds, Bird vs. Frog).
 Verification: `grep -q "## Methodology for Parameter Limit" research.md` AND `grep -q "## External Oracle Protocol" research.md` AND `grep -q "## Philosophical & Operational Definitions" research.md`.
- [ ] T001c [P] Implement "Pre‑flight URL Verification" in `utils/data_loader.py` (`verify_urls(urls: List[str])`). Raises error on unreachable URLs. **Depends on**: T000. Verification: Unit test added.
- [ ] T001d [P] Implement "Data Download & Checksumming" (`download_and_checksum(dataset_name, dest_path)`). Writes SHA‑256 file. **Depends on**: T001c. Verification: Unit test added.

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create project structure per implementation plan: directories `code/`, `code/tests/`, `code/tests/unit/`, `code/tests/integration/`, `data/raw/`, `data/processed/`, `results/`, `state/` and `__init__.py` files. Verification: run `python -c "import os; assert os.path.exists('code/tests/unit/__init__.py') and os.path.exists('data/raw') and os.path.exists('results') and os.path.exists('state')"`.
- [ ] T008 [P] Create `config.py` with hyperparameters (lr=5e-5, bs=4, seed). For `MAX_PARAM_INCREASE_RATIO`, if `research.md` exists and contains a defined methodology/value, read it; otherwise, set to `None` (or `'[DEFERRED]'`) and log a warning that the default 0.30 is provisional. **Depends on**: T000. Verification: imports and asserts; check that value is not hardcoded 0.30 if research.md is missing.

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T001a [P] Unit test for `verify_urls` in `utils/data_loader.py`. Verification test added.
- [X] T001b [P] Unit test for `download_and_checksum` in `utils/data_loader.py`. Verification test added.
- [X] T005b [P] Implement exponential backoff wrapper (`exponential_backoff`) with `initial_delay=30` seconds and `max_retries=5`. Verification test added.
- [X] T005a [P] Implement dataset loaders for OpenWebText, GSMK, ARC‑Challenge, BoolQ with fail‑fast logic and streaming support. Uses backoff from T005b. Verification: ensure training and eval datasets are disjoint (no overlap in IDs/URLs) and generate `data/disjoint_check_report.json`.
- [X] T006 [P] Implement `models/loader.py` CPU-only loader for GPT checkpoint. Verification: device check (device='cpu').
- [X] T013 [P] Define `ModificationProposal` Pydantic schema. Verification test added.
- [X] T014b [P] Implement `validate_schema(proposal)` using the schema. Verification test added.
- [X] T059 [P] Implement External Oracle (`validate_external_oracle`) enforcing parameter limit from `research.md` (via config) and structural validity. Verification test added.
- [X] T020 [P] Implement Distinctness Validator (`validate_distinctness`) ensuring Hamming distance ≥ 1 or >5% param change against history. Verification test added.
- [X] T007 [P] Implement paired bootstrap statistical testing (`run_bootstrap_test`) with Bonferroni correction for multiple benchmark comparisons (α=0.05 adjusted). (1409.4317, https://arxiv.org/abs/1409.4317). **Note**: This task implements paired bootstrap with Bonferroni correction. Verification test added.
- [X] T073 [P] Implement linear regression trend analysis (`run_regression_analysis`). Verification test added.
- [X] T009 [P] Implement structured JSON logging for cycles.Verification: log file creation.
- [X] T010 [P] Implement benchmark evaluator for GSM8K, ARC‑Challenge, BoolQ. Verification test added.
- [X] T017c [P] Implement FLOP counter (`calculate_flops`) using `torch.profiler`. Verification test added.
- [X] T004 [P] Implement RAM monitoring (`check_ram_usage(limit_gb)`) that records peak RAM usage. Verification test added.
- [X] T004a [P] Implement RAM feasibility check (`enforce_ram_limit`) that records peak RAM. If peak RAM > 7 GB, the system MUST write a 'infeasible' status to `results/feasibility_status.json` and flag the run as violating SC-005. The pipeline may proceed to log data but the final report MUST reflect the feasibility violation. **Note**: This task enforces the constraint by flagging, not by silently ignoring. Verification test added.
- [X] T011 [P] Unit test `tests/unit/test_memory.py::test_check_ram_usage_logs_warning`. Verification ensured.
- [X] T012 [P] Unit test `tests/unit/test_loader.py::test_exponential_backoff_initial_delay`. Verification ensured.
- [X] T014c [P] Unit test `tests/unit/test_model.py::test_generate_proposal_excludes_benchmark_data`. Verification ensured.
- [X] T002 [P] Implement Baseline Capability Check (`run_baseline_check`) that evaluates the unmodified model on all benchmarks, writes Cycle 0 metrics to `results/trajectory.json`, and explicitly flags if performance is near-random (<10% on GSM8K/ARC). **Dependency**: Must complete before T048. Verification integration test added.

## Phase 3: User Story 1 – Single Refinement Cycle (Priority P1)

- [X] T015 [P] Implement `generate_proposal` that prompts the model, renders `templates/modification_proposal.j2`, and returns a validated `ModificationProposal`. **Constraint**: This task is strictly an orchestrator; it MUST accept callable validator functions (schema, oracle, distinctness) as arguments and delegate validation to them without re-implementing logic. Verification: Code review ensures no duplicate validation logic; unit test mocks Phase 2 functions and asserts T015 only calls them.
- [X] T016 [P] Implement `apply_modification` that creates a new model instance per proposal (layer_add, head_count_change, hidden_size_change, activation_change) and maps existing weights. Verification test added.
- [X] T017a [P] Implement training loop `train_epoch` (AdamW, bs=4, lr=5e-5, 1 epoch) on OpenWebText subset. Saves model to `results/cycle_N/model.pt`. Includes **Time-Estimation and Subset-Reduction Fallback**: if estimated time > 2h, reduce training subset to [deferred] samples. Verification test added: `tests/unit/test_trainer.py::test_epoch_loss_convergence`.
- [X] T017b [P] Integrate FLOP counting into training via `calculate_flops`. Verification test added.
- [X] T018 [P] Implement evaluation logic for GSM8K, ARC‑Challenge, BoolQ, storing accuracies/ECE. Verification test added.
- [X] T044 [P] Implement training retry logic: up to 2 retries per cycle; on 2nd failure, log failure, increment cycle counter, and proceed to next cycle with a NEW modification. Verification test added: `tests/unit/test_attempt_tracker.py::test_retry_fails_after_2_attempts`.
- [X] T036 [P] Implement early‑stop based on performance degradation ≥5 % from baseline (uses `check_termination`). Verification test added.
- [X] T048 [P] Orchestrate a single refinement cycle: invoke proposal generation (T015), validation, modification (T016), training (T017a/b), FLOP counting, evaluation (T018), statistical analysis (T007), logging, and termination checks. **Prerequisites**: T002 (Baseline) must be completed and metrics present in `results/trajectory.json` before execution. **Dependency**: Explicitly requires T002. **Note**: Linear regression (T073) is NOT performed here; it is reserved for after 3 cycles. Integration test added verifying `results/trajectory.json` contains entry for Cycle 0 before T048 runs.

## Phase 4: User Story 2 – Three Refinement Cycles (Priority P2)

- [X] T049 [P] Extend orchestrator to repeat the refinement loop for up to three attempted cycles, respecting retry and early‑stop rules. Verification integration test added.
- [X] T050 [P] After all cycles, aggregate metrics into `results/trajectory.json` (cycle number, parameter count, benchmark scores, FLOPs, training time). Verification test added.
- [X] T075 [P] Implement `update_state_file` to hash artifacts (model.pt, trajectory.json) and record per‑cycle hashes in `state/cycle_N.yaml`. Verification test added: verify hash in `state/cycle_N.yaml` matches artifact hash of `model.pt`.
- [X] T074 [P] Implement `record_resource_metrics` that writes peak RAM and total wall‑clock time to `results/trajectory.json` and `results/final_report.md`. Depends on T004a and T114. Runs sequentially after T050 to append resource metrics. Verification test added.

## Phase 5: User Story 3 – Resource‑Performance Trade‑off (Priority P3)

- [X] T071 [P] Compute performance‑per‑FLOP and performance‑per‑hour metrics for each cycle and append to `results/trajectory.json`. Verification test added.
- [X] T114 [P] Record peak RAM usage from T004 into `results/trajectory.json` and `results/final_report.md`. This task explicitly satisfies SC-005's requirement to measure and report peak RAM. Verification test added: `grep -q "peak_ram_gb" results/trajectory.json`.
- [X] T072 [P] Generate final report summarizing trade‑off analysis, including tables and compliance with SC-target metrics. Verification test added.
- [ ] T131 [P] [Review] Implement "Capacity Normalization" analysis in `pipeline/trajectory.py`. Analyze if improvements correlate with parameter count or topology as required by Plan Step 4.3. **Depends on**: T050. Verification: `results/trajectory.json` includes `capacity_normalization_analysis` field.

## Phase 6: Documentation & Philosophical Synthesis (Review Response)

**Purpose**: Address specific concerns from research-stage reviews regarding authority, fixed-points, scaling laws, and computational irreducibility. This phase generates the final research report linking experimental results to Success Criteria.

**Prerequisites**: Phase 0 tasks (T000) must be completed to ensure definitions are in place.

- [X] T123 [P] Create `docs/final_report.md` from scratch. This file MUST include a placeholder structure for the final synthesis. **Depends on**: T000 (indirectly via T099). Verification: `test -f docs/final_report.md`.
- [X] T113 [P] Generate `docs/final_report.md` synthesizing the 3-cycle trajectory analysis, trade-off metrics, and compliance with SC-003 (Trajectory Persistence), SC-004 (Cost-Effectiveness), and SC-005 (Feasibility). Explicitly map findings to the original research question and address the "External Oracle" and "Fixed-Point" protocols defined in `research.md` (T000) and linked to FR-021. **Depends on**: T123, T000. Verification: `grep -q "SC-003" docs/final_report.md` and `grep -q "SC-004" docs/final_report.md`.
- [X] T115 [P] Update `docs/final_report.md` to explicitly discuss "Source of Authority", "Fixed-Point Problem", "Scaling Law Analysis", "Computational Irreducibility", "Recursive Adaptation", "Overfitting", "Minimality Search", "Thermodynamic Bounds", and "Bird vs. Frog" concepts, addressing the specific reviewer concerns. **Depends on**: T123, T000. Verification: `grep -q "Source of Authority" docs/final_report.md` AND `grep -q "Fixed-Point Problem" docs/final_report.md` AND `grep -q "Scaling Law" docs/final_report.md` AND `grep -q "Computational Irreducibility" docs/final_report.md` AND `grep -q "Recursive Adaptation" docs/final_report.md` AND `grep -q "Overfitting" docs/final_report.md` AND `grep -q "Minimality Search" docs/final_report.md` AND `grep -q "Thermodynamic Bounds" docs/final_report.md` AND `grep -q "Bird vs. Frog" docs/final_report.md`.
- [X] T116 [P] (Consolidated into T115) Update `docs/final_report.md` to analyze the "Fixed-Point Problem". Verification: (See T115).
- [X] T117 [P] (Consolidated into T115) Update `docs/final_report.md` to present the "Scaling Law Analysis". Verification: (See T115).
- [X] T118 [P] (Consolidated into T115) Update `docs/final_report.md` to address "Computational Irreducibility". Verification: (See T115).
- [X] T119 [P] (Consolidated into T115) Update `docs/final_report.md` to distinguish "Recursive Improvement" vs. "Recursive Adaptation". Verification: (See T115).
- [X] T120 [P] (Consolidated into T115) Update `docs/final_report.md` to explicitly confirm the separation of training data and immutable benchmarks. Verification: (See T115).
- [X] T121 [P] (Consolidated into T115) Update `docs/final_report.md` to include a discussion on the "Minimality Search". Verification: (See T115).
- [X] T122 [P] (Consolidated into T115) Update `docs/final_report.md` to address the "Bird vs. Frog" question. Verification: (See T115).

## Phase 7: Addressing Research-Stage Review Concerns (New Tasks)

**Purpose**: Implement specific safeguards and documentation required by the simulated reviews (Lovelace, Turing, Von Neumann, etc.) to ensure the system is not merely executing a pre-ordered sequence but is rigorously tested for genuine improvement.

- [ ] T124 [P] [Review] Implement "Authority Trace" logging in `utils/logging.py`. Every modification proposal must log the chain of authority: the specific benchmark score used, the oracle check result, and the human-defined constraint (e.g., "Parameter limit 0.30 from config"). This addresses the "Source of Authority" concern raised by Ada Lovelace and John Von Neumann. **Depends on**: T009. Verification: Log output must contain "Authority Trace" and the specific metric value.
- [ ] T125 [P] [Review] Implement "Curriculum Lock" mechanism in `pipeline/evaluator.py`. Ensure the benchmark suite (GSM8K, ARC, BoolQ) is loaded from a read-only, immutable source and cannot be altered by the model's proposal generation logic. This addresses Alan Turing's concern about the machine selecting its own curriculum. **Depends on**: T010. Verification: Unit test attempts to modify benchmark config during proposal generation and asserts failure.
- [ ] T126 [P] [Review] Implement "Rollback & Verification" state machine in `pipeline/attempt_tracker.py`. If a cycle fails the "External Oracle Check" or results in degradation > 5%, the system MUST log a "Rollback Event", increment the cycle counter, and proceed to the next cycle with a NEW modification. **Note**: This task does NOT revert model weights; it ensures the cycle counter advances and a new modification is attempted, strictly adhering to FR-012. **Depends on**: T044, T036. Verification: Integration test simulates a degradation event and verifies cycle counter increments and new modification is attempted.
- [ ] T127 [P] [Review] Implement "Computational Irreducibility" report generator in `pipeline/trajectory.py`. This task adds a section to the trajectory analysis that explicitly states: "No closed-form prediction exists for this trajectory; results are empirically derived." It must also plot the "Rule Space Exploration" (number of distinct modification types tried vs. performance gain) to satisfy Stephen Wolfram's request for rule-space enumeration. **Depends on**: T050. Verification: `results/trajectory.json` includes a `computational_irreducibility_note` field.
- [ ] T128 [P] [Review] Implement "Thermodynamic Bounds" calculator in `pipeline/trainer.py`. Calculate the energy cost (approximated by FLOPs * time) per unit of accuracy gain for each cycle. Compute performance-per-FLOP and performance-per-hour ratios as required by SC-004. **Note**: This task does NOT implement a 'super-linear' flag or 'Geoffrey West' logic. **Depends on**: T017b, T071. Verification: `results/trajectory.json` includes `energy_per_accuracy_unit`.
- [ ] T129 [P] [Review] Implement "Minimality Search" heuristic in `models/modifier.py`. Before applying a complex modification (e.g., adding layers), the system MUST first attempt the simplest valid modification (e.g., hyperparameter tweak or single neuron count change) and log why the complex one was chosen. This addresses Stephen Wolfram's "simplest rule" and David Krakauer's "novelty vs. fit" concerns. **Depends on**: T016. Verification: Log shows "Attempting minimal modification first" before complex proposal.
- [ ] T130 [P] [Review] Implement "Fixed-Point Convergence" detector in `pipeline/attempt_tracker.py`. If three consecutive cycles yield no statistically significant improvement (p > 0.05) and parameter count is increasing, the system MUST terminate and report "Fixed Point Reached: No further improvement detected". This addresses John Von Neumann's "convergence" and "infinite regress" concerns. **Depends on**: T007, T049. Verification: Integration test simulates 3 stagnant cycles and asserts early termination.
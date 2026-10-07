# Tasks: Self-improving LLM: recursive architecture refinement and re‑training

**Input**: Design documents from `/specs/001-self-imoving-llm-recursive-architectur/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/ (research.md and final_report.md are generated artifacts)

## Phase 0: Research Design & Documentation (Prerequisites)

**Note**: These tasks must be executed sequentially. T000 creates the `research.md` artifact required by all subsequent tasks.

- [X] T000 [S] Create `research.md` from scratch. This file MUST include the following sections:
 1. `## Methodology for Parameter Limit` (describing how the limit is determined, marking value as `[deferred]` until research analysis, but explicitly stating the formula structure: `limit = baseline_params * a moderate scaling factor` where the factor is to be determined by research).
 2. `## External Oracle Protocol` (defining the immutable evaluation metric, explicitly stating: "Reject if new_params significantly exceed baseline.").
 3. `## Philosophical & Operational Definitions` (covering Source of Authority, Fixed-Point, Scaling Laws, Computational Irreducibility, Recursive Adaptation, Overfitting, Minimality Search, Thermodynamic Bounds, Bird vs. Frog).
 Verification: `grep -q "## Methodology for Parameter Limit" research.md` AND `grep -q "## External Oracle Protocol" research.md` AND `grep -q "## Philosophical & Operational Definitions" research.md`.
- [X] T001c [S] Implement "Pre‑flight URL Verification" in `utils/data_loader.py` (`verify_urls(urls: List[str])`). Raises error on unreachable URLs. Implements FR-011 exponential backoff (initial=30s, max=5) for all HTTP requests. **Note**: This task is independent of T000. Verification: Unit test added.
- [X] T001d [S] Implement "Data Download & Checksumming" (`download_and_checksum(dataset_name, dest_path)`). Writes SHA‑256 file. **Note**: This task is independent of T000. Verification: Unit test added.
- [X] T005b [S] Implement exponential backoff wrapper (`exponential_backoff`) with `initial_delay=30` seconds and `max_retries=5`. **Note**: This is the core logic used by T001c. Verification test added.

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create project structure per implementation plan: directories `code/`, `code/tests/`, `code/tests/unit/`, `code/tests/integration/`, `data/raw/`, `data/processed/`, `results/`, `state/` and `__init__.py` files. Verification: run `python -c "import os; assert os.path.exists('code/tests/unit/__init__.py') and os.path.exists('data/raw') and os.path.exists('results') and os.path.exists('state')"`.
- [X] T008 [S] Create `config.py` with hyperparameters (lr=5e-5, bs=4, seed). For `MAX_PARAM_INCREASE_RATIO`, read the float value from the section `## Methodology for Parameter Limit` in `research.md`. **CRITICAL**: If `research.md` is missing, the section is missing, or the value is invalid, the system MUST raise a `ConfigurationError` immediately. NO default is allowed. Verification: imports and asserts; check that value is not hardcoded 0.30 and that missing research causes failure.

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T001a [P] Unit test for `verify_urls` in `utils/data_loader.py`. Verification test added.
- [X] T001b [P] Unit test for `download_and_checksum` in `utils/data_loader.py`. Verification test added.
- [X] T005a [P] Implement dataset loaders for OpenWebText, GSMK, ARC‑Challenge, BoolQ with fail‑fast logic and streaming support. Uses backoff from T005b. [UNRESOLVED-CLAIM: c_54934791 — status=not_enough_info] Verification: ensure training and eval datasets are disjoint (no overlap in IDs/URLs) and generate `data/disjoint_check_report.json`.
- [X] T006 [P] Implement `models/loader.py` CPU-only loader for GPT checkpoint. Verification: device check (device='cpu').
- [X] T013 [P] Define `ModificationProposal` Pydantic schema. Verification test added.
- [X] T014b [P] Implement `validate_schema(proposal)` using the schema. Verification test added.
- [X] T019 [S] Implement "Parameter Constraint Check" (`check_parameter_constraint`). This task explicitly implements FR-019. It validates that `new_params <= baseline_params * MAX_PARAM_INCREASE_RATIO`. **CRITICAL**: This task MUST read `MAX_PARAM_INCREASE_RATIO` from `config.py` (which reads from `research.md`). If the value is missing or invalid, the system MUST raise a `ConfigurationError`. NO hardcoded fallback is allowed. Verification test added.
- [X] T059 [S] Implement External Oracle (`validate_external_oracle`) enforcing parameter limit (using the value from config) and structural validity. Verification test added.
- [X] T020 [S] Implement Distinctness Validator (`validate_distinctness`) ensuring Hamming distance ≥ 1 or >5% param change against history. Verification test added.
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
- [X] T002 [S] Implement Baseline Capability Check (`run_baseline_check`) that evaluates the unmodified model on all benchmarks, writes Cycle 0 metrics to `results/trajectory.json`, and explicitly flags if performance is near-random (<10% on GSM8K/ARC) [UNRESOLVED-CLAIM: c_1e8188db — status=not_enough_info]. **Dependency**: Must complete before T048. Verification integration test added.

## Phase 3: User Story 1 – Single Refinement Cycle (Priority P1)

- [X] T015 [S] Implement `generate_proposal` that prompts the model, renders `templates/modification_proposal.j2`, and returns a validated `ModificationProposal`. **Constraint**: This task is strictly an orchestrator; it MUST accept callable validator functions (schema, oracle, distinctness) as arguments and delegate validation to them without re-implementing logic. Verification: Code review ensures no duplicate validation logic; unit test mocks Phase 2 functions and asserts T015 only calls them.
- [X] T016 [S] Implement `apply_modification` that creates a new model instance per proposal (layer_add, head_count_change, hidden_size_change, activation_change) and maps existing weights. Verification test added.
- [X] T017a [S] Implement training loop `train_epoch` (AdamW, bs=4, lr=5e-5, 1 epoch) on OpenWebText subset. Saves model to `results/cycle_N/model.pt`. Includes **Time-Estimation and Subset-Reduction Fallback**: if estimated time > 2h, reduce training subset to a dynamic sample count determined by the research phase or a calculated fraction of the total dataset to fit within the time budget. [UNRESOLVED-CLAIM: c_fa63739b — status=not_enough_info] This fallback is deterministic and documented. Verification test added: `tests/unit/test_trainer.py::test_epoch_loss_convergence`.
- [X] T017b [P] Integrate FLOP counting into training via `calculate_flops`. Verification test added.
- [X] T018 [S] Implement evaluation logic for GSM8K, ARC‑Challenge, BoolQ, storing accuracies/ECE. Verification test added.
- [X] T044 [S] Implement training retry logic: up to 2 retries per cycle [UNRESOLVED-CLAIM: c_1c2717a1 — status=not_enough_info]; on 2nd failure, log failure, increment cycle counter, and proceed to next cycle with a NEW modification. Verification test added: `tests/unit/test_attempt_tracker.py::test_retry_fails_after_2_attempts`.
- [X] T036 [S] Implement **Early Termination Check** (`check_termination`). This task explicitly implements FR-015. If performance degradation >= 5% from baseline (Cycle 0), the system MUST terminate the pipeline immediately. [UNRESOLVED-CLAIM: c_74f28d5e — status=not_enough_info] Verification test added.
- [X] T048 [S] Orchestrate a single refinement cycle: invoke proposal generation (T015), validation, modification (T016), training (T017a/b), FLOP counting, evaluation (T018), statistical analysis (T007), logging, and termination checks (calls T036 logic). **Prerequisites**: T002 (Baseline) must be completed and metrics present in `results/trajectory.json` before execution. **CRITICAL**: T048 MUST explicitly verify that `results/trajectory.json` contains a valid entry for Cycle 0 before proceeding. If missing, T048 MUST fail immediately. **Dependency**: Explicitly requires T002. **Note**: T048 *calls* the function implemented in T036; T036 is a foundational function implementation, not a blocking artifact prerequisite. Linear regression (T073) is NOT performed here; it is reserved for after 3 cycles. Integration test added verifying `results/trajectory.json` contains entry for Cycle 0 before T048 runs.

## Phase 4: User Story 2 – Three Refinement Cycles (Priority P2)

- [X] T049 [S] Extend orchestrator to repeat the refinement loop for up to three attempted cycles [UNRESOLVED-CLAIM: c_8def6bb1 — status=not_enough_info], respecting retry and early‑stop rules. Verification integration test added.
- [X] T050 [S] After all cycles, aggregate metrics into `results/trajectory.json` (cycle number, parameter count, benchmark scores, FLOPs, training time). Verification test added.
- [X] T075 [S] Implement `update_state_file` to hash artifacts (model.pt, trajectory.json) and record per‑cycle hashes in `state/cycle_N.yaml`. Verification test added: verify hash in `state/cycle_N.yaml` matches artifact hash of `model.pt`.
- [X] T074 [S] Implement `record_resource_metrics` that writes peak RAM and total wall‑clock time to `results/trajectory.json` and `results/final_report.md`. Depends on T004a and T114. Runs sequentially after T050 to append resource metrics. Verification test added.

## Phase 5: User Story 3 – Resource‑Performance Trade‑off (Priority P3)

- [X] T071 [S] Compute performance‑per‑FLOP and performance‑per‑hour metrics for each cycle and append to `results/trajectory.json`. Verification test added.
- [X] T114 [S] Record peak RAM usage from T004 into `results/trajectory.json` and `results/final_report.md`. This task explicitly satisfies SC-005's requirement to measure and report peak RAM. Verification test added: `grep -q "peak_ram_gb" results/trajectory.json`.
- [X] T072 [S] Generate final report summarizing trade‑off analysis, including tables and compliance with SC-target metrics. Verification test added.

## Phase 6: Documentation & Philosophical Synthesis (Review Response)

**Purpose**: Address specific concerns from research-stage reviews regarding authority, fixed-points, scaling laws, and computational irreducibility. This phase generates the final research report linking experimental results to Success Criteria.

**Prerequisites**: Phase 0 tasks (T000) must be completed to ensure definitions are in place.

- [X] T123 [S] Create `docs/final_report.md` from scratch. This file MUST include a placeholder structure for the final synthesis. **Depends on**: T000 (indirectly via T099). Verification: `test -f docs/final_report.md`.
- [X] T115 [S] Generate `docs/final_report.md` synthesizing the 3-cycle trajectory analysis, trade-off metrics, and compliance with SC-003 (Trajectory Persistence), SC-004 (Cost-Effectiveness), and SC-005 (Feasibility). Explicitly map findings to the original research question and address the "External Oracle" and "Fixed-Point" protocols defined in `research.md` (T000) and linked to FR-021. **CRITICAL**: This task MUST also include the "Bird vs. Frog" analysis, "Source of Authority", "Fixed-Point Problem", "Scaling Law Analysis", "Computational Irreducibility", "Recursive Adaptation", "Overfitting", "Minimality Search", "Thermodynamic Bounds", and "Minimality Search" concepts, addressing the specific reviewer concerns. **Depends on**: T123, T000. Verification: `grep -q "SC-003" docs/final_report.md` and `grep -q "SC-004" docs/final_report.md` and `grep -q "Bird vs. Frog" docs/final_report.md`.

## Phase 7: Addressing Research-Stage Review Concerns (New Tasks)

**Purpose**: Implement specific safeguards and documentation required by the simulated reviews (Lovelace, Turing, Von Neumann, etc.) to ensure the system is not merely executing a pre-ordered sequence but is rigorously tested for genuine improvement.

- [ ] T124 [S] [Review] Implement "Authority Trace" logging in `utils/logging.py`. Every modification proposal must log the chain of authority: the specific benchmark score used, the oracle check result, and the human-defined constraint (e.g., "Parameter limit from research.md"). This addresses the "Source of Authority" concern raised by Ada Lovelace and John Von Neumann. **Depends on**: T009. Verification: Log output must contain "Authority Trace" and the specific metric value.
- [X] T125 [S] [Review] Implement "Curriculum Lock" mechanism in `pipeline/evaluator.py`. Ensure the benchmark suite (GSM8K, ARC, BoolQ) is loaded from a read-only, immutable source and cannot be altered by the model's proposal generation logic. This addresses Alan Turing's concern about the machine selecting its own curriculum. **Depends on**: T010. Verification: Unit test attempts to modify benchmark config during proposal generation and asserts failure.
- [X] T126 [S] [Review] Implement "Rollback & Verification" state machine in `pipeline/attempt_tracker.py`. If a cycle fails the "External Oracle Check", the system MUST log a "Rollback Event", increment the cycle counter, and proceed to the next cycle with a NEW modification. **CRITICAL**: If the cycle results in degradation >= 5% from baseline, the system MUST terminate the pipeline (do not proceed to next cycle), strictly adhering to FR-015. **Note**: This task does NOT revert model weights; it ensures the cycle counter advances and a new modification is attempted, strictly adhering to FR-012. **CRITICAL**: T126 MUST verify that T044 and T036 are completed and functional before T126 logic is invoked. **Depends on**: T044, T036. Verification: Integration test simulates a degradation event and verifies pipeline termination.
- [X] T127 [S] [Review] Implement "Computational Irreducibility" report generator in `pipeline/trajectory.py`. This task adds a section to the trajectory analysis that explicitly states: "No closed-form prediction exists for this trajectory; results are empirically derived." It must also plot the "Rule Space Exploration" (number of distinct modification types vs. performance gain). **Definition**: 'Distinct modification types' are defined as unique combinations of (layer_type_change, param_change_category). This satisfies Stephen Wolfram's request for rule-space enumeration. **Depends on**: T050. Verification: `results/trajectory.json` includes a `computational_irreducibility_note` field.
- [X] T128 [S] [Review] Implement "Thermodynamic Bounds" calculator in `pipeline/trainer.py`. Compute performance-per-FLOP and performance-per-hour ratios as required by SC-004. **Note**: This task strictly implements the metrics defined in SC-004 (accuracy / FLOPs, accuracy / hours) and does NOT implement a 'super-linear' flag or 'Geoffrey West' logic. **Depends on**: T017b, T071. Verification: `results/trajectory.json` includes `performance_per_flop` and `performance_per_hour`.
- [X] T129 [S] [Review] Implement "Minimality Search" heuristic in `models/modifier.py`. Before applying a complex modification (e.g., adding layers), the system MUST first attempt the simplest valid modification (e.g., hyperparameter tweak or single neuron count change) and log why the complex one was chosen. This addresses Stephen Wolfram's "simplest rule" and David Krakauer's "novelty vs. fit" concerns. **Depends on**: T016. Verification: Log shows "Attempting minimal modification first" before complex proposal.
- [X] T130 [S] [Review] Implement "Fixed-Point Convergence" detector in `pipeline/attempt_tracker.py`. If three consecutive cycles yield no statistically significant improvement (p > 0.05) and parameter count is increasing, the system MUST terminate and report "Fixed Point Reached: No further improvement detected". This addresses John Von Neumann's "convergence" and "infinite regress" concerns. **Depends on**: T007, T049. Verification: Integration test simulates 3 stagnant cycles and asserts early termination.

## Phase 8: Scaling & Complexity Analysis (New Tasks for Reviewers West & Krakauer)

**Purpose**: Explicitly address concerns regarding scaling laws, diminishing returns, and the distinction between optimization and adaptation raised by Geoffrey West and David Krakauer.

- [ ] T131 [S] [Review] Implement "Scaling Law Analyzer" in `pipeline/trajectory.py`. Calculate the exponent of the power-law relationship between iteration count and performance gain (Δperformance vs. cycle). Plot this against the theoretical sublinear (exponent < 1) and superlinear (exponent > 1) bounds. Explicitly report if the system hits a "wall of diminishing returns" as predicted by West's scaling theory. **Depends on**: T050, T128. Verification: `results/trajectory.json` includes `scaling_exponent` and `scaling_regime` (sublinear/superlinear/linear).
- [ ] T132 [S] [Review] Implement "Adaptation vs. Optimization" classifier in `pipeline/evaluator.py`. Analyze whether performance gains are due to better fitting the training distribution (optimization) or improved generalization to out-of-distribution benchmarks (adaptation). Use the gap between training loss and benchmark accuracy as a proxy. **Depends on**: T018, T017a. Verification: Log output includes `adaptation_score` and `optimization_score`.
- [ ] T133 [S] [Review] Generate "Complexity vs. Capability" report in `docs/final_report.md`. Explicitly address David Krakauer's concern about "runaway complexity without corresponding gains". Include a table showing parameter count, FLOPs, and benchmark accuracy for each cycle. If parameter count increases >10% without significant accuracy gain (p < 0.05), flag as "Maladaptive Complexity". **Depends on**: T050, T131. Verification: `docs/final_report.md` contains "Maladaptive Complexity" section if triggered.
- [ ] T134 [S] [Review] Implement "Bird vs. Frog" heuristic in `code/config.py`. Allow the user to toggle between "Frog" mode (strictly refining within the transformer paradigm, no architectural type changes) and "Bird" mode (allowing fundamental architectural shifts as per Freeman Dyson's suggestion). Log which mode was active for each cycle. **Depends on**: T000. Verification: `results/trajectory.json` includes `mode` (bird/frog) for each cycle.

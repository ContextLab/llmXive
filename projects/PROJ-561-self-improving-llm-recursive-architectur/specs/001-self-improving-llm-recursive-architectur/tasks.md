# Tasks: Self-improving LLM: recursive architecture refinement and re‑training

**Input**: Design documents from `/specs/001-self-improving-llm-recursive-architectur/`  
**Prerequisites**: `plan.md`, `spec.md`, `data-model.md`, `contracts/` (research.md and final_report.md are generated artifacts)

## Phase 0: Research Design & Documentation (Prerequisites)

- [X] T000 [S] Create `research.md` from scratch. This file **MUST** include the following sections:  
  1. `## Methodology for Parameter Limit` (describing how the limit is determined, explicitly stating the limit is 30% above baseline as mandated by FR-003).  
  2. `## External Oracle Protocol` (defining the immutable evaluation metric, explicitly stating: “Reject if new_params significantly exceed baseline.”).  
  3. `## Philosophical & Operational Definitions` (covering Source of Authority, Fixed‑Point, Scaling Laws, Computational Irreducibility, Recursive Adaptation, Overfitting, Minimality Search, Thermodynamic Bounds, Bird vs. Frog).  
  **Verification**: `grep -q "## Methodology for Parameter Limit" research.md` **AND** `grep -q "## External Oracle Protocol" research.md` **AND** `grep -q "## Philosophical & Operational Definitions" research.md`.

- [X] T005b [S] Implement exponential‑backoff wrapper `exponential_backoff` (initial_delay = 30 s, max_retries = 5). **Verification**: unit test added in `tests/unit/test_backoff.py`.

- [ ] T001c [S] Implement **Pre‑flight URL Verification** in `utils/data_loader.py` (`verify_urls(urls: List[str])`). Raises an error on unreachable URLs and implements FR‑011 exponential back‑off using the wrapper from T005b. **Verification**: unit test added in `tests/unit/test_data_loader.py`.

- [ ] T001d [S] Implement **Data Download & Checksumming** (`download_and_checksum(dataset_name, dest_path)`). Writes a SHA‑256 hash file alongside the downloaded data. **Verification**: unit test added in `tests/unit/test_data_loader.py`.

- [X] T001e [S] Implement **Random Seed Pinning** in `code/utils/random.py` to ensure reproducibility (Constitution I). **Verification**: unit test asserts that `random.seed`, `np.random.seed`, and `torch.manual_seed` are called with the seed from `config.py`.

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 [S] Create project directory layout (`code/`, `code/tests/`, `code/tests/unit/`, `code/tests/integration/`, `data/raw/`, `data/processed/`, `results/`, `state/`) and add `__init__.py` files.  
  **Verification**: `python -c "import os; assert os.path.exists('code/tests/unit/__init__.py') and os.path.isdir('data/raw') and os.path.isdir('results') and os.path.isdir('state')"`.

- [X] T001f [S] Author `data-model.md` documenting the entities and data flow defined in the project plan. **Verification**: `test -f data-model.md`.

- [X] T001g [S] Author `quickstart.md` providing instructions for running the pipeline. **Verification**: `test -f quickstart.md`.

- [ ] T008 [S] Create `config.py` with hyper‑parameters (lr = 5e‑5, bs = 4, seed). `MAX_PARAM_INCREASE_RATIO` MUST be capped at 0.30 as per FR-003; any value read from `research.md` exceeding 0.30 MUST be clamped to 0.30. **Verification**: import `config` and assert `MAX_PARAM_INCREASE_RATIO <= 0.30`.

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T001a [P] Unit test for `verify_urls` (see `tests/unit/test_data_loader.py`).  
- [ ] T001b [P] Unit test for `download_and_checksum` (see `tests/unit/test_data_loader.py`).  
- [ ] T005a [P] Implement dataset loaders for OpenWebText, GSM8K, ARC‑Challenge, BoolQ with fail‑fast logic and streaming support; use back‑off from T005b. **Verification**: ensure training and eval splits are disjoint and generate `data/disjoint_check_report.json`.  
- [ ] T006 [P] Implement `models/loader.py` CPU‑only loader for the GPT‑2 checkpoint. **Verification**: `device='cpu'` after load.  
- [ ] T013 [P] Define `ModificationProposal` Pydantic schema. **Verification**: schema validation unit test.  
- [ ] T014b [P] Implement `validate_schema(proposal)` using the schema. **Verification**: unit test.  
- [ ] T019 [S] Implement **Parameter Constraint Check** (`check_parameter_constraint`). Validates `new_params <= baseline_params * 0.30` as mandated by FR-003. **Verification**: unit test.  
- [ ] T059 [S] Implement **External Oracle** (`validate_external_oracle`) enforcing the parameter limit and structural validity. **Verification**: unit test.  
- [ ] T020 [S] Implement **Distinctness Validator** (`validate_distinctness`) ensuring Hamming distance ≥ 1 or >5 % parameter change versus history. **Verification**: unit test.  
- [ ] T007 [P] Implement paired bootstrap statistical testing (`run_bootstrap_test`) with Bonferroni correction (α = 0.05). **Verification**: unit test.  
- [ ] T073 [P] Implement linear‑regression trend analysis (`run_regression_analysis`). **Verification**: unit test.  
- [ ] T009 [P] Implement structured JSON logging for cycles (`pipeline/logging.py`). **Verification**: log file creation test.  
- [ ] T010 [P] Implement benchmark evaluator for GSM8K, ARC‑Challenge, BoolQ. **Verification**: unit test.  
- [ ] T017c [P] Implement FLOP counter (`calculate_flops`) using `torch.profiler`. **Verification**: unit test.  
- [ ] T004 [P] Implement RAM monitoring (`check_ram_usage(limit_gb)`) that records peak RAM usage. **Verification**: unit test.  
- [ ] T004a [P] Implement RAM feasibility check (`enforce_ram_limit`). If peak RAM > 7 GB, writes `results/feasibility_status.json` with status “infeasible” and flags the run. **Verification**: unit test.  
- [ ] T011 [P] Unit test `tests/unit/test_memory.py::test_check_ram_usage_logs_warning`.  
- [ ] T012 [P] Unit test `tests/unit/test_loader.py::test_exponential_backoff_initial_delay`.  
- [ ] T014c [P] Unit test `tests/unit/test_model.py::test_generate_proposal_excludes_benchmark_data`.  
- [ ] T002 [S] Implement **Baseline Capability Check** (`run_baseline_check`) that evaluates the unmodified model on all benchmarks, writes Cycle 0 metrics to `results/trajectory.json`, and flags near‑random performance (<10 % on GSM8K/ARC). **Verification**: integration test ensures Cycle 0 entry exists.

## Phase 3: User Story 1 – Single Refinement Cycle (Priority P1)

- [ ] T015 [S] Implement `generate_proposal` that prompts the model, renders `templates/modification_proposal.j2`, and returns a validated `ModificationProposal`. Delegates validation to schema, oracle, and distinctness validators only. **Verification**: unit test mocks validators and asserts they are called.  
- [ ] T016 [S] Implement `apply_modification` that creates a new model instance per proposal (layer_add, head_count_change, hidden_size_change, activation_change) and maps existing weights. **Verification**: unit test.  
- [ ] T017a [S] Implement training loop `train_epoch` (AdamW, bs = 4, lr = 5e‑5, 1 epoch) on OpenWebText subset. Saves model to `results/cycle_N/model.pt`. Includes time‑estimation and deterministic subset‑reduction fallback if estimated time > 2 h. **Verification**: `tests/unit/test_trainer.py::test_epoch_loss_convergence`.  
- [ ] T017b [P] Integrate FLOP counting via `calculate_flops`. **Verification**: unit test.  
- [ ] T018 [S] Implement evaluation logic for GSM8K, ARC‑Challenge, BoolQ; store accuracies/ECE. **Verification**: unit test.  
- [ ] T044 [S] Implement training‑retry logic: up to 2 retries per cycle; after 2 failures log the failure, increment the cycle counter, and proceed with a new modification. **Verification**: `tests/unit/test_attempt_tracker.py::test_retry_fails_after_2_attempts`.  
- [ ] T036 [S] Implement **Early Termination Check** (`check_termination`). If performance degradation ≥ 5 % from baseline, terminate the pipeline immediately. **Verification**: unit test.  
- [ ] T048 [S] Orchestrate a single refinement cycle: invoke proposal generation, validation, modification, training, FLOP counting, evaluation, statistical analysis, logging, and termination checks. **Prerequisite**: T002 must have produced a valid Cycle 0 entry in `results/trajectory.json`. **Verification**: integration test that aborts if Cycle 0 entry is missing.

## Phase 4: User Story 2 – Three Refinement Cycles (Priority P2)

- [ ] T049 [S] Extend orchestrator to repeat the refinement loop for up to three attempted cycles, respecting retry and early‑stop rules. **Verification**: integration test that ensures at most three cycles are recorded.  
- [ ] T050 [S] After all cycles, aggregate metrics into `results/trajectory.json` (cycle number, parameter count, benchmark scores, FLOPs, training time). **Verification**: test that the JSON conforms to `trajectory.schema.yaml`.  
- [ ] T075 [S] Implement `update_state_file` to hash artifacts (`model.pt`, `trajectory.json`) and record per‑cycle hashes in `state/cycle_N.yaml`. **Verification**: test that the hash in the YAML matches the actual file hash.  
- [ ] T074 [S] Implement `record_resource_metrics` that writes peak RAM and total wall‑clock time to `results/trajectory.json` and `results/final_report.md`. Depends on T004a. **Verification**: test that `peak_ram_gb` appears in `results/trajectory.json`.

## Phase 5: User Story 3 – Resource‑Performance Trade‑off (Priority P3)

- [ ] T071 [S] Compute performance‑per‑FLOP and performance‑per‑hour metrics for each cycle and append them to `results/trajectory.json`. **Verification**: unit test checks the fields `perf_per_flop` and `perf_per_hour` exist for every cycle.  
- [ ] T114 [S] Record peak RAM usage from T004 into `results/trajectory.json` and `results/final_report.md`. **Verification**: `grep -q "peak_ram_gb" results/trajectory.json`.  
- [ ] T072 [S] Generate final report summarizing trade‑off analysis, including tables and compliance with SC‑003, SC‑004, SC‑005. **Verification**: `grep -q "SC-003" docs/final_report.md` and similar for SC‑004 and SC‑005.

## Phase 6: Documentation & Philosophical Synthesis (Review Response)

- [ ] T123 [S] Create `docs/final_report.md` placeholder structure. **Verification**: `test -f docs/final_report.md`.  
- [ ] T115 [S] Populate `docs/final_report.md` with synthesis of the 3‑cycle trajectory, trade‑off metrics, and mapping to SC‑003, SC‑004, SC‑005. Include all reviewer‑requested conceptual sections (Bird vs. Frog, Source of Authority, Fixed‑Point, Scaling Law Analysis, Computational Irreducibility, Recursive Adaptation, Overfitting, Minimality Search, Thermodynamic Bounds). **Verification**: grep for each required heading.

## Phase 7: Addressing Research‑Stage Review Concerns (New Tasks)

- [ ] T124 [S] Implement **Authority Trace** logging in `utils/logging.py`. Every modification proposal must log a JSON line containing: `benchmark_score`, `oracle_result`, and `parameter_limit` (sourced from `research.md`). Provide helper `log_authority_trace(event: dict)` that writes to `results/logs/authority_trace.log`.  
  **Verification**: unit test `tests/unit/test_logging.py::test_authority_trace` asserts that after a mocked proposal the log file exists and contains the required keys; an integration test runs a single cycle and checks that `authority_trace.log` has at least one entry.

- [ ] T125 [S] Implement **Curriculum Lock** in `pipeline/evaluator.py` to ensure the benchmark suite is loaded from a read‑only source and cannot be altered by proposal generation. **Verification**: unit test attempts to modify benchmark config during proposal generation and expects a failure.

- [ ] T126 [S] Implement **Rollback & Verification** state machine in `pipeline/attempt_tracker.py`. On an external‑oracle rejection, log a “Rollback Event”, increment the cycle counter, and start the next cycle with a new modification. If degradation ≥ 5 % from baseline, terminate the pipeline (as per FR‑015). Depends on T044 and T036. **Verification**: integration test simulates a degradation event and asserts pipeline termination.

- [ ] T127 [S] Implement **Computational Irreducibility** report generator in `pipeline/trajectory.py`. Add a field `computational_irreducibility_note` to `results/trajectory.json` with the sentence “No closed‑form prediction exists for this trajectory; results are empirically derived.” Also plot “Rule Space Exploration” (distinct modification types vs. performance gain). **Verification**: unit test checks the JSON field exists.

- [ ] T128 [S] Implement **Thermodynamic Bounds** calculator in `pipeline/trainer.py`. Compute and store `performance_per_flop` and `performance_per_hour` (as defined in SC‑004) in `results/trajectory.json`. **Verification**: unit test confirms the fields are present and correctly calculated.

- [ ] T129 [S] Implement **Minimality Search** heuristic in `models/modifier.py`. Before applying a complex modification, attempt the simplest valid modification first; log the decision with a message “Attempting minimal modification first”. **Verification**: unit test checks log contains the minimal‑modification message prior to any complex change.

*All checked tasks have already been verified. The unchecked tasks above constitute the remaining scientific work required to complete the study and satisfy the specification.*
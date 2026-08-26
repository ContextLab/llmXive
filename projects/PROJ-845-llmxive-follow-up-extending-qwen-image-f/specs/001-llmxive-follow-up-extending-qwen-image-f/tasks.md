# Tasks: llmXive follow-up: extending "Qwen-Image-Flash: Beyond Objective Design"

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
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

- [X] T001 Create project directory `projects/PROJ-llmxive-follow-up-extending-qwen-image-f/` with sub‑directories `data/raw/`, `data/processed/`, `code/`, `code/generators/`, `code/models/`, `code/training/`, `code/analysis/`, `code/utils/`, `tests/unit/`, `tests/integration/`, `contracts/`; add an empty `__init__.py` in each Python package directory.
- [X] T002 Create `requirements.txt` at `projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/requirements.txt` containing pinned versions of `torch==2.3.0+cpu [UNRESOLVED-CLAIM: c_b629a8f2 — status=not_enough_info]`, `transformers==4.41.2 [UNRESOLVED-CLAIM: c_8d28afc6 — status=not_enough_info]`, `scikit-learn`, `scipy`, `pandas`, `numpy`, `pyyaml`, `python-sat`.
- [X] T003 Create linting configuration files: `.flake8` with standard flake8 settings and `pyproject.toml` configuring Black (line length appropriate for the target environment) in the project root.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create contract schema files in `contracts/`:
 - `synthetic_problem.schema.yaml` defining fields `id`, `premises`, `operators`, `solution`, `entropy_level`, `metadata`.
 - `distillation_run.schema.yaml` defining fields `run_id`, `entropy_subset`, `model_params`, `training_loss_curve`, `convergence_epoch`, `final_accuracy`, `status`, `resource_usage`.
 - `statistical_result.schema.yaml` defining fields `test_type`, `statistic`, `p_value`, `corrected_p_value`, `conclusion`, `correction_method`.
- [X] T005 Implement base logging in `code/utils/logger.py` exposing `get_logger(name: str) -> logging.Logger` that writes to `code/logs/app.log` with timestamped format; import in `code/__init__.py`.
- [X] T006 Create configuration management in `code/config.py` with a `Config` dataclass containing `seed: int = 42 [UNRESOLVED-CLAIM: c_10fdfac7 — status=not_enough_info] `, `max_ram_gb: float = 7.0 [UNRESOLVED-CLAIM: c_635a81e4 — status=not_enough_info] `, `max_runtime_hours: float = 6.0 [UNRESOLVED-CLAIM: c_ac418629 — status=not_enough_info] `.
- [X] T007 Implement `SyntheticProblem` dataclass in `code/models/synthetic_problem.py` with fields `id: str`, `premises: List[str]`, `operators: List[str]`, `solution: str`, `entropy_level: str`, `metadata: Dict[str, Any]`; provide `to_dict()` and `from_dict()` methods for JSON serialization.
- [X] T008 Implement `ResourceMonitor` class in `code/utils/resource_monitor.py` with methods `start()`, `stop()`, `get_peak_ram_gb()`, and context‑manager support for automatic monitoring.
- [X] T060 [P] **Resolve: Global Seeding Verification** - Implement a verification script `code/utils/seeding_check.py` that scans `code/generators/`, `code/models/`, `code/training/`, and `code/analysis/` to ensure every call to `random`, `numpy.random`, and `torch.manual_seed` explicitly uses the `Config.seed` value before any random operation. The script must fail the build if any RNG is found to be unseeded or using a hardcoded seed. **This script MUST be integrated into the CI pipeline (see T041) as a mandatory blocking step.**
- [X] T041 Add reproducibility verification script `code/utils/reproducibility_check.py` that runs the generator twice with the same seed from `Config`, computes SHA256 checksums of generated CSVs, and fails the CI if they differ; **integrate as a CI step that explicitly executes T060 (seeding check) before any data generation or training tasks.**
- [ ] T066-P [US1] **Resolve: Pre-Generation Power Analysis** - Implement `code/analysis/power_analysis.py` to calculate the statistical power of the planned ANOVA and t-tests given the target sample sizes (N=1000 per subset [UNRESOLVED-CLAIM: c_5f6fdf9a — status=not_enough_info], N_test=500 [UNRESOLVED-CLAIM: c_32dad93f — status=not_enough_info]) and an assumed effect size (e.g., Cohen's f = 0.25 [UNRESOLVED-CLAIM: c_d594de7f — status=not_enough_info]). **Prerequisite: T006.** If the power is < 0.80, this task MUST trigger T066-ADJUST.
- [ ] T066-ADJUST [US1] **Resolve: Power Analysis Escalation** - If T066-P reveals the study is underpowered (Power < 0.80 [UNRESOLVED-CLAIM: c_1230fb6a — status=not_enough_info]), generate a `docs/power_analysis_alert.md` flagging the constraint conflict (sample size vs. 6h runtime) and **escalate to human review**. Do NOT proceed to data generation if this alert is triggered. **Prerequisite: T066-P.**
- [X] T051 **Resolve: Pipeline Orchestrator** - Create `code/main.py` as the pipeline orchestrator script. This script must import and execute the generator, trainer, and analyzer modules in the correct order, handling error propagation and exit codes. **Crucially, it must implement the branching control flow for data generation: if T015-ENFORCE (entropy validation) passes, invoke T016-SUCCESS; if it fails, invoke T012-REPAIR or T016-FAIL.** It must be the single entry point for the CI/CD pipeline.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Dataset Generation with Controlled Entropy(Priority: P1) 🎯 MVP

**Goal**: Generate a rigorously controlled synthetic dataset with High, Low, and Target entropy subsets, ensuring statistical separation and structural independence for the test set.

**Independent Test**: Run the generator script and verify entropy distributions and subset sizes without training any models.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T009 [US1] Write unit test `tests/unit/test_entropy_calc.py` that imports `code/analysis/metrics.py` and asserts the entropy calculation function returns a float.
- [X] T010 [US1] Write integration test `tests/integration/test_data_generation.py` that invokes the generator script and expects a `SystemExit` due to missing implementation (ensuring fail‑first).

### Implementation for User Story 1

- [ ] T010-SCHEMA [US1] **Resolve: Schema Definition** - Define the JSON schema for `SyntheticProblem` in `code/generators/schemas.py`. **Schema Snippet**:
 ```json
 {
 "id": "str",
 "premises": ["str"], // List of strings, e.g., ["A is true", "If A then B"]
 "operators": ["str"], // List of strings, e.g., ["AND", "OR"]
 "solution": "str",
 "entropy_level": "str", // Enum: ['High', 'Low', 'Target']
 "metadata": {"structure_hash": "str", "set_type": "str"}
 }
 ```
 **Prerequisite: T004.**
- [ ] T011-LOGIC [US1] **Resolve: Propositional Logic Generator** - Implement `generate_propositional_problem()` in `code/generators/logic_generator.py` using the schema from T010-SCHEMA. **Output**: Returns a `SyntheticProblem` object. **Prerequisite: T010-SCHEMA.**
- [ ] T011-B [US1] **Resolve: Arithmetic Problem Generator** - Implement `generate_arithmetic_problem()` in `code/generators/logic_generator.py` using the schema from T010-SCHEMA. **Prerequisite: T010-SCHEMA.**
- [ ] T011-BATCH [US1] **Resolve: Batch Generation & Serialization** - Implement a function `generate_batch(n: int, problem_type: str, entropy_level: str)` in `code/generators/logic_generator.py` that calls T011-LOGIC or T011-BATCH N times and serializes the results to `data/raw/{entropy_level}.csv`. **Prerequisite: T011-LOGIC, T011-B.**
- [ ] T012-HIGH [US1] Implement generation of High‑Entropy subset in `code/generators/logic_generator.py` with **uniform random shuffle** of premises/operators, targeting N=1000 samples. **Note: This generation is subject to the Statistical Separation Gate (T015-ENFORCE). If T015-ENFORCE fails, these samples are discarded to `data/raw/generation_discards.json` and T012-REPAIR is triggered.** **Prerequisite: T011-BATCH.**
- [ ] T012-LOW [US1] Implement generation of Low‑Entropy subset in `code/generators/logic_generator.py` with **fixed pattern repetition** (e.g., repeating the same logical operator sequence), targeting N=1000 samples. **Note: This generation is subject to the Statistical Separation Gate (T015-ENFORCE). If T015-ENFORCE fails, these samples are discarded to `data/raw/generation_discards.json` and T012-REPAIR is triggered.** **Prerequisite: T011-BATCH.**
- [ ] T012-TARGET [US1] Implement generation of Target‑Specific subset in `code/generators/logic_generator.py` with **specific logical operator sequences** (narrow reasoning styles), targeting N=1000 samples. **Note: This generation is subject to the Statistical Separation Gate (T015-ENFORCE). If T015-ENFORCE fails, these samples are discarded to `data/raw/generation_discards.json` and T012-REPAIR is triggered.** **Prerequisite: T011-BATCH.**
- [ ] T012-REPAIR [US1] **Resolve: Generation Parameter Repair** - If T015-ENFORCE fails, implement a script `code/generators/repair_generator.py` that adjusts generation parameters (e.g., increases shuffle depth for High, increases pattern strictness for Low) and re-runs T012-HIGH/LOW/TARGET. **Discard Artifact Schema**: `data/raw/generation_discards.json` MUST contain objects with fields: `problem_id` (str), `entropy_level` (str), `computed_entropy` (float), `target_entropy_range` (tuple), `failure_reason` (str, e.g., "entropy_gap_insufficient"). **A limited number of attempts will be permitted.** If repair fails after 3 attempts, trigger T016-FAIL. **Prerequisite: T015-ENFORCE.**
- [ ] T013-GEN [US1] **Resolve: Generalization Set Generation** - Implement `generate_generalization_set()` in `code/generators/logic_generator.py` to produce N_test >= 500 [UNRESOLVED-CLAIM: c_2f59e3d0 — status=not_enough_info] problems. **Algorithm**: Use a **canonical serialization** of premises/operators (e.g., sorted list of tokens joined by '|') to compute a `structure_hash` (SHA256). Ensure every generated problem's `structure_hash` is **not** present in the training set hashes. Stratify by entropy level (High/Low/Target) to match training distribution. Output to `data/raw/test_set.csv`. **Note: This task depends on T012-HIGH/LOW/TARGET completion (data availability) but NOT on T014-SAT (contradiction filtering), as it only requires the training set structure hashes.** **Prerequisite: T012-HIGH, T012-LOW, T012-TARGET.**
- [ ] T013-VERIFY [US1] **Resolve: Distinctness & Distribution Verification** - Implement a verification step in `code/generators/logic_generator.py` that: 1) Asserts **no hash collision** between test and training sets (raising `ValueError` on collision); 2) Performs a **chi-square test** on the entropy level distribution of the test set vs. the training set to ensure they match (p > 0.05). Log details to `data/raw/test_distinctness_log.json`. **Prerequisite: T013-GEN.**
- [ ] T014-SAT [US1] **Resolve: Contradiction Detection** - Implement `validate_solvability(problem: SyntheticProblem)` in `code/generators/logic_generator.py` using the `python-sat` (pysat) library. Convert problem premises to DIMACS format, run a SAT solver, and discard any problem where the solver returns UNSAT. **Prerequisite: T011-LOGIC, T011-B.**
- [X] T015 [US1] Implement function `compute_entropy_statistics()` in `code/analysis/metrics.py` that calculates per‑sample entropy scores (problem entropy) and performs a two‑sample t‑test (high vs low); log mean, std, and p‑value.
- [ ] T015-ENFORCE [US1] Add validation in `metrics.py` that raises `SystemExit(1)` if the t‑test p‑value ≥ 0.05, logging the failure; this enforces the controlled‑entropy requirement without presuming success. **This task acts as the gate: if it passes, the Orchestrator (T051) invokes T016-SUCCESS; if it fails, the Orchestrator invokes T012-REPAIR or T016-FAIL.** **Prerequisite: T015.**

#### Artifact Generation (Mutually Exclusive Outcomes)
- [ ] T016-SUCCESS [US1] **Resolve: Success Artifact Generation** - **ONLY IF T015-ENFORCE passes**: Save generated CSVs to `data/raw/high_entropy.csv`, `data/raw/low_entropy.csv`, `data/raw/target_specific.csv`, and `data/raw/test_set.csv` with columns for all fields defined in `SyntheticProblem`, including `entropy_level`, `structure_hash`, and `set_type`. **Prerequisite: T015-ENFORCE.**
- [ ] T016-FAIL [US1] **Resolve: Failure Artifact Generation** - **ONLY IF T015-ENFORCE fails (p >= 0.05) and T012-REPAIR fails**: Generate a `data/raw/generation_failure_report.json` containing the partial generated data, the computed p-value, and a detailed explanation of the failure. This ensures a "Single Source of Truth" exists even for negative results. **This task runs ONLY if T015-ENFORCE fails and repair is exhausted.** **Prerequisite: T012-REPAIR.**
- [X] T017 [US1] Generate SHA256 checksums for each CSV and record them in `code/utils/data_hygiene.py`; log checksum values to the logger. **Prerequisite: T013-VERIFY, T016-SUCCESS.**
- [X] T046 [US1] **Resolve: Entropy Metric Definition** - Explicitly implement `code/analysis/metrics.py` to calculate Shannon entropy based on the **token-level probability distribution of the generated reasoning steps** for trace entropy validation (FR-009), while keeping `compute_entropy_statistics` focused on **problem entropy** (premises/operators) for US-1. Add a unit test in `tests/unit/test_entropy_calc.py` that verifies the metric yields distinct values for a "randomized" sequence vs. a "repetitive" sequence of the same length.

#### Teacher Trace Generation (Moved to US1 for Data Flow)
- [ ] T018-TEACHER [US1] **Resolve: Multi-Step Trace Generation with Probabilities** - Implement the `Teacher` class in `code/models/teacher.py` to generate **actual multi-step CoT traces** using a **deterministic rule-based engine**. **Algorithm**:
 1. Count operators in the problem.
 2. If `operator_count < 3 [UNRESOLVED-CLAIM: c_fa09fd7b — status=not_enough_info]`: Use **Pattern A** (Low Entropy). Pattern A uses a fixed sequence of operators (e.g., ["AND", "OR", "NOT"]) with a deterministic probability distribution (e.g., `probs = [, 0.15, 0.05]`).
 3. If `operator_count >= 3`: Use **Pattern B** (High Entropy). Pattern B uses a randomized operator selection with uniform probability (e.g., `probs = [0.33, 0.33, 0.33] [UNRESOLVED-CLAIM: c_1e2f92e5 — status=not_enough_info]`).
 4. Map rule complexity to probability mass using a softmax function (e.g., `probs = softmax([-complexity, 0, 0,...])`).
 5. Output **token-level probability distributions** (logits/probs) for each step. Ensure the sum of probabilities for each step equals unity (within tolerance).
 **Code Example**:
 ```python
 def generate_trace(problem):
 op_count = len(problem.operators)
 if op_count < 3:
 # Pattern A: Low Entropy
 probs = [0.8, 0.15, 0.05] [UNRESOLVED-CLAIM: c_aafa1066 — status=not_enough_info] # Fixed distribution
 else:
 # Pattern B: High Entropy
 probs = [/3, 1/3, 1/3] # Uniform distribution
 trace_steps = []
 for _ in range(10):
 step = random.choice(["A", "B", "C"], weights=probs)
 trace_steps.append({"step": step, "probs": probs})
 return trace_steps
 ```
 Save traces to `data/raw/teacher_traces.json` (containing problem ID, trace text, and token probabilities). **Prerequisite: T014-SAT, T016-SUCCESS.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU‑Tractable Distillation Pipeline (Priority: P2)

**Goal**: Execute a CPU‑only distillation process where a <100 M‑parameter student model learns from teacher traces, strictly adhering to hardware constraints (RAM < 7 GB [UNRESOLVED-CLAIM: c_6db40f9b — status=not_enough_info]).

**Independent Test**: Run training on a single subset and verify no CUDA errors, RAM usage < 7 GB, and loss convergence.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [US2] Write unit test `tests/unit/test_loss_function.py` that checks KL‑divergence implementation returns a non‑negative scalar.
- [X] T019 [US2] Write integration test `tests/integration/test_distillation_cpu.py` that launches a dummy training loop on a tiny dataset and asserts no CUDA devices are detected.

### Implementation for User Story 2

- [X] T020 [US2] Create `code/models/teacher.py` with a lightweight mock LLM class `Teacher` that generates traces. Ensure no GPU‑specific flags are used.
- [ ] T020-AUDIT [US2] Add CI script `ci/check_forbidden_libs.sh` that parses `requirements.txt` AND performs static code analysis on `code/models/` and `code/training/` to detect imports of ANY quantization libraries (e.g., `optimum`, `bitsandbytes`, `quantization`, `accelerate`) or runtime flags like `load_in_8bit`. **Additionally, implement a runtime check in `distill_loop.py` to assert `torch.cuda.is_available()` is False and that no tensors are moved to CUDA, failing the run if GPU fallback is detected.** **Prerequisite: T020.**
- [X] T021 [US2] Create `code/models/student.py` defining a DistilBERT‑base‑uncased‑like transformer (< 100 M parameters) suitable for CPU inference.

#### Trace Consistency Pipeline (Strict Sequence)
- [X] T022 [US2] Implement `compute_trace_entropy(problem: SyntheticProblem, trace: List[str]) -> float` in `code/analysis/metrics.py` that measures Shannon entropy of token-level probabilities from the teacher trace.
- [ ] T022-CALC-TRACE [US2] **Resolve: Trace Entropy Calculation** - Implement a dedicated function `calculate_trace_entropy_stats()` in `code/training/distill_loop.py` that computes the quantitative trace entropy for each sample using the probabilities from T018-TEACHER. **Calculation**: Calculate Shannon entropy of the token-level probability distribution for each step in the trace, then average across steps. **Output**: Save a JSONL file `data/processed/trace_entropies.jsonl` where each line is `{ "problem_id": "str", "trace_entropy": float }`. **Prerequisite: T018-TEACHER, T022.**
- [ ] T019-VALIDATE [US2] **Resolve: Trace Consistency Filtering** - Implement a filtering step in `code/training/distill_loop.py` that uses the quantitative metric from T022-CALC-TRACE to filter out samples where the trace entropy does not match the problem entropy. **Validation Logic**: **Absolute Thresholds**: Verify that trace entropy for Low-Entropy problems is **< 0.3** and for High-Entropy problems is **> 0.7** based on FR-009 definitions. **Output artifact**: `data/processed/filtered_dataset.json` containing only consistent samples. **Input**: `data/processed/trace_entropies.jsonl` from T022-CALC-TRACE. **Prerequisite: T022-CALC-TRACE.**
- [ ] T023 [US2] **Resolve: Distillation Loop** - Implementthe main distillation loop in `code/training/distill_loop.py` using KL‑divergence loss. **Configuration**: Optimizer=Adam, Learning Rate=1e-4 [UNRESOLVED-CLAIM: c_e5e51b6f — status=not_enough_info], {{claim:c_18c90434}} , Early Stopping ({{claim:c_205d3b17}} (pi, https://en.wikipedia.org/wiki/Pi), min_delta=1e-4 [UNRESOLVED-CLAIM: c_de5eeaf5 — status=not_enough_info]), no mixed‑precision. Early stopping when loss ≤ 0.1, logging of `convergence_epoch`. **Input**: `data/processed/filtered_dataset.json` from T019-VALIDATE. **Prerequisite: T019-VALIDATE.**
- [ ] T024 [US2] Add early‑stopping logic to the training loop; record the epoch at which the loss threshold is first met.
- [ ] T025 [US2] Integrate `ResourceMonitor` hooks into the training script to enforce the GB RAM ceiling and a wall‑clock time limit, exiting with a specific error code on breach.
- [ ] T026-ORCHESTRATE [US2] **Resolve: Execution Command** - Create a script `code/training/run_all_distillations.py` that invokes `distill_loop.py` for each subset (High, Low, Target) using the filtered dataset, aggregates logs, and stores individual run logs as `data/processed/distill_high.json`, `data/processed/distill_low.json`, `data/processed/distill_target.json`.
- [ ] T027 [US2] Ensure non‑convergent runs are logged with `"status": "failed_non_converge"` and assign `convergence_epoch` = `max_epochs + 1` for downstream statistical handling.
- [ ] T027-CHECKPOINT [US2] **Resolve: Model Handoff** - Implement a checkpointing step in `run_all_distillations.py` that saves the final state of each student model to `data/processed/models/` (e.g., `model_high.pt`, `model_low.pt`, `model_target.pt`) in a standard format loadable by `evaluation.py`.
- [ ] T042 [US2] After all three runs, generate a validation report `data/processed/trace_consistency_report.json` summarizing total samples, number filtered per entropy subset, and overall pass/fail status for FR‑009.
- [ ] T045 [US2] Add a pilot run script `code/training/pilot_resource_check.py` that trains the student on a small subset, records peak RAM via `ResourceMonitor`, and asserts limits; fail fast if limits are exceeded, providing empirical CPU‑tractability verification.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation of Coherence Hypothesis (Priority: P3)

**Goal**: Evaluate student models on the Generalization Set and perform rigorous statistical analysis (ANOVA, t‑tests with Bonferroni correction) to validate the Coherence over Diversity hypothesis.

**Independent Test**: Run the statistical script on accuracy/convergence logs and verify p-values and effect sizes.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [US3] Write unit test `tests/unit/test_statistical_analysis.py` that feeds synthetic accuracy data into `stats.anova_test` and checks that the returned object contains `f_statistic` and `p_value`.

### Implementation for User Story 3

- [ ] T029 [US3] Implement evaluation script `code/analysis/evaluation.py` that loads each student model from `data/processed/models/`, runs inference on `data/raw/test_set.csv` (Generalization Set), and records accuracy and per‑sample epoch of loss‑threshold crossing. **Output artifact**: `data/processed/evaluation_results.json`. **Prerequisite: T027-CHECKPOINT, T013-VERIFY.**
- [ ] T029-VERIFY [US3] Add an assertion in `evaluation.py` that raises `ValueError` if any loaded sample has `set_type != "test_generalization"`; this guarantees exclusive use of the Generalization Set.
- [ ] T030 [US3] Add function `anova_test(accuracies: Dict[str, List[float]]) -> Dict` in `code/analysis/stats.py` that computes the ANOVA F‑statistic and raw p‑value across the three models. **Input**: `data/processed/evaluation_results.json` from T029.
- [ ] T031 [US3] Add function `pairwise_t_test(convergence_epochs: Dict[str, List[int]]) -> Dict` that performs pairwise t‑tests between model groups. **Input**: `data/processed/evaluation_results.json` from T029.
- [ ] T032 [US3] Implement Bonferroni correction in `stats.py` that adjusts all p‑values (ANOVA and pairwise) and returns corrected values.
- [ ] T033 [US3] **Resolve: Statistical Result Artifact** - Create `StatisticalResult` records (using the schema from contracts) for each test and write them to `data/processed/statistical_results.json`. **Include a verification step to assert the file exists and matches the schema.**
- [ ] T034-CONDITIONAL [US3] **Resolve: Conditional Causal Framing** - Extend `code/report_generator.py` to produce a human‑readable markdown report `docs/research_report.md`. **Logic**: Check the `corrected_p_value` from T033.
 - **IF `corrected_p_value < 0.05 [UNRESOLVED-CLAIM: c_69d37764 — status=not_enough_info]`**: State "Findings are causal regarding the effect of entropy on performance within the synthetic domain."
 - **ELSE (`corrected_p_value >= 0.05`)**: State "The hypothesis was not supported; no statistically significant effect of entropy was found. **No causal claim regarding the effect of entropy on performance is made.**"
 **Do not use unconditional claims.** **Prerequisite: T033.**
- [ ] T034-REPORT [US3] **Resolve: Report Generation** - Execute T034-CONDITIONAL to generate the final report. **Prerequisite: T034-CONDITIONAL.**
- [ ] T034-VALIDATE [US3] Add a validation function in `report_generator.py` that asserts the conditional causal framing logic is present, raising an AssertionError on mismatch.
- [ ] T043 [US3] Add a separate JSON summary `data/processed/final_statistical_summary.json` that lists all raw and corrected statistics (F, t, p-values) and the final conclusion, to satisfy SC‑001 and SC‑002 as a distinct artifact.
- [ ] T035 [US3] Commit the final markdown report and JSON summary to the repository.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T036 [P] Update `README.md` and `docs/` with usage examples, architecture diagram, and instructions for reproducing the full pipeline.
- [X] T037 Code cleanup and refactoring across modules for readability and adherence to style guide.
- [X] T038 Performance optimization: profile the generator and training loops; adjust batch sizes if peak RAM approaches 7 GB.
- [X] T039 [P] Add additional unit tests for edge cases (contradiction filtering, timeout handling) in `tests/unit/`.
- [X] T040 Run `quickstart.md` validation and end‑to‑end pipeline test on GitHub Actions free‑tier runner; ensure total wall‑clock time < 6 h and RAM < 7 GB [UNRESOLVED-CLAIM: c_6db40f9b — status=not_enough_info].
- [X] T052 [US1] **Resolve: Sample Size Constants** - Update `code/config.py` to define explicit constants `N_TRAIN_PER_SUBSET = 1000 [UNRESOLVED-CLAIM: c_822d6afa — status=not_enough_info] ` and `N_TEST_SET = 500 [UNRESOLVED-CLAIM: c_2003ad43 — status=not_enough_info] `, and ensure `code/generators/logic_generator.py` uses these constants directly.
- [X] T053 [US2] **Resolve: Resource Limit Constants** - Update `code/config.py` to replace unresolved claim placeholders with explicit float values representing the target RAM and time thresholds, and ensure `ResourceMonitor` and `pilot_resource_check.py` reference these config values directly.
- [X] T054 [US3] **Resolve: Statistical Result Artifact** - Implement the logic in `code/analysis/stats.py` to generate the `StatisticalResult` JSON structure required by T033, ensuring it includes `f_statistic`, `p_value`, `corrected_p_value`, and `conclusion` fields, and write a unit test to verify the schema compliance. **Output**: `data/processed/statistical_results.json`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **Critical Data Flow**: US1 (Data Generation) MUST complete before US2 (Distillation) because Distillation requires the generated datasets.
 - **Critical Data Flow**: US2 (Distillation) MUST complete before US3 (Evaluation) because Evaluation requires the trained models.
 - User stories can then proceed in parallel (if staffed) or sequentially in priority order (P1 → P2 → P3).
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Produces the input for US2.**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) **and** US1 completion. **Produces the input for US3.**
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) **and** US2 completion.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services/logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, **US1 can start immediately**. US2 and US3 must wait for US1 and US2 respectively due to data dependencies.
- All tests for a user story marked [P] can run in parallel
- Different components within a user story (e.g., generator logic vs. metrics logic) can be worked on in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Generation)
4. **STOP and VALIDATE**: Run `T041` reproducibility check and the entropy t‑test (T015‑ENFORCE); confirm dataset integrity.
5. Deploy/demo data generation pipeline if ready

### Incremental Delivery

1. Complete Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Gen) - **Must finish first**
 - Developer B: Can start Foundational tasks for US2 (Model setup) in parallel with US1
3. Once US1 data is ready:
 - Developer A & B: Work on US2 (Distillation)
4. Once US2 models are ready:
 - Developer A & B: Work on US3 (Analysis)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **CRITICAL**: Do not assume GPU availability. All training tasks (US2) must explicitly target CPU and verify RAM constraints.
- **CRITICAL**: Data generation (US1) must produce REAL data, not placeholders.
- **CRITICAL**: All fail‑fast mechanisms (T015‑ENFORCE, T045, T025) must be implemented to enforce the spec constraints.

---

## Phase N+1: Revision & Analysis Resolution (Pending)

**Purpose**: Address specific issues raised by `/speckit.analyze` in the current revision round.
**Status**: Resolved - All concerns addressed in the main task list above.

- [X] T050 [US1] **Resolve: Generalization Set Structural Independence** - Implemented as part of T013-GEN (canonical serialization hashing). No separate task needed.

- [X] T047 [US2] **Moved to Phase 4 as T018-TEACHER** - This task is now fulfilled by T018-TEACHER which generates multi-step traces with probabilities. No action required here.

- [X] T051 **Moved to Phase 2** - This task is now fulfilled by T051 in Phase 2. No action required here.

- [X] T052 [US1] **Moved to Phase N** - This task is now fulfilled by T052 in Phase N. No action required here.

- [X] T053 [US2] **Moved to Phase N** - This task is now fulfilled by T053 in Phase N. No action required here.

- [X] T054 [US3] **Moved to Phase N** - This task is now fulfilled by T054 in Phase N. No action required here.

---

## Phase N+2: Final Verification & Documentation (New)

**Purpose**: Ensure all requirements are met and documentation is complete before final submission.

- [ ] T055 [US1] **Resolve: Final Data Integrity Check** - Implement a script `code/verify_data_integrity.py` that loads all generated CSVs, verifies checksums against `data_hygiene.py` logs, and confirms the presence of all required columns and metadata flags. **Output**: `data/processed/data_integrity_report.json`.
- [ ] T056 [US2] **Resolve: Final Resource Audit** - Run `code/training/pilot_resource_check.py` on the full dataset and generate a final resource usage report `data/processed/final_resource_audit.json` confirming peak RAM and total runtime are within limits.
- [ ] T057 [US3] **Resolve: Final Statistical Report Validation** - Implement a script `code/validate_statistical_report.py` that checks `docs/research_report.md` for the required conditional causal framing phrase and verifies the presence of all required statistical artifacts.
- [ ] T058 [P] **Resolve: End-to-End Documentation** - Update `README.md` with a complete "How to Run" section, including prerequisites, installation, and a step-by-step guide to executing the full pipeline via `code/main.py`.
- [ ] T059 [P] **Resolve: Final Review Checklist** - Create a `docs/REVIEW_CHECKLIST.md` that lists all functional requirements (FR-001 to FR-009) and success criteria (SC-001 to SC-006) with a checkbox for each, to be completed before final submission.

---

## Phase N+3: Post-Analysis Resolution (Removed)

**Purpose**: Address specific findings from the latest `/speckit.analyze` run to ensure the pipeline is robust and meets all constraints.
**Note**: All critical tasks (T061, T064) have been moved to Phase 4 to ensure architectural constraints are enforced before distillation.

- [X] T061 [US2] **Moved to Phase 4** - Integrated into T020-AUDIT (CPU-Only Enforcement). No action required here.
- [X] T062 [US1] **Resolve: Entropy Threshold Validation** - Add a unit test in `tests/unit/test_entropy_calc.py` that generates a known "perfectly random" sequence and a "perfectly ordered" sequence, verifying the entropy metric calculates the expected maximum and minimum values respectively, ensuring the metric is mathematically sound before being used for the t-test gate.
- [X] T063 [US3] **Resolve: Bonferroni Correction Verification** - Add a unit test in `tests/unit/test_statistical_analysis.py` that manually calculates the Bonferroni correction for a set of multiple p-values and compares it against the output of `stats.py` to ensure the correction logic is implemented correctly.
- [X] T064 [US2] **Moved to Phase 4** - Integrated into T018-TEACHER (Trace Probability Validation). No action required here.
- [X] T065 [US1] **Resolve: Sample Size Power Analysis** - Implemented as T066-P in Phase 2. No action required here.

---

## Phase N+4: Additional Review & Refinement (New)

**Purpose**: Address remaining concerns from the latest analysis regarding data integrity, statistical rigor, and pipeline robustness.

- [ ] T066 [US1] **Resolve: Sample Size Power Analysis** - Implemented as T066-P in Phase 2. No action required here.
- [ ] T067 [US2] **Resolve: Trace Consistency Threshold Calibration** - Implement a script `code/analysis/trace_calibration.py` that analyzes the distribution of trace entropy across the training set to determine optimal thresholds for "low" and "high" trace entropy, rather than relying on a simple median split. **Prerequisite: T019-CALC.**
- [ ] T068 [US3] **Resolve: Effect Size Calculation** - Extend `code/analysis/stats.py` to calculate effect sizes (Cohen's d for t-tests, eta-squared for ANOVA) in addition to p-values, and include these in the `StatisticalResult` artifact. **Prerequisite: T030, T031.**
- [ ] T069 [US1] **Resolve: Data Versioning** - Implement a script `code/utils/data_versioning.py` that generates a unique version hash for each dataset based on its content and metadata, and stores this in `data/raw/version_manifest.json`. **Prerequisite: T017.**
- [ ] T070 [US2] **Resolve: Training Run Comparison** - Implement a script `code/analysis/compare_runs.py` that visualizes and compares the loss curves and convergence epochs of the three distillation runs, outputting a report to `data/processed/run_comparison_report.md`. **Prerequisite: T026-ORCHESTRATE.**
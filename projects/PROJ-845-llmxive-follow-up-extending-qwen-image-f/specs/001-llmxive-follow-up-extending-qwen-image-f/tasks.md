# Tasks: llmXive follow-up: extending "Qwen-Image-Flash: Beyond Objective Design"

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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

- [X] T001 Create project directory `projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/` with sub‑directories `data/raw/`, `data/processed/`, `code/`, `code/generators/`, `code/models/`, `code/training/`, `code/analysis/`, `code/utils/`, `tests/unit/`, `tests/integration/`, `contracts/`; add an empty `__init__.py` in each Python package directory.
- [X] T002 Create `requirements.txt` at `projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/requirements.txt` containing pinned versions of `torch==2.3.0+cpu`, `transformers==4.41.2`, `scikit-learn`, `scipy`, `pandas`, `numpy`, `pyyaml`.
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
- [X] T006 Create configuration management in `code/config.py` with a `Config` dataclass containing `seed: int = 42`, `max_ram_gb: float = 7.0`, `max_runtime_hours: float = 6.0`.
- [X] T007 Implement `SyntheticProblem` dataclass in `code/models/synthetic_problem.py` with fields `id: str`, `premises: List[str]`, `operators: List[str]`, `solution: str`, `entropy_level: str`, `metadata: Dict[str, Any]`; provide `to_dict()` and `from_dict()` methods for JSON serialization.
- [X] T008 Implement `ResourceMonitor` class in `code/utils/resource_monitor.py` with methods `start()`, `stop()`, `get_peak_ram_gb()`, and context‑manager support for automatic monitoring.
- [X] T041 Add reproducibility verification script `code/utils/reproducibility_check.py` that runs the generator twice with the same seed from `Config`, computes SHA256 checksums of generated CSVs, and fails the CI if they differ; integrate as a CI step.
- [X] T051 **Resolve: Pipeline Orchestrator** - Create `code/main.py` as the pipeline orchestrator script. This script must import and execute the generator, trainer, and analyzer modules in the correct order, handling error propagation and exit codes. It must be the single entry point for the CI/CD pipeline.

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

- [X] T011 [US1] Implement propositional logic problem generator function `generate_propositional_problem()` in `code/generators/logic_generator.py`.
- [X] T011‑B [US1] Implement arithmetic problem generator function `generate_arithmetic_problem()` in the same module.
- [X] T012‑HIGH [US1] Implement generation of High‑Entropy subset in `code/generators/logic_generator.py` with randomized premises/operators, targeting **exactly 1000 samples**, and metadata flags.
- [X] T012‑LOW [US1] Implement generation of Low‑Entropy subset in `code/generators/logic_generator.py` with structured/repetitive patterns, targeting **exactly 1000 samples**, and metadata flags.
- [X] T012‑TARGET [US1] Implement generation of Target‑Specific subset in `code/generators/logic_generator.py` with narrow reasoning styles, targeting **exactly 1000 samples**, and metadata flags.
- [X] T013 [US1] Implement generation of a distinct Generalization Set (`data/raw/test_set.csv`) with N_test ≥ 500, ensuring each sample's `structure_hash` (SHA256 of premises + operators) is **not** present in any training subset; also stratify by entropy level.
- [X] T013‑VERIFY [US1] **Resolve: Distinctness Verification** - Implement a verification step in `code/generators/logic_generator.py` that asserts the `structure_hash` of every test sample is unique relative to the training set. If any collision is found, the script must raise a `ValueError` and log the collision details to `data/raw/test_distinctness_log.json` before exiting. **This task must pass before T016 runs.**
- [X] T014 [US1] Add contradiction detection: before writing a problem, verify solvability (e.g., using a simple SAT check); discard unsolvable problems.
- [X] T015 [US1] Implement function `compute_entropy_statistics()` in `code/analysis/metrics.py` that calculates per‑sample entropy scores (problem entropy) and performs a two‑sample t‑test (high vs low); log mean, std, and p‑value.
- [X] T015‑ENFORCE [US1] Add validation in `metrics.py` that raises `SystemExit(1)` if the t‑test p‑value ≥ 0.05, logging the failure; this enforces the controlled‑entropy requirement without presuming success. **Must run before T016.**
- [X] T016‑SUCCESS [US1] **Resolve: Success Artifact Generation** - If T015-ENFORCE passes, save generated CSVs to `data/raw/high_entropy.csv`, `data/raw/low_entropy.csv`, `data/raw/target_specific.csv`, and `data/raw/test_set.csv` with columns for all fields defined in `SyntheticProblem`, including `entropy_level`, `structure_hash`, and `set_type`.
- [X] T016‑FAIL [US1] **Resolve: Failure Artifact Generation** - If T015-ENFORCE fails (p >= 0.05), generate a `data/raw/generation_failure_report.json` containing the partial generated data, the computed p-value, and a detailed explanation of the failure. This ensures a "Single Source of Truth" exists even for negative results. **This task runs if T015-ENFORCE fails.**
- [X] T017 [US1] Generate SHA256 checksums for each CSV and record them in `code/utils/data_hygiene.py`; log checksum values to the logger.
- [X] T044 [US1] Add explicit hash‑based distinctness verification in the generator (used by T013) to guarantee that logical structures (premises/operators) of the Generalization Set differ from any training sample, satisfying FR‑008.
- [X] T046 [US1] **Resolve: Entropy Metric Definition** - Explicitly implement `code/analysis/metrics.py` to calculate Shannon entropy based on the **token-level probability distribution of the generated reasoning steps** for trace entropy validation (FR-009), while keeping `compute_entropy_statistics` focused on **problem entropy** (premises/operators) for US-1. Add a unit test in `tests/unit/test_entropy_calc.py` that verifies the metric yields distinct values for a "randomized" sequence vs. a "repetitive" sequence of the same length.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU‑Tractable Distillation Pipeline (Priority: P2)

**Goal**: Execute a CPU‑only distillation process where a <100 M‑parameter student model learns from teacher traces, strictly adhering to hardware constraints (RAM < 7 GB).

**Independent Test**: Run training on a single subset and verify no CUDA errors, RAM usage < 7 GB, and loss convergence.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [US2] Write unit test `tests/unit/test_loss_function.py` that checks KL‑divergence implementation returns a non‑negative scalar.
- [X] T019 [US2] Write integration test `tests/integration/test_distillation_cpu.py` that launches a dummy training loop on a tiny dataset and asserts no CUDA devices are detected.

### Implementation for User Story 2

- [X] T020 [US2] Create `code/models/teacher.py` with a lightweight mock LLM class `Teacher` that generates traces. Ensure no GPU‑specific flags are used.
- [X] T020‑AUDIT [US2] Add CI script `ci/check_forbidden_libs.sh` that parses `requirements.txt` and fails if `bitsandbytes`, `accelerate`, or any CUDA‑related packages are present.
- [X] T020‑TEACHER [US2] **Resolve: 10-step Trace Generation** - Implement the `Teacher` class to generate **actual -step CoT traces** using a deterministic rule-based engine that strictly adheres to the problem's logical structure. **Crucially, output token-level probability distributions (logits/probs) for each step** derived from a deterministic mapping of rule complexity to probability mass (e.g., higher complexity = lower probability for non-optimal steps), ensuring valid KL-divergence targets.
- [X] T020‑GENERATE [US2] Implement a script `code/models/generate_traces.py` that invokes the `Teacher` class to generate traces for all training problems and saves them as `data/raw/teacher_traces.json` (containing problem ID, trace text, and token probabilities). **Prerequisite: T020-TEACHER.**
- [X] T021 [US2] Create `code/models/student.py` defining a DistilBERT‑base‑uncased‑like transformer (< 100 M parameters) suitable for CPU inference.
- [X] T022 [US2] Implement `compute_trace_entropy(problem: SyntheticProblem, trace: List[str]) -> float` in `code/analysis/metrics.py` that measures Shannon entropy of token-level probabilities from the teacher trace.
- [X] T022‑TRACE [US2] **Resolve: Trace Entropy Calculation** - Implement a dedicated function `validate_trace_consistency()` in `code/training/distill_loop.py` that computes the quantitative trace entropy for each sample and compares it against the problem entropy using a **Pearson correlation coefficient > 0.8** as the quantitative threshold for alignment, satisfying FR-009.
- [X] T022‑VALIDATE [US2] **Resolve: Trace Consistency Filtering** - Implement a filtering step in `code/training/distill_loop.py` that uses the quantitative metric from T022-TRACE to filter out samples where the trace entropy does not match the problem entropy. **Output a filtered dataset artifact `data/processed/filtered_dataset.json`** containing only consistent samples. This must run before T023.
- [X] T045 [US2] Add a pilot run script `code/training/pilot_resource_check.py` that trains the student on a small subset, records peak RAM via `ResourceMonitor`, and asserts limits; fail fast if limits are exceeded, providing empirical CPU‑tractability verification.
- [X] T023 [US2] Implement the main distillation loop in `code/training/distill_loop.py` using KL‑divergence loss, no mixed‑precision, early stopping when loss ≤ 0.1, and logging of `convergence_epoch`. **Input: `data/processed/filtered_dataset.json` from T022-VALIDATE.**
- [X] T024 [US2] Add early‑stopping logic to the training loop; record the epoch at which the loss threshold is first met.
- [X] T025 [US2] Integrate `ResourceMonitor` hooks into the training script to enforce the GB RAM ceiling and A wall‑clock time limit will be imposed., exiting with a specific error code on breach.
- [X] T026‑ORCHESTRATE [US2] **Resolve: Execution Command** - Create a script `code/training/run_all_distillations.py` that invokes `distill_loop.py` for each subset (High, Low, Target) using the filtered dataset, aggregates logs, and stores individual run logs as `data/processed/distill_high.json`, `data/processed/distill_low.json`, `data/processed/distill_target.json`.
- [X] T027 [US2] Ensure non‑convergent runs are logged with `"status": "failed_non_converge"` and assign `convergence_epoch` = `max_epochs + 1` for downstream statistical handling.
- [X] T027‑CHECKPOINT [US2] **Resolve: Model Handoff** - Implement a checkpointing step in `run_all_distillations.py` that saves the final state of each student model to `data/processed/models/` (e.g., `model_high.pt`, `model_low.pt`, `model_target.pt`) in a standard format loadable by `evaluation.py`.
- [X] T042 [US2] After all three runs, generate a validation report `data/processed/trace_consistency_report.json` summarizing total samples, number filtered per entropy subset, and overall pass/fail status for FR‑009.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation of Coherence Hypothesis (Priority: P3)

**Goal**: Evaluate student models on the Generalization Set and perform rigorous statistical analysis (ANOVA, t‑tests with Bonferroni correction) to validate the Coherence over Diversity hypothesis.

**Independent Test**: Run the statistical script on accuracy/convergence logs and verify p-values and effect sizes.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [US3] Write unit test `tests/unit/test_statistical_analysis.py` that feeds synthetic accuracy data into `stats.anova_test` and checks that the returned object contains `f_statistic` and `p_value`.

### Implementation for User Story 3

- [X] T029 [US3] Implement evaluation script `code/analysis/evaluation.py` that loads each student model from `data/processed/models/`, runs inference on `data/raw/test_set.csv` (Generalization Set), and records accuracy and per‑sample epoch of loss‑threshold crossing. **Output artifact: `data/processed/evaluation_results.json`**. **Prerequisite: T027-CHECKPOINT.**
- [X] T029‑VERIFY [US3] Add an assertion in `evaluation.py` that raises `ValueError` if any loaded sample has `set_type != "test_generalization"`; this guarantees exclusive use of the Generalization Set.
- [X] T030 [US3] Add function `anova_test(accuracies: Dict[str, List[float]]) -> Dict` in `code/analysis/stats.py` that computes the ANOVA F‑statistic and raw p‑value across the three models.
- [X] T031 [US3] Add function `pairwise_t_test(convergence_epochs: Dict[str, List[int]]) -> Dict` that performs pairwise t‑tests between model groups.
- [X] T032 [US3] Implement Bonferroni correction in `stats.py` that adjusts all p‑values (ANOVA and pairwise) and returns corrected values.
- [X] T033 [US3] **Resolve: Statistical Result Artifact** - Create `StatisticalResult` records (using the schema from contracts) for each test and write them to `data/processed/statistical_results.json`. **Include a verification step to assert the file exists and matches the schema.**
- [X] T034 [US3] **Resolve: Causal Framing** - Extend `code/report_generator.py` to produce a human‑readable markdown report `docs/research_report.md` that includes the statistical results. **Logic:** The report MUST explicitly state "causal regarding the effect of entropy on performance" with a qualification (e.g., "within the synthetic domain" or "subject to statistical significance") if p < 0.05, or "No statistically significant effect found; causal claim is limited" if not. **Do not omit the phrase entirely.**
- [X] T034‑VALIDATE [US3] Add a validation function in `report_generator.py` that asserts the conditional causal framing logic is present, raising an AssertionError on mismatch.
- [X] T043 [US3] Add a separate JSON summary `data/processed/final_statistical_summary.json` that lists all raw and corrected statistics (F, t, p-values) and the final conclusion, to satisfy SC‑001 and SC‑002 as a distinct artifact.
- [X] T035 [US3] Commit the final markdown report and JSON summary to the repository.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T036 [P] Update `README.md` and `docs/` with usage examples, architecture diagram, and instructions for reproducing the full pipeline.
- [X] T037 Code cleanup and refactoring across modules for readability and adherence to style guide.
- [X] T038 Performance optimization: profile the generator and training loops; adjust batch sizes if peak RAM approaches 7 GB.
- [X] T039 [P] Add additional unit tests for edge cases (contradiction filtering, timeout handling) in `tests/unit/`.
- [X] T040 Run `quickstart.md` validation and end‑to‑end pipeline test on GitHub Actions free‑tier runner; ensure total wall‑clock time < 6 h and RAM < 7 GB.
- [X] T052 [US1] **Resolve: Sample Size Constants** - Update `code/config.py` to define explicit constants `N_TRAIN_PER_SUBSET = 1000` and `N_TEST_SET = 500`, and ensure `code/generators/logic_generator.py` uses these constants directly.
- [X] T053 [US2] **Resolve: Resource Limit Constants** - Update `code/config.py` to replace unresolved claim placeholders with the explicit float values `7.0` (RAM) and `6.0` (hours) and ensure `ResourceMonitor` and `pilot_resource_check.py` reference these config values directly.
- [X] T054 [US3] **Resolve: Statistical Result Artifact** - Implement the logic in `code/analysis/stats.py` to generate the `StatisticalResult` JSON structure required by T033, ensuring it includes `f_statistic`, `p_value`, `corrected_p_value`, and `conclusion` fields, and write a unit test to verify the schema compliance. **Output: `data/processed/statistical_results.json`.**

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

- [X] T050 [US1] **Resolve: Generalization Set Structural Independence** - Implement a robust `structure_hash` algorithm in `code/generators/logic_generator.py` that hashes the **serialized logical structure** of the problem (e.g., a canonical string representation of the premises/operators) rather than the raw string, ensuring that semantically identical but syntactically different problems are correctly identified as distinct, preventing accidental leakage into the test set. (Note: AST hashing removed as per spec scope).

- [X] T047 [US2] **Moved to Phase 4 as T020-TEACHER** - This task is now fulfilled by T020-TEACHER which generates 10-step traces with probabilities. No action required here.

- [X] T051 **Moved to Phase 2** - This task is now fulfilled by T051 in Phase 2. No action required here.

- [X] T052 [US1] **Moved to Phase N** - This task is now fulfilled by T052 in Phase N. No action required here.

- [X] T053 [US2] **Moved to Phase N** - This task is now fulfilled by T053 in Phase N. No action required here.

- [X] T054 [US3] **Moved to Phase N** - This task is now fulfilled by T054 in Phase N. No action required here.

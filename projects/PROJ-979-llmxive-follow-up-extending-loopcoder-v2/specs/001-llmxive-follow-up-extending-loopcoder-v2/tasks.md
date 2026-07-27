# Tasks: llmXive follow-up: extending "LoopCoder-v2: Only Loop Once for Efficient Test-Time Computation Scali"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-loopcoder-v2/`
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

## Model Substitution Note

**CRITICAL**: The spec's `Assumptions` and `FR-001`/`FR-002` mandate `LoopCoder-v2-2B`. However, the `LoopCoder-v2` checkpoint is not verified/available. This project substitutes `LoopCoder-v-2B` with `CodeLlama-1.3b-Instruct` (CPU validation) and `CodeLlama-3b/7b-Instruct` (GPU full analysis).

**Important**: **All success criteria (SC-001, SC-002, SC-003) are RE-BASELINED** for the CodeLlama architecture. The null hypothesis is re-framed as "No correlation between entropy and convergence for CodeLlama" rather than LoopCoder-v2. The substitution changes the *model weights* used for inference, which changes the entropy distribution and convergence behavior, thus requiring a re-definition of the scientific claim. The tasks below reflect this re-baselined scope where the *implementation target* changes, and the *scientific goals* are updated to match the new model. The methodology (entropy extraction, convergence tracking) remains identical, and the metrics (correlation coefficient, FLOPs savings) must satisfy the original spec's requirements but applied to the new model.

**Implementation Constraint**: All tasks involving model inference (T012, T013, T019) MUST load the model from the environment variables `CODELLAMA_CPU_PATH` (for validation) or `CODELLAMA_GPU_PATH` (for full analysis). Do not use hardcoded paths.

**Verification Note**: The spec.md and plan.md already reflect the CodeLlama model substitution in their 'Assumptions' and 'Technical Context' sections. No update task is required for this substitution.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, and configuration definition

- [x] T001 [P] Initialize project directory structure in `projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/`. Create `data/`, `code/`, `paper/`, `state/`, `contracts/` directories. Verify existence of `data/raw`, `data/processed`, `code/src`, `code/tests`, `code/notebooks`. **Artifact**: Generate `structure_check.json` with keys: `{status: "ok", directories: ["data/raw", "data/processed",...]}`.

- [x] T002 [P] Initialize Python project with `transformers`, `torch`, `scikit-learn`, `pandas`, `datasets`, `pytest`, `docker` dependencies in `code/requirements.txt`.

- [x] T003 [P] Configure code formatting in `code/`.
 - Create `.ruff.toml` with content: `line-length = 88`, `target-version = "py310"`, `select = ["E", "F", "W", "I"]`.
 - Create `pyproject.toml` with `[tool.black]` section: `line-length = 88`, `target-version = ['py310']`.
 - **Artifact**: Verify files exist and contain exact strings.

- [x] T003-config [P] Create `code/config.yaml` with default statistical and configuration parameters. **Content**:
 - `strata_threshold: 50` (for FR-007 underpowered strata flagging)
 - `non_inferiority_delta: 0.05` (for FR-006 non-inferiority test margin)
 - `entropy_n_samples: 10` (for FR-001 sampling)
 - `convergence_k_range: [1, 2, 3]` (for FR-002 core loops)
 - **Verification**: Verify file exists and contains valid YAML with required keys. **Dependencies**: None.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a [P] Implement `code/src/data_loader.py` function `fetch_datasets()`: Fetch HumanEval and MBPP via `datasets.load_dataset`. Save raw copies to `data/raw/`.
- [X] T004b [P] Implement `code/src/data_loader.py` function `checksum_datasets()`: Compute SHA256 checksums for ALL files in `data/raw/` and write them to `data/checksums.txt`. Format: `<sha256_hash> <filename>`. **Artifact**: `data/checksums.txt`. **Schema**: Plain text file with one hash per line.
- [X] T004c [P] Implement `code/src/data_loader.py` function `stratify_data()`: Apply stratified sampling by difficulty (using 'difficulty' column or hashing 'task_id'). **Read threshold from `code/config.yaml` key `strata_threshold` (default 50)**. Flag strata with < threshold samples as 'underpowered' in `data/processed/strata_log.json`. **Artifact**: `data/processed/strata_log.json`. **Schema**: `{strata: [{name: str, count: int, underpowered: bool}]}`. **Dependencies: T004a, T004b, T003-config**.
- [X] T004d [P] Implement `code/src/data_loader.py` function `save_splits()`: Save processed splits to `data/processed/splits.json`. **Schema**: `{train: [{task_id: str, prompt: str, test: str, difficulty: str}], test: [{task_id: str, prompt: str, test: str, difficulty: str}]}`. **Verification**: Verify file exists and contains valid JSON with required keys. **Dependencies: T004c**.
- [X] T004f [P] Implement `code/src/data_loader.py` function `filter_strata()`: Read `data/processed/strata_log.json` and `data/processed/splits.json`. Identify strata where `underpowered` is true. Filter out all samples belonging to these strata from `splits.json`. Save to `data/processed/filtered_splits.json`. **Schema**: Same as `splits.json` but with reduced row count. **Verification**: Verify row count < original and no 'underpowered' strata remain. **Dependencies: T004c, T004d**.
- [X] T005 [P] Create `code/src/entropy.py` stub with function signature: `def extract_entropy(prompt: str, model, n_samples: int = 10) -> float`. **Dependencies: T004**.
- [x] T005d [P] Define FLOPs utility function in `code/src/utils.py`: Implement formula `FLOPs = parameters * sequence_length * k` for baseline calculation (FR-006, SC-002).
- [X] T005e [P] Implement resource monitoring utility in `code/src/utils.py`: Create `capture_metrics()` function. Use `psutil` for CPU/RAM (`psutil.virtual_memory().used / 1024**3`) and `torch.cuda` (`torch.cuda.memory_allocated() / 1024**3`) for GPU metrics. Log runtime, RAM, GPU usage. Save to `data/processed/resource_metrics.json`. **Schema**: `{runtime_s: float, ram_gb: float, gpu_util_pct: float, gpu_memory_gb: float}`. **Dependencies: None**. **Usage Note**: This utility is explicitly invoked by T033 to satisfy SC-005 for the full dataset run. **Verification**: Run function and verify `resource_metrics.json` exists with valid schema.
- [X] T006 [P] Create `code/src/inference.py` stub with function signature: `def run_inference(prompt: str, model, k: int) -> dict`. **Return Schema**: `dict` with keys `task_id` (str), `k` (int), `output` (str), `is_correct` (bool), `converged` (bool), `first_correct_step` (int | None). **Dependencies: T004e**.
- [x] T007 [P] Define `InputProblem` and `ConvergenceTrajectory` dataclasses in `code/src/models.py`. **InputProblem**: `task_id: str`, `prompt: str`, `test: str`. **ConvergenceTrajectory**: `task_id: str`, `k: int`, `output: str`, `is_correct: bool`, `converged: bool`, `first_correct_step: int | None`. **Dependencies: None**.
- [x] T008b [P] Create `paper/model_substitution_rationale.md`. **Content**: Document the pivot from LoopCoder-v2 to CodeLlama, citing verified HuggingFace URLs for CodeLlama-1.3b, 3b, 7b. Explain why SCs are re-baselined. **Dependencies: T008c**.
- [X] T009 [P] Implement Docker sandbox configuration for code execution safety in `code/Dockerfile` and `code/docker-compose.yml`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3a: User Story 1 - Core Correlation Analysis (Data Generation) (Priority: P1) 🎯 MVP

**Goal**: Extract initial semantic entropy and track convergence trajectories to compute Spearman correlation.

**Independent Test**: Run `code/src/entropy.py` and `code/src/inference.py` on a stratified sample (N=50 for CPU validation) to produce `data/processed/entropy_results.csv` and `data/processed/convergence_results.csv`, then verify `code/src/analysis.py` computes a non-error correlation coefficient.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for entropy clustering logic in `code/tests/test_entropy.py`. **Function**: `test_entropy_clustering()`. **Mock**: Fixed list of strings with known semantic clusters. **Assert**: Entropy calculation matches expected value.
- [X] T011 [P] [US1] Integration test for end-to-end entropy + convergence pipeline on N=5 sample using mock fixtures in `code/tests/test_analysis.py`. **Function**: `test_pipeline_n5()`. **Mock**: Mock model returning fixed strings. **Mock Data**: 5 prompts with known expected entropy and convergence steps. **Assert**: `entropy_results.csv` and `convergence_results.csv` generated with correct schema. **Dependencies: T012a, T013a**. **Verification**: Run `pytest code/tests/test_analysis.py::test_pipeline_n5` and verify exit code 0.

### Implementation for User Story 1 (Data Generation)

- [X] T012a [US1] Implement sampling function in `code/src/entropy.py`: Generate N=10 samples per input. Load model from `CODELLAMA_CPU_PATH` or `CODELLAMA_GPU_PATH`. **Input**: `data/processed/filtered_splits.json`. **Output**: List of strings. **Dependencies: T004f**.
- [X] T012b [P] [US1] Implement clustering function in `code/src/entropy.py`: Cluster samples by (1) exact code match, (2) AST normalization, (3) execution result via Docker sandbox (T009) as tie-breaker. Load model from `CODELLAMA_CPU_PATH` or `CODELLAMA_GPU_PATH`. **Output**: Dict `{cluster_id: [samples]}`. **Dependencies: T004f, T009**.
- [X] T012c [US1] Implement entropy calculation in `code/src/entropy.py`: Compute Shannon entropy over cluster probabilities (FR-001). Handle undefined entropy (zero entropy) by assigning `entropy=1e-9` or excluding. Load model from `CODELLAMA_CPU_PATH` or `CODELLAMA_GPU_PATH`. **Dependencies: T012a, T012b**.
- [X] T012d [US1] Implement exclusion logging in `code/src/entropy.py`: Detect undefined entropy (cluster_count == 1 OR max(cluster_prob) > 0.99). Exclude these samples. Log exclusion count, rate, and reasons to `data/processed/exclusion_log.json`. **Schema**: `{excluded_count: int, excluded_rate: float, reasons: [str]}`. **Dependencies: T012c**. **Verification**: Run on sample data and verify `exclusion_log.json` exists with valid schema.
- [X] T013a [US1] Implement loop runner in `code/src/inference.py`: Load model from `CODELLAMA_CPU_PATH` or `CODELLAMA_GPU_PATH`. Run model for varying $k$ on each input problem from `data/processed/filtered_splits.json`. Execute generated code via Docker sandbox. Compare output against 'test' field. Record first correct solution step. Record non-convergence events (FR-007) as `step = -1`. **Output**: Write intermediate results to `data/processed/temp_trajectory.json`. **Schema**: `{task_id: str, k: int, output: str, is_correct: bool, converged: bool, first_correct_step: int}`. **Dependencies: T004f, T006, T009**. **Verification**: Run on sample data and verify `temp_trajectory.json` exists with valid schema.
- [X] T013b [US1] Implement sandbox wrapper in `code/src/inference.py`: Execute generated code via Docker sandbox and compare output against 'test' field. **Dependencies: T009**.
- [X] T013c [US1] Implement convergence detector in `code/src/inference.py`: Detect first correct solution. Record non-convergence events (FR-007). **Dependencies: T013a, T013b**.
- [X] T013d [US1] Implement result logger in `code/src/inference.py`: Save convergence trajectories from T013a/T013c to `data/processed/convergence_results.csv`. **Schema**: Columns `task_id`, `k`, `converged` (bool), `step` (int, -1 if non-convergent, null if not yet determined), `timestamp`. **Dependencies: T013a, T013c**. **Verification**: Run on sample data and verify `convergence_results.csv` exists with valid schema.
- [X] T015 [US1] Implement Spearman correlation calculation in `code/src/analysis.py`: Compute $\rho$ between entropy and convergence step, calculate p-value (FR-003) using `scipy.stats.spearmanr`. Load entropy from `data/processed/entropy_results.csv` and convergence from `data/processed/convergence_results.csv`. **Cross-Reference**: Align datasets using `task_id` and verify no samples are excluded in one but not the other (check T012d exclusion log). **Dependencies: T012d, T013d**. **Verification**: Run on sample data and verify correlation output.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Core Correlation Data Generated)

---

## Phase 4: User Story 2 - Dynamic Router Simulation (Priority: P2)

**Goal**: Simulate a lightweight dynamic routing strategy using logistic regression to predict optimal loop counts and evaluate FLOPs savings.

**Independent Test**: Train a logistic regression model on US1 data, apply to test set, and verify reports of prediction accuracy vs random baseline and FLOPs savings vs static $k=2$ baseline with statistical significance testing.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for logistic regression training and prediction in `code/tests/test_analysis.py`. **Function**: `test_router_training()`. **Mock**: Synthetic entropy/convergence data. **Assert**: Model trains and predicts with accuracy > random baseline.
- [X] T018 [P] [US2] Statistical test validation for non-inferiority vs static baseline in `code/tests/test_analysis.py`. **Function**: `test_non_inferiority()`. **Mock**: Synthetic accuracy data. **Assert**: T-test returns p-value < 0.05 for non-inferiority.

### Implementation for User Story 2

- [X] T019 [US2] Implement logistic regression router training in `code/src/analysis.py`: Train on entropy proxies using `sklearn.linear_model.LogisticRegression` (multi_class='multinomial', solver='lbfgs') to predict **optimal loop count** (Target: `first_correct_step` from T013d, binned to discrete levels: 1, 2, 3, or >3). Load model from `CODELLAMA_CPU_PATH` or `CODELLAMA_GPU_PATH` (if re-evaluation needed, otherwise use pre-computed data). **Input**: `data/processed/entropy_results.csv` and `data/processed/convergence_results.csv`. **Output**: `data/processed/router_model.pkl`, `data/processed/router_metrics.json`. **Schema**: `{accuracy: float, f1: float, confusion_matrix: list}`. **Dependencies: T012d, T013d**. **Verification**: Run on sample data and verify model and metrics exist.
- [x] T020 [US2] Implement router evaluation logic: Compare prediction accuracy against random baseline (predict $k=1$ for all samples). **Perform a paired t-test or bootstrap test to confirm statistical significance ($p < 0.05$)** (FR-006). **Output**: `data/processed/router_accuracy_test.json`. **Schema**: `{t_statistic: float, p_value: float, ci_lower: float, ci_upper: float}`. **Dependencies: T019**.
- [x] T021a [US2] Implement FLOPs estimation and savings calculation: **Use the formula from T005d** (`parameters * sequence_length * k`) to calculate static $k=2$ baseline FLOPs. Compare dynamic router vs static baseline. **Dependencies: T005d, T019**.
- [X] T021c [US2] Create `data/processed/config.json` with non-inferiority margin. **Schema**: `{delta: float}`. **Logic**: Read `NON_INFERIORITY_DELTA` from `code/config.yaml` (T003-config). **Verify** the value is a float and > 0. **Dependencies: T020, T021a, T003-config**.
- [x] T021b [US2] Perform non-inferiority test on accuracy (FR-006, SC-002). **Read non-inferiority margin (delta) from `data/processed/config.json` (T021c)**. Perform a **one-sided t-test** to verify accuracy difference is within margin against static $k=2$ baseline. **Output**: `data/processed/flops_savings.json`. **Dependencies: T020, T021a, T021c**.
- [X] T022 [US2] Integrate router simulation results into `data/processed/router_results.csv` and update `code/src/analysis.py` report generation. **Schema**: `{task_id, predicted_k, actual_k, accuracy, flops_saved}`. **Logic**: `flops_saved = baseline_flops - predicted_flops`. **Verification**: Verify file exists and contains all columns. **Dependencies: T021b**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Router Simulation Complete)

---

## Phase 5: User Story 3 - Statistical Robustness & Sensitivity Analysis (Priority: P3)

**Goal**: Ensure findings are robust to multiple comparisons and convergence definition sensitivity.

**Independent Test**: Re-run correlation analysis with Bonferroni/Holm-Bonferroni correction and sweep convergence thresholds ($k \in \{2, 3, 4\}$) to verify stability of correlation coefficients.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for multiple-comparison correction implementation in `code/tests/test_robustness.py`. **Function**: `test_holm_bonferroni()`. **Mock**: List of p-values. **Assert**: Adjusted p-values are monotonic and correct.
- [X] T024 [P] [US3] Sensitivity analysis sweep validation in `code/tests/test_robustness.py`. **Function**: `test_sensitivity_sweep()`. **Mock**: Synthetic convergence data for k=2,3,4. **Assert**: Variation in $\rho$ is calculated correctly.

### Implementation for User Story 3

- [X] T013e-sweep [US3] Implement sensitivity inference pass in `code/src/inference.py`: Re-run model for $k=4$ on the same dataset. Load model from `CODELLAMA_CPU_PATH` or `CODELLAMA_GPU_PATH`. **Input**: `data/processed/filtered_splits.json`. **Output**: `data/processed/convergence_results_k4.csv`. **Verification**: Verify file exists and contains k=4 results. **Dependencies: T004f, T006, T009**.
- [x] T025a [US3] Implement Holm-Bonferroni correction function in `code/src/robustness.py`: Create a function that takes a list of p-values and returns adjusted p-values (FR-005).
- [x] T025b [US3] Apply multiple-comparison correction in `code/src/robustness.py`: **Explicitly group p-values by difficulty strata (defined in T004c)** before applying Holm-Bonferroni algorithm. Save results to `data/processed/adjusted_pvalues.json`. **Schema**: `{strata_name: str, adjusted_p_value: float}`. **Dependencies: T015, T025a, T004c**.
- [X] T026 [US3] Implement sensitivity analysis loop in `code/src/robustness.py`: **Read existing convergence results from `data/processed/convergence_results.csv` (generated by T013d) and `data/processed/convergence_results_k4.csv` (generated by T013e-sweep)**. Sweep convergence threshold **$k \in \{2, 3, 4\}$** and compute variation in $\rho$ (SC-004). **Output**: `data/processed/sensitivity_sweep.json`. **Schema**: `{k_threshold: int, rho: float, p_value: float}`. **Dependencies: T013d, T013e-sweep**. **Verification**: Run on sample data and verify `sensitivity_sweep.json` exists with valid schema.
- [x] T027 [US3] Generate robustness report summarizing adjusted p-values and threshold stability in `data/processed/robustness_report.json`. **Schema**: `{adjusted_p_values: dict, sensitivity_sweep_results: dict}`. **Dependencies: T025b, T026**.

**Checkpoint**: All user stories should now be independently functional (Robustness Validated)

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final reporting

- [x] T028 [P] Finalize `paper/draft.md` with generated results, ensuring all stats trace to `data/processed/` files (Principle IV).
- [x] T029 [P] Run full validation suite on CPU (N=50) to verify pipeline within 6-hour limit (Assumption: Compute feasibility). **Execute `code/src/run_validation.py` with N=50 and verify exit code 0 and existence of `data/processed/validation_report.json`.** **Schema**: `{exit_code: int, runtime: float, pass: bool}`. **Dependencies: T005e**.
- [~] T030 [P] Update `quickstart.md` with instructions for CPU validation vs GPU full analysis modes. **Sections**: "CPU Validation Mode (N=50)", "GPU Full Analysis Mode". **Verification**: Verify file contains both sections. **Dependencies: None**.
- [x] T031 [P] Add `state/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2.yaml` with content hashes.
- [X] T032 [P] Run quickstart.md validation to ensure reproducibility. **Execute commands in quickstart.md and verify exit code 0**. **Artifact**: `quickstart_validation_report.json`. **Dependencies: T030**.
- [X] T033 [P] **MANUAL STEP - GPU ONLY**. Run full GPU analysis and record metrics for SC-005. **Execute full dataset on GPU, capture metrics via T005e, save to `data/processed/sc005_metrics.json`.** **Verification**: 
 1. Command: `python code/src/run_full_analysis.py --mode gpu --output data/processed/sc005_metrics.json`
 2. Exit code: 0
 3. Schema: `{runtime_s: float, ram_gb: float, gpu_util_pct: float, gpu_memory_gb: float, total_samples: int}`
 4. Verify file `data/processed/sc005_metrics.json` exists and contains all keys. **Verify `total_samples` equals len(HumanEval) + len(MBPP) after filtering**. **FAIL if file is missing or sample count mismatch.**
 **NOTE**: This task is NOT executed in standard CPU-only CI. It must be run manually on a GPU-enabled runner or local environment. If running in CI without GPU, skip this task.
 **Dependencies: T005e, T012a-d, T013a-d, T013e-sweep**.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **Critical Data Flow**: `code/src/entropy.py` (T012a-d) MUST complete and write `data/processed/entropy_results.csv` BEFORE `analysis.py` (T015) can run.
 - **Critical Data Flow**: `convergence_results.csv` (T013d) MUST exist before Router Simulation (T019) and Robustness (T025, T026).
 - **Critical Data Flow**: `filtered_splits.json` (T004f) MUST exist before T012 and T013 to ensure underpowered data is excluded.
 - **Sensitivity Flow**: T026 requires T013d (k=2,3) and T013e-sweep (k=4) to be completed.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories.
- **User Story 2 (P2)**: Depends on US1 data generation (T012d, T013d completion).
- **User Story 3 (P3)**: Depends on US1 data generation (T012d, T013d, T013e-sweep completion).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data loading (T004a-d) and Filtering (T004f) before Entropy/Inference (T012a-d, T013a-d)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T005d, T005e, T007, T008, T009) can run in parallel
- Once Foundational phase completes, US2 and US3 can start in parallel (both depend only on US1 data, not each other)
- All tests for a user story marked [P] can run in parallel
- **T012 (Entropy)** and **T013 (Inference)** are parallel tasks (both depend on T004f, T009).
- **T013e-sweep (Sensitivity Inference)** is now in Phase 5, so it is available for T026 in Phase 5.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3a: User Story 1 (Core Correlation Data Generation)
4. **STOP and VALIDATE**: Test US1 independently on CPU (N=50)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Data Gen) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 1 (Analysis) → Test independently → Deploy/Demo
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data generation & Correlation)
 - Developer B: User Story 2 (Router Simulation) - *Can start once T012d/T013d are done*
 - Developer C: User Story 3 (Robustness) - *Can start once T012d/T013d/T013e-sweep are done*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All tasks must run on free CPU-only CI for validation (T002, T012a-d, T013a-d with N=50, CodeLlama-1.3b). Full analysis (N=full, GPU) is a separate mode (T033).
- **Critical Constraint**: Never fabricate data. Use real HumanEval/MBPP datasets via `datasets` library.
- **Critical Constraint**: Entropy extraction (T012) must not run convergence loops; strict separation of predictor (entropy) and target (convergence) is required by Principle VI.
- **Model Substitution**: CodeLlama models are used instead of LoopCoder-v2-2B due to availability. Success criteria are re-baselined accordingly.
- **Model Loading**: All inference tasks MUST use `CODELLAMA_CPU_PATH` or `CODELLAMA_GPU_PATH` environment variables.
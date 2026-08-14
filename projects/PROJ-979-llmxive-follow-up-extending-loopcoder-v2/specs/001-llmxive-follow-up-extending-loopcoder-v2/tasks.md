# Tasks: llmXive follow-up: extending "LoopCoder-v2: Only Loop Once for Efficient Test-Time Computation Scali"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-loopcoder-v2/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[D]**: Sequential dependency (must run after specific tasks)
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

**Purpose**: Project initialization, basic structure, and configuration definition

- [x] T000-config [P] **Environment & Configuration Setup**: Create `code/config.yaml` and verify environment variables. **Logic**:
 1. Create `code/config.yaml` if it does not exist.
 2. Populate with keys: `CODELLAMA_CPU_PATH: "NOT_SET"`, `CODELLAMA_GPU_PATH: "NOT_SET"`, `strata_threshold: 50`, `non_inferiority_delta: 0.05`, `entropy_n_samples: 10`, `convergence_k_range: [1, 2, 3]`.
 3. If `CODELLAMA_CPU_PATH` or `CODELLAMA_GPU_PATH` are "NOT_SET", verify the existence of environment variables `CODELLAMA_CPU_PATH` and `CODELLAMA_GPU_PATH`. If env vars are missing, create a `.env` template file with placeholders.
 4. **Artifact**: `code/config.yaml`, `.env` (if needed). **Schema**: `{CODELLAMA_CPU_PATH: str, CODELLAMA_GPU_PATH: str, strata_threshold: int, non_inferiority_delta: float, entropy_n_samples: int, convergence_k_range: list}`. **Verification**: Verify file exists, keys are present, and defaults are correct. **Dependencies**: None.
- [x] T000-seed [P] **Random Seed Pinning**: Implement global random seed pinning in `code/src/utils.py`. **Logic**: 1. Create function `set_global_seed(seed: int = 42)`. 2. Set `random.seed(seed)`, `numpy.random.seed(seed)`, `torch.manual_seed(seed)`, and `torch.cuda.manual_seed_all(seed)`. 3. Set `os.environ['PYTHONHASHSEED'] = str(seed)`. 4. Ensure this function is called at the very start of `entropy.py`, `inference.py`, and `survival.py`. **Artifact**: `code/src/utils.py` (updated). **Verification**: Verify that running the script twice with the same seed produces identical outputs for entropy and convergence tasks. **Dependencies**: None.
- [x] T000-model [P] **Model Availability Check**: Verify the existence of `meta-llama/CodeLlama-7b-Instruct-hf`. **Logic**: 1. Attempt to load the model config using `transformers.AutoConfig.from_pretrained`. 2. If the model is not cached locally and `HF_TOKEN` is available, trigger a download verification (or document the required download command). 3. If the model is missing and cannot be downloaded, raise a clear error `ModelNotFoundError`. **Artifact**: `data/model_status.json` (status: "available" or "missing"). **Dependencies**: T000-config.

- [x] T001 [P] Initialize project directory structure in `projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/`. Create `data/`, `code/`, `paper/`, `state/`, `contracts/` directories. Verify existence of `data/raw`, `data/processed`, `code/src`, `code/tests`, `code/notebooks`. **Artifact**: Generate `structure_check.json` with keys: `{status: "ok", directories: ["data/raw", "data/processed",...]}`.

- [x] T002 [P] Initialize Python project with `transformers`, `torch`, `scikit-learn`, `pandas`, `datasets`, `pytest`, `docker`, `psutil`, `lifelines`, `statsmodels` dependencies in `code/requirements.txt`.

- [x] T003a [P] Create `.ruff.toml` in `code/`. **Content**: `line-length = 88`, `target-version = "py310"`, `select = ["E", "F", "W", "I"]`. **Verification**: Verify file exists and contains exact strings.
- [x] T003b [P] Create `pyproject.toml` in `code/`. **Content**: `[tool.black]` section: `line-length = 88`, `target-version = ['py310']`. **Verification**: Verify file exists and contains exact strings.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a [P] Implement `code/src/data_loader.py` function `fetch_datasets()`: Fetch HumanEval and MBPP via `datasets.load_dataset`. Save raw copies to `data/raw/`.
- [X] T004b [P] Implement `code/src/data_loader.py` function `checksum_datasets()`: Compute SHA256 checksums for ALL files in `data/raw/` and write them to `data/checksums.txt`. Format: `<sha256_hash> <filename>`. **Artifact**: `data/checksums.txt`. **Schema**: Plain text file with one hash per line. **Dependencies**: T004a.
- [X] T004c [P] Implement `code/src/data_loader.py` function `stratify_data()`: Apply stratified sampling by difficulty (using 'difficulty' column or hashing 'task_id'). Flag strata with <50 samples as 'underpowered' in `data/processed/strata_log.json`. **Use threshold=50** (read from `code/config.yaml` key `strata_threshold`; if missing, use default 50). **Pre-check**: Verify `code/config.yaml` exists and contains `strata_threshold`. **Artifact**: `data/processed/strata_log.json`. **Schema**: `{strata: [{name: str, count: int, underpowered: bool}]}`. **Dependencies**: T004a, T000-config.
- [X] T004d [P] Implement `code/src/data_loader.py` function `save_splits()`: Save processed splits to `data/processed/splits.json`. **Schema**: `{train: [{task_id: str, prompt: str, test: str, difficulty: str}], test: [{task_id: str, prompt: str, test: str, difficulty: str}]}`. **Verification**: Verify file exists and contains valid JSON with required keys. **Dependencies**: T004c.
- [x] T004f [P] Implement `code/src/data_loader.py` function `filter_strata()`: Read `data/processed/strata_log.json` and `data/processed/splits.json`. Generate a filtered dataset excluding 'underpowered' strata for primary analysis, BUT ALSO retain the full dataset in a separate file `data/processed/full_splits.json` to handle small strata. Save the filtered splits to `data/processed/filtered_splits.json` and the exclusion rate report to `data/processed/exclusion_rate_report.json`. **Schema**: `{strata: [{name: str, count: int, underpowered: bool}]}`. **Dependencies**: T004c, T004d.
- [X] T004g [P] **Generate Unseen Validation Set**: Create `code/src/data_loader.py` function `generate_unseen_set()`. **Logic**: 1. Read `data/processed/splits.json`. 2. Split the 'test' set into 'held_out_test' (for convergence) and 'unseen_validation' (for functional equivalence clustering). Use a fixed seed (42) for reproducibility. 3. Save the 'unseen_validation' subset to `data/processed/unseen_validation_set.csv`. **Artifact**: `data/processed/unseen_validation_set.csv`. **Schema**: `{task_id: str, prompt: str, test: str, difficulty: str}`. **Dependencies**: T004d.
- [X] T005 [P] Create `code/src/entropy.py` stub with function signature: `def extract_entropy(prompt: str, model, n_samples: int = 10) -> float`. **Dependencies**: T004g, T000-seed.
- [x] T005d [P] Define FLOPs utility function in `code/src/utils.py`: Implement formula `FLOPs = parameters * sequence_length * k` for baseline calculation. **Function Signature**: `def calculate_flops(model_params: int, seq_len: int, k: int) -> float`. **Dependencies**: None.
- [x] T005e [P] Implement resource monitoring utility in `code/src/utils.py`: Create `capture_metrics(mode: str)` function. **Logic**: 1. Use `time.perf_counter` to calculate runtime. 2. Use `psutil` for CPU/RAM. 3. Use `torch.cuda` and `nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader` (via subprocess) for GPU metrics. Parse the output by splitting on `,`, stripping whitespace, and converting the first column to float for utilization and second to float for memory. If GPU is available, log `gpu_util_pct` and `gpu_memory_gb`; if not, set to `null`. 4. **Capture metrics SPECIFICALLY for the invoked mode ('validation' or 'full_analysis') and ensure no data from other modes is included in the output**. 5. Save to `data/processed/resource_metrics.json`. **Schema**: `{runtime_s: float, ram_gb: float, gpu_util_pct: float | null, gpu_memory_gb: float | null, mode: str}`. **Verification**: Verify file exists and contains valid JSON with required keys. **Dependencies**: None.
- [X] T006 [P] Create `code/src/inference.py` stub with function signature: `def run_inference(prompt: str, model, k: int) -> dict`. **Return Schema**: `dict` with keys `task_id` (str), `k` (int), `output` (str), `is_correct` (bool), `converged` (bool), `first_correct_step` (int | None), `censored` (bool). **Dependencies: T004f, T000-seed, T000-model.**
- [X] T007 [P] Define `InputProblem` and `ConvergenceTrajectory` dataclasses in `code/src/models.py`. **InputProblem**: `task_id: str`, `prompt: str`, `test: str`. **ConvergenceTrajectory**: `task_id: str`, `k`: int, `output: str`, `is_correct: bool`, `converged: bool`, `first_correct_step: int | None`, `censored` (bool). **Dependencies: T004f.**
- [X] T008b [P] Create `paper/model_substitution_rationale.md`. **Content**: "The Success Criteria (SC-001 to SC-005) remain invariant under model substitution because they measure statistical relationships (correlation, FLOPs savings, robustness) and methodological soundness (survival analysis, multiple comparisons) rather than absolute performance metrics tied to a specific model size. The hypothesis concerns the *relationship* between entropy and convergence, which is a structural property of the iterative refinement process, not the specific capability of the 7B model. Thus, changing the model size (e.g., to 13B) would alter the absolute values of entropy and convergence rates, but the *validity of the SC metrics* (e.g., significance of correlation, non-inferiority of router) remains unchanged." **Dependencies: T000-config.**
- [X] T009 [P] Implement Docker sandbox configuration for code execution safety in `code/Dockerfile` and `code/docker-compose.yml`.
- [X] T009b [P] **Build Unseen Sandbox Image**: Build and verify the specific Docker image for functional equivalence testing. **Logic**: 1. Create `code/Dockerfile.unseen` (based on `python:3.11-slim`). 2. Install `ast` module and dependencies. 3. Build image with tag `entropy-sandbox:latest`. 4. Verify the image exists and can run a simple `echo` command. **Artifact**: `docker_image_status.json`. **Dependencies**: T009.

---

## Phase 3a: User Story 1 - Core Correlation Analysis (Data Generation) (Priority: P1) 🎯 MVP

**Goal**: Extract initial semantic entropy and track convergence trajectories to compute Spearman correlation.

**Independent Test**: Run `code/src/entropy.py` and `code/src/inference.py` on a stratified sample (N=50 for CPU validation) to produce `data/processed/entropy_results.csv` and `data/processed/convergence_results_core.csv`, then verify `code/src/analysis.py` computes a non-error correlation coefficient.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for entropy clustering logic in `code/tests/test_entropy.py`. **Function**: `test_entropy_clustering()`. **Mock**: Fixed list of strings with known semantic clusters. **Assert**: Entropy calculation matches expected value.
- [X] T011 [P] [US1] Integration test for end-to-end entropy + convergence pipeline on N=5 sample using mock fixtures in `code/tests/test_analysis.py`. **Function**: `test_pipeline_n5()`. **Mock**: Mock model returning fixed strings. **Mock Data**: 5 prompts with known expected entropy and convergence steps. **Assert**: `entropy_results.csv` and `convergence_results_core.csv` generated with correct schema. **Dependencies: T005, T006**. **Verification**: Run `pytest code/tests/test_analysis.py::test_pipeline_n5` and verify exit code 0.

### Implementation for User Story 1 (Data Generation)

- [ ] T012a [US1] Implement **Entire Entropy Extraction Pipeline** in `code/src/entropy.py`. **Logic**: 1. Load model from `CODELLAMA_CPU_PATH` or `CODELLAMA_GPU_PATH` (env vars). 2. Generate N=10 samples per input from `data/processed/filtered_splits.json`. 3. Cluster samples by **semantic equivalence** using priority: (1) Exact code match, (2) AST normalization (using `ast` module) comparing **structural equality (normalized AST tree equality via `ast.dump(ast.parse(code))`)**, (3) **Functional equivalence** via execution in a Docker sandbox on *unseen* inputs from `data/processed/unseen_validation_set.csv` (generated by T004g). 4. Compute Shannon entropy over cluster probabilities. 5. Handle undefined entropy (zero entropy) by assigning `entropy=1e-9` or excluding. 6. Log exclusion events to `data/processed/exclusion_log.json`. 7. Save final results to `data/processed/entropy_results.csv`. **Schema**: `{task_id: str, entropy: float, exclusion_reason: str | null}`. **Dependencies**: T004f, T004g, T009b, T000-seed, T000-model. **Artifact**: `data/processed/entropy_results.csv`. **Constraint**: Do not write intermediate files; produce `entropy_results.csv` directly.
- [ ] T013a [US1] Implement **Core Convergence Inference & Logging (k=1..3)** in `code/src/inference.py`. **Logic**: 1. Load model from `CODELLAMA_CPU_PATH` or `CODELLAMA_GPU_PATH`. 2. Run model for **k=1, k=2, and k=3** on each input from `data/processed/filtered_splits.json` **in a single sequential loop per input**. 3. **Stateful Tracking**: Maintain a `first_correct_step` variable for each input. If `is_correct` is true at step `k` AND `first_correct_step` is null, set `first_correct_step = k` and `converged = true`. If `first_correct_step` is already set, `converged = false` (even if correct again). 4. Execute generated code via Docker sandbox (using standard test suite). 5. Compare output against 'test' field. 6. Record `is_correct`, `converged` (true only on the *first* correct step), and `first_correct_step`. 7. **Handle non-convergence events (FR-007) at k=3 by setting `censored: true` if `first_correct_step` remains null**. 8. **Write directly to `data/processed/convergence_results_core.csv`** (no temp file). **Schema**: `{task_id: str, k: int, output: str, is_correct: bool, converged: bool, first_correct_step: int | None, censored: bool}`. **Dependencies**: T004f, T006, T009, T000-seed, T000-model. **Artifact**: `data/processed/convergence_results_core.csv`. **Note**: This task covers k=1..3 ONLY, strictly adhering to FR-002 for the primary correlation analysis (SC-001).
- [ ] T013b [US1] Implement **Sensitivity Convergence Inference & Logging (k=4)** in `code/src/inference.py`. **Logic**: 1. Load model from `CODELLAMA_CPU_PATH` or `CODELLAMA_GPU_PATH`. 2. Read `data/processed/convergence_results_core.csv` (from T013a) to check `first_correct_step` for each task. 3. Run model for **k=4** on each input from `data/processed/filtered_splits.json`. 4. Execute generated code via Docker sandbox. 5. **Stateful Logic**: If `first_correct_step` from T013a is NOT null, set `converged = false` (already converged) and `censored = false`. If `first_correct_step` is null, check `is_correct` at k=4. If correct, set `first_correct_step = 4` and `converged = true`. If not correct, set `censored = true`. 6. **Write directly to `data/processed/convergence_results_sensitivity.csv`**. **Schema**: `{task_id: str, k: int, output: str, is_correct: bool, converged: bool, first_correct_step: int | None, censored: bool}`. **Dependencies**: T004f, T006, T009, T000-seed, T000-model, T013a. **Artifact**: `data/processed/convergence_results_sensitivity.csv`. **Note**: This task is reserved exclusively for the sensitivity analysis (US3, T026) and is separate from the core US1 analysis to maintain modular independence.
- [ ] T015 [US1] Implement **Kaplan-Meier Survival Analysis & Correlation** in `code/src/survival.py`. **Logic**: 1. Merge `data/processed/entropy_results.csv` and `data/processed/convergence_results_core.csv` on `task_id`. 2. Prepare data for survival analysis: `time` = `first_correct_step` (or `k_max` for censored), `event` = `converged` (1 if converged, 0 if censored). 3. **Compute Spearman rank correlation** between initial entropy and convergence step (handling censored data by using the observed step or `k_max` as a lower bound for the correlation, or using a rank-based method for censored data). 4. **Secondary**: Use `lifelines.KaplanMeierFitter` to estimate survival function and `lifelines.CoxPHFitter` to estimate the hazard ratio of convergence as a function of entropy. 5. Perform power analysis to determine MDES. 6. Save results to `data/processed/correlation_results.json`. **Schema**: `{spearman_rho: float, spearman_p_value: float, hazard_ratio: float, p_value_cox: float, median_survival_time: float, power_analysis: {mdes: float, power: float}}`. **Dependencies**: T012a, T013a. **Artifact**: `data/processed/correlation_results.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Core Correlation Data Generated)

---

## Phase 4: User Story 2 - Dynamic Router Simulation (Priority: P2)

**Goal**: Simulate a lightweight dynamic routing strategy using logistic regression to predict optimal loop counts and evaluate FLOPs savings.

**Independent Test**: Train a logistic regression model on US1 data, apply to test set, and verify reports of prediction accuracy vs random baseline and FLOPs savings vs static $k=2$ baseline with statistical significance testing.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for logistic regression training and prediction in `code/tests/test_analysis.py`. **Function**: `test_router_training()`. **Mock**: Synthetic entropy/convergence data. **Assert**: Model trains and predicts with accuracy > random baseline.
- [X] T018 [P] [US2] Statistical test validation for non-inferiority vs static baseline in `code/tests/test_analysis.py`. **Function**: `test_non_inferiority()`. **Mock**: Synthetic accuracy data. **Assert**: T-test returns p-value < 0.05 for non-inferiority.

### Implementation for User Story 2

- [ ] T019 [US2] Implement logistic regression router training in `code/src/analysis.py`: Train on entropy proxies using `sklearn.linear_model.LogisticRegression` (multi_class='multinomial', solver='lbfgs') to predict **optimal loop count**. **Logic**: 1. Load `data/processed/entropy_results.csv` and `data/processed/convergence_results_core.csv`. 2. **Filter out censored samples** (where `censored` is true) as they lack a known optimal k. 3. Derive target variable: `optimal_k` = `first_correct_step`. 4. ** (Wikipedia: Cross-validation (statistics), https://en.wikipedia.org/wiki/Cross-validation_(statistics))**. 5. **Iterate multiple times**: train on 4 folds, validate on 1 fold, aggregate metrics (accuracy, F1). 6. **Compare against random baseline**: Train a model that predicts `k=1` for all samples; calculate its accuracy. 7. **Test statistical significance** of router accuracy vs random baseline (paired t-test or bootstrap). 8. Save model and metrics to `data/processed/router_model.pkl`, `data/processed/router_metrics.json`. **Schema**: `{accuracy: float, f1: float, confusion_matrix: list, random_baseline_accuracy: float, p_value_vs_random: float}`. **Dependencies: T012a, T013a**.
- [ ] T019b [US2] **Generate Router Results**: Apply the trained router model from T019 to the test set to generate predictions. **Logic**: 1. Load `data/processed/router_model.pkl`. 2. Read `data/processed/entropy_results.csv` and `data/processed/convergence_results_core.csv`. 3. **Filter inputs using `data/processed/filtered_splits.json` to exclude underpowered strata**. 4. Predict optimal loop count for each sample. 5. **Evaluation**: Compare predicted k with actual optimal k (from convergence data) **only for the non-censored subset**. For censored samples, record the router's prediction but mark them as 'censored' in the evaluation output. 6. Save results to `data/processed/router_results.csv`. **Schema**: `{task_id: str, predicted_k: int, actual_k: int | null, accuracy: bool, is_censored: bool}`. **Dependencies: T019, T004f**.
- [x] T020 [US2] Implement router evaluation logic: Compare prediction accuracy against random baseline (predict $k=1$ for all samples). **Perform a paired t-test or bootstrap test to confirm statistical significance ($p < 0.05$)** (FR-006). **Output**: `data/processed/router_accuracy_test.json`. **Schema**: `{t_statistic: float, p_value: float, ci_lower: float, ci_upper: float}`. **Dependencies: T019b**.
- [x] T021a [US2] **Generate Oracle Baseline**: Compute the optimal static baseline (oracle) metrics. **Logic**: 1. Read `data/processed/convergence_results_core.csv`. 2. For each sample, determine the true optimal `k` (the first `k` where `is_correct` is true, or k=3 if never converged). 3. Calculate the total FLOPs for this optimal strategy. 4. Calculate the accuracy of this optimal strategy (should be [deferred] for converged, or lower if censored). 5. Save to `data/processed/oracle_baseline.json`. **Schema**: `{total_flops: float, accuracy: float}`. **Dependencies: T013a**. **Artifact**: `data/processed/oracle_baseline.json`.
- [x] T021b [US2] **Unified FLOPs & Non-Inferiority Test**: Perform a unified verification step that: 1. Calculates FLOPs savings vs **optimal static baseline (oracle)** (from T021a) using the formula from T005d. 2. Performs a **one-sided t-test** to verify accuracy difference is within margin (delta from T021c) against the **oracle baseline**. **Input**: `data/processed/router_results.csv` (from T019b), `data/processed/config.json` (from T021c), `data/processed/convergence_results_core.csv` (from T013a), `data/processed/convergence_results_sensitivity.csv` (from T013b), `data/processed/oracle_baseline.json` (from T021a). **Logic**: 1. Compute average FLOPs for router vs oracle using actual k values from T013a/T013b. 2. Compute accuracy difference. 3. Perform one-sided t-test for non-inferiority. 4. Set `is_non_inferior` to True if p-value < 0.05 and accuracy_diff > -delta. **Output**: `data/processed/flops_savings.json`. **Schema**: `{flops_saved: float, accuracy_diff: float, p_value: float, is_non_inferior: bool}`. **Dependencies: T020, T021c, T021a, T013a, T013b, T005d**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Router Simulation Complete)

---

## Phase 5: User Story 3 - Statistical Robustness & Sensitivity Analysis (Priority: P3)

**Goal**: Ensure findings are robust to multiple comparisons and convergence definition sensitivity.

**Independent Test**: Re-run correlation analysis with Bonferroni/Holm-Bonferroni correction and sweep convergence thresholds ($k \in \{, 3, 4\}$) to verify stability of correlation coefficients.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for multiple-comparison correction implementation in `code/tests/test_robustness.py`. **Function**: `test_holm_bonferroni()`. **Mock**: List of p-values. **Assert**: Adjusted p-values are monotonic and correct.
- [X] T024 [P] [US3] Sensitivity analysis sweep validation in `code/tests/test_robustness.py`. **Function**: `test_sensitivity_sweep()`. **Mock**: Synthetic convergence data for k=2,3,4. **Assert**: Variation in $\rho$ is calculated correctly.

### Implementation for User Story 3

- [ ] T025a [US3] Implement **Per-Stratum Correlation Calculation** in `code/src/robustness.py`: Create a function that calculates Spearman correlation and p-value for each difficulty stratum defined in `data/processed/strata_log.json`. **Input**: `data/processed/entropy_results.csv`, `data/processed/convergence_results_core.csv`, `data/processed/strata_log.json`. **Output**: `data/processed/stratum_pvalues.json`. **Schema**: `{strata_name: str, rho: float, p_value: float, sample_count: int}`. **Dependencies: T015, T004c**.
- [ ] T025b [US3] Apply multiple-comparison correction in `code/src/robustness.py`: **Explicitly group p-values by difficulty strata (defined in T004c)**. **CRITICAL**: Read `data/processed/stratum_pvalues.json` from T025a and **filter out ALL strata marked as 'underpowered' (using `data/processed/strata_log.json`) from the Holm-Bonferroni correction list**. Apply correction only to valid, powered strata. Save results to `data/processed/adjusted_pvalues.json`. **Schema**: `{strata_name: str, adjusted_p_value: float}`. **Dependencies: T025a, T004c, T004f**.
- [ ] T025d [US3] Implement **Hierarchical Mixed-Effects Model** in `code/src/robustness.py**: **Logic**: 1. Identify strata marked as 'underpowered' in `data/processed/strata_log.json`. 2. **Merge** `data/processed/entropy_results.csv` and `data/processed/convergence_results_core.csv` to get results. 3. **Join** the merged results with `data/processed/full_splits.json` (or `strata_log.json`) to filter for the specific 'underpowered' strata. 4. Fit a hierarchical mixed-effects model using `statsmodels` with formula `entropy ~ convergence + (1|strata)` to estimate correlation while accounting for strata uncertainty. 5. Save results to `data/processed/mixed_effects_results.json`. **Schema**: `{strata_name: str, rho_estimate: float, confidence_interval: [float, float], variance_components: dict}`. **Dependencies: T004c, T012a, T013a, T004f**.
- [ ] T025c [US3] **Merge Convergence Results**: Merge `data/processed/convergence_results_core.csv` (k=1..3) and `data/processed/convergence_results_sensitivity.csv` (k=4) into a single dataset. **Logic**: 1. Read both CSV files. 2. Concatenate rows. 3. Save to `data/processed/convergence_results_merged.csv`. **Schema**: `{task_id: str, k: int, output: str, is_correct: bool, converged: bool, first_correct_step: int | None, censored: bool}`. **Dependencies: T013a, T013b**.
- [ ] T026 [US3] Implement sensitivity analysis loop in `code/src/robustness.py`: **Read existing convergence results from `data/processed/convergence_results_merged.csv`**. **Pre-check**: Verify `convergence_results_merged.csv` exists. If missing, **FAIL LOUDLY** with a clear error message indicating that the sensitivity analysis cannot proceed without the full loop range. **Logic**: 1. **Compute baseline**: Calculate Spearman rho for k={1,2,3} (from T013a data). 2. **Sweep**: Calculate Spearman rho for thresholds $k \in \{2, 3, 4\}$ (using k=2,3,4 data). 3. **Compare**: Report the variation in $\rho$ relative to the baseline (SC-004). **Output**: `data/processed/sensitivity_sweep.json`. **Schema**: `{baseline_rho: float, k_threshold: int, rho: float, p_value: float, delta_from_baseline: float}`. **Dependencies: T013a, T013b, T025c**.

**Checkpoint**: At this point, User Stories 1 AND 2 AND 3 should all work independently (Statistical Robustness Validated)

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final reporting

- [x] T028 [P] Finalize `paper/draft.md` with generated results, ensuring all stats trace to `data/processed/` files (Principle IV).
- [x] T029 [P] Run full validation suite on CPU (N=50) to verify pipeline within 6-hour limit (Assumption: Compute feasibility). **Execute `code/src/run_validation.py` with N=50 and verify exit code 0 and existence of `data/processed/validation_report.json`.** **Schema**: `{exit_code: int, runtime: float, pass: bool}`. **Dependencies: T005e**.
- [ ] T030 [P] Update `quickstart.md` with instructions for CPU/GPU modes. **Sections**: "CPU Validation Mode (N=50)", "Full GPU Analysis". **Verification**: Verify file contains both sections. **Dependencies: T029**.
- [x] T031 [P] Add `state/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2.yaml` with content hashes.
- [X] T032 [P] Run quickstart.md validation to ensure reproducibility. **Execute commands in quickstart.md and verify exit code 0**. **Artifact**: `quickstart_validation_report.json`. **Dependencies: T030**.
- [x] T033 [D] Run full GPU analysis and record metrics for SC-005. **Execute full dataset on GPU, capture metrics via T005e (mode='full_analysis'), save to `data/processed/sc005_metrics.json`.** **Verification**:
 1. Command: `python code/src/run_full_analysis.py --mode gpu --output data/processed/sc005_metrics.json`
 2. Exit code: 0
 3. Schema: `{runtime_s: float, ram_gb: float, gpu_util_pct: float, gpu_memory_gb: float, total_samples: int, mode: "full_analysis"}`
 4. Verify file `data/processed/sc005_metrics.json` exists and contains all keys. **FAIL if file is missing.**
 **Dependencies: T012a, T013a**. **Note**: This task ensures the full pipeline, including the sensitivity sweep (T026), is validated on the GPU.
- [x] T034 [P] **Aggregate SC-005 Metrics**: Combine `data/processed/sc005_metrics.json` and `data/processed/resource_metrics.json` to produce a final feasibility report. **Logic**: 1. Read metrics from T033 and T005e. 2. Compare runtime against predefined computational time constraints. 3. Report RAM/GPU usage against limits. 4. Save to `data/processed/sc005_final_report.json`. **Schema**: `{runtime_s: float, runtime_hours: float, within_budget: bool, ram_gb: float, gpu_memory_gb: float, feasibility_status: str}`. **Dependencies: T033, T005e**.
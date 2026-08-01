# Tasks: llmXive follow-up: extending "Mellum2 Technical Report"

**Input**: Design documents from `/specs/001-llmxive-complexity-loss/`
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

## Phase 0: Setup & Feasibility (Blocking Prerequisites)

**Purpose**: Project initialization and feasibility check. **T011 MUST run before T015.**

- [ ] T001a [P] Initialize project root directory: Create `projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/` root directory.
  - **Action**: `mkdir -p projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech`.
  - **Artifact**: `project_root_init.log` containing `pwd` output.
- [ ] T001b [P] Initialize project subdirectories: Create `code/`, `data/`, `tests/`, `data/raw/`, `data/processed/`, `data/results/` directories inside the project root.
  - **Action**: `mkdir -p code data tests data/raw data/processed data/results`.
  - **Artifact**: `project_subdirs_init.log` containing `ls -R` output of the new structure.
- [ ] T001c [P] Log creation of project root directory.
  - **Action**: Write a log entry confirming creation of the root directory.
  - **Artifact**: `project_root_creation.log`.
- [ ] T001d [P] Log creation of project subdirectories.
  - **Action**: Write a log entry confirming creation of all subdirectories.
  - **Artifact**: `project_subdirs_creation.log`.
- [ ] T002 Create `requirements.txt` with exact versions for datasets, transformers, tree-sitter, codeql, scikit-learn, statsmodels, pandas, numpy, matplotlib, seaborn, kenlm, pwlf, ruptures.
- [ ] T003a [P] Create `.gitignore` file: Add standard Python, HF cache, and data exclusions (e.g., `__pycache__`, `.env`, `data/`, `*.pt`).
  - **Artifact**: `.gitignore`.
- [ ] T003b [P] Create `README.md` with specific sections: Write `README.md` containing sections: "Project Overview", "Setup Instructions", "Usage", "Results Directory", "License".
  - **Artifact**: `README.md`.
- [ ] T004a [P] Configure linting (ruff): Create `ruff.toml` file with specific rules (e.g., `select = ["E", "F", "I"]`).
  - **Artifact**: `ruff.toml`.
- [ ] T004b [P] Configure formatting (black): Create `pyproject.toml` at repository root with `[tool.black]` section (e.g., `line-length = 88`).
  - **Artifact**: `pyproject.toml`.
- [ ] T008a [P] Create `code_chunk` schema: Write `code/contracts/code_chunk.schema.yaml` with explicit field definitions for `chunk_id`, `complexity`, `depth`, `loss`.
  - **Artifact**: `code/contracts/code_chunk.schema.yaml`.
- [ ] T008b [P] Create `analysis` schema: Write `code/contracts/analysis.schema.yaml` with explicit field definitions for `correlation`, `threshold`, `p_value`.
  - **Artifact**: `code/contracts/analysis.schema.yaml`.
- [ ] T008c [P] Create `output` schema: Write `code/contracts/output.schema.yaml` with explicit field definitions for final report structure.
  - **Artifact**: `code/contracts/output.schema.yaml`.
- [ ] T009a [P] Create `.env.template`: Write `.env.template` file listing required variables (e.g., `HF_TOKEN`, `HF_DATASET_NAME`).
  - **Artifact**: `.env.template`.
- [ ] T009b [P] Implement env loading: Update `code/config.py` to load `.env` using `python-dotenv` and validate required variables.
  - **Artifact**: `code/config.py` (updated).
- [ ] T010 [P] Implement timeout enforcement and benchmarking logic in `code/utils/timeout.py` to enforce a fixed per‑chunk duration constraint (FR‑003); must raise `TimeoutError` on breach.
- [ ] T011 [US1] Implement `code/analysis/feasibility.py` (Pilot Sample & A Priori Power Analysis):
  - **Input**: Fetch metadata only (N=50) of code chunks from `codeparrot/github-code` (Python/Java) using `datasets.load_dataset(..., streaming=True).take(50)` to estimate complexity variance WITHOUT downloading full files.
  - **Dependency**: **MUST run BEFORE T015** (Download).
  - **Action**: Perform a priori power analysis (alpha=0.05, Power=0.8, estimated effect size r=0.3). Compute required sample size N.
  - **Gate**:
    1. If calculated N > max feasible chunks for 6 h limit, **Cap N** to the maximum feasible size.
    2. Calculate `perturbation_magnitude` (default a standard significance threshold if not calculable) and `bootstrap_count` (default 1000) based on N.
  - **Write** `data/results/feasibility_report.json` with:
    - `status`: `"capped"` or `"feasible"`
    - `capped_N`: `<int>`
    - `power_limitation`: message if capped
    - `perturbation_magnitude`: `<float>`
    - `bootstrap_count`: `<int>`
    - `proceed_flag`: `true`
  - **Artifact**: `data/results/feasibility_report.json`.
- [ ] T011c [US1] Implement `code/analysis/power_sensitivity.py` (Power Sensitivity Fallback):
  - **Dependency**: **T011** (Feasibility Report).
  - **Action**: Read `feasibility_report.json`. If power limitation prevents FR‑005 or FR‑009, add `scope_reduction` field describing disabled components.
  - **Write** `data/results/power_sensitivity_fallback.md` and update `feasibility_report.json`.
  - **Artifact**: `data/results/power_sensitivity_fallback.md`.

## Phase 1: User Story 1 - Correlation Analysis of Code Complexity and Prediction Loss (Priority: P1) 🎯 MVP

**Goal**: Download code, label with static analysis, run frozen LLM inference, compute correlations, and generate scatter plots.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T012 [P] [US1] Add `tests/unit/test_download.py::test_download_handles_network_timeout` and `tests/unit/test_download.py::test_download_handles_empty_dataset`.
- [ ] T013 [P] [US1] Add `tests/unit/test_preprocess.py::test_preprocess_skips_unparseable_files` and `tests/unit/test_preprocess.py::test_preprocess_handles_syntax_errors`.
- [ ] T014 [P] [US1] Add `tests/unit/test_inference.py::test_inference_handles_timeout` and `tests/unit/test_inference.py::test_inference_handles_oom`.

### Implementation for User Story 1

- [ ] T015 [US1] Implement `code/data/download.py` to fetch `codeparrot/github-code` subset (Python/Java) with streaming to stay within Disk storage constraints.
  - **Dependency**: **T011c** (Feasibility & Scope passed).
  - **Logic**:
    1. Read `capped_N` and `scope_reduction` from `feasibility_report.json`.
    2. If `scope_reduction` disables cross‑language, download only Python; otherwise download both languages.
    3. Stream dataset, take exactly `capped_N` examples, split into `data/processed/train_python/` and `data/processed/val_java/` (if Java enabled).
    4. **Fail loudly** on any fetch error (`sys.exit(1)`), no synthetic fallback.
  - **Artifact**: `data/processed/train_python/`, `data/processed/val_java/` (if applicable).

- [ ] T016 [US1] Implement `code/data/preprocess.py` to run CodeQL and tree‑sitter.
  - **Dependency**: **T015** (Download/Split).
  - **Logic**: Process files, generate `queries/complexity.ql`, label cyclomatic complexity, nesting depth, repetition ratio, skip unparseable files with logging.
  - **Artifact**: `data/processed/annotated_python.jsonl`, `data/processed/annotated_java.jsonl`.

- [ ] T011b [US1] Implement `code/analysis/variance_check.py` (Variance Detection & Graceful Degradation):
  - **Dependency**: **T016** (Preprocess).
  - **Action**: Load annotated JSONL files, compute variance of `cyclomatic_complexity` and `nesting_depth`.
  - **Logic**: If any metric has zero variance, write `data/results/variance_null_report.json` with status `"null_variance"` and appropriate message; otherwise produce no artifact (proceed).
  - **Artifact**: `data/results/variance_null_report.json` (only on zero variance).

- [ ] T018a [US1] Implement `code/data/ngram.py` (Python) to build KenLM n‑gram model for the Python training set.
  - **Dependency**: **T016** (Preprocess).
  - **Logic**: Build 5‑gram model from `data/processed/train_python/`.
  - **Artifact**: `data/processed/kenlm_model_python.arpa`.

- [ ] T018b [US1] Implement `code/data/ngram.py` (Java) to build KenLM n‑gram model for the Java validation set.
  - **Dependency**: **T016** (Preprocess).
  - **Logic**: Build 5‑gram model from `data/processed/val_java/` (if Java data exists).
  - **Artifact**: `data/processed/kenlm_model_java.arpa`.

- [ ] T017 [US1] Implement `code/inference/engine.py` to run frozen LLM (Mistral‑7B primary) with retry logic, n‑gram normalization, and OOM fallback.
  - **Dependency**: **T018a** and **T018b** (KenLM models ready – PRIMARY GATE).
  - **Constraint**: Must load model with `device='cpu'` and enforce `torch.set_num_threads()`; no GPU usage.
  - **Model Strategy**:
    1. **PRIMARY**: Load `mistralai/Mistral-7B-v0.1`.
    2. **FALLBACK**: If Mistral‑7B fails to load or exceeds per‑chunk time, generate `data/results/scope_reduction_report.md` documenting the failure and then load `TinyLlama/TinyLlama-1.1B-Chat-v1.0`. If fallback also fails, abort pipeline.
  - **Retry Logic**: On `TimeoutError`, `ConnectionError`, or generic `OSError` (non‑OOM), retry up to 3 times with exponential backoff (factor 2). After retries, skip the chunk, log failure, and continue.
  - **Normalization**:
    1. Load the correct KenLM model per language (`kenlm_model_python.arpa` for Python chunks, `kenlm_model_java.arpa` for Java chunks).
    2. Verify KenLM outputs log‑probability in nats; convert if necessary.
    3. Compute `normalized_loss = token_loss - ngram_log_prob` (both in nats).
    4. Store `normalized_loss` per token.
  - **Artifact**: `data/processed/inference_results_python.jsonl`, `data/processed/inference_results_java.jsonl` (fields: `chunk_id`, `token_loss`, `entropy`, `normalized_loss`).

- [ ] T019 [US1] Implement `code/analysis/correlation.py` to compute Pearson/Spearman coefficients using the normalized loss.
  - **Dependency**: **T017** (Inference).
  - **Artifact**: `data/results/us1_correlation_stats.json`.

- [ ] T020 [US1] Implement `code/analysis/correlation.py` visualization.
  - **Dependency**: **T019** AND **T011b** (Variance Check).
  - **Logic**:
    1. Read `variance_null_report.json`; if present, write `us1_correlation_stats.json` with status `"no_correlation"` and exit gracefully.
    2. Otherwise generate scatter plots with regression lines (separate for Python and Java) using `seaborn.regplot`.
  - **Artifact**: `data/results/us1_correlation_plot.png` (if variance > 0) and updated `us1_correlation_stats.json`.

- [ ] T021a [US1] Implement `code/main.py` CLI argument parsing (e.g., `--phase`, `--config`).
  - **Artifact**: `code/main.py` (CLI section).

- [ ] T021b [US1] Generate DAG file `code/dag.yaml` defining the exact execution graph based on the dependencies described (Feasibility → Download → Preprocess → parallel {Variance Check, N‑Gram Python, N‑Gram Java} → Inference → Correlation → Visualization → Threshold Detection → Statistical Significance → Perturbation → Output).
  - **Artifact**: `code/dag.yaml`.

- [ ] T021c [US1] Implement `code/main.py` execution loop that reads `code/dag.yaml` and runs tasks in order, respecting parallel groups.
  - **Artifact**: `code/main.py` (Execution section).

- [ ] T022 [US1] Extend `code/analysis/correlation.py` for cross‑language validation.
  - **Dependency**: **T019** (Correlation results).
  - **Logic**: Compare Pearson/Spearman coefficients between Python and Java subsets, append comparison stats to `us1_correlation_stats.json`.
  - **Artifact**: Updated `data/results/us1_correlation_stats.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Correlation computed, plot generated, held‑out validation complete).

## Phase 2: User Story 2 - Non-Linear Threshold Detection (Priority: P2)

**Goal**: Identify structural thresholds where complexity/loss relationship shifts and perform sensitivity analysis.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US2] Add `tests/unit/test_threshold.py::test_piecewise_regression_handles_linear_data` and `tests/unit/test_threshold.py::test_piecewise_regression_detects_breakpoint`.

### Implementation for User Story 2

- [ ] T024 [US2] Implement `code/analysis/threshold.py` to apply piecewise regression/change‑point detection on US1 correlation data (FR‑005).
  - **Input**: `data/results/us1_correlation_stats.json`.
  - **Artifact**: `data/results/us2_threshold_candidates.json`.

- [ ] T025 [US2] Implement model comparison logic in `code/analysis/threshold.py` to evaluate linear vs. non‑linear models using AIC/BIC; record preference.
  - **Artifact**: Append `model_preference` to `us2_threshold_candidates.json`.

- [ ] T026 [US2] Implement sensitivity analysis in `code/analysis/threshold.py`.
  - **Dependency**: **T024** (Threshold candidates) and **T019** (Correlation data).
  - **Logic**:
    1. Read `perturbation_magnitude` and `bootstrap_count` from `feasibility_report.json`.
    2. **Perturbation Sweep**: For each magnitude value in the list defined by the report, re‑run the threshold detection and record the shift in identified threshold (`delta`).
    3. **Bootstrap Perturbation**: Perform `bootstrap_count` resamples of the chunk‑level data (with replacement) and recompute thresholds, recording shift distribution.
    4. Append `threshold_shifts_by_magnitude` and `dataset_perturbation_shifts` to `us2_threshold_candidates.json`.
  - **Artifact**: Updated `data/results/us2_threshold_candidates.json`.

- [ ] T027 [US2] Generate a markdown report summarizing thresholds and sensitivity results.
  - **Artifact**: `data/results/us2_threshold_report.md` with sections: Identified Threshold, Sensitivity Sweep Results (table), Justification.

**Checkpoint**: User Stories 1 & 2 functional independently.

## Phase 3: User Story 3 - Statistical Significance and Power Validation (Priority: P3)

**Goal**: Perform permutation tests, power analysis, and multiple‑comparison correction.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Add `tests/unit/test_stats.py::test_permutation_test_shuffles_labels` and `tests/unit/test_stats.py::test_permutation_test_computes_pvalue`.

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/analysis/stats.py` for cluster‑robust permutation test (block permutation at repository level) to compute p‑values (FR‑007).
  - **Artifact**: `data/results/us3_permutation_pvalue.json`.

- [ ] T030 [US3] Implement multiple‑comparison correction (Bonferroni/FDR) on hypothesis tests (FR‑008).
  - **Artifact**: `data/results/us3_corrected_pvalues.json`.

- [ ] T031a [US3] Perform post‑hoc power analysis using observed effect size, sample size, and alpha=0.05; compare to a priori target from T011.
  - **Dependency**: **T019** (Correlation) and **T029** (Permutation).
  - **Artifact**: `data/results/us3_power_analysis.json` (fields: `power_value`, `effect_size`, `sample_size`, `limitation_notes`).

- [ ] T031 [US3] Validate complexity metrics against the human‑labeled CodeXGLUE benchmark.
  - **Source**: `codeXGLUE/defect-detection` test split.
  - **Logic**:
    1. Attempt to load the benchmark. If unavailable, **raise RuntimeError** and abort the pipeline (must not silently continue).
    2. If loaded, compute Pearson r between the benchmark labels (or derived proxy) and the complexity metrics.
    3. Write `data/results/us3_validation_result.json` with `status: "validated"` and correlation details.
  - **Artifact**: `data/results/us3_validation_result.json`.

- [ ] T031b [US3] Generate limitation report if benchmark loading fails (this task will only run if T031 aborts, but is kept for completeness in case of future fallback logic).
  - **Dependency**: **T031**.
  - **Logic**: If `us3_validation_result.json` indicates missing benchmark, create `us3_limitation_report.md` describing the missing external validation and the impact on study conclusions.
  - **Artifact**: `data/results/us3_limitation_report.md` (only on failure).

**Checkpoint**: All user stories now functional with proper statistical rigor.

## Phase N: Polish & Cross‑Cutting Concerns

- [ ] T032a [P] Update README.md with usage instructions: Add "Running the Pipeline" and "Interpreting Results" sections.
  - **Artifact**: `README.md` (updated).
- [ ] T032b [P] Create docs/ with API reference: Generate `docs/api.md` with function signatures for `code/` modules.
  - **Artifact**: `docs/api.md`.
- [ ] T034a [P] Optimize T015 streaming logic: Refactor `code/data/download.py` to use chunked streaming with explicit `chunk_size=100` and `max_workers=4`.
  - **Artifact**: `code/data/download.py` (updated).
- [ ] T034b [P] Optimize T017 inference memory: Refactor `code/inference/engine.py` to use `torch.no_grad()` and explicit `batch_size=1` to keep memory < 6 GB.
  - **Artifact**: `code/inference/engine.py` (updated).
- [ ] T034c [P] Optimize T026 perturbation: Refactor `code/analysis/threshold.py` to use `joblib` for parallel processing of the bootstrap samples.
  - **Artifact**: `code/analysis/threshold.py` (updated).
- [ ] T035 [P] Implement comprehensive edge‑case tests covering network timeout, empty dataset, syntax errors, OOM, constant variance, and invalid file formats.
  - **Artifact**: `tests/unit/test_edge_cases.py`.
- [ ] T036 Run `quickstart.md` validation.
- [ ] T037 Update `state/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech.yaml` with data checksums.

## Dependencies & Execution Order

- **Phase 0 (Setup & Feasibility)**: No dependencies; T011 must complete before T015.
- **Phase 1 (User Story 1)**:
  1. T015 (Download) ← depends on T011c.
  2. T016 (Preprocess) ← depends on T015.
  3. Parallel block: T011b (Variance Check), T018a (KenLM Python), T018b (KenLM Java) ← all depend on T016.
  4. T017 (Inference) ← depends on T018a & T018b.
  5. T019 (Correlation) ← depends on T017.
  6. T020 (Visualization) ← depends on T019 & T011b.
  7. T021a‑c (CLI, DAG generation, execution loop) ← orchestrate all above.
  8. T022 (Cross‑language validation) ← depends on T019.
- **Phase 2 (User Story 2)**:
  - T024 ← depends on T019.
  - T025 ← depends on T024.
  - T026 ← depends on T024 & T019 (uses feasibility parameters).
  - T027 ← depends on T026.
- **Phase 3 (User Story 3)**:
  - T029 ← depends on T019.
  - T030 ← depends on T029.
  - T031 ← depends on T019 (and aborts if benchmark missing).
  - T031a ← depends on T019 & T029.
  - T031b ← runs only if T031 reports missing benchmark.
- **Phase N (Polish)**: Independent optimizations and documentation updates.

All tasks now respect data flow, resource constraints, and the strict requirements of the specification. 
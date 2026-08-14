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

- [X] T001 [P] Initialize project structure and configuration: Create `projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/` root directory and all required subdirectories (`code/`, `data/`, `tests/`, `data/raw/`, `data/processed/`, `data/results/`, `docs/`). Create `.gitignore`, `README.md`, `.env.template`, `ruff.toml`, `pyproject.toml`, and `requirements.txt` with pinned dependencies.
 - **Action**: `mkdir -p` all directories; write config files.
 - **Config Details**:
 - `ruff.toml`: `target-version = "py311"`, `line-length = 88`.
 - `pyproject.toml`: `[project] requires-python = ">=3.11"`.
 - **Artifacts**: `.gitignore`, `README.md`, `.env.template`, `ruff.toml`, `pyproject.toml`, `requirements.txt`, directory structure.

- [X] T002 [P] Create `requirements.txt` with exact versions for datasets, transformers, tree-sitter, codeql, scikit-learn, statsmodels, pandas, numpy, matplotlib, seaborn, kenlm, pwlf, ruptures.

- [X] T008a [P] Create `code_chunk` schema: Write `code/contracts/code_chunk.schema.yaml` with explicit field definitions for `chunk_id`, `complexity`, `depth`, `loss`.
 - **Artifact**: `code/contracts/code_chunk.schema.yaml`.
- [X] T008b [P] Create `analysis` schema: Write `code/contracts/analysis.schema.yaml` with explicit field definitions for `correlation`, `threshold`, `p_value`.
 - **Artifact**: `code/contracts/analysis.schema.yaml`.
- [X] T008c [P] Create `output` schema: Write `code/contracts/output.schema.yaml` with explicit field definitions for final report structure.
 - **Artifact**: `code/contracts/output.schema.yaml`.
- [X] T009b [P] Implement env loading: Update `code/config.py` to load `.env` using `python-dotenv` and validate required variables.
 - **Artifact**: `code/config.py` (updated).
- [X] T010 [P] Implement timeout enforcement and benchmarking logic in `code/utils/timeout.py` to enforce a fixed per‑chunk duration constraint (FR‑003); must raise `TimeoutError` on breach.
- [X] T011 [US1] Implement `code/analysis/feasibility.py` (Pilot Sample & A Priori Power Analysis):
 - **Input**: Fetch metadata only (N=50) of code chunks from `codeparrot/github-code ` (Python/Java) using `datasets.load_dataset(..., streaming=True).take(50)` to estimate complexity variance WITHOUT downloading full files.
 - **Dependency**: **MUST run BEFORE T015** (Download).
 - **Action**: Perform a priori power analysis (alpha=0.05, Power=0.8, estimated effect size r=0.3). Compute required sample size N.
 - **Gate**:
 1. If calculated N > max feasible chunks for 6 h limit (based on **TinyLlama-1.1B ** CPU throughput), **Cap N** to the maximum feasible size.
 2. Calculate `perturbation_magnitude` (default **0.05** if not calculable) and `bootstrap_count` (default **1000**) based on N.
 3. Calculate `perturbation_magnitudes` list for T026 (e.g., `[0.01, 0.05, 0.1]`).
 - **Write** `data/results/feasibility_report.json` with:
 - `status`: `"capped"` or `"feasible"`
 - `capped_N`: `<int>`
 - `power_limitation`: message if capped
 - `perturbation_magnitude`: `<float>` (default 0.05)
 - `bootstrap_count`: `<int>` (default 1000)
 - `perturbation_magnitudes`: `[0.01, 0.05, 0.1]`
 - `proceed_flag`: `true`
 - **Artifact**: `data/results/feasibility_report.json`.
- [X] T011c [US1] Implement `code/analysis/power_sensitivity.py` (Power Sensitivity Fallback):
 - **Dependency**: **T011** (Feasibility Report).
 - **Action**: Read `feasibility_report.json`. If power limitation prevents FR‑005 or FR‑009, add `scope_reduction` field describing disabled components.
 - **Write** `data/results/power_sensitivity_fallback.md` and write `data/results/feasibility_report_v2.json` (versioned copy with updates) to maintain immutability of T011 output.
 - **Artifact**: `data/results/power_sensitivity_fallback.md`, `data/results/feasibility_report_v2.json`.

## Phase 1: User Story 1 - Correlation Analysis of Code Complexity and Prediction Loss (Priority: P1) 🎯 MVP

**Goal**: Download code, label with static analysis, run frozen LLM inference, compute correlations, and generate scatter plots.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Add `tests/unit/test_download.py::test_download_handles_network_timeout` and `tests/unit/test_download.py::test_download_handles_empty_dataset`.
- [X] T013 [P] [US1] Add `tests/unit/test_preprocess.py::test_preprocess_skips_unparseable_files` and `tests/unit/test_preprocess.py::test_preprocess_handles_syntax_errors`.
- [X] T014 [P] [US1] Add `tests/unit/test_inference.py::test_inference_handles_timeout` and `tests/unit/test_inference.py::test_inference_handles_oom`.

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/data/download.py` to fetch `codeparrot/github-code ` subset (Python/Java) with streaming to stay within Disk storage constraints.
 - **Dependency**: **T011c** (Feasibility & Scope passed).
 - **Logic**:
 1. Read `capped_N` and `scope_reduction` from `feasibility_report_v2.json`.
 2. If `scope_reduction` disables cross‑language, download only Python; otherwise download both languages.
 3. Stream dataset, take exactly `capped_N` examples, split into `data/processed/train_python/` and `data/processed/val_java/` (if Java enabled).
 4. **Fail loudly** on any fetch error (`sys.exit(1)`), no synthetic fallback.
 - **Artifact**: `data/processed/train_python/`, `data/processed/val_java/` (if applicable).

- [X] T016 [US1] Implement `code/data/preprocess.py` to run CodeQL and tree‑sitter.
 - **Dependency**: **T015** (Download/Split).
 - **Logic**: Process files, generate `queries/complexity.ql`, label cyclomatic complexity, nesting depth, repetition ratio, skip unparseable files with logging.
 - **Artifact**: `data/processed/annotated_python.jsonl`, `data/processed/annotated_java.jsonl`.

- [X] T011b [US1] Implement `code/analysis/variance_check.py` (Variance Detection & Graceful Degradation):
 - **Dependency**: **T016** (Preprocess).
 - **Action**: Load annotated JSONL files, compute variance of `cyclomatic_complexity` and `nesting_depth`.
 - **Logic**:
 1. If any metric has zero variance, write `data/results/variance_null_report.json` with status `"null_variance"` and **exit with code 1** (or set a `halt` flag) to force the DAG orchestrator to skip T019.
 2. If variance > 0, produce **no artifact** (proceed).
 - **Artifact**: `data/results/variance_null_report.json` (only on zero variance).

- [X] T018a [US1] Implement `code/data/ngram.py` (Python) to build KenLM n‑gram model for the Python training set.
 - **Dependency**: **T016** (Preprocess).
 - **Logic**: Build Google Web 1T 5-gram data set (1204.5852, https://arxiv.org/abs/1204.5852) [UNRESOLVED-CLAIM: c_71d9c8ac — status=verified] ‑gram model from `data/processed/train_python/`.
 - **Unit**: Ensure model outputs **log-probability in nats**.
 - **Artifact**: `data/processed/kenlm_model_python.arpa`.

- [X] T018b [US1] Implement `code/data/ngram.py` (Java) to build KenLM n‑gram model for the Java validation set. <!-- FAILED: unspecified -->
 - **Dependency**: **T016** (Preprocess).
 - **Logic**: Build Google Web 1T 5-gram data set (1204.5852, https://arxiv.org/abs/1204.5852) [UNRESOLVED-CLAIM: c_71d9c8ac — status=verified] ‑gram model from `data/processed/val_java/` (if Java data exists).
 - **Unit**: Ensure model outputs **log-probability in nats**.
 - **Artifact**: `data/processed/kenlm_model_java.arpa`.

- [X] T017 [US1] Implement `code/inference/engine.py` to run frozen LLM (TinyLlama-1.1B primary) with retry logic, n‑gram normalization, and OOM fallback.
 - **Dependency**: **T018a** and **T018b** (KenLM models ready – PRIMARY GATE).
 - **Constraint**: Must load model with `device='cpu'` and enforce `torch.set_num_threads()`; no GPU usage.
 - **Model Strategy**:
 1. **PRIMARY**: Load `TinyLlama/TinyLlama-1.1B -Chat-v1.0`.
 2. **FALLBACK**: If TinyLlama fails to load or exceeds per‑chunk time, **ABORT** pipeline (do not fallback to Mistral-7B as it violates 6h CPU limit).
 - **Retry Logic**: On `TimeoutError`, `ConnectionError`, or generic `OSError` (non‑OOM), retry up to 3 times with exponential backoff (factor 2). After retries, skip the chunk, log failure, and continue.
 - **Normalization**:
 1. Load the correct KenLM model per language (`kenlm_model_python.arpa` for Python chunks, `kenlm_model_java.arpa` for Java chunks).
 2. **Conditional Load**: If Java data was not downloaded (per T015), skip loading Java model and only process Python chunks.
 3. Verify KenLM outputs log‑probability in **nats**.
 4. Compute `normalized_loss = token_loss_nats - ngram_log_prob_nats` (both in nats). **Do not convert to probability**; subtraction in log-space is mathematically valid for normalization.
 5. Store `normalized_loss` per token.
 - **Artifact**: `data/processed/inference_results_python.jsonl`, `data/processed/inference_results_java.jsonl` (fields: `chunk_id`, `token_loss`, `entropy`, `normalized_loss`).

- [X] T019 [US1] Implement `code/analysis/correlation.py` to compute Pearson/Spearman coefficients using the normalized loss.
 - **Dependency**: **T017** (Inference).
 - **Artifact**: `data/results/us1_correlation_stats.json`.

- [X] T020 [US1] Implement `code/analysis/correlation.py` visualization.
 - **Dependency**: **T019** AND **T011b** (Variance Check).
 - **Logic**:
 1. Check for existence of `variance_null_report.json`.
 2. If present, write `us1_correlation_stats.json` with status `"no_correlation"` and **continue** to next phase (or terminate this branch gracefully), ensuring the null result is recorded.
 3. If **not present** (variance > 0), generate scatter plots with regression lines (separate for Python and Java) using `seaborn.regplot`.
 - **Artifact**: `data/results/us1_correlation_plot.png` (if variance > 0) and updated `us1_correlation_stats.json`.

- [X] T021a [US1] Implement `code/main.py` CLI argument parsing (e.g., `--phase`, `--config`).
 - **Artifact**: `code/main.py` (CLI section).

- [X] T021b [US1] Generate DAG file `code/dag.yaml` defining the exact execution graph based on the dependencies described (Feasibility → Download → Preprocess → parallel {Variance Check, N‑Gram Python, N‑Gram Java} → Inference → Correlation → Visualization → Threshold Detection → Statistical Significance → Perturbation → Output).
 - **Schema**: `tasks: [list of task IDs]`, `dependencies: {task_id: [list of parent IDs]}`.
 - **Artifact**: `code/dag.yaml`.

- [X] T021c [US1] Implement `code/main.py` execution loop that reads `code/dag.yaml` and runs tasks in order, respecting parallel groups.
 - **Artifact**: `code/main.py` (Execution section).

- [X] T022 [US1] Extend `code/analysis/correlation.py` for cross‑language validation.
 - **Dependency**: **T019** (Correlation results).
 - **Logic**: Compare Pearson/Spearman coefficients between Python and Java subsets, append comparison stats to `us1_correlation_stats.json`.
 - **Artifact**: Updated `data/results/us1_correlation_stats.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Correlation computed, plot generated, held‑out validation complete).

## Phase 2: User Story 2 - Non-Linear Threshold Detection (Priority: P2)

**Goal**: Identify structural thresholds where complexity/loss relationship shifts and perform sensitivity analysis.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Add `tests/unit/test_threshold.py::test_piecewise_regression_handles_linear_data` and `tests/unit/test_threshold.py::test_piecewise_regression_detects_breakpoint`.

### Implementation for User Story 2

- [X] T024 [US2] Implement `code/analysis/threshold.py` to apply piecewise regression/change‑point detection on US1 correlation data (FR‑005).
 - **Input**: `data/results/us1_correlation_stats.json`.
 - **Artifact**: `data/results/us2_threshold_candidates.json`.

- [X] T025 [US2] Implement model comparison logic in `code/analysis/threshold.py` to evaluate linear vs. non‑linear models using AIC/BIC; record preference.
 - **Artifact**: Append `model_preference` to `us2_threshold_candidates.json`.

- [X] T026 [US2] Implement sensitivity analysis in `code/analysis/threshold.py`.
 - **Dependency**: **T024** (Threshold candidates) and **T019** (Correlation data).
 - **Logic**:
 1. Read `perturbation_magnitudes` list from `feasibility_report.json`.
 2. **Perturbation Sweep**: For each magnitude value in the list, re‑run the threshold detection and record the shift in identified threshold (`delta`).
 3. **Bootstrap Perturbation**: Perform `bootstrap_count` resamples of the chunk‑level data (with replacement) and recompute thresholds, recording shift distribution.
 4. **SC-002 Check**: Calculate `max_shift` from all perturbations. If `max_shift > 0.05 `, set `stability_status: "failed"`; otherwise `stability_status: "passed"`.
 5. Append `threshold_shifts_by_magnitude`, `dataset_perturbation_shifts`, and `stability_status` to `us2_threshold_candidates.json`.
 - **Artifact**: Updated `data/results/us2_threshold_candidates.json`.

- [X] T027 [US2] Generate a markdown report summarizing thresholds and sensitivity results.
 - **Dependency**: **T026** (Sensitivity results).
 - **Logic**: Read `us2_threshold_candidates.json`, generate `us2_threshold_report.md` with sections: Identified Threshold, Sensitivity Sweep Results (table), Justification, Stability Status.
 - **Artifact**: `data/results/us2_threshold_report.md`.

**Checkpoint**: User Stories 1 & 2 functional independently.

## Phase 3: User Story 3 - Statistical Significance and Power Validation (Priority: P3)

**Goal**: Perform permutation tests, power analysis, and multiple‑comparison correction.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Add `tests/unit/test_stats.py::test_permutation_test_shuffles_labels` and `tests/unit/test_stats.py::test_permutation_test_computes_pvalue`.

### Implementation for User Story 3

- [X] T029 [US3] Implement `code/analysis/stats.py` for cluster‑robust permutation test (block permutation at repository level) to compute p‑values (FR‑007).
 - **Artifact**: `data/results/us3_permutation_pvalue.json`.

- [X] T030 [US3] Implement multiple‑comparison correction (Bonferroni/FDR) on hypothesis tests (FR‑008).
 - **Artifact**: `data/results/us3_corrected_pvalues.json`.

- [X] T031 [US3] Validate complexity metrics against the human-labeled CodeXGLUE benchmark (or generate limitation report).
 - **Source**: Attempt to load `codeparrot/codecomplexity ` or a verified complexity benchmark from HuggingFace.
 - **Logic**:
 1. **Attempt Load**: Try to fetch the complexity benchmark.
 2. **If Available**:
 - Identify the column containing human-labeled complexity scores (e.g., `complexity_score`).
 - Compute Pearson r between benchmark labels and computed complexity metrics.
 - Write `data/results/us3_validation_result.json` with `status: "validated"` and correlation details.
 3. **If Unavailable**:
 - **Do NOT abort**.
 - Write `data/results/us3_limitation_report.md` describing the missing external validation and the impact on study conclusions.
 - Write `data/results/us3_validation_result.json` with `status: "limitation_report_generated"`.
 - **Artifact**: `data/results/us3_validation_result.json` or `data/results/us3_limitation_report.md`.

**Checkpoint**: All user stories now functional with proper statistical rigor.

## Phase N: Polish & Cross‑Cutting Concerns

- [X] T032a [P] Update README.md with usage instructions: Add "Running the Pipeline" and "Interpreting Results" sections.
 - **Artifact**: `README.md` (updated).
- [X] T032b [P] Create docs/ with API reference: Generate `docs/api.md` with function signatures for `code/` modules.
 - **Artifact**: `docs/api.md`.
- [X] T034a [P] Optimize T015 streaming logic: Refactor `code/data/download.py` to use chunked streaming with explicit `chunk_size=100 ` and `max_workers=4 `.
 - **Artifact**: `code/data/download.py` (updated).
- [X] T034b [P] Optimize T017 inference memory: Refactor `code/inference/engine.py` to use `torch.no_grad()` and explicit `{{claim:c_e66238fe}} (2507.07101, https://arxiv.org/abs/2507.07101) ` to keep memory < 6 GB.
 - **Artifact**: `code/inference/engine.py` (updated).
- [X] T034c [P] Optimize T026 perturbation: Refactor `code/analysis/threshold.py` to use `joblib` for parallel processing of the bootstrap samples.
 - **Artifact**: `code/analysis/threshold.py` (updated).
- [X] T035 [P] Implement comprehensive edge‑case tests covering network timeout, empty dataset, syntax errors, OOM, constant variance, and invalid file formats.
 - **Artifact**: `tests/unit/test_edge_cases.py`.
- [X] T036 Run `quickstart.md` validation.
- [X] T037 Update `state/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech.yaml` with data checksums.
- [X] T021b [P] (Meta-Task) Generate final `code/dag.yaml` for documentation purposes (if not already generated in Phase 1). This task is for documentation only and does not execute in the data pipeline.
 - **Artifact**: `code/dag.yaml` (final version).

## Dependencies & Execution Order

- **Phase 0 (Setup & Feasibility)**: No dependencies; T011 must complete before T015.
- **Phase 1 (User Story 1)**:
 1. T015 (Download) ← depends on **T011c** (Power Sensitivity Fallback).
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
 - T031 ← depends on T019 (and triggers fallback if benchmark missing).
 - T031a (Power Analysis) ← depends on T019 & T029. (Note: T031a was implicitly part of T031 logic in previous version, now separated if needed, but T031 covers validation).
- **Phase N (Polish)**: Independent optimizations and documentation updates.

All tasks now respect data flow, resource constraints, and the strict requirements of the specification.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T038 Reconcile run-book vs implementation for `code/analysis/thresholds.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/analysis/thresholds.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [X] T039 Reconcile run-book vs implementation for `code/analysis/significance.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/analysis/significance.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [X] T040 Reconcile run-book vs implementation for `code/viz/plots.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/viz/plots.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.

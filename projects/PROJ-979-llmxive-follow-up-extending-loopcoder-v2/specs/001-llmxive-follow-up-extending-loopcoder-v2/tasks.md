---
description: "Task list template for feature implementation"
---

# Tasks: llmXive follow-up: extending "LoopCoder-v2: Only Loop Once for Efficient Test-Time Computation Scali"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-loopcoder-v2/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, and configuration definition

- [x] T000-config [D] **Environment & Configuration Setup**: Create `code/src/config.py` with concrete defaults as Python variables. **Logic**: 1. Define `NON_INFERIORITY_DELTA = 0.05`, `ENTROPY_N_SAMPLES = 10`, `CONVERGENCE_K_RANGE = [1, 2, 3]`, `STRATA_THRESHOLD = 50`, `MODEL_TEMP = 0.7`, `MODEL_TOP_P = 0.95`, `RANDOM_SEED = 42`. 2. Define paths for datasets and model. 3. Ensure `NON_INFERIORITY_DELTA` is exported for downstream modules. **Artifact**: `code/src/config.py`. **Verification**: Verify file exists at `code/src/config.py`, is valid Python, and contains variables `NON_INFERIORITY_DELTA`, `ENTROPY_N_SAMPLES`, `CONVERGENCE_K_RANGE`, `STRATA_THRESHOLD`, `MODEL_TEMP`, `MODEL_TOP_P`, `RANDOM_SEED` with the specified values. **Dependencies**: None.
- [x] T000-seed-setup [D] **Random Seed Setup**: Implement global random seed pinning function in `code/src/utils.py`. **Logic**: 1. Create function `set_global_seed(seed: int = 42)`. 2. Set `random.seed(seed)`, `numpy.random.seed(seed)`, `torch.manual_seed(seed)`, and `torch.cuda.manual_seed_all(seed)`. 3. Set `os.environ['PYTHONHASHSEED'] = str(seed)`. **Artifact**: `code/src/utils.py` (updated). **Verification**: Verify function exists and sets all required seeds. **Dependencies**: None.
- [x] T000-seed-verify [D] **Seed Verification**: Create `code/tests/dummy_seed_test.py` to test seed reproducibility. Run `python code/tests/dummy_seed_test.py` twice with seed=42. Compare outputs. Assert equality. **Artifact**: `data/seed_verification.json`. **Schema**: `{seed: 42, hash: <sha256>, status: 'ok'}`. **Dependencies**: T000-seed-setup.
- [x] T000-model [D] **Model Availability Check**: Verify the existence of a CodeLlama instruct model. **Logic**: 1. Attempt to load the model config using `transformers.AutoConfig.from_pretrained`. 2. If the model is not cached locally and `HF_TOKEN` is available, trigger a download verification (or document the required download command). 3. If the model is missing and cannot be downloaded, raise a clear error `ModelNotFoundError`. 4. **Artifact**: `data/model_status.json`. **Schema**: `{status: 'available' | 'missing', path: str, message: str}`. **Dependencies**: T000-config.

- [x] T001a [P] **Create Project Directory Structure**: Create `projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/` with sub‑directories `data/`, `code/`, `paper/`, `state/`, `contracts/`. **Artifact**: `structure_check.json`. **Verification**: Verify directories exist.
- [x] T001b [D] **Verify Directory Structure**: Read `structure_check.json` and assert all required directories are present. **Artifact**: `structure_verify.json`.
- [x] T001c [D] **Generate Structure Report**: Summarize directory creation results into `data/structure_report.json`. **Artifact**: `data/structure_report.json`. **Dependencies**: T001b.

- [x] T002 [P] **Initialize Python project**: Write `code/requirements.txt` with pinned versions for `transformers`, `torch`, `scikit-learn`, `pandas`, `datasets`, `pytest`, `docker`, `psutil`, `lifelines`, `statsmodels`.

- [x] T003 [D] **Project Configuration Files**: Create `.ruff.toml` and `pyproject.toml` in `code/`. **Logic**:
 1. Create `.ruff.toml` with `line-length = 88`, `target-version = "py310"`, `select = ["E", "F", "W", "I"]`.
 2. Create `pyproject.toml` with `[tool.black]` section: `line-length = 88`, `target-version = ['py']`.
 3. Verify both files exist and contain valid TOML syntax.
 **Artifact**: `.ruff.toml`, `pyproject.toml`. **Dependencies**: None.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a [P] **Implement `code/src/data_loader.py` function `fetch_datasets()`**: Fetch HumanEval and MBPP via `datasets.load_dataset`. Save raw copies to `data/raw/`.
- [X] T004b-raw [P] **Checksum Raw Datasets**: Compute SHA256 checksums for ALL files in `data/raw/` and write them to `data/checksums_raw.txt`. **Logic**: 1. Iterate over all files in `data/raw/`. 2. Compute SHA256 hash for each file. 3. Write to `data/checksums_raw.txt` in format: `<sha256_hash> <filename>`. **Artifact**: `data/checksums_raw.txt`. **Dependencies**: T004a.
- [X] T004c [D] **Implement `code/src/data_loader.py` function `stratify_data()`**: Apply stratified sampling by difficulty (using 'difficulty' column or hashing 'task_id'). Flag strata with <50 samples as 'underpowered' in `data/processed/strata_log.json`. **Use threshold=50** (read from `code/src/config.py` key `STRATA_THRESHOLD`; if missing, use default 50). **Pre-check**: Verify `code/src/config.py` exists and contains `STRATA_THRESHOLD`. **Artifact**: `data/processed/strata_log.json`. **Dependencies**: T004b-raw.
- [X] T004d [D] **Implement `code/src/data_loader.py` function `save_splits()`**: Save processed splits to `data/processed/splits.json`. **Schema**: `{train: [...], test: [...]}`. **Verification**: Verify file exists and contains valid JSON with required keys. **Dependencies**: T004c.
- [X] T004f-split-logic [D] **Generate Full Dataset Splits (No Filtering)**: Read `data/processed/splits.json` and `data/processed/strata_log.json`. Generate `data/processed/full_splits.json` containing ALL samples (including underpowered strata). **Logic**: 1. Load `splits.json`. 2. DO NOT filter out any strata. 3. Write `full_splits.json`. **Artifact**: `data/processed/full_splits.json`. **Dependencies**: T004d, T004c.
- [X] T004g [D] **Generate Unseen Validation Set**: Create `code/src/data_loader.py` function `generate_unseen_set`. Split the **training** set (not test) into a held‑out test subset and an `unseen_validation` subset (stratified, 50/50). This ensures strict disjointness from the convergence test set. Save to `data/processed/unseen_validation_set.csv` and checksum it. **Dependencies**: T004d.
- [X] T004h [D] **Verify Set Disjointness**: Ensure `task_id` sets of `data/processed/splits.json` (test) and `data/processed/unseen_validation_set.csv` (from training) are disjoint. Log result to `data/processed/disjoint_verification.json`. **Dependencies**: T004g.
- [X] T004i [D] **Generate Baseline Pass@1**: Load literature values or fetch them, then save to `data/processed/baseline_pass1.json`. **Dependencies**: T004f-split-logic.
- [X] T004b-processed [D] **Checksum Processed Datasets**: Compute SHA256 checksums for all files in `data/processed/` (excluding temporary files) and write to `data/checksums_processed.txt`. **Dependencies**: T004f-split-logic, T004g, T004h, T004i.

- [X] T005 [P] **Create `code/src/entropy.py` stub** with function `def extract_entropy(prompt: str, model, n_samples: int = 10) -> float`. **Dependencies**: T004h, T000-seed-setup.
- [x] T005d [P] **Define FLOPs utility** `def calculate_flops(model_params: int, seq_len: int, k: int) -> float`. **Dependencies**: None.
- [x] T005e [P] **Implement resource monitoring** `capture_metrics(mode: str)` saving to `data/processed/resource_metrics.json`. **Dependencies**: None.
- [X] T006 [P] **Create `code/src/inference.py` stub** with `def run_inference(prompt: str, model, k: int) -> dict`. **Artifact schema** as previously defined. **Dependencies**: T004f-split-logic, T000-seed-setup.
- [X] T007 [P] **Define dataclasses** `InputProblem` and `ConvergenceTrajectory` in `code/src/models.py`. **Dependencies**: T004f-split-logic.
- [X] T008b [P] **Create `paper/model_substitution_rationale.md`** (unchanged). **Dependencies**: T000-config.
- [X] T009 [P] **Implement Docker sandbox** (`code/Dockerfile`, `code/docker-compose.yml`). **Dependencies**: None.
- [X] T009b [D] **Build Unseen Sandbox Image**: Build `entropy-sandbox:latest` from `code/Dockerfile.unseen`. Verify it can run a simple command. **Artifact**: `docker_image_status.json`. **Dependencies**: T009.

---

## Phase 3a: User Story 1 - Core Correlation Analysis (Data Generation) (Priority: P1) 🎯 MVP

### Tests (optional)

- [X] T010 [P] [US1] **Unit test for entropy clustering** (`code/tests/test_entropy.py`). **Dependencies**: T005.
- [X] T011 [P] [US1] **Integration test for pipeline** (`code/tests/test_analysis.py`). **Dependencies**: T005, T006.

### Implementation

- [ ] T012a [US1] [D] **Entropy Extraction Pipeline**: Load model and `data/processed/full_splits.json`. For each problem, generate N=10 samples (`temperature=0.7`, `top_p=0.95`). Normalize each sample with `ast.unparse`, hash with SHA256, cluster by hash, compute Shannon entropy over cluster probabilities. **Crucial**: Load `data/processed/unseen_validation_set.csv` (from T004g) as the **sole** reference for clustering. Do **not** use test data for clustering. Assign minimal entropy `1e-9` for deterministic outputs. Log exclusions to `data/processed/exclusion_log.json`. Save results to `data/processed/entropy_results.csv` (`{task_id, entropy, exclusion_reason}`). **Command**: `python code/src/entropy.py --input data/processed/full_splits.json --output data/processed/entropy_results.csv --reference data/processed/unseen_validation_set.csv --device cuda --seed 42`. **Dependencies**: T004f-split-logic, T004g, T000-model.

- [ ] T013a [US1] [D] **Core Convergence Inference (k=1‑3)**: Load model and `data/processed/full_splits.json`. For each problem, run **iterative refinement** for k ∈ {1,2,3}: the output of step k-1 is fed as input to step k. Record `output`, `is_correct` (compare to reference), `first_correct_step` (the smallest k where `is_correct` is true), and set `censored` flag to `True` if no correct answer by k=3. Also compute `time_to_event` = `first_correct_step` (or `k_max` if censored). Write directly to `data/processed/convergence_results_core.csv` with schema `{task_id, k, output, is_correct, first_correct_step, censored, time_to_event}`. Manage RNG deterministically: reset seed before each k iteration using `set_global_seed`. **Command**: `python code/src/inference.py --input data/processed/full_splits.json --output data/processed/convergence_results_core.csv --k_range 1 2 3 --device cuda --seed 42`. **Dependencies**: T004f-split-logic, T006, T000-model.

- [ ] T013a-full [US3] [D] **Full Convergence Inference (k=1‑3) for Mixed Effects**: Load model and `data/processed/full_splits.json`. For each problem, run **iterative refinement** for k ∈ {1,2,3}. Record `output`, `is_correct`, `first_correct_step`, `censored`, `time_to_event`. Write to `data/processed/convergence_results_core_full.csv`. **Logic**: Same as T013a but explicitly for the mixed-effects model input. **Command**: `python code/src/inference.py --input data/processed/full_splits.json --output data/processed/convergence_results_core_full.csv --k_range 1 2 3 --device cuda --seed 42`. **Dependencies**: T004f-split-logic, T006, T000-model.

- [ ] T013a-verify [D] **Verify Censored Logic**: Load `convergence_results_core.csv` and assert rows with `k=3` and `is_correct=False` have `censored=True` and `time_to_event=3`. Raise error if mismatch. **Artifact**: `data/processed/censored_verification.json`. **Dependencies**: T013a.

- [ ] T013b [US3] [D] **Sensitivity Convergence (k=4)**: Load model and `data/processed/full_splits.json` (including underpowered strata). Run inference for k=4. Update `first_correct_step` if still null, adjust `censored` accordingly, and write to `data/processed/convergence_results_sensitivity.csv`. **Logic**: Must use `full_splits.json` to include underpowered strata for robustness analysis. **Command**: `python code/src/inference.py --input data/processed/full_splits.json --output data/processed/convergence_results_sensitivity.csv --k_range 4 --device cuda --seed 42`. **Dependencies**: T013a-full, T006, T000-model.

- [ ] T015a-strata [US1] [D] **Per‑Stratum Correlation**: Load `entropy_results.csv` and `convergence_results_core.csv`. Group by stratum (from `strata_log.json`). For **all** strata (including underpowered), compute Spearman ρ and p‑value between `entropy` and `first_correct_step`. Save to `data/processed/stratum_pvalues.json`. **Dependencies**: T012a, T013a, T004c.

- [ ] T015a-strata-exec [US1] [D] **Execute Per‑Stratum Correlation**: Run `python code/src/analysis.py --mode strata --entropy data/processed/entropy_results.csv --convergence data/processed/convergence_results_core.csv --strata data/processed/strata_log.json --output data/processed/stratum_pvalues.json`. **Dependencies**: T015a-strata.

- [ ] T015-correlation [US1] [D] **Spearman Correlation**: Merge `entropy_results.csv` with `convergence_results_core.csv` on `task_id`. Explicitly merge `time_to_event` from the convergence file. Compute Spearman ρ and p‑value between `entropy` and `first_correct_step`. Save to `data/processed/correlation_spearman.json`. **Dependencies**: T012a, T013a.

- [ ] T015-correlation-exec [US1] [D] **Execute Spearman Correlation**: Run `python code/src/analysis.py --mode spearman --entropy data/processed/entropy_results.csv --convergence data/processed/convergence_results_core.csv --output data/processed/correlation_spearman.json`. **Dependencies**: T015-correlation.

- [ ] T015-survival [US1] [D] **Kaplan‑Meier & Cox PH**: Using merged data, prepare survival input (time=`time_to_event`, event=`~censored`). Fit `lifelines.KaplanMeierFitter` and `CoxPHFitter` with `entropy` as covariate. Save results to `data/processed/correlation_survival.json`. **Dependencies**: T012a, T013a.

- [ ] T015-survival-exec [US1] [D] **Execute Survival Analysis**: Run `python code/src/analysis.py --mode survival --convergence data/processed/convergence_results_core.csv --output data/processed/correlation_survival.json`. **Dependencies**: T015-survival.

- [ ] T015-power [US1] [D] **Power Analysis**: Based on sample size and observed effect, compute MDES and power; store in `data/processed/correlation_power.json`. **Dependencies**: T015-correlation-exec.

- [ ] T015-power-exec [US1] [D] **Execute Power Analysis**: Run `python code/src/analysis.py --mode power --input data/processed/correlation_spearman.json --output data/processed/correlation_power.json`. **Dependencies**: T015-power.

- [ ] T015b-adjust [US1] [D] **Multiple‑Comparison Correction (Strata)**: Read per‑stratum p‑values from `data/processed/stratum_pvalues.json`. Apply Holm‑Bonferroni to **all** strata. Save to `data/processed/adjusted_pvalues.json`. **Dependencies**: T015a-strata-exec.

- [ ] T015b-adjust-exec [US1] [D] **Execute Multiple‑Comparison Correction**: Run `python code/src/analysis.py --mode holm-bonferroni --input data/processed/stratum_pvalues.json --output data/processed/adjusted_pvalues.json`. **Dependencies**: T015b-adjust.

- [ ] T038-merge-results [US1] [D] **Merge Correlation Artifacts**: Combine the three JSON files into `data/processed/correlation_results.json`. **Dependencies**: T015-correlation-exec, T015-survival-exec, T015-power-exec.

- [ ] T037 [US1] [D] **Final Survival Summary**: Run any final post‑processing if needed; produce `data/processed/correlation_results_final.json`. **Dependencies**: T038-merge-results.

---

## Phase 4: User Story 2 - Dynamic Router Simulation (Priority: P2)

### Tests (optional)

- [X] T017 [P] [US2] **Unit test for logistic regression** (`code/tests/test_analysis.py`). **Dependencies**: T019-exec.
- [X] T018 [P] [US2] **Statistical test validation** (`code/tests/test_analysis.py`). **Dependencies**: T019-exec.

### Implementation

- [ ] T019-prep [US2] [D] **Generate Cross-Validation Splits**: Load `entropy_results.csv`, `convergence_results_core.csv`, and `baseline_pass1.json`. Generate 5 stratified folds based on `optimal_k` (derived from `first_correct_step`). Save the split indices to `data/processed/router_cv_folds.json`. **Logic**: Use `sklearn.model_selection.StratifiedKFold` with `n_splits=5`, `shuffle=True`, `random_state=42`. **Artifact**: `data/processed/router_cv_folds.json`. **Dependencies**: T012a, T013a, T004i.

- [ ] T019-prep-verify [US2] [D] **Verify Cross-Validation Splits**: Load `data/processed/router_cv_folds.json`. Verify: 1. Exactly 5 folds exist. 2. Each fold is stratified by `optimal_k`. 3. No overlap between folds. 4. Random seed 42 was used. Save verification result to `data/processed/router_cv_folds_verified.json`. **Dependencies**: T019-prep.

- [ ] T019 [US2] [D] **Train Ordinal Logistic Regression Router**: Load `entropy_results.csv`, `convergence_results_core.csv`, `baseline_pass1.json`, and `data/processed/router_cv_folds_verified.json`. Derive target variable `optimal_k` = minimum k required for correctness. Feature set = `entropy` + `baseline_pass1`. Perform **5‑fold cross‑validation** using `statsmodels` `OrdinalGEE` with `strata` option to predict the ordinal target. Aggregate accuracy, F1, and confusion matrix. Save model to `data/processed/router_model.pkl` and metrics to `data/processed/router_metrics.json`. **Command**: `python code/src/analysis.py --mode train_router --entropy data/processed/entropy_results.csv --convergence data/processed/convergence_results_core.csv --baseline data/processed/baseline_pass1.json --cv_folds data/processed/router_cv_folds_verified.json --output data/processed/router_model.pkl --metrics data/processed/router_metrics.json`. **Dependencies**: T019-prep-verify, T004i.

- [ ] T019-exec [US2] [D] **Execute Router Training**: Run the command defined in T019. **Dependencies**: T019.

- [ ] T019b [US2] [D] **Generate Router Predictions**: Apply trained router to test set (filtered splits) to produce `router_results.csv` with `{task_id, predicted_k, actual_k, accuracy, is_censored}`. **Command**: `python code/src/analysis.py --mode predict_router --model data/processed/router_model.pkl --input data/processed/full_splits.json --output data/processed/router_results.csv`. **Dependencies**: T019-exec.

- [ ] T019b-exec [US2] [D] **Execute Router Predictions**: Run the command defined in T019b. **Dependencies**: T019b.

- [ ] T020 [US2] [D] **Router vs Random Baseline Evaluation**: Compare router accuracy against random baseline (`k=1` for all). Perform paired t‑test; store results in `router_accuracy_test.json`. **Dependencies**: T019b-exec.

- [ ] T020-exec [US2] [D] **Execute Router vs Random**: Run `python code/src/analysis.py --mode compare_random --input data/processed/router_results.csv --output data/processed/router_accuracy_test.json`. **Dependencies**: T020.

- [ ] T020a [US2] [D] **Static k=2 Baseline Metrics**: Compute FLOPs and accuracy for always using `k=2` on the filtered test set. Save to `static_k2_baseline.json` (`{total_flops, accuracy}`). **Command**: `python code/src/analysis.py --mode static_baseline --convergence data/processed/convergence_results_core.csv --output data/processed/static_k2_baseline.json`. **Dependencies**: T013a.

- [ ] T020a-exec [US2] [D] **Execute Static Baseline**: Run the command defined in T020a. **Dependencies**: T020a.

- [ ] T020a-oracle [US2] [D] **Oracle Baseline Metrics**: Compute the theoretical optimal FLOPs and accuracy. **Logic**: 1. Load `convergence_results_core.csv`. 2. For each `task_id`, find the minimum `k` where `is_correct=True`. If none, use `k_max` (censored). 3. Sum `calculate_flops` for that specific `k` across all samples. 4. Compute accuracy (pass@1) for the Oracle (always use optimal k). 5. Save to `oracle_baseline.json`. **Dependencies**: T013a.

- [ ] T020a-oracle-exec [US2] [D] **Execute Oracle Baseline**: Run `python code/src/analysis.py --mode oracle_baseline --convergence data/processed/convergence_results_core.csv --output data/processed/oracle_baseline.json`. **Dependencies**: T020a-oracle.

- [ ] T021b-test-static [US2] [D] **Non‑Inferiority Test vs Oracle**: Using `router_results.csv`, `oracle_baseline.json`, and `config.json` (delta=0.05), perform a **One-Sided** Non-Inferiority Test on **FLOPs savings** (Router FLOPs vs Oracle FLOPs). The test verifies that the router does not use significantly more FLOPs than the Oracle (efficiency). Additionally, test that Router Accuracy is not worse than Oracle Accuracy ([deferred]) by more than delta (non-inferiority). Save to `flops_savings_test.json`. **Command**: `python code/src/analysis.py --mode non_inferiority --router data/processed/router_results.csv --oracle data/processed/oracle_baseline.json --delta 0.05 --output data/processed/flops_savings_test.json`. **Dependencies**: T020-exec, T020a-oracle-exec.

- [ ] T021b-test-static-exec [US2] [D] **Execute Non-Inferiority Test**: Run the command defined in T021b-test-static. **Dependencies**: T021b-test-static.

- [ ] T021c [US2] [D] **Generate Config for Non‑Inferiority**: Extract `NON_INFERIORITY_DELTA` and `RANDOM_SEED` from `code/src/config.py` and write to `data/processed/config.json`. **Dependencies**: T000-config.

- [ ] T021b-flops [US2] [D] **Calculate FLOPs Savings**: Using `router_results.csv` and `oracle_baseline.json`, compute average FLOPs saved (via `calculate_flops`). Save to `flops_savings_calc.json`. **Dependencies**: T019b-exec, T020a-oracle-exec.

- [ ] T021b-flops-exec [US2] [D] **Execute FLOPs Calculation**: Run `python code/src/analysis.py --mode flops_savings --router data/processed/router_results.csv --oracle data/processed/oracle_baseline.json --output data/processed/flops_savings_calc.json`. **Dependencies**: T021b-flops.

- [ ] T021b-report [US2] [D] **Assemble FLOPs & Non‑Inferiority Report**: Merge `flops_savings_calc.json` and `flops_savings_test.json` into `flops_savings.json`. **Dependencies**: T021b-flops-exec, T021b-test-static-exec.

---

## Phase 5: User Story 3 - Statistical Robustness & Sensitivity Analysis (Priority: P3)

### Tests (optional)

- [X] T023 [P] [US3] **Unit test for Holm‑Bonferroni** (`code/tests/test_robustness.py`). **Dependencies**: T025b-adjusted-exec.
- [X] T024 [P] [US3] **Sensitivity sweep validation** (`code/tests/test_robustness.py`). **Dependencies**: T026-exec.

### Implementation

- [ ] T025a [US3] [D] **Per‑Stratum Correlation (powered only)**: Same as T015a-strata but explicitly skips underpowered strata. Output `stratum_pvalues_powered.json`. **Dependencies**: T012a, T013a, T004c.

- [ ] T025a-exec [US3] [D] **Execute Per‑Stratum Correlation (Powered)**: Run `python code/src/analysis.py --mode strata_powered --input data/processed/stratum_pvalues.json --output data/processed/stratum_pvalues_powered.json`. **Dependencies**: T025a.

- [ ] T025b-adjusted [US3] [D] **Holm‑Bonferroni on Powered Strata**: Apply correction to p‑values from `stratum_pvalues_powered.json`. Save to `adjusted_pvalues_powered.json`. **Dependencies**: T025a-exec.

- [ ] T025b-adjusted-exec [US3] [D] **Execute Holm‑Bonferroni (Powered)**: Run `python code/src/analysis.py --mode holm-bonferroni --input data/processed/stratum_pvalues_powered.json --output data/processed/adjusted_pvalues_powered.json`. **Dependencies**: T025b-adjusted.

- [ ] T025d-prepare [US3] [D] **Prepare Mixed‑Effects Data**: Merge `entropy_results.csv`, `convergence_results_core_full.csv` (from T013a-full), and `full_splits.json`. Include all strata (powered and underpowered). Save to `mixed_effects_data.csv`. **Dependencies**: T012a, T013a-full, T004d.

- [ ] T025d-prepare-exec [US3] [D] **Execute Mixed‑Effects Data Prep**: Run `python code/src/analysis.py --mode prepare_mixed --entropy data/processed/entropy_results.csv --convergence data/processed/convergence_results_core_full.csv --splits data/processed/full_splits.json --output data/processed/mixed_effects_data.csv`. **Dependencies**: T025d-prepare.

- [ ] T025d-verify [US3] [D] **Verify Underpowered Strata Presence**: Load `mixed_effects_data.csv` and `strata_log.json`; assert that every stratum marked `underpowered` appears at least once. Write verification result to `mixed_effects_strata_check.json`. **Dependencies**: T025d-prepare-exec.

- [ ] T025d-verify-exec [US3] [D] **Execute Mixed‑Effects Strata Check**: Run `python code/src/analysis.py --mode verify_strata --input data/processed/mixed_effects_data.csv --strata data/processed/strata_log.json --output data/processed/mixed_effects_strata_check.json`. **Dependencies**: T025d-verify.

- [ ] T025d-fit [US3] [D] **Fit Hierarchical Mixed‑Effects Model**: Use `statsmodels.MixedLM` with `groups='strata_name'` and `exog_re='1'`. Formula: `entropy ~ convergence_step`. Set `maxiter=1000` for convergence. Save results to `mixed_effects_results.json`. **Command**: `python code/src/analysis.py --mode mixed_effects --input data/processed/mixed_effects_data.csv --output data/processed/mixed_effects_results.json`. **Dependencies**: T025d-verify-exec.

- [ ] T025d-fit-exec [US3] [D] **Execute Mixed‑Effects Fit**: Run the command defined in T025d-fit. **Dependencies**: T025d-fit.

- [ ] T025c [US3] [D] **Merge Convergence Results**: Concatenate `convergence_results_core.csv` and `convergence_results_sensitivity.csv` into `convergence_results_merged.csv`. **Dependencies**: T013a, T013b.

- [ ] T025c-exec [US3] [D] **Execute Merge Convergence**: Run `python code/src/analysis.py --mode merge_convergence --input1 data/processed/convergence_results_core.csv --input2 data/processed/convergence_results_sensitivity.csv --output data/processed/convergence_results_merged.csv`. **Dependencies**: T025c.

- [ ] T026 [US3] [D] **Sensitivity Sweep**: Using `convergence_results_merged.csv`, compute Spearman ρ for thresholds k ∈ {2,3,4}. Compare against baseline (k={1,2,3}) and output `sensitivity_sweep.json`. **Command**: `python code/src/analysis.py --mode sensitivity --input data/processed/convergence_results_merged.csv --output data/processed/sensitivity_sweep.json`. **Dependencies**: T025c-exec.

- [ ] T026-exec [US3] [D] **Execute Sensitivity Sweep**: Run the command defined in T026. **Dependencies**: T026.

- [ ] T025f-merge [US3] [D] **Merge Robustness Results**: Combine `adjusted_pvalues_powered.json` and `mixed_effects_results.json` into `robustness_summary.json`. **Dependencies**: T025b-adjusted-exec, T025d-fit-exec.

- [ ] T025f-merge-exec [US3] [D] **Execute Merge Robustness**: Run `python code/src/analysis.py --mode merge_robustness --input1 data/processed/adjusted_pvalues_powered.json --input2 data/processed/mixed_effects_results.json --output data/processed/robustness_summary.json`. **Dependencies**: T025f-merge.

- [ ] T025f-verify [US3] [D] **Verify Robustness Summary**: Check `robustness_summary.json` for completeness. **Dependencies**: T025f-merge-exec.

---

## Phase 6: Polish & Cross‑Cutting Concerns

- [x] T028 [P] **Finalize paper draft** (`paper/draft.md`) ensuring all statistics trace to files under `data/processed/`.
- [x] T029 [P] **Run validation suite (CPU, N=50)** via `code/src/run_validation.py`. Produce `validation_report.json`. **Dependencies**: T005e.
- [x] T030 [P] **Update quickstart.md** with separate sections for "CPU Validation Mode (N=50)" and "Full GPU Analysis". Verify both sections exist. **Dependencies**: T029.
- [x] T031 [P] **Create state YAML** (`state/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2.yaml`) with content hashes.
- [x] T032 [P] **Run quickstart validation**; generate `quickstart_validation_report.json`. **Dependencies**: T030.
- [x] T033 [P] **Run full GPU analysis**; capture metrics via `capture_metrics(mode='full_analysis')` and save to `sc005_metrics.json`. **Dependencies**: T012a, T013a, T026-exec, T038-merge-results.
- [x] T034 [P] **Aggregate SC‑005 Metrics**: Merge `sc005_metrics.json` and `resource_metrics.json` into `sc005_final_report.json`. **Dependencies**: T033, T005e.
- [x] T042-local-entropy-check [P] **Local Artifact Integrity Check (Entropy)**: Verify `data/processed/entropy_results.csv` is non-empty and checksums match. **Dependencies**: T029.
- [x] T042-local-convergence-check [P] **Local Artifact Integrity Check (Convergence)**: Verify `data/processed/convergence_results_core.csv` is non-empty and checksums match. **Dependencies**: T029.
- [x] T042-local-summary [P] **Local Artifact Integrity Summary**: Aggregate check results into `local_gpu_artifact_integrity.json`. **Dependencies**: T042-local-entropy-check, T042-local-convergence-check.

---

## Phase 7: GPU Offload & Execution (Critical Path for 7B Model)

**Purpose**: Ensure the heavy inference tasks (T012a, T013a) execute on Kaggle GPU as required by the compute feasibility constraint (B model inference is infeasible on CPU).

- [X] T040-env-setup [P] **Define GPU Environment Versions**: Create `gpu_env.lock` file by querying the target Kaggle base image (e.g., `kaggle/kernels:latest`) for CUDA, cuDNN, and NVIDIA Driver versions. Pin these versions. **Dependencies**: T002.

- [X] T040-gpu-docker [P] **Build GPU Docker Image**: Create a Dockerfile (`code/Dockerfile.gpu`) that pins CUDA, cuDNN, and NVIDIA Driver versions from `gpu_env.lock`. Build the image `llmxive-gpu:latest`. **Dependencies**: T040-env-setup.

- [X] T040 [P] **Create Kaggle Offload Script**: Write `code/run_gpu.sh` that:
 1. Validates `HF_TOKEN` and `KAGGLE_KEY` environment variables.
 2. Generates a unique kernel name: `llmxive-gpu-run-${PROJECT_ID}-${TIMESTAMP}`.
 3. Submits the job to Kaggle using `kaggle kernels push -p code/ -d llmxive-gpu-run-${PROJECT_ID}-${TIMESTAMP}`.
 4. Includes a `requirements.txt` specific to the GPU environment (pinned versions from `gpu_env.lock`).
 5. Waits for completion and downloads `data/processed/` artifacts.
 6. **Dependencies**: T002, T000-model, T040-env-setup, T040-gpu-docker.

- [X] T041-submit [D] **GPU Smoke Test Submission**: Run `code/run_gpu.sh` to submit a **real, minimal inference job** (N=1 problem, k=1) to Kaggle. **Dependencies**: T040.
- [X] T041-wait [D] **GPU Smoke Test Wait**: Wait for job completion. **Dependencies**: T041-submit.
- [X] T041-download [D] **GPU Smoke Test Download**: Download artifacts from Kaggle. **Dependencies**: T041-wait.
- [X] T041-verify [D] **GPU Smoke Test Verify**: Verify artifacts match expected schema. **Dependencies**: T041-download.

- [X] T042-gpu-entropy-check [P] **GPU Artifact Integrity Check (Entropy)**: Verify `data/processed/entropy_results.csv` is non-empty and checksums match. **Dependencies**: T033.
- [X] T042-gpu-convergence-check [P] **GPU Artifact Integrity Check (Convergence)**: Verify `data/processed/convergence_results_core.csv` is non-empty and checksums match. **Dependencies**: T033.
- [X] T042-gpu-summary [P] **GPU Artifact Integrity Summary**: Aggregate check results into `gpu_artifact_integrity.json`. **Dependencies**: T042-gpu-entropy-check, T042-gpu-convergence-check.

---

## Phase 8: Revision & Robustness (Addressing Review Concerns)

**Purpose**: Address specific gaps identified in prior analysis: explicit data streaming for large datasets, robust error handling for missing data, and verification of statistical assumptions.

- [ ] T050 [US1] [D] **Implement Streaming Data Loader for Large Datasets**: Modify `code/src/data_loader.py` to support `streaming=True` for HumanEval/MBPP if local disk space is constrained. Implement chunked processing to accumulate statistics (entropy, convergence) without loading the full dataset into RAM. **Logic**: 1. Use `datasets.load_dataset(..., streaming=True)`. 2. Iterate over the stream, processing one problem at a time. 3. Accumulate results in a temporary buffer and flush to `data/processed/entropy_results.csv` and `convergence_results_core.csv` periodically. 4. Document the streaming logic and sample size in `data/processed/streaming_log.json`. **Dependencies**: T004a, T004c.
- [ ] T051 [US1] [D] **Robust Error Handling for Entropy Extraction**: Update `code/src/entropy.py` to handle cases where `ast.unparse` fails (e.g., malformed code) by logging the error and skipping the sample, rather than crashing the entire pipeline. **Logic**: 1. Wrap `ast.unparse` in a try-except block. 2. Log failures to `data/processed/entropy_errors.json`. 3. Ensure the pipeline continues for subsequent problems. **Dependencies**: T012a.
- [ ] T052 [US1] [D] **Verify Statistical Assumptions for Survival Analysis**: Add a task to check the proportional hazards assumption for the Cox PH model. **Logic**: 1. Use `lifelines.CoxPHFitter.check_assumptions()`. 2. If the assumption is violated, log the violation and suggest alternative models (e.g., Accelerated Failure Time). 3. Save the diagnostic report to `data/processed/survival_assumptions.json`. **Dependencies**: T015-survival-exec.
- [ ] T053 [US2] [D] **Validate Ordinal Logistic Regression Convergence**: Ensure the ordinal logistic regression model converges properly. **Logic**: 1. Check the `converged` flag in the model summary. 2. If not converged, adjust regularization or iteration limits and re-run. 3. Log convergence status to `data/processed/router_convergence.json`. **Dependencies**: T019-exec.
- [ ] T054 [US3] [D] **Sensitivity Analysis for Mixed-Effects Model**: Perform a sensitivity analysis on the hierarchical mixed-effects model by varying the random effects structure (e.g., `(1|strata)` vs `(1+entropy|strata)`). **Logic**: 1. Fit alternative models. 2. Compare AIC/BIC scores. 3. Save the comparison to `data/processed/mixed_effects_sensitivity.json`. **Dependencies**: T025d-fit-exec.
- [ ] T055 [P] **Final Integration & Verification**: Run a comprehensive verification script that checks all output artifacts for schema compliance, non-empty content, and logical consistency (e.g., no negative entropy, censored flags match convergence steps). **Dependencies**: T037, T021b-report, T025f-verify-exec.
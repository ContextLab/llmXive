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

- [x] T000-config [D] **Environment & Configuration Setup**: Create `code/src/config.py` with concrete defaults as Python variables. **Logic**: 1. Define `NON_INFERIORITY_DELTA = 0.05`, `ENTROPY_N_SAMPLES = 10`, `CONVERGENCE_K_RANGE = [1, 2, 3]`, `STRATA_THRESHOLD = 50`, `MODEL_TEMP = 0.7`, `MODEL_TOP_P = 0.95`, `RANDOM_SEED = 42`. 2. Define paths for datasets and model. 3. Ensure `NON_INFERIORITY_DELTA` is exported for downstream modules. **Artifact**: `code/src/config.py`. **Verification**: Verify file exists, is valid Python, and variables are correctly set. **Dependencies**: None.
- [x] T000-seed-setup [D] **Random Seed Setup**: Implement global random seed pinning function in `code/src/utils.py`. **Logic**: 1. Create function `set_global_seed(seed: int = 42)`. 2. Set `random.seed(seed)`, `numpy.random.seed(seed)`, `torch.manual_seed(seed)`, and `torch.cuda.manual_seed_all(seed)`. 3. Set `os.environ['PYTHONHASHSEED'] = str(seed)`. **Artifact**: `code/src/utils.py` (updated). **Verification**: Verify function exists and sets all required seeds. **Dependencies**: None.
- [x] T000-seed-verify [D] **Seed Verification**: Verify that running the script twice with the same seed produces identical outputs. **Logic**: 1. Run `python code/tests/dummy_seed_test.py` twice with seed=42. 2. Compare outputs. 3. Assert equality. 4. **Artifact**: `data/seed_verification.json`. **Schema**: `{seed: 42, hash: <sha256>, status: 'ok'}`. **Dependencies**: T000-seed-setup.
- [x] T000-model [D] **Model Availability Check**: Verify the existence of a CodeLlama instruct model. **Logic**: 1. Attempt to load the model config using `transformers.AutoConfig.from_pretrained`. 2. If the model is not cached locally and `HF_TOKEN` is available, trigger a download verification (or document the required download command). 3. If the model is missing and cannot be downloaded, raise a clear error `ModelNotFoundError`. 4. **Artifact**: `data/model_status.json`. **Schema**: `{status: 'available' | 'missing', path: str, message: str}`. **Dependencies**: T000-config.

- [x] T001a [P] **Create Project Directory Structure**: Create `projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/` with sub‑directories `data/`, `code/`, `paper/`, `state/`, `contracts/`. **Artifact**: `structure_check.json`. **Verification**: Verify directories exist.
- [x] T001b [D] **Verify Directory Structure**: Read `structure_check.json` and assert all required directories are present. **Artifact**: `structure_verify.json`.
- [x] T001c [D] **Generate Structure Report**: Summarize directory creation results into `data/structure_report.json`. **Artifact**: `data/structure_report.json`.

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
- [X] T004f-filter-data [D] **Filter Strata**: Read `data/processed/strata_log.json` and `data/processed/splits.json`. Generate a filtered dataset excluding underpowered strata for primary analysis and write to `data/processed/filtered_splits.json`. Also write the full dataset (unfiltered) to `data/processed/full_splits.json`. **Artifact**: `data/processed/filtered_splits.json`, `data/processed/full_splits.json`. **Dependencies**: T004c, T004d.
- [x] T004f-report [P] **Generate Exclusion Report**: Compute exclusion rate from `data/processed/filtered_splits.json` vs `data/processed/splits.json` and save to `data/processed/exclusion_rate_report.json`. **Schema**: `{total_samples: int, filtered_samples: int, exclusion_rate: float, excluded_strata: list}`. **Dependencies**: T004f-filter-data.
- [X] T004g [D] **Generate Unseen Validation Set**: Create `code/src/data_loader.py` function `generate_unseen_set`. Split the 'test' set into a held‑out test subset and an `unseen_validation` subset (stratified, 50/50). Fallback logic as described. Save to `data/processed/unseen_validation_set.csv` and checksum it. **Dependencies**: T004d.
- [X] T004h [D] **Verify Set Disjointness**: Ensure `task_id` sets of `data/processed/splits.json` and `data/processed/unseen_validation_set.csv` are disjoint. Log result to `data/processed/disjoint_verification.json`. **Dependencies**: T004g.
- [X] T004i [D] **Generate Baseline Pass@1**: Load literature values or fetch them, then save to `data/processed/baseline_pass1.json`. **Dependencies**: T004f-filter-data.
- [X] T004b-processed [D] **Checksum Processed Datasets**: Compute SHA256 checksums for all files in `data/processed/` (excluding temporary files) and write to `data/checksums_processed.txt`. **Dependencies**: T004f-filter-data, T004g, T004h, T004i.

- [X] T005 [P] **Create `code/src/entropy.py` stub** with function `def extract_entropy(prompt: str, model, n_samples: int = 10) -> float`. **Dependencies**: T004h, T000-seed-setup.
- [x] T005d [P] **Define FLOPs utility** `def calculate_flops(model_params: int, seq_len: int, k: int) -> float`. **Dependencies**: None.
- [x] T005e [P] **Implement resource monitoring** `capture_metrics(mode: str)` saving to `data/processed/resource_metrics.json`. **Dependencies**: None.
- [X] T006 [P] **Create `code/src/inference.py` stub** with `def run_inference(prompt: str, model, k: int) -> dict`. **Artifact schema** as previously defined. **Dependencies**: T004f-filter-data, T000-seed-setup.
- [X] T007 [P] **Define dataclasses** `InputProblem` and `ConvergenceTrajectory` in `code/src/models.py`. **Dependencies**: T004f-filter-data.
- [X] T008b [P] **Create `paper/model_substitution_rationale.md`** (unchanged). **Dependencies**: T000-config.
- [X] T009 [P] **Implement Docker sandbox** (`code/Dockerfile`, `code/docker-compose.yml`). **Dependencies**: None.
- [X] T009b [D] **Build Unseen Sandbox Image**: Build `entropy-sandbox:latest` from `code/Dockerfile.unseen`. Verify it can run a simple command. **Artifact**: `docker_image_status.json`. **Dependencies**: T009.

---

## Phase 3a: User Story 1 - Core Correlation Analysis (Data Generation) (Priority: P1) 🎯 MVP

### Tests (optional)

- [X] T010 [P] [US1] **Unit test for entropy clustering** (`code/tests/test_entropy.py`). **Dependencies**: T005.
- [X] T011 [P] [US1] **Integration test for pipeline** (`code/tests/test_analysis.py`). **Dependencies**: T005, T006.

### Implementation

- [ ] T012a [US1] [D] **Entropy Extraction Pipeline**: Load model (CPU/GPU) and `data/processed/filtered_splits.json`. For each problem, generate N=10 samples (`temperature=0.7`, `top_p=0.95`). Normalize each sample with `ast.unparse`, hash with SHA256, cluster by hash, compute Shannon entropy over cluster probabilities. Use the **unseen_validation** set (from T004g) only for clustering reference; do **not** use held‑out test data. Assign minimal entropy `1e-9` for deterministic outputs. Log exclusions to `data/processed/exclusion_log.json`. Save results to `data/processed/entropy_results.csv` (`{task_id, entropy, exclusion_reason}`). **Dependencies**: T004f-filter-data, T004g, T000-model.

- [ ] T013a [US1] [D] **Core Convergence Inference (k=1‑3)**: Load model and `data/processed/filtered_splits.json`. For each problem, run a **single deterministic inference** for each k ∈ {1,2,3} (no N=10 sampling). Record `output`, `is_correct` (compare to reference), `first_correct_step` (the smallest k where `is_correct` is true), and set `censored` flag to `True` if no correct answer by k=3. Also compute `time_to_event` = `first_correct_step` (or `k_max` if censored). Write directly to `data/processed/convergence_results_core.csv` with schema `{task_id, k, output, is_correct, first_correct_step, censored, time_to_event}`. Manage RNG deterministically: reset seed before each k iteration using `set_global_seed`. **Dependencies**: T004f-filter-data, T006, T000-model, T012a.

- [ ] T013a-robustness [US3] [D] **Full Convergence Inference (k=1‑3)**: Same as T013a but operates on `data/processed/full_splits.json` for robustness analysis (mixed-effects). **Artifact**: `data/processed/convergence_results_core_full.csv`. **Dependencies**: T004d, T006, T000-model, T012a.
- [ ] T013a-verify [D] **Verify Censored Logic**: Load `convergence_results_core.csv` and assert rows with `k=3` and `is_correct=False` have `censored=True` and `time_to_event=3`. Raise error if mismatch. **Artifact**: `data/processed/censored_verification.json`. **Dependencies**: T013a.
- [ ] T013b [US1] [D] **Sensitivity Convergence (k=4)**: After T013a, run inference for k=4 on same inputs, update `first_correct_step` if still null, adjust `censored` accordingly, and write to `data/processed/convergence_results_sensitivity.csv`. **Dependencies**: T013a, T006, T000-model.
- [ ] T015a-strata [US1] [D] **Per‑Stratum Correlation**: Load `entropy_results.csv` and `convergence_results_core.csv`. Group by stratum (from `strata_log.json`). For each powered stratum, compute Spearman ρ and p‑value between `entropy` and `first_correct_step`. Save to `data/processed/stratum_pvalues.json`. **Dependencies**: T012a, T013a, T004c.
- [ ] T015-correlation [US1] [D] **Spearman Correlation**: Merge `entropy_results.csv` with `convergence_results_core.csv` on `task_id`. Explicitly merge `time_to_event` from the convergence file. Compute Spearman ρ and p‑value between `entropy` and `first_correct_step`. Save to `data/processed/correlation_spearman.json`. **Dependencies**: T012a, T013a.
- [ ] T015-survival [US1] [D] **Kaplan‑Meier & Cox PH**: Using merged data, prepare survival input (time=`time_to_event`, event=`~censored`). Fit `lifelines.KaplanMeierFitter` and `CoxPHFitter` with `entropy` as covariate. Save results to `data/processed/correlation_survival.json`. **Dependencies**: T012a, T013a.
- [ ] T015-power [US1] [D] **Power Analysis**: Based on sample size and observed effect, compute MDES and power; store in `data/processed/correlation_power.json`. **Dependencies**: T015-correlation.
- [ ] T015b-adjust [US1] [D] **Multiple‑Comparison Correction (Strata)**: Read per‑stratum p‑values from `data/processed/stratum_pvalues.json` (produced by T015a-strata). Apply Holm‑Bonferroni **only to powered strata** (exclude those flagged `underpowered` in `strata_log.json`). Save to `data/processed/adjusted_pvalues.json`. **Dependencies**: T015a-strata, T004c.

- [ ] T035 [US1] [D] **Execute Entropy Extraction**: Run `python code/src/entropy.py --input data/processed/filtered_splits.json --output data/processed/entropy_results.csv`. Verify exit code 0 and file existence. **Dependencies**: T012a.
- [ ] T036 [US1] [D] **Execute Convergence Inference**: Run `python code/src/inference.py --input data/processed/filtered_splits.json --output data/processed/convergence_results_core.csv --k_range 1 2 3`. Verify exit code 0. **Dependencies**: T013a.
- [ ] T038-run-correlation [US1] [D] **Run Correlation Scripts**: Execute `python code/src/analysis.py --mode spearman --entropy data/processed/entropy_results.csv --convergence data/processed/convergence_results_core.csv`. Generates `correlation_spearman.json`, `correlation_survival.json`, `correlation_power.json`. **Dependencies**: T035, T036, T015-correlation, T015-survival, T015-power.
- [ ] T038-merge-results [US1] [D] **Merge Correlation Artifacts**: Combine the three JSON files into `data/processed/correlation_results.json`. **Dependencies**: T038-run-correlation.
- [ ] T037 [US1] [D] **Final Survival Summary**: Run any final post‑processing if needed; produce `data/processed/correlation_results_final.json`. **Dependencies**: T038-merge-results.

---

## Phase 4: User Story 2 - Dynamic Router Simulation (Priority: P2)

### Tests (optional)

- [X] T017 [P] [US2] **Unit test for logistic regression** (`code/tests/test_analysis.py`). **Dependencies**: T019c.
- [X] T018 [P] [US2] **Statistical test validation** (`code/tests/test_analysis.py`). **Dependencies**: T019c.

### Implementation

- [ ] T019 [US2] [D] **Train Ordinal Logistic Regression Router**: Load `entropy_results.csv`, `convergence_results_core.csv`, and `baseline_pass1.json`. Derive target variable `optimal_k` = `first_correct_step` (or 3 if censored). Feature set = `entropy` + `baseline_pass1`. Perform **5‑fold cross‑validation** using an **Ordinal Logistic Regression** model (e.g., `statsmodels` or `mlogit`) to predict the ordinal target. Aggregate accuracy, F1, and confusion matrix. Save model to `data/processed/router_model.pkl` and metrics to `data/processed/router_metrics.json`. **Dependencies**: T012a, T013a, T004i.
- [ ] T019c [US2] [D] **Explicit 5‑Fold CV Implementation**: Ensure the cross‑validation loop uses `sklearn.model_selection.StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` and respects the ordinal nature of the target. Verify that each fold’s metrics are logged to `data/processed/router_cv_folds.json`. **Dependencies**: T019.
- [ ] T019b [US2] [D] **Generate Router Predictions**: Apply trained router to test set (filtered splits) to produce `router_results.csv` with `{task_id, predicted_k, actual_k, accuracy, is_censored}`. **Dependencies**: T019, T004f-filter-data.
- [ ] T020 [US2] [D] **Router vs Random Baseline Evaluation**: Compare router accuracy against random baseline (`k=1` for all). Perform paired t‑test; store results in `router_accuracy_test.json`. **Dependencies**: T019b.
- [ ] T020a [US2] [D] **Static k=2 Baseline Metrics**: Compute FLOPs and accuracy for always using `k=2` on the filtered test set. Save to `static_k2_baseline.json` (`{total_flops, accuracy}`). **Dependencies**: T013a.
- [ ] T021b-test-static [US2] [D] **Non‑Inferiority Test vs Static k=2**: Using `router_results.csv`, `static_k2_baseline.json`, and `config.json` (delta=0.05), perform a Two One‑Sided Tests (TOST) procedure to verify that router accuracy is not worse than static k=2 by more than delta. Save to `flops_savings_test.json`. **Dependencies**: T020, T020a, T021c.
- [ ] T021c [US2] [D] **Generate Config for Non‑Inferiority**: Extract `NON_INFERIORITY_DELTA` and `RANDOM_SEED` from `code/src/config.py` and write to `data/processed/config.json`. **Dependencies**: T000-config.
- [ ] T021b-flops [US2] [D] **Calculate FLOPs Savings**: Using `router_results.csv` and `static_k2_baseline.json`, compute average FLOPs saved (via `calculate_flops`). Save to `flops_savings_calc.json`. **Dependencies**: T019b, T020a.
- [ ] T021b-report [US2] [D] **Assemble FLOPs & Non‑Inferiority Report**: Merge `flops_savings_calc.json` and `flops_savings_test.json` into `flops_savings.json`. **Dependencies**: T021b-flops, T021b-test-static.

---

## Phase 5: User Story 3 - Statistical Robustness & Sensitivity Analysis (Priority: P3)

### Tests (optional)

- [X] T023 [P] [US3] **Unit test for Holm‑Bonferroni** (`code/tests/test_robustness.py`). **Dependencies**: T025b.
- [X] T024 [P] [US3] **Sensitivity sweep validation** (`code/tests/test_robustness.py`). **Dependencies**: T026.

### Implementation

- [ ] T025a [US3] [D] **Per‑Stratum Correlation (powered only)**: Same as T015a-strata but explicitly skips underpowered strata. Output `stratum_pvalues_powered.json`. **Dependencies**: T012a, T013a, T004c.
- [ ] T025b-adjusted [US3] [D] **Holm‑Bonferroni on Powered Strata**: Apply correction to p‑values from `stratum_pvalues_powered.json`. Save to `adjusted_pvalues_powered.json`. **Dependencies**: T025a, T004c.
- [ ] T025d-prepare [US3] [D] **Prepare Mixed‑Effects Data**: Merge `entropy_results.csv`, `convergence_results_core_full.csv` (from T013a-robustness), and `full_splits.json`. Include all strata (powered and underpowered). Save to `mixed_effects_data.csv`. **Dependencies**: T012a, T013a-robustness, T004d.
- [ ] T025d-verify [US3] [D] **Verify Underpowered Strata Presence**: Load `mixed_effects_data.csv` and `strata_log.json`; assert that every stratum marked `underpowered` appears at least once. Write verification result to `mixed_effects_strata_check.json`. **Dependencies**: T025d-prepare, T004c.
- [ ] T025d-fit [US3] [D] **Fit Hierarchical Mixed‑Effects Model**: Use `statsmodels` formula `entropy ~ convergence_step + (1|strata_name)`. Save results to `mixed_effects_results.json`. **Dependencies**: T025d-verify.
- [ ] T025c [US3] [D] **Merge Convergence Results**: Concatenate `convergence_results_core.csv` and `convergence_results_sensitivity.csv` into `convergence_results_merged.csv`. **Dependencies**: T013a, T013b.
- [ ] T026 [US3] [D] **Sensitivity Sweep**: Using `convergence_results_merged.csv`, compute Spearman ρ for thresholds k ∈ {2,3,4}. Compare against baseline (k={1,2,3}) and output `sensitivity_sweep.json`. **Dependencies**: T025c.
- [ ] T025f [US3] [D] **Integrate Robustness Results**: Combine `adjusted_pvalues_powered.json` and `mixed_effects_results.json` into `robustness_summary.json`. **Dependencies**: T025b-adjusted, T025d-fit.

---

## Phase 6: Polish & Cross‑Cutting Concerns

- [x] T028 [P] **Finalize paper draft** (`paper/draft.md`) ensuring all statistics trace to files under `data/processed/`.
- [x] T029 [P] **Run validation suite (CPU, N=50)** via `code/src/run_validation.py`. Produce `validation_report.json`. **Dependencies**: T005e.
- [ ] T030 [P] **Update quickstart.md** with separate sections for “CPU Validation Mode (N=50)” and “Full GPU Analysis”. Verify both sections exist. **Dependencies**: T029.
- [x] T031 [P] **Create state YAML** (`state/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2.yaml`) with content hashes.
- [x] T032 [P] **Run quickstart validation**; generate `quickstart_validation_report.json`. **Dependencies**: T030.
- [x] T033 [P] **Run full GPU analysis**; capture metrics via `capture_metrics(mode='full_analysis')` and save to `sc005_metrics.json`. **Dependencies**: T012a, T013a, T026, T038-merge-results.
- [x] T034 [P] **Aggregate SC‑005 Metrics**: Merge `sc005_metrics.json` and `resource_metrics.json` into `sc005_final_report.json`. **Dependencies**: T033, T005e.

---

## Phase 7: GPU Offload & Execution (Critical Path for 7B Model)

**Purpose**: Ensure the heavy inference tasks (T012a, T013a) execute on Kaggle GPU as required by the compute feasibility constraint (7B model inference is infeasible on CPU).

- [ ] T040 [P] **Create Kaggle Offload Script**: Write `code/run_gpu.sh` that:
 1. Validates `HF_TOKEN` and `KAGGLE_KEY` environment variables.
 2. Submits the job to Kaggle using the `kaggle kernels push` command with the `code/` directory and a `kaggle.json` configuration.
 3. Includes a `requirements.txt` specific to the GPU environment (pinned versions).
 4. Waits for completion and downloads `data/processed/` artifacts.
 5. **Dependencies**: T002, T000-model.

- [ ] T041 [D] **Execute GPU Smoke Test**: Run `code/run_gpu.sh` to submit a **real, minimal inference job** (N=1 problem, k=1) to Kaggle. Verify that the job completes successfully, artifacts are downloaded, and the output matches expected schema. This validates the full offload pipeline end-to-end. **Dependencies**: T040.

- [ ] T042 [D] **GPU Artifact Integrity Check**: After T041 (and subsequent full runs), verify that `data/processed/entropy_results.csv` and `data/processed/convergence_results_core.csv` are non-empty and checksums match the expected schema. **Dependencies**: T035, T036, T041.

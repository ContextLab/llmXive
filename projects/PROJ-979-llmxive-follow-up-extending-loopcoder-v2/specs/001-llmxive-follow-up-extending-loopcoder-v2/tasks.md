---
description: "Task list for llmXive follow‑up: extending LoopCoder‑v2"
---

# Tasks: llmXive follow‑up: extending "LoopCoder‑v2: Only Loop Once for Efficient Test‑Time Computation Scali"

**Inputs:** `specs/001-llmxive-follow-up-extending-loopcoder-v2/spec.md`, `specs/001-llmxive-follow-up-extending-loopcoder-v2/plan.md`  
**Prerequisites:** All previously‑checked infrastructure tasks (configuration, seed setup, model availability, basic project layout).

> **Notation**  
> `- [ ] T### [P/D] [USx?] description – <artifact‑path>`  
> `P` = can run in parallel with other tasks that do not touch the same files.  
> `D` = must run after its listed dependencies.  
> `USx` = user‑story identifier (US1 = core correlation, US2 = router simulation, US3 = robustness).

---

## Phase 0 – Verified Core Infrastructure (already completed)

- [ ] T000-config [P] **Environment & Configuration Setup** – `code/src/config.py`  
  *Defines `NON_INFERIORITY_DELTA = 0.05`, `ENTROPY_N_SAMPLES = 10`, `CONVERGENCE_K_RANGE = [1,2,3]`, `STRATA_THRESHOLD = 50`, `MODEL_TEMP = 0.7`, `MODEL_TOP_P = 0.95`, `RANDOM_SEED = 42`.*

- [ ] T000-seed-setup [P] **Global Random‑Seed Pinning** – `code/src/utils.py`  
  *Provides `set_global_seed(seed: int = 42)` that seeds `random`, `numpy`, `torch`, and `PYTHONHASHSEED`.*

- [ ] T000-model [P] **Model Availability Check** – `data/model_status.json`  
  *Attempts `transformers.AutoConfig.from_pretrained("meta-llama/CodeLlama-7b-Instruct-hf")`; writes status JSON.*

- [ ] T001a [P] **Project Directory Skeleton** – `projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/` (sub‑dirs `data/`, `code/`, `paper/`, `contracts/`).  

- [ ] T001b [D] **Directory Structure Verification** – `data/structure_verify.json`.  

- [ ] T002 [P] **Python Requirements File** – `code/requirements.txt` (pinned versions of `transformers`, `torch`, `datasets`, `scikit-learn`, `lifelines`, `statsmodels`, `pandas`, `numpy`, `pytest`).  

- [ ] T003 [P] **Project Configuration Files** – `.ruff.toml`, `pyproject.toml` in `code/`.  

- [ ] T004a [P] **Fetch HumanEval & MBPP (streaming enabled)** – `code/src/data_loader.py` (`fetch_datasets()` stores raw Parquet files under `data/raw/`).  

- [ ] T004b-raw [D] **Checksum Raw Datasets** – `data/checksums_raw.txt`.  

- [ ] T004c [D] **Stratify Data & Log Under‑powered Strata** – `data/processed/strata_log.json`.  

- [ ] T004d [D] **Save Train/Test Splits** – `data/processed/splits.json` (`{train: [...], test: [...]}`).  

- [ ] T004f-split-logic [D] **Generate Full‑Dataset Splits (no filtering)** – `data/processed/full_splits.json`.  

- [ ] T004g [D] **Create Unseen Validation Set** – `data/processed/unseen_validation_set.csv` + checksum.  

- [ ] T004h [D] **Verify Disjointness of Test & Unseen Sets** – `data/processed/disjoint_verification.json`.  

- [ ] T004i [D] **Persist Baseline Pass@1 Values** – `data/processed/baseline_pass1.json`.  

- [ ] T004b-processed [D] **Checksum Processed Files** – `data/checksums_processed.txt`.  

- [ ] T005 [P] **Entropy Module Stub** – `code/src/entropy.py` (contains `extract_entropy`).  

- [ ] T005d [P] **FLOPs Utility** – `code/src/utils.py` (`calculate_flops`).  

- [ ] T005e [P] **Resource‑Monitoring Helper** – `code/src/utils.py` (`capture_metrics`).  

- [ ] T006 [P] **Inference Module Stub** – `code/src/inference.py` (`run_inference`).  

- [ ] T007 [P] **Data‑Model Dataclasses** – `code/src/models.py` (`InputProblem`, `ConvergenceTrajectory`).  

- [ ] T009 [P] **Docker Sandbox Definition** – `code/Dockerfile`, `code/docker-compose.yml`.  

- [ ] T028 [P] **Finalize Paper Draft** – `paper/draft.md`.  

- [ ] T029 [P] **Run CPU‑Validation Suite (N=50)** – `code/src/run_validation.py` → `validation_report.json`.  

- [ ] T030 [P] **Update Quick‑Start Documentation** – `quickstart.md` (CPU‑validation and full‑GPU sections).  

- [ ] T031 [P] **Create Project State YAML** – `state/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2.yaml`.  

- [ ] T032 [P] **Execute Quick‑Start Validation** – `quickstart_validation_report.json`.  

- [ ] T033 [P] **Run Full GPU Analysis (end‑to‑end)** – produces all core result artifacts (see Phase 3‑6).  

- [ ] T034 [P] **Aggregate SC‑005 Metrics** – `sc005_final_report.json`.  

- [ ] T040-env-setup [P] **Pin GPU Environment Versions** – `gpu_env.lock`.  

- [ ] T040-gpu-docker [P] **Build GPU Docker Image** – `code/Dockerfile.gpu` → image `llmxive-gpu:latest`.  

- [ ] T040 [P] **Kaggle Off‑load Script** – `code/run_gpu.sh`.  

- [ ] T041-smoke-test-submit [D] **Submit Minimal GPU Job** – uses `run_gpu.sh` (N=1, k=1).  

- [ ] T041-smoke-test-wait [D] **Wait for GPU Job Completion**.  

- [ ] T041-smoke-test-download [D] **Download Minimal GPU Artifacts**.  

- [ ] T041-smoke-test-verify [D] **Verify Minimal GPU Artifacts** – schema compliance of tiny `entropy_results.csv` & `convergence_results_core.csv`.

---

## Phase 1 – Data Acquisition & Streaming (new end‑to‑end foundation)

- [ ] T101 [P] **Streaming Data Loader Implementation** – `code/src/data_loader.py`  
  *Uses `datasets.load_dataset(..., streaming=True)` for HumanEval & MBPP; processes one problem at a time, writes rows incrementally to `data/processed/entropy_results_partial.csv` and `data/processed/convergence_results_partial.csv`; logs progress in `data/processed/streaming_log.json`.*

- [ ] T102 [D] **Flush Partial Results to Final Files** – `data/processed/entropy_results.csv`, `data/processed/convergence_results_core.csv`  
  *After streaming completes, concatenate partial files, compute SHA‑256 checksums, write to `data/checksums_processed.txt`.*

- [ ] T103 [D] **Validate Streaming Loader Output Schema** – `data/processed/streaming_validation.json`  
  *Runs a lightweight schema validator against `entropy_schema.schema.yaml` and `convergence_schema.schema.yaml`; records pass/fail.*

---

## Phase 2 – Entropy Extraction (US‑1)

- [ ] T201 [D] **Run Full Entropy Extraction (GPU)** – `code/src/entropy.py`  
  *Command:*  
  ```bash
  python -m code.src.entropy \
    --input data/processed/full_splits.json \
    --output data/processed/entropy_results.csv \
    --reference data/processed/unseen_validation_set.csv \
    --device cuda \
    --seed 42
  ```  
  *Generates `entropy_results.csv` (columns: `problem_id, dataset, entropy_value, num_clusters, num_samples, excluded`). Logs any exclusion events to `data/processed/exclusion_log.json`.*

- [ ] T202 [D] **Verify Entropy Results Compliance** – `data/processed/entropy_verification.json`  
  *Checks: (1) file exists and non‑empty; (2) each row conforms to `entropy_schema.schema.yaml`; (3) `entropy_value ≥ 0`; (4) `num_samples == 10`.*

---

## Phase 3 – Convergence Inference (US‑1)

- [ ] T301 [D] **Run Core Convergence Inference (k = 1‑3, GPU)** – `code/src/inference.py`  
  *Command:*  
  ```bash
  python -m code.src.inference \
    --input data/processed/full_splits.json \
    --output data/processed/convergence_results_core.csv \
    --k_range 1 2 3 \
    --device cuda \
    --seed 42
  ```  
  *Outputs CSV with schema defined in `convergence_schema.schema.yaml` (including `is_censored` and `convergence_step`).*

- [ ] T302 [D] **Run Sensitivity Convergence (k = 4)** – `code/src/inference.py`  
  *Command:* same as T301 but `--k_range 4` → `data/processed/convergence_results_sensitivity.csv`.

- [ ] T303 [D] **Censored‑Logic Verification** – `data/processed/censored_verification.json`  
  *Ensures any row with `k=3` (or `k=4` for sensitivity) where `is_correct=False` has `is_censored=True` and `convergence_step` is `null`.*

---

## Phase 4 – Core Statistical Analysis (US‑1)

- [ ] T401 [D] **Spearman Correlation (entropy ↔ first_correct_step)** – `code/src/analysis.py`  
  *Command:*  
  ```bash
  python -m code.src.analysis \
    --mode spearman \
    --entropy data/processed/entropy_results.csv \
    --convergence data/processed/convergence_results_core.csv \
    --output data/processed/correlation_spearman.json
  ```  
  *Result JSON follows `results_schema.schema.yaml` (fields: `metric_name`, `value`, `confidence_interval`, `significance_flag`).*

- [ ] T402 [D] **Survival Analysis (Kaplan‑Meier & Cox PH)** – `code/src/analysis.py`  
  *Command:*  
  ```bash
  python -m code.src.analysis \
    --mode survival \
    --convergence data/processed/convergence_results_core.csv \
    --entropy data/processed/entropy_results.csv \
    --output data/processed/correlation_survival.json
  ```

- [ ] T403 [D] **Power Analysis for Observed Effect** – `code/src/analysis.py`  
  *Command:*  
  ```bash
  python -m code.src.analysis \
    --mode power \
    --spearman data/processed/correlation_spearman.json \
    --output data/processed/correlation_power.json
  ```

- [ ] T404 [D] **Per‑Stratum Correlation (all strata)** – `code/src/analysis.py`  
  *Command:*  
  ```bash
  python -m code.src.analysis \
    --mode strata \
    --entropy data/processed/entropy_results.csv \
    --convergence data/processed/convergence_results_core.csv \
    --strata data/processed/strata_log.json \
    --output data/processed/stratum_pvalues.json
  ```

- [ ] T405 [D] **Holm‑Bonferroni Correction (all strata)** – `code/src/analysis.py`  
  *Command:*  
  ```bash
  python -m code.src.analysis \
    --mode holm-bonferroni \
    --input data/processed/stratum_pvalues.json \
    --output data/processed/adjusted_pvalues.json
  ```

- [ ] T406 [D] **Merge All Core Results** – `data/processed/correlation_results_final.json`  
  *Combines `correlation_spearman.json`, `correlation_survival.json`, `correlation_power.json`, and `adjusted_pvalues.json` into a single JSON document that satisfies `results_schema.schema.yaml` for each metric.*

---

## Phase 5 – Dynamic Router Simulation (US‑2)

- [ ] T501 [D] **Generate 5‑Fold Stratified CV Splits** – `data/processed/router_cv_folds.json`  
  *Uses `sklearn.model_selection.StratifiedKFold` on the derived target `optimal_k` (first correct loop).*

- [ ] T502 [D] **Verify CV Split Integrity** – `data/processed/router_cv_folds_verified.json`  
  *Checks: exactly 5 folds, no overlap, stratification by `optimal_k`, seed = 42.*

- [ ] T503 [D] **Train Ordinal Logistic Regression Router** – `code/src/analysis.py`  
  *Command:*  
  ```bash
  python -m code.src.analysis \
    --mode train_router \
    --entropy data/processed/entropy_results.csv \
    --convergence data/processed/convergence_results_core.csv \
    --baseline data/processed/baseline_pass1.json \
    --cv_folds data/processed/router_cv_folds_verified.json \
    --output data/processed/router_model.pkl \
    --metrics data/processed/router_metrics.json
  ```  
  *Model saved as Pickle; metrics JSON follows `router.schema.yaml`.*

- [ ] T504 [D] **Generate Router Predictions on Test Set** – `data/processed/router_results.csv`  
  *Command:*  
  ```bash
  python -m code.src.analysis \
    --mode predict_router \
    --model data/processed/router_model.pkl \
    --input data/processed/full_splits.json \
    --output data/processed/router_results.csv
  ```

- [ ] T505 [D] **Evaluate Router vs Random Baseline** – `data/processed/router_accuracy_test.json`  
  *Performs a paired t‑test comparing router accuracy to a random `k=1` baseline; stores test statistic, p‑value, and significance flag.*

- [ ] T506 [D] **Compute Static k = 2 Baseline** – `data/processed/static_k2_baseline.json`  
  *Aggregates FLOPs (via `calculate_flops`) and pass@1 accuracy when always using loop count 2.*

- [ ] T507 [D] **Compute Oracle Baseline (optimal k per problem)** – `data/processed/oracle_baseline.json`  
  *Uses the true `optimal_k` from convergence data to calculate ideal FLOPs and accuracy.*

- [ ] T508 [D] **Non‑Inferiority Tests (FLOPs & Accuracy)** – `data/processed/flops_savings_test.json`  
  *One‑sided tests checking that router FLOPs are not > 5 % above Oracle FLOPs and that accuracy loss ≤ 0.05 (δ = 0.05).*

- [ ] T509 [D] **Calculate FLOPs Savings Summary** – `data/processed/flops_savings.json`  
  *Merges `flops_savings_calc.json` (average savings) with `flops_savings_test.json` into a single report.*

---

## Phase 6 – Robustness & Sensitivity Analyses (US‑3)

- [ ] T601 [D] **Per‑Stratum Correlation (Powered Strata Only)** – `data/processed/stratum_pvalues_powered.json`  
  *Same as T404 but skips strata with `< 50` samples (uses `STRATA_THRESHOLD`).*

- [ ] T602 [D] **Holm‑Bonferroni on Powered Strata** – `data/processed/adjusted_pvalues_powered.json`  
  *Applies correction to the powered‑only p‑values.*

- [ ] T603 [D] **Prepare Mixed‑Effects Dataset** – `data/processed/mixed_effects_data.csv`  
  *Merges entropy, convergence (full, including k = 4), and split metadata; retains all strata.*

- [ ] T604 [D] **Fit Hierarchical Mixed‑Effects Model** – `data/processed/mixed_effects_results.json`  
  *Uses `statsmodels.MixedLM` with random intercepts for `strata_name`; formula `entropy ~ convergence_step`. Stores coefficients, standard errors, and model fit statistics.*

- [ ] T605 [D] **Sensitivity Sweep Over Convergence Thresholds (k = 2,3,4)** – `data/processed/sensitivity_sweep.json`  
  *Computes Spearman ρ for each threshold, records variation, and flags stability.*

- [ ] T606 [D] **Merge Robustness Outputs** – `data/processed/robustness_summary.json`  
  *Combines `adjusted_pvalues_powered.json`, `mixed_effects_results.json`, and `sensitivity_sweep.json` into a single JSON summary.*

---

## Phase 7 – GPU Off‑load Execution (critical path)

- [ ] T701 [P] **Finalize Kaggle GPU Script** – `code/run_gpu.sh` (already present, verified).  

- [ ] T702 [D] **Submit Full‑Scale GPU Job** – uses `run_gpu.sh` to execute the full pipeline (T101 → T509).  

- [ ] T703 [D] **Download GPU‑Generated Artifacts** – pulls the `data/processed/` directory from the completed Kaggle run.  

- [ ] T704 [D] **Verify GPU Artifacts** – `data/processed/gpu_artifact_integrity.json`  
  *Checks existence and SHA‑256 checksums of `entropy_results.csv`, `convergence_results_core.csv`, `router_results.csv`, and all JSON result files; confirms schema compliance.*

---

## Phase 8 – Final Aggregation & Handoff

- [ ] T801 [D] **Assemble Final Research Report** – `paper/final_report.md`  
  *Links to all result artifacts, includes tables/figures generated directly from JSON/CSV files, reports significance flags, power analysis outcomes, and FLOPs savings.*

- [ ] T802 [D] **Update Quick‑Start for End‑Users** – `quickstart.md`  
  *Adds a “Run Full GPU Study” section that points to `code/run_gpu.sh` and describes how to reproduce the results locally (including streaming loader option).*

- [ ] T803 [D] **Create Reproducibility Manifest** – `data/processed/reproducibility_manifest.json`  
  *Lists every input file, its checksum, the exact command line used to generate each downstream artifact, and the git commit hash of the code at execution time.*

- [ ] T804 [D] **Run Comprehensive Verification Suite** – `code/src/verification.py` → `verification_report.json`  
  *Automated script that (1) validates all schema files, (2) checks that every required artifact exists and is non‑empty, (3) confirms that all statistical thresholds (p < 0.05, δ = 0.05) are met or appropriately reported, and (4) produces a pass/fail summary for the entire project.*

---

### Dependency Overview (selected)

| Task | Depends on |
|------|------------|
| T101 | T004f‑split‑logic, T004c, T004d |
| T102 | T101 |
| T103 | T102 |
| T201 | T102 |
| T202 | T201 |
| T301 | T102 |
| T302 | T102 |
| T303 | T301 |
| T401‑T406 | T202, T303 |
| T501‑T509 | T406, T301 |
| T601‑T606 | T406, T303 |
| T702 | T701, T401‑T509, T601‑T606 |
| T704 | T702 |
| T801‑T804 | All preceding tasks |

---

> **Note:** All tasks that produce files are designed to be *deterministic* given the same random seed (`RANDOM_SEED = 42`). The GPU off‑load mechanism will automatically re‑run the same commands on a Kaggle GPU if a CPU‑only run fails due to CUDA requirements, satisfying the “real GPU computation” rule.

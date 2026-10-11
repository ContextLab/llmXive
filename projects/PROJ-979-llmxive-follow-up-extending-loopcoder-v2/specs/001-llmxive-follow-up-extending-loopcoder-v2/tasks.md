---
description: "Task list for llmXive follow‑up: extending LoopCoder‑v2"
---

# Tasks: llmXive follow‑up: extending "LoopCoder‑v2: Only Loop Once for Efficient Test‑Time Computation Scali"

**Inputs:** `specs/001-llmxive-follow-up-extending-loopcoder-v2/spec.md`, `specs/001-llmxive-follow-up-extending-loopcoder-v2/plan.md`  
**Prerequisites:** All previously‑checked infrastructure tasks (configuration, seed setup, model availability, basic project layout).

> **Notation**  
> `- [ ] T### [P/D] [USx?] description – <artifact‑path>`  
> `P` = can run in parallel with other tasks that do **not** touch the same files.  
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

## Phase 1 – Data Acquisition & Streaming (foundational end‑to‑end)

- [ ] T101 [P] **Implement Streaming Data Loader** – `code/src/data_loader.py`  
  *Uses `datasets.load_dataset(..., streaming=True)` for HumanEval & MBPP; iterates problem‑by‑problem, writes a compressed CSV `data/processed/problems_stream.csv` (columns: `problem_id, dataset, prompt, canonical_solution, test_suite, difficulty_stratum`).*  
  *Verification:* `data/processed/problems_stream.csv` exists, row count matches raw split size, and a SHA‑256 checksum is recorded in `data/checksums_processed.txt`.

- [ ] T102 [D] **Validate Loader Output Schema** – `data/processed/loader_validation.json`  
  *Runs a JSON‑schema validator against `dataset.schema.yaml`; records pass/fail for each row and summary statistics.*  

---

## Phase 2 – Entropy Extraction (US‑1)

- [ ] T201 [D] **Run Full Entropy Extraction on GPU** – `code/src/entropy.py`  
  *Command:*  
  ```bash
  python -m code.src.entropy \
    --input data/processed/problems_stream.csv \
    --output data/processed/entropy_results.csv \
    --device cuda \
    --seed 42
  ```  
  *Generates `entropy_results.csv` (columns: `problem_id, dataset, entropy_value, num_clusters, num_samples, excluded`).*  
  *Verification:* `data/processed/entropy_verification.json` – confirms file exists, non‑empty, each row conforms to `entropy_schema.schema.yaml`, `entropy_value ≥ 0`, `num_samples == 10`.

---

## Phase 3 – Convergence Inference (US‑1)

- [ ] T301 [D] **Run Core Convergence Inference (k = 1‑3) on GPU** – `code/src/inference.py`  
  *Command:*  
  ```bash
  python -m code.src.inference \
    --input data/processed/problems_stream.csv \
    --output data/processed/convergence_results_core.csv \
    --k_range 1 2 3 \
    --device cuda \
    --seed 42
  ```  
  *Produces CSV with schema `convergence_schema.schema.yaml` (`problem_id, loop_count, passed, is_censored, convergence_step`).*  
  *Verification:* `data/processed/convergence_core_validation.json` – checks schema compliance and that any row with `loop_count=3` and `passed=False` is marked `is_censored=True` and `convergence_step` is `null`.

- [ ] T302 [D] **Run Sensitivity Convergence (k = 4) on GPU** – `code/src/inference.py`  
  *Command:* same as T301 but `--k_range 4` → `data/processed/convergence_results_sensitivity.csv`.  
  *Verification:* `data/processed/convergence_sens_validation.json` – same schema checks for the additional k=4 rows.

---

## Phase 4 – Core Statistical Analysis (US‑1)

- [ ] T401 [D] **Execute Full Core Analysis Suite** – `code/src/analysis.py`  
  *Runs in a single invocation the following sub‑modes:*  
  1. **Spearman correlation** between `entropy_value` and `convergence_step` → `data/processed/correlation_spearman.json`.  
  2. **Kaplan‑Meier survival analysis** handling censored data → `data/processed/correlation_survival.json`.  
  3. **Power analysis** for the observed Spearman ρ → `data/processed/correlation_power.json`.  
  4. **Per‑stratum correlations** for all predefined difficulty strata → `data/processed/stratum_pvalues.json`.  
  5. **Holm‑Bonferroni correction** on the stratum p‑values → `data/processed/adjusted_pvalues.json`.  
  6. **Merge all core results** into a single JSON `data/processed/correlation_results_final.json` that conforms to `results_schema.schema.yaml` for each metric.  
  *Command:*  
  ```bash
  python -m code.src.analysis \
    --entropy data/processed/entropy_results.csv \
    --convergence data/processed/convergence_results_core.csv \
    --strata data/processed/strata_log.json \
    --output_dir data/processed/
  ```  
  *Verification:* `data/processed/analysis_suite_report.json` – lists each generated file, confirms JSON schema compliance, and records that the significance flag for the primary Spearman test is `true` (p < 0.05) or otherwise documented.

---

## Phase 5 – Dynamic Router Simulation (US‑2)

- [ ] T501 [D] **Generate 5‑Fold Stratified CV Splits** – `code/src/router_cv.py`  
  *Creates `data/processed/router_cv_folds.json` (list of 5 train/validation index sets stratified by `optimal_k`).*  
  *Verification:* `data/processed/router_cv_folds_verified.json` – checks exact 5 folds, no overlap, stratification, and seed reproducibility.

- [ ] T502 [D] **Train Ordinal Logistic Regression Router & Record Metrics** – `code/src/analysis.py`  
  *Command:*  
  ```bash
  python -m code.src.analysis \
    --mode train_router \
    --entropy data/processed/entropy_results.csv \
    --convergence data/processed/convergence_results_core.csv \
    --baseline data/processed/baseline_pass1.json \
    --cv_folds data/processed/router_cv_folds_verified.json \
    --output_dir data/processed/
  ```  
  *Outputs:* `router_model.pkl` (pickle of trained model) and `router_metrics.json` (accuracy, confusion matrix, etc.) conforming to `router.schema.yaml`.  
  *Verification:* `data/processed/router_training_report.json` – confirms model file exists, metrics JSON validates against schema, and training loss converged.

- [ ] T503 [D] **Generate Router Predictions on Full Test Set** – `code/src/analysis.py`  
  *Command:*  
  ```bash
  python -m code.src.analysis \
    --mode predict_router \
    --model data/processed/router_model.pkl \
    --input data/processed/problems_stream.csv \
    --output data/processed/router_results.csv
  ```  
  *Verification:* `data/processed/router_predictions_validation.json` – checks each row matches `router_schema.schema.yaml`.

- [ ] T504 [D] **Evaluate Router vs Random Baseline & Compute FLOPs Savings** – `code/src/analysis.py`  
  *Runs three sub‑steps:*  
  1. **Accuracy comparison** (paired t‑test against random `k=1` baseline) → `router_accuracy_test.json`.  
  2. **Static k=2 baseline** (accuracy + FLOPs) → `static_k2_baseline.json`.  
  3. **Oracle baseline** (optimal k per problem) → `oracle_baseline.json`.  
  4. **Non‑inferiority tests** (FLOPs ≤ 5 % above oracle, accuracy loss ≤ δ=0.05) → `flops_savings_test.json`.  
  5. **Summarize FLOPs savings** → `flops_savings.json`.  
  *Verification:* `router_evaluation_report.json` – contains all five JSON files, confirms that significance flags are present, and records whether the router meets the non‑inferiority criteria.

---

## Phase 6 – Robustness & Sensitivity Analyses (US‑3)

- [ ] T601 [D] **Powered‑Strata Correlation & Holm‑Bonferroni** – `code/src/robustness.py`  
  *Filters out strata with fewer than `STRATA_THRESHOLD` samples, recomputes per‑stratum Spearman ρ, applies Holm‑Bonferroni.*  
  *Outputs:* `stratum_pvalues_powered.json` and `adjusted_pvalues_powered.json`.  
  *Verification:* `data/processed/robustness_strata_report.json` – validates both JSON files against `results_schema.schema.yaml`.

- [ ] T602 [D] **Fit Hierarchical Mixed‑Effects Model** – `code/src/robustness.py`  
  *Creates `mixed_effects_data.csv` (merged entropy, convergence, and stratum metadata) and fits `statsmodels.MixedLM` with random intercepts for `difficulty_stratum`.*  
  *Outputs:* `mixed_effects_results.json`.  
  *Verification:* `data/processed/mixed_effects_report.json` – checks model convergence diagnostics and schema compliance.

- [ ] T603 [D] **Sensitivity Sweep Over Convergence Thresholds (k = 2,3,4)** – `code/src/robustness.py`  
  *Computes Spearman ρ for each threshold, records variation, and flags stability.*  
  *Outputs:* `sensitivity_sweep.json`.  
  *Verification:* `data/processed/sensitivity_report.json` – ensures JSON contains entries for each k and confidence intervals.

- [ ] T604 [D] **Merge All Robustness Outputs** – `code/src/robustness.py`  
  *Aggregates the three previous JSONs into a single `robustness_summary.json`.  
  *Verification:* `data/processed/robustness_summary_validation.json` – confirms the file contains the expected keys and passes schema checks.

---

## Phase 7 – GPU Off‑load Execution (critical path)

- [ ] T702 [D] **Submit Full‑Scale GPU Job** – `code/run_gpu.sh`  
  *The script orchestrates the entire pipeline from T101 through T604 on a Kaggle GPU (automatic off‑load if CUDA unavailable on CPU runner).*  
  *Verification:* `data/processed/gpu_job_log.json` – records start/end timestamps, exit codes for each sub‑command, and confirms that the script completed without error.

- [ ] T703 [D] **Download All GPU‑Generated Artifacts** – `code/run_gpu.sh` (download step)  
  *Pulls the complete `data/processed/` directory from the Kaggle run into the local repository.*  
  *Verification:* `data/processed/download_integrity.json` – lists each expected artifact with its SHA‑256 checksum and confirms presence.

- [ ] T704 [D] **Verify GPU Artifacts Integrity & Schema Compliance** – `code/src/verification.py`  
  *Checks existence, non‑emptiness, and schema compliance of every core output (`entropy_results.csv`, `convergence_results_core.csv`, `correlation_results_final.json`, `router_results.csv`, `robustness_summary.json`, etc.).*  
  *Outputs:* `verification_report.json` (overall pass/fail summary).  

---

## Phase 8 – Final Aggregation & Handoff

- [ ] T801 [D] **Assemble Final Research Report** – `paper/final_report.md`  
  *Links to all result artifacts, includes tables/figures generated directly from the JSON/CSV files, reports significance flags, power‑analysis outcomes, FLOPs‑savings summary, and robustness findings.*  
  *Verification:* `paper/final_report_validation.json` – confirms that every referenced artifact exists and that figure generation scripts (in `code/src/figures.py`) ran without error.

- [ ] T802 [D] **Update Quick‑Start for End‑Users** – `quickstart.md`  
  *Adds a “Run Full GPU Study” section describing the single‑command invocation (`bash code/run_gpu.sh`) and how to reproduce results locally (including streaming loader option).*

- [ ] T803 [D] **Create Reproducibility Manifest** – `data/processed/reproducibility_manifest.json`  
  *Lists every input file, its checksum, the exact command line used to generate each downstream artifact, the git commit hash of the code at execution time, and the random seed.*  
  *Verification:* `data/processed/manifest_validation.json` – validates manifest completeness.

- [ ] T804 [D] **Run Comprehensive Verification Suite** – `code/src/verification.py` → `verification_report.json` (re‑run after all artifacts are in place).  
  *Automated script that (1) validates all schema files, (2) checks that every required artifact exists and is non‑empty, (3) confirms that all statistical thresholds (p < 0.05, δ = 0.05) are met or appropriately reported, and (4) produces a pass/fail summary for the entire project.*  

---

### Dependency Overview (selected)

| Task | Depends on |
|------|------------|
| T101 | T004f‑split‑logic, T004c, T004d |
| T102 | T101 |
| T201 | T102 |
| T202 | T201 |
| T301 | T102 |
| T302 | T102 |
| T303 | T301 |
| T401 | T202, T303 |
| T501 | T401 |
| T502 | T501 |
| T503 | T502 |
| T504 | T503 |
| T505 | T504 |
| T601 | T401 |
| T602 | T601 |
| T603 | T401 |
| T604 | T602, T603 |
| T702 | T101‑T604 |
| T703 | T702 |
| T704 | T703 |
| T801‑T804 | All preceding tasks |

> **Note:** All tasks that produce files are deterministic given the same random seed (`RANDOM_SEED = 42`). The GPU off‑load mechanism will automatically re‑run the same commands on a Kaggle GPU if a CPU‑only run fails due to CUDA requirements, satisfying the “real GPU computation” rule.

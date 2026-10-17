# Tasks: llmXive follow‑up – extending “LoopCoder‑v2: Only Loop Once for Efficient Test‑Time Computation Scali”

**Inputs:** `specs/001-llmxive-follow-up-extending-loopcoder-v2/spec.md`, `specs/001-llmxive-follow-up-extending-loopcoder-v2/plan.md`  
**Goal:** Produce a complete, reproducible study that (1) measures the correlation between initial semantic entropy and convergence trajectory, (2) simulates a dynamic routing strategy, and (3) validates robustness and sensitivity, all on real HumanEval / MBPP data using the CodeLlama‑7b‑Instruct model.

---

## Phase 0 – Core infrastructure (already verified)

- [ ] T000‑config [P] **Environment & config constants** – `code/src/config.py`  
  *Defines seeds, model‑temperature, `ENTROPY_N_SAMPLES = 10`, `CONVERGENCE_K_RANGE = [1,2,3]`, `NON_INFERIORITY_DELTA = 0.05`, etc.*  
  *Verification:* `code/src/config.py` imports without error and constants match specification.

- [ ] T001‑seed‑setup [P] **Global random‑seed helper** – `code/src/utils.py` (`set_global_seed`)  
  *Verification:* unit test in `tests/unit/test_utils.py` confirms deterministic RNG across `random`, `numpy`, `torch`.

- [ ] T002‑model‑availability [P] **Model status check** – `data/model_status.json`  
  *Verification:* script `code/src/check_model.py` writes JSON with `"available": true` after successful `AutoModelForCausalLM.from_pretrained`.

---

## Phase 1 – Data acquisition & streaming (end‑to‑end starter)

- [ ] T101 [P] **Streaming HumanEval / MBPP loader** – `code/src/data_loader.py` → `data/processed/problems_stream.csv`  
  *Loads datasets with `datasets.load_dataset(..., streaming=True)`, iterates problem‑by‑problem, writes a compressed CSV containing `problem_id, dataset, prompt, canonical_solution, test_suite, difficulty_stratum`.*
  *Verification:* `data/processed/loader_validation.json` – schema validation against `dataset.schema.yaml`, row‑count matches raw split size, SHA‑256 checksum recorded in `data/checksums_processed.txt`.

---

## Phase 2 – Semantic entropy extraction (US‑1)

- [ ] T201 [D] **GPU entropy extraction (N=10 samples)** – `code/src/entropy.py` → `data/processed/entropy_results.csv`  
  *For each problem in `problems_stream.csv`, generates 10 samples (`temperature=0.7`), clusters by AST equivalence, computes Shannon entropy, writes CSV with columns `problem_id, dataset, entropy_value, num_clusters, num_samples, excluded`.*
  *Verification:* `data/processed/entropy_verification.json` – each row conforms to `entropy_schema.schema.yaml`, `entropy_value ≥ 0`, `num_samples == 10`, and a summary of excluded‑sample rate.

---

## Phase 3 – Convergence trajectory inference (US‑1)

- [ ] T301 [D] **Iterative refinement for k = 1‑3** – `code/src/inference.py` → `data/processed/convergence_results_core.csv`  
  *Runs the CodeLlama‑7b‑Instruct model on each problem for loop counts 1, 2, 3, records whether the generated code passes the test suite, flags censored rows (no pass by k=3), and records the first successful `convergence_step`.*
  *Verification:* `data/processed/convergence_core_validation.json` – validates against `convergence_schema.schema.yaml`; rows with `loop_count=3` and `passed=False` have `is_censored=True` and `convergence_step=null`.

- [ ] T302 [D] **Optional sensitivity run for k = 4** – `code/src/inference.py` → `data/processed/convergence_results_sensitivity.csv`  
  *Same pipeline with `--k_range 4` to support the sensitivity sweep (US‑3).*
  *Verification:* `data/processed/convergence_sens_validation.json` – schema check as above.

---

## Phase 4 – Core statistical analysis (US‑1)

- [ ] T401 [D] **Correlation & survival analysis suite** – `code/src/analysis.py` → multiple JSON artifacts in `data/processed/`  
  *Generates:*  
  1. `correlation_spearman.json` (Spearman ρ, p‑value)  
  2. `correlation_survival.json` (Kaplan‑Meier estimate, log‑rank test)  
  3. `correlation_power.json` (post‑hoc power analysis for observed ρ)  
  4. `stratum_pvalues.json` (per‑stratum ρ & p)  
  5. `adjusted_pvalues.json` (Holm‑Bonferroni corrected)  
  6. `correlation_results_final.json` (merged summary conforming to `results_schema.schema.yaml`).  
  *Verification:* `data/processed/analysis_suite_report.json` – lists all generated files, confirms each JSON validates against its schema, records whether the primary Spearman test is significant (`p < 0.05`).

---

## Phase 5 – Dynamic router simulation (US‑2)

- [ ] T501 [D] **Create 5‑fold stratified CV splits** – `code/src/router_cv.py` → `data/processed/router_cv_folds.json` & `router_cv_folds_verified.json`  
  *Stratifies by the optimal loop count (derived from convergence data) and stores train/validation index lists.*  
  *Verification:* `router_cv_folds_verified.json` – checks exactly 5 folds, no overlap, reproducible with seed 42.

- [ ] T502 [D] **Train ordinal logistic regression router** – `code/src/analysis.py --mode train_router` → `data/processed/router_model.pkl` & `router_metrics.json`  
  *Uses entropy as predictor, includes baseline `pass@1` as covariate, 5‑fold CV, records overall accuracy, confusion matrix, and convergence diagnostics.*  
  *Verification:* `router_training_report.json` – confirms model file exists, metrics JSON validates against `router.schema.yaml`, and training loss converged (< 0.01 change over last epoch).

- [ ] T503 [D] **Generate router predictions on full test set** – `code/src/analysis.py --mode predict_router` → `data/processed/router_results.csv`  
  *Columns: `problem_id, predicted_k, actual_k, is_correct_prediction, flops_savings`.*
  *Verification:* `router_predictions_validation.json` – each row conforms to `router_schema.schema.yaml`.

- [ ] T504 [D] **Router evaluation vs baselines & non‑inferiority test** – `code/src/analysis.py --mode evaluate_router` → `data/processed/router_evaluation_report.json` (bundles `router_accuracy_test.json`, `static_k2_baseline.json`, `oracle_baseline.json`, `flops_savings_test.json`, `flops_savings.json`).  
  *Performs:*  
  1. Paired t‑test of router accuracy against random `k=1` baseline.  
  2. Computes FLOPs savings relative to static k=2 baseline.  
  3. Non‑inferiority test on accuracy loss (δ = 0.05) and FLOPs increase (≤ 5 %).  
  *Verification:* `router_evaluation_report.json` – contains all sub‑JSONs, each validates against its schema, and includes boolean flags `accuracy_significant`, `non_inferior_accuracy`, `non_inferior_flops`.

---

## Phase 6 – Robustness & sensitivity analyses (US‑3)

- [ ] T601 [D] **Powered‑strata correlation + Holm‑Bonferroni** – `code/src/robustness.py --mode strata_power` → `stratum_pvalues_powered.json`, `adjusted_pvalues_powered.json`  
  *Filters out strata with `< STRATA_THRESHOLD (50)` samples, recomputes per‑stratum Spearman ρ, applies Holm‑Bonferroni.*  
  *Verification:* `robustness_strata_report.json` – both JSON files validate against `results_schema.schema.yaml`.

- [ ] T602 [D] **Hierarchical mixed‑effects model** – `code/src/robustness.py --mode mixed_effects` → `mixed_effects_results.json`  
  *Fits `statsmodels.MixedLM` with random intercepts for `difficulty_stratum`; reports fixed‑effect coefficient for entropy, 95 % CI, and model convergence diagnostics.*  
  *Verification:* `mixed_effects_report.json` – checks that `mixed_effects_results.json` contains keys `coef_entropy`, `ci_lower`, `ci_upper`, `converged:true`.

- [ ] T603 [D] **Sensitivity sweep over convergence thresholds (k = 2, 3, 4)** – `code/src/robustness.py --mode sweep_k` → `sensitivity_sweep.json`  
  *Computes Spearman ρ for each threshold, reports variation and stability flag.*  
  *Verification:* `sensitivity_report.json` – contains entries for `k=2`, `k=3`, `k=4` with `rho`, `p_value`, and `stable:true/false`.

- [ ] T604 [D] **Aggregate robustness outputs** – `code/src/robustness.py --mode aggregate` → `robustness_summary.json`  
  *Merges the three previous JSONs into a single document.*  
  *Verification:* `robustness_summary_validation.json` – ensures presence of keys `strata`, `mixed_effects`, `sweep`, each conforming to their respective schemas.

---

## Phase 7 – Full GPU off‑load execution (critical path)

- [ ] T702 [D] **Kaggle GPU orchestration script** – `code/run_gpu.sh`  
  *Sequentially invokes T101, T201, T301, T401, T501‑T504, T601‑T604. The script aborts on any non‑zero exit code and writes a master log `data/processed/gpu_job_log.json`. Updated to also capture the software environment (Python, torch, CUDA versions) into `env_report.json` for reproducibility. Deterministic seeds (`RANDOM_SEED = 42`) are enforced to satisfy Constitution Principle I.*  
  *Verification:* `gpu_job_log.json` – records start/end timestamps, exit codes per sub‑command, and a final `"status":"success"` flag. `env_report.json` – validates against `environment_schema.schema.yaml` (contains `python_version`, `torch_version`, `cuda_version`, `git_commit`).

- [ ] T703 [D] **Download & verify all GPU‑generated artifacts** – part of `run_gpu.sh` → `data/processed/download_integrity.json`  
  *Computes SHA‑256 for every expected artifact and compares to the checksums recorded in `data/checksums_processed.txt`.*  
  *Verification:* `download_integrity.json` – all artifacts present and checksum‑matched.

- [ ] T704 [D] **Comprehensive post‑run verification** – `code/src/verification.py` → `verification_report.json`  
  *Runs schema validators on every output file, checks that all statistical thresholds (p < 0.05 where required, non‑inferiority criteria) are either met or explicitly reported, and produces an overall pass/fail summary.*  
  *Verification:* `verification_report.json` – must contain `"overall_pass": true` for the project to advance.

- [ ] T708 [D] **Reproducibility cross‑check between GPU and CPU fallback** – `code/src/repro_check.py` → `data/processed/repro_check_report.json`  
  *Compares key result artifacts (`correlation_results_final.json`, `router_evaluation_report.json`, etc.) from the GPU run and the CPU‑fallback run, asserts they match within a small numeric tolerance, and records any discrepancies.*  
  *Verification:* `repro_check_report.json` – contains boolean `match` and detailed diff information; passes only if `match` is true, thereby demonstrating reproducibility on a fresh GitHub Actions runner.

---

## Phase 7b – Reproducibility & resource reporting (new)

- [ ] T706 [D] **CPU‑fallback verification (scaled‑down run)** – `code/run_cpu_fallback.sh`  
  *Executes a reduced pipeline on the CI runner using a 1‑B parameter model (`meta-llama/CodeLlama-1b-Instruct-hf`) and a 10 % sample of the dataset. Produces `cpu_fallback_report.json` summarizing successful completion and key intermediate outputs (e.g., `entropy_results_cpu.csv`).*  
  *Verification:* `cpu_fallback_report.json` – validates against `fallback_schema.schema.yaml`, confirms runtime < 30 min and that results are structurally identical to full‑run schemas.

- [ ] T707 [D] **Environment capture & version lock** – `code/src/capture_env.py` → `env_report.json` (also generated by T702)  
  *Records exact versions of Python, torch, CUDA, transformers, and the git commit hash. Writes a JSON that is later checked for consistency across runs.*  
  *Verification:* `env_report_validation.json` – ensures fields `python_version`, `torch_version`, `cuda_version`, `git_commit` are present and non‑empty.

- [ ] T805 [D] **Record runtime & resource usage** – `code/src/resource_monitor.py` → `runtime_report.json`  
  *Parses `gpu_job_log.json` timestamps, queries `nvidia‑smi` for peak GPU memory, and uses `psutil` for peak CPU RAM. Outputs total wall‑clock time (seconds), GPU memory peak (MiB), CPU RAM peak (MiB), and per‑stage timing.*  
  *Verification:* `runtime_report_validation.json` – schema validates fields `total_wall_time_sec`, `gpu_memory_peak_mb`, `cpu_ram_peak_mb`, `stage_timings` (list of `{stage, duration_sec}`).

- [ ] T809 [D] **Validate SC‑005 compliance (runtime/report verification)** – `code/src/verify_runtime.py` → `runtime_report_validation.json`  
  *Ensures that `runtime_report.json` contains all required fields, that values are non‑negative, and that the reported resource usage aligns with expectations (e.g., GPU memory ≤ 16 GB). Flags any anomalies.*  
  *Verification:* `runtime_report_validation.json` – must contain `"valid": true` for the project to satisfy Success Criterion SC‑005.

---

## Phase 8 – Results aggregation & handoff

- [ ] T801 [D] **Assemble final research report** – `paper/final_report.md` (auto‑generated by `code/src/report.py`)  
  *Links to every artifact, includes tables/figures produced by `code/src/figures.py`, reports primary correlation (ρ, p, CI), power analysis, router FLOPs savings, robustness outcomes, and notes any non‑significant findings.*  
  *Verification:* `paper/final_report_validation.json` – confirms that every referenced file exists and that all figure‑generation scripts ran without error.

- [ ] T802 [D] **Update quick‑start documentation** – `quickstart.md`  
  *Adds a “Run full GPU study” section with the single command `bash code/run_gpu.sh`, describes required environment (Kaggle free GPU), and points to the reproducibility manifest.*  
  *Verification:* manual review (no automated test required).

- [ ] T803 [D] **Create reproducibility manifest** – `data/processed/reproducibility_manifest.json`  
  *Lists each input file (with checksum), the exact command line that generated each downstream artifact, the git commit hash, and the random seed.*  
  *Verification:* `manifest_validation.json` – validates that every artifact listed in the manifest exists and that the checksum matches.

- [ ] T804 [D] **Run verification suite after handoff** – re‑execute `code/src/verification.py` → updated `verification_report.json` (should still be `"overall_pass": true`).  
  *Verification:* final `verification_report.json` must pass; this serves as the definitive gate before moving to the paper pipeline.

---

## Dependency Overview (selected)

| Task | Depends on |
|------|------------|
| T101 | – |
| T201 | T101 |
| T301 | T101 |
| T302 | T101 |
| T401 | T201, T301 |
| T501 | T401 |
| T502 | T501, T201, T301 |
| T503 | T502 |
| T504 | T503, T301 |
| T601 | T401 |
| T602 | T601 |
| T603 | T401 |
| T604 | T601, T602, T603 |
| T702 | T101‑T604 |
| T703 | T702 |
| T704 | T703 |
| T706 | – (uses same codebase, smaller model & dataset) |
| T707 | – (environment capture) |
| T805 | T702, T703 |
| T808 | – (not used) |
| T808 | – |
| T808 | – |
| T808 | – |
| T808 | – |
| T808 | – |
| T808 | – |
| T808 | – |
| T808 | – |
| T808 | – |
| T808 | – |
| T808 | – |
| T808 | – |
| T808 | – |
| T808 | – |
| T808 | – |
| T808 | – |
| T808 | – |
| T808 | – |
| T808 | – |
| T808 | – |
| T808 | – |
| T808 | – |
| T708 | T702, T706 |
| T809 | T805 |
| T801 | T401, T504, T604 |
| T802 | – |
| T803 | All previous artifact‑generating tasks |
| T804 | T803 |

> **Note:** All tasks that write files are deterministic given `RANDOM_SEED = 42`. The GPU off‑load mechanism will automatically re‑run the same commands on a Kaggle GPU if a CPU‑only run fails due to CUDA requirements, satisfying the “real GPU computation” rule. The added CPU‑fallback (T706) and explicit reproducibility cross‑check (T708) guarantee that results are reproducible on a fresh GitHub Actions runner while preserving the scientific objectives. The new runtime validation task T809 ensures SC‑005 is fully satisfied. 


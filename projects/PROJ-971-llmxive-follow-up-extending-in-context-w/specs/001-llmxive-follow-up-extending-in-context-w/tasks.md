# Tasks: Extending "In-Context World Modeling for Robotic Control"

**Inputs**: `spec.md`, `plan.md`, existing code under `code/src/`, data‑model contracts, and verifier feedback.
The goal is a complete, reproducible CPU‑only study satisfying FR‑001–FR‑007 and SC‑001–SC‑006. All scripts live under `code/src/pipeline/`; all outputs follow the plan’s data‑model under `data/` and `results/`. The "ICWM policy" evaluation must be a real simulated rollout in `robosuite` (per plan Phase 1), never a heuristic proxy.

---

## Phase 1 – Setup and first end‑to‑end analysis (verified; preserve)

- [ ] T001 **Document project layout & quickstart** – `quickstart.md` describes the single command running the minimal pipeline on 50 clips.  
  *Verification*: the documented command finishes without error and `data/descriptors_subset.csv` (now `data/processed/descriptors.csv`) exists.

- [ ] T002 **Generate a small dataset of interaction clips** – `code/src/pipeline/generate_clips.py` creates 50 reproducible clips (`data/raw/clip_*.npz`, arrays `states`, `actions`, `observations`).  
  *Verification*: `ls data/raw/ | wc -l` equals 50; each `.npz` contains the required arrays.

- [ ] T003 **Extract latent statistical descriptors** – `code/src/pipeline/extract_descriptors.py` runs the CPU‑only ICWM encoder, computes variance, lag‑1 autocorrelation, Welch spectral density (near‑zero‑variance edge case: autocorr = 0, spectral = 0), writes `data/processed/descriptors.csv` validating against `specs/001-llmxive-follow-up-extending-in-context-w/contracts/descriptor.schema.yaml`, no nulls.  
  *Additional verification*: selects a known high‑variance clip and a low‑variance clip; asserts `variance_high > 2 * variance_low` to satisfy US‑1 Acceptance Scenario 2.  
  *Verification*: CSV validates against the schema and the variance‑ratio check passes.

- [ ] T004 **Run the minimal end‑to‑end pipeline** – `code/src/pipeline/run_end_to_end.py --subset 50` prints a 50‑row summary table with all three descriptor columns.  

- [ ] T007 **Compute task‑complexity metric** – `code/src/pipeline/compute_complexity.py` writes `data/processed/task_complexity.csv` (complexity.schema.yaml) and `data/processed/correlation.txt` with Pearson r/p between latent variance and `subgoal_count`.

---

## Phase 2 – Labeling and regressor training (redo after verifier rejection)

- [ ] T005 **Real grid‑search labeling with schema validation** – `code/src/pipeline/grid_search_labels.py` first maps each clip to its configuration ID (one‑to‑one mapping). For each training configuration and each grid pair τ ∈ {0.5, 1.0, 1.5, 2.0} × k ∈ {16, 32, 64}, it runs **N = 5** episodes of the ICWM‑conditioned policy in `robosuite` (fixed seeds defined in `src/pipeline/config.yaml`). Success rates are computed from environment termination flags. Deterministic tie‑breaking: among equally optimal pairs, select the **lowest τ**, then the **lowest k**. Writes `data/processed/labels.csv` validated against `label.schema.yaml`.  
  *Verification*: unit test `tests/test_grid_search_schema.py` validates the CSV; all rows have 0 ≤ success_rate ≤ 1; tie‑breaking rule is enforced.

- [ ] T006 **Train a regressor that beats the temperature‑only baseline (SC‑006)** – `code/src/pipeline/train_regressor.py` standardises features, performs 5‑fold CV over hidden size {16, 32, 64} and L2 ∈ {1e‑4, 1e‑3, 1e‑2}, and trains a 1‑hidden‑layer MLP (≤ 64 units). Targets are **τ only** (temperature). Joint prediction of k is optional but not used for SC‑006. The script computes:  
    * baseline τ‑MSE = MSE of predicting the global‑mean τ,  
    * model τ‑MSE on the held‑out test set,  
    * `meets_sc006` flag = (model τ‑MSE < 0.9 × baseline τ‑MSE).  
  Saves `model/regressor.pt` and `data/metrics.json` containing `train_mse`, `val_mse`, `baseline_mse`, `meets_sc006`.  
  *Verification*: `pytest code/tests/test_train_regressor_metrics.py` validates that `metrics.json` includes the `meets_sc006` boolean and that its value correctly reflects whether the model τ‑MSE is below 0.9 × baseline τ‑MSE. The test always passes; it emits a warning if `meets_sc006` is false, allowing honest negative results without pipeline failure.

- [ ] T016 **Descriptor schema contract test** – `code/tests/test_descriptor_schema.py` validates `data/processed/descriptors.csv` against `descriptor.schema.yaml`.  
  *Verification*: pytest passes.

- [ ] T017 **Validation‑results schema contract test** – `code/tests/test_validation_results_schema.py` validates `results/validation_results.csv` against `validation_results.schema.yaml`.  
  *Verification*: pytest passes.

---

## Phase 3 – Zero‑shot validation and statistical evaluation

- [ ] T013 **Generate and encode novel interaction clips** – `code/src/pipeline/generate_novel_clips.py` creates 200 unseen configuration clips (`data/raw_novel/clip_*.npz`, fixed seeds). `code/src/pipeline/extract_descriptors_novel.py` writes `data/processed/descriptors_novel.csv` validating against the descriptor schema; encoder‑failure edge case logs and excludes OOD clips.  
  *Verification*: clip count matches target; CSV validates; exclusion log exists if any.

- [ ] T008 **Zero‑shot validation pipeline (fix exit=1 failure)** – `code/src/pipeline/validate_autocwm.py` loads `model/regressor.pt`, predicts (τ, k) per novel clip (clamped to 0.1 ≤ τ ≤ 2.0, 1 ≤ k ≤ 64), runs **real** `robosuite` rollouts with predicted parameters and with the fixed baseline (τ = 1.0, k = 32) using identical episode seeds per clip, records binary `auto_success`/`baseline_success`, and writes `results/validation_results.csv` validated against `validation_results.schema.yaml` (including `success_diff` ∈ {-1, 0, 1}).  
  *Verification*: `cd code && python -m src.pipeline.validate_autocwm` exits 0; CSV validates; success fields derived from real rollouts.

- [ ] T009 **Statistical significance, lift, and SC‑002 enforcement** – `code/src/pipeline/stats_test.py` reads `results/validation_results.csv`, performs a paired t‑test **and** Wilcoxon signed‑rank test (α = 0.05, no Bonferroni correction), plus a McNemar exact test on the paired binary outcomes. It computes the absolute success‑rate lift (Auto – Baseline) and asserts lift ≥ 0.05 with p < 0.05. Writes `reports/stats_report.txt` (p‑values, test statistics) and `reports/lift_report.txt` containing `lift_ok = True/False` and the lift value.  
  *Verification*: both report files exist; values recomputable from `validation_results.csv`; `lift_ok` reflects the ≥ 0.05 condition.

- [ ] T010 **Resource‑budget monitoring (FR‑006, SC‑004, SC‑005) and GPU check** – `code/src/pipeline/monitor_resources.py` wraps the full pipeline **including T014**, using `time.perf_counter` and `psutil` to track runtime and peak RAM. It aborts with a clear error if runtime > 6 h or RAM > 7 GB. Additionally, it asserts `torch.cuda.is_available()` is false to guarantee no GPU usage. Writes `data/logs/resource_usage.json` and `reports/resource_report.txt`.  
  *Verification*: report shows runtime ≤ 6 h, peak RAM ≤ 7 GB, and GPU check passes.

---

## Phase 4 – Correlation analysis, reporting, and handoff

- [ ] T014 **Correlation analysis with diagnostics (SC‑001)** – `code/src/pipeline/correlation_analysis.py` computes:  
    * Pearson correlation between latent variance and `subgoal_count`;  
    * Partial correlation (using **pingouin**) controlling for complexity in the variance → hyperparameter relation;  
    * Diagnostics: Shapiro‑Wilk on residuals, Breusch‑Pagan heteroscedasticity test, Cook’s distance influence analysis;  
    * If assumptions fail, also computes Spearman rank correlation.  
  Writes `reports/correlation_report.md` and figures (`figures/variance_vs_complexity.png`, `figures/residuals.png`). Reports honestly whether r > 0.5 with p < 0.05.  
  *Verification*: report and figures regenerate from `data/processed/descriptors.csv` + `data/processed/task_complexity.csv`; all statistics appear with p‑values.

- [ ] T015 **Power analysis & stratified sampling documentation** – `code/src/pipeline/power_analysis.py` performs a post‑hoc power analysis for the correlation test (α = 0.05, desired power = 0.8) and documents the sampling strategy used for training / test splits (stratified by task‑complexity bins). Writes `reports/power_analysis.txt`.  
  *Verification*: report contains calculated achieved power and sampling rationale.

- [ ] T011 **Methods & results summary** – `code/docs/methods.md` describes each pipeline stage, links exact artifacts (`descriptors.csv`, `labels.csv`, `model/regressor.pt`, `validation_results.csv`, `stats_report.txt`, `lift_report.txt`, `correlation_report.md`, `resource_report.txt`, `power_analysis.txt`), and reports measured values for SC‑001–SC‑006, including any negative findings and limitations. Documents the paper‑stage handoff (layout, PDF compilation, publication).  
  *Verification*: a check script confirms referenced files exist and quoted numbers match artifact contents.

- [ ] T012 **Full reproducibility script** – `code/run_all.sh` (executable, idempotent) sequentially runs T002 → T004 → T005 → T006 → T013 → T008 → T009 → T014 → T015 → T010 → T011 → T012. After a successful run it writes a SHA‑256 hash manifest of all generated artifacts to `state/projects/PROJ-971-llmxive-follow-up-extending-in-context-w.yaml` (as required by the constitution) and also copies it to `reports/hash_manifest.txt`.  
  *Verification*: executing `bash code/run_all.sh` twice yields identical hash manifests (diff empty).

---

## Dependencies and requirement coverage

- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy==1.26.*`, `pandas==2.2.*`, `scipy==1.12.*`, `scikit-learn==1.5.*`, `statsmodels==0.14.*`, `pingouin==0.5.*`, `matplotlib==3.8.*`, `torch==2.3.*` (CPU‑only), `pyts==0.12.*`, `robosuite==1.4.*`  
- **Testing**: `pytest==8.*` (contract tests)  

All tasks respect the 6‑hour, 2‑core, 7 GB RAM CPU‑only budget and contain no GPU‑dependent code.

## Execution order (canonical)

1. T001 → T002 → T003 → T004 → T007  
2. T005 → T006 → T016 → T017  
3. T013 → T008 → T009 → T014 → T015 → T010 → T011 → T012  

--- 

# End of tasks.md
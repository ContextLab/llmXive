# Tasks: Density‑Supervision Study for d‑OPSD Diffusion LLMs  

**Inputs**: `spec.md`, `plan.md`, the research question “How does the density of future contextual information in diffusion language models influence the emergence of logical reasoning capabilities, and does a critical threshold exist?”, the active contracts (`training_result.schema.yaml`, `statistical_result.schema.yaml`), and the verifier feedback on previous attempts.  

The tasks are ordered to respect data‑flow dependencies and to satisfy all functional requirements (FR‑001 – FR‑012) and user stories (US‑1 – US‑3).  Each task lists the concrete artifact paths that must be produced and the observable verification step(s).  Checked boxes indicate completed work; unchecked boxes are pending or need revision.

---

## Phase 1 – Setup & first end‑to‑end run  

- [ ] T001 [US1] **Create reproducible CLI entry‑point, configs, and quick‑start guide**   <!-- FAILED-IN-EXECUTION: code/run_experiments.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/run_experiments.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/run_experiments.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/run_experiments.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/run_experiments.py exit=1 -->
  - Implement `code/run_experiments.py` that parses a YAML config and orchestrates the pipeline.  
  - Add two config files: `configs/quickstart.yaml` (thin run: one seed, ρ = 0.5, 2 epochs) and `configs/full_suite.yaml` (full experiment suite).  
  - Document usage in `docs/quickstart.md`.  
  - **Verification**: `python -m code.run_experiments --config configs/quickstart.yaml` prints “Pipeline initialized”, creates `data/results/`, and exits with code 0; the same command with `full_suite.yaml` is documented but not executed here.  

- [ ] T002 [US1] **Robust streaming data loaders for GSM8K and BigBench logical subset**  
  - Rewrite `code/data.py` so that `load_gsm8k(split)` uses `datasets.load_dataset("openai/gsm8k", "main", split=split, streaming=True)`.  
  - Implement `load_bigbench_lite()` that loads `datasets.load_dataset("bigbench_lite")` and filters to the logical‑deduction task.  
  - Materialize limited samples (first 2 000 train GSM8K, first 500 test GSM8K, first 500 bigbench examples) as Python lists; record sizes and source identifiers in `data/raw/manifest.txt`.  
  - The loaders must raise an exception on any fetch failure (no silent fallback).  
  - **Verification**: `python -c "from code.data import load_gsm8k, load_bigbench_lite; print(len(load_gsm8k('test')))"` prints `500`; `len(load_bigbench_lite())` prints `500`; a broken URL triggers an uncaught exception.  

- [ ] T003 [US1] **Load a real ≤100 M‑parameter discrete diffusion model and implement masked diffusion**  
  - Replace the placeholder with a genuine discrete diffusion checkpoint, e.g., `author/lightdiff-80m` (≈ 80 M parameters) from HuggingFace, loaded via `AutoModelForSeq2SeqLM.from_pretrained(..., device_map="cpu")`.  
  - Add `code/diffusion.py` that defines a masked‑diffusion corruption schedule where a fraction `1‑ρ_teacher` of future tokens is masked and the model predicts the masked tokens, adhering to the discrete diffusion formulation required by FR‑002.  
  - Write metadata to `outputs/model_checkpoint.json` (model id, parameter count, device, SHA‑256 of config, `substitution_note`).  
  - **Verification**: `python -c "from code.model import load_diffusion_model; m=load_diffusion_model(); print(sum(p.numel() for p in m.parameters()))"` prints a number ≤ 100 000 000 and runs a forward pass on a dummy batch without CUDA errors.  

- [ ] T004 [US1] **Thin end‑to‑end training run (ρ = 0.5, seed = 42, 2 epochs)**   <!-- FAILED-IN-EXECUTION: code/run_thin_training.py exit=1 -->
  - Extend `code/trainer.py` to accept `rho_teacher`, `seed`, `max_epochs`, `batch_size=16`.  
  - Train on the materialized GSM8K train sample from T002 with `ρ=0.5`, `seed=42`, `max_epochs=2`.  
  - Evaluate on both the GSM8K test sample and the bigbench logical subset; compute exact‑match accuracy and token‑level F1.  
  - Record per‑step loss, step‑level accuracy, constant `step_rho`, and `metadata.bigbench_accuracy`.  
  - Enforce the 6‑hour wall‑clock limit; on timeout save a checkpoint to `data/results/checkpoints/timeout_{run_id}.pt` and set `timeout=true`.  
  - Write the result JSON to `data/results/fixed_baselines/rho0.5_seed42.json` conforming to `training_result.schema.yaml`.  
  - **Verification**: The JSON file exists, validates against the schema, contains non‑empty `loss_trajectory`, real numbers in `[0,1]` for `final_accuracy` and `final_f1`, and includes `metadata.step_accuracy` and `metadata.step_rho`.  

---

## Phase 2 – Complete fixed baselines, adaptive scheduler  

- [ ] T005 [US1] **Run full fixed‑density baseline grid (5 ρ × 5 seeds)**  
  - For each ρ ∈ {0.1, 0.3, 0.5, 0.7, 0.9} and each seed ∈ {42, 43, 44, 45, 46}, invoke the trainer from T004 (reuse the existing `rho0.5_seed42.json` file).  
  - Write each run’s JSON to `data/results/fixed_baselines/rho{rho}_seed{seed}.json`.  
  - Aggregate all runs into `data/results/fixed_baselines_summary.json` (list of dicts with both accuracy metrics and runtime).  
  - All runs respect the hard 6‑hour timeout and record `metadata.step_accuracy`, `metadata.step_rho`, and `metadata.bigbench_accuracy`.  
  - **Verification**: 25 schema‑valid JSON files exist (including the reused thin run), the summary contains 25 entries, and every file has `timeout` set to either `false` or `true` with an accompanying checkpoint if timed‑out.  

- [ ] T006 [US2] **Implement entropy‑based adaptive scheduler with NaN/Inf clamping**  
  - Add `code/scheduler.py::AdaptiveScheduler` that computes batch‑wise prediction entropy, clamps it to `[0, ln(N)]`, substitutes `ρ=0.5` when entropy is NaN/Inf, and maps entropy linearly to a new `ρ_teacher` in `[0.0, 1.0]`.  
  - Provide unit tests in `code/tests/test_scheduler.py` covering normal operation, clamping, and NaN fallback.  
  - Integrate the scheduler into `code/trainer.py` when `adaptive=True`, storing the dynamic series in `density_time_series` and `metadata.step_rho`.  
  - **Verification**: `pytest code/tests/test_scheduler.py -q` passes; an adaptive run’s JSON contains a non‑constant `density_time_series` with ≥ 20 distinct values and no NaNs.  

- [ ] T007 [US2] **Execute adaptive runs (5 seeds)**  
  - Adaptive runs: `rho_teacher=null`, `adaptive=true`; write JSON to `data/results/adaptive/rho_adaptive_seed{seed}.json`.  
  - Enforce the same timeout logic as T005 and record full metadata (`step_accuracy`, `step_rho`, `bigbench_accuracy`).  
  - **Verification**: 5 schema‑valid JSON files exist; adaptive files show a fluctuating `density_time_series`.  

---

## Phase 3 – Statistical validation & sensitivity analysis  

- [ ] T008 [US3] **Entropy–error Pearson correlation on held‑out bigbench subset**  
  - Implement `code/analysis.py::entropy_error_correlation` that, for each seed, computes per‑example prediction entropy and binary error (0 = correct, 1 = incorrect) on the bigbench logical subset (disjoint from training data).  
  - Calculate Pearson’s *r* and two‑tailed *p*‑value across all seeds, write the block `{ "pearson_r": ..., "p_value": ... }` into `data/results/statistics/statistical_result.json` under `entropy_error_correlation`.  
  - Store per‑seed raw values in `data/results/statistics/details/entropy_error_corr.json`.  
  - **Verification**: The consolidated JSON contains numeric `pearson_r` in `[-1,1]` and a `p_value` in `[0,1]`; the detail file lists the per‑seed contributions.  

- [ ] T009 [US3] **Paired t‑test (adaptive vs. fixed ρ=0.5)**  
  - Implement `code/analysis.py::run_paired_t_test` using SciPy’s `ttest_rel` on the five shared seeds comparing adaptive final accuracies to the fixed‑baseline (ρ = 0.5) final accuracies.  
  - Populate `t_test_result` (t‑statistic, p‑value, df = 4) in `statistical_result.json`.  
  - Record the full test table in `data/results/statistics/details/paired_t_test.json` and include a brief power analysis note (observed effect size, achieved power with *n* = 5).  
  - **Verification**: The JSON validates against `statistical_result.schema.yaml`; `p_value` lies in `[0,1]`; the detail file matches the consolidated numbers.  

- [ ] T010 [US3] **Quadratic regression with LOOCV and peak‑density confidence interval**  
  - Implement `code/analysis.py::quadratic_loocv` that fits a · ρ² + b·ρ + c to the mean exact‑match accuracies of the five fixed ratios, using leave‑one‑ratio‑out cross‑validation.  
  - Compute the cross‑validated peak density (ρ maximizing the fitted curve) and obtain a 95 % bootstrap CI by resampling seeds.  
  - Write `quadratic_coefficients` (array `[a, b, c]`) and `peak_density` (float) into `statistical_result.json`; store full bootstrap results in `data/results/statistics/details/quadratic_fit.json`.  
  - **Verification**: The JSON contains a three‑element coefficient array, `peak_density` within `[0,1]`, and the detail file lists the CI bounds.  

- [ ] T011 [US3] **Sensitivity sweep around the peak density (±0.05, ±0.1)**  
  - For each offset (−0.1, −0.05, +0.05, +0.1) compute the clamped density ρ′ = clip(peak + offset, 0, 1).  
  - Run the fixed‑density trainer for the five seeds at each ρ′, reusing any existing run from T005 when the exact (ρ,seed) pair already exists.  
  - Calculate the mean accuracy change per 0.01 density relative to the peak for each offset; store the four values under `sensitivity_slopes` in `statistical_result.json`.  
  - Detailed per‑seed slopes and standard deviations go to `data/results/statistics/details/sensitivity_analysis.json`.  
  - **Verification**: All four slope entries are real numbers derived from actual training runs (not from the fitted curve); the detail file matches the consolidated values; JSON validates.  

- [ ] T012 [US3] **Generate tables and figures from validated artifacts**  
  - Produce PNG figures:  
    - `figures/accuracy_vs_rho.png` (per‑seed points, LOOCV quadratic fit with CI, peak marker).  
    - `figures/rho_over_time.png` (density time‑series for each adaptive seed).  
    - `figures/loss_curves.png` (average loss trajectories for fixed and adaptive runs).  
    - `figures/entropy_error_scatter.png` (entropy vs. error scatter with regression line).  
  - Create `data/results/summary_table.csv` aggregating final accuracies, F1 scores, t‑test outcomes, peak density, and sensitivity slopes; each cell is programmatically read from the JSON artifacts.  
  - **Verification**: All PNG files open without error; the CSV contains no hand‑typed numbers (checked by a script that cross‑references source JSON paths).  

---

## Phase 4 – Reproducibility, contract validation, and paper hand‑off  

- [ ] T013 [US3] **Contract tests for all output artifacts**  
  - Add `code/tests/test_contracts.py` that iterates over every JSON file under `data/results/` and validates against the appropriate schema (`training_result.schema.yaml` or `statistical_result.schema.yaml`).  
  - Include cross‑artifact consistency checks (e.g., the summary CSV matches the aggregated JSON values).  
  - **Verification**: `pytest code/tests/test_contracts.py -q` exits with 0 failures.  

- [ ] T014 [US3] **Methods/results documentation, suite‑runtime aggregation, and paper‑stage hand‑off**  
  - Write `docs/results.md` summarizing:  
    - Model substitution rationale (discrete diffusion, ≤100 M parameters) and sample‑size limitations.  
    - Fixed‑baseline and adaptive findings (p‑values, peak density, sensitivity slopes, entropy‑error correlation).  
    - Power limitation (5 seeds vs. planned 10) and its impact.  
    - Paths to all figures, tables, and JSON artifacts.  
  - Compute total wall‑clock time across all runs (sum of `runtime_seconds` plus orchestration overhead) and store in `data/results/suite_runtime.json`.  
  - Provide reproducibility instructions: running the thin path (`configs/quickstart.yaml`) and the full suite (`configs/full_suite.yaml`).  
  - State the paper‑stage hand‑off (figures, tables, statistical results) and any remaining limitations.  
  - **Verification**: The documentation renders without broken links; `suite_runtime.json` contains a numeric `total_seconds`; the final CI log prints “Pipeline completed successfully, all artifacts validated”.  

---  

### Dependency Mapping (summary)

| FR / US / SC | Satisfied by Task(s) |
|--------------|----------------------|
| FR‑001 (dataset download) | T002, T004‑T007, T008 |
| FR‑002 (real ≤100 M discrete diffusion model) | T003 |
| FR‑003 (fixed‑density training) | T004, T005 |
| FR‑004 (adaptive scheduler) | T006, T007 |
| FR‑005 (6 h timeout) | T004‑T007 |
| FR‑006 (paired t‑test) | T009 |
| FR‑007 (sensitivity analysis) | T011 |
| FR‑008 / FR‑011 (quadratic LOOCV + CI) | T010 |
| FR‑009 (≥5 seeds) | T005, T007, T011 |
| FR‑010 (entropy–error correlation) | T008 |
| FR‑012 (exact‑match & token‑F1) | T004‑T007 |
| US‑1 (fixed‑density baseline) | T001‑T005 |
| US‑2 (adaptive scheduler) | T006‑T008 |
| US‑3 (statistical validation) | T009‑T014 |
| SC‑1 – SC‑7 (measurement & reporting) | T005‑T014 |

All tasks respect the platform’s directory conventions (`code/`, `data/`, `figures/`, `docs/`, `outputs/`) and never modify platform state files.  

---  

*All unchecked tasks are pending implementation; checked tasks (none at present) would indicate completed work that already satisfies its verification criteria.*  
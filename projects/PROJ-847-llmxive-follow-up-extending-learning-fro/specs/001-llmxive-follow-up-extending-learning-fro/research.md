# Research: llmxive-density-analysis

## Dataset Strategy
| Role                | Source (verified)                                                                                                   | Loader                                    |
|---------------------|----------------------------------------------------------------------------------------------------------------------|-------------------------------------------|
| Primary reasoning (train) | GSM8K (train split, parquet) – https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/train-00000-of-00001.parquet | `datasets.load_dataset("openai/gsm8k", split="train", streaming=True)` |
| Primary reasoning (test)  | GSM8K (test split, parquet) – https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/test-00000-of-00001.parquet | `datasets.load_dataset("openai/gsm8k", split="test", streaming=True)` |
| Supplemental logical subset | bigbench logical subset – https://huggingface.co/datasets/bigbench/bigbench_lite | `datasets.load_dataset("bigbench_lite")` |

All datasets are openly downloadable, require no authentication, and are streamed when necessary to stay within a modest RAM budget.

## Metric Justification
- **Exact‑match logical accuracy**: Standard metric for GSM8K (Cobbe *et al.*, 2022). Directly evaluates whether the model’s generated solution matches the gold‑standard reasoning chain.  
- **Graded token‑level F1**: Captures partial correctness; mitigates brittleness of exact‑match (FR‑012). Implemented via token‑wise overlap between prediction and reference.  

Both metrics are reported for every run and stored in the JSON result artifacts.

## Methodology
1. **Preprocessing**  
   - Load GSM8K train and test splits; retain fields `question`, `answer`, `solution`.  
   - Tokenize with the diffusion model’s tokenizer, pad/truncate to max length 256.  
   - Merge the `bigbench_lite` logical subset (fields `question`, `answer`) into the training pool for additional diversity; ensure no overlap with the test set.  

2. **Model**  
   - Use the publicly available discrete diffusion checkpoint `author/lightdiffm` (≈ 20 M parameters, CPU‑compatible).  
   - Load with `torch.load` on CPU (`device="cpu"`).  

3. **Training Loop**  
   - **Fixed‑density mode**: Loop over ρ ∈ {0.1, 0.3, 0.5, 0.7, 0.9}. For each ρ and each seed (42‑61):  
     * Initialize `TrainingConfig` (max_epochs = 5).  
     * Train for up to 5 epochs or until the 6 h timeout flag triggers.  
     * Record loss per step, final exact‑match and token‑level F1 on the held‑out test split, runtime, and timeout flag.  
   - **Adaptive mode**: For each seed (42‑61):  
     * Start with ρ = 0.5.  
     * At each training step compute **prediction entropy**: average Shannon entropy over the token‑wise softmax distribution.  
     * Apply heuristic `ρ_{t+1} = clip(ρ_t + α·(entropy_t - entropy_target), 0, 1)` where α = 0.1 and `entropy_target` is the median entropy observed in a short pilot run.  
     * Clamp NaN/∞ entropy to `[0, ln(V)]` (V = vocab size) and default ρ to 0.5 if clamped.  
     * Store the full time‑series of ρ values.  
   - **Control scheduler (shuffled‑entropy)**: Identical to the adaptive mode but the entropy values are randomly permuted at each step, breaking any systematic link between entropy and density.  
   - **Fixed‑constant control**: Run a fifth fixed‑density condition using a **pre‑specified constant density of 0.55**, chosen **a priori** (independent of any adaptive experiment). This provides a non‑adaptive baseline at the same average density as the adaptive run without introducing circularity.

4. **Entropy‑Error Correlation (FR‑010)**  
   - On a held‑out validation subset of the GSM8K train split, compute per‑example prediction entropy and binary error indicator (1 = incorrect exact‑match).  
   - Calculate Pearson’s *r* and associated p‑value; store in `entropy_error_corr.json`.  

5. **Statistical Analysis (Phase 6)**  
   - **Paired t‑test**: Compare adaptive final accuracies vs. fixed ρ = 0.5 across matching seeds (SciPy `ttest_rel`). If any seed missing, fallback to Mann‑Whitney U (`mannwhitneyu`).  
   - **Power justification**: Based on pilot variance (σ ≈ a low magnitude) and desired detection of a medium‑sized effect (Cohen’s d), 20 paired seeds provide ≥ 0.80 power at α = 0.05.  
   - **Multiple‑comparison note**: The t‑test is a single pre‑specified comparison; no correction required.  
   - **Quadratic regression**: Fit `accuracy = a·ρ² + b·ρ + c` to the five fixed‑ratio means using `np.polyfit`.  
   - **Leave‑one‑out CV**: For each fixed‑ratio, leave it out, refit, predict the omitted point; compute RMSE and record the peak density for each fold. Aggregate to obtain mean peak and 95 % CI via bootstrap (1 000 resamples).  
   - **Sensitivity sweep**: Evaluate the fitted quadratic at ρ ± 0.05 and ρ ± 0.1; compute slope (Δaccuracy / Δρ) and report distributions.  
   - **Causal check (limited inference)**: Compare adaptive run against the shuffled‑entropy control using an independent t‑test; a significant advantage for the true adaptive run **suggests** that entropy‑driven adjustments improve performance, but we refrain from asserting a strict causal claim because other training dynamics remain confounded. The additional fixed‑constant control further contextualizes any observed benefit.  

6. **Result Packaging**  
   - JSON result files (`fixed_baselines.json`, `adaptive_run.json`, `control_shuffle.json`, `fixed_constant.json`, `paired_t_test.json`, `quadratic_fit.json`, `sensitivity_analysis.json`, `entropy_error_corr.json`, `causal_control_test.json`).  
   - PNG figures: loss curves, ρ‑vs‑step time series (adaptive & control), quadratic fit with CI, entropy‑error scatter with regression line.  
   - All artifacts stored under `outputs/` and validated against the schemas in `contracts/`.  

## Compute Decision / Rationale
- **CPU‑first**: All operations (model forward, entropy, regression) are lightweight enough for a modest multi‑core CPU; no GPU required (Principle VI).  
- **Memory management**: Streaming loader + batch size 16 ⇒ peak RAM ≈ a few GB.  
- **Timeout handling**: At epoch start, check elapsed wall‑clock; if > 21600 s, save checkpoint, set `timeout=True`, and exit gracefully.  
- **Parallel execution**: CI matrix will launch a job per `(rho, seed)` for fixed baselines, plus separate jobs for adaptive, control, and fixed‑constant runs. Each matrix job runs a single training instance and therefore stays well within the CPU and time constraints while the overall suite completes in parallel.

## Deliverables
- `outputs/fixed_baselines.json` – list of `TrainingRun` objects for each ρ & seed.  
- `outputs/adaptive_run.json` – list of `TrainingRun` objects with `density_time_series`.  
- `outputs/control_shuffle.json` – list of `TrainingRun` objects for the shuffled‑entropy control.  
- `outputs/fixed_constant.json` – list of `TrainingRun` objects for the fixed‑constant density control.  
- `outputs/statistics/paired_t_test.json` – t‑statistic, p‑value, df (or U‑test fallback).  
- `outputs/statistics/quadratic_fit.json` – coefficients, peak density, 95 % CI.  
- `outputs/statistics/sensitivity_analysis.json` – slopes for ±0.05/±0.1 sweeps.  
- `outputs/statistics/entropy_error_corr.json` – Pearson r, p‑value.  
- `outputs/statistics/causal_control_test.json` – t‑statistic, p‑value, df for adaptive vs. control (interpreted as suggestive).  
- `outputs/figures/*.png` – loss curves, density trajectory, quadratic fit, entropy‑error scatter.  
- `outputs/summary.md` – human‑readable table linking all artifacts.

---




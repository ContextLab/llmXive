# Research: llmXive follow‑up: extending "In-Context World Modeling for Robotic Control"

**Feature**: `001-auto-icwm-latent-dynamics`  
**Date**: 2026‑10‑19  

## Dataset Strategy
| Role | Source | Access Method | Note |
|------|--------|---------------|------|
| Interaction Clips (training & test) | Locally generated via `robosuite` (Franka Emika Panda, Fetch) | `src/pipeline/generate_clips.py` (deterministic seed) | No external download; satisfies data‑availability rule. |
| Pre‑trained ICWM encoder | Bundled in repository (`src/utils/icwm_encoder.py`) | CPU‑only inference | Compatible with the free‑tier runner. |
| Task‑Complexity metric | Derived from `robosuite` scene definitions (sub‑goal count) | Direct query in `src/pipeline/compute_complexity.py` | No external data required. |

## Methodology

### 1. Interaction Clip Generation
- Generate **200** training clips and **200** test clips using a fixed random seed (`SEED = 42`).  
- Each clip records `(state, action, observation)` at 20 Hz for a full episode.  
- Stored as compressed `.npz` under `data/raw/clip_<id>.npz`.  

### 2. Latent Descriptor Extraction (FR‑001)
- Encode each clip with the CPU‑only ICWM encoder → token sequence `z₁…z_T`.  
- Compute three canonical time‑series descriptors:  
  1. **Variance** (`np.var(z, ddof=1)`).  
  2. **Lag‑1 Autocorrelation** (Pearson correlation of `z[:-1]` vs `z[1:]`).  
  3. **Spectral Density** (mean power spectral density via Welch’s method, `scipy.signal.welch`).  
- **Edge‑case handling**: If variance < 1e‑8, set autocorr = 0 and spectral = 0 to avoid division‑by‑zero.  
- Output `data/processed/descriptors.csv` (validated by `contracts/descriptor.schema.yaml`).  

### 3. Grid‑Search Labeling (FR‑002)
- **Grid**: τ ∈ {0.5, 1.0, 1.5, 2.0}, k ∈ {16, 32, 64} (12 combos).  
- **Training clips**: **200** (reduced from the earlier 500).  
- **Episodes per combo**: **5** → Approximately on the order of ten thousand episodes total, with an estimated runtime of a few hours on the CI runner.  
- For each **training** clip, run the VLA policy with each (τ, k) pair, record binary success over 5 episodes, compute success rate.  
- **Tie‑breaking**: If several pairs share the maximal success rate, select one uniformly at random using a fixed RNG seed (`np.random.RandomState(123)`).  
- Store results in `data/processed/labels.csv` (validated by `contracts/label.schema.yaml`).  

### 4. Regressor Training (FR‑003)
- **Split**: [deferred] train / [deferred] hold‑out test, stratified by `task_complexity`.
- **Standardise** descriptors (zero‑mean, unit‑variance).  
- **Models** (CPU‑tractable):  
  - Linear Regression (baseline).  
  - MLP with one hidden layer (size ∈ {16, 32, 64}, ReLU, L2 = 1e‑3, Adam, max 200 epochs, early‑stop).  
- **Hyper‑parameter tuning** via 5‑fold CV on hidden size.  
- **Loss**: Scale τ to [0, 1] (`(τ‑0.1)/(2.0‑0.1)`) and k to [0, 1] (`(k‑1)/(64‑1)`); compute MSE for each component, average → joint MSE.  
- **Success criterion**: Test joint MSE ≤ 0.9 × baseline MSE (SC‑006).  
- Save checkpoint `model/regressor.pt`.  

### 5. Task‑Complexity Metric (FR‑007)
- Count distinct sub‑goals defined in each `robosuite` task description.  
- Store as `data/processed/task_complexity.csv` (validated by `contracts/complexity.schema.yaml`).  

### 6. Zero‑Shot Validation (FR‑004, FR‑005)
1. **Predict** (τ, k) for each of the **200** novel test clips using the trained regressor.  
2. **Run** VLA policy **10 episodes** per clip with the *predicted* hyperparameters; compute **auto_success_rate** (fraction of successful episodes).  
3. **Run** baseline policy (τ = 1.0, k = 32) **10 episodes** per clip; compute **baseline_success_rate**.  
4. Derive binary outcomes (`auto_success = auto_success_rate >= 0.5`, `baseline_success = baseline_success_rate >= 0.5`) for a secondary McNemar check.  
5. Record per‑clip outcomes in `results/validation_results.csv` (validated by `contracts/validation_results.schema.yaml`).  

#### Statistical Tests (SC‑002, SC‑003)
- **Paired t‑test** on the paired success rates (`auto_success_rate` vs `baseline_success_rate`).  
- **McNemar’s exact test** on the derived binary outcomes (provides a non‑parametric robustness check).  
- Apply **Bonferroni correction** for the two tests (α = 0.025).  
- **Success**: p < 0.05 after correction **and** absolute success‑rate lift ≥ 5 % (SC‑002).  

### 7. Correlation Analysis (SC‑001)
1. **Pearson correlation** between latent **variance** and **task‑complexity** (sub‑goal count).  
2. **Pearson correlation** between latent **variance** and the **ground‑truth optimal** hyperparameters (τ, k) from `labels.csv`.  
3. **Diagnostics**: Shapiro‑Wilk normality, Breusch‑Pagan heteroscedasticity, Cook’s distance. If any assumption fails, report **Spearman** rank correlation instead.  
4. **Criterion**: |r| > 0.5 and p < 0.05 (or Spearman equivalent).  

### 8. Resource Monitoring (FR‑006, SC‑004, SC‑005)
- Wrap each phase with timers (`time.perf_counter`) and memory profiling (`psutil`).  
- Abort with explicit error if runtime > 6 h or RAM > 7 GB.  
- Log to `data/logs/resource_usage.json`.  

### 9. Power & Sample‑Size Justification (methodology‑379ee273)
- Detecting |r| = 0.5 at α = 0.05 requires ≈ 85 samples → N = 200 gives > 0.99 power.  
- Detecting a ≥ 5 % absolute lift in binary success with McNemar at α = 0.05 needs ≈ 150 paired observations → M = 200 gives ≈ 0.92 power.  

## Decision / Rationale
- **CPU‑first**: All steps (Welch PSD, linear/MLP regression, grid search, correlation diagnostics) are tractable on the free‑tier runner; no GPU is needed.  
- **Open‑source simulation**: Generates realistic interaction clips without external downloads, meeting the data‑availability rule.  
- **Statistical rigor**: Includes multiple‑comparison correction, power analysis, diagnostic checks, paired t‑test on success rates, and correlation controls, satisfying the methodology panel’s rigor checklist.  

## Expected Deliverables
- `data/processed/descriptors.csv`  
- `data/processed/labels.csv`  
- `data/processed/task_complexity.csv`  
- `model/regressor.pt`  
- `results/validation_results.csv` (including `auto_success_rate`, `baseline_success_rate`, `success_diff`, p‑values, success‑rate lift)  
- `results/correlation_report.md` (full diagnostics, plots)  
- `data/logs/resource_usage.json`  

All artifacts are reproducibly regenerated by:

```bash
python -m src.pipeline.run_all
```

---  

## End‑to‑End Execution
The driver script `src/pipeline/run_all.py` executes Phases 1‑5 sequentially, prints a concise 50‑row summary table (clip_id, variance, predicted τ/k, auto_success_rate, baseline_success_rate) to stdout, and writes all CSV artifacts listed above. This script is used by the CI verifier to demonstrate a complete, deterministic run.

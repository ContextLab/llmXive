# Research: llmXive follow‑up: extending "In-Context World Modeling for Robotic Control"

**Feature**: `001-auto-icwm-latent-dynamics`  
**Date**: 2026‑10‑14  

## Dataset Strategy
| Role | Source | Access Method | Note |
|------|--------|---------------|------|
| Interaction Clips (training & test) | Locally generated via `robosuite` (Franka Emika Panda, Fetch) | `src/pipeline/generate_clips.py` (deterministic seed) | No external download; satisfies data‑availability rule. |
| Pre‑trained ICWM encoder | Bundled in repository (`src/utils/icwm_encoder.py`) | CPU‑only inference | Compatible with free‑tier runner. |
| Task‑Complexity metric | Derived from simulation metadata (sub‑goal count) | Direct query of `robosuite` scene definition | No external data. |

## Methodology

### 1. Interaction Clip Generation
- Generate **N = 500** training clips and **M = 200** test clips (fixed seed).  
- Each clip records `(state, action, observation)` at 20 Hz for a full episode.  
- Stored as compressed `.npz` under `data/raw/`.

### 2. Latent Descriptor Extraction (FR‑001)
- Encode each clip with the CPU‑only ICWM encoder → token sequence `z₁…z_T`.  
- Compute:
  - **Variance**: `np.var(z, ddof=1)`.
  - **Lag‑1 Autocorrelation**: Pearson correlation between `z[:-1]` and `z[1:]`.
  - **Spectral Density**: Mean power spectral density via Welch’s method (`scipy.signal.welch`), averaged across token dimensions.  
- **Justification** (addresses methodology‑578529b3): Variance captures amplitude, lag‑1 autocorrelation captures temporal dependency, and spectral density captures frequency‑domain energy—standard, validated time‑series descriptors (Welch 1967; Box & Jenkins 1976).  
- **Construct‑Validity Extension** (addresses methodology‑29cd71af): In addition to the three primary descriptors we will compute **entropy**, **Lyapunov exponent**, and **token‑level mutual information** on a subset of clips for an ablation study. These additional measures will be reported but are not required for the primary hypothesis.  
- Edge‑case handling: If variance ≈ 0, set autocorr = 0 and spectral density = 0 to avoid division‑by‑zero.  
- Output: `data/processed/descriptors.csv` (validated by `contracts/descriptor.schema.yaml`).

### 3. Grid‑Search for Optimal Hyperparameters (FR‑002)
- Hyperparameter grid: τ ∈ {0.5, 1.0, 1.5, 2.0}, k ∈ {16, 32, 64}.  
- For each **training** configuration:
  - Run the VLA policy with each (τ, k) pair on the associated clips.  
  - Record binary success per episode; compute success rate.  
  - **Tie‑breaking** (methodology‑f31d3f95): If multiple pairs tie for maximal success, select one uniformly at random using a fixed seed (`np.random.seed(123)`).  
- Store labels in `data/processed/labels.csv` (validated by `contracts/label.schema.yaml`).

### 4. Regressor Training (FR‑003)
- Split training data into train/hold‑out test (stratified by task‑complexity).  
- **Feature Scaling**: Standardise variance, autocorr, and spectral density (zero‑mean, unit‑variance).  
- Models (CPU‑tractable):
  - **Linear Regression** (baseline).  
  - **MLP** with one hidden layer (≤ 64 units, ReLU, L2 = 1e‑3).  
- Hyperparameter tuning via 5‑fold CV on the training split (hidden size ∈ {16, 32, 64}).  
- **Baseline MSE Definition** (addresses methodology‑1b7a7b9b):  
  - Scale τ to [0, 1] by `(τ‑0.1)/(2.0‑0.1)` and k to [0, 1] by `(k‑1)/(64‑1)`.  
  - Compute MSE for each component separately, then average the two values → joint MSE.  
- Evaluate MSE on hold‑out test set.  
- **Success Criterion**: Test MSE ≤ 0.9 × baseline MSE (SC‑006).  
- Model checkpoint saved as `model/regressor.pt`.

### 5. Task‑Complexity Metric (FR‑007)
- Count distinct sub‑goals defined in each `robosuite` task description.  
- Store as `data/processed/task_complexity.csv` (validated by `contracts/complexity.schema.yaml`).  

### 6. Zero‑Shot Validation (FR‑004, FR‑005)
- Apply trained regressor to **novel** test clips (M = 200).  
- Run VLA policy with predicted (τ, k) and record binary success.  
- Also run fixed baseline (τ = 1.0, k = 32).  
- Produce `results/validation_results.csv` (validated by `contracts/validation_results.schema.yaml`).

#### Statistical Tests (SC‑002, SC‑003)
- **McNemar exact test** for paired binary outcomes (Auto‑ICWM vs baseline).  
- **Wilcoxon signed‑rank test** as non‑parametric complement.  
- Apply **Bonferroni correction** for the two tests (α = 0.025).  

#### Correlation Analysis (SC‑001) (addresses methodology‑4a9d7bba & methodology‑1954846e)
- Compute **Pearson correlation** between latent variance and task‑complexity.  
- Perform **partial correlation** controlling for task‑complexity when relating variance (and other descriptors) to hyperparameter performance, using `statsmodels.stats.partial_corr`.  
- **Diagnostic Checks**:  
  - Shapiro‑Wilk test for normality of residuals.  
  - Breusch‑Pagan test for heteroscedasticity.  
  - Cook’s distance to identify influential points.  
- If any assumption fails, report **Spearman rank correlation** as a robustness alternative.  
- Requirement: |r| > 0.5 and p < 0.05 (or Spearman equivalent).  

### 7. Resource Monitoring (FR‑006, SC‑004, SC‑005)
- Timer (`time.perf_counter`) and memory profiler (`psutil`) wrap each stage.  
- Abort with clear error if runtime > 6 h or RAM > 7 GB.  
- Log to `data/logs/resource_usage.json`.

### 8. Power & Sample‑Size Justification (methodology‑379ee273)
- Detecting |r| = 0.5 at α = 0.05 needs ≈ 85 samples → N = 500 gives > 0.99 power.  
- Detecting an absolute lift in binary success with McNemar at α = 0.05 needs ≈ 150 pairs → M = 200 gives ≈ 0.92 power.

## Decision / Rationale
- **CPU‑first**: All algorithms (Welch PSD, linear/MLP regression, grid search over ≤ 12 combos, correlation diagnostics) run comfortably on the free‑tier runner.  
- **Open‑source simulation**: Generates realistic interaction clips without external data download, meeting the data‑availability rule.  
- **Statistical rigor**: Partial correlation, diagnostic checks, Bonferroni correction, explicit power analysis, and stratified sampling ensure robust inference.

## Expected Deliverables
- `data/processed/descriptors.csv`  
- `data/processed/labels.csv`  
- Trained model checkpoint `model/regressor.pt`  
- `results/validation_results.csv` (including success rates, p‑values, correlation)  
- `results/correlation_report.md` (full diagnostics, plots)  
- `data/logs/resource_usage.json`  

All artifacts are reproducibly regenerated by:

```bash
python -m src.pipeline.run_all
```

---


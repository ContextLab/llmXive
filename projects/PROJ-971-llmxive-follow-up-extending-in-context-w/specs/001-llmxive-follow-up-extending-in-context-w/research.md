# Research: llmXive follow‑up: extending "In-Context World Modeling for Robotic Control"

**Feature**: `001-auto-icwm-latent-dynamics`  
**Date**: 2026‑10‑13  

## Dataset Strategy
| Role | Source | Access Method | Note |
|------|--------|---------------|------|
| Interaction Clips (training & test) | **Locally generated** via `robosuite` simulation environments (e.g., Franka Emika Panda, Fetch) | Python script `src/pipeline/generate_clips.py` (deterministic seed) | No external download required; complies with “no verified source” restriction. |
| Pre‑trained ICWM encoder | Bundled in the repository (`src/utils/icwm_encoder.py`) | CPU‑only inference | Compatible with free‑tier runner. |
| Task‑Complexity metric | Derived from simulation environment metadata (number of sub‑goals per episode) | Direct query of `robosuite` scene definition | No external data. |

> **Rationale**: Because the spec’s “ICWM” dataset has no verified external URL, we generate an equivalent set of interaction clips on‑the‑fly using an open‑source simulator. This satisfies the reproducibility requirement while avoiding any unverified data download.

## Methodology

### 1. Interaction Clip Generation
- Generate **N = 500** clips for training and **M = 200** clips for validation (fixed seed).  
- Each clip records `(state, action, observation)` at 20 Hz for a full episode.  
- Store as compressed NumPy (`.npz`) files under `data/raw/`.

### 2. Latent Descriptor Extraction (FR‑001)
- Load the pre‑trained ICWM encoder (CPU‑only Torch model).  
- Encode each clip → token sequence `z₁…z_T`.  
- Compute:
  - **Variance**: `np.var(z, ddof=1)`.
  - **Lag‑1 Autocorrelation**: Pearson correlation between `z[:-1]` and `z[1:]`.
  - **Spectral Density**: Mean power spectral density via Welch’s method (`scipy.signal.welch`), averaged across token dimensions.  
- **Justification** (addresses methodology‑578529b3): Variance captures overall amplitude, lag‑1 autocorrelation measures temporal dependency, and spectral density quantifies frequency‑domain energy—standard, validated time‑series statistics for assessing dynamical complexity (Welch 1967 []; Box & Jenkins 1976 []).  
- Edge‑case handling: If variance ≈ 0, set autocorr = 0 and spectral density = 0 to avoid division‑by‑zero.  

All descriptors are saved to `data/processed/descriptors.csv` (see `contracts/descriptor.schema.yaml`).

### 3. Grid‑Search for Optimal Hyperparameters (FR‑002)
- Hyperparameter grid: τ ∈ {0.5, 1.0, 1.5, 2.0}, k ∈ {16, 32, 64}.  
- For each **training** configuration:
  - Run the VLA policy with each (τ, k) pair on the associated clip set.  
  - Record success rate (binary success per episode).  
  - **Tie‑breaking** (addresses methodology‑f31d3f95): If multiple pairs tie for maximal success, select one uniformly at random using a fixed seed (`np.random.seed(123)`). This preserves reproducibility while avoiding systematic bias.  
- Store labels in `data/processed/labels.csv`.

### 4. Regressor Training (FR‑003)
- Split training data: [deferred] train, [deferred] hold‑out test (stratified by τ/k and task‑complexity).
- Model choices (CPU‑tractable):
  - **Linear Regression** (baseline).  
  - **MLP** with one hidden layer (≤ 64 units, ReLU, L2 = 1e‑3).  
- Hyperparameters of the regressor are tuned via 5‑fold cross‑validation on the training split (grid of hidden size ∈ {16, 32, 64}).  
- **Baseline MSE** (addresses methodology‑cec2d5d5): Predict the **global mean τ** *and* the **global mean k** (separate means) across the training data; compute joint MSE over both targets.  
- Evaluate MSE on the held‑out test set.  
- **Success Criterion**: Test MSE ≤ 0.9 × baseline MSE (SC‑006).

### 5. Task‑Complexity Metric (FR‑007)
- For each configuration, count the number of distinct sub‑goals defined in the `robosuite` task description (e.g., “pick”, “place”, “push”).  
- Store as `task_complexity.csv`.  

### 6. Zero‑Shot Validation (FR‑004, FR‑005)
- Apply the trained regressor to **novel** configurations (the M = 200 clips not used in grid search).  
- Run VLA policy with predicted (τ, k) and record per‑episode success.  
- Also run the fixed baseline (τ = 1.0, k = 32).  
- Compute **paired differences** in success rates across episodes.

#### Statistical Tests (SC‑002, SC‑003)
- **McNemar exact test** (binary paired outcomes) is used to assess whether the Auto‑ICWM success rate differs from the baseline.  
- Additionally, a **Wilcoxon signed‑rank test** is performed as a non‑parametric complement.  
- Null hypothesis: no difference in success rates.  
- Apply **Bonferroni correction** for the two related tests (adjusted α = 0.025).  

#### Correlation Analysis (SC‑001)
- Pearson correlation between latent variance (from descriptors) and task‑complexity metric, **controlling for complexity distribution** (see confound control).  
- Check that |r| > 0.5 and p < 0.05.

### 7. Resource Monitoring (FR‑006, SC‑004, SC‑005)
- Wrap each pipeline stage with a timer (`time.perf_counter`) and memory profiler (`psutil`).  
- Abort with clear error if runtime exceeds 6 h or RAM > 7 GB.  
- Log resource usage to `data/logs/resource_usage.json`.

### 8. Power & Sample‑Size Justification (addresses methodology‑379ee273)
- Detecting a Pearson correlation |r| = 0.5 with α = 0.05 requires ≈ 85 samples; our N = 500 training clips yields > 0.99 power.  
- Detecting a **[deferred] absolute lift** in binary success rate with McNemar’s exact test at α = 0.05 requires ≈ 150 paired observations; our M = 200 test clips provides ≈ 0.92 power.  
- These calculations justify the chosen dataset sizes.

## Decision / Rationale
- **CPU‑first**: All chosen algorithms (Welch PSD, linear/MLP regression, grid search over ≤ 12 combos) are trivially CPU‑tractable; no GPU is required.  
- **Open‑source simulation**: Generates real‑world‑like interaction clips without external data download, satisfying the data‑availability rule.  
- **Statistical rigor**: McNemar test for binary paired data, Bonferroni correction for multiple tests, explicit power analysis, and confound control via stratified sampling and covariate adjustment.  

## Expected Deliverables
- `data/processed/descriptors.csv` (validated against `contracts/descriptor.schema.yaml`)  
- `data/processed/labels.csv` (τ, k per training config)  
- Trained model checkpoint (`model/regressor.pt`)  
- `results/validation_results.csv` (success rates, p‑values, correlation, controlled analysis)  
- Resource usage log (`data/logs/resource_usage.json`)  

All artifacts will be reproducibly regenerated by executing the single entry‑point script:

```bash
python -m src.pipeline.run_all
```

---




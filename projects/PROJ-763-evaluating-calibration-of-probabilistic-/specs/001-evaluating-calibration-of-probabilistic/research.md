# Research: Evaluating Calibration of Probabilistic Weather Forecasts

## Summary

This research investigates methods to recalibrate probabilistic weather forecasts, specifically addressing systematic mis-calibration in the SubseasonalRodeo dataset (or a verified alternative). The study compares a non-parametric baseline (Isotonic Regression) against a parametric, hierarchical approach (Bayesian Logistic Regression) that leverages lead-time correlations.

**Data Availability Note**: The "SubseasonalRodeo" dataset is currently **not** listed in the project's "Verified datasets" block. The pipeline is designed to halt immediately if a verified source cannot be found. If a verified alternative (e.g., NOAA parquet) is available and contains the required `probability_value` fields, it will be used. Otherwise, the project cannot proceed.

## Dataset Strategy

The primary data source is the **SubseasonalRodeo** dataset, *subject to verification*.

| Dataset Name | Source Type | Verified URL | Usage Notes |
| :--- | :--- | :--- | :--- |
| **SubseasonalRodeo** | Public Archive | **NO verified source found** | **BLOCKED**: No URL in the "Verified datasets" block. The pipeline will halt with "Data Source Not Verified" unless a verified URL is provided or an alternative is selected. |
| **NOAA (parquet)** | HuggingFace | `https://huggingface.co/datasets/Qdrant/NOAA-Buoy/resolve/main/full_2023_remove_flawed.parquet` | **Verified Alternative**: If SubseasonalRodeo is unavailable, this dataset will be checked for `probability_value` fields. If present, it will be used as a fallback. |
| **GFS (zip)** | HuggingFace | `https://huggingface.co/datasets/jacobbieker/gfs-kerchunk/resolve/main/data/2021/2021022712.zip` | *Not used for this specific feature unless it contains the required probability fields.* |

**Critical Constraint**: The plan relies **ONLY** on datasets with verified URLs. No unverified `wget` commands will be executed.

## Methodology & Statistical Rigor

### 1. Baseline Metrics (FR-003)
- **Brier Score**: Computed for binary events (e.g., precipitation > 1mm) at each lead time.
- **CRPS**: Continuous Ranked Probability Score for continuous variables (temperature).
- **Reliability Diagrams**: Kernel-smoothed plots of forecast probability vs. observed frequency.
- **PIT Histograms**: Probability Integral Transform to check uniformity of forecast CDFs.

### 2. Isotonic Recalibration (FR-004)
- **Method**: Pool Adjacent Violators Algorithm (PAVA).
- **Validation Strategy**: **Blocked Temporal Split**. Train on full historical years (e.g., the five-year period prior to the test set), Test on the final full year (2022). This prevents data leakage and respects seasonal cycles.
- **Sensitivity**: Runs repeated with varying temporal splits (maintaining the temporal boundary logic) to ensure stability against non-stationarity.
- **Constraint**: Minimum sample size threshold enforced to prevent overfitting on sparse lead times.

### 3. Bayesian Hierarchical Recalibration (FR-005)
- **Model**: Logistic regression with a hierarchical prior on coefficients to share information across lead times.
- **Prior Structure**:
  - **Physics-Informed**: `beta_lead ~ Normal(0, sigma_decay)` where `sigma_decay` decreases with lead time.
  - **Control**: **Flat Prior** (Weakly Informative) model without decay assumptions to serve as a baseline and decouple prior influence from data signal.
- **Inference**: MCMC (NUTS sampler).
- **Configuration**: **4 chains** (mandatory for all runs, including sensitivity and control models), **minimum 2000 draws** (to ensure stable R-hat and ESS).
- **Convergence Criteria**: R-hat ≤ 1.05 AND Effective Sample Size (ESS) > 200 per parameter.
- **Dynamic Adjustment**: If ESS or R-hat targets are not met, the sampler will extend draws up to a maximum timeout.
- **Timeout/Fallback**: Hard 60-minute timeout. If exceeded or convergence fails, status = "Unconverged" or "Timeout", and results fall back to Isotonic.
- **Sensitivity**: Prior strength varied (weak, medium, strong) and compared against the Flat Prior control.

### 4. Statistical Comparison (FR-006)
- **Input Data**: Time series of **individual forecast errors** (daily/weekly loss differentials) for each lead time. **NOT** aggregated mean metrics.
- **Primary Test**: Diebold-Mariano (DM) with HAC estimators to compare loss series between methods.
- **Normality Handling**:
  - If normality assumption fails (Shapiro-Wilk, p < 0.05), **DO NOT** switch to Wilcoxon (assumes i.i.d.).
  - Instead, use a **Bootstrap** method that preserves the time-series structure to generate confidence intervals and p-values.
- **Significance**: α = 0.05.
- **Scope**: DM tests are run *within* a single fixed test set. Sensitivity splits use bootstrapped CIs for meta-analysis.

## Compute Feasibility & Escape Hatch

- **CPU-First**:
  - **Baseline & Isotonic**: `scikit-learn` and `pandas` operations are lightweight. Expected runtime < 30 mins on 2 CPU cores.
  - **Bayesian**: `pymc` can run on CPU but is slow for large datasets.
- **GPU Escape Hatch**:
  - If `pymc` detects CUDA or if the CPU run exceeds time limits, the execution stage will offload to a Kaggle GPU (16GB VRAM).
  - **Scaling**: If the full dataset is too large for GPU memory, the plan streams data or uses a representative sample (first N rows) for the Bayesian step, while retaining the full dataset for baseline/isotonic.
  - **Real Computation**: The plan uses `device="cuda"` in PyMC if available. No synthetic stand-ins.

## Statistical Considerations

- **Causal Inference**: The study is observational. Claims are limited to "associational improvements in calibration" for the specific model, not causal claims about weather physics.
- **Collinearity**: Predictors (lead times) are correlated. The hierarchical model explicitly models this correlation structure rather than treating them as independent.
- **Power**: Sample size is determined by the dataset size. If a specific lead time has < 100 samples, the system flags this as a power limitation and may skip that lead time or use the raw forecast.
- **Prior Dominance**: The inclusion of a "Flat Prior" control ensures that any improvement claimed by the physics-informed prior is empirical and not a tautology of the prior specification.

## Decision Rationale

- **Why Isotonic First?** Non-parametric, robust, and fast. Establishes a strong baseline for the more complex Bayesian method.
- **Why Bayesian?** To address data sparsity in rare events (e.g., heavy rain) by borrowing strength across lead times.
- **Why 4 Chains?** R-hat convergence diagnostics require multiple chains to be meaningful. 2 chains are insufficient for robust R-hat estimation.
- **Why Minimum 2000 Draws?** To ensure stable R-hat and ESS for the hierarchical model with structured priors; 500 draws are insufficient.
- **Why Hard Fallback?** To ensure the pipeline always produces a result (`results_bayesian.csv`) even if the complex model fails, satisfying FR-007.
- **Why Bootstrap over Wilcoxon?** Forecast errors are autocorrelated. Wilcoxon assumes i.i.d. and yields invalid p-values. Bootstrap preserves the time-series structure.
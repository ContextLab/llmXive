# Research: Evaluating Calibration of Probabilistic Weather Forecasts

## Summary
This research phase validates the feasibility of the implementation plan, focusing on dataset availability, statistical methodology, and computational constraints. It confirms that the SubseasonalRodeo dataset (or a verified substitute) contains the necessary variables (GFS ensemble probabilities, ground-truth observations) and that the chosen statistical methods (Isotonic Regression, Bayesian Hierarchical Logistic Regression) are viable within the GitHub Actions resource limits.

## Dataset Strategy

| Dataset Name | Purpose | Verified Source / Loader | Feasibility Notes |
| :--- | :--- | :--- | :--- |
| **SubseasonalRodeo** | Primary source for GFS ensemble forecasts and ground-truth observations. | **NO verified source found**. <br> *Strategy*: The plan assumes the dataset is accessible via `wget` from a canonical URL as per the spec's assumption. **If the URL fails, checksum mismatch, or schema validation fails, the pipeline will HALT with "Dataset Unavailable" or "Schema Mismatch"**. No fallback to NOAA-Buoy/GFS is permitted as they lack the required ensemble probability structure. | **Critical Risk**: The spec assumes the dataset is downloadable via `wget`. Since no verified URL exists in the provided list, the implementation must handle the "NO verified source" case by explicitly coding a **HALT** if the download fails. The plan will attempt to fetch from the assumed canonical location; if it fails, the pipeline stops. |
| **NOAA (parquet)** | Not used as fallback. | `https://huggingface.co/datasets/Qdrant/NOAA-Buoy/resolve/main/full_2023_remove_flawed.parquet` | **Rejected**: Lacks ensemble probability fields required for Brier/CRPS. Analysis is infeasible without these fields. |
| **GFS (zip)** | Not used as fallback. | `https://huggingface.co/datasets/jacobbieker/gfs-kerchunk/resolve/main/data/2021/2021022712.zip` | **Rejected**: Lacks ensemble probability fields required for Brier/CRPS. Analysis is infeasible without these fields. |
| **CRPS (jsonl)** | Reference for CRPS calculation logic (not for data). | `https://huggingface.co/datasets/PeiyangLiu/CRPS-30K/resolve/main/crps_train_30k.jsonl` | Verified source. Used for reference on CRPS implementation, not as a data source for the weather study. |

**Dataset Variable Fit Analysis**:
- **Required Variables**: `grid_id`, `lead_time`, `forecast_date`, `probability_value` (ensemble), `event_occurred` (binary observation).
- **SubseasonalRodeo**: Assumed to contain these fields based on the spec. If the dataset lacks `probability_value` for specific variables (e.g., heavy precipitation), the plan will fall back to binary occurrence data (Assumption: Variable Fit).
- **Gap Handling**: If the dataset lacks a required variable (e.g., post-task anxiety equivalent in weather, or specific lead time), the plan will explicitly state the mismatch and adjust the analysis scope (e.g., "Analysis restricted to available lead times 1-7").
- **Infeasibility**: If the primary dataset is unavailable or lacks required fields, the study is **infeasible**. The pipeline will halt and log a "Research Infeasible" status. No alternative analysis path is available. **Fallback datasets (NOAA-Buoy, GFS-kerchunk) are explicitly rejected** as they do not contain the necessary ensemble probability fields.

**Dataset Size Contingency**:
- If the downloaded dataset exceeds the available memory or disk capacity, the pipeline will automatically switch to streaming mode (processing shards one by one) or a fixed-seed random sample with a logged warning about power limitations.

## Methodological Rigor

### Statistical Framework
The study employs a frequentist framework for baseline and isotonic methods, and a Bayesian framework for the hierarchical model.
- **Baseline**: Brier Score (BS) and Continuous Ranked Probability Score (CRPS) are computed for each lead time and variable.
- **Isotonic Regression**: Non-parametric, monotonic mapping to correct bias. Fitted on [deferred] chronological data, tested on [deferred].
- **Bayesian Hierarchical Model**: Logistic regression with a structured prior for lead-time decay.
  - **Prior Structure**: The prior for the lead-time coefficient will follow an exponential decay function: `beta_lead_time ~ Normal(0, sigma * exp(-alpha * lead_time))` to respect the physics of forecast degradation (Assumption: Variable Fit).
  - **Inference**: Variational Inference (ADVI) with ≤ 500 iterations (or equivalent) for speed. If diagnostics fail, switch to GPU-accelerated MCMC.
  - **Convergence**: R-hat < 1.05 (SC-006) or ELBO convergence. If unconverged, results are flagged, and isotonic results are used as fallback.

### Statistical Rigor Checks
- **Multiple Comparisons**: When comparing multiple lead times or variables, the plan will apply a **Holm-Bonferroni** correction to the p-values of the Diebold-Mariano tests. Standard Bonferroni is rejected due to over-conservatism for time-series data.
- **Power Justification**: A **Power Analysis (T000)** will be conducted to calculate the minimum detectable effect size for rare events. If the dataset lacks sufficient power, results will be flagged as "Underpowered" rather than concluding "no improvement".
- **Causal Inference**: The study is observational. Claims are framed as "associational improvements in calibration" rather than causal claims about weather systems.
- **Collinearity**: Predictors (lead time, forecast value) are not definitionally related in a way that causes perfect collinearity. However, the hierarchical model accounts for correlations across lead times.
- **Stationarity**: A pre-test (Augmented Dickey-Fuller) will be performed on loss differentials. If non-stationarity is detected, the **Harvey-Leybourne-Newbold (HLN)** modification of the Diebold-Mariano test will be used.
- **Normality**: The Wilcoxon test is **rejected** for time-series data. Instead, a **HAC (Heteroskedasticity-and-Autocorrelation-Consistent)** variance estimator will be used within the Diebold-Mariano test framework.
- **Bootstrapping**: For sensitivity analysis, **Moving Block Bootstrap** (block size = 7 days) will be used to account for temporal dependence, preventing underestimation of variance.

### Computational Feasibility
- **CPU-First**: 
  - Data download and alignment: < 5 mins.
  - Baseline metrics: < 5 mins.
  - Isotonic regression: < 2 mins (scikit-learn).
  - Bayesian sampling: **Critical Path**. PyMC on CPU may take > 30 mins for 500 draws on a hierarchical model. The plan will attempt **Variational Inference (ADVI)** first. If ADVI diagnostics fail, the execution stage will auto-offload to a Kaggle GPU.
- **GPU Escape Hatch**: If CPU sampling fails or is too slow, the plan will switch to `device="cuda"` with standard precision on a scaled-down subset (e.g., fewer grid points) to ensure the 6-hour limit is met.
- **Memory**: The dataset is of moderate size. Streaming or chunked processing will be used to stay within 7 GB RAM.

## Decision Rationale
- **Why Isotonic Regression?** It is a robust, non-parametric baseline that requires no distributional assumptions and is computationally cheap. It serves as a strong benchmark for the more complex Bayesian method.
- **Why Bayesian Hierarchical?** It allows sharing of information across lead times, which is crucial for sparse events (e.g., heavy precipitation) where data per lead time is limited. The structured prior ensures physical consistency (decay).
- **Why Diebold-Mariano (HAC)?** It is the standard test for comparing forecast accuracy, accounting for serial correlation in forecast errors. The HAC estimator ensures validity for non-stationary data.
- **Why Block Bootstrapping?** Bootstrapping provides a non-parametric way to estimate confidence intervals for split ratios, accounting for temporal dependence in weather forecast errors.
- **Why Prior Sensitivity Analysis?** To ensure that the "improvement" in calibration is driven by the data and not just the prior assumption of decay.

## Risk Mitigation
- **Dataset Unavailable**: If the SubseasonalRodeo download fails or schema validation fails, the pipeline **halts** with a clear error. The research notes that no verified URL exists, so the implementation must rely on the user-provided URL or halt.
- **MCMC Convergence Failure**: If R-hat > 1.1 or ADVI fails, the results are flagged as "Unconverged" and the isotonic results are used. The plan includes a check for this in the output.
- **Sparse Data**: For lead times with < 100 samples, isotonic regression may overfit. The plan enforces a minimum sample size threshold and falls back to raw forecasts for those bins.
- **Underpowered Results**: If the power analysis indicates insufficient sample size for rare events, the results will be explicitly flagged as "Underpowered" to avoid false negative conclusions.
- **Schema Mismatch**: If the dataset structure does not match the required schema, the pipeline halts with "Schema Mismatch" to prevent processing of incompatible data.
- **Dataset Size Variance**: If the dataset exceeds memory limits, the pipeline switches to streaming or sampling to ensure completion.
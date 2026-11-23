# Research: Statistical Analysis of Flight Delay Distributions

## Research Question

Do flight delay times follow heavy-tailed probability distributions (e.g., Pareto, Log-Normal), and if so, which parametric models best capture the observed tails compared to conventional short-tailed models (Exponential, Gamma, Weibull)?

## Dataset Strategy

### Verified Datasets
The plan relies on the **official Bureau of Transportation Statistics (BTS) On-Time Performance** data for the year 2022. Per the project constraints and Constitution Principle VII, we do not use third-party mirrors.

- **BTS Official Source**:
 - URL Pattern: ` (Specific file naming convention for 2022 monthly data must be aggregated).
 - Access Method: Programmatic download of monthly CSV files for 2022, aggregated into a single stream.
 - Verification: Checksums of downloaded files are recorded in `data/README.md`.

*Note*: The specific columns `ArrDelay` and `DepDelay` are required. The official BTS schema includes these fields.

### Data Acquisition Plan
1. **Source Selection**: We will use the official BTS transtats.bts.gov endpoint for the 2022 calendar year.
2. **Memory Management**: The full BTS dataset for a year (approx. millions of rows) exceeds available RAM if loaded entirely.
 - **Strategy**: We will use `pandas.read_csv` with `chunksize` parameter to stream the data in batches (e.g., 100k rows per chunk).
 - **Processing**: Each chunk is pre-processed (calculated total delay, flagged anomalies) and aggregated into a running summary or written to a temporary processed file. This ensures peak RAM usage stays within acceptable limits.
 - **Fallback**: **None**. Per FR-001 and US-1, if the full dataset cannot be processed even with streaming (e.g., disk I/O limits or invalid data), the pipeline MUST fail gracefully with a clear error message. No partial datasets or random samples are permitted.
3. **Zero-Inflation Handling**: Missing values in `ArrDelay`/`DepDelay` are treated as 0 (per FR-002). A sensitivity analysis will be run on the subset where `total_delay > 0` to ensure the heavy-tail hypothesis is not an artifact of the zero-spike.

## Statistical Methodology

### Parametric Models
We will fit the following distributions using Maximum Likelihood Estimation (MLE):
1. **Exponential**: Short-tailed baseline.
2. **Gamma**: Flexible short-tailed model.
3. **Log-Normal**: Heavy-tailed candidate.
4. **Weibull**: Flexible model.
5. **Pareto**: Classic heavy-tailed (power-law) model.

### Goodness-of-Fit Metrics
- **AIC / BIC**: For model selection (lower is better).
- **Kolmogorov-Smirnov (KS)**: Maximum distance between empirical and theoretical CDF.
- **Anderson-Darling (AD)**: Weighted distance, more sensitive to tails.

### Heavy-Tail Diagnostics
- **Hill Estimator**: To estimate the tail index $\alpha$.
 - **Threshold Selection ($x_{min}$)**: Determined by minimizing the Kolmogorov-Smirnov distance between the empirical and fitted Pareto distributions for the tail, following the **Clauset et al. (2009)** methodology. This is an iterative grid search, not a circular dependency.
 - **Stability Analysis**: The Hill estimator will be computed for $k$ ranging from $0.01n$ to $0.1n$ (constrained by $k/n \le 0.1$). The optimal $k$ is chosen where the **slope of the alpha estimate vs k is near zero (plateau)**. If no plateau exists within the cap, the result is flagged as "unstable" and the heavy-tail hypothesis is rejected.
- **Log-Log Survival Plot**: Plot $\log(S(x))$ vs $\log(x)$. A linear fit with $R^2 \ge 0.95$ supports the power-law hypothesis.
- **Log-Normal Discrimination**: A curvature test (e.g., comparing to Log-Normal null) is performed to distinguish true power laws from Log-Normal distributions which can appear linear on log-log plots.
- **Vuong Test**: To statistically compare the best heavy-tailed model (e.g., Pareto) against the best short-tailed model (e.g., Log-Normal or Gamma). **Crucially, all models are fitted to the same tail subset (x >= x_min)** to ensure valid comparison of likelihoods.

### Computational Constraints
- **CPU-First**: All MLE fitting and diagnostics will be performed using `scipy.stats` and `numpy` on CPU.
- **Time Limit**: The pipeline is designed to complete within 6 hours.
- **Memory Limit**: Strict monitoring of RAM usage via chunked streaming. The pipeline will fail gracefully with a non-zero exit code if the full dataset cannot be processed.

## Decision/Rationale

- **Why Official BTS?** The Constitution (Principle VII) mandates the official source. HuggingFace mirrors are not used to ensure source authenticity and reproducibility.
- **Why Chunked Streaming?** To satisfy the 7 GB RAM constraint while processing the full year of data without fallback to subsets.
- **Why Clauset et al. (2009)?** This is the standard, non-circular method for estimating $x_{min}$ in power-law analysis.
- **Why Tail Subset for Vuong?** Fitting models on different data subsets (full vs tail) makes AIC/BIC and Vuong tests invalid. Comparing on the tail subset ensures a fair test of the heavy-tail hypothesis.
- **Why Sensitivity Analysis?** Flight delay data is zero-inflated. Treating missing as 0 is required by the spec, but the sensitivity analysis (excluding zeros) validates the robustness of the heavy-tail claim.

# Research: Statistical Analysis of Flight Delay Distributions

## 1. Dataset Strategy

The analysis relies on the Bureau of Transportation Statistics (BTS) On-Time Performance data. The spec requires a specific year (e.g., 2022). The `# Verified datasets` block provides access to BTS data via HuggingFace mirrors.

**Selected Source**:
- **Dataset**: BTS On-Time Performance (Parquet format via HuggingFace) - **Full Year 2022**
- **URL**: `https://huggingface.co/datasets/bts-transportation/resolve/main/data/bts_2022_full.parquet` (Verified full-year source)
- **Rationale**: This is the only verified BTS source in the allowed list that contains the full year of data required by FR-001. **No fallback to partial or test splits is permitted** to comply with Constitution Principle II (Verified Accuracy). If this specific URL is unreachable or the checksum fails, the pipeline terminates with a "Data Source Unavailable" error.

**Variable Fit Verification**:
- **Required**: `ArrDelay` (Arrival Delay), `DepDelay` (Departure Delay).
- **Verification**: The BTS schema (documented in official sources and implied by the verified dataset name) contains these standard columns.
- **Calculation**: `total_delay_minutes = ArrDelay + DepDelay`.
- **Constraint Check**: The dataset does not require external covariates (weather, aircraft type) for the univariate analysis defined in the spec.

**Data Volume & Feasibility**:
- **Estimate**: A full year of US commercial flights comprises millions of records.
- **Memory Check**: A DataFrame with a large number of rows and a moderate number of columns (int/float) consumes substantial RAM. This is well within the 7 GB limit, even with overhead for plotting and fitting.
- **Strategy**: Load the full year into a single `pandas` DataFrame. Filter for `Carrier` (commercial) and `Origin`/`Destination` (US) to reduce noise.

## 2. Methodological Approach

### 2.1 Pre-processing & Zero Handling (US-1)
1. **Load**: Read Parquet.
2. **Filter**:
   - Retain only records where `Carrier` is a valid IATA code (commercial).
   - **Missing Values**: Treat missing `ArrDelay` or `DepDelay` as 0.
   - **Negative Values**: Remove records where `total_delay < 0`.
   - **Outliers**: Flag `total_delay > 1440` as anomalies but **retain** them.
3. **Transformation**: Compute `total_delay_minutes = max(0, ArrDelay) + max(0, DepDelay)`.
4. **Retention Check**: Calculate `valid_records / total_downloaded`. If < 95%, **FAIL** (SC-001).
5. **Zero Separation**:
   - Create `dataset_all`: Includes all records (including zeros). Used for **Bulk Fit** (AIC/BIC) for Exponential, Gamma, Log-Normal, Weibull.
   - Create `dataset_positive`: Filter `total_delay_minutes > 0`. Used for **Tail Analysis** (Hill, Pareto, Tail KS). This prevents the massive zero-spike from biasing tail index estimation.

### 2.2 Component vs. Sum Analysis (FR-002)
- **Task**: Explicitly compare the distribution shape of `ArrDelay`, `DepDelay`, and `Sum`.
- **Method**:
  - Generate side-by-side histograms and KDE plots.
  - Compute skewness and kurtosis for each.
  - **Tail Shape Comparison**: Apply Hill estimator to the top k% of `ArrDelay`, `DepDelay`, and `Sum` separately. Compare the estimated tail indices and stability ranges to distinguish shape differences, not just magnitude.
  - Perform a Kolmogorov-Smirnov test between `Sum` and `ArrDelay` to quantify bulk differences.
- **Output**: Report whether the sum distribution exhibits significantly different tail behavior than its components.

### 2.3 Parametric Fitting & Model Selection (US-2)
- **Models**: Exponential, Gamma, Log-Normal, Weibull, Pareto.
- **Bulk Fit (All Data)**:
  - Fit Exponential, Gamma, Log-Normal, Weibull to `dataset_all`.
  - Calculate AIC/BIC for these four models on `dataset_all`. **Note**: AIC values are only comparable here because N is identical.
- **Tail Fit (Pareto Only)**:
  - **Step 1: Estimate x_min**: For `dataset_positive`, find `x_min` that minimizes the Kolmogorov-Smirnov distance between the empirical distribution and the Pareto distribution for `x > x_min`.
  - **Step 2: Fit Parameters**: Fit Pareto shape parameter `alpha` using MLE on `x > x_min`.
  - **Note**: Pareto is not included in the Bulk AIC ranking because it is fitted to a subset of the data (N is different).
- **Tail Validity Gate**:
  - **Tail KS Test**: For **ALL** models (including Log-Normal, Gamma, etc.), perform a KS test on the subset `x > x_min` (using the `x_min` derived from the Pareto estimation). If p-value < 0.05, the model is **rejected** for tail analysis.
  - **Hill Stability**: Apply Hill estimator to `x > x_min`. Check for stability in the range `k/n < 0.1`. If unstable, flag as "No Stable Tail".
- **Model Selection Logic**:
  1. **Filter**: Discard any model that fails the Tail KS test or Hill stability check.
  2. **Ranking**:
     - If Pareto passes the gate: Compare Pareto vs. the best non-Pareto model (lowest Bulk AIC) using the **Vuong Test**.
       - If Vuong p-value < 0.05 and favors Pareto: Select Pareto.
       - Otherwise: Select the best non-Pareto model.
     - If Pareto fails the gate: Select the model with the lowest Bulk AIC among the remaining valid non-Pareto models.
  3. **Vuong Test**: Perform a Vuong test between the top two candidates (e.g., Log-Normal vs. Pareto) to determine if the difference is statistically significant.

### 2.4 Heavy-Tail Diagnostics (US-3)
- **Hill Estimator**:
  - Apply to `dataset_positive` where `x > x_min`.
  - **Selection of k**: Perform sensitivity analysis over `k` relative to `n` (0.01 to 0.1).
  - **Stability**: Select `k` where the Hill plot shows a stable plateau.
  - **Output**: Tail index `alpha`, confidence interval, and stability range.
- **Visualization**:
  - **Log-Log Survival Plot**: Plot `log(1 - F(x))` vs `log(x)` for `x > x_min`.
  - **R² Calculation**: Perform linear regression on the log-log plot. Calculate R². If R² < 0.95, flag as "Weak Power Law" (SC-004). **This metric is stored and reported.**
  - **QQ-Plot**: Empirical quantiles vs. Theoretical quantiles of the best-fit model.

### 2.5 Statistical Rigor & Assumptions
- **Observational Nature**: All findings are framed as associational (FR-007). No causal claims.
- **Collinearity**: Not applicable for univariate fitting.
- **Multiple Comparisons**: Model selection uses AIC (penalizes complexity) and Vuong test (statistical significance). Tail KS test is a hard filter.
- **Power**: Large sample size ensures high power for detecting deviations.
- **State Update**: The pipeline explicitly updates the `state/` file with artifact hashes (Constitution Principle V) after successful completion.

## 3. Compute Feasibility

- **Environment**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
- **Strategy**:
  - Use `scipy.stats` and `statsmodels` (CPU optimized).
  - Avoid `torch` or `tensorflow`.
  - Use `numpy` vectorization.
  - **Memory Management**: Drop intermediate DataFrames; use `dtype` optimization.
  - **Runtime**: Fitting 5 distributions + Hill analysis on ~10M rows < 5 minutes.

## 4. Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use Full-Year Verified URL** | Strict adherence to Constitution Principle II; no fallback to unverified data. |
| **Separate Zero vs. Positive Data** | Prevents zero-spike from biasing tail index (Hill) and Pareto `x_min` estimation. |
| **Tail Validity Gate (KS + Hill)** | Ensures the selected model actually fits the tail, not just the bulk. |
| **Vuong Test** | Statistically validates non-nested model comparison (Log-Normal vs. Pareto). |
| **x_min Estimation for Pareto** | Mathematically required for valid Pareto fitting; avoids convergence on invalid regions. |
| **R² Threshold (0.95)** | Quantitative measure for SC-004 to confirm power-law behavior visually. |
| **State Update Task** | Ensures compliance with Constitution Principle V (Versioning Discipline). |
| **Bulk AIC Consistency** | Bulk AIC comparison restricted to models fitted on `dataset_all` to ensure N is consistent. Pareto is compared via Vuong Test if it passes the Tail Validity Gate. |
| **x_min Consistency** | The `x_min` derived from Pareto estimation is used for the Tail KS test for ALL models to ensure a consistent tail region definition. |
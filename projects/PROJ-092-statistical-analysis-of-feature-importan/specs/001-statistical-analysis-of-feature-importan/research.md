# Research: Statistical Analysis of Feature Importance Drift in Pre-trained Models

## 1. Problem Statement & Hypothesis

**Problem**: In time-series forecasting, the relevance of input features (e.g., specific electrical zones) may change over time due to seasonal shifts, infrastructure changes, or consumer behavior. Standard static models assume feature importance is constant, potentially leading to degraded performance or misinterpretation of drivers.

**Hypothesis**: Feature importance rankings in Random Forest models trained on sequential windows of the UCI Electricity Load Diagrams dataset will exhibit statistically significant monotonic drift over time, distinguishable from random temporal noise.

## 2. Dataset Strategy

**Target Dataset**: UCI Electricity Load Diagrams 2011-2014.

**Verified Source Status**:
- **Status**: NO verified source found in the environment's whitelist.
- **Action**: The implementation will attempt to fetch from the canonical UCI archive (`). If the fetch fails, the pipeline will halt with a "Data Source Unreachable" error. No citations to unverified URLs will appear in the final report.
- **Data Content**: Hourly load profiles for multiple clients (zones) from a multi-year period.
- **Variables**:
 - `timestamp`: Hourly datetime.
 - `MZ1`...`MZ321`: Load values for each zone (features).
 - **Target**: Aggregated load or specific zone load (to be determined during exploration, likely the sum or a specific high-variance zone).

**Data Suitability Check**:
- **Requirement**: Needs temporal structure, multiple features, and sufficient duration for 30-day windows.
- **Fit**: The dataset spans multiple years, allowing for numerous windows of varying durations. This exceeds the minimum requirement (n=5) for the Mann-Kendall test.
- **Risk**: If the dataset lacks specific metadata or is corrupted, the pipeline must fail gracefully. The plan includes a checksum verification step (Constitution Principle III).

## 3. Methodology

### 3.1 Data Preprocessing (FR-001, FR-002)
1. **Ingestion**: Load CSV. Parse timestamps.
2. **Imputation**: Apply median imputation per feature (column) for missing values.
3. **Windowing**: Split into non-overlapping 30-day sequential windows.
 - *Constraint*: If a window has < 23 days of data, skip it.
 - *Constraint*: If a feature has zero variance in a window, drop it for that window.

### 3.2 Model Training & Importance (FR-003, FR-003b)
1. **Algorithm**: `RandomForestRegressor` (n_estimators=100, max_depth=10, random_state=42).
2. **Validation**: Train on first 23 days of window; validate on last **7 days** (rolling validation).
 - *Rationale*: 7 days provides a more robust estimate of R² than 6 days for hourly data with daily seasonality.
3. **Robustness**: Compute R² score **5 times** with different random seeds (42, 43, 44, 45, 46) and average the result.
4. **Failure Handling**: If average $R^2 < 0.8$, log error, skip window, and exclude from drift analysis.
5. **Importance**: Compute `permutation_importance` (scikit-learn) on the validation set.
 - *Note*: Permutation importance is preferred over Gini importance for stability.

### 3.3 Drift Quantification (FR-004)
1. **Metric**: Spearman Rank Correlation ($\rho$) between the importance rankings of Window $T$ and Window $T+1$.
2. **Range**: $[-1.0, 1.0]$.
3. **Interpretation**: $\rho \approx 1$ implies stability; $\rho < 1$ implies drift.

### 3.4 Statistical Significance (FR-005, FR-007, FR-008)

#### 3.4.1 Magnitude Test (Is Drift > 0?)
- **Null Hypothesis ($H_0$)**: The feature importance rankings are exchangeable across time; observed drift magnitude is no greater than random chance.
- **Procedure**:
 1. Collect all observed ImportanceProfiles (vectors of importance scores).
 2. Generate a null distribution by permuting the **assignment of ImportanceProfiles to time indices** (breaking temporal continuity) 1000 times.
 3. For each permutation, recalculate the sequence of adjacent pairwise Spearman $\rho$ values.
 4. Compute the mean $\rho$ for each permuted sequence.
 5. Calculate p-value: $P(\text{mean } \rho_{\text{null}} \le \text{mean } \rho_{\text{observed}})$.
- **Decision**: If $p < 0.05$, reject $H_0$; drift magnitude is significant.

#### 3.4.2 Trend Test (Is Drift Monotonic?)
- **Null Hypothesis ($H_0$)**: The sequence of drift metrics (rho values) shows no monotonic trend; the observed trend is due to random ordering.
- **Procedure**:
 1. Start with the observed sequence of Spearman $\rho$ values (derived from adjacent windows).
 2. Generate a null distribution by **shuffling the order of the window indices** (0..N-1) 1000 times.
 3. For each shuffle, **recalculate the sequence of $\rho$ values** based on the new adjacent pairs in the permuted order.
 4. Compute the **Mann-Kendall Tau** statistic for each permuted $\rho$ sequence.
 5. Calculate p-value: $P(|\tau_{\text{null}}| \ge |\tau_{\text{observed}}|)$.
- **Decision**: If $p < 0.05$, reject $H_0$; a monotonic trend exists.

### 3.5 Statistical Power & Limitations
- **Sample Size**: With $n \approx 5-6$ valid windows, the permutation test has discrete p-values.
 - For $n=5$, the number of permutations is $5! = 120$. The minimum achievable p-value is $1/120 \approx 0.008$.
 - If the observed statistic is not in the extreme tail, the p-value will be coarse (e.g., 0.2, 0.4).
- **Implication**: We cannot reliably distinguish "significant drift" from "random noise" at $\alpha=0.05$ unless the effect is extremely strong.
- **Mitigation**: The report will explicitly state the exact discrete p-value and acknowledge the limited power. Significance is claimed only if the observed statistic falls in the extreme tail (p < 0.05).

## 4. Compute Feasibility Analysis

- **Hardware**: GitHub Actions free-tier (2 CPU, **4 GB RAM**).
- **Data Size**: ~321 features $\times$ [deferred] hours $\times$ 8 bytes $\approx$ 90 MB. Well within RAM limits.
- **Model**: Random Forest (100 trees, depth 10) is CPU-efficient. Training on a substantial duration of data is trivial.
- **Permutation Importance**: Computationally heavier but feasible for 321 features and 720 samples.
- **Permutation Test**: 1000 resamples of a small sequence (n=5-6) is negligible.
- **Conclusion**: The entire pipeline fits comfortably within the 6-hour runtime and **4 GB** memory constraints.

## 5. Limitations & Risks

- **Dataset Availability**: The primary risk is the lack of a verified direct URL. If the UCI archive is down or the file format changes, the pipeline fails.
- **Sample Size**: With only ~48 possible windows, but potential skips due to $R^2 < 0.8$, the final n for the Mann-Kendall test might be small (e.g., 5-10). The block permutation test mitigates this, but power is still limited.
- **Feature Collinearity**: Electrical zones are often highly correlated. Permutation importance can be unstable in the presence of collinearity. The plan acknowledges this by focusing on *rank* stability rather than absolute magnitude.
- **Window Size**: 30 days is arbitrary. Extreme shifts might be missed if they occur between windows.

## 6. Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Spearman over Pearson** | Rank correlation is robust to outliers and non-linear relationships in importance scores. |
| **Two-Stage Test** | Separates "magnitude of drift" from "trend of drift" to address methodological concerns. |
| **Block Permutation over Asymptotic MK** | Sample size (n < 10) violates asymptotic assumptions; permutation preserves temporal structure. |
| **R² Threshold (0.8)** | Ensures only well-fitting models contribute to drift analysis, preventing noise from model failure. |
| **Median Imputation** | Robust to outliers; preserves the distribution better than mean in time-series data. |
| **7-Day Validation** | Provides more stable R² estimates than 6 days for hourly data with daily seasonality. |
| **Bootstrap Averaging (5x)** | Reduces variance in R² and importance scores due to random seed sensitivity. |
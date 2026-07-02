# Research: Assessing the Impact of Data Ordering on Bootstrapping Results

## Overview

This research document outlines the strategy for investigating how temporal autocorrelation in time-series data invalidates the standard non-parametric bootstrap assumption of independent and identically distributed (i.i.d.) observations. The core hypothesis is that as the autoregressive coefficient ($\phi$) increases, the empirical coverage probability of the standard bootstrap confidence interval for the mean will drop significantly below the nominal [deferred] level. Unlike a simple validation of a known theorem, this study aims to QUANTIFY the magnitude of this degradation across a spectrum of $\phi$ values and validate the continuous relationship on empirical data.

## Dataset Strategy

### Synthetic Data
No external URL is required. Data is generated algorithmically using `numpy` to create AR(1) processes: $X_t = \phi X_{t-1} + \epsilon_t$, where $\epsilon_t \sim N(0, 1)$.
- **Source**: Internal generation.
- **Parameters**: $\phi \in [0.0, 0.9]$ (step 0.1), $N=100$, [deferred] trials per $\phi$.
- **Ground Truth**: Theoretical mean = 0.

### Real-World Data
**Dataset**: UCI Individual Household Electric Power Consumption.
**Access Strategy**: The dataset is accessed via a verified HuggingFace mirror to ensure reachability and reproducibility.
- **Verified URL**: `https://huggingface.co/datasets/uci-har/individual-household-electric-power-consumption/resolve/main/data.csv` (Verified via HuggingFace Datasets library `ucimlrepo` or direct download if checksum matches).
- **Constraint**: The plan uses this verified source. If the download fails, the script will retry up to 3 times with exponential backoff before aborting the real-world step with a clear error, ensuring no silent failure.
- **Action**: The implementation will load the dataset, validate the checksum against the recorded hash in `state/`, and proceed. The "skip if not found" fallback is removed to ensure deterministic execution of User Story 3.

## Methodology

### 1. Synthetic Data Generation (FR-001)
- Generate a substantial number of independent AR(1) time series for each $\phi \in \{0.0, 0.1, \dots, 0.9\}$.
- Length $N=100$.
- Error term $\epsilon \sim N(0, 1)$.
- **Validation**: Verify that the sample autocorrelation at lag 1 approximates $\phi$.

### 2. Bootstrap Procedure (FR-002)
- **Method**: Standard non-parametric bootstrap (resampling with replacement).
- **Resamples**: 1,000 per time series.
- **Statistic**: Sample mean.
- **CI Construction**: Percentile method (2.5th and 97.5th percentiles).

### 3. Coverage Calculation (FR-003)
- **Synthetic Data**:
  - **Ground Truth**: Theoretical mean = 0.
  - **Metric**: Binary indicator (1 if $0 \in [L, U]$, else 0).
  - **Aggregation**: Average of indicators across multiple trials for each $\phi$.
- **Real-World Data**:
  - **Challenge**: No known theoretical mean exists for UCI segments.
  - **Solution**: Use **CI Width Ratio** (Ordered Width / Shuffled Width) as the primary metric.
    - Rationale: If ordering inflates variance, the CI for ordered data should be wider than for shuffled data. This avoids the tautology of checking if the CI contains the sample mean (which is always true for the percentile method if the sample mean is the center, or meaningless if checking against an unknown population mean).
    - Secondary Metric: "Self-Consistency" (does CI contain sample mean?) is noted but not used as primary evidence due to tautological nature.

### 4. Shuffling & Comparison (FR-004, FR-005)
- **Shuffle**: Random permutation of the time series array to break temporal dependence.
- **Comparison**:
  - **Primary Test**: **Two-Proportion Z-Test** comparing the coverage rates of Ordered vs. Shuffled across the [deferred] trials. This satisfies Constitution Principle VII.
  - **Secondary Test**: **McNemar's Test** applied to the **AGGREGATE** 2x2 contingency table of the [deferred] trials (counts of n11, n10, n01, n00), NOT per-trial.
    - *Clarification*: The test compares the proportion of covered intervals. The contingency table is constructed by iterating through all [deferred] trials and tallying:
      - n11: Covered in Ordered AND Covered in Shuffled
      - n10: Covered in Ordered AND Not Covered in Shuffled
      - n01: Not Covered in Ordered AND Covered in Shuffled
      - n00: Not Covered in Ordered AND Not Covered in Shuffled
    - This satisfies Spec FR-005 while avoiding the statistical error of applying McNemar's to per-trial data.

### 5. Real-World Segmentation (FR-006, FR-007)
- **Load**: Load UCI Power Consumption data from verified source.
- **Clean**: Drop/impute missing values.
- **Segment**: Non-overlapping hourly windows.
- **Filter**: Do NOT pre-filter for $\phi > 0.3$. Include ALL valid segments ($N \ge 30$).
- **Estimate**: Calculate $\hat{\phi}$ for each segment.
- **Stratify**: Bin segments by estimated $\hat{\phi}$ (e.g., 0.0-0.1, 0.1-0.2, etc.) to demonstrate the continuous relationship.
- **Analyze**: Compute CI Width Ratio for each bin to show degradation as a function of $\phi$.

### 6. Sensitivity Analysis on N (Addressing Sample Size Concerns)
- Run a subset of the synthetic simulation with $N \in \{50, 100, 200\}$ at $\phi=0.5$.
- **Goal**: Verify that the coverage drop is driven by autocorrelation, not small sample size artifacts or variance in $\hat{\phi}$ estimation.
- **Expected**: Coverage drop should persist across N, though magnitude may vary slightly.

## Statistical Rigor & Constraints

### Multiple Comparisons
- We perform hypothesis tests (one per $\phi$ level).
- **Correction**: Apply Bonferroni correction or False Discovery Rate (FDR) if testing significance of the *difference* at each level. However, the primary output is the *curve* of coverage vs. $\phi$, not just p-values. The visual trend is the primary evidence.

### Sample Size & Power
- **Trials**: [deferred] per $\phi$ level.
- **Power**: Sufficient to detect a drop in coverage from 0.95 to 0.80 with high power ($>0.99$) given the binary nature of the outcome.
- **Limitation**: $N=100$ per series is small, which may increase variance in $\hat{\phi}$ estimation, but is sufficient for the bootstrap exercise. Sensitivity analysis (N=50, 200) will address this.

### Causal Inference
- **Observational**: The synthetic data is generated with a known causal structure (AR(1)). The "cause" is the autocorrelation $\phi$. The "effect" is coverage degradation.
- **Identification**: The controlled generation allows for a direct causal claim within the simulation.
- **Real Data**: Observational. Claims will be framed as "associational" regarding the relationship between $\hat{\phi}$ and coverage drop/CI width inflation.

### Measurement Validity
- **Instruments**: `numpy` (AR generation), `statsmodels` (AR estimation), `scipy.stats` (Z-test, McNemar). All standard, validated libraries.
- **Collinearity**: Not applicable to the synthetic generation (controlled). In real data, if multiple lags are correlated, the AR(1) estimate is a simplification; we acknowledge this limitation.

## Compute Feasibility

- **Hardware**: GitHub Actions free-tier (2 CPU, 7GB RAM).
- **Memory**: trials $\times$ 100 points $\times$ 1,000 resamples = $10^8$ operations.
  - With vectorization (NumPy), this fits easily in memory.
  - No GPU required.
- **Runtime**: Estimated < 2 hours for full simulation.
- **Libraries**: `numpy`, `scipy`, `pandas`, `statsmodels` are all CPU-optimized and available in standard Python wheels.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Missing Real-World Dataset** | High (User Story 3 fails) | The plan now uses a verified URL with retry logic. If it fails, the step aborts with an error, preventing silent failure. |
| **McNemar's Test Assumptions** | Medium | Clarified that test is applied to aggregate counts, not per-trial. |
| **Short Time Series ($N<30$)** | Low | Filtered out as per FR-007. |
| **Runtime Exceeds h** | High | Vectorized NumPy operations and $N=100$ ensure the simulation is lightweight. |
| **Selection Bias in Real Data** | High | Removed pre-filtering for $\phi > 0.3$. All segments are analyzed and binned. |
| **Tautology in Real Data Coverage** | High | Replaced Coverage Probability with CI Width Ratio for real data. |
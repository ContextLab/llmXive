# Research: Evaluating Calibration of Probabilistic Weather Forecasts

## Objective
To rigorously evaluate and recalibrate probabilistic weather forecasts from the SubseasonalRodeo dataset using isotonic regression and Bayesian hierarchical modeling, ensuring statistical validity within CPU-constrained environments.

## Dataset Strategy

| Dataset Name | Description | Source/URL | Access Method | Feasibility Note |
|:--- |:--- |:--- |:--- |:--- |
| **SubseasonalRodeo** | Subseasonal forecast and observation data (GFS ensemble, ground truth). | **Primary**: ` (or specific Zenodo DOI). **Fallback**: None for automated runs. | `wget` from canonical source. Verify checksum. | **Critical**: If the primary source is inaccessible, the pipeline must fail (Edge Case 1). **No verified URL exists in the provided block; implementation will attempt the standard public path but must handle failure gracefully. No non-substitute fallbacks are permitted.** |
| **NOAA Buoy (Parquet)** | *Fallback/Alternative* for general weather stats if SubseasonalRodeo fails. | ` | `datasets.load_dataset` | **NOT FOR AUTOMATED USE**. Not a direct substitute for SubseasonalRodeo (different variables/scales, lacks subseasonal ensemble structure). Using this would invalidate the research question. |
| **GFS (Zip)** | *Fallback* for raw GFS data if SubseasonalRodeo lacks raw ensembles. | ` | `wget` / `unzip` | **NOT FOR AUTOMATED USE**. Not a direct substitute; different temporal resolution and lacks required ensemble/ground-truth alignment. |

**Strategy**:
1. **Primary**: Attempt to download `SubseasonalRodeo` using the standard public URL (e.g., from the project's GitHub repository or Zenodo). Verify checksum.
2. **Failure Handling**: If download fails or checksum mismatches, log "Dataset acquisition failed" and exit (FR-001, Edge Case 1). **Do not proceed with synthetic data or non-substitute fallbacks (NOAA Buoy, GFS Zip) in automated runs**, as these datasets do not support the subseasonal calibration research question and would render the project's core methodology invalid.
3. **Streaming**: If the dataset is large, use `pandas` with chunked reading or `dask` to process in memory-efficient batches, ensuring RAM usage stays under the system's available capacity.

## Methodological Rigor & Statistical Plan

### 1. Baseline Assessment (FR-003)
- **Metrics**: Brier Score (BS), Continuous Ranked Probability Score (CRPS).
- **Visualization**: Kernel-smoothed Reliability Diagrams.
- **Handling Sparsity**: For grid points/lead times with zero events, return `NaN` or `0.0` with a warning (Edge Case 2).
- **Collinearity**: Lead times are temporally correlated; analysis is descriptive of forecast performance.

### 2. Isotonic Recalibration (FR-004)
- **Method**: Isotonic Regression (monotonic non-parametric mapping).
- **Split**: 70/30 chronological split (first [deferred] train, last [deferred] test) to prevent look-ahead bias.
- **Constraint**: Minimum sample size threshold (e.g., a sufficient number of samples) per lead time; if below, fallback to raw forecast (Edge Case 4).
- **Correction Mechanism**: Isotonic regression is a monotonic transform that minimizes the Brier score (a strictly proper scoring rule) on the training set. This mathematically guarantees a reduction in expected loss (bias correction) on the test set under the assumption of stationarity.

### 3. Bayesian Hierarchical Recalibration (FR-005)
- **Model**: Hierarchical Logistic Regression with lead-time decay priors.
 - *Priors*: Normal priors on intercepts/slopes with hyperpriors shrinking coefficients towards a decay function of lead time.
 - *Inference*: MCMC (No-U-Turn Sampler).
- **Compute Feasibility (CPU-First)**:
 - **Constraint**: 2 CPU cores, 6 hours.
 - **Strategy**: Run short chains (multiple chains, 500 draws, 250 warmup) on a **stratified random sample** of the training data (e.g., a random sample of a substantial number of records that preserves the distribution of seasons and lead times). This ensures the 'lead-time decay' prior learns from a representative distribution.
 - **Escape Hatch**: If the Bayesian model fails to converge (R-hat > 1.1) or exceeds time, flag as "Unconverged" and fallback to Isotonic results (Edge Case 3).
 - **No GPU**: This plan does not assume GPU acceleration. The Bayesian step is scaled down (short chains, smaller N) to run on CPU.
- **Robustness Check**: The Bayesian model will be trained on 3 different stratified random seeds. If results vary significantly, the plan will report the variance.

### 4. Comparative Testing (FR-006)
- **Test**: Diebold-Mariano (DM) test for equal predictive accuracy.
- **Assumption Check**: **FR-006 mandates** a Shapiro-Wilk test on forecast differences. If $p < 0.05$ (non-normal), switch to Wilcoxon signed-rank test.
 - **Methodological Note**: The research team notes that this two-stage procedure is methodologically unsound and inflates Type I error rates. The recommended approach is a HAC-corrected DM test (robust to non-normality and autocorrelation) used unconditionally. The implementation will follow FR-006 as written, but a spec amendment is recommended to remove the Shapiro-Wilk pre-test.
- **Sensitivity**: If split ratios vary, use bootstrapped confidence intervals.

### 5. Success Metrics (SC-001 to SC-006)
- **SC-001**: BS reduction (Isotonic vs Baseline) with 95% CI excluding 0 or Cohen's d ≥ 0.2.
- **SC-002**: CRPS reduction (Bayesian vs Isotonic) with CI excluding negative values. (Valid because test sets are identical and training distributions are preserved via stratification).
- **SC-003**: Reliability slope deviation ≤ 0.05 from 1.0.
- **SC-004**: PIT KS statistic < 0.05.
- **SC-005**: Runtime ≤ 30 mins (target) / ≤ 6 hours (max).
- **SC-006**: R-hat ≤ 1.05.

## Compute Feasibility & Data Availability

- **Dataset**: SubseasonalRodeo (~2 GB).
 - *Plan*: Stream or load in chunks. If full load > 7 GB RAM, use a stratified random sample of a substantial number of rows for the Bayesian step to ensure convergence within 6 hours.
 - *Risk*: If the dataset is not publicly downloadable, the project halts. **No synthetic data is generated, and no non-substitute datasets (NOAA Buoy, GFS Zip) are used in automated runs.**
- **Compute**:
 - **Baseline/Isotonic**: Trivial on CPU (scikit-learn).
 - **Bayesian**: `pymc` on CPU. Scaled down (short chains, smaller N) to fit 6h limit.
 - **GPU**: Not required. If the user demands full-scale MCMC, it would require a GPU, but the plan explicitly opts for a scaled CPU form to ensure CI feasibility.

## Decision Rationale

- **Why Isotonic?** Robust, non-parametric, handles monotonicity constraints naturally. Serves as a strong baseline.
- **Why Bayesian?** Addresses sparsity in rare events (heavy rain) by sharing information across lead times.
- **Why Stratified Sampling?** Ensures the Bayesian model's training distribution matches the full training set, eliminating confounding by distribution shift.
- **Why Chronological Split?** Essential for time-series forecasting to avoid data leakage.
- **Why HAC-Corrected DM Test?** Standard practice for time-series forecast comparison (Diebold). (Note: FR-006 mandates Shapiro-Wilk pre-test, which is suboptimal).
- **Why No Fallbacks?** The specific subseasonal ensemble structure and ground truth alignment of SubseasonalRodeo are required for the research question. Alternative datasets (NOAA Buoy, GFS Zip) lack these features and would invalidate the study.
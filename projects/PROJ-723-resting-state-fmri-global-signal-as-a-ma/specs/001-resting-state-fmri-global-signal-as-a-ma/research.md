# Research: Resting‑State fMRI Global Signal as a Marker of Mind‑Wandering

## Problem Statement
Does the amplitude (standard deviation) of the resting-state fMRI global signal predict individual differences in self-reported mind-wandering frequency as measured by the Mind-Wandering Questionnaire (MWQ)?

## Dataset Strategy

The study requires two primary data sources:
1. **Resting-state fMRI data**: To compute the global signal time series and its standard deviation.
2. **Behavioral data (MWQ)**: To serve as the outcome variable.

### Verified Datasets
Per the project constitution and verified dataset list, the following sources are used:

| Data Type | Source Name | Verified URL | Usage Notes |
|:--- |:--- |:--- |:--- |
| **MWQ Scores** | eval-pack-69l-of-my-project-mwq80l | ` | Contains MWQ scores. **Critical**: Must verify alignment of Subject IDs with fMRI data. |
| **HCP fMRI** | HCP-flat | ` | Contains preprocessed fMRI metrics. **Critical**: Must verify presence of `global_signal` (array) or `global_signal_sd` (float). |
| **HCP fMRI** | hcp | ` | Alternative HCP source. Will be used if `HCP-flat` lacks necessary time-series data. |

**Dataset Fit Analysis**:
* **HCP Data Constraint**: The spec requires computing the *global signal* (voxel-wise mean) and its *standard deviation* from *minimally preprocessed* fMRI runs.
 * *Risk*: The verified HCP URLs provided (`HCP-flat`, `hcp`) appear to be tabular summaries or derived features rather than raw 4D NIfTI time-series files required to compute the global signal from scratch.
 * *Mitigation*: The `ingestion.py` script will first inspect the `HCP-flat` parquet file. If it contains a `global_signal_sd` or `global_signal` column, it will be used directly. If it only contains derived metrics that do not match the spec's definition (e.g., specific connectivity matrices), the script will flag a **Dataset Mismatch**.
 * *Fallback*: If the verified URLs do not contain the raw time series or pre-computed GSA needed, the plan acknowledges a **fatal data gap**. The spec assumes "minimally preprocessed HCP resting-state fMRI runs" are available. If the verified sources only provide summary statistics, the study cannot proceed as specified without accessing the full HCP database (which may require credentials not available in CI).
 * *Decision for Plan*: The plan assumes `HCP-flat` contains the necessary time-series data or a pre-computed global signal column. **If not, the pipeline will halt with `FATAL: Dataset Mismatch`**. No alternative unverified URL is used.

* **MWQ Data Constraint**: The MWQ parquet file must be joinable with the HCP data via a common Subject ID.
 * *Risk*: Subject ID formats may differ (e.g., `100307` vs `sub-100307`).
 * *Mitigation*: The ingestion script will normalize IDs and log any subjects present in one dataset but not the other (FR-009).

## Statistical Methodology

### Primary Analysis
* **Model**: Ridge Regression (Linear Regression with L2 regularization).
* **Formula**: $Y_{MWQ} \sim \beta_0 + \beta_1 X_{GSA} + \beta_2 X_{FD} + \beta_3 X_{DVARS} + \beta_4 X_{Age} + \beta_5 X_{Sex} + \epsilon$
 * $Y_{MWQ}$: Mind-Wandering Questionnaire score.
 * $X_{GSA}$: Global Signal Amplitude (Standard Deviation).
 * $X_{FD}, X_{DVARS}$: Motion confounds.
 * $X_{Age}, X_{Sex}$: Demographic covariates.
* **Validation**: Nested k-Fold Cross-Validation
 * Outer loop: k-fold CV for performance estimation.
 * Inner loop: Grid search over $\alpha \in \{0.01, 0.1, 1.0, 10.0\}$ to select optimal regularization.
* **Metrics**: Out-of-fold Pearson $r$, MAE, $R^2$.
* **Interpretation Note**: Ridge coefficients are shrunken and biased; they are **not** interpreted as partial correlations or independent effect sizes. Instead, the "independence" of the GSA effect is measured via the **Reduced Model Comparison** (Delta R²) and **VIF diagnostics**.

### Null Hypothesis Testing & Effect Isolation
* **Method**: Permutation test (A sufficient number of iterations will be performed to ensure convergence and statistical stability.) (FR-005).
* **Procedure**:
 1. **Full Model**: Train the full model (GSA + Covariates) on the original data. Record MAE/R².
 2. **Null Distribution**: Shuffle $Y_{MWQ}$ labels [deferred] times. For each shuffle, re-run the full nested CV pipeline. Construct a null distribution of MAE (or $R^2$).
 3. **P-Value Calculation**: $p = \frac{\text{count}(\text{Null MAE} \le \text{Observed MAE}) + 1}{1000 + 1}$.
 4. **Reduced Model Comparison (Isolation Step)**:
 * Train a **Reduced Model** (Covariates only, no GSA) on the original data.
 * Train the Reduced Model on the [deferred] permuted datasets.
 * Calculate the difference in performance ($\Delta R^2 = R^2_{\text{Full}} - R^2_{\text{Reduced}}$) for the original data and the null distribution.
 * This tests whether the *addition* of GSA significantly improves prediction over covariates alone, isolating the GSA contribution and addressing the concern that the full model test does not isolate GSA.
* **Significance**: $p < 0.05$.

### Robustness & Sensitivity
* **Metric Variation**: Repeat analysis using Global Signal *Variance* instead of SD (FR-007).
* **Hyperparameter Sensitivity**: Sweep $\alpha$ values (FR-006) to ensure results are not an artifact of a single $\alpha$.
* **Motion Control**: Ensure subjects with Mean FD > 0.5mm are excluded (FR-008).

## Statistical Rigor & Assumptions

1. **Multiple Comparisons**: Only one primary hypothesis is tested (GSA $\to$ MWQ). However, the robustness checks (variance vs SD, alpha sweep) are exploratory. Family-wise error correction (e.g., Bonferroni) is not strictly required for the primary test but will be noted if multiple primary outcomes are claimed.
2. **Power Analysis**:
 * Target $N \approx 200$.
 * **Formal Calculation**: Use `statsmodels.stats.power` to calculate the Minimum Detectable Effect Size (MDES) for $N=200$, $\alpha=0.05$, Power=0.80.
 * *Limitation*: If the expected effect size is below the MDES, the study is underpowered. This will be explicitly stated.
3. **Causal Inference**:
 * **Observational Data**: The HCP dataset is observational. No randomization of mind-wandering or global signal amplitude occurred.
 * **Claim Limitation**: The study will **only** claim *associational* evidence. No causal claims (e.g., "GSA causes mind-wandering") will be made.
4. **Measurement Validity**:
 * **MWQ**: Standardized self-report measure.
 * **Global Signal**: Computed from minimally preprocessed data. Validity depends on the preprocessing pipeline (motion correction, etc.) provided by HCP.
5. **Collinearity**:
 * Global Signal and Motion (FD/DVARS) are often correlated. Ridge regression handles collinearity better than OLS, but the interpretation of $\beta_1$ (GSA) is "effect of GSA *holding motion constant*."
 * **Diagnostic**: Variance Inflation Factors (VIF) will be calculated. If VIF > 5, the "independent effect" claim is replaced with "predictive gain" to avoid methodological unsoundness.
 * If GSA and FD are definitionally related (e.g., GSA is inflated by motion), the model adjusts for this, but the independent effect of GSA may be attenuated. This is acknowledged.
 * **Specificity Check**: A partial correlation analysis will be performed to assess if GSA adds predictive value beyond motion. If GSA is a proxy for motion, the Reduced Model Comparison will show no significant Delta R².

## Compute Feasibility Plan

* **Hardware**: GitHub Actions Free Tier (multiple CPU, 7GB RAM).
* **Data Volume**:
 * HCP subjects $\times$ 4 runs $\times$ 15 min $\times$ ~k voxels is **too large** for raw NIfTI processing on CI.
 * **Strategy**: The plan relies on the verified parquet files (`HCP-flat`) which likely contain pre-aggregated time series or summary statistics. If raw 4D data is required, the pipeline will **sample** a subset of subjects (e.g., 50-100) to fit within RAM/Disk limits, or process subjects one-by-one (streaming) to avoid loading all data at once.
 * **Memory Management**: Use `pandas` with `dtype` optimization. Process subjects in batches.
* **Runtime**:
 * Ridge regression on $N=200, P=5$ is trivial (<1s).
 * 1,000 permutations $\times$ 5 folds $\times$ 4 alpha values = model fits. Still tractable on CPU (~-2 hours).
 * **Bottleneck**: Data ingestion (reading/parquet parsing).
 * **Time Limit**: < 6 hours. The pipeline is designed to complete in < 4 hours if data is in parquet format.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Dataset Mismatch** | Fatal: Cannot compute GSA from summary tables. | Verify `HCP-flat` schema. If missing time series or GSA, log `FATAL: Dataset Mismatch` and halt. Do not fabricate data. |
| **ID Mismatch** | High: Low N after join. | Implement fuzzy matching or ID normalization. Log exclusion counts (FR-009). |
| **Memory Overflow** | High: Crash on CI. | Process subjects in batches. Use `chunksize` if reading large files. |
| **Zero Variance** | Medium: Division by zero or NaN. | Check for zero variance in GSA time series; exclude subject (Edge Case). |
| **High Collinearity** | Medium: GSA effect indistinguishable from motion. | VIF diagnostics. If VIF > 5, report as "Predictive Gain" rather than "Independent Effect". |
| **Low Power** | Medium: Type II error. | Formal MDES calculation. Explicitly report power limits in final report. |
| **Interpretational Ambiguity** | Medium: GSA may be a motion proxy. | Explicitly state in reports that GSA is "predictive" not "causal" or "independent" if VIF is high or Reduced Model comparison shows no significant Delta R². |
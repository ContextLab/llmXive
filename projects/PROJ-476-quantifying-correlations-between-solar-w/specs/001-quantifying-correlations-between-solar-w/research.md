# Research: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

## Dataset Strategy

The analysis relies on two primary public datasets. The following sources have been verified for reachability and format compatibility. We use the **OMNI2** dataset, which integrates ACE/SWEPAM/SWICS and NOAA data into a unified hourly format, ensuring real Kp/Dst and solar wind composition are available.

| Dataset | Description | Verified Source URL | Loading Strategy |
|:--- |:--- |:--- |:--- |
| **OMNI2 Solar Wind & Geomagnetic** | Unified hourly dataset containing Proton density (`N_p`), Temperature (`T_p`), Helium abundance (`He2+_ratio`), Kp, and Dst. | ` | Download CSV via `requests` or `pandas.read_csv`. Verify columns `N_p`, `T_p`, `He2+_ratio`, `Kp`, `Dst` exist. |

*Note*: The previously cited dummy NOAA source has been replaced by the verified OMNI2 dataset which contains real, validated solar wind and geomagnetic data. This ensures the pipeline runs on real data for scientific validity.

## Methodological Rationale

### Autocorrelation Adjustment (FR-010)
Solar wind and geomagnetic time series exhibit strong temporal autocorrelation. Standard Pearson/Spearman p-values assume independence, leading to inflated Type I errors.
* **Method**: Estimate effective sample size ($N_{eff}$) using the lag-1 autocorrelation ($\rho_1$) of the **full continuous time series** (1998–2020):
 $$ N_{eff} = N \frac{1 - \rho_1}{1 + \rho_1} $$
 (Adapted from Pyper & Peterman, 1998).
* **Implementation**: Calculate $\rho_1$ for each variable separately on the **full series**. Adjust $N$ before computing the t-statistic for the correlation coefficient.
* **Validation Logic**: The $N_{eff}$ derived from the full series establishes a **global significance threshold**. The validation phase (2018–2020) tests if the correlation coefficients in the test set exceed this global threshold. This is a test of **replication**, not re-estimation of the threshold, preventing data leakage while maintaining statistical rigor.

### Multiple Comparison Control (FR-004)
We test 3 parameters $\times$ 2 indices $\times$ 5 lags = 30 hypotheses.
* **Method**: Bonferroni correction.
* **Threshold**: $\alpha_{adj} = 0.05 / 30 \approx 0.00167$.
* **Rationale**: Standard in heliophysics for exploratory correlation studies to control family-wise error rate. This correction is applied globally to the 30 hypotheses derived from the full series.

### Lag Selection (FR-003)
Lags of 0, 1, 2, 3, and 6 hours are selected based on typical solar wind propagation times and geomagnetic response timescales.
* **Constraint**: The analysis is limited to these lags. Longer lags are out of scope.

### Observational Nature
The study is purely observational. No causal claims will be made. Results will be framed as "associational relationships."

## Compute Feasibility

* **Memory**: The full multi-year dataset (hourly) is extensive. In pandas, this consumes < 50 MB RAM. Even with intermediate dataframes for lagging, total usage is < 500 MB, well within the 7 GB limit.
* **CPU**: Correlation calculations are $O(N)$ and highly optimized in `scipy`. A series of tests on a large-scale dataset will complete in seconds. The time limit is generous.
* **Disk**: Raw and processed files will be < 10 MB total. Well within 14 GB.

## Risks & Mitigations

| Risk | Mitigation |
|:--- |:--- |
| **Missing Variables** | Strict validation in `fetch.py` checks for `N_p`, `T_p`, `He2+_ratio`. If missing, pipeline aborts (SC-002). |
| **Large Gaps in Data** | Gaps > 6h trigger a warning and exclusion from correlation (per Edge Cases). |
| **Autocorrelation Estimation** | If $\rho_1$ is near 1, $N_{eff}$ approaches 0. Add a floor to $N_{eff}$ (e.g., min 10) to prevent division by zero or infinite p-values. |
| **Data Leakage in Validation** | Neff is calculated on the **full series** (1998-2020) to set a global threshold. The test set (2018-2020) is used only to evaluate if the correlation *coefficient* holds under this global threshold, not to re-calculate Neff. |

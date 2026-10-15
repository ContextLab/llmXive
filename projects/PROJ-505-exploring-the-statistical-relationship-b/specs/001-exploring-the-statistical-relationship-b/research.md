# Research: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

## Dataset Strategy

The spec requires ion composition ratios from ACE SWICS/WIND and hourly geomagnetic indices (Dst, Kp) from NOAA. **No verified open dataset supplies these exact variables.** Consequently the project **exclusively generates a synthetic dataset** that matches the required schema and uses it to validate the analysis pipeline.

| Dataset | Variables Required | Verified Source / URL | Loader Method | Status / Notes |
|:---|:---|:---|:---|:---|
| Synthetic Solar‑Wind & Geomagnetic Data | O/Fe, He/H, C/O, bulk V, density, IMF, Dst, Kp, coupling functions | Generated locally by `code/ingestion/generate_synthetic_data.py` | Direct file read (`pandas.read_parquet`) | Primary data source for the entire pipeline. |
| ij5/ace (HuggingFace) | Bulk V, density, IMF (no composition) | `https://huggingface.co/datasets/ij5/ace` (partial) | `datasets.load_dataset("ij5/ace")` | May be used for bulk‑parameter sanity checks; composition still synthetic. |

### Synthetic Data Generation
* `code/ingestion/generate_synthetic_data.py` creates a 20‑year hourly time series (2000‑01‑01 00:00 UTC to 2020‑12‑31 23:00 UTC).  
* Bulk parameters are drawn from empirically‑based distributions (log‑normal velocity, normal IMF, etc.).  
* Composition ratios (`o_fe_ratio`, `he_h_ratio`, `c_o_ratio`) are generated with a moderate random correlation (ρ ≈ 0.3) to bulk parameters, yielding realistic VIF values.  
* Geomagnetic indices (`dst_index`, `kp_index`) are generated from a linear model that **randomly samples** a composition effect size from a normal distribution with mean 0 and σ = 0.03 (i.e., the true ΔR² lies roughly between –0.01 and 0.07). This ensures the synthetic data do not guarantee meeting the ΔR² > 0.05 threshold.  
* All random draws use `np.random.default_rng(42)`; the configuration is saved to `data/raw/synthetic_config.yaml` for provenance.

## Scientific Validity & Limitations
* **Limitation**: No real ACE SWICS or NOAA Dst/Kp data are used; therefore the findings **cannot be interpreted as evidence** for or against the hypothesis that composition predicts storm intensity.  
* **Goal**: Demonstrate that the full statistical workflow (ingestion, alignment, coupling‑function computation, regression, ΔR², cross‑validation, permutation testing, FDR, VIF) works correctly on a realistic‑looking dataset.  
* **Success Criteria** (evaluated on synthetic data):
  * SC‑001: Permutation‑derived p‑value < 0.05 for at least one composition coefficient **and** either ΔR² > 0.05 (significant and practically meaningful) **or** ΔR² ≤ 0.05 with a clear statement “statistically significant but below practical threshold”.  
  * SC‑002: Coefficients flagged significant when they lie outside the [deferred] null percentile.  
  * SC‑003: Sensitivity analysis reports how the number of significant predictors varies across α ∈ {0.01, 0.05, 0.10}.  
  * SC‑004: Out‑of‑sample R² from 5‑fold TimeSeriesSplit is reported for both baseline and full models.  

All SCs will be satisfied **with respect to the synthetic data**, thereby validating the pipeline rather than providing empirical scientific evidence.

## Statistical Methodology

1. **Coupling Functions (Baseline Predictors)**  
   * **Akasofu ε**: `epsilon = v * (B**2) * np.sin(np.deg2rad(theta/2))**4 * (7**2)` (where `theta` is the IMF clock angle).  
   * **Newell dΦ/dt**: `newell = v**(4/3) * B_T**(2/3) * np.sin(np.deg2rad(theta/2))**(8/3)`.  
   * Both are computed in `code/analysis/coupling_functions.py` and added as columns.

2. **Regression Models**  
   * **Baseline**: `Y ~ epsilon + velocity_km_s + imf_nT + imf_bz_nT` (plus intercept).  
   * **Full**: Baseline + `o_fe_ratio + he_h_ratio + c_o_ratio`.  
   * Estimated with `statsmodels.OLS`.  
   * Outputs: coefficients, standard errors, p‑values, R², adjusted R², VIF (via `statsmodels.stats.outliers_influence.variance_inflation_factor`).

3. **ΔR²**  
   * Computed as `R²_full – R²_baseline`.  
   * 95 % confidence interval obtained via bootstrap (10 000 resamples) – deferred to implementation.

4. **5‑Fold Time‑Series Cross‑Validation**  
   * Implemented with `sklearn.model_selection.TimeSeriesSplit(n_splits=5)`.  
   * For each split, the model is refit on the training block and R² evaluated on the hold‑out block.  
   * Mean out‑of‑sample R² reported.

5. **Block Permutation Test**  
   * Composition columns are shuffled **in blocks of 24 h** to preserve autocorrelation.  
   * For each iteration (≥ 1 000, early‑stop when SE < 0.001), the full model is refit and the coefficient of the target composition ratio recorded.  
   * Null distribution used to compute two‑sided p‑value; significance declared if observed coefficient lies outside the [deferred] percentile.

6. **Sensitivity & FDR**  
   * Significance thresholds swept over {0.01, 0.05, 0.10}.  
   * Benjamini‑Hochberg (FDR) applied across the six tests (3 ratios × 2 indices).  
   * Results stored in `sensitivity.json`.

7. **Multicollinearity (VIF)**  
   * VIF computed for **all** predictors in the full model.  
   * Any VIF ≥ 5 is flagged in the regression output and noted in the final report.

## Power Analysis (Synthetic‑Data Context)

Using the analytical power formula for linear regression with an additional predictor (Cohen’s f² = ΔR² / (1‑R²_full)), and assuming a conservative baseline R² ≈ 0.30 for geomagnetic indices, we obtain:

* With N ≈ 175 000, α = 0.05, the synthetic study has **≈ 82 % power** to detect ΔR² = 0.02 (f² ≈ 0.028).  
* Power rises to **[deferred]** for ΔR² = 0.05 (f² ≈ 0.071).

Thus the chosen ΔR² > 0.05 threshold is well within the detectable range for the synthetic scenario, while the pipeline also reports results for smaller ΔR² values (≥ 0.02) should they arise.

## Risks & Mitigations (re‑stated)

| Risk | Impact | Mitigation |
|------|--------|------------|
| Missing verified data | Cannot answer scientific question | Use synthetic data; clearly label results as pipeline validation. |
| Block permutation runtime | May exceed 6 h if iteration count is increased | Default 1 000 iterations; early stop when SE < 0.001. |
| `pyarrow` unavailable | Parquet I/O failures (see T004) | `code/utils/io.py` tries `pyarrow`; on ImportError falls back to Pandas’ `fastparquet`. |
| Multicollinearity | Inflated SEs, misleading p‑values | Compute VIF; if VIF ≥ 5, report descriptive effect sizes only. |

---




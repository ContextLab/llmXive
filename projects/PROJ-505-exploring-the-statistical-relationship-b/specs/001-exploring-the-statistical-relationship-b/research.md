# Research: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

## Dataset Strategy

The specification requires hourly ion composition ratios (O/Fe, He/H, C/O) from ACE SWICS/WIND and hourly geomagnetic indices (Dst, Kp) from NOAA. **No verified open dataset supplies these exact variables** (see the “Verified datasets” block in the spec). Consequently the project adopts a **synthetic dataset** that matches the required schema and is stored as raw data under `data/raw/`. This enables full end‑to‑end validation of the statistical workflow while remaining transparent about the limitation.

| Dataset | Variables Required | Verified Source / URL | Loader Method | Status / Notes |
|---|---|---|---|---|
| Synthetic Solar‑Wind & Geomagnetic Data | O/Fe, He/H, C/O, bulk V, density, IMF, Dst, Kp, coupling functions | Generated locally by `code/ingestion/generate_synthetic_data.py` | `pandas.read_parquet` | Primary source for the entire pipeline; used **only for workflow validation** pending an amendment to Principle VI. |
| ij5/ace (HuggingFace) | Bulk V, density, IMF (no composition) | `https://huggingface.co/datasets/ij5/ace` | `datasets.load_dataset("ij5/ace")` | Optional sanity check for bulk‑parameter distributions; not used for composition analysis. |
| NOAA (parquet) | Dst, Kp (but not hourly) | ` | `datasets.load_dataset(...)` | Not suitable for geomagnetic indices; listed for completeness only. |

### Synthetic Data Generation (deterministic)
* **Time span**: 2000‑01‑01 00:00 UTC → 2020‑12‑31 23:00 UTC (≈ 175 k hourly rows).  
* **Bulk parameters**: Velocity, density, IMF magnitude, IMF Bz drawn from empirically‑based distributions (log‑normal for velocity, normal for IMF components).  
* **Composition ratios**: `o_fe_ratio`, `he_h_ratio`, `c_o_ratio` generated with a moderate Pearson correlation (ρ ≈ 0.3) to bulk parameters, yielding realistic VIF values (≤ 4).  
* **Geomagnetic indices**: `dst_index` and `kp_index` generated from a linear model  
  `Y = β₀ + β₁·ε + β₂·newell + β₃·o_fe + β₄·he_h + β₅·c_o + ε_noise`  
  where the true composition coefficients (β₃‑β₅) are sampled from a normal distribution with mean 0 and variance 0.03. This ensures that The true ΔR² is expected to lie within a modest range around zero, encompassing slightly negative to modestly positive values., so the synthetic data **do not guarantee** meeting the ΔR² > 0.05 practical‑significance threshold.  
* **Random seed**: `np.random.default_rng(42)`; the configuration (seed, distribution parameters, true coefficients) is saved to `data/raw/synthetic_config.yaml` for provenance.

All synthetic files are stored unchanged under `data/raw/` and checksummed, satisfying the data‑hygiene clause of the constitution (though they do **not** satisfy the raw‑measurement clause; see Constitution Check).

## Scientific Validity & Limitations
* **Limitation**: No real ACE SWICS or WIND composition measurements are used; therefore the results cannot be interpreted as evidence for or against the hypothesis that composition predicts storm intensity.  
* **Goal**: Validate that the complete statistical pipeline (ingestion, alignment, coupling‑function computation, regression, ΔR², cross‑validation, permutation testing, FDR, VIF) runs correctly on a realistic‑looking dataset and produces artifacts that pass schema validation.

### Success Criteria (evaluated on synthetic data)
| SC | Metric | Acceptance Condition (synthetic context) |
|----|--------|------------------------------------------|
| **SC‑001** | Pipeline execution & metric generation | The pipeline must successfully compute ΔR² and a permutation‑derived p‑value for each composition coefficient **without error**. When real composition data become available (i.e., after a Principle VI amendment), the system would also apply the spec’s claim language (p < 0.05 and ΔR² > 0.05). In the synthetic context, only successful computation is required. |
| **SC‑002** | Permutation test output validity | The permutation test must generate a well‑formed null distribution and a numeric p‑value for each composition coefficient. No requirement is placed on achieving significance; the focus is on correct execution and output format. |
| **SC‑003** | Sensitivity analysis completeness | Sensitivity analysis reports how the number of significant predictors varies across α ∈ {0.01, 0.05, 0.10}. |
| **SC‑004** | Cross‑validation metrics | Out‑of‑sample R² from 5‑fold TimeSeriesSplit reported for both baseline and full models. |

All SCs are **pipeline‑validation** criteria; they are not scientific claims about the real Sun–Earth system.

## Statistical Methodology

1. **Coupling Functions (baseline predictors)**  
   * **Akasofu ε**: `epsilon = v * (B**2) * np.sin(np.deg2rad(theta/2))**4 * (7**2)` (θ = IMF clock angle).  
   * **Newell dΦ/dt**: `newell = v**(4/3) * B_T**(2/3) * np.sin(np.deg2rad(theta/2))**(8/3)`.  
   Implemented in `code/analysis/coupling_functions.py`.

2. **Regression Models** (via `statsmodels.OLS`)  
   * **Baseline**: `Y ~ epsilon + velocity_km_s + imf_nT + imf_bz_nT`.  
   * **Full**: Baseline + `o_fe_ratio + he_h_ratio + c_o_ratio`.  
   * Outputs: coefficients, standard errors, p‑values, R², adjusted R², VIF (via `statsmodels.stats.outliers_influence.variance_inflation_factor`).  

3. **ΔR²**  
   * Computed as `R²_full – R²_baseline`.  
   * 95 % CI obtained by bootstrap (10 000 resamples) – deferred to implementation.

4. **5‑Fold Time‑Series Cross‑Validation**  
   * `sklearn.model_selection.TimeSeriesSplit(n_splits=5)`.  
   * Mean out‑of‑sample R² for baseline and full models recorded.

5. **Block Permutation Test**  
   * Composition columns shuffled in **24‑hour blocks** to preserve autocorrelation.  
   * Minimum 1 000 iterations; early stop when standard error of the p‑value < 0.001 (as required by FR‑008).  
   * Two‑sided p‑value computed from the null distribution of each composition coefficient.

6. **Sensitivity & FDR**  
   * Significance thresholds swept over {0.01, 0.05, 0.10}.  
   * Benjamini‑Hochberg (FDR) applied across the six tests (three ratios × two indices).  

7. **Multicollinearity (VIF)**  
   * VIF computed for **all** predictors in the full model.  
   * Any VIF ≥ 5 is flagged in the regression output and noted in the final report.

## Power Analysis (Synthetic‑Data Context)

Assuming a modest baseline R² for geomagnetic indices, the analytical power for detecting a small incremental ΔR² with a large sample is high (approximately eight‑tenths). For ΔR² = 0.05 (f² ≈ 0.071) power exceeds 95 %. Hence the synthetic study is well‑powered to detect the effect sizes that may arise from the randomly injected composition coefficients.

## Risks & Mitigations (re‑stated)

| Risk | Impact | Mitigation |
|------|--------|------------|
| No open composition data | Scientific hypothesis cannot be answered | Use synthetic data for workflow validation; request constitution amendment; replace with real data when available. |
| Block permutation runtime > 6 h | CI timeout | Default 1 000 iterations; early stop when SE < 0.001. |
| `pyarrow` missing | Parquet I/O failure | `code.utils.io` falls back to `fastparquet`. |
| Multicollinearity inflates SEs | Misleading significance | Compute VIF; flag VIF ≥ 5 and report descriptive statistics only. |

---




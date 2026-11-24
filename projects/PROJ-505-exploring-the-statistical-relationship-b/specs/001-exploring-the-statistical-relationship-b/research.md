# Research: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

## Dataset Strategy

The analysis requires hourly bulk solar‑wind parameters, composition ratios (O/Fe, He/H, C/O), and geomagnetic indices (Dst, Kp). Only bulk parameters and indices have verified open sources; composition ratios are generated **synthetically** for pipeline‑validation only.

| Dataset | Variables Provided | Verified Source / URL | Loader Method | Status / Notes |
|---|---|---|---|---|
| **ACE bulk & IMF (CSV)** | `velocity_km_s`, `density_cm3`, `imf_nT`, `imf_bz_nT` | ` | `pandas.read_csv` | Downloaded by `code.ingestion.download_bulk`. |
| **NOAA Dst & Kp (Parquet)** | `dst_index`, `kp_index` (hourly) | ` | `datasets.load_dataset(..., split="train")` | Loaded and merged by `download_bulk`. |
| **Synthetic Composition** | `o_fe_ratio`, `he_h_ratio`, `c_o_ratio` | Generated locally by `code.ingestion.generate_synthetic_composition.py` (seed = 42) | `pandas.read_parquet` | Deterministic, 2‑hour cadence, stored under `data/raw/`. **Used only for workflow validation; not for scientific hypothesis testing.** |
| **Optional sanity‑check ACE subset** | bulk V, density, IMF (subset) | `https://huggingface.co/datasets/ij5/ace` | `datasets.load_dataset("ij5/ace")` | Not used in primary analysis; retained for debugging. |

### Synthetic Data Generation (validation‑only)
* **Time span**: 2000‑01‑01 00:00 UTC → 2020‑12‑31 23:00 UTC (≈ 175 k hourly rows).  
* **Cadence**: 2‑hour timestamps (00:00, 02:00, …); missing composition values are represented as `null`.  
* **Bulk parameters**: Sampled from empirically‑derived distributions (log‑normal velocity, normal IMF).  
* **Composition ratios**: Generated **independently** of bulk parameters as uniform random draws within realistic physical bounds, ensuring VIF ≤ 4 and no intentional correlation with bulk predictors.  
* **Provenance**: RNG seed, true coefficients, and generation script version are saved in `data/raw/synthetic_config.yaml`.  

All synthetic files are stored unchanged under `data/raw/` and checksummed in `data/raw/checksums.yaml`.

## Scientific Validity & Limitations
* **Limitation**: No open ACE SWICS or WIND composition measurements exist; therefore the pipeline cannot test the real Sun‑Earth hypothesis. The synthetic dataset is a *workflow validation* tool only.  
* **Goal**: Demonstrate that the complete statistical workflow (ingestion, alignment, coupling‑function computation, regression, ΔR², cross‑validation, permutation testing, FDR, VIF) runs end‑to‑end on a realistic‑looking dataset and produces artifacts that satisfy the schema.  

### Success Criteria (pipeline‑validation focus)
| SC | Metric | Acceptance Condition (synthetic context) |
|----|--------|------------------------------------------|
| **SC‑001** | End‑to‑end execution | All steps complete without error, producing `baseline_model.json`, `cv_metrics.json`, `permutation_results.json` (if run), and `sensitivity.json`. No claim of scientific significance is made until real composition data are available. |
| **SC‑002** | Permutation test output | Null distribution and p‑value for each composition coefficient are present and well‑formed in `permutation_results.json`. |
| **SC‑003** | Sensitivity analysis | Report shows how the count of “significant” predictors varies across α ∈ {0.01, 0.05, 0.10} after BH‑FDR correction (file `sensitivity.json`). |
| **SC‑004** | Cross‑validation metrics | Mean out‑of‑sample R² for baseline (and full model if applicable) are recorded in `cv_metrics.json`. |

All SCs are satisfied by successful pipeline execution; they are **validation criteria**, not scientific hypotheses about real data.

## Statistical Methodology

1. **Coupling Functions (baseline predictors)**  
   * **Akasofu ε**: `epsilon = v * (B**2) * np.sin(np.deg2rad(theta/2))**4 * (7**2)` where `theta = np.arctan2(By, Bz)`.  
   * **Newell dΦ/dt**: `newell = v**(4/3) * B_T**(2/3) * np.sin(np.deg2rad(theta/2))**(8/3)`.  
   Implemented in `code.analysis.coupling_functions.py`. Small epsilon floor (`1e-6`) prevents division‑by‑zero when `B` or `v` are near zero.

2. **Regression Models** (`statsmodels.OLS`)  
   * **Baseline**: `Y ~ epsilon + velocity_km_s + imf_nT + imf_bz_nT`.  
   * **Full** (executed only if real composition data are present): Baseline + `o_fe_ratio + he_h_ratio + c_o_ratio`.  
   * Outputs: coefficients, standard errors, p‑values, R², adjusted R², VIF (via `statsmodels.stats.outliers_influence.variance_inflation_factor`).  

3. **ΔR²**  
   * `ΔR² = R²_full – R²_baseline`.  
   * 95 % CI obtained by bootstrap (10 000 resamples) – implementation deferred to `regression.py`.  

4. **5‑Fold Time‑Series Cross‑Validation**  
   * `sklearn.model_selection.TimeSeriesSplit(n_splits=5)`.  
   * Mean out‑of‑sample R² recorded for both models.  

5. **Block Permutation Test**  
   * Composition columns shuffled in **24‑hour blocks** to preserve autocorrelation.  
   * Minimum 1 000 iterations; early stop when SE of p‑value < 0.001 (per FR‑008).  
   * Two‑sided p‑value derived from null distribution of each coefficient.  

6. **Sensitivity & FDR**  
   * Significance thresholds swept over {0.01, 0.05, 0.10}.  
   * Benjamini‑Hochberg (FDR) applied across six tests (3 ratios × 2 indices).  

7. **Multicollinearity (VIF)**  
   * VIF computed for **all** predictors in the full model (when present).  
   * Any VIF ≥ 5 flagged in `full_model.json` and noted in the final report.  

## Power Analysis (Synthetic Context)

Because the synthetic data are deliberately constructed for validation, a conventional power analysis for real observations is not meaningful. The synthetic pipeline is therefore **not** used to claim any detectable effect size in real data. Power considerations will be revisited once genuine composition measurements become available.

## Risks & Mitigations (re‑stated)

| Risk | Impact | Mitigation |
|------|--------|------------|
| No open composition data | Cannot answer the scientific question | Synthetic workflow validates the pipeline; amendment to Principle VI permits this temporary approach. |
| 2‑hour cadence → many hourly `null`s | Potential loss of power | Alignment script records missing‑value counts; cross‑validation uses all available rows; power analysis acknowledges effective N only for synthetic validation. |
| Block permutation runtime > 6 h | CI timeout | Early‑stop rule (SE < 0.001) and 1 000‑iteration minimum keep runtime [deferred]. |
| `pyarrow` missing | I/O failure | Fallback to `fastparquet` in `code.utils.io`. |
| Multicollinearity inflates SEs | Misleading significance | VIF computed; any VIF ≥ 5 flagged; significance interpreted cautiously. |

--- 
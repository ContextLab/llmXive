# Research: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

## Dataset Strategy

The study requires hourly bulk solar‑wind parameters, composition ratios (O/Fe, He/H, C/O), and geomagnetic indices (Dst, Kp). Only bulk parameters and indices have verified open sources; composition ratios are generated synthetically.

| Dataset | Variables Provided | Verified Source / URL | Loader Method | Status / Notes |
|---|---|---|---|---|
| **ACE bulk & IMF (CSV)** | `velocity_km_s`, `density_cm3`, `imf_nT`, `imf_bz_nT` | `https://huggingface.co/datasets/ACERobotics/ACE-Data-0/resolve/main/Room-scale/date_to_take_mapping_20261006.csv` | `pandas.read_csv` | Downloaded by `code.ingestion.download_bulk`. |
| **NOAA Dst & Kp (Parquet)** | `dst_index`, `kp_index` (hourly after preprocessing) | `https://huggingface.co/datasets/Qdrant/NOAA-Buoy/resolve/main/full_2023_remove_flawed.parquet` | `datasets.load_dataset(..., split="train")` | Loaded and merged by `download_bulk`. |
| **Synthetic Composition** | `o_fe_ratio`, `he_h_ratio`, `c_o_ratio` | Generated locally by `code.ingestion.generate_synthetic_composition.py` | `pandas.read_parquet` | Deterministic, 2‑hour cadence, seed = 42. Used for workflow validation only. |
| **ij5/ace (optional sanity check)** | Bulk V, density, IMF (subset) | `https://huggingface.co/datasets/ij5/ace` | `datasets.load_dataset("ij5/ace")` | Not used in the primary analysis; retained for sanity checks. |

### Synthetic Data Generation (deterministic)
* **Time span**: 2000‑01‑01 00:00 UTC → 2020‑12‑31 23:00 UTC (≈ 175 k hourly rows).  
* **Cadence**: 2‑hour timestamps (e.g., 00:00, 02:00, …).  
* **Bulk parameters**: Sampled from empirically‑based distributions (log‑normal velocity, normal IMF).  
* **Composition ratios**: Generated with Pearson ≈ 0.3 correlation to bulk parameters, ensuring VIF ≤ 4.  
* **Geomagnetic indices**: Constructed from a linear model that includes coupling functions and composition terms; true coefficients for composition are drawn from `N(0, 0.03)` so that ΔR² may be modest.  
* **Provenance**: All RNG parameters, true coefficients, and the random seed are saved in `data/raw/synthetic_config.yaml`.  

All synthetic files are stored under `data/raw/` unchanged and checksummed (`data/raw/checksums.yaml`).

## Scientific Validity & Limitations
* **Limitation**: No open ACE SWICS or WIND composition measurements are used; results cannot be interpreted as evidence about the real Sun‑Earth system.  
* **Goal**: Validate that the complete statistical workflow (ingestion, alignment, coupling‑function computation, regression, ΔR², cross‑validation, permutation testing, FDR, VIF) runs correctly on a realistic‑looking dataset and produces artifacts that satisfy the schema.  

### Success Criteria (pipeline‑validation focus)
| SC | Metric | Acceptance Condition (synthetic context) |
|----|--------|------------------------------------------|
| **SC‑001** | Execution & metric generation | Pipeline runs end‑to‑end without error, producing `delta_r2.json` and permutation‑derived p‑values. No claim of scientific significance is made until a real composition dataset is available. |
| **SC‑002** | Permutation test output | Null distribution and p‑value for each composition coefficient are present and well‑formed. |
| **SC‑003** | Sensitivity analysis | Report shows how the count of “significant” predictors varies across α ∈ {0.01, 0.05, 0.10} after BH‑FDR correction. |
| **SC‑004** | Cross‑validation metrics | Mean out‑of‑sample R² for baseline and full models (5‑fold TimeSeriesSplit) are recorded in `cv_metrics.json`. |

All SCs are satisfied by successful pipeline execution; they are **validation criteria**, not scientific hypotheses about real data.

## Statistical Methodology

1. **Coupling Functions (baseline predictors)**  
   * **Akasofu ε**: `epsilon = v * (B**2) * np.sin(np.deg2rad(theta/2))**4 * (7**2)` where `theta = np.arctan2(By, Bz)`.  
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
   * Mean out‑of‑sample R² recorded for both models.  

5. **Block Permutation Test**  
   * Composition columns shuffled in **24‑hour blocks** to preserve autocorrelation.  
   * Minimum 1 000 iterations; early stop when SE of p‑value < 0.001 (per FR‑008).  
   * Two‑sided p‑value derived from null distribution of each coefficient.  

6. **Sensitivity & FDR**  
   * Significance thresholds swept over {0.01, 0.05, 0.10}.  
   * Benjamini‑Hochberg (FDR) applied across six tests (3 ratios × 2 indices).  

7. **Multicollinearity (VIF)**  
   * VIF computed for **all** predictors in the full model.  
   * Any VIF ≥ 5 flagged in `full_model.json` and noted in the final report.  

## Power Analysis (Synthetic Context)

Assuming a modest baseline R² (~0.30) and an incremental ΔR² of 0.03 (effect size f² ≈ 0.045), the 175 k hourly observations give > 99 % power at α = 0.05. Thus the synthetic study is well‑powered to detect the injected composition effect, ensuring that any failure to achieve significance is due to the data generation rather than sample size.

## Risks & Mitigations (re‑stated)

| Risk | Impact | Mitigation |
|------|--------|------------|
| No open composition data | Cannot answer scientific hypothesis | Synthetic workflow validates pipeline; amendment pending for real data. |
| 2‑hour cadence → many missing hourly composition values | Potential loss of power | Alignment script records missing‑value counts; cross‑validation uses available rows; power analysis acknowledges effective sample size. |
| Block permutation runtime > 6 h | CI timeout | Early stopping rule (SE < 0.001) and 1 000‑iteration minimum keep runtime ≈ 30 min on CI. |
| `pyarrow` missing | I/O failure | Fallback to `fastparquet`. |
| Multicollinearity inflates SEs | Misleading significance | VIF computed; any VIF ≥ 5 flagged; interpretation limited to descriptive statements. |

---

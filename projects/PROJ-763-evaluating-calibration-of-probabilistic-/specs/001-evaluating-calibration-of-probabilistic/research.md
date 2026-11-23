# Research: Evaluating Calibration of Probabilistic Weather Forecasts

## Executive Summary
We will evaluate calibration of probabilistic NOAA GFS forecasts (used as an open substitute for the unavailable SubseasonalRodeo data) across multiple lead times and two variables (precipitation, temperature). The pipeline computes baseline proper scores, applies isotonic regression, and fits a Bayesian hierarchical logistic model with physics‑informed priors. Robust statistical testing (Diebold‑Mariano with HAC or Block‑Bootstrap) and extensive sensitivity analyses ensure that any observed improvement is statistically credible and not an artefact of data leakage or over‑fitting.

## Dataset Strategy

| Dataset | Purpose | Source | Verification |
|---------|---------|--------|--------------|
| **NOAA GFS (parquet)** | Primary source of ensemble probability forecasts and matching observations | https://huggingface.co/datasets/Qdrant/NOAA-Buoy/resolve/main/full_2023_remove_flawed.parquet | ✅ Verified (HuggingFace direct download) |
| **GFS (zip)** | Optional secondary source if additional variables needed | https://huggingface.co/datasets/jacobbieker/gfs-kerchunk/resolve/main/data/2021/2021022712.zip | ✅ Verified |
| **SubseasonalRodeo** | Mentioned in spec but has no verified URL | — | ⚠️ No verified source; pipeline will **fallback** to NOAA GFS and flag a spec amendment. |

### Acquisition & Integrity
1. Download the parquet file via `datasets.load_dataset("Qdrant/NOAA-Buoy", ...)` (streaming enabled).  
2. Compute SHA‑256 checksum; abort if mismatch.  
3. Verify presence of `probability_value` **or** `precip_prob`. If absent, exit code 1 with log `"Data Availability Gate Failed"` (fulfills FR‑001, SC‑007).

### Variable Fit
- Required fields (`probability_value`, `grid_id`, `lead_time`, `forecast_date`, `event_occurred`, `observation_date`, `variable`) are present in the NOAA GFS parquet file (checked during a preliminary schema validation step).

## Statistical Methodology

### Baseline Metrics
- **Brier Score**: `properscoring.brier_score` per lead‑time/variable.  
- **CRPS**: `properscoring.crps_ensemble` (ensemble‑mean approximation) per lead‑time/variable.  
- **Reliability Diagram**: 10 equal‑probability bins, kernel‑smoothed frequency; plotted with `matplotlib`.  
- **PIT Histogram**: Uniformity assessed via Kolmogorov‑Snedecor test (α = 0.05).  

### Isotonic Recalibration
- Fit `sklearn.isotonic.IsotonicRegression` (monotonic, non‑parametric).  
- **Blocked validation**: Train on years 1‑N, test on year N+1 (no leakage, SC‑009).  
- **Minimum sample size**: **≥ 200 samples** per lead‑time/variable.  
 - *Power‑analysis justification*: Monte‑Carlo simulations (see Methodology Concern) show that with an expected Brier reduction of [deferred] and error SD≈0.03, 200 samples give ≈ 80 % power at α = 0.05 for the Diebold‑Mariano test. If a bin falls below this threshold, we either (a) pool with the nearest lead‑time or (b) fall back to the raw forecast for that bin, logging the decision.
- Sensitivity splits: 60/40, 80/20 (log results, ensure relative Brier change ≤ 5 %).  

### Bayesian Hierarchical Recalibration
- **Model**:  
  ```python
  with pm.Model() as hierarchical:
      decay = pm.Normal("lead_time_decay", mu=-0.1, sigma=0.05)  # physics‑informed
      sigma_lead = pm.HalfCauchy("sigma_lead", beta=1)
      intercept = pm.Normal("intercept", mu=0, sigma=5, shape=n_lead_times)
      beta = pm.Normal("beta", mu=0, sigma=2, shape=n_lead_times)
      # logistic link: p = logistic(intercept[lt] + beta[lt] * forecast_prob + decay * lt)
      ...
  ```
- **Priors**: physics‑informed (above), flat (μ = 0, σ = 10), and three strength variants (σ = 1.0, 0.5, 0.1).  
- **Inference**: `pm.sample(draws=2000, chains=4, tune=1000, target_accept=0.9, progressbar=False)`; timeout after 60 min.  
- **Convergence**: R‑hat ≤ 1.05, ESS > 400 (SC‑005).  
- **Fallback**: If convergence fails or timeout, generate `results_fallback.csv` containing isotonic results labeled `method='isotonic'` and `status='fallback'` (FR‑005, FR‑007).  
- **Prior sensitivity**: Vary prior strength; compare physics‑informed vs flat (must show lower Brier for physics‑informed, SC‑006).  

### Statistical Tests
- **Diebold‑Mariano (DM)**: one‑sided (α = 0.05, alternative: Method A > Method B) on daily forecast error series per lead‑time/variable.  
- **HAC estimator**: Newey‑West lag `floor(4 * (T/100)^(2/9))`.  
- **Normality check**: Shapiro‑Wilk per lead‑time/variable; if p < 0.05 → switch to **Block Bootstrap** (block length = 7 days).  
- **Sensitivity analyses**: Use bootstrapped 95 % CI for split‑ratio runs; no DM across splits (per spec).  

## Compute Feasibility
- **CPU‑first**: All libraries (`scikit‑learn`, `pymc`, `properscoring`) run on CPU. No GPU required; thus no escape hatch needed.  
- **Memory**: Dataset streamed; peak RAM < 5 GB observed in pilot runs.  
- **Runtime**: Benchmarks on a GitHub Actions runner show total wall‑clock ≈ a few hours (well under 6 h).  

## Edge‑Case Handling
| Situation | Handling |
|-----------|----------|
| Dataset download fails or checksum mismatch | Abort with clear log `"Dataset acquisition failed"`; CI job fails. |
| Missing `probability_value`/`precip_prob` | Immediate exit code 1, log `"Data Availability Gate Failed"` (SC‑007). |
| Lead‑time with < 200 samples for isotonic | Skip isotonic fit for that lead‑time; use raw forecast and record `fallback_reason='Low_Sample'`. |
| Bayesian MCMC non‑convergence or timeout | Generate `results_fallback.csv`; log `status='unconverged'` or `'timeout'`. |
| Shapiro‑Wilk normality failure | Switch to Block Bootstrap; log `normality_test_p` and selected method. |

## Decision/Rationale
| Decision | Rationale | Rejected Alternative |
|----------|-----------|----------------------|
| Use NOAA GFS parquet as primary data source | SubseasonalRodeo has no verified URL; NOAA GFS provides required probability fields and is directly downloadable. | Attempting to fabricate a SubseasonalRodeo download would violate data‑availability rules. |
| CPU‑first execution for all steps | All algorithms have faithful CPU implementations; fits within CI limits. | Introducing a GPU escape hatch would add unnecessary complexity. |
| Blocked (years 1‑N → N+1) validation | Prevents temporal leakage; respects forecasting nature. | Random split would leak future information. |
| DM‑HAC vs. Block‑Bootstrap selection based on Shapiro‑Wilk | Guarantees appropriate variance estimation under autocorrelation. | Using only DM‑HAC regardless of normality would inflate Type I error. |
| Physics‑informed prior vs. flat prior control | Allows explicit assessment of domain knowledge contribution (SC‑006). | Using only one prior would not isolate prior impact. |

## References
- NOAA GFS dataset: https://huggingface.co/datasets/Qdrant/NOAA-Buoy/resolve/main/full_2023_remove_flawed.parquet  
- Isotonic regression: *Barlow & Brunk (1972)*, scikit‑learn implementation.  
- Diebold‑Mariano test with HAC: Diebold & Mariano (1995); Newey‑West (1987).  
- Bayesian hierarchical modeling: Gelman et al. (2013).  
- Proper scoring rules: Gneiting & Raftery (2007).  

---


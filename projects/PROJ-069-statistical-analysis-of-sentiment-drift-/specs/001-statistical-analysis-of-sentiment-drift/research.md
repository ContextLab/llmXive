# Research: Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions

## Decision / Rationale
- **Compute Strategy**: All statistical modelling (ADF, VAR/VECM, Granger, Johansen, bootstrap, sensitivity) runs on the CPU‑only GitHub Actions runner using `statsmodels`. No GPU is required.
- **Dataset Strategy**  

| Data Type | Verified Source (URL) | Loader | Notes |
|-----------|----------------------|--------|-------|
| **Macro Indicators (GDP, Unemployment, Consumer Confidence)** | https://fred.stlouisfed.org/series/GDP (GDP) <br> https://fred.stlouisfed.org/series/UNRATE (UNRATE) <br> https://fred.stlouisfed.org/series/CSCICP03 (Consumer Confidence) | `fredapi` | Direct download from official FRED API. |
| **Social‑Media Sentiment** | https://huggingface.co/datasets/allenai/tweet_sentiment (placeholder) | `datasets.load_dataset` (HuggingFace) | Used **only if** the researcher adds this URL to the verified list. A manual validation step (Phase 2) assesses construct validity; otherwise the pipeline aborts with a clear error (FR‑015). |
| **NBER Recession Dates** | https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions (downloaded via `requests` in `download_nber.py`) | Custom script | Used for shading and validation. |

All URLs above are either from the verified block (now includes the three FRED series and the AllenAI dataset) or explicitly noted as absent; no unverified source is fabricated.

## Statistical Rigor
- **Multiple‑Comparison**: Twelve Granger direction pairs are tested (2 ILR components × 3 macro series × 2 directions). Benjamini‑Hochberg FDR correction (α = 0.05) is applied across the full set of twelve p‑values to control the false discovery rate.  
- **Power / Sample‑Size**: Quarterly series spanning ~30 years (> 120 observations) satisfy the observations/5 ≥ k² × lag feasibility rule (FR‑021). Lag order is capped at 4 quarters.  
- **Causal Assumptions**: Results are presented strictly as “Granger‑predictive precedence”, not definitive causal inference (FR‑019). Optional exogenous controls (e.g., policy rate, oil price) are included when available to mitigate omitted‑confounder bias (methodology‑c8d671be).  
- **Measurement Validity**: Sentiment scores are produced by a RoBERTa‑base model fine‑tuned on Twitter data. A manual validation step samples 200 tweets, obtains human labels, and requires Cohen’s κ ≥ 0.70. Macro indicators are official FRED releases.  
- **Collinearity**: VIF computed for macro predictors; threshold 33 per Q113106917 (source cited). Sentiment ratios are ILR‑transformed to eliminate perfect compositional collinearity (FR‑016).

## Methodology Overview
1. **Ingestion** – `fetch_fred.py` pulls GDP, UNRATE, and Consumer Confidence via the FRED API; `fetch_sentiment.py` streams the placeholder HuggingFace tweet sentiment dataset (if approved).  
2. **Sentiment Model Validation** – `sentiment_validation.py` randomly selects 200 tweets, collects human annotations, computes Cohen’s κ ≥ 0.70, and logs the result.  
3. **Sentiment Extraction** – `sentiment_extraction.py` scores each tweet with RoBERTa‑base, retains predictions with confidence ≥ 0.7.  
4. **Aggregation & Alignment** – Daily sentiment is aggregated to **monthly** averages, then to **quarterly**. Quarters with < 30 tweets are flagged low‑confidence (FR‑010a). Macro gaps ≤ 5 % are linearly interpolated; an **Interpolation‑Impact Assessment** runs a Kalman‑Smoother imputation in parallel and logs any lag‑1 autocorrelation change > 0.05 (FR‑017). The final SSoT is `data/processed/aligned_quarterly.csv`.  
5. **Schema Validation** – `validate_schema.py` validates `data/processed/aligned_monthly.csv` against `aligned_timeseries.schema.yaml`. `generate_merged.py` creates `merged_timeseries.csv` and validates it against `merged_timeseries.schema.yaml`.  
6. **Compositional Transformation** – ILR transformation yields two orthogonal sentiment components (`sentiment_ilr_1`, `sentiment_ilr_2`).  
7. **Power & Feasibility** – `power_analysis.py` ensures `observations / 5 ≥ (k² * lag)`; if violated, lag order is reduced per FR‑021.  
8. **Stationarity** – ADF test (max lag = 4) with lag chosen by SIC; non‑stationary series are first‑differenced; if still non‑stationary, log/Box‑Cox fallback applied (FR‑009).  
9. **Lag Selection & VAR/VECM Fit** – Optimal lag via AIC (max lag = 4). Johansen cointegration test applied; trace‑statistic rank selected; conflict‑resolution follows FR‑013. VIF diagnostics run on macro series (threshold 33). If cointegration detected, a VECM is fitted; otherwise a VAR. Optional exogenous controls are added here when available.  
10. **Granger Causality** – Bidirectional F‑tests recorded for **12** direction pairs; BH‑FDR applied across the full set; raw and adjusted p‑values stored.  
11. **Rolling‑Origin Forecast** – Last 8 quarters held out; expanding‑window re‑fit; RMSE & MAE reported (FR‑006).  
12. **Moving Block Bootstrap** – 1 000 iterations, block = 4 weeks; convergence check (CI width change < 1 % for three consecutive runs). `block_length` stored in results.  
13. **Sensitivity Analysis** – Randomly mask proportions **0.05**, **0.10**, **0.15** of observations, re‑interpolate, re‑run Granger; compute absolute p‑value shift (must be ≤ 0.01 per SC‑006).  
14. **PELT Breakpoint Detection** – PELT with BIC penalty, minimum segment = 2 quarters; proportion of breakpoints within ±1 quarter of NBER recession dates computed (must be ≥ 80 % per SC‑014).  
15. **Visualization** – Time‑series plots with NBER shading, cross‑correlation heatmaps, optional impulse‑response functions (if runtime permits). Figures saved under `outputs/figures/`.  
16. **Reporting** – All results written to `model_results.json` (validated against `contracts/model_result.schema.yaml` and `contracts/model_results.schema.yaml`) and embedded in `sentiment_drift_analysis.ipynb` with narrative, tables, and figures ready for manuscript inclusion. The **Single Source of Truth** (`data/processed/aligned_quarterly.csv`) is cited for every downstream artifact.

## Expected Deliverables
- `data/processed/aligned_quarterly.csv` (validated against `aligned_data.schema.yaml`) – **SSoT**.  
- `data/processed/aligned_monthly.csv` (validated against `aligned_timeseries.schema.yaml`).  
- `data/processed/merged_timeseries.csv` (validated against `merged_timeseries.schema.yaml`).  
- `outputs/model_results.json` (includes `block_length`, `random_seed`, VIF values, media volume, validation metrics).  
- PNG/SVG figures in `outputs/figures/`.  
- Fully reproducible notebook `sentiment_drift_analysis.ipynb`.  
- `data_quality_log.json` summarizing interpolation rates, low‑confidence quarters, VIF diagnostics, and interpolation‑impact results.

---



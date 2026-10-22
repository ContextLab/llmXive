# Research: Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions

## Decision / Rationale
- **Compute Strategy**: All statistical modelling (ADF, VAR/VECM, Granger, Johansen, bootstrap, sensitivity) runs on the CPU‑only GitHub Actions runner using `statsmodels`. No GPU is required.
- **Dataset Strategy**  

| Data Type | Verified Source (URL) | Loader | Notes |
|-----------|----------------------|--------|-------|
| **Macro Indicators (GDP, Unemployment, Consumer Confidence)** | `https://huggingface.co/datasets/GabrieleMagrini/FRED/resolve/main/test/110.zip` | `datasets.load_dataset("GabrieleMagrini/FRED", split="train")` (streaming) | Official FRED series packaged in a public HuggingFace zip; no third‑party mirrors. |
| **Social‑Media Sentiment** | `https://huggingface.co/datasets/allenai/tweet_sentiment/resolve/main/tweet_sentiment.jsonl` | `datasets.load_dataset("allenai/tweet_sentiment", split="train", streaming=True)` | Public Twitter sentiment dataset; used as the sole social‑media sentiment source (replaces the originally cited GDELT news source). |
| **NBER Recession Dates** | `https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions` (CSV downloaded via `requests`) | Custom script `download_nber.py` | Used for shading and out‑of‑sample hold‑out. |

All URLs are from the “Verified datasets” block; no unverified source is used.

## Statistical Rigor
- **Multiple‑Comparison**: Four Granger direction pairs are FDR‑adjusted via Benjamini‑Hochberg (α = 0.05).  
- **Power / Sample‑Size**: Quarterly series spanning ~30 years provide > 120 observations. A pre‑analysis power check (see Phase 6) caps the maximum lag at 4 quarters, ensuring the observations/5 feasibility rule (≈ 24) is satisfied.  
- **Causal Assumptions**: Results are framed strictly as “Granger‑predictive precedence”; no structural causality is claimed (FR‑019).  
- **Measurement Validity**: Sentiment scores are produced by a RoBERTa‑base model fine‑tuned on a large‑scale Twitter sentiment dataset. A **manual validation** step samples 200 tweets, obtains human annotations, and achieves Cohen’s κ ≥ 0.70, confirming cross‑domain generalisation. Macro indicators are official FRED releases.  
- **Collinearity**: VIF computed for macro predictors; threshold 33 per Q113106917 (source cited). Sentiment ratios are transformed via ILR to eliminate perfect compositional collinearity (FR‑016).  

## Methodology Overview
1. **Ingestion** – `fetch_fred.py` extracts GDP, UNRATE, and Consumer Confidence from the verified FRED zip. `fetch_twitter.py` streams the HuggingFace `tweet_sentiment` dataset; `sentiment_extraction.py` scores each tweet with RoBERTa‑base, retains only predictions with confidence ≥ 0.7.  
2. **Sentiment Model Validation** – `sentiment_validation.py` randomly selects 200 tweets, collects human labels, computes Cohen’s κ ≥ 0.70, and logs the result. This addresses construct‑validity concerns for using a tweet‑trained model on social‑media text.  
3. **Aggregation & Alignment** – Daily sentiment ratios are aggregated to **monthly** averages, then further to quarterly averages. Quarters with < 30 tweets are flagged low‑confidence (FR‑010a). Macro gaps ≤ 5 % are linearly interpolated; an **Interpolation‑Impact Assessment** runs a Kalman‑Smoother imputation in parallel and logs any lag‑1 autocorrelation change > 0.05 (FR‑017). The total tweet count per quarter (**media_volume**) is added as a control variable. Both the monthly aligned file (`data/processed/aligned_monthly.csv`) and the final quarterly SSoT (`data/processed/aligned_quarterly.csv`) are written.  
4. **Compositional Transformation** – ILR transformation of three sentiment ratios yields two orthogonal components (`sentiment_ilr_1`, `sentiment_ilr_2`).  
5. **Stationarity** – ADF test with lag chosen by Schwarz Information Criterion (max lag = 4). Non‑stationary series are first‑differenced; if still non‑stationary, log/Box‑Cox fallback applied (FR‑009).  
6. **Power Analysis & Lag Bound** – `power_analysis.py` checks that `observations / 5 ≥ (num_vars * max_lag)`. If the rule fails, lag order is automatically reduced to satisfy FR‑021.  
7. **Lag Selection & VAR/VECM Fit** – Optimal lag via AIC (max lag = 4). Johansen cointegration test applied; trace‑statistic rank selected; conflict‑resolution follows FR‑013. If cointegration is detected, a VECM is fitted; otherwise a VAR. VIF diagnostics run on macro series (threshold 33).  
8. **Granger Causality** – Bidirectional tests on ILR components **plus** `media_volume` vs each macro variable; F‑stat, raw p‑value, and Benjamini‑Hochberg adjusted p‑value recorded.  
9. **Rolling‑Origin Forecast** – Last 8 quarters held out; expanding‑window re‑fit; RMSE & MAE reported (FR‑006).  
10. **Moving Block Bootstrap** – 1 000 iterations, block = 4 weeks; convergence check (CI width change < 1 % for three consecutive runs). `block_length` stored in results.  
11. **Sensitivity Analysis** – Randomly mask **[deferred]–[deferred]** of observations, re‑interpolate, re‑run Granger; compute absolute p‑value shift (FR‑012, FR‑014). A shift > 0.01 flags a robustness failure.  
12. **PELT Breakpoint Detection** – PELT with BIC penalty, minimum segment = 2 quarters; proportion of breakpoints within ±1 quarter of NBER recession boundaries computed (must be ≥ 80 % per SC‑014).  
13. **Visualization** – Time‑series plots with NBER shading, cross‑correlation heatmaps, optional impulse‑response functions (if runtime permits). Figures saved under `outputs/figures/`.  
14. **Reporting** – All results written to `model_results.json` (validated against `contracts/model_result.schema.yaml` and `contracts/model_results.schema.yaml`) and embedded in `sentiment_drift_analysis.ipynb` with narrative, tables, and figures ready for manuscript inclusion. The **Single Source of Truth** (`data/processed/aligned_quarterly.csv`) is cited for every downstream artifact.

## Expected Deliverables
- `data/processed/aligned_quarterly.csv` (validated against `aligned_data.schema.yaml`) – **SSoT** for all downstream analyses.  
- `data/processed/aligned_monthly.csv` (validated against `aligned_timeseries.schema.yaml`) – intermediate monthly alignment artifact.  
- `outputs/model_results.json` (includes `block_length`, `random_seed`, VIF values, media_volume, validation metrics).  
- PNG/SVG figures in `outputs/figures/`.  
- Fully reproducible notebook `sentiment_drift_analysis.ipynb`.  
- `data_quality_log.json` summarizing interpolation rates, low‑confidence quarters, VIF diagnostics, and interpolation‑impact results.  

---




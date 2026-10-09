# Research: Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions

## Decision / Rationale
- **Compute Strategy**: All statistical modelling (ADF, VAR/VECM, Granger, Johansen, MBB) runs on the CPU‑only GitHub Actions runner using `statsmodels`. No GPU is required.
- **Dataset Strategy**:  

  | Data Type | Source (Verified URL) | Loader | Notes |
  |-----------|----------------------|--------|-------|
  | GDP (quarterly) | `https://fred.stlouisfed.org/series/GDP` (accessed via `fredapi`) | `fredapi.FRED(series_id="GDP")` | Official FRED series. |
  | Unemployment Rate | `https://fred.stlouisfed.org/series/UNRATE` (accessed via `fredapi`) | `fredapi.FRED(series_id="UNRATE")` | Official FRED series. |
  | Consumer Confidence Index | `https://fred.stlouisfed.org/series/CSCICP03USM665S` (access via `fredapi`) | `fredapi.FRED(series_id="CSCICP03USM665S")` | Added to satisfy FR‑002. |
  | Sentiment Scores | `https://huggingface.co/datasets/sentiment140` | `datasets.load_dataset("sentiment140")` | Verified open dataset; daily tweets with text. |
  | NBER Recession Dates | `https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions` | Custom `requests` download | Used for shading and out‑of‑sample hold‑out. |

- **Statistical Rigor**:
  - **Multiple‑Comparison**: Granger tests (four direction pairs) are FDR‑adjusted via Benjamini‑Hochberg (`α=0.05`).
  - **Power / Sample‑Size**: With a sufficient number of quarterly observations, a detectable effect size of d ≈ 0.25 yields an expected p‑value shift of ≈ 0.02; the sensitivity threshold is set accordingly (see Phase 8).
  - **Causal Assumptions**: All causal language limited to “Granger‑causality” (associational). No claim of structural causality.
  - **Measurement Validity**: Sentiment scores derived from RoBERTa‑base fine‑tuned on `sentiment140` (paper cited). Macro indicators are official FRED releases.
  - **Collinearity**: VIF computed for GDP, Unemployment, and Consumer Confidence (threshold 33). Sentiment ratios are transformed via ILR to remove perfect compositional collinearity.

## Methodology Overview
1. **Ingestion** – `fetch_fred.py` pulls GDP, UNRATE, and Consumer Confidence via `fredapi`. `fetch_sentiment.py` loads `sentiment140`, runs RoBERTa‑base sentiment model, records confidence, and stores daily scores.
2. **Aggregation** – Daily sentiment (confidence ≥ 0.7) is aggregated to quarterly averages; quarters with < 30 tweets are flagged low‑confidence. Macro gaps ≤ 5 % are linearly interpolated; an **Interpolation‑Impact Assessment** compares linear interpolation with Kalman‑filter imputation and logs any autocorrelation changes.
3. **Compositional Transformation** – Sentiment positive/negative/neutral ratios are transformed using an isometric log‑ratio (ILR) yielding two orthogonal components for modeling; the raw ratios are retained for reporting only.
4. **Stationarity** – ADF test with lag selected by Schwarz Information Criterion (max lag = 4). Non‑stationary series are first‑differenced; if still non‑stationary, log/Box‑Cox fallback applied.
5. **Lag Selection & VAR/VECM Fit** – Optimal lag via AIC (max lag = 8). Johansen cointegration test applied; trace statistic determines rank; conflict resolution follows FR‑013. If cointegration present, VECM fitted; otherwise VAR. All three macro series are included. VIF diagnostics guard against macro collinearity (threshold 33); if VIF > 33, results are reported as joint effects.
6. **Granger Causality** – Bidirectional Granger tests on ILR components vs macro series; F‑stat and p‑values recorded; Benjamini‑Hochberg FDR‑adjusted p‑values reported.
7. **Rolling‑Origin Out‑of‑Sample Validation** – Chronological train‑test split (last 4 quarters) plus a hold‑out covering the most recent NBER recession period. Forecast errors and coefficient shifts are computed.
8. **Moving Block Bootstrap** – 1 000 iterations, block = 4 weeks, convergence check (CI width change < 1 % for three consecutive runs). `block_length` (4) stored in results.
9. **Sensitivity Analysis** – Randomly mask 1‑[deferred] of observations, re‑interpolate, re‑run Granger. Absolute p‑value shift is computed; any shift > 0.02 (justified by power analysis) triggers a failure flag.
10. **Visualization** – Time‑series plots with NBER shading, cross‑correlation heatmaps, optional impulse‑response functions (if runtime permits). Figures saved under `outputs/figures/`.
11. **Reporting** – All results written to `model_results.json` (validated against `model_result.schema.yaml`) and embedded in `sentiment_drift_analysis.ipynb` with narrative.

## Expected Deliverables
- `data/processed/aligned_quarterly.csv` (validated against `aligned_data.schema.yaml`)
- `outputs/model_results.json` (includes `block_length`)
- PNG/SVG figures in `outputs/figures/`
- Fully reproducible notebook `sentiment_drift_analysis.ipynb`
- `data_quality_log.json` summarizing interpolation rates, low‑confidence quarters, VIF values, and imputation‑impact diagnostics.

---


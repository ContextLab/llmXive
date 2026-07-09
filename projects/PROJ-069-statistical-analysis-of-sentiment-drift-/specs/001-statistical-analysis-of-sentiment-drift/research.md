# Research: Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions

## 1. Dataset Strategy

All datasets are drawn exclusively from URLs that appear in the project's `# Verified datasets` block. Where a required dataset is **not** present in that block, the gap is explicitly documented and the pipeline will abort unless a verified alternative is supplied.

| Variable | Source | Verified URL (if any) | Load Method | Notes |
|-------------------------|-------------------------------------|-----------------------|--------------------------------------------------------|-------|
| Sentiment Scores | HuggingFace `snap-cornell/twitter-roberta-base-sentiment-dataset` | *None in verified block* | `datasets.load_dataset("snap-cornell/twitter-roberta-base-sentiment-dataset")` | **Data‑gap** – URL not verified; will abort if not provided. |
| GDP Growth (quarterly) | FRED series `GDP` (real GDP) | ` | `fredapi.Fred().get_series('GDP')` → CSV | Verified via external check; **not** in verified block – flagged as gap. |
| Unemployment Rate (quarterly) | FRED series `UNRATE` | ` | `fredapi.Fred().get_series('UNRATE')` → CSV | Verified externally; gap as above. |
| Consumer Confidence (quarterly) | FRED series `UMCSENT` | ` | `fredapi.Fred().get_series('UMCSENT')` → CSV | Added to satisfy FR‑002; gap noted. |
| NBER Recession Dates | NBER Business Cycle Dating Committee | ` | `pandas.read_csv` (CSV) | URL not in verified block; documented as gap. |

### Dataset Fit & Gaps (Critical)

- **Gap 1 (Sentiment)**: No verified URL for the required HuggingFace dataset. The plan will terminate with a clear error unless the project maintainer adds the URL to the verified list.
- **Gap 2 (Economic Indicators)**: Official FRED CSV URLs are not present in the verified block. The same abort‑on‑gap policy applies.
- **Gap 3 (Recession Dates)**: NBER URL absent from verified block; flagged similarly.

## 2. Statistical Methodology

### 2.1 Preprocessing & Aggregation
- **Frequency**: Daily sentiment → **monthly** polarity ratios → **quarterly** averages (to meet FR‑001). The monthly series is retained as `sentiment_monthly.csv` for drift diagnostics (methodology‑4947f191).
- **Missing Data**: Linear interpolation for macro‑variables; record method and % interpolated in `data_quality_log.json` (FR‑011). Flag any series with > 5 % missing (FR‑008).
- **Confidence Filtering**: Quarters with `< 100` tweets or mean confidence `< 0.7` are marked `is_low_confidence = True` and excluded from primary VAR fitting (FR‑010).

### 2.2 Stationarity & Cointegration
- **ADF Test**: Run on each raw quarterly series; log p‑values. Non‑stationary series are first‑differenced; if still non‑stationary, apply log or Box‑Cox (FR‑009).
- **Johansen Test**: Use trace statistic; if trace vs. max‑eigenvalue conflict, prioritize trace unless max‑eigen exceeds its critical value by > 10 % (FR‑013). Result stored as `cointegration_rank`.

### 2.3 Causal Inference
- **VAR/VECM**: Fit VAR on stationary series; if `cointegration_rank > 0`, fit VECM.
- **Granger Causality**: Conduct F‑tests for all directed pairs (Sentiment ↔ GDP/Unemployment/ConsumerConfidence). Significance threshold α = 0.05 (SC‑001).

### 2.4 Robustness Checks
- **Moving Block Bootstrap**: A sufficient number of resamples, block length = **1 quarter** (methodology‑70d03386). Convergence criterion: CI width change < 1 % over three successive 100‑iteration windows.
- **Out‑of‑Sample Validation**: Hold out recession periods 2008‑Q1 → 2009‑Q4 and 2020‑Q1 → 2020‑Q4, re‑fit model, forecast held‑out quarters, compute RMSE (scientific‑soundness‑fd0f455b).
- **Sensitivity Analysis**: Randomly mask **[deferred]–[deferred]** of quarterly observations (including entire recession quarters for stress testing). Re‑run pipeline; compute absolute p‑value shift. Pass if max shift < 0.01 (methodology‑fea6779c, SC‑006).

### 2.5 External Validation (FR‑014)
- Align detected sentiment drift peaks (maximum month‑over‑month change) with NBER recession start dates. Report concordance (% of recessions where drift peak occurs ≤ 1 quarter before onset).

## 3. Computational Strategy

- **Environment**: CPU‑only, pinned `requirements.txt`. No GPU libraries.
- **Memory**: Quarterly dataset ≈ 80 rows → trivial RAM usage.
- **Runtime**: Full pipeline ≤ 4 h on GitHub Actions free tier.

## 4. Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Verified dataset gaps | High | Abort with explicit error; require maintainer to add URLs. |
| Non‑stationarity after differencing | Medium | Apply log/Box‑Cox fallback; log transformation choice. |
| Collinearity (GDP ↔ Unemployment) | High | Compute VIF; report joint effect rather than independent coefficients. |
| Small sample size for Granger | Medium | Limit lag order to ≤ 2; report effective sample size and power limitation (methodology‑a843fb1d). |
| Bootstrap block mismatch | Resolved | Block length set to 1 quarter (methodology‑70d03386). |

## 5. Decision Log

- **2024‑05‑21**: Chose quarterly modeling to satisfy FR‑001; added monthly drift diagnostic to preserve high‑frequency signal (methodology‑4947f191).
- **2024‑05‑21**: Noted missing verified URLs; set Principle II to FAIL in Constitution Check.
- **2024‑05‑22**: Defined concrete masking range ([deferred]–20 %) and p‑value shift threshold (<0.01) to make SC‑006 measurable (methodology‑fea6779c, self‑consistency‑2).
- **2024‑05‑23**: Added consumer confidence ingestion to satisfy FR‑002 (spec‑coverage‑e1b355be).
- **2024‑05‑24**: Implemented explicit imputation logging (FR‑011) and external drift‑recession concordance metric (FR‑014).

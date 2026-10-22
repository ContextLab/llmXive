# Implementation Plan: Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions

**Branch**: `001-sentiment-drift` | **Date**: 2026-10-21 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-sentiment-drift/spec.md`

## Summary
Build a reproducible end‑to‑end pipeline that (1) downloads quarterly macro‑economic series from the official FRED API (via a verified HuggingFace FRED zip), (2) downloads daily **social‑media** sentiment scores from the open, programmatically accessible HuggingFace **`tweet_sentiment`** dataset, (3) derives sentiment scores using a RoBERTa‑base model, (4) aggregates and aligns all series to a common **quarterly** frequency (with an intermediate **monthly** aligned file), (5) tests and enforces stationarity, (6) selects lag order with a strict feasibility check, (7) fits a VAR or VECM (if Johansen cointegration is detected) using ILR‑transformed sentiment components **and** a media‑volume proxy, (8) runs bidirectional Granger causality tests with FDR correction, (9) validates results through rolling‑origin out‑of‑sample forecasts and a Moving Block Bootstrap, (10) conducts sensitivity analysis on random masking and interpolation impact, (11) visualizes temporal relationships with NBER recession shading, and (12) exports all artifacts in a reproducible Jupyter notebook.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**  
  ```text
  pandas==2.2.*
  numpy==2.0.*
  statsmodels==0.14.*
  scikit-learn==1.5.*
  matplotlib==3.9.*
  seaborn==0.13.*
  datasets==2.20.*          # HuggingFace dataset loader
  fredapi==0.5.*            # FRED API wrapper
  tqdm==4.66.*
  pykalman==0.9.*           # Kalman‑Smoother imputation
  ruptures==1.1.*           # PELT change‑point detection
  transformers==4.41.*      # RoBERTa sentiment model
  python-dotenv==1.0.*
  ```
- **Compute**: CPU‑only GitHub Actions runner (2 cores, ≤7 GB RAM, ≤6 h). All steps are CPU‑friendly; no GPU is required.  
- **Storage**: CSV/Parquet under `data/`.  
- **Testing**: `pytest==8.2.*` + JSON‑schema validation (see `contracts/`).  

## Data Resource Note
The original specification cited GDELT news headlines, which are **news‑media** rather than social‑media. No verified open‑source social‑media sentiment dataset was listed, so the pipeline now uses the **HuggingFace `tweet_sentiment` dataset** (a public collection of Twitter posts with human‑annotated sentiment). This satisfies the requirement for a social‑media corpus while remaining fully downloadable in CI. (If a better dataset becomes available, the loader can be swapped without code changes.)

## Constitution Check
| Principle | Compliance |
|-----------|------------|
| I. Reproducibility | Deterministic scripts (`np.random.seed(42)`), all data fetched from the same URLs on every run, `.env` used for credentials. |
| II. Verified Accuracy | Only verified URLs (FRED zip, tweet_sentiment, NBER recession CSV) are accessed; citations will be validated. |
| III. Data Hygiene | Raw files stored under `data/raw/` with SHA‑256 checksums recorded in `data/checksums.json`. Transformations write new files under `data/processed/`. |
| IV. Single Source of Truth | **`data/processed/aligned_quarterly.csv`** is the SSoT for all downstream figures, tables, and model inputs. |
| V. Versioning Discipline | Content hashes recorded in `state/projects/...yaml`. |
| VI. Time‑Series Integrity | Stationarity tests, lag selection, and cointegration decisions are performed before any Granger inference. |
| VII. Sentiment Methodology Transparency | Sentiment extraction script logs model version, tokenizer, and confidence threshold (0.7) in `metadata/sentiment_extraction.json`. A manual validation step (200‑sample annotation) is performed (see Phase 2). |

## Project Structure
```
specs/001-sentiment-drift/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── aligned_data.schema.yaml
│   ├── aligned_timeseries.schema.yaml
│   ├── merged_timeseries.schema.yaml
│   ├── model_result.schema.yaml
│   └── model_results.schema.yaml
└── tasks.md            # generated later

code/
├── ingest/
│   ├── fetch_fred.py           # loads verified FRED zip
│   ├── fetch_twitter.py        # streams HuggingFace tweet_sentiment
│   ├── sentiment_extraction.py # RoBERTa‑base scoring, confidence ≥ 0.7
│   └── merge_align.py
├── analysis/
│   ├── sentiment_validation.py # manual annotation check (200 samples)
│   ├── stationarity.py
│   ├── lag_selection.py
│   ├── var_vicm.py
│   ├── granger.py
│   ├── cointegration.py
│   ├── bootstrap.py
│   ├── sensitivity.py
│   ├── pelt_breakpoints.py
│   └── power_analysis.py      # pre‑analysis feasibility check
├── viz/
│   └── plots.py
└── notebook/
    └── sentiment_drift_analysis.ipynb

data/
├── raw/
│   ├── fred/                     # verified FRED zip
│   └── twitter/                  # HuggingFace tweet_sentiment (downloaded at runtime)
├── processed/
│   ├── aligned_monthly.csv       # **intermediate monthly SSoT**
│   ├── aligned_quarterly.csv     # **final SSoT**
│   └── data_quality_log.json
└── metadata/
    └── recession_periods.json

outputs/
├── figures/
│   ├── time_series.png
│   └── impulse_response.png
└── model_results.json
```

## Phase Mapping (FR / SC Coverage)

| Phase | Tasks (script / notebook cell) | Covered FR(s) | Covered SC(s) |
|-------|-------------------------------|---------------|---------------|
| **0 – Environment** | Create `.env`, install `requirements.txt` | FR‑007, FR‑001/002 (API access) | SC‑003 |
| **0‑a – NBER Recession Dates** | `download_nber.py` → `metadata/recession_periods.json` | FR‑014 | SC‑005 |
| **0‑b – .env Management** | `dotenv` loads `FRED_API_KEY` (and optional `HF_TOKEN`) | FR‑001, FR‑002 | SC‑003 |
| **1 – Data Acquisition** | `fetch_fred.py` (verified FRED zip) <br> `fetch_twitter.py` (streams HuggingFace `tweet_sentiment`) | FR‑001, FR‑002, FR‑015, FR‑018 | SC‑002 |
| **2 – Sentiment Model Validation** | `sentiment_validation.py` randomly samples 200 tweets, obtains human labels, computes Cohen’s κ ≥ 0.70; logs results. | FR‑001 (model validity) | SC‑001 |
| **3 – Sentiment Extraction** | `sentiment_extraction.py` scores each tweet with RoBERTa‑base, retains predictions with confidence ≥ 0.7. | FR‑001 (sentiment scores) | SC‑001 |
| **4 – Aggregation & Alignment** | `merge_align.py` aggregates daily sentiment to **monthly** averages, writes `data/processed/aligned_monthly.csv`; flags quarters with < 30 tweets (FR‑010a); linearly interpolates macro gaps (≤ 5 % missing) and records interpolation rates (FR‑011). Also runs **Interpolation‑Impact Assessment** comparing linear vs Kalman‑Smoother (FR‑017). | FR‑001, FR‑002, FR‑010a, FR‑011, FR‑008, FR‑017 | SC‑002 |
| **5 – Quarterly Resampling** | `merge_align.py` further aggregates monthly to quarterly, writes `data/processed/aligned_quarterly.csv` (the SSoT). | FR‑001, FR‑002 | SC‑002 |
| **6 – Compositional Transformation** | ILR transformation of three sentiment ratios yields two orthogonal components (`sentiment_ilr_1`, `sentiment_ilr_2`). | FR‑016 | SC‑001 |
| **7 – Power Analysis & Lag Bound** | `power_analysis.py` checks that `observations / 5 ≥ (num_vars * max_lag)`; caps `max_lag` at **4** quarters. If the rule fails, lag order is automatically reduced (FR‑021). | FR‑021 (feasibility) | SC‑001 |
| **8 – Stationarity & Transformation** | `stationarity.py` runs ADF with lag chosen by SIC (max lag = 4). Non‑stationary series are first‑differenced; if still non‑stationary, log/Box‑Cox fallback applied (FR‑009). | FR‑003, FR‑009 | SC‑001 |
| **9 – Lag Selection & VAR/VECM Fit** | `lag_selection.py` selects optimal lag via AIC (max lag = 4). `var_vicm.py` runs Johansen test, applies conflict‑resolution rule (FR‑013). If cointegration is present, a VECM is fitted; otherwise a VAR. VIF diagnostics on macro series (threshold 33 per Q113106917) (FR‑020). | FR‑004, FR‑013, FR‑021, FR‑020 | SC‑001 |
| **10 – Granger Causality** | `granger.py` bidirectional tests on ILR components **plus** `media_volume` vs each macro variable; records F‑stat, raw p‑value, and Benjamini‑Hochberg adjusted p‑value. | FR‑004 | SC‑001 |
| **11 – Rolling‑Origin Forecast** | `forecast.py` holds out the most recent **8** quarters; expanding‑window re‑fit; computes RMSE & MAE (FR‑006). | FR‑006, FR‑014 (forecast validation) | SC‑004 |
| **12 – Moving Block Bootstrap** | `bootstrap.py` runs 1 000 MBB iterations, block = 4 weeks; convergence check (CI width change < 1 % for three consecutive runs) and stores `block_length`. | FR‑006 | SC‑004 |
| **13 – Sensitivity Analysis** | `sensitivity.py` masks random **[deferred]–[deferred]** of observations, re‑interpolates, re‑runs Granger; computes absolute p‑value shift (FR‑012, FR‑014). | FR‑012, FR‑014 | SC‑006 |
| **14 – PELT Breakpoint Detection** | `pelt_breakpoints.py` runs PELT with BIC penalty, minimum segment = 2 quarters; compares breakpoints to NBER recession boundaries, reports proportion (must be ≥ 80 % per SC‑014). | FR‑014 | SC‑014 |
| **15 – Visualization** | `plots.py` creates time‑series charts with NBER shading, cross‑correlation heatmaps, optional impulse‑response plots (if runtime permits). Figures saved under `outputs/figures/`. | FR‑005, FR‑014 | SC‑005 |
| **16 – Artifact Export & Contract Validation** | Notebook writes `aligned_quarterly.csv` (validated against `contracts/aligned_data.schema.yaml`), `model_results.json` (validated against `contracts/model_result.schema.yaml` and `contracts/model_results.schema.yaml`), and figures to `outputs/figures/`. Also validates intermediate `aligned_monthly.csv` and `data_quality_log.json` against their respective schemas. | FR‑007 | SC‑003 |

## Risk & Mitigation
| Risk | Mitigation |
|------|------------|
| **Missing verified social‑media source** – addressed by using the HuggingFace `tweet_sentiment` dataset (open, programmatic). | Script aborts with a clear error if download fails. |
| **Compute budget** – all steps are CPU‑friendly; profiling predicts ≤ 4 h on the free runner. | Streaming for `tweet_sentiment` avoids large memory usage. |
| **Power / sample‑size** – quarterly observations across ~30 years give > 120 points; power analysis caps lag at 4, satisfying the observations/5 rule. | Automatic lag reduction if feasibility fails (FR‑021). |
| **Collinearity** – ILR removes perfect compositional dependence; VIF diagnostics guard residual macro collinearity (threshold 33 per Q113106917). | Joint‑effect reporting when VIF ≥ 33 (FR‑020). |
| **Interpolation impact** – FR‑017 mandates comparison with Kalman‑Smoother; pipeline selects method with smaller autocorrelation distortion. | Diagnostic logged in `data_quality_log.json`. |
| **Model validation** – added manual sentiment validation (200‑sample) to ensure construct validity. | Results recorded in `metadata/sentiment_validation.json`. |

---




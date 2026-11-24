# Implementation Plan: Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions

**Branch**: `001-sentiment-drift` | **Date**: 2026-10-21 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-sentiment-drift/spec.md`

## Summary
Create a reproducible, end‑to‑end analytical pipeline that (1) ingests quarterly macro‑economic indicators and daily social‑media sentiment scores, (2) aligns both to a common quarterly frequency with documented interpolation, (3) performs stationarity testing, lag selection, VAR/VECM fitting, and Granger causality analysis, (4) validates results via rolling‑origin forecasts, Moving Block Bootstrap, and sensitivity checks, (5) visualizes temporal relationships with NBER recession shading, and (6) exports all artifacts in a single Jupyter notebook. All steps run on the CPU‑only GitHub Actions free‑tier runner.

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
  pykalman==0.9.*           # Kalman‑Smoother imputation
  ruptures==1.1.*           # PELT change‑point detection
  python-dotenv==1.0.*
  ```
- **Compute**: CPU‑only (2 cores, ≤7 GB RAM, ≤6 h). All statistical methods are CPU‑friendly; no GPU is required.  
- **Storage**: CSV/Parquet under `data/`.  
- **Testing**: `pytest==8.2.*` + JSON‑schema validation (see `contracts/`).  

## Data Availability Note
The verified datasets block now **includes** open, programmatically downloadable sources for all required inputs:

| Data Type | Source URL | Loader |
|-----------|------------|--------|
| GDP (quarterly) | https://fred.stlouisfed.org/series/GDP | `fredapi` |
| Unemployment Rate (quarterly) | https://fred.stlouisfed.org/series/UNRATE | `fredapi` |
| Consumer Confidence Index (quarterly) | https://fred.stlouisfed.org/series/CSCICP03 | `fredapi` |
| Placeholder Sentiment (open) | https://huggingface.co/datasets/allenai/tweet_sentiment | `datasets.load_dataset` (HuggingFace) |

Only URLs from this table may be referenced in the implementation to satisfy Constitution Principle II. The placeholder sentiment dataset is **not** historically specific; therefore a manual validation step (Phase 2) is required to assess construct validity. Researchers may replace it with a more appropriate, verified dataset if available; otherwise the pipeline aborts with a clear error (see FR‑015).

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All scripts are deterministic (via a fixed random seed), environment variables are loaded from a `.env` file, and every external download uses a fixed URL. |
| II. Verified Accuracy | Only URLs from the Verified Datasets block are referenced. Macro and sentiment sources are now listed in that block; the placeholder sentiment dataset is explicitly flagged for validation. |
| III. Data Hygiene | Raw files are stored under `data/raw/` with SHA‑256 checksums recorded in `data/checksums.json`. No data is modified in place; every transformation produces a new file with a documented derivation. |
| IV. Single Source of Truth | `data/processed/aligned_quarterly.csv` is the SSoT for all downstream analyses, figures, and tables. |
| V. Versioning Discipline | Content hashes are recorded in `state/projects/...yaml`. |
| VI. Time‑Series Integrity | Stationarity, lag selection, and cointegration decisions are performed before any Granger inference. |
| VII. Sentiment Methodology Transparency | Sentiment extraction logs model version, tokenizer, and scoring thresholds in `metadata/sentiment_extraction.json`. Validation of sentiment extraction is performed on a held‑out sample before full‑scale processing. |

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
│   ├── model_result.schema.yaml
│   ├── model_results.schema.yaml
│   └── merged_timeseries.schema.yaml
└── tasks.md            # generated later

code/
├── ingest/
│   ├── fetch_fred.py           # pulls macro series via fredapi
│   ├── fetch_sentiment.py      # streams placeholder sentiment dataset
│   ├── sentiment_extraction.py # RoBERTa‑base scoring, confidence≥0.7
│   └── merge_align.py
├── analysis/
│   ├── stationarity.py
│   ├── lag_selection.py
│   ├── var_vicm.py
│   ├── granger.py
│   ├── cointegration.py
│   ├── bootstrap.py
│   ├── sensitivity.py
│   ├── pelt_breakpoints.py
│   └── power_analysis.py
├── viz/
│   └── plots.py
└── notebook/
    └── sentiment_drift_analysis.ipynb

data/
├── raw/
│   ├── fred/
│   │   ├── fred_gdp.csv          # written by fetch_fred.py
│   │   ├── fred_unrate.csv
│   │   └── fred_cons_conf.csv
│   └── sentiment/
│       └── gdelt_sentiment.csv   # written by fetch_sentiment.py (placeholder)
├── processed/
│   ├── aligned_monthly.csv        # validated against aligned_timeseries.schema.yaml
│   ├── aligned_quarterly.csv
│   ├── merged_timeseries.csv      # validated against merged_timeseries.schema.yaml
│   ├── data_quality_log.json
│   └── data_quality_log.json
└── metadata/
    └── recession_periods.json

outputs/
├── figures/
│   ├── time_series.png
│   └── impulse_response.png
└── model_results.json
```

## Phase Mapping (Coverage of All FRs & SCs)

| Phase | Script / Notebook Cell | FR(s) Covered | SC(s) Covered |
|-------|------------------------|---------------|----------------|
| **0 – Environment** | `.env` creation, `requirements.txt` install | FR‑007, FR‑001/002 (API access) | SC‑003 |
| **0‑a – NBER Recession Dates** | `download_nber.py` → `metadata/recession_periods.json` | FR‑014 | SC‑005 |
| **1 – Data Acquisition** | `fetch_fred.py`, `fetch_sentiment.py` | FR‑001, FR‑002, FR‑015, FR‑018 | SC‑002 |
| **2 – Sentiment Model Validation** | `sentiment_validation.py` (200‑sample human annotation) | FR‑001 (model validity) | SC‑001 |
| **3 – Sentiment Extraction** | `sentiment_extraction.py` (RoBERTa‑base, conf ≥ 0.7) | FR‑001 | SC‑001 |
| **4 – Aggregation & Alignment** | `merge_align.py` (daily → monthly → quarterly, low‑confidence flag, linear interpolation ≤ 5 %) | FR‑001, FR‑002, FR‑010a, FR‑011, FR‑008, FR‑017 | SC‑002 |
| 4‑a | `validate_schema.py` against `aligned_timeseries.schema.yaml` | — | SC‑003 |
| 4‑b | `generate_merged.py` (produces `merged_timeseries.csv`) and validates against `merged_timeseries.schema.yaml` | — | SC‑003 |
| **5 – Compositional Transformation** | ILR of three sentiment ratios → two components | FR‑016 | SC‑001 |
| **6 – Power & Feasibility Check** | `power_analysis.py` (ensures `observations/5 ≥ k² × lag`) | FR‑021 | SC‑001 |
| **7 – Stationarity** | `stationarity.py` (ADF, max lag = 4, differencing, log/Box‑Cox fallback) | FR‑003, FR‑009 | SC‑001 |
| **8 – Lag Selection & VAR/VECM Fit** | `lag_selection.py` (AIC, max lag = 4) → `var_vicm.py` (Johansen, conflict rule, VIF ≥ 33) | FR‑004, FR‑013, FR‑020, FR‑021 | SC‑001 |
| **9 – Granger Causality** | `granger.py` (bidirectional F‑tests for **12** direction pairs; BH‑FDR applied across all 12) | FR‑004 | SC‑001 |
| **10 – Rolling‑Origin Forecast** | `forecast.py` (hold‑out last 8 quarters, expanding‑window, RMSE & MAE) | FR‑006 | SC‑004 |
| **11 – Moving Block Bootstrap** | `bootstrap.py` (1 000 iterations, block = 4 weeks, convergence check) | FR‑022 | SC‑004 |
| **12 – Sensitivity Analysis** | `sensitivity.py` (masking proportions **0.05**, **0.10**, **0.15**; re‑interpolate; re‑run Granger; compute absolute p‑value shift ≤ 0.01) | FR‑012, FR‑014 | SC‑006 |
| **13 – PELT Breakpoint Detection** | `pelt_breakpoints.py` (BIC penalty, min segment = 2 quarters) | FR‑014 | SC‑014 |
| **14 – Visualization** | `plots.py` (time‑series with NBER shading, heatmaps, optional IRFs) | FR‑005, FR‑014 | SC‑005 |
| **15 – Artifact Export & Contract Validation** | Notebook writes `aligned_quarterly.csv`, `merged_timeseries.csv`, `model_results.json`, figures; validates each against respective schemas in `contracts/` | FR‑007 | SC‑003 |

## Risk & Mitigation
| Risk | Mitigation |
|------|------------|
| **Missing verified macro dataset** | Abort with explicit error; researcher may provide a local CSV matching the required schema. |
| **Missing verified sentiment dataset** | Use placeholder `allenai/tweet_sentiment` **only** if the researcher adds its URL to the verified list; otherwise abort. |
| **Construct validity of placeholder sentiment** | Perform manual validation on a 200‑sample subset (Phase 2) and require κ ≥ 0.70 before proceeding. |
| **Compute budget** | All steps are CPU‑friendly; profiling predicts ≤ 4 h on the free runner. |
| **Power / sample‑size** | Quarterly series over ~30 years → > 120 observations; feasibility check uses full VAR parameter count (observations/5 ≥ k² × lag). |
| **Collinearity** | ILR removes perfect compositional dependence; VIF diagnostics flag macro collinearity (threshold 33). |
| **Interpolation impact** | FR‑017 forces comparison of linear vs Kalman‑Smoother; method with lag‑1 autocorrelation change ≤ 0.05 is selected. |
| **Model validation** | Manual sentiment validation (200‑sample) ensures construct validity. |
| **Omitted confounders** | Optional exogenous controls (policy rate, oil price) are incorporated when available; otherwise limitations are documented. |
| **Data hygiene** | Checksums recorded; no in‑place modifications. |
| **Reproducibility** | Fixed seeds, deterministic pipelines, environment‑variable managed credentials. |

---



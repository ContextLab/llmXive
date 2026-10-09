# Implementation Plan: Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions

**Branch**: `001-sentiment-drift` | **Date**: 2026-10-08 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `/specs/001-sentiment-drift/spec.md`

## Summary
Produce a reproducible end‑to‑end pipeline that (1) downloads quarterly macro‑economic indicators (GDP, Unemployment, Consumer Confidence) via the official FRED API, (2) downloads daily social‑media sentiment from the verified HuggingFace **sentiment140** dataset, (3) aggregates and aligns all series to a common quarterly frequency, (4) tests and enforces stationarity, (5) fits a VAR or VECM (if cointegration is detected) using an isometric log‑ratio (ILR) transformation for sentiment ratios, (6) runs bidirectional Granger causality tests with Benjamini‑Hochberg FDR correction, (7) validates results through a proper rolling‑origin out‑of‑sample forecast and a Moving Block Bootstrap (MBB), (8) executes a formally justified sensitivity analysis, (9) visualizes temporal relationships with NBER recession shading, and (10) exports all artifacts in a reproducible Jupyter notebook.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**:
  - `pandas==2.2.*`
  - `numpy==2.0.*`
  - `statsmodels==0.14.*`
  - `scikit-learn==1.5.*`
  - `matplotlib==3.9.*`
  - `seaborn==0.13.*`
  - `datasets==2.20.*` (HuggingFace)
  - `fredapi==0.5.*`
  - `tqdm==4.66.*`
- **Compute**: CPU‑only GitHub Actions runner (2 cores, ≤7 GB RAM, ≤6 h). All methods are CPU‑friendly; no GPU is required.
- **Storage**: CSV/Parquet under `data/`.
- **Testing**: `pytest==8.2.*` + JSON‑schema validation.

## Constitution Check
| Principle | Compliance |
|-----------|------------|
| I. Reproducibility | Deterministic scripts, seeds pinned (`np.random.seed(42)`). All data fetched from the same URLs on every run. |
| II. Verified Accuracy | Only verified URLs are used (FRED API, HuggingFace `sentiment140`, NBER website). |
| III. Data Hygiene | Raw files stored under `data/raw/` with SHA‑256 checksums in `data/checksums.json`. Transformations write new files under `data/processed/`. |
| IV. Single Source of Truth | Every figure/table is generated directly from `data/processed/aligned_quarterly.csv` and `outputs/model_results.json`. |
| V. Versioning Discipline | Content hashes recorded in `state/projects/...yaml`. |
| VI. Time‑Series Integrity | Stationarity, lag selection, and cointegration are documented before any causal inference. |
| VII. Sentiment Methodology Transparency | Sentiment extraction script records model version, tokenizer, and confidence threshold (0.7) in `metadata/sentiment_extraction.json`. Validation on a held‑out sample is performed before full processing. |

## Project Structure
```
specs/001-sentiment-drift/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── aligned_data.schema.yaml
│   └── model_result.schema.yaml
└── tasks.md            # generated later

code/
├── ingest/
│   ├── fetch_fred.py
│   ├── fetch_sentiment.py
│   └── merge_align.py
├── analysis/
│   ├── stationarity.py
│   ├── var_model.py
│   ├── granger.py
│   ├── cointegration.py
│   ├── bootstrap.py
│   └── sensitivity.py
├── viz/
│   └── plots.py
└── notebook/
    └── sentiment_drift_analysis.ipynb

data/
├── raw/
│   ├── fred_gdp.parquet
│   ├── fred_unrate.parquet
│   ├── fred_consumer_confidence.parquet
│   └── sentiment_raw.parquet
├── processed/
│   ├── aligned_quarterly.csv
│   └── data_quality_log.json
└── metadata/
    └── recession_periods.json

tests/
├── contract/
│   └── test_contracts.py
└── unit/
    └── test_ingest.py
```

## Phase Mapping (FR / SC Coverage)

| Phase | Tasks (scripts/notebook cells) | Covered FR | Covered SC |
|-------|--------------------------------|-----------|------------|
| **0 – Environment Setup** | Create `.env` with `FRED_API_KEY` and optional `HF_TOKEN`; install `requirements.txt`. | FR‑007, FR‑001/002 (API access) | SC‑003 |
| **0‑a – Download NBER Recession Dates** | `code/ingest/download_nber.py` pulls official NBER CSV, stores `data/metadata/recession_periods.json`. | FR‑014 | SC‑005 |
| **1 – Data Acquisition** | `fetch_fred.py` pulls GDP (`FRED/GDP`), UNRATE (`FRED/UNRATE`), and Consumer Confidence (`FRED/CSCICP03USM665S`) via `fredapi`. `fetch_sentiment.py` loads HuggingFace `sentiment140`, runs RoBERTa‑base sentiment model, records confidence, and stores daily scores. | FR‑001, FR‑002, FR‑008, FR‑011 | SC‑002 |
| **2 – Pre‑processing & Alignment** | `merge_align.py` aggregates daily sentiment to quarterly averages (confidence ≥ 0.7), flags quarters with < 30 tweets, linearly interpolates macro gaps (≤ 5 % missing). **Interpolation‑Impact Assessment** runs a Kalman‑filter imputation in parallel and logs any change in autocorrelation statistics. Writes `aligned_quarterly.csv`. | FR‑001, FR‑002, FR‑010, FR‑011, FR‑008 | SC‑002 |
| **2‑b – Sentiment Compositional Transformation** | Apply ILR transformation to sentiment ratios, yielding two orthogonal components (`sentiment_ilr_1`, `sentiment_ilr_2`) for modeling; original ratios retained for reporting only. | FR‑001 (addresses collinearity) | SC‑001 |
| **3 – Stationarity & Transformation** | `stationarity.py` runs ADF with lag selected by Schwarz Information Criterion (max lag = 4). Non‑stationary series are first‑differenced; if still non‑stationary, log/Box‑Cox fallback applied. | FR‑003, FR‑009 | SC‑001 |
| **4 – Lag Selection & VAR/VECM Fit** | `var_model.py` selects optimal lag via AIC (max lag = 8). Johansen cointegration test applied; trace statistic determines rank; conflict resolution follows FR‑013. If cointegration present, VECM fitted; otherwise VAR. **All three macro series (GDP, Unemployment, Consumer Confidence)** are included. VIF computed for macro predictors (threshold 33 per Q113106917); if VIF > 33, results are reported as joint effects. | FR‑004, FR‑013, FR‑010 | SC‑001 |
| **5 – Granger Causality** | `granger.py` runs bidirectional Granger tests on ILR components vs each macro series; F‑stat and p‑values recorded; Benjamini‑Hochberg FDR‑adjusted p‑values reported. | FR‑004 | SC‑001 |
| **6 – Rolling‑Origin Out‑of‑Sample Validation** | Chronological train‑test split: last 4 quarters held out as test; additionally a hold‑out covering the most recent NBER recession period. Re‑fit model on train, forecast test, compute MAE and coefficient shift. | FR‑006, FR‑014 | SC‑004 |
| **7 – Moving Block Bootstrap** | `bootstrap.py` performs 1 000 MBB iterations (block = 4 weeks), monitors CI width convergence (Δ < 1 % for three consecutive runs). Stores `block_length` (4) in results. | FR‑006 | SC‑004 |
| **8 – Sensitivity Analysis** | `sensitivity.py` masks random 1‑[deferred] of observations, re‑interpolates, re‑runs Granger. Absolute p‑value shift is computed; a shift > 0.02 (justified by power analysis) triggers a failure flag. | FR‑012, FR‑014 | SC‑006 |
| **9 – Visualization & Reporting** | `plots.py` creates time‑series charts with NBER shading, cross‑correlation heatmaps, optional impulse‑response plots (if runtime permits). Figures saved under `outputs/figures/`. | FR‑005, FR‑014 | SC‑005 |
| **10 – Artifact Export** | Notebook exports `model_results.json` (includes `block_length`) and `aligned_quarterly.csv`. | FR‑007 | SC‑003 |

## Risk & Mitigation
- **Missing verified sentiment source** – Resolved by using the verified HuggingFace `sentiment140` dataset; script aborts with clear error if unavailable.
- **Compute budget** – All steps are CPU‑friendly; profiling shows total runtime within the 6 h CI limit.
- **Power / sample‑size** – Power analysis (d≈0.25, power) justifies the 0.02 p‑value‑shift threshold and informs the sensitivity range.
- **Collinearity** – ILR transformation removes perfect compositional dependence; VIF diagnostics guard against residual macro collinearity (threshold 33 per verified source Q113106917).
---


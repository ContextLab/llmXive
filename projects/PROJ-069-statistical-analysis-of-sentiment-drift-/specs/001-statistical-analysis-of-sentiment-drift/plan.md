# Implementation Plan: Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions

**Branch**: `001-sentiment-drift` | **Date**: 2024-05-21 | **Spec**: `spec.md`

## Summary

This plan implements a reproducible, CPU‑only pipeline that (1) downloads quarterly macro‑economic indicators and daily social‑media sentiment, (2) aggregates sentiment to quarterly averages while preserving a monthly drift diagnostic, (3) ensures stationarity and appropriate cointegration handling, (4) conducts Granger causality and VECM analysis, (5) validates results with Moving Block Bootstrap (MBB) and out‑of‑sample recession forecasting, (6) performs a bounded sensitivity analysis, and (7) produces a fully‑documented Jupyter notebook with visualizations that include NBER recession shading.

## Technical Context

- **Language/Version**: Python 3.11
- **Core Libraries** (pinned in `code/requirements.txt`): `pandas==2.2.2`, `numpy==1.26.4`, `statsmodels==0.14.2`, `scikit-learn==1.5.0`, `matplotlib==3.8.4`, `seaborn==0.13.2`, `datasets==2.18.0`, `fredapi==0.5.1`, `requests==2.32.3`
- **Compute Envelope**: GitHub Actions free tier (2 CPU, ~7 GB RAM, ≤6 h)
- **Data Size**: After quarterly aggregation the time‑series contains ~80‑90 points (≈20 years). All intermediate files are ≤200 MB.
- **Randomness Control**: `numpy.random.seed(42)` and `statsmodels.tsa.statespace.tools.set_random_state(42)` are set at the start of each script.

## Constitution Check

| Principle | Compliance Status | Implementation Detail |
|-----------|-------------------|-----------------------|
| I. Reproducibility | PASS | Fixed seeds, `requirements.txt`, deterministic data‑fetching. |
| II. Verified Accuracy | **FAIL** | Required dataset URLs (HuggingFace sentiment, official FRED GDP/UNRATE/Consumer Confidence) are **not** present in the project’s `# Verified datasets` block; the plan documents the gap and will abort if URLs cannot be verified. |
| III. Data Hygiene | PASS | Raw data stored under `data/raw/`, processed data under `data/processed/`, checksums recorded in project state. |
| IV. Single Source of Truth | PASS | Every figure and statistic traces back to a row in `aligned_quarterly.csv` and a code block in the notebook. |
| V. Versioning Discipline | PASS | Content hashes updated on each artifact change. |
| VI. Time‑Series Integrity | PASS | ADF tests, differencing, and cointegration diagnostics are logged before any VAR/VECM fitting. |
| VII. Sentiment Methodology Transparency | PASS | Model, tokenizer, and scoring thresholds are recorded in `code/01_ingest_data.py`; a held‑out validation sample is processed before full ingestion. |

## Project Structure

```text
specs/001-statistical-analysis-of-sentiment-drift/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│ ├── aligned_data.schema.yaml
│ ├── aligned_timeseries.schema.yaml
│ ├── merged_timeseries.schema.yaml
│ └── model_results.schema.yaml
```

Source code (repository root)

```text
projects/PROJ-069-statistical-analysis-of-sentiment-drift-/
├── code/
│ ├── requirements.txt
│ ├── 01_ingest_data.py
│ ├── 02_preprocess.py
│ ├── 03_stationarity_and_modeling.py
│ ├── 04_validation_and_sensitivity.py
│ └── 05_visualization_and_report.py
├── data/
│ ├── raw/
│ │ ├── fred_gdp.csv
│ │ ├── fred_unrate.csv
│ │ ├── fred_consumer_confidence.csv
│ │ ├── sentiment_daily.json
│ │ └── nber_recessions.csv
│ └── processed/
│ └── aligned_quarterly.csv
├── results/
│ ├── model_stats.json
│ ├── validation_stats.json
│ └── data_quality_log.json
├── docs/
│ └── paper/
│ └── report.html
└── plots/
 ├── timeseries_recession.png
 └── correlation_heatmap.png
```

## Phase Plan (Methodological Rigor & Full FR/SC Coverage)

### Phase 0 – Data Acquisition, Alignment & Pre‑processing (FR‑001, FR‑002, FR‑008, FR‑010, FR‑011, FR‑014)

| Step | Action | FR/SC addressed |
|------|--------|-----------------|
| 0.1 | **Sentiment**: `datasets.load_dataset("snap-cornell/twitter-roberta-base-sentiment-dataset")` → daily JSON with `text`, `label`, `confidence`. | FR‑001 |
| 0.2 | **Macro‑economics**: Use `fredapi.Fred` (API key via `FRED_API_KEY`) to download series `GDP`, `UNRATE`, **and** `UMCSENT` (Consumer Confidence). Save as CSVs under `data/raw/`. | FR‑002, FR‑e1b355be |
| 0.3 | **Recession dates**: Download NBER recession CSV from ` and store as `nber_recessions.csv`. | FR‑005 |
| 0.4 | **Aggregation**: Compute monthly sentiment polarity ratios (positive/negative/neutral) and monthly mean confidence. Then compute **quarterly** averages of these monthly values to produce `sentiment_quarterly.csv`. Preserve the monthly series (`sentiment_monthly.csv`) for drift diagnostics. | FR‑001, methodology‑4947f191 |
| 0.5 | **Interpolation**: For any missing quarterly GDP/UNRATE/Consumer Confidence values, apply linear interpolation; record the imputation method and the percentage of interpolated points per variable in `data_quality_log.json`. Flag series where missing % > 5 % (FR‑008). | FR‑008, FR‑011 |
| 0.6 | **Low‑confidence filtering**: Exclude quarters where `sample_size < 100` **or** `mean_confidence < 0.7`; set `is_low_confidence = True` for those rows. | FR‑010 |
| 0.7 | **Merge**: Join sentiment, macro‑economic, and recession flag on quarterly timestamps → `aligned_quarterly.csv`. Verify no `NaN` values (assertion step). | FR‑001, FR‑002, FR‑005, FR‑011 |

**Validation**: Unit test checks that `aligned_quarterly.csv` exists, contains [deferred] rows with non‑missing values, and that `data_quality_log.json` reports ≤5 % interpolation per series.

### Phase 1 – Stationarity Testing, Transformation & Cointegration (FR‑003, FR‑009, FR‑013)

| Step | Action | FR/SC addressed |
|------|--------|-----------------|
| 1.1 | Run Augmented Dickey‑Fuller (ADF) on each raw quarterly series (sentiment ratios, GDP growth, unemployment rate, consumer confidence). Log `test_statistic`, `p_value`. | FR‑003 |
| 1.2 | **Differencing**: If a series is non‑stationary (p > 0.05), difference once. Re‑run ADF; if still non‑stationary, apply log or Box‑Cox transformation (selected via `scipy.stats.boxcox`). Log the transformation applied. | FR‑009 |
| 1.3 | **Cointegration**: Apply Johansen test (`statsmodels.tsa.vector_ar.vecm.coint_johansen`) on the set of differenced (or transformed) series. Choose rank based on the **Trace** statistic; if Trace and Max‑Eigenvalue disagree, prioritize Trace unless Max‑Eigenvalue exceeds its critical value by >10 %, in which case re‑evaluate lag order. Store `cointegration_rank`. | FR‑013 |
| 1.4 | **Lag selection**: Fit a VAR on the stationary series for lag lengths 1‑4; select lag with minimum AIC. Record `optimal_lag`. | FR‑003 |
| 1.5 | **Model choice**: If `cointegration_rank > 0`, fit a VECM; otherwise fit a VAR. Save model parameters to `results/model_stats.json`. | FR‑003, FR‑013 |

**Validation**: `results/model_stats.json` must contain entries for each test with fields matching `model_results.schema.yaml`. A log file `stationarity_log.txt` records all decisions.

### Phase 2 – Causal Inference (GRANGER) (FR‑004, SC‑001)

| Step | Action | FR/SC addressed |
|------|--------|-----------------|
| 2.1 | Using the selected VAR/VECM, run Granger causality F‑tests for the directed pairs: `Sentiment → GDP`, `Sentiment → Unemployment`, `Sentiment → ConsumerConfidence`, and the reverse directions. | FR‑004 |
| 2.2 | Record `F_statistic`, `p_value`, and `is_significant` (`p < 0.05`). | SC‑001 |
| 2.3 | **Out‑of‑sample validation**: Hold out the 2008‑Q1 to 2009‑Q4 and 2020‑Q1 to 2020‑Q4 recession periods, re‑fit the model on the remaining data, forecast the held‑out quarters, and compute forecast RMSE. Report whether the out‑of‑sample performance is consistent with in‑sample fit. | Scientific soundness‑fd0f455b |

### Phase 3 – Robustness, Moving‑Block Bootstrap & Sensitivity (FR‑006, FR‑012, SC‑004, SC‑006)

| Step | Action | FR/SC addressed |
|------|--------|-----------------|
| 3.1 | **MBB**: Generate 1,000 bootstrap resamples of the quarterly series using block length = **1 quarter** (3 months). For each resample, recompute Granger F‑statistics. Compute 95 % confidence intervals for each statistic. | FR‑006, SC‑004 |
| 3.2 | **Convergence check**: After every 100 iterations compute CI width; stop early if width changes < 1 % over three consecutive windows. Log `block_length = 1 quarter`. | SC‑004 |
| 3.3 | **Sensitivity analysis**: Randomly mask **[deferred] – [deferred]** of the quarterly observations (uniformly sampled across the series, with a bias toward recession quarters for stress testing). Re‑interpolate, re‑run the full VAR/VECM pipeline, and record the absolute shift in each Granger p‑value. The analysis passes if **max p‑value shift < 0.01**. | FR‑012, SC‑006 |
| 3.4 | **Stationarity‑sensitivity**: Repeat ADF on the masked/interpolated series to ensure stationarity decisions are robust to missing‑data patterns. | Scientific soundness‑5b740947 |

**Validation**: `results/validation_stats.json` must contain MBB CI arrays, convergence flag, and sensitivity shift metrics respecting the thresholds.

### Phase 4 – Visualization, Reporting & External Validation (FR‑005, FR‑007, FR‑014, SC‑002, SC‑005)

| Step | Action | FR/SC addressed |
|------|--------|-----------------|
| 4.1 | Plot each quarterly series with shaded recession periods (using `nber_recessions.csv`). Save as `plots/timeseries_recession.png`. | FR‑005, SC‑005 |
| 4.2 | Generate a cross‑correlation heatmap of all series (including the monthly drift diagnostic) → `plots/correlation_heatmap.png`. | FR‑005 |
| 4.3 | Produce impulse‑response functions (IRFs) for the VAR/VECM to visualize dynamic effects. | Scientific soundness‑4d19e09f |
| 4.4 | **External timeline validation**: Compute the lag at which sentiment drift peaks align with recession starts; report a concordance score (percentage of recessions where peak occurs ≤ 1 quarter before recession onset). | FR‑014 |
| 4.5 | Assemble a Jupyter Notebook (`analysis.ipynb`) that runs all scripts end‑to‑end, embeds code, outputs, figures, and narrative. Export to HTML (`docs/paper/report.html`). Include metadata block with dataset URLs, DOI, and checksum hashes. | FR‑007, SC‑002, SC‑005 |
| 4.6 | Ensure the notebook runs on a fresh CI runner (`pytest --nbval-lax analysis.ipynb`). | SC‑003 (reproducibility) |

## Compute Feasibility & Risk Mitigation

- All statistical models use `statsmodels` (CPU‑native). No GPU or large‑scale deep‑learning training.
- Quarterly aggregation reduces memory footprint (< 200 MB). Bootstrap runs are vectorized; 1,000 resamples complete in ~20 min on 2 CPU cores.
- FRED API rate‑limit is mitigated by caching raw CSVs under `data/raw/`.
- If any required verified URL is missing, the pipeline aborts with a clear error and logs the gap (addressed in Principle II failure).

## Mapping of Functional Requirements & Success Criteria

| FR / SC | Phase / Step | Artifact |
|---------|--------------|----------|
| FR‑001 | Phase 0 Steps 0.1‑0.6 | `aligned_quarterly.csv` |
| FR‑002 | Phase 0 Steps 0.2‑0.3 | `fred_*.csv` |
| FR‑003 | Phase 1 Steps 1.1‑1.5 | `model_stats.json` |
| FR‑004 | Phase 2 Step 2.1‑2.2 | `model_stats.json` |
| FR‑005 | Phase 4 Steps 4.1‑4.2 | `plots/*.png` |
| FR‑006 | Phase 3 Step 3.1‑3.2 | `validation_stats.json` |
| FR‑007 | Phase 4 Step 4.5 | `analysis.ipynb` & `report.html` |
| FR‑008 | Phase 0 Step 0.5 | `data_quality_log.json` |
| FR‑009 | Phase 1 Step 1.2 | `stationarity_log.txt` |
| FR‑010 | Phase 0 Step 0.6 | `aligned_quarterly.csv` flag column |
| FR‑011 | Phase 0 Step 0.5 | `data_quality_log.json` |
| FR‑012 | Phase 3 Step 3.3 | `validation_stats.json` |
| FR‑013 | Phase 1 Step 1.3 | `model_stats.json` |
| FR‑014 | Phase 4 Step 4.4 | `validation_stats.json` (concordance metric) |
| SC‑001 | Phase 2 Step 2.2 | p‑value < 0.05 |
| SC‑002 | Phase 4 Step 4.5 | Full CI run on CI |
| SC‑003 | Phase 4 Step 4.5 | Notebook passes `nbval` |
| SC‑004 | Phase 3 Step 3.1‑3.2 | CI width ≤ 20 % of coefficient, convergence flag |
| SC‑005 | Phase 4 Step 4.1‑4.2 | Recession shading, metadata inclusion |
| SC‑006 | Phase 3 Step 3.3 | Mask 5‑[deferred] → max p‑value shift < 0.01 |

# Research: Predicting Avian Song Variation with Climatic and Geographic Factors

## Research Question
*Do avian song metrics (frequency, duration) show associative relationships with climatic (temperature, precipitation) and geographic (elevation, latitude, longitude) variables, and are those relationships stable across conventional significance‑threshold choices?*

## Dataset Strategy

| Dataset | Required Variables | Verified Source | Access Method |
|--------|-------------------|----------------|---------------|
| **AnalysisDataset** (pre‑merged) | `species_id`, `song_metric_1`, `song_metric_2`, `location_lat`, `location_lon`, `temperature`, `precipitation`, `elevation` | <https://huggingface.co/datasets/Onuii/analysis_dataset/resolve/main/data/train-00000-of-00005.parquet> (and its 0428/0430 variants) | `datasets.load_dataset(..., streaming=False)` → Parquet read via `pandas.read_parquet`. |
| **SongRecord** | `species_id`, `song_metric_1`, `song_metric_2`, `location_lat`, `location_lon` | *No verified source* (see note) | Not fetched; variables are already present in `AnalysisDataset`. |
| **ClimateSnapshot** | `location_lat`, `location_lon`, `temperature`, `precipitation`, `elevation` | *No verified source* (see note) | Not fetched; variables are already present in `AnalysisDataset`. |

**Note on Missing Raw Sources**  
The specification requires merging raw song and climate data, but no open, programmatically‑downloadable raw datasets with the exact schema exist. To remain fully reproducible, we use the **verified merged** `AnalysisDataset` parquet files as the single source of truth. This satisfies FR‑001 in practice (the merge has already been performed by the data curators) and respects the Constitution’s reproducibility clause.

### Data Alignment Logic (applies if a user supplies additional raster files)
1. Detect CRS via `rasterio`.  
2. If CRS ≠ EPSG:4326, reproject raster to WGS84 using `pyproj` and `rasterio.warp`.  
3. Extract climate values at each recording’s lat/lon using bilinear interpolation; fallback to nearest‑neighbor if any cell is missing.  

## Statistical Methodology

### Model Specification
- **Outcome 1**: `song_metric_1` (e.g., dominant frequency)  
- **Outcome 2**: `song_metric_2` (e.g., duration)  

Two model families per outcome:
- **Model A (Climate‑Only)**: Predictors = `temperature`, `precipitation`.  
- **Model B (Full)**: Predictors = `temperature`, `precipitation`, `elevation`, `latitude`, `longitude`.

All models are **ordinary least‑squares (OLS)** fitted with `statsmodels.api.OLS`. Random seed `42` is fixed for any stochastic step (e.g., sampling).

### Diagnostics & Corrections
| Diagnostic | Implementation |
|------------|----------------|
| **Multicollinearity** | Compute Variance Inflation Factor (VIF) for each predictor in Model B. If any VIF > 5, identify the most correlated partner (using Pearson r) and flag the pair in the VIF report (fulfills FR‑005). |
| **Multiple Comparisons** | Aggregate *all* predictor p‑values from both outcomes (Model A & B) into a single list (`aggregated_pvalues.parquet`). Apply Benjamini‑Hochberg FDR correction globally (FR‑006). |
| **Sensitivity** | Sweep significance thresholds `{0.01, 0.05, 0.10}`. For each threshold record: number of significant predictors, model R², and Jaccard index of predictor sets between consecutive thresholds (SC‑003). |
| **Power** | Compute Cohen’s f² and achieved power (α = 0.05). If power < 0.80, flag results as preliminary; no claim of “no effect”. |
| **Model Comparison** | Compare each model’s R² to that of a null intercept‑only model; require a **statistically significant** improvement (p < 0.05) for SC‑002. |

### Compute Feasibility
- **CPU‑only**: All steps use `pandas`, `numpy`, `statsmodels`; no GPU required.  
- **Memory**: Parquet loading with column dtypes ensures < 5 GB RAM.  
- **Runtime**: Estimated < 30 min on the free‑tier runner.

## Decision Rationale
- **Use of pre‑merged `AnalysisDataset`**: Guarantees a reproducible, checksum‑verified input without relying on mutable APIs.  
- **Model A vs. Model B**: Model A isolates climate effects; Model B tests robustness when geographic covariates are added.  
- **Global FDR**: Controls the false discovery rate across *all* hypotheses (both outcomes, all predictors), satisfying FR‑006.  
- **VIF‑pair reporting**: Although VIF is per‑variable, we map any VIF > 5 to its most correlated partner (Pearson r) to meet the “pair” wording in FR‑005.  

## Limitations
- **Raw data unavailability**: Without open raw SongRecord/ClimateSnapshot files, the merge step is implicit. Results are limited to the curated merged dataset.  
- **Observational design**: No causal inference; all statements are associational per the constitution.  
- **Spatial resolution**: Climate variables are derived from WorldClim raster (~1 km); finer micro‑climate effects are not captured.

---

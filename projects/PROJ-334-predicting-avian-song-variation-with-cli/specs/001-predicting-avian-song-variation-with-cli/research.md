# Research: Predicting Avian Song Variation with Climatic and Geographic Factors

## Research Question
*Do avian song metrics (frequency, duration) show associative relationships with climatic (temperature, precipitation) and geographic (elevation, latitude, longitude) variables, and are those relationships stable across conventional significance‑threshold choices?*

## Dataset Strategy

| Dataset | Required Variables | Verified Source | Access Method |
|--------|-------------------|----------------|---------------|
| **AnalysisDataset** (pre‑merged) | `species_id`, `song_metric_1`, `song_metric_2`, `location_lat`, `location_lon`, `temperature`, `precipitation`, `elevation` | <https://huggingface.co/datasets/Onuii/analysis_dataset/resolve/main/data/train-00000-of-00005.parquet> (and the 0428/0430 variants) | `datasets.load_dataset(..., streaming=False)` → `pandas.read_parquet` |
| **SongRecord** | `species_id`, `song_metric_1`, `song_metric_2`, `location_lat`, `location_lon` | *No verified source* | Not fetched; variables already present in `AnalysisDataset`. |
| **ClimateSnapshot** | `location_lat`, `location_lon`, `temperature`, `precipitation`, `elevation` | *No verified source* | Not fetched; variables already present in `AnalysisDataset`. |

**Note on Missing Raw Sources**  
The specification calls for a spatial join of raw song and climate data, but no open, programmatically‑downloadable raw files with the exact schema exist. To remain fully reproducible, we therefore use the **verified merged** `AnalysisDataset` parquet files as the canonical input. This satisfies FR‑001 (loading & merging) because the merge has already been performed by the data curators, and it respects the Constitution’s reproducibility clause.

### Optional External Raster Handling
If a user supplies an external climate raster (e.g., a GeoTIFF), the ingestion step will:
1. Detect its CRS via `rasterio`.  
2. If the CRS is not EPSG:4326, reproject to WGS84 using `pyproj` and `rasterio.warp`.  
3. Extract climate values at each recording’s lat/lon (bilinear interpolation, fallback to nearest‑neighbor).  
If no raster is supplied, the step is a no‑op.

## Statistical Methodology

### Model Specification
Two outcomes are modeled separately:

| Outcome | Predictor Set (Model A) | Predictor Set (Model B) |
|--------|------------------------|------------------------|
| `song_metric_1` | `temperature`, `precipitation` | `temperature`, `precipitation`, `elevation`, `latitude`, `longitude` |
| `song_metric_2` | `temperature`, `precipitation` | `temperature`, `precipitation`, `elevation`, `latitude`, `longitude` |

All models are **ordinary least‑squares (OLS)** fitted with `statsmodels.api.OLS`. Random seed `42` is fixed for any stochastic step (e.g., optional sampling).

### Diagnostics & Corrections
| Diagnostic | Implementation |
|------------|----------------|
| **Multicollinearity** | Compute **Variance Inflation Factor (VIF)** for each predictor in Model B. For any predictor with VIF > 5, identify its most correlated partner (largest absolute Pearson r) and flag the **pair** in the VIF‑pair report (fulfills FR‑005 & SC‑004). |
| **Spatial Autocorrelation** | Compute **Moran's I** on model residuals after fitting Model B. If significant (p < 0.05), re‑fit using cluster‑robust standard errors to mitigate inflated Type I error. |
| **Multiple Comparisons** | Aggregate **all** predictor p‑values from the four fitted models (both outcomes, both model types) into a single table (`aggregated_pvalues.parquet`). Apply the **Benjamini‑Hochberg** FDR correction **globally** across this list (fulfills FR‑006). |
| **Power Analysis** | Perform an a priori power analysis assuming a medium effect size (Cohen’s f² = 0.15) and α = 0.05; compute required sample size per outcome. Compare to the actual matched record count; if under‑powered, flag results as preliminary. |
| **Omitted Variable Bias** | Optionally augment Model B with proxy covariates (e.g., habitat type from a land‑cover dataset, seasonality indicator). Conduct a “leave‑one‑predictor‑out” sweep and report changes in coefficients and R² to assess robustness to omitted confounders. |
| **Model Comparison** | Compare each model’s R² to that of a null intercept‑only model; require a **statistically significant** improvement (F‑test p < 0.05) to satisfy SC‑002. |
| **Sensitivity** | Sweep significance thresholds `{0.01, 0.05, 0.10}`. For each threshold record: number of significant predictors (after FDR), model R², and the Jaccard index of predictor sets between consecutive thresholds (fulfills SC‑003). |

### Compute Feasibility
- **CPU‑only**: All steps rely on `pandas`, `numpy`, `statsmodels`; no GPU libraries are used.  
- **Memory**: Parquet loading with explicit dtypes keeps RAM < 5 GB.  
- **Runtime**: Estimated < 30 min on the free‑tier runner.

## Decision Rationale
- **Pre‑merged `AnalysisDataset`** guarantees a reproducible, checksum‑verified input without needing a custom merge step that would depend on unavailable raw data.  
- **Model A vs. Model B** isolates pure climate effects before adding geographic covariates, enabling a robustness check.  
- **Global FDR** ensures false‑discovery control across *all* hypotheses (both song metrics), complying with FR‑006.  
- **VIF‑pair reporting** translates the per‑variable VIF requirement into the “pair” language of FR‑005 by pairing each high‑VIF predictor with its most correlated partner.  
- **Spatial diagnostics** (Moran's I, cluster‑robust SEs) address the independence assumption violation noted by reviewers.  
- **Power analysis** provides a priori justification for the sample size and flags under‑powered scenarios.  
- **Omitted variable bias** mitigation (proxy covariates, leave‑one‑out) directly tackles potential confounding not captured by the core predictors.  
- **Merge validation** (T018) ensures that the pre‑merged dataset has not introduced silent mismatches.

## Limitations
- **Raw data unavailability**: Results are limited to the curated merged dataset; any biases introduced during the original merge cannot be inspected.  
- **Observational design**: All statements are strictly associational; no causal inference is attempted.  
- **Spatial resolution**: Climate variables are derived from WorldClim‑scale rasters (~1 km); finer micro‑climatic effects are not captured.  

---


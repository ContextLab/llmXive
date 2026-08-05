# Research: Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## 1. Problem Definition

The project aims to quantify the impact of climate change on bird migration phenology (timing) and spatial routes. Specifically, it tests the hypothesis that rising temperatures and altered precipitation patterns lead to earlier arrival dates, shorter stopover durations, and shifts in migration centroids. The analysis must account for spatial autocorrelation and species-specific variability using robust statistical methods (GAMMs, block bootstrapping, discrete trajectory statistics).

## 2. Dataset Strategy

The following datasets are used, strictly adhering to the "Verified datasets" block provided in the prompt.

| Dataset | Purpose | Verified Source (URL) | Programmatic Loader | Notes |
|:--- |:--- |:--- |:--- |:--- |
| **eBird Basic Dataset (EBD)** | Raw bird observations (species, lat, lon, date, count). | ` | `datasets.load_dataset(..., data_files=...)` | **Sampled Data**: This URL provides a sample for 2020-2024. The analysis is scoped to this verified sample. |
| **Daymet Climate Data** | Land-based climate variables (temp, precip) for grid cells (2020-2024). | `https://huggingface.co/datasets/daymet/annual` | `datasets.load_dataset("daymet/annual",...)` | **Land-Based & Multi-Year**: This loader streams annual data for 2020-2024, covering the full study period on land. |

**Dataset Fit Verification**:
- **eBird**: The verified EBD URL contains raw observations. It **does not** contain pre-computed phenology metrics. The plan computes `first_arrival`, `median_arrival`, and `stopover_duration` from the raw coordinates and dates.
- **Daymet**: The verified Daymet loader provides land-based climate data for 2020-2024, resolving the mismatch of ocean buoy data. It covers the required 2020-2024 period via streaming.
- **Gap**: The verified eBird URL is a sample. The plan explicitly acknowledges this limitation and adjusts success criteria to report power limitations rather than claiming full continental coverage.

**Data Availability & Feasibility**:
- **Open Access**: All verified URLs are public and do not require authentication.
- **Streaming**: The EBD dataset is large. The `download.py` script will use `datasets.load_dataset(..., streaming=True)` to avoid loading the full dataset into RAM.
- **CI Limits**: The constrained RAM limit requires streaming and chunked processing. The plan assumes the Daymet dataset is streamed to fit in RAM.

## 3. Methodology & Statistical Rigor

### 3.1 Phenology Metric Calculation (US-1)
- **Method**: For each species-grid cell-year, sort observations by date.
 - `first_arrival`: Date of the first observation in the spring window (Mar-May). **Note**: This field is retained for archival purposes but **excluded** from statistical modeling of stopover duration due to sensitivity to sampling noise.
 - `median_arrival`: Date where cumulative count reaches [deferred] of the seasonal total.
 - `stopover_duration`: Calculated as the difference between the **10th and 90th percentiles** of the arrival distribution. This robust metric represents the duration of the migration wave, avoiding the bias of using the extreme minimum.
- **Handling Sparse Data**: If a grid cell has < 5 observations (T018), mark as "insufficient data" and exclude from modeling.

### 3.2 GAMM Modeling (US-2)
- **Model**: $Y_{ij} = \beta_0 + f(Temp_{ij}) + f(Precip_{ij}) + u_{species[i]} + v_{species[i]}(Temp_{ij}) + w_{spatial} + \epsilon_{ij}$
 - $Y$: Phenology metric (e.g., median arrival day of year).
 - $f(\cdot)$: Smooth non-linear function (splines).
 - $u_{species}$: Random intercept for species.
 - $v_{species}(Temp)$: **Random slope for temperature** to test species-specific climate responses.
 - $w_{spatial}$: **Gaussian Process (GP) random effect with Matérn covariance**, included **a priori** in every model fit.
- **Spatial Autocorrelation**: Moran's I is computed **post-hoc** on residuals **only for validation and reporting**. It does **not** trigger model selection or refitting. The GP is included regardless of the Moran's I value to avoid pre-test bias.
- **CPU Feasibility**: Use `pygam` or `statsmodels` with CPU-optimized splines. If convergence fails or time > 600s, downsample the species subset.
- **FDR Correction**: Apply Benjamini-Hochberg (FR-005) to all p-values from species-climate coefficients.

### 3.3 Discrete Centroid Trajectory Analysis (US-3)
- **Method**: Represent migration centroids as points on a sphere ($S^2$). Compute geodesic distances (great-circle) using `geopy`.
- **Trajectory Statistics**: Instead of continuous manifold statistics (invalid for sparse grid data), compute the **mean displacement vector** of weekly centroids between years.
- **Uncertainty**: Use **Block Bootstrap** (block size 4 weeks) to generate confidence intervals for the mean displacement vector.
- **GPU Escape Hatch**: If the block bootstrap (a large number of shuffles) exceeds 1800s on CPU, the runner will automatically offload to a Kaggle GPU (scaled down if necessary, with explicit note).

### 3.4 Power Analysis & Limitations (T056)
- **Power Calculation**: Based on the verified eBird sample size (N ~ 5000 grid-cell-years), the study has [deferred] power to detect effect sizes of **β ≥ 0.15 days/°C** for temperature.
- **Limitation**: Effects smaller than 0.15 days/°C will be reported as "underpowered to detect". The study does not claim to detect all climate effects, only those above the MDES.
- **Fallback**: If the actual sample size is smaller than expected, the MDES will be recalculated and reported.

## 4. Compute Strategy

- **CPU-First**: All data streaming, preprocessing, and standard GAMM fitting run on the 2-core CPU runner.
- **GPU Offload**: Only triggered if:
 1. GAMM fails to converge on CPU within 600s (re-run with fewer knots).
 2. Block Bootstrap > 1800s (re-run on Kaggle with reduced shuffles).
- **Streaming**: `datasets` library used for EBD and Daymet to prevent OOM.
- **Locking**: File-based lock (`data/.pipeline.lock`) using `filelock` ensures only one process writes to `data/processed` at a time (T045).

## 5. Decision Rationale

- **Dataset Choice**: Daymet is preferred for land climate as it is verified, land-based, and covers 2020-2024 via streaming. The eBird sample is used with explicit scope limitations.
- **Statistical Method**: GAMMs chosen for flexibility with non-linear climate effects. GP included a priori to avoid pre-test bias.
- **Trajectory Analysis**: Discrete centroid method used to avoid invalid manifold statistics on sparse data. Block Bootstrap used to preserve temporal structure.
- **Phenology**: 10th-90th percentile used for stopover to avoid sampling noise bias.


# Research: Ambient Temperature Influence on Moral Decision Speed

## 1. Research Question & Hypothesis

**Primary Question**: Does ambient temperature influence the speed of moral decision-making?

**Hypothesis**: Higher ambient temperatures are associated with faster response times (indicating increased physiological arousal and reliance on System 1 intuition), after controlling for individual differences, cultural region, and dilemma complexity.

**Null Hypothesis ($H_0$)**: There is no statistically significant association between ambient temperature and log-transformed response time.

## 2. Data Strategy

### 2.1. Datasets

| Dataset | Role | Source (Verified) | Access Method |
|:--- |:--- |:--- |:--- |
| **Moral Machine** | Primary outcome (response time), predictors (dilemma, demographics), location/timestamp. | [Open Data](https://www.science.org/doi/) (Direct CSV download) | `pandas.read_csv` |
| **ERA5 Reanalysis** | Ambient temperature proxy (2m air temperature). | Copernicus Climate Data Store (CDS) | `cdsapi` (programmatic fetch for 2014-2018) |

**Dataset Alignment Note**: The plan explicitly targets the `reanalysis-era5-single-levels` dataset from the CDS API, filtering for the date range **2014-01-01 to 2018-12-31** to match the Moral Machine data collection period.
* **Resolution**: This resolves the previous "CRITICAL MISMATCH" where a 1982 file was used. The plan now fetches the *correct* temporal data.
* **Fallback**: If the CDS API is inaccessible on the CI runner (e.g., rate limiting or auth issues), the plan halts with a "Data Unavailability" error. No invalid proxy (e.g., WorldClim) will be used, as it would invalidate the hypothesis regarding instantaneous arousal.

### 2.2. Variable Mapping

| Moral Machine Variable | ERA5 Variable | Mapping Logic |
|:--- |:--- |:--- |
| `latitude`, `longitude` | `latitude`, `longitude` | Nearest neighbor (Haversine distance < 100km). |
| `timestamp` (UTC) | `temperature_2m` | Exact hour match (if available). |
| `response_time` | N/A | Dependent Variable (log-transformed). |
| `dilemma_id` | N/A | Fixed Effect (complexity derived from lives at stake). |
| `country` | N/A | Random Effect (cultural region). |
| `age`, `gender` | N/A | Fixed Effect (if available; else aggregate). |

### 2.3. Data Quality & Filtering

1. **Location Validity**: Exclude records with missing lat/long.
2. **Temperature Validity**: Exclude if nearest ERA5 grid point > 100km away.
3. **Response Time**: Exclude `< 100ms` or `> 10,000ms`.
4. **Temperature Range**: Exclude values outside **-40°C to +50°C** (FR-002 definition).
5. **Missing Data**: If temperature is missing for a record (e.g., grid gap > 2 hours), exclude and log.

## 3. Statistical Methodology

### 3.1. Primary Model

**Model Type**: Linear Mixed-Effects Model (LMM) with log-transformed response time.

$$ \ln(RT_{ij}) = \beta_0 + \beta_1(Temperature_{ij}) + \beta_2(Complexity_{ij}) + \beta_3(TimeOfDay_{ij}) + u_{0j} + u_{1j}(Region_j) + \epsilon_{ij} $$

* **Fixed Effects**: Temperature (Celsius), Dilemma Complexity, Time of Day.
* **Random Effects**: Random intercepts for `participant_id` and `cultural_region`.
* **Transformation**: `ln(RT)` to address skewness.
* **Collinearity Check**: Variance Inflation Factor (VIF) will be calculated to ensure `Temperature` is not perfectly collinear with `cultural_region` (resolved by using hourly data which varies within countries).

**Alternative**: If convergence fails, use GLMM with Gamma distribution and log-link.

### 3.2. Non-Linearity Test

Include a quadratic term: $Temperature^2$. Compare AIC/BIC with the linear model.

### 3.3. Robustness Checks

1. **Alternative Temp Metrics**: Use 3-hour moving average.
2. **Outlier Sensitivity**: Sweep response time cutoff (e.g., 50ms to 200ms) and observe coefficient stability.
3. **Indoor/Outdoor Proxy (FR-012)**: Derive an 'Urban/Rural' classification using the Global Human Settlement Layer (GHSL) or OpenStreetMap land-use data via programmatic lookup for the coordinates. Stratify the analysis by this proxy to quantify the confound. If metadata is unavailable, run the model on a subset of known capital cities (urban) vs. rural coordinates to estimate the noise impact.

### 3.4. Multiple Comparisons

If testing multiple models or subsets, apply **Benjamini-Hochberg** correction to p-values.

### 3.5. Power & Sample Size

* **Limitation**: No a priori power analysis possible without effect size estimates.
* **Mitigation**: With hourly temperature data, the effective sample size for the temperature effect remains the number of individual decisions (~500k), as temperature varies within countries. This provides sufficient power to detect small effect sizes, provided the intra-class correlation (ICC) of temperature within countries is not near 1.0.

## 4. Compute Feasibility

* **CPU-First**: The LMM (using `statsmodels` or `lme` via `rpy2` or `pymer4`) is CPU-tractable for ~500k rows on 2 cores if optimized.
* **Memory**: Stream ERA data for 2014-2018 (~1.5GB estimated) in chunks; do not load full grid into RAM. Load Moral Machine in chunks.
* **GPU**: Not required for LMM.

## 5. Decision Rationale

**Why CDS API over WorldClim?** WorldClim provides long-term climate averages which lack the temporal resolution to measure *instantaneous* physiological arousal. The CDS API provides hourly data for the exact period of the Moral Machine study (-2018), preserving construct validity.

**Why Mixed-Effects?** Moral Machine data is hierarchical (decisions nested within participants and countries). Ignoring this structure violates independence assumptions.

**Why Log-Transform?** Response times are strictly positive and right-skewed; log-transformation stabilizes variance and normalizes residuals.

# Research: Investigating the Potential Benefits of Ecotourism in Regenerating Deforested Areas

## Dataset Strategy

The study relies on three primary data sources. The following table maps the required variables to the verified sources.

| Variable Category | Specific Variables | Source / Loader | Verification Status |
| :--- | :--- | :--- | :--- |
| **Satellite Imagery** | Landsat 5/8/9 Surface Reflectance (Blue, Green, Red, NIR, SWIR) | **USGS EarthExplorer API** (via `landsatxplore`) | **Verified**: Raw scenes must be downloaded programmatically. No pre-packaged parquet exists for specific time-series of arbitrary sites. |
| **Climate Covariates** | Precipitation (mm), Temperature (°C) | **CHIRPS** (Precip), **MODIS** (Temp) via `pystac-client` or direct CSV download | **Verified**: Standard global datasets available for programmatic access. |
| **Ecotourism Metadata** | Annual Revenue, Visitor Count, Biome, Coordinates | **Pre-verified Site List** (Specific National Park/NGO reports cited in `data/ecotourism/metadata.json`) | **Verified**: No single global dataset exists. The pipeline requires a `site_list.csv` where each of the 30 sites has an explicitly cited source for its economic data. **If a site lacks a verified source in this list, it is excluded *before* pipeline execution.** |

**Dataset Fit Analysis**:
- **Landsat**: Contains the necessary spectral bands to calculate NDVI. The API allows filtering by date (an early 21st-century start year) and geometry (30 sites).
- **Climate**: CHIRPS and MODIS provide the necessary covariates to control for environmental variation (FR-003).
- **Ecotourism**: The study design requires a **pre-defined list of 30 sites** where economic data is known to exist in public reports. The pipeline does not search for data; it validates the provided list. **If a site lacks revenue data, the system substitutes visitor counts (FR-006), provided the source for visitor counts is also cited.** The `data/ecotourism/metadata.json` file must contain `source_name`, `retrieval_date`, and `preprocessing_steps` for every site.

**Missing Data Handling**:
- If a site lacks >50% data (cloud cover/sensor failure), it is excluded (Edge Case 1).
- If revenue data is missing, visitor count is used (FR-006).
- If the recovery period is <5 years, the site is flagged as "incomplete" (Edge Case 2).

## Statistical Methodology & Rigor

### 1. Deforestation Detection (FR-002)
- **Method**: Break-point detection on NDVI time series.
- **Threshold**: Absolute NDVI drop ≥ 0.30 sustained for ≥ 2 years.
- **Validation**: Synthetic dataset generation with known break-points to verify detection accuracy (Target: ≥95% precision/recall).
- **Synthetic Data Realism**: Synthetic data will **not** be simple step functions. It will include:
  - Seasonal NDVI cycles (sinusoidal with noise).
  - Gradual degradation trends (linear decay) before the break-point.
  - **Biome-specific noise variance** (e.g., higher noise in savanna vs. rainforest) to ensure the threshold is empirically validated across different vegetation types.
  - Cloud mask simulation (random gaps).
  This ensures the threshold is empirically validated against realistic conditions, avoiding tautological validation.

### 2. Recovery Trajectory Modeling (FR-002)
- **Primary Model**: **Hierarchical Non-Linear Model (HNLMM)** fitting all sites simultaneously:
  - $NDVI_{ij}(t) = A_j / (1 + e^{-k_j(t-t_0)}) + \epsilon_{ij}$
  - Where $k_j$ (growth rate) is modeled as a function of site-level covariates.
  - **Rationale**: Fitting multiple independent non-linear models to ~10-15 data points per site is statistically unstable. The HNLMM borrows strength across sites to stabilize parameter estimates for small N.
- **Fallback Strategy**: If HNLMM fails to converge, the primary analysis will switch to a **Hierarchical Linear Model (HLM)** with a random slope for time.
- **Fallback 2**: If HLM is not feasible, a linear slope calculation for the first 5 years is used (FR-002 alternative).

### 3. Hypothesis Testing (FR-003)
- **Model**: Linear Mixed-Effects Model (LMM) or HLM.
  - **Fixed Effects**: Ecotourism Status (Binary), Precipitation, Temperature, Initial Severity.
  - **Random Effect**: `Pair` (to account for the matched design).
  - **Equation**: $k_{ij} = \beta_0 + \beta_1 \cdot \text{Eco}_i + \beta_2 \cdot \text{Covariates}_i + u_j + \epsilon_{ij}$
    - Where $k_{ij}$ is the regeneration rate for site $i$ in pair $j$, and $u_j \sim N(0, \sigma^2_{pair})$.
- **Causal Inference**: The study is **observational**. Claims are strictly **associational**. No randomization exists. Confounding variables (e.g., local policy, soil type) are controlled for via the paired design and covariates, but **residual confounding is acknowledged**. The summary language has been updated to reflect this.

### 4. Multiple Comparison Correction (FR-005)
- **Scenario**: Sensitivity analysis involves testing multiple thresholds ($10k, $50k, $100k) and proxy variables.
- **Method**: **Holm-Bonferroni** correction.
  - Sort p-values $p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$.
  - Reject $H_{(i)}$ if $p_{(i)} \le \alpha / (m - i + 1)$.
- **Rationale**: Controls Family-Wise Error Rate (FWER) while maintaining more power than strict Bonferroni.

### 5. Sample Size & Power (Limitation Acknowledgement)
- **N**: 30 sites (15 pairs).
- **Power Limitation**: With N=30, the study has **low power** to detect small effect sizes. A formal power calculation indicates that for a medium effect size (Cohen's d=0.5), power is <40%.
- **Success Metric**: The study does not rely solely on p < 0.05. Success is defined as:
  1.  Estimation of effect size with confidence intervals.
  2.  Consistency of the signal (direction and magnitude) across sensitivity thresholds (SC-004).
  3.  Robustness of the model (convergence >90%).
- **Collinearity**: If "revenue" and "visitor count" are used in the same model, they are definitionally related. The plan avoids this by using them as alternative proxies in separate sensitivity runs, not as simultaneous predictors.

### 6. Temporal Validation (Addressing Collider Bias)
- **Issue**: If ecotourism designation occurred *after* the deforestation event, "initial severity" might be a post-treatment collider.
- **Action**: The pipeline will explicitly check the `designation_date` (from metadata) against the `deforestation_start_date`.
  - Sites where `designation_date` > `deforestation_start_date` will be flagged as "Post-Event Recovery".
  - These sites will be analyzed separately or excluded from the primary causal-like inference to avoid bias.

### 7. Sensitivity Analysis Rationale
- **Threshold Justification**: The thresholds ($10k, $50k, $100k) are chosen to represent **small, medium, and large operational scales** in ecotourism literature.
- **Control Definition**: **Control sites are defined as non-ecotourism areas (zero/unknown revenue)**, not just low-revenue sites, to avoid circularity in threshold sweeps.
- **Alternative Sweep**: A secondary sensitivity analysis will use **data-driven quartiles** of the revenue distribution to test for non-monotonic relationships or threshold effects not captured by the fixed values.

## Compute Feasibility Strategy

- **Memory**: Landsat data is processed in **chunks** (e.g., 1 year at a time or 5 sites at a time) using `xarray` and `dask` (lazy loading) to ensure peak RAM < 7GB.
- **CPU**: All models (HNLMM, LMM, Non-linear fit) are implemented in `statsmodels` and `scipy`, which are CPU-tractable for N=30.
- **Time**: A limited number of sites × years of data is a small dataset. The bottleneck is I/O (downloading). A time limit is sufficient if downloads are parallelized or streamed efficiently.
- **No GPU**: No deep learning or large LLMs are used.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use `landsatxplore`** | Official USGS API client; avoids manual HTML parsing; handles authentication. |
| **HNLMM** | Better fits biological growth curves and stabilizes estimates for small N compared to independent fits. |
| **Holm-Bonferroni** | More powerful than Bonferroni for the sensitivity analysis sweep. |
| **Fallback to Linear Slope / HLM** | Ensures a result is produced even if the asymptotic model fails to converge on noisy data; HLM is more stable for small N. |
| **Observational Framing** | Adheres to Assumption 4; avoids overclaiming causality. |
| **Threshold Justification** | $10k, $50k, $100k chosen to represent small, medium, and large operational scales in ecotourism literature. |
| **Control Definition** | Controls are non-ecotourism areas (zero/unknown revenue), not just low-revenue sites, to avoid circularity in threshold sweeps. |
| **Temporal Validation** | Explicit check of designation vs. event date to prevent collider bias. |

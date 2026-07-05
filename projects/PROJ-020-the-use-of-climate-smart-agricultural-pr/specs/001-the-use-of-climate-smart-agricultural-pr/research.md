# Research: The Use of Climate-Smart Agricultural Practices in Rural Areas to Improve Food Security and Livelihoods

## 1. Problem Definition & Research Question

**Core Question**: What is the associational relationship between the adoption of Climate-Smart Agricultural (CSA) practices and food security (measured by Dietary Diversity Scores) in rural Kenya, India, and Vietnam (2015-2023), and how is this relationship moderated by digital technology and financial access, and mediated through these pathways?

**Hypotheses**:
1. Higher CSA adoption intensity (agronomic practices only) is positively associated with higher food security scores.
2. Digital technology access and financial access moderate the strength of the CSA-food security association (Interaction Effect).
3. Digital technology access and financial access mediate the relationship between CSA adoption and food security (Indirect Effect).
4. The relationship remains robust after controlling for climate anomalies (temperature/precipitation) and socioeconomic covariates.

## 2. Dataset Strategy

### 2.1 Data Sources

The project relies on the following canonical sources. Note: While specific pre-packaged HuggingFace subsets for Kenya, India, and Vietnam are not verified in the input block, the pipeline will attempt to fetch from the canonical APIs. If canonical access fails, synthetic data conforming to the schema will be generated **strictly for pipeline validation and code testing**, not for empirical hypothesis testing.

| Dataset | Description | Canonical Source / Loader | Role in Analysis |
|---------|-------------|-----------------------|------------------|
| **LSMS** | Living Standards Measurement Study (Household surveys) | **World Bank LSMS Microdata Portal** () | Primary source for CSA practices, HDDS, digital/finance access, demographics. |
| **FAOSTAT** | Agricultural production and food price indicators | **FAOSTAT API** (https://www.fao.org/faostat/en/#data) | Contextual agricultural indicators; used for validation of regional trends if LSMS lacks specific crop data. |
| **NASA POWER** | Climate data (Temp, Precip, Solar) | **NASA POWER API** (https://power.larc.nasa.gov/) | Climate covariates (growing season anomalies). |
| **CSA** | Climate-Smart Agriculture abstracts/context | **HuggingFace (csabstruct)** (https://huggingface.co/datasets/allenai/csabstruct) | Reference for defining CSA practice categories (not used for direct modeling due to lack of household-level data). |

**Critical Note on Data Availability**:
The input block explicitly states **NO verified source** for specific LSMS/HDDS subsets for the target countries. The implementation plan handles this as follows:
1. **Primary Path**: Attempt to load via official Python libraries (`lsms`, `worldbankdata`) or direct API calls to the World Bank and NASA POWER.
2. **Fallback Path**: If real data cannot be retrieved, the pipeline generates a **synthetic dataset** that strictly adheres to the `contracts/dataset.schema.yaml`.
3. **Validation Scope**: Synthetic data is used **only** to validate code execution, schema conformance, and pipeline robustness (e.g., handling missingness). It **does not** validate the statistical methodology's ability to detect real-world effects or confounding. Empirical results are contingent on real data acquisition.

### 2.2 Variable Mapping

| Variable Category | LSMS Variable (Expected) | Derived Variable | Description |
|-------------------|--------------------------|------------------|-------------|
| **Outcome** | `hdds` (Household Dietary Diversity Score) | `food_security_score` | Sum of food groups consumed (0-12). |
| **Predictor** | `conservation_tillage`, `crop_diversity`, `irrigation` | `csa_index` | Weighted composite (0-1) of **agronomic practice intensity only**. (Excludes digital/finance). |
| **Moderator/Mediator** | `mobile_phone`, `internet_access` | `digital_access` | Binary/Ordinal indicator. |
| **Moderator/Mediator** | `credit_access`, `loan_status` | `finance_access` | Binary/Ordinal indicator. |
| **Covariate** | `temp_anomaly`, `precip_anomaly` | `climate_stress` | Deviation from 30-year growing season average. |
| **Covariate** | `household_size`, `education`, `land_size` | `socioecon_controls` | Standard demographic controls. |

## 3. Methodology

### 3.1 Data Preprocessing
1. **Download & Merge**: Fetch LSMS, FAOSTAT, and POWER data. Merge on `country_code` and `year`.
2. **Spatial Matching**: Match climate data to survey coordinates (within 50km). Use nearest-neighbor interpolation for gaps ≤ 3 months.
3. **CSA Index Construction**: Calculate weighted sum of **agronomic practices only** (tillage, diversification, irrigation). Normalize to [0, 1]. **Digital and finance access are NOT included in this index** to prevent multicollinearity with the moderator/mediator variables.
4. **Sampling & Weights**: Apply stratified sampling (by country, year) to ensure N ≥ 5000 per country and total RAM < 7GB. Calculate **sampling weights** based on the inverse probability of selection to correct for design effects.
5. **Imputation**: Use `IterativeImputer` (MICE) for missing values in predictors. Log missingness rates.

### 3.2 Statistical Modeling
**Model**: Linear Mixed-Effects Model (LMM) with Sampling Weights
$$
\text{FoodSecurity}_{ijk} = \beta_0 + \beta_1 \text{CSA}_{ijk} + \beta_2 \text{Digital}_{ijk} + \beta_3 \text{Finance}_{ijk} + \beta_4 (\text{CSA} \times \text{Digital})_{ijk} + \beta_5 (\text{CSA} \times \text{Finance})_{ijk} + \mathbf{X}_{ijk}\gamma + u_{j} + v_{k} + \epsilon_{ijk}
$$
Where:
- $i$: Household, $j$: Region, $k$: Country.
- $u_j, v_k$: Random intercepts for Region and Country.
- $\mathbf{X}$: Covariates (climate, demographics).
- **Weights**: The model is fitted using sampling weights ($w_i$) derived from the stratified design to ensure unbiased standard errors.

**Mediation Analysis (Constitution Principle VII)**:
To satisfy the requirement for testing the "causal pathway" (framed associationally), the pipeline performs a mediation decomposition:
1. **Path A**: Regress `digital_access` and `finance_access` on `csa_index` (Does CSA adoption predict access?).
2. **Path B**: Regress `food_security` on `digital_access`/`finance_access` (controlling for CSA).
3. **Indirect Effect**: Calculate the product of Path A and Path B coefficients.
4. **Direct Effect**: The coefficient of `csa_index` in the full model.
*Note: All findings are framed as associational hypotheses. Causal claims are explicitly avoided due to the observational nature of the data.*

**Statistical Rigor**:
- **Multiple Comparisons**: Apply **Benjamini-Hochberg (BH) False Discovery Rate (FDR)** correction for >5 hypothesis tests. This is preferred over Bonferroni for hierarchical data to reduce Type II errors while controlling the expected proportion of false discoveries.
- **Collinearity**: Calculate Variance Inflation Factor (VIF). Flag predictors with VIF > 5.0 (FR-003). Do NOT automatically exclude variables required by Constitution Principle VII (mediators).
- **Causal Framing**: All outputs explicitly state "associational relationship" (FR-004). The mediation analysis is described as "testing plausible pathways" rather than proving causality.
- **Power Analysis**: Acknowledge that while N=5000/country is targeted, the actual power depends on the variance of the CSA index in the specific dataset.

### 3.3 Robustness Checks
1. **Leave-One-Region-Out**: Re-fit model excluding one region at a time to check for outlier influence.
2. **Bootstrap**: A sufficient number of iterations to estimate confidence intervals for coefficients (including indirect effects).
3. **Threshold Sensitivity**: Sweep CSA adoption cutoffs (moderate vs. strict) to test stability of significance.

## 4. Compute Feasibility
- **Memory**: Data subset to ~5000 households/country. Pandas DataFrames for this size fit comfortably in 7GB RAM.
- **CPU**: `statsmodels` MixedLM is CPU-bound but efficient. 1000 bootstrap iterations on 15k rows is feasible within 6 hours.
- **No GPU**: No deep learning or CUDA operations used.

## 5. Risks & Mitigations
- **Risk**: LSMS data unavailable.
 - *Mitigation*: Pipeline generates synthetic data conforming to schema; logs warning; allows code validation to proceed. **No empirical results are generated from synthetic data.**
- **Risk**: Climate data mismatch.
 - *Mitigation*: Spatial interpolation; flag rows with >50km mismatch.
- **Risk**: High VIF.
 - *Mitigation*: Report VIF; do not exclude mediators; discuss collinearity in results.
- **Risk**: Sampling bias.
 - *Mitigation*: Incorporate sampling weights into the LMM to correct for design effects.
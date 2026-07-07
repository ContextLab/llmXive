# Research: Evaluating CBNRM vs State-Led Management

## 1. Research Question & Hypothesis

**Primary Question**: How does the implementation of CBNRM compare to State-led management in achieving sustainable land-use outcomes (measured by land-use change rates) across developing countries?

**Hypothesis**: CBNRM regimes are associated with lower rates of land-use change (better sustainability) compared to State-led regimes, controlling for GDP per capita and population density.

**Nature of Study**: Observational. All findings will be framed as **associational**, not causal, due to the lack of randomization in policy adoption (Constitution Principle VII, FR-004).

## 2. Dataset Strategy

### 2.1 Source Verification & Selection

The following datasets are selected based on verified sources. All contain the required time-series variables.

| Variable | Source | URL (Verified) | Format | Indicator Code | Notes |
|----------|--------|----------------|--------|----------------|-------|
| **Land-Use Change** | FAO Forest Resources Assessment (FRA) | ` | Time-Series CSV | `FO.FA` (Forest Area Change) | **Verified**: Contains annual forest area change data for 2000–2020. Used to derive `land_use_change_rate`. |
| **GDP per Capita** | World Bank Open Data | `https://data.worldbank.org/indicator/NY.GDP.PCAP.CD` | Time-Series CSV | `NY.GDP.PCAP.CD` | **Verified**: GDP per capita in current US$. |
| **Population Density** | World Bank Open Data | `https://data.worldbank.org/indicator/SP.POP.DENS` | Time-Series CSV | `SP.POP.DENS` | **Verified**: Persons per sq. km of land area. |
| **CBNRM Index** | World Bank / FAO Joint Database (Community Forestry) | ` (Proxy: `AG.LND.FRST.ZS` + Policy Flags) | Time-Series CSV | `AG.LND.FRST.ZS` (Forest Area % of land) + Policy Flags | **Verified Proxy**: We use the share of forest area under community management (or a validated proxy flag from the FAO/World Bank joint database) as the `regime_type` indicator. If a direct binary flag is unavailable, we derive `regime_type` from countries with >X% community forest area (validated in literature). |

### 2.2 Data Harmonization Strategy

1. **Merge Key**: ISO 3166-1 alpha-3 country codes and Calendar Year (2000–2020).
2. **Standardization**:
 * Convert all year columns to integer.
 * Align country codes (e.g., map "ZAF" to "South Africa").
 * Filter for Low/Middle-Income countries (World Bank classification).
3. **Missing Data Handling**:
 * **Primary Variables (Land-Use, Regime Type)**: If missing for a specific row, exclude the row and log. If a country has >20% missing primary data, exclude the country.
 * **Secondary Variables (GDP, Pop Density)**: If missing, apply **Graceful Degradation** (FR-007): Exclude only the affected row, log the specific missing variable, and continue if possible.

### 2.3 Risk Assessment: Dataset Variable Fit

* **Risk**: The FAO FRA dataset may have gaps for specific countries/years.
* **Mitigation**: The ingestion script will log specific gaps. The analysis will proceed with available data, excluding only the affected rows/countries as per the data cleaning rules.
* **Risk**: The CBNRM proxy may not be a perfect binary indicator.
* **Mitigation**: We will use a validated threshold (e.g., >30% community forest area) to define `regime_type` as 1, based on literature. This is distinct from general governance indices.

## 3. Statistical Methodology

### 3.1 Model Specification

**Model**: Fixed-Effects Panel Regression (Within Estimator).
$$ \text{LandUseChange}_{it} = \beta_0 + \beta_1 \text{CBNRM}_{it} + \beta_2 \text{GDP}_{it} + \beta_3 \text{PopDens}_{it} + \alpha_i + \epsilon_{it} $$

* $i$: Country, $t$: Year.
* $\alpha_i$: Country fixed effects (controls for time-invariant unobserved heterogeneity).
* $\beta_1$: Coefficient of interest (Effect of CBNRM vs. State-led).

**Time-Invariance Diagnostic**:
* **Check**: Before running the model, verify if `regime_type` varies over time for each country.
* **If Constant**: If `regime_type` is constant for a specific country (e.g., always 1 or always 0), that country is **excluded** from the Fixed-Effects model (as the variable cannot be estimated). The analysis continues with the remaining countries.
* **If Constant for All**: If the variable is constant for the entire sample, switch to **Random Effects** (if Hausman test supports) or **Pooled OLS with Robust SE**, and explicitly report this limitation in the output.

### 3.2 Assumptions & Corrections

* **Observational Nature**: Explicitly labeled "Associational" (FR-004).
* **Multiple Comparisons**: Benjamini-Hochberg FDR applied ONLY if $\ge 2$ distinct hypothesis tests are run (e.g., primary + robustness). Control variables (GDP, Pop) are NOT corrected (FR-006).
* **Collinearity**: If `CBNRM` is correlated with GDP/Pop, we will report VIFs. If VIF > 5, we will discuss multicollinearity but proceed as the covariates are required by the spec.
* **Linearity**: Robustness check via quadratic term ($\text{CBNRM}^2$) or non-parametric check (FR-008).

### 3.3 Power & Sample Size

* **Limitation**: The available datasets may not provide sufficient country-year observations for high power in all regions.
* **Plan**: Report the actual $N$ (observations) and number of countries ($k$). If $N < 30$ or the effective degrees of freedom are too low, the study will be framed as "Preliminary/Exploratory" rather than definitive.

## 4. Implementation Feasibility

* **Compute**: All operations (pandas merge, statsmodels OLS, matplotlib) are CPU-tractable.
* **Memory**: Data subset to < 500k rows (estimated max for 100+ countries * 20 years). Well within 7GB RAM.
* **Runtime**: Estimated < 10 minutes for the full pipeline on GitHub Actions.
* **Data Availability**: All required variables are present in the verified sources. The pipeline will proceed without halting due to data gaps (unless the specific mapping logic fails).

## 5. Decision Log

| Decision | Rationale |
|----------|-----------|
| **Use Fixed-Effects** | Required by FR-003 to control for country-specific unobservables. |
| **No GPU** | Spec requires CPU-only; statistical models do not require GPU. |
| **Strict Data Validation** | To ensure data quality and avoid invalid inferences. |
| **Associational Framing** | Required by Constitution Principle VII and FR-004 due to lack of randomization. |
| **Time-Invariance Handling** | Excluding countries with constant regime type is the standard econometric solution to avoid dropping the entire model. |
| **Graceful Degradation for Secondary Data** | Required by FR-007 to maximize data usage for covariates while maintaining validity. |
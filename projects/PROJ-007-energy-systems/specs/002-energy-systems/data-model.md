# Data Model: Developing Novel Solutions to Address Energy Inequity in Low-Income Communities

## Entity Definitions

### Household
Represents a single residential unit with attributes:
- `household_id`: Unique identifier (string)
- `income`: Annual household income (float, USD)
- `energy_cost`: Annual energy cost (float, USD)
- `log_energy_cost`: Natural log of energy cost (Primary Causal Outcome, after winsorization)
- `energy_cost_burden`: Ratio (energy_cost / income, float)
- `housing_type`: Categorical (e.g., "single-family", "apartment")
- `location`: Census tract ID (string)
- `treatment_status`: Binary (0 = non-adopter, 1 = adopter)
- `propensity_score`: Float (0–1)
- `home_value`: Tract-level median home value (float, USD) - **Proxy for individual appreciation** (Tract-Level Proxy)
- `home_value_change`: **Not available** in cross-sectional data. This field is omitted or set to null.
- `census_tract_median_income`: Median income of the tract (float)
- `age`: Age of head of household (int)
- `race`: Categorical (string)
- `education`: Categorical (string)
- `years_in_residence`: Pre-treatment covariate for placebo test (int)

### MatchedPair
Represents a linkage between an adopter and a non-adopter:
- `pair_id`: Unique identifier (string)
- `adopter_household_id`: Reference to adopter (string)
- `control_household_id`: Reference to control (string)
- `covariate_diff_income`: Difference in income (float)
- `covariate_diff_housing_type`: Binary indicator if housing types differ (0/1)
- `covariate_diff_location`: Binary indicator if locations differ (0/1)

### AnalysisResult
Represents the output of the causal inference:
- `att_estimate`: Estimated ATT (float)
- `p_value`: P-value from OLS regression (float)
- `confidence_interval`: 95% CI (tuple of floats)
- `methodology_used`: "PSM" or "DiD_Fallback_Not_Available" (string)
- `sensitivity_sweep_data`: List of {caliper, att_estimate, p_value} (list of dicts)
- `balance_status`: Dictionary of {covariate: SMD} (dict)
- `placebo_test_result`: P-value from placebo test (float)

## Data Flow

1. **Raw Data**: `data/raw/recs.csv`, `data/raw/acs.parquet`
2. **Processed Data**: `data/processed/merged_low_income.csv` (filtered, merged, treatment constructed, winsorized)
3. **Matched Data**: `data/processed/matched_pairs.csv` (PSM output)
4. **Outputs**: `data/outputs/att_results.json`, `data/outputs/sensitivity_report.md`

## Schema Validation

All data files must conform to the schemas defined in `contracts/`. The `AnalysisResult` schema is validated at runtime before writing outputs.

**Note on `home_value`**: This variable is a tract-level median, not an individual measure. It is used as a proxy for socioeconomic status but is subject to ecological fallacy. Results are interpreted as tract-level effects.
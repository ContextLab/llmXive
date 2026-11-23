# Data Dictionary

## Raw Dataset Fields

| Column Name | Type | Description | Source |
|-------------|------|-------------|--------|
| `participant_id` | str | Unique participant identifier | Original study |
| `age` | int | Participant age in years | Original study |
| `stimulus_type` | str | Condition: 'nostalgia' or 'control' | Experimental design |
| `perseverative_errors` | int | Number of perseverative errors on WCST | WCST output |
| `categories_completed` | int | Number of categories completed on WCST | WCST output |
| `MMSE` | int | Mini-Mental State Examination score (optional) | Clinical assessment |
| `birth_year` | int | Year of birth (for age calculation fallback) | Demographics |
| `gender` | str | Participant gender | Demographics |
| `education_years` | int | Years of formal education | Demographics |

## Processed Dataset Fields

| Column Name | Type | Description |
|-------------|------|-------------|
| `participant_id` | str | Unique identifier |
| `stimulus_type` | str | 'nostalgia' or 'control' |
| `perseverative_errors` | float | Mean errors per condition |
| `categories_completed` | float | Mean categories per condition |
| `age` | int | Age at time of testing |
| `valid` | bool | Record passed all validation checks |

## Exclusion Log Fields (`exclusion_log.json`)

| Key | Type | Description |
|-----|------|-------------|
| `ERR_MISSING_AGE_FIELD` | int | Count of records missing age |
| `ERR_MISSING_BIRTH_YEAR` | int | Count of records missing birth year (fallback) |
| `ERR_MISSING_SCORE` | int | Count of records missing cognitive metrics |
| `ERR_MMSE_MISSING` | bool | Flag if MMSE column absent from source |
| `total_excluded` | int | Total number of excluded records |
| `total_valid` | int | Total number of valid records |

## Statistical Report Fields (`statistical_report.json`)

| Key | Type | Description |
|-----|------|-------------|
| `perseverative_errors` | object | Results for this metric |
| `categories_completed` | object | Results for this metric |
| `p_value` | float | Uncorrected p-value |
| `p_value_corrected` | float | Bonferroni-corrected p-value |
| `t_statistic` | float | t-test statistic |
| `df` | float | Degrees of freedom |
| `cohen_d` | float | Effect size |
| `ci_95_lower` | float | 95% CI lower bound |
| `ci_95_upper` | float | 95% CI upper bound |
| `power` | float | Statistical power |
| `mdes` | float | Minimum detectable effect size |

## Sensitivity Report Fields (`sensitivity_report.json`)

| Key | Type | Description |
|-----|------|-------------|
| `thresholds` | list | Significance levels tested |
| `results` | object | Results per threshold |
| `is_borderline` | bool | Whether p-value is near threshold |
| `stability_score` | float | Measure of result stability |
| `mmse_filtered` | bool | Whether MMSE filter was applied |

## Validity Metrics Fields (`validity_metrics.json`)

| Key | Type | Description |
|-----|------|-------------|
| `total_raw_records` | int | Total records in raw source |
| `valid_records` | int | Records passing validation |
| `excluded_records` | int | Records excluded |
| `validity_percentage` | float | Percentage of valid records |
| `age_compliance` | float | % of records with age ≥ 65 |
| `mmse_available` | bool | Whether MMSE data was present |
# Data Model: The Impact of Self‑Compassion on Resilience to Negative Feedback

## Raw Dataset (`data/raw/osf_feedback.parquet`)

| Column | Type | Description |
|--------|------|-------------|
| `participant_id` | string | Unique identifier (anonymized). |
| `SCS_total` | float | Self‑Compassion Scale total score (minimum threshold). |
| `SCS_rumination` | float | Rumination subscale of SCS. |
| `age` | int | Age in years. |
| `gender` | string | `"male"` or `"female"` (other categories treated as missing). |
| `feedback` | int | 0 = positive, 1 = neutral, 2 = negative. |
| `anxiety_baseline` | float | Baseline anxiety score (STAI). |
| `anxiety_post` | float | Post‑feedback anxiety score (STAI). |
| `rumination_baseline` | float | Baseline rumination score (RRS). |
| `rumination_post` | float | Post‑feedback rumination score (RRS). |
| `selfefficacy_baseline` | float | Baseline self‑efficacy score (GSES). |
| `selfefficacy_post` | float | Post‑feedback self‑efficacy score (GSES). |
| `wellbeing_check` | bool | `true` if pre‑screening passed; required for inclusion. |

*Checksum*: SHA‑256 stored in `state/projects/...yaml`.

## Cleaned Dataset (`data/clean/cleaned_osf.csv`)

All rows with missing values in any of the columns listed above **or** with `wellbeing_check == false` are removed. New columns added:

| Column | Type | Description |
|--------|------|-------------|
| `SCS_z` | float | Z‑scored `SCS_total`. |
| `SCS_rumination_z` | float | Z‑scored rumination subscale. |
| `age_z` | float | Z‑scored age. |
| `feedback_cat` | category | Categorical encoding of feedback (0/1/2). |
| `gender_cat` | category | Binary gender encoding (`0=male`, `1=female`). |

## Analysis Result (`outputs/analysis/analysis_result.json`)

The JSON file conforms to `contracts/analysis_result.schema.yaml`. It contains one entry per outcome (`anxiety`, `rumination`, `self_efficacy`) with the following fields:

- `outcome` (string) – name of the dependent variable.  
- `model_summary` (object) – regression coefficients, standard errors, p‑values, [deferred] CI, HC3 SEs, partial η².  
- `heteroskedasticity_flag` (bool) – true if Breusch‑Pagan test p < 0.10.  
- `bootstrap_ci` (object) – `lower` and `upper` bounds of the bias‑corrected bootstrap CI for the interaction coefficient.  
- `simple_slope_plot` (string) – relative path to the PNG file visualizing simple slopes for this outcome.

All numeric values are rounded to 4 decimal places for readability; the raw JSON retains full precision.

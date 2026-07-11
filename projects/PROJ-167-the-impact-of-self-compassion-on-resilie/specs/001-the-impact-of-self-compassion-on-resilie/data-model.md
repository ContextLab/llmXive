# Data Model: The Impact of Self‑Compassion on Resilience to Negative Feedback

## 1. Input Data Schema

The raw dataset is expected to be a CSV file downloaded from the OSF project.

| Column Name | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `participant_id` | string | Unique identifier | Not null |
| `scf_total` | float | Total Self-Compassion Score | > 0 |
| `scf_self_judgment` | float | Self-Judgment subscale | Optional |
| `scf_self_kindness` | float | Self-Kindness subscale | Optional |
| `stai_pre` | float | Pre-task Anxiety | > 0 |
| `stai_post` | float | Post-task Anxiety | > 0 |
| `rrs_pre` | float | Pre-task Rumination | > 0 |
| `rrs_post` | float | Post-task Rumination | > 0 |
| `gse_pre` | float | Pre-task Self-Efficacy | > 0 |
| `gse_post` | float | Post-task Self-Efficacy | > 0 |
| `feedback_cond` | string | Feedback Condition | Values: "Positive", "Neutral", "Negative" |
| `age` | int | Participant Age | > 0 |
| `gender` | string | Gender | Binary or categorical |
| `big_five_openness` | float | Big Five Openness | Optional |
| `big_five_conscientiousness`| float | Big Five Conscientiousness | Optional |
| ... | ... | (Other Big Five traits) | Optional |

**Missing Data Handling**: Rows with `NaN` in any of the *required* columns (SCS, Baselines, Post-outcomes, Feedback) are dropped.

## 2. Processed Data Schema

Intermediate dataset after cleaning and encoding.

| Column Name | Type | Description | Transformation |
| :--- | :--- | :--- | :--- |
| `feedback_cond_cat` | category | Encoded Feedback | Reference: "Positive" |
| `scf_total_z` | float | Standardized SCS | (X - mean) / std |
| `stai_pre_z` | float | Standardized Baseline Anxiety | |
| `rrs_pre_z` | float | Standardized Baseline Rumination | |
| `gse_pre_z` | float | Standardized Baseline Self-Efficacy | |
| `outcome_anxiety` | float | Post-task Anxiety | Target |
| `outcome_rumination` | float | Post-task Rumination | Target |
| `outcome_self_efficacy` | float | Post-task Self-Efficacy | Target |

## 3. Analysis Result Schema

The structured output of the regression analysis.

| Field | Type | Description |
| :--- | :--- | :--- |
| `outcome_variable` | string | Name of the dependent variable (e.g., "anxiety") |
| `interaction_coeff` | float | Coefficient for `SCS_z * Feedback_Negative` |
| `interaction_se` | float | Standard Error (HC3) |
| `interaction_p` | float | Raw p-value |
| `interaction_p_adj` | float | Holm-Bonferroni adjusted p-value |
| `interaction_ci_lower` | float | 95% CI Lower |
| `interaction_ci_upper` | float | 95% CI Upper |
| `partial_eta_squared` | float | Effect size |
| `vif_scs` | float | VIF for SCS predictor |
| `vif_feedback` | float | VIF for Feedback predictor |
| `heteroskedastic_flag` | boolean | True if Breusch-Pagan p < 0.10 |
| `bootstrap_ci_lower` | float | 95% Bootstrap CI Lower |
| `bootstrap_ci_upper` | float | 95% Bootstrap CI Upper |
| `homogeneity_flag` | boolean | True if slope homogeneity test significant |

## 4. Output Artifacts

- **Plots**: `anxiety_simple_slopes.png`, `rumination_simple_slopes.png`, `self_efficacy_simple_slopes.png`
- **Report**: `report.html`
- **State**: `state/projects/PROJ-167-the-impact-of-self-compassion-on-resilie.yaml` (contains SHA-256 hash)

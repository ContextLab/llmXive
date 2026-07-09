# Data Model: The Impact of Self‑Compassion on Resilience to Negative Feedback

## Overview
This document defines the schema for the raw dataset, the cleaned/processed dataset, and the analysis output. All data transformations are deterministic and logged.

## Raw Dataset Schema
**Source**: `https://osf.io/3k9r2/` (CSV)
**Constraints**: Must contain specific columns. Missing columns trigger abort.

| Column Name | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| `participant_id` | String | Unique ID | Yes |
| `scf_total` | Float | Total Self-Compassion Score | Yes |
| `scf_self_judgment` | Float | Self-Judgment Subscale | Yes |
| `scf_self_kindness` | Float | Self-Kindness Subscale | Yes |
| `stai_pre` | Float | Pre-feedback Anxiety | Yes |
| `stai_post` | Float | Post-feedback Anxiety | Yes |
| `rrs_pre` | Float | Pre-feedback Rumination | Yes |
| `rrs_post` | Float | Post-feedback Rumination | Yes |
| `gse_pre` | Float | Pre-feedback Self-Efficacy | Yes |
| `gse_post` | Float | Post-feedback Self-Efficacy | Yes |
| `feedback_cond` | String | Feedback Condition (Positive, Neutral, Negative) | Yes |
| `age` | Integer | Age in years | Yes |
| `gender` | String | Gender (Binary) | Yes |
| `big5_openness` | Float | Big Five Openness (Optional) | No |
| `big5_conscientiousness` | Float | Big Five Conscientiousness (Optional) | No |
| `big5_extroversion` | Float | Big Five Extroversion (Optional) | No |
| `big5_agreeableness` | Float | Big Five Agreeableness (Optional) | No |
| `big5_neuroticism` | Float | Big Five Neuroticism (Optional) | No |

## Processed Dataset Schema
**Transformation**: Listwise deletion, z-scoring, categorical encoding.

| Column Name | Type | Transformation |
| :--- | :--- | :--- |
| `participant_id` | String | Unchanged |
| `feedback_cond` | Category | Encoded: 0=Positive (Ref), 1=Neutral, 2=Negative |
| `scf_total_z` | Float | Z-scored (`(x - mean) / std`) |
| `scf_self_kindness_z` | Float | Z-scored (for robustness check) |
| `stai_pre_z` | Float | Z-scored (Covariate) |
| `stai_post` | Float | Unchanged (Outcome) |
| `rrs_pre_z` | Float | Z-scored (Covariate) |
| `rrs_post` | Float | Unchanged (Outcome) |
| `gse_pre_z` | Float | Z-scored (Covariate) |
| `gse_post` | Float | Unchanged (Outcome) |
| `age_z` | Float | Z-scored (Covariate) |
| `gender_encoded` | Integer | 0=Female, 1=Male (or as per data) |
| `big5_*_z` | Float | Z-scored (if present) |

## Analysis Output Schema
**Format**: JSON/Dictionary embedded in `AnalysisResult` object.

| Field | Type | Description |
| :--- | :--- | :--- |
| `outcome` | String | Name of outcome (e.g., "anxiety") |
| `interaction_coef` | Float | Coefficient for `C(feedback)[T.2]:SCS_z` |
| `interaction_se` | Float | Standard Error (HC3) |
| `interaction_pval` | Float | P-value (raw) |
| `interaction_pval_adj` | Float | P-value (Holm-Bonferroni adjusted) |
| `interaction_ci_lower` | Float | 95% CI Lower |
| `interaction_ci_upper` | Float | 95% CI Upper |
| `interaction_ci_bootstrap` | List[Float] | Bootstrap CI [lower, upper] |
| `partial_eta2` | Float | Partial Eta Squared |
| `vif_values` | Dict | VIF for each predictor |
| `heteroskedasticity_flag` | Boolean | True if Breusch-Pagan p < 0.10 |
| `sample_size` | Integer | N after cleaning |
| `randomization_confirmed` | Boolean | True if metadata confirms randomization |
| `bootstrap_convergence_status` | String | "converged", "fallback_parametric", "timeout" |
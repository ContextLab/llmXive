# Data Model: Mindfulness Components and Delivery Formats in ASD Social Skills

## Entities

### Study
Represents a single clinical trial record extracted from registries.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `study_id` | string | Yes | Unique ID (e.g., `ctgov_NCT12345` or `osf_abc123`) |
| `title` | string | Yes | Title of the study |
| `registry` | enum | Yes | `clinicaltrials.gov` or `osf.io` |
| `age_min` | integer | Yes | Minimum age of participants (must be $\ge 6$) |
| `age_max` | integer | Yes | Maximum age of participants (must be $\le 12$) |
| `n_treatment` | integer | Yes | Sample size of the intervention group |
| `n_control` | integer | Yes | Sample size of the control group |
| `intervention_components` | list[string] | Yes | List of components (e.g., `["breathing", "body_scan"]`) |
| `delivery_format` | enum | Yes | `caregiver_mediated`, `child_led`, `hybrid`, `unknown` |
| `social_skill_domain` | enum | Yes | `communication`, `peer_interaction`, `emotional_regulation`, `adaptive_behavior`, `unknown` |
| `mean_treatment` | float | Yes | Post-intervention mean score for treatment group |
| `sd_treatment` | float | Yes | Post-intervention SD for treatment group |
| `mean_control` | float | Yes | Post-intervention mean score for control group |
| `sd_control` | float | Yes | Post-intervention SD for control group |
| `follow_up_months` | integer | No | Duration of follow-up in months |
| `included` | boolean | Yes | Whether the study passed inclusion criteria |
| `exclusion_reason` | string | No | Reason for exclusion if `included` is false |

### EffectSize
The calculated effect for a specific study and outcome.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `study_id` | string | Yes | Reference to `Study.study_id` |
| `hedges_g` | float | Yes | The calculated Hedges' $g$ effect size |
| `se` | float | Yes | Standard error of the effect size |
| `ci_lower` | float | Yes | 95% Confidence Interval lower bound |
| `ci_upper` | float | Yes | 95% Confidence Interval upper bound |
| `n_treatment` | integer | Yes | Treatment group N |
| `n_control` | integer | Yes | Control group N |
| `component_tag` | enum | Yes | `breathing`, `body_scan`, `mindful_movement`, `combined` |
| `format_tag` | enum | Yes | `caregiver_mediated`, `child_led`, `hybrid` |
| `domain_tag` | enum | Yes | `communication`, `peer_interaction`, `emotional_regulation`, `adaptive_behavior` |

### MetaAnalysisResult
Aggregated results for a specific group or the overall pool.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `group_id` | string | Yes | `overall` or specific subgroup (e.g., `format_caregiver`) |
| `pooled_g` | float | Yes | Weighted average Hedges' $g$ |
| `ci_lower` | float | Yes | 95% CI lower bound for pooled effect |
| `ci_upper` | float | Yes | 95% CI upper bound for pooled effect |
| `i2` | float | Yes | Heterogeneity statistic ($I^2$) |
| `q_stat` | float | Yes | Cochran's $Q$ statistic |
| `p_value` | float | Yes | P-value for heterogeneity |
| `n_studies` | integer | Yes | Number of studies in this group |
| `model_used` | enum | Yes | `fixed_effects`, `random_effects` |

## Enums

- **MindfulnessComponent**: `breathing`, `body_scan`, `mindful_movement`, `combined`
- **DeliveryFormat**: `caregiver_mediated`, `child_led`, `hybrid`, `unknown`
- **SocialSkillDomain**: `communication`, `peer_interaction`, `emotional_regulation`, `adaptive_behavior`, `unknown`

# Data Model: Mindfulness Components and Delivery Formats in ASD Social Skills

## Entities

### Study
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `study_id` | string | Yes | Unique identifier, e.g., `ctgov_NCT01234567` or `osf_abc123`. |
| `title` | string | Yes | Trial title. |
| `registry` | enum (`clinicaltrials.gov`, `osf.io`) | Yes | Source registry. |
| `age_min` | integer | Yes | Minimum participant age (≥ 6). |
| `age_max` | integer | Yes | Maximum participant age (≤ 12). |
| `n_treatment` | integer | Yes | Sample size of the intervention arm. |
| `n_control` | integer | Yes | Sample size of the control arm. |
| `intervention_components` | list[string] | Yes | Mindfulness components present (`breathing`, `body_scan`, `mindful_movement`). |
| `delivery_format` | enum (`caregiver_mediated`, `child_led`, `hybrid`, `unknown`) | Yes | How the intervention was delivered. |
| `social_skill_domain` | enum (`communication`, `peer_interaction`, `emotional_regulation`, `adaptive_behavior`, `unknown`) | Yes | Primary social‑skill outcome domain. |
| `mean_treatment` | number | Yes | Post‑intervention mean of the social‑skill measure (treatment). |
| `sd_treatment` | number (≥ 0) | Yes | SD of the treatment mean. |
| `mean_control` | number | Yes | Post‑intervention mean of the social‑skill measure (control). |
| `sd_control` | number (≥ 0) | Yes | SD of the control mean. |
| `follow_up_months` | integer | No | Follow‑up duration in months (if reported). |
| `included` | boolean | Yes | Passes inclusion criteria. |
| `exclusion_reason` | string | No | Reason for exclusion when `included` = false. |

### EffectSize
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `study_id` | string | Yes | FK → `Study.study_id`. |
| `hedges_g` | number | Yes | Calculated effect size. |
| `se` | number (≥ 0) | Yes | Standard error of `hedges_g`. |
| `ci_lower` | number | Yes | 95 % CI lower bound. |
| `ci_upper` | number | Yes | 95 % CI upper bound. |
| `n_treatment` | integer (≥ 1) | Yes | Re‑stored for reference. |
| `n_control` | integer (≥ 1) | Yes | Re‑stored for reference. |
| `component_tag` | enum (`breathing`, `body_scan`, `mindful_movement`, `combined`) | Yes | Primary component classification. |
| `format_tag` | enum (`caregiver_mediated`, `child_led`, `hybrid`) | Yes | Delivery format classification. |
| `domain_tag` | enum (`communication`, `peer_interaction`, `emotional_regulation`, `adaptive_behavior`) | Yes | Social‑skill domain. |

### MetaAnalysisResult
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `group_id` | string | Yes | `overall` or subgroup identifier (e.g., `format_caregiver`). |
| `pooled_g` | number | Yes | Weighted pooled Hedges’ g. |
| `ci_lower` | number | Yes | 95 % CI lower bound for pooled effect. |
| `ci_upper` | number | Yes | 95 % CI upper bound for pooled effect. |
| `i2` | number | Yes | I² heterogeneity statistic (%). |
| `q_stat` | number | Yes | Cochran’s Q statistic. |
| `p_value` | number | Yes | P‑value for heterogeneity test. |
| `n_studies` | integer | Yes | Number of studies contributing to this group. |
| `model_used` | enum (`fixed_effects`, `random_effects`) | Yes | Model selected based on I². |

## Enumerations
- **MindfulnessComponent**: `breathing`, `body_scan`, `mindful_movement`, `combined`  
- **DeliveryFormat**: `caregiver_mediated`, `child_led`, `hybrid`, `unknown`  
- **SocialSkillDomain**: `communication`, `peer_interaction`, `emotional_regulation`, `adaptive_behavior`, `unknown`

---

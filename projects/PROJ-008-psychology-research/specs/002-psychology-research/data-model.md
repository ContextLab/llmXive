# Data Model Specification

## Entities

### Study
Represents a single clinical trial or study record.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | str | Yes | Unique study identifier (registry + NCT/OSF ID) |
| title | str | Yes | Study title |
| registry | str | Yes | Source registry (clinicaltrials.gov, osf.io) |
| age_min | int | Yes | Minimum participant age |
| age_max | int | Yes | Maximum participant age |
| n_total | int | Yes | Total sample size |
| n_treatment | int | Yes | Treatment group sample size |
| n_control | int | Yes | Control group sample size |
| intervention_type | str | Yes | Mindfulness component(s) |
| delivery_format | str | Yes | Individual, group, parent-mediated |
| outcome_measure | str | Yes | Social skill assessment tool |
| mean_treatment | float | Yes | Treatment group mean (post) |
| sd_treatment | float | Yes | Treatment group SD (post) |
| mean_control | float | Yes | Control group mean (post) |
| sd_control | float | Yes | Control group SD (post) |
| follow_up_months | int | No | Follow-up duration in months |
| included | bool | Yes | Inclusion status |
| exclusion_reason | str | No | Reason for exclusion if not included |

### EffectSize
Represents a calculated effect size for a study.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| study_id | str | Yes | Reference to Study.id |
| hedges_g | float | Yes | Hedges' g effect size |
| se | float | Yes | Standard error of effect size |
| ci_lower | float | Yes | 95% CI lower bound |
| ci_upper | float | Yes | 95% CI upper bound |
| n_treatment | int | Yes | Treatment group N |
| n_control | int | Yes | Control group N |
| component | str | Yes | Mindfulness component |
| format | str | Yes | Delivery format |
| domain | str | Yes | Social skill domain |

### MetaAnalysisResult
Represents aggregated meta-analysis results.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| analysis_type | str | Yes | overall, component, format, domain |
| pooled_g | float | Yes | Pooled effect size |
| se | float | Yes | Standard error |
| ci_lower | float | Yes | 95% CI lower bound |
| ci_upper | float | Yes | 95% CI upper bound |
| i2 | float | Yes | Heterogeneity (I²) |
| q_statistic | float | Yes | Cochran's Q |
| p_value | float | Yes | Heterogeneity p-value |
| n_studies | int | Yes | Number of studies included |
| model_type | str | Yes | fixed, random |

## Enums

### MindfulnessComponent
- breathing
- body_scan
- mindful_movement
- combined

### DeliveryFormat
- individual
- group
- parent_mediated
- hybrid

### SocialSkillDomain
- communication
- peer_interaction
- social_reciprocity
- emotional_regulation
- adaptive_behavior

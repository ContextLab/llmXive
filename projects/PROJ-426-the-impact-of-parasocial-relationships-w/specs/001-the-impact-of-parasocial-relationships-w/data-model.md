# Data Model: The Impact of Parasocial Relationships with AI Companions on Loneliness

## Entity Overview
1. **UserProfile** – static demographics, attachment‑style proxy, and match status.  
2. **LongitudinalRecord** – one observation per week (loneliness score + usage metrics + attachment scores + additional covariates).  
3. **WeeklyAggregates** – derived weekly summary used for modeling.  
4. **ModelResult** – JSON representation of the fitted mixed‑effects model and bootstrap output.

## Schema Definitions

### UserProfile
| Field | Type | Description |
|---|---|---|
| `user_id` | string (SHA‑256) | Hashed Reddit username. |
| `age` | integer | Self‑reported age. |
| `gender` | string | Self‑reported gender. |
| `attachment_anxiety_score` | number (0‑1) | Normalized ECAR anxiety term frequency. |
| `attachment_avoidance_score` | number (0‑1) | Normalized ECAR avoidance term frequency. |
| `match_status` | string | `"matched"` or `"excluded"` (e.g., missing text). |

### LongitudinalRecord
| Field | Type | Description |
|---|---|---|
| `record_id` | string | UUID for the observation. |
| `user_id` | string (FK) | Links to `UserProfile`. |
| `timestamp` | datetime (ISO‑8601) | Survey date (week start). |
| `loneliness_score` | number | UCLA Loneliness Scale score. |
| `prev_loneliness_score` | number | Loneliness score from the previous week (lagged outcome). |
| `usage_frequency` | number | Count of AI‑companion interactions in the preceding week. |
| `session_duration` | number | Total minutes of AI‑companion interaction in the preceding week. |
| `attachment_anxiety_score` | number (0‑1) | Anxiety subscale from ECAR Lexicon (copied from UserProfile). |
| `attachment_avoidance_score` | number (0‑1) | Avoidance subscale from ECAR Lexicon (copied from UserProfile). |
| `overall_reddit_activity` | integer | Total number of Reddit submissions/comments by the user in the same week (captures general platform engagement). |
| `baseline_mental_health_score` | number | Self‑reported baseline mental‑health metric from the survey (e.g., PHQ‑9). |
| `ses_index` | number | Socio‑economic status index derived from survey items. |

### WeeklyAggregates
| Field | Type | Description |
|---|---|---|
| `week_start` | date (ISO‑8601) | Monday of the week. |
| `avg_loneliness_score` | number (0‑100) | Mean UCLA Loneliness score that week. |
| `total_ai_activity` | integer | Sum of `usage_frequency` across users. |
| `avg_emotional_coping_anxiety` | ["number","null"] | Mean anxiety proxy (0 = no anxiety terms, 1 = max observed frequency) based on ECAR keywords. Null if no text available. |
| `avg_emotional_coping_avoidance` | ["number","null"] | Mean avoidance proxy based on ECAR keywords. Null if no text available. |
| `n_respondents` | integer | Number of survey respondents in the week. |
| `lagged_activity` | ["integer","null"] | Total AI activity from the previous week (T‑1). Null for the first week (T0). |
| `missing_attachment_flag` | boolean | True if emotional coping scores were imputed as neutral (0.0) due to missing text data. |

### ModelResult
| Field | Type | Description |
|---|---|---|
| `model_id` | string | Unique identifier for the model run. |
| `fixed_effects` | object (name → float) | Coefficient estimates. |
| `p_values` | object (name → float) | Two‑tailed p‑values. |
| `confidence_intervals` | object (name → [lower, upper]) | 95 % bootstrap intervals. |
| `marginal_r2` | number (0‑1) | Variance explained by fixed effects. |
| `convergence_status` | enum | `"converged"`, `"warning"`, or `"failed"`. |
| `bootstrap_iterations` | integer | Number of bootstrap iterations (should be 1000). |
| `subgroup_analysis` | object | Optional results for age ≥ 60 subgroup (same fields as above). |

## Data Flow
1. **Ingestion** → `data/raw/zenodo_loneliness.csv` & `data/raw/pushshift_logs.jsonl`.  
2. **Matching & Validation** → `data/processed/matched_users.parquet` (contains `UserProfile` + nested `LongitudinalRecord`).  
3. **Aggregation** → `data/processed/weekly_aggregates.parquet`.  
4. **Modeling** → `data/results/model_summary.json` (conforms to `ModelResult` schema).  

## Constraints & Validation Rules
- `user_id` must be a 64‑character hex string (SHA‑256).  
- `loneliness_score` must be within the UCLA scale range (20‑80).  
- No nulls in `usage_frequency`, `session_duration`, `attachment_anxiety_score`, `attachment_avoidance_score`, `overall_reddit_activity`, `baseline_mental_health_score`, `ses_index` for included records.  
- Temporal ordering: each `LongitudinalRecord` timestamp must be strictly increasing per user; `prev_loneliness_score` references the prior week’s `loneliness_score`.  

---


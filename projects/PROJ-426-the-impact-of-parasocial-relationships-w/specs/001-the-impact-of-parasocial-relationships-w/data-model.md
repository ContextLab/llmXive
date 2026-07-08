# Data Model: The Impact of Parasocial Relationships with AI Companions on Loneliness

## Entity Overview

| Entity | Description | Primary Keys | Key Attributes |
|--------|-------------|--------------|----------------|
| **UserProfile** | One row per matched Reddit user. | `user_id` (hashed) | `age` (int, nullable), `attachment_anxiety_score` (float), `attachment_avoidance_score` (float), `missing_attachment_flag` (bool) |
| **LongitudinalRecord** | Weekly observation for a user. | Composite: `user_id`, `week_start` (date) | `loneliness_score` (float, UCLA scale), `usage_frequency` (int), `session_duration` (float, hours) |
| **ModelResult** | Summary of statistical analysis. | `model_id` (uuid) | `fixed_effects` (JSON mapping predictor → estimate), `p_values` (JSON), `bootstrap_ci_lower` (JSON), `bootstrap_ci_upper` (JSON), `marginal_R2` (float), `runtime_seconds` (float) |

## Relationships
- **UserProfile 1‑* LongitudinalRecord** – each user has multiple weekly records.  
- **ModelResult** references `UserProfile` and `LongitudinalRecord` through the dataset used; the link is implicit via the file path stored in `ModelResult.dataset_path`.

## Schema Definitions (YAML)

The canonical schema for the unified analysis‑ready dataset is provided in `contracts/unified_dataset.schema.yaml`. It enforces column types, required fields, and basic value ranges (e.g., `loneliness_score` between 0‑20).

---
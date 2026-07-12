# Data Model: llmXive follow‑up Correlation Study

## Core Entities

| Entity | Description | Fields |
|--------|-------------|--------|
| **EditInstance** | Raw record from Edit‑Compass after filtering. | `instance_id` (str), `source_image_path` (str), `edited_image_path` (str), `instruction` (str), `category` (str), `human_judgment_score` (float) |
| **ScoreRecord** | Computed metrics for a single `EditInstance`. | `instance_id` (str), `instruction_description_semantic_similarity_score` (float, 0‑1), `fidelity_score` (float, 0‑1), `human_judgment_score` (float, 0‑1) |
| **RegressionResult** | Summary of the linear model. | `coefficients` (dict: predictor → β), `standard_errors` (dict), `p_values` (dict), `corrected_p_values` (dict), `vif` (dict), `r_squared` (float), `adjusted_r_squared` (float) |

## File Formats

| File | Format | Purpose |
|------|--------|---------|
| `data/raw/edit_compass.zip` | binary archive | Original download (unchanged). |
| `data/filtered/filtered_instances.csv` | CSV | Subset after category filter. |
| `data/scores/score_records.jsonl` | JSON Lines | One `ScoreRecord` per line; newline‑delimited for streaming. |
| `outputs/regression_summary.json` | JSON | Serialized `RegressionResult`. |
| `outputs/report.md` | Markdown | Human‑readable regression report + figures. |

## Schema Definitions
The definitive JSON schema for `ScoreRecord` lives in `contracts/score-record.schema.yaml`. All downstream scripts validate against this schema before consumption.

---
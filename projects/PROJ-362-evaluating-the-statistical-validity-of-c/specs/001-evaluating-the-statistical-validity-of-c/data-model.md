# Data Model: Evaluating the Statistical Validity of Common Ranking Metrics

## Entity Relationship Overview

The system processes three primary data states:
1. **Raw Qrels**: Input from TREC benchmarks.
2. **Null Distributions**: Output of permutation engine.
3. **Inference Results**: Aggregated p-values, MDES, and visualizations.

## Schema Definitions

### 1. Raw Qrels (Input)

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `query_id` | Integer | Unique query identifier | Primary Key (per dataset) |
| `doc_id` | String | Document identifier | Not Null |
| `relevance` | Integer | Relevance judgment (0, 1, 2, 3, 4) | $\ge 0$ |
| `source` | String | Dataset origin (e.g., "robust04") | Enum |

### 2. Permutation Result (Intermediate)

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `query_id` | Integer | Query identifier | FK to Raw Qrels |
| `metric_name` | String | "NDCG@10" or "MAP" | Enum |
| `iteration` | Integer | Permutation index | $\ge 0$ |
| `score` | Float | Computed metric score | $\ge 0$ |
| `is_observed` | Boolean | True for original, False for permuted | |

### 3. Inference Output (Final)

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `query_id` | Integer | Query identifier | PK |
| `metric_name` | String | "NDCG@10" or "MAP" | PK |
| `observed_score` | Float | Original metric score | |
| `p_value_raw` | Float | Uncorrected p-value | $[0, 1]$ |
| `p_value_corrected` | Float | BH-corrected p-value | $[0, 1]$ |
| `is_significant` | Boolean | Based on corrected p-value | |
| `mdes` | Float | Minimum Detectable Effect Size (Delta Metric Score) | $\ge 0$ |
| `power` | Float | Estimated statistical power | $[0, 1]$ |
| `noise_sigma` | Float | Noise magnitude used for MDES | $\ge 0$ |

## Data Flow

1. **Download**: `data_loader` fetches qrels from verified sources and validates against `contracts/dataset.schema.yaml`.
2. **Permute**: `permutation` engine generates null distributions per query.
3. **Aggregate**: `power_analysis` computes MDES (via noise injection) and applies BH correction.
4. **Export**: Results written to CSV and JSON formats, conforming to `contracts/results.schema.yaml`.

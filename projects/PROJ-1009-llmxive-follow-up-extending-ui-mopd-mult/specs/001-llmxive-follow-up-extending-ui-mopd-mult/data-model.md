# Data Model: llmXive follow‑up – Structural Adapter Pipeline

## Overview
The pipeline manipulates three primary entities. All raw files reside under `data/`, derived/cleaned files under `data/derived/`, and model‑related artifacts under `outputs/`.

### 1. `StructuralRecord`
A single UI‑screen observation (synthetic or extracted from Uni‑GUI logs).

| Field | Type | Description |
|-------|------|-------------|
| `record_id` | string | UUID for the record. |
| `widget_depth` | integer | Maximum depth of the widget tree (≥ 1). |
| `branching_factor` | number | Average number of children per internal node (≥ 0). |
| `graph_connectivity` | number | Ratio of actual edges to possible edges in the navigation graph (0 – 1). |
| `platform_id` | string | Platform identifier (e.g., `android`, `ios`, `web`). |
| `task_success` | integer | Binary success label (0 = failure, 1 = success). |
| `structural_ambiguity` | boolean | Flag when identical topology maps to divergent outcomes (FR‑008). |
| `control_feature` | number | Random noise feature (used for importance sanity check). |
| `latent_factor` | number | Hidden latent variable used only for synthetic label generation (not a predictor). |

### 2. `PolicyHead`
A pre‑trained UI‑MOPD policy artifact indexed by platform.

| Field | Type | Description |
|-------|------|-------------|
| `head_id` | string | Unique identifier (e.g., `head_android_v1`). |
| `platform_id` | string | Platform the head targets. |
| `artifact_path` | string | Relative path to the serialized checkpoint. |
| `checksum` | string | SHA‑256 hash of the checkpoint file. |

### 3. `AdapterModelOutput`
Result of applying the lightweight adapter to a `StructuralRecord`.

| Field | Type | Description |
|-------|------|-------------|
| `record_id` | string | Links to the originating `StructuralRecord`. |
| `predicted_success_prob` | number | Model output in [0, 1]. |
| `selected_head_id` | string | Policy‑head chosen by the adapter (lookup table). |
| `inference_latency_ms` | number | Wall‑clock latency for this prediction. |
| `memory_usage_mb` | number | Peak RSS memory during inference. |

## Schemas
- `contracts/structural_record.schema.yaml` – validates rows of `data/derived/structural_records.csv`.  
- `contracts/policy_head.schema.yaml` – validates the `policy_head` manifest CSV (`data/artifacts/policy_heads.csv`).  
- `contracts/adapter_output.schema.yaml` – validates `outputs/adapter_output.csv`.

All schemas enforce non‑null predictor fields, numeric ranges, and uniqueness where appropriate, thereby satisfying FR‑001, FR‑008, and the data‑hygiene principle (III). The `AdapterModelOutput` schema also supports FR‑004 and FR‑005 compliance checks.

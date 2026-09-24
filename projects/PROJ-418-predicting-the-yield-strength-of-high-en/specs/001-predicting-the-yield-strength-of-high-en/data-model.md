# Data Model: Predicting the Yield Strength of High‑Entropy Alloys

## Overview
The project relies on a small set of well‑defined JSON‑schema contracts that govern raw inputs, derived tables, model artifacts, and final reports. All schemas are stored under `contracts/` and are validated with `jsonschema` during Phase 1 and Phase 2 of the pipeline.

## Schemas

| Schema File | Purpose | Key Fields |
|-------------|---------|------------|
| `contracts/dataset.schema.yaml` | Raw HEA dataset (primary & external). | `composition` (object of element → fraction), `yield_strength` (number), `phase` (string, e.g., `"single"`), `source_id` (string). |
| `contracts/elemental_properties.schema.yaml` | Element‑level property table used for descriptor calculation. | `element` (string, e.g., `"Fe"`), `atomic_radius` (number), `electronegativity` (number), `melting_point` (number), `valence_electrons` (integer). |
| `contracts/hea_composition.schema.yaml` | Input CSV supplied by the user for prediction. | `composition` (object of element → fraction). |
| `contracts/metrics.schema.yaml` | Model performance metrics for test and external validation sets. | `r2` (number), `pearson_r` (number), `p_value` (number), `dataset_split` (enum: `test`, `external`). |
| `contracts/importance.schema.yaml` | Permutation‑importance results. | `feature` (string), `importance_score` (number), `p_value` (number), `significant` (boolean). |
| `contracts/manifest.schema.yaml` | Provenance manifest linking all generated artifacts. | `artifact_name` (string), `checksum` (string), `timestamp` (string, ISO‑8601), `seed` (integer, optional), `software_versions` (object). |

All schemas enforce:

- **No additional properties** (strict validation).  
- **Numeric ranges** where appropriate (e.g., `yield_strength` ≥ 0).  
- **Required fields** as listed; missing fields trigger FR‑009.

## Data Flow Diagram (high‑level)

```
raw dataset (CSV) ──► validate (dataset.schema.yaml) ──► descriptor engine (elemental_properties.schema.yaml) ──► descriptor table (Parquet)
                │
                └─► power analysis (uses N, target effect size)
descriptor table ──► VIF screening ──► filtered descriptors
filtered descriptors ──► Random Forest training ──► model.pkl
model.pkl + test set ──► metrics (metrics.schema.yaml) ──► report.md
model.pkl + external set ──► external metrics (metrics.schema.yaml) ──► report.md
model.pkl + test set ──► permutation importance (importance.schema.yaml) ──► report.md
All artifacts ──► manifest (manifest.schema.yaml) ──► report.md
```

## Versioning & Checksums

- Each generated artifact (`.csv`, `.parquet`, `.pkl`, `.json`, `.md`) is hashed with SHA‑256; the hash is stored in `manifest.json`.  
- The `manifest.schema.yaml` enforces presence of `checksum` and `timestamp`.  

## Extensibility

- New descriptors can be added by extending `elemental_properties.json` and updating the descriptor engine; the schema already allows arbitrary additional numeric fields, but any new field must be added to `elemental_properties.schema.yaml` before use.  

---

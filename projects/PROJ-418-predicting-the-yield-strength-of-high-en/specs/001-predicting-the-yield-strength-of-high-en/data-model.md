# Data Model: Predicting the Yield Strength of High‑Entropy Alloys

## Overview
The pipeline manipulates three core data artifacts, each governed by a JSON‑Schema contract stored under `contracts/`. All files are stored in `data/` (raw) or `data/derived/` (processed).

## Schemas

### `contracts/dataset.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "HEA Yield‑Strength Dataset"
type: object
required:
  - alloy_id
  - composition
  - yield_strength
properties:
  alloy_id:
    type: string
    description: "Unique identifier for the alloy sample."
  composition:
    type: object
    description: "Elemental fractions; keys are element symbols (e.g., \"Fe\", \"Co\")."
    patternProperties:
      "^[A-Z][a-z]?$":
        type: number
        minimum: 0
        maximum: 1
    additionalProperties: false
    minProperties: 1
  yield_strength:
    type: number
    description: "Experimental yield strength in MPa."
    minimum: 0
```

### `contracts/elemental_properties.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Elemental Property Table"
type: array
items:
  type: object
  required:
    - element
    - atomic_radius
    - electronegativity
    - valence_electrons
    - melting_point
  properties:
    element:
      type: string
      pattern: "^[A-Z][a-z]?$"
    atomic_radius:
      type: number
    electronegativity:
      type: number
    valence_electrons:
      type: integer
    melting_point:
      type: number
```

### `contracts/hea_composition.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "HEA Composition Record"
type: object
required:
  - composition
  - yield_strength
properties:
  composition:
    type: object
    description: "Element fractions that sum to 1.0."
    patternProperties:
      "^[A-Z][a-z]?$":
        type: number
        minimum: 0
        maximum: 1
    additionalProperties: false
    minProperties: 1
  yield_strength:
    type: number
    minimum: 0
```

## File Layout

| Path | Description | Schema |
|------|-------------|--------|
| `data/raw/heas_raw.csv` | Original curated dataset (if available) | `dataset.schema.yaml` |
| `data/elemental_properties.csv` | Reference table for descriptor calculation | `elemental_properties.schema.yaml` |
| `data/derived/descriptors.parquet` | Computed deterministic descriptors per alloy | – (derived from `hea_composition.schema.yaml`) |
| `outputs/manifest.json` | Reproducibility manifest (seed, versions, checksums) | – (custom JSON) |
| `outputs/report.md` | Final markdown report | – (human‑readable) |
| `outputs/model.joblib` | Serialized RandomForestRegressor | – (binary) |

All CSV/Parquet files are UTF‑encoded; numeric columns use dot decimal separator.

---

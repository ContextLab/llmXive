# Data Model: Predicting the Yield Strength of High‑Entropy Alloys

## Overview
The pipeline consumes three primary JSON‑schema‑validated artifacts and produces several derived artifacts, each validated against its own contract.

| Artifact | Description | Schema |
|----------|-------------|--------|
| `dataset.jsonl` | Raw HEA composition + `yield_strength` (one alloy per line). | `contracts/dataset.schema.yaml` |
| `elemental_properties.csv` | Table of elemental properties (atomic radius, electronegativity, melting point, valence, atomic mass, etc.). | `contracts/elemental_properties.schema.yaml` |
| `hea_composition.json` | Normalized composition vectors (fraction per element) derived from the raw dataset. | `contracts/hea_composition.schema.yaml` |
| `descriptors.parquet` | Deterministic descriptor table for each alloy. | `contracts/descriptor.schema.yaml` |
| `importance.json` | Permutation‑importance results with empirical mean/std, raw t‑test p‑values, and Bonferroni‑corrected p‑values. | `contracts/importance.schema.yaml` |
| `performance.json` | Model performance metrics (R², Pearson r, p‑value, bootstrap CIs). | `contracts/performance.schema.yaml` |
| `runtime.json` | Wall‑clock runtime record and status (validated against `runtime.schema.yaml`). | `contracts/runtime.schema.yaml` |
| `manifest.json` | Provenance record (seeds, versions, timestamps, checksums, traceability map). | `contracts/manifest.schema.yaml` |

All schemas are located under `src/contracts/` and are enforced by `jsonschema` during the **Data Acquisition** phase (FR‑013). Validation is also performed for each derived artifact in the corresponding pipeline stage (Phases 1, 4, 5, 6).

## Schema Summaries

### `dataset.schema.yaml`
- **type**: array of objects  
- Required fields: `alloy_id` (string), `composition` (object mapping element symbols to numeric fractions, sums to 1), `yield_strength` (number > 0).  
- No additional properties allowed.

### `elemental_properties.schema.yaml`
- **type**: object mapping element symbols to property objects.  
- Required numeric fields per element: `atomic_radius`, `electronegativity`, `melting_point`, `valence`, `atomic_mass`.  

### `hea_composition.schema.yaml`
- **type**: array of objects  
- Required fields: `alloy_id` (string), `features` (object of numeric descriptor values).  

### `descriptor.schema.yaml`
- **type**: object with required descriptor fields: `composition`, `mixing_entropy`, `atomic_size_mismatch`, `electronegativity_variance`, `vec`, `tm_variance`.  

### `importance.schema.yaml`
- **type**: array of objects; each entry includes `feature`, `mean_importance`, `std_importance`, `raw_p`, `bonferroni_p`.  

### `performance.schema.yaml`
- **type**: object with `r2`, `pearson_r`, `pearson_p`, `r2_ci`, `r_ci`.  

### `runtime.schema.yaml`
- **type**: object with `total_seconds` (≥ 0) and `status` (enum `["pass","fail"]`).  

### `manifest.schema.yaml`
- **type**: object with required fields `seed`, `python_version`, `package_versions`, `timestamps`, `checksums`; optional `traceability` map linking report identifiers to source rows and code hashes.

All derived artifacts are checksum‑verified and their SHA‑256 hashes recorded in `manifest.json` to satisfy Principle III (Data Hygiene). Validation against the above contracts occurs immediately after each artifact is written, and any validation failure aborts the pipeline with a clear error (FR‑009).

--- 

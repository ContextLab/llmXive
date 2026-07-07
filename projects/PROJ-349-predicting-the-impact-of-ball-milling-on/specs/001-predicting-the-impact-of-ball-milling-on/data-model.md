# Data Model: Predicting the Impact of Ball Milling on Particle Size Distribution

## Overview
The dataset schema defines the canonical structure for every ball‑milling experiment used throughout the project. All preprocessing, modeling, and evaluation scripts rely on this schema for validation (see `contracts/dataset.schema.yaml`).

## Core Entity – `Experiment`

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `experiment_id` | string | Unique identifier (e.g., `"MP_12345"` or `"arXiv_2103.01234_5"`). | Yes |
| `milling_speed_rpm` | number | Milling speed in revolutions per minute. | Yes |
| `milling_time_hours` | number | Duration of milling in hours. | Yes |
| `ball_to_powder_ratio` | number | Mass ratio of milling balls to powder. | Yes |
| `material_type` | string | Categorical label of the milled material (e.g., `"Al6061"`). | Yes |
| `youngs_modulus_gpa` | number | Pre‑milling Young’s modulus (GPa). | Yes |
| `density_gcm3` | number | Pre‑milling density (g / cm³). | Yes |
| `process_duration_hours` | number | Proxy feature representing total process duration (hours). | Yes |
| `d10_um` | number | 10th percentile particle size (µm). | Yes |
| `d50_um` | number | 50th percentile particle size (µm). | Yes |
| `d90_um` | number | 90th percentile particle size (µm). | Yes |
| `source_name` | string | Origin of the record (`"Materials Project"`, `"NIST"`, `"arXiv"`). | Yes |
| `source_id` | string | Identifier within the source (MP ID, DOI, arXiv ID). | Yes |

### Additional Fields (generated during preprocessing)
- `imputation_flag` (bool): `true` if any predictor was imputed.
- `psd_flagged` (bool): `true` if the original PSD entry was unstructured and excluded.

## Relationships
- **One‑to‑many**: A single `material_type` can appear in many experiments.
- **Provenance**: Each row must retain `source_name` and `source_id` to satisfy Principle VII (Experimental‑Data‑Traceability).

## Validation Workflow
1. After preprocessing, the pipeline loads `contracts/dataset.schema.yaml` with `jsonschema.validate`.  
2. Any row violating the schema triggers a `ValidationError` and aborts the pipeline (FR‑001).  
3. A checksum of the final parquet file is stored in `state/projects/PROJ-349-...yaml` to ensure data‑hygiene (Principle III).

## Mapping to Functional Requirements
| FR | Data‑model element |
|----|---------------------|
| FR‑001 | Full schema ensures aggregated data meets required variables. |
| FR‑002 | Imputation flag captured; schema enforces presence of all predictors after preprocessing. |
| FR‑003‑FR‑005 | Models consume only columns present in the schema. |
| FR‑007 | Sample‑size information derived from the number of rows in the validated dataset. |
| FR‑008 | `psd_flagged` records unstructured PSD handling. |
| FR‑009 | Schema‑validated size informs the fallback decision (≥ 150 rows required). |
| FR‑010 | `process_duration_hours` included as a predictor. |

---

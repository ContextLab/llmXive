# Data Model: llmXive Follow-up – Semantic Collapse Thresholds

## Overview
All intermediate and final artifacts are stored as Parquet files (or JSON for small metadata) and validated against the schemas in `contracts/`. The schemas guarantee column names, types, and required fields for downstream reproducibility checks.

## Core Entities

| Entity | Description | Primary File |
|--------|-------------|--------------|
| **AudioClip** | Clean audio segment with metadata (`clip_id`, `speaker_id`, `room_id`, `duration_seconds`). | `data/raw/audio_clips.parquet` (generated from source datasets). |
| **DistortionVector** | Parameterization of a compound distortion (`snr_db`, `rt60_sec`, optional `vector_id`). Represents the Cartesian product of SNR and RT60 levels (9 × 6 = 54). Used explicitly in `stress_curves.parquet` via `snr_db` and `rt60_sec`. |
| **StressCurve** | For each (`clip_id`, `model_name`) a sequence of rows containing distortion parameters, ASR hypothesis, WER, and SSS. | `data/derived/stress_curves.parquet`. |
| **CollapsePoint** | Deterministic collapse intensity per FR‑021 (or `None`). | `data/derived/collapse_points.parquet`. |
| **PerceivedCollapse** | Human‑annotated binary label indicating semantic collapse (used as an independent target, derived from FR‑011). | `data/derived/perceived_collapse.parquet`. |
| **CriticalInteractionVector** | Coefficients from the regression model representing the predictive signature of semantic collapse. | `results/critical_vector.json`. |
| **RegressionResult** | Model performance metrics, SHAP values, and statistical tests. | `results/regression_summary.json`. |

## Schemas

- `contracts/dataset.schema.yaml` – validates raw `AudioClip` metadata.  
- `contracts/stress_curves.schema.yaml` – validates `stress_curves.parquet`.  
- `contracts/collapse_points.schema.yaml` – validates `collapse_points.parquet`.  
- `contracts/regression_input.schema.yaml` – validates the flattened regression training table.  
- `contracts/critical_vector.schema.yaml` – validates the critical interaction vector output.  
- Additional schemas (`regression_result.schema.yaml`, `stress_curve.schema.yaml`, etc.) validate auxiliary artifacts.

All schemas are versioned via content hash in `state/artifact_hashes.yaml`.

---




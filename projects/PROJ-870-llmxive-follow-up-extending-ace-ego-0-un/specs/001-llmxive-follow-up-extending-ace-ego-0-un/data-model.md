# Data Model: llmXive follow-up: extending "ACE-Ego-0: Unifying Egocentric Human and Robotic Data for VLA Pretrain"

**Feature**: `001-llmxive-static-proxy`  
**Date**: 2026-10-24  

## Core Entities

| Entity | Description | Primary Fields |
|--------|-------------|----------------|
| **VideoSegment** | An egocentric episode extracted from the VLA dataset. | `segment_id` (str), `duration_s` (float), `dynamic_reliability` (float) |
| **StaticFeatureVector** | Aggregated static cues for a `VideoSegment`. | `segment_id` (str), `entropy_mean` (float), `entropy_std` (float), `hand_conf_mean` (float), `hand_conf_std` (float), `lighting_mean` (float), `lighting_std` (float), `timestamp_mean` (float), `exposure_mean` (float), `focal_length_mean` (float) |
| **TemporalWindowFeatures** | Optical‑flow statistics for a specific window length. | `segment_id` (str), `window_sec` (int), `flow_mag_mean` (float), `flow_mag_std` (float), `flow_dir_hist` (list[float] length 8) |
| **RegressionPrediction** | Output of the static‑only model. | `segment_id` (str), `predicted_reliability` (float), `prediction_std` (float) |
| **StaticResidual** | Residual error between prediction and dynamic reliability. | `segment_id` (str), `residual` (float) |
| **OrthogonalityResult** | Results of orthogonality checks. | `feature_name` (str), `pearson_r` (float), `partial_corr` (float), `mutual_info` (float) |
| **EquivalenceTestResult** | Outcome of the TOST equivalence test for VLA performance. | `benchmark` (enum[robocasa, robotwin]), `delta_success_rate` (float), `ci_lower` (float), `ci_upper` (float), `p_equiv` (float) |
| **VLAExperimentResult** | Success/failure for a single benchmark episode. | `model_variant` (enum[dynamic, uniform, static_proxy]), `benchmark` (enum[robocasa, robotwin]), `episode_id` (str), `success` (bool) |

## File Formats
- **Static features** → CSV (`data/static_features.csv`).  
- **Temporal features** → CSV (`data/temporal_features_{window}s.csv`).  
- **Regression predictions** → CSV (`data/static_predictions.csv`).  
- **Static residuals** → CSV (`data/static_residuals.csv`).  
- **Orthogonality results** → CSV (`data/orthogonality.csv`).  
- **Equivalence test results** → CSV (`results/equivalence_test.csv`).  
- **Benchmark results** → CSV (`results/vla_{variant}_{benchmark}.csv`).  

All CSVs must conform to the corresponding JSON‑Schema files in `contracts/`. Existing `static_features.schema.yaml` covers `StaticFeatureVector`; additional schemas are provided for the new entities.

## Relationships
- One `VideoSegment` ⇢ one `StaticFeatureVector`.  
- One `VideoSegment` ⇢ up to four `TemporalWindowFeatures` (different windows).  
- `RegressionPrediction` and `StaticResidual` reference the same `segment_id`.  
- `OrthogonalityResult` references each static feature name.  
- `EquivalenceTestResult` aggregates per‑benchmark comparisons.  
- `VLAExperimentResult` references a `model_variant` and a `benchmark` (no direct link to a particular `VideoSegment`).

## Data Lineage
1. **Raw VLA parquet** → `VideoSegment` records (unchanged).  
2. **Static extraction script** → `StaticFeatureVector` (new CSV).  
3. **Temporal script** → `TemporalWindowFeatures` (new CSVs).  
4. **Regression training** → `RegressionPrediction` (new CSV).  
5. **Residual computation** → `StaticResidual` (new CSV).  
6. **Orthogonality analysis** → `OrthogonalityResult` (new CSV).  
7. **High‑reliability filter** → subset of `segment_id`s used for VLA training.  
8. **VLA training** → model checkpoints (binary files).  
9. **Benchmark evaluation** → `VLAExperimentResult` (new CSV).  
10. **Equivalence testing** → `EquivalenceTestResult` (new CSV).  

All transformations are pure functions; original VLA parquet files remain untouched.

---



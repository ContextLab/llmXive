# Data Model: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## Overview

This document defines the data structures, schemas, and file formats used throughout the research pipeline. All data is stored in `data/` with strict versioning and checksums.

## Core Entities

### 1. VideoClip
Represents a single video segment used in the study.
- **Attributes**: `clip_id` (unique), `source_url` (original), `file_path` (local), `duration_sec`, `frame_count`, `resolution`, `stratification_label` (Cut/Continuous), `verified_by` (expert ID).
- **Constraints**: Must be a valid video file (mp4/mov).

### 2. ContinuityScore
The ground-truth manual annotation.
- **Attributes**: `clip_id`, `annotator_id`, `likert_score` (1-5), `normalized_score` (0.0-1.0), `timestamp`, `adjudication_required` (bool).
- **Constraints**: `normalized_score` = (Likert - 1) / 4.0.

### 3. DivergenceMetric
The computed model instability score.
- **Attributes**: `clip_id`, `divergence_score`, `solver_steps` (N), `latent_dim`, `runtime_ms`, `status` (Success/Failed).
- **Constraints**: `divergence_score` >= 0.0.

### 4. AnalysisResult
Aggregated statistical outputs.
- **Attributes**: `metric_type` (Pearson/Spearman/Logistic), `value`, `p_value`, `confidence_interval`, `sample_size`.

## File Formats

### CSV: `data/annotations/manual_continuity_scores.csv`
Columns: `clip_id`, `annotator_id`, `likert_score`, `normalized_score`, `adjudicated`
- **Format**: UTF-8, comma-separated, no header quotes.
- **Validation**: `normalized_score` in [0.0, 1.0].

### CSV: `data/annotations/adjudication_log.csv`
Columns: `clip_id`, `annotator_1_score`, `annotator_2_score`, `expert_id`, `final_score`
- **Format**: UTF-8, comma-separated.
- **Validation**: `final_score` in [1, 5].

### Markdown: `data/annotations/rubric_definition.md`
- **Format**: UTF-8 text.
- **Content**: Detailed rubric for annotators (pixel-space features, 5-point scale definitions).
- **Contract**: `contracts/rubric_definition.md`.

### CSV: `data/processed/divergence_scores.csv`
Columns: `clip_id`, `divergence_score`, `solver_steps`, `runtime_ms`
- **Format**: UTF-8, comma-separated.
- **Validation**: `divergence_score` numeric.

### JSON: `data/processed/ipw_log.json`
- **Format**: UTF-8 JSON.
- **Content**: IPW weights for each clip.
- **Columns**: `clip_id`, `weight`, `estimated_prevalence`.
- **Contract**: `contracts/ipw_log.json`.

### CSV: `data/processed/dip_test_results.csv`
Columns: `clip_id`, `dip_statistic`, `p_value`, `is_bimodal`
- **Format**: UTF-8, comma-separated.
- **Contract**: `contracts/dip_test_results.schema.yaml`.

### CSV: `data/processed/fisher_z_test_results.csv`
Columns: `group1`, `group2`, `z_statistic`, `p_value`
- **Format**: UTF-8, comma-separated.
- **Contract**: `contracts/fisher_z_test_results.schema.yaml`.

### CSV: `data/processed/control_analysis.csv`
Columns: `clip_id`, `true_label`, `predicted_label`, `divergence_score`, `error_type` (FP/FN/TP/TN)
- **Format**: UTF-8, comma-separated.
- **Contract**: `contracts/control_analysis.schema.yaml`.

### Markdown: `artifacts/runtime_pilot_report.md`
- **Format**: UTF-8 text.
- **Content**: Runtime estimates, N adjustments, pilot results.
- **Contract**: `contracts/runtime_pilot_report.md`.

### Markdown: `artifacts/power_analysis_report.md`
- **Format**: UTF-8 text.
- **Content**: Effect size, power, sample size justification.
- **Contract**: `contracts/power_analysis_report.md`.

### Markdown: `artifacts/synthetic_validation_report.md`
- **Format**: UTF-8 text.
- **Content**: Sensitivity analysis results.
- **Contract**: `contracts/synthetic_validation_report.md`.

### CSV: `data/processed/variance_report.csv`
Columns: `variance`, `mean`, `std_dev`, `is_bimodal`, `dip_p_value`, `sample_size`
- **Format**: UTF-8, comma-separated.
- **Contract**: `contracts/variance_report.schema.yaml`.

### JSON: `data/processed/manual_calculation_expected.json`
- **Format**: UTF-8 JSON.
- **Content**: Expected values for validation.
- **Contract**: `contracts/manual_calculation_expected.schema.yaml`.

### JSON: `artifacts/final_report_manifest.json`
List of all artifacts with checksums.
```json
{
  "files": [
    {"path": "data/annotations/manual_continuity_scores.csv", "sha256": "..."},
    {"path": "artifacts/power_analysis_report.md", "sha256": "..."},
    {"path": "data/processed/variance_report.csv", "sha256": "..."},
    {"path": "data/processed/manual_calculation_expected.json", "sha256": "..."},
    {"path": "data/processed/dip_test_results.csv", "sha256": "..."}
  ]
}
```

### JSON: `artifacts/stability_check.json`
- **Format**: UTF-8 JSON.
- **Content**: Stability check results (noise level, delta r, stability met).
- **Contract**: `contracts/stability_check.schema.yaml`.

## Data Flow

1.  **Raw**: Video files downloaded to `data/raw/`.
2.  **Processed**:
    -   `data/annotations/`: Manual scores, adjudication log, rubric definition.
    -   `data/processed/`: Divergence scores, control analysis, IPW log, dip test results, fisher z test results, variance report, manual calculation expected.
    -   `data/synthetic/`: Physically modified clips.
3.  **Artifacts**: Reports and manifests in `artifacts/`.

## Constraints & Hygiene

- **Immutability**: Raw data in `data/raw/` is never modified.
- **Checksums**: All files in `data/` and `artifacts/` must be checksummed (SHA-256).
- **PII**: No PII allowed in video filenames or annotations.
- **Versioning**: Each run produces a timestamped subdirectory if re-run (e.g., `data/run_20260822/`).
- **Contract Compliance**: The annotation tool must validate output against `contracts/annotation.schema.yaml` and `contracts/adjudication_log.schema.yaml` before saving.

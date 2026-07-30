# Data Model: llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss

## Overview

This document defines the data structures used in the analysis pipeline. It ensures consistency between ingestion, feature engineering, and modeling.

## Entities

### 1. Sample
A single data point containing prompt, teacher scores, student score, and human annotations.

| Field | Type | Description |
|-------|------|-------------|
| `sample_id` | string | Unique identifier |
| `prompt` | string | Input text prompt |
| `teacher_scores` | list[float] | Scores for [Alignment, Realism, Aesthetics, Plausibility] |
| `student_score` | float | Scalar output from student model |
| `human_annotations` | dict | Keys: dimension names, Values: float scores |
| `primary_dimension` | string | The dimension used for fidelity loss calculation (from metadata) |
| `fidelity_loss` | float | MAE between student_score and human_annotations[primary_dimension] |
| `exclusion_status` | string | "included" or "excluded"; reason if excluded (e.g., "missing_human_annotation") |

### 2. Entanglement Features
Derived features for each sample.

| Field | Type | Description |
|-------|------|-------------|
| `sample_id` | string | Unique identifier |
| `variance` | float | Variance of teacher_scores |
| `entropy` | float | Shannon entropy of normalized teacher_scores |
| `skewness` | float | Skewness of teacher_scores |
| `kurtosis` | float | Kurtosis of teacher_scores |
| `mahalanobis_distance` | float | Distance from mean of teacher_scores using global covariance |
| `difficulty_proxy` | float | Mean of teacher_scores (control for prompt difficulty) |
| `dominant_eigenvalue` | float | Global dominant eigenvalue (context_only, not for training) |

### 3. Model Results
Final output of the pipeline.

| Field | Type | Description |
|-------|------|-------------|
| `r_squared` | float | R² score of the model |
| `mae` | float | Mean Absolute Error |
| `p_value` | float | P-value from permutation test |
| `n_samples` | int | Number of samples used |
| `n_features` | int | Number of features used |

## Storage Formats

- **Raw Data**: CSV or JSON (downloaded from source).
- **Processed Data**: Parquet (for efficiency) or JSON.
- **Features**: JSON (one record per sample).
- **Results**: JSON (`results/results.json`).
- **Data Quality Report**: JSON (`data/processed/data_quality_report.json`).

## Data Flow

1. **Ingestion**: Raw CSV/JSON -> `data/processed/raw_samples.json`
2. **Feature Engineering**: `raw_samples.json` -> `data/processed/features.json`
3. **Modeling**: `features.json` -> `results/model.pkl`, `results/results.json`
4. **Quality Report**: `ingestion.py` -> `data/processed/data_quality_report.json`
5. **Validation Report**: `stats.py` -> `results/validation_report.json`
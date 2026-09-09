# Data Model: The Impact of Simulated Social Validation on Self-Perception in Adolescents

## Overview

This document defines the data structures for the project, ensuring alignment with **FR-001** (Data Acquisition), **FR-008** (Measurement Model), and **Constitution VI** (Instrument Validity). The model supports both real data loading (if available) and synthetic generation.

## Entity Definitions

### 1. Participant
Represents an individual adolescent.
- `participant_id`: Unique string identifier (UUID).
- `age`: Integer (13-19).
- `gender`: Categorical (Male, Female, Non-binary, Prefer not to say).
- `offline_relationship_count`: Integer (Number of close friends/family).
- `intrinsic_trait_score`: Float (Standardized score, e.g., Neuroticism, range 0-100).

### 2. EngagementMetric
Represents social media interaction data.
- `participant_id`: Foreign key to Participant.
- `timestamp`: ISO 8601 datetime (must precede psychometric assessment).
- `likes_count`: Integer (≥ 0).
- `comment_count`: Integer (≥ 0).
- `comment_sentiment_score`: Float (-1.0 to 1.0, derived from NLP or simulated).
- `raw_validation_proxy`: Float (Computed: `likes_count` * weight + `comment_sentiment_score` * weight).

### 3. PsychometricScore
Represents validated self-report scales.
- `participant_id`: Foreign key to Participant.
- `assessment_timestamp`: ISO 8601 datetime (must be after `timestamp`).
- `rosenberg_self_esteem_score`: Float (0-30, raw score from RSES).
- `body_image_score`: Float (Standardized score).
- `perceived_validation_score`: Float (Latent construct derived from `EngagementMetric` via measurement model).

### 4. ModelResult
Output of the regression analysis.
- `model_id`: Unique identifier.
- `predictor`: Name of the variable (e.g., `perceived_validation_score`).
- `coefficient`: Float ($\beta$).
- `standard_error`: Float.
- `p_value`: Float.
- `confidence_interval_lower`: Float.
- `confidence_interval_upper`: Float.
- `vif_score`: Float (if applicable).

### 5. SyntheticDataConfig
Parameters for the generator.
- `target_n`: Integer (Sample size).
- `true_beta_validation`: Float (Ground truth coefficient).
- `true_beta_confounders`: Dict (True coefficients for confounders).
- `noise_variance`: Float.
- `seed`: Integer (Random seed).

## Data Flow

1.  **Ingestion**: `loader.py` attempts to load real CSV/Parquet.
    - If columns missing: Triggers `generator.py`.
2.  **Generation**: `generator.py` creates `Participant`, `EngagementMetric`, and `PsychometricScore` records with known correlations.
    - Ensures `timestamp` < `assessment_timestamp`.
    - Applies **FR-008** to derive `perceived_validation_score`.
3.  **Validation**: `validator.py` checks:
    - $N \ge 100$.
    - No PII.
    - Longitudinal ordering.
4.  **Analysis**: `regression.py` consumes validated data to produce `ModelResult`.

## Constraints & Rules

- **Longitudinal Integrity**: `EngagementMetric.timestamp` MUST be strictly less than `PsychometricScore.assessment_timestamp`.
- **Missing Data**: Rows with missing `age`, `gender`, or `intrinsic_trait_score` are dropped (listwise deletion) and logged.
- **Scaling**: All continuous predictors (except counts) are standardized (Z-score) before regression to interpret coefficients as effect sizes.
- **Causality**: No field in the data model implies causality; all relationships are labeled "associational".

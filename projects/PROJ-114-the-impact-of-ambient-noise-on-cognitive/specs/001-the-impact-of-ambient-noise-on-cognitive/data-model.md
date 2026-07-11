# Data Model: The Impact of Ambient Noise on Cognitive Flexibility in Remote Workers

## Overview

This document defines the data structures for the ambient noise study. The model supports ingestion of raw logs, computation of derived metrics (CFI) with validation checks, and storage of model results. All data is stored in CSV/JSONL formats with checksums for reproducibility.

## Entity Definitions

### Participant

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `participant_id` | str | Unique identifier | Primary key; non-null |
| `age` | int | Age in years | 18-80 |
| `gender` | str | Self-reported gender | Enum: "M", "F", "Other" |
| `job_type` | str | Remote work category | Enum: "Tech", "Admin", "Creative", "Other" |
| `noise_sensitivity` | float | Self-reported sensitivity (1-10) | 1.0-10.0 |
| `baseline_cfi` | float | Baseline cognitive flexibility score | Z-scored |
| `calibration_status` | str | Calibration result | Enum: "pass", "fail", "missing" |
| `valid_logging_proportion` | float | Proportion of valid 1-min bins | 0.0-1.0 (Calculated) |

### NoiseLog

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `log_id` | str | Unique log identifier | Primary key |
| `participant_id` | str | Foreign key to Participant | Non-null |
| `timestamp` | datetime | Time of recording | Resolution ≤10ms |
| `decibel_level` | float | Ambient noise in dB | ≥0.0; error margin <2dB |
| `session_id` | str | Session identifier | Non-null |

### TaskPerformance

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `trial_id` | str | Unique trial identifier | Primary key |
| `participant_id` | str | Foreign key to Participant | Non-null |
| `session_id` | str | Session identifier | Non-null |
| `trial_type` | str | Switch or Repeat | Enum: "switch", "repeat" |
| `reaction_time_ms` | float | Reaction time in ms | >0; outliers >3SD removed |
| `error_flag` | bool | Rule violation | True/False |
| `timestamp` | datetime | Trial timestamp | Non-null |

### ModelResult

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `model_id` | str | Unique model identifier | Primary key |
| `participant_id` | str | Participant (if per-subject) | Nullable |
| `noise_level_coef` | float | Coefficient for linear noise term | |
| `noise_level_sq_coef` | float | Coefficient for quadratic noise term | |
| `noise_var_coef` | float | Coefficient for noise variability | |
| `p_value_lrt` | float | P-value from likelihood-ratio test | 0.0-1.0 |
| `convergence_status` | str | Model convergence | Enum: "success", "warning", "failure" |
| `vif_level` | float | VIF for noise_level | ≥1.0 |
| `vif_var` | float | VIF for noise_variability | ≥1.0 |
| `fwer_observed` | float | Observed family-wise error rate | 0.0-1.0 |

## Data Flow

1.  **Ingestion**: Raw logs (NoiseLog) and task data (TaskPerformance) are loaded from `data/raw/`.
2.  **Validation**: Gaps >20% of session time flagged (1-min bin logic); outliers >3SD removed; calibration status checked.
3.  **Aggregation**: Noise logs aggregated to session-level (mean, std); CFI computed with correlation check.
4.  **Modeling**: LMM fitted; results stored in `ModelResult`.
5.  **Sensitivity**: Threshold sweeps re-run model; results aggregated.

## Derived Metrics

### Cognitive Flexibility Index (CFI)

**Step 1: Calculate Components**
- `reaction_time_diff`: Mean reaction time for switch trials minus mean for repeat trials.
- `error_count`: Total rule violations in the session.
- `z_rt_diff`: Standardized (mean=0, std=1) reaction time difference.
- `z_error`: Standardized (mean=0, std=1) error count.

**Step 2: Component Independence Check**
- Calculate Pearson correlation `r` between `z_rt_diff` and `z_error` across the dataset.
- **If r > 0.7**: The components are redundant. **CFI = z_rt_diff** (Error count is ignored for this metric).
- **Else**: **CFI = z_rt_diff + z_error**.

> **Note**: This conditional logic prevents the creation of a redundant composite score if the speed-accuracy trade-off is high, ensuring the CFI accurately measures the intended construct. Theoretical justification: In task-switching literature, switch cost (RT difference) is the primary metric; error counts are often highly correlated with RT. Summing them without checking for redundancy risks creating a tautological score.

### Noise Categories (Descriptive Only)

| Category | Range (dB) |
|----------|------------|
| Low | <45 |
| Moderate | 45-65 |
| High | >65 |

> **Note**: These categories are used for descriptive analysis and post-hoc comparisons only. The primary model uses continuous noise levels.

### Valid Logging Hours (FR-007)

- **Definition**: Count of 1-minute bins containing ≥1 log entry.
- **Threshold**: Participant is valid if `valid_logging_proportion` >= 0.80.
- **Calculation**: `(Number of valid 1-min bins) / (Total expected 1-min bins in session)`.

## Residualized Variability (for Structural Dependency)

If `noise_variability` is found to be structurally dependent on `noise_level` (VIF > 5):
- **Method**: Regress `noise_variability` against `noise_level` and use the residuals as the predictor.
- **Purpose**: To isolate the unique variance of variability not explained by the mean, preventing confounding of the quadratic term.
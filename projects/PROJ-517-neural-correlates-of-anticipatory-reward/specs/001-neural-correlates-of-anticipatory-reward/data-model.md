# Data Model: Neural Correlates of Anticipatory Reward Processing

## Overview

This document defines the data model for the project, derived from `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml`. It specifies the field types, units, and constraints required for ingestion, validation, and statistical modeling of neural spike data in the context of reward processing.

## Input Data Model (Raw)

### Entity: Spike Event

Represents a single detected spike from a neuron during a trial. This entity is the fundamental unit of analysis for calculating firing rates and temporal correlations.

| Field | Type | Unit | Description | Constraints |
|:--- |:--- |:--- |:--- |:--- |
| `trial_id` | string | - | Unique trial identifier | Pattern: `trial_XXXX` (e.g., `trial_0001`) |
| `neuron_id` | string | - | Unique neuron identifier | Pattern: `neuron_XX` (e.g., `neuron_01`) |
| `spike_time_ms` | float | ms | Timestamp of spike relative to trial start | >= 0.0; Must be a flat float for streaming compatibility |
| `cue_time_ms` | float | ms | Timestamp of cue stimulus onset | >= 0.0; Required for `cue_delay` calculation |
| `reward_time_ms` | float | ms | Timestamp of reward delivery | >= 0.0; Required for spike windowing |
| `reward_magnitude` | float | units | Magnitude of reward delivered | Discrete levels (e.g., 0.1, 0.5, 1.0) |
| `snr` | float | ratio | Signal-to-Noise Ratio from spike sorting | > 3.0 (valid); <= 3.0 triggers rejection |
| `isolation_distance` | float | ratio | Spike sorting isolation metric | > 20.0 (valid); <= 20.0 triggers rejection |

## Derived Fields (Processed)

These fields are calculated during the ingestion phase (Task T012, T012b) and used in modeling.

| Field | Type | Unit | Derivation Logic | Constraints |
|:--- |:--- |:--- |:--- |:--- |
| `spike_count` | integer | count | Count of `spike_time_ms` in window `[-500ms, 0ms]` relative to `reward_time_ms` | >= 0 |
| `cue_delay` | float | ms | `reward_time_ms` - `cue_time_ms` | > 0.0; < 500ms flags as `confounded` |
| `firing_rate` | float | spikes/sec | `spike_count` / 0.5 | >= 0.0 |
| `confounded` | boolean | - | `True` if `cue_delay` < 500ms | N/A |

## Output Data Model (Validation & Reporting)

### Entity: Validation Report

Aggregated metrics regarding data quality and filtering.

| Field | Type | Description |
|:--- |:--- |:--- |
| `ingestion_rows_total` | integer | Total rows read from input source |
| `ingestion_rows_valid` | integer | Rows passing quality checks (SNR, Isolation) |
| `ingestion_rows_dropped` | integer | Rows filtered out due to quality or missing data |
| `validated_sample_size` | integer | Final N (trials) available for analysis |
| `confounded_trial_count` | integer | Count of trials with `cue_delay` < 500ms |
| `confounded_trial_ids` | list[string] | List of `trial_id`s flagged as confounded |
| `status` | string | Overall pipeline status: `SUCCESS`, `LIMITED`, or `REJECTED` |

### Entity: Model Results

Statistical outputs from the Generalized Linear Model (GLM).

| Field | Type | Description |
|:--- |:--- |:--- |
| `coefficient` | float | GLM coefficient for `reward_magnitude` |
| `std_err` | float | Standard error of the coefficient |
| `p_value` | float | Significance of the coefficient (two-tailed) |
| `dispersion` | float | Estimated dispersion parameter (for NB model) |
| `mdes` | float | Minimum Detectable Effect Size at 80% power |
| `cv_score_mean` | float | Cross-validation R² mean |
| `cv_score_std` | float | Cross-validation R² std |
| `formula` | string | Final model formula used (e.g., `firing_rate ~ reward_magnitude + cue_delay`) |

## Relationships

- **Spike Event** -> **Trial**: Many-to-One (Multiple spikes per trial)
- **Spike Event** -> **Neuron**: Many-to-One (Multiple spikes per neuron)
- **Validation Report** -> **Model Results**: One-to-One (Derived from validated data)

## Constraints & Rules

1. **Streaming Compatibility**: All timestamp fields (`spike_time_ms`, `cue_time_ms`, `reward_time_ms`) are stored as flat floats, not arrays, to enable chunked processing of large datasets via `streaming=True`.
2. **Quality Thresholds**:
 - `snr` must be > 3.0.
 - `isolation_distance` must be > 20.0.
 - Rows failing these checks are dropped and logged.
3. **Temporal Validity**:
 - `cue_time_ms` and `reward_time_ms` must be >= 0.0.
 - `cue_delay` < 500ms indicates a confounded trial (cue and reward overlap too closely).
4. **Statistical Power**:
 - Minimum 30 trials per reward magnitude level required (FR-007).
 - If `validated_sample_size` is insufficient, MDES will be high, limiting interpretability.
5. **Data Integrity**:
 - Synthetic data is only allowed in CI environments (`CI=true`).
 - Production runs must use real data from verified sources (OpenNeuro/Zenodo) or fail loudly.
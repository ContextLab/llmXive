# Data Model: Neural Correlates of Anticipatory Reward Processing in Vocal Learning

## Overview
This document defines the data structures for the ingestion, processing, and analysis pipeline. It ensures traceability from raw spike data to final statistical reports.

## Input Schema (contracts/dataset.schema.yaml)
*Refer to `contracts/dataset.schema.yaml` for the formal YAML definition.*

### Fields
| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `trial_id` | string | Unique identifier for each trial. | Non-empty, unique per session. |
| `neuron_id` | string | Identifier for the recorded neuron. | Non-empty. |
| `spike_timestamps` | list[float] | Array of spike times in milliseconds. | Sorted ascending. |
| `reward_magnitude` | float | Magnitude of reward delivered. | >= 0. |
| `cue_timestamps` | list[float] | Array of cue presentation times. | Sorted ascending. |
| `spike_sorting_metadata` | object | SNR and isolation distance metrics. | `snr` >= 0, `isolation_distance` >= 0. |
| `reward_timestamp` | float | Timestamp of reward delivery. | Reference point (t=0). |
| `cue_timestamp` | float | Timestamp of cue presentation. | Must be < `reward_timestamp`. |

## Output Schema (contracts/output.schema.yaml)
*Refer to `contracts/output.schema.yaml` for the formal YAML definition.*

### Unified DataFrame Columns
| Field | Type | Description |
| :--- | :--- | :--- |
| `trial_id` | string | Original trial ID. |
| `neuron_id` | string | Original neuron ID. |
| `spike_count` | int | Count of spikes in [-500ms, 0ms] window. |
| `reward_magnitude` | float | Normalized reward magnitude. |
| `cue_delay_ms` | float | Time difference (cue to reward). |
| `valid_spike_sorting` | bool | True if SNR and isolation distance meet thresholds. |
| `flagged_short_delay` | bool | True if cue-reward delay < 500ms. |
| `firing_rate` | float | Calculated firing rate (spikes/sec). |
| `cv_score` | float | Cross-validation score. |
| `mdes` | float | Minimum Detectable Effect Size. |
| `ingestion_rows_total` | int | Total rows read. |
| `ingestion_rows_valid` | int | Valid rows. |
| `ingestion_rows_dropped` | int | Dropped rows. |

### Reports
1.  **Validation Report (JSON)**: `data/processed/validation_report.json`
    *   Contains ingestion metrics: `total_rows`, `valid_rows`, `dropped_rows`, `reasons`.
2.  **Spike Sorting Report (Markdown)**: `data/processed/spike_sorting_validation_report.md`
    *   Contains counts of neurons passing/failing SNR/isolation thresholds.
3.  **Summary Statistics (Text)**: `data/processed/summary_report.txt`
    *   Contains GLM coefficients, p-values, MDES, CV scores.

## Data Flow

1.  **Raw Ingestion**: `data/raw/*.csv` -> `ingestion.py` -> `data/processed/unified_data.csv`.
2.  **Validation**: `ingestion.py` checks `spike_sorting_metadata` -> `spike_sorting_validation_report.md`.
3.  **Modeling**: `modeling.py` reads `unified_data.csv` -> `data/processed/model_results.json`.
4.  **Visualization**: `visualization.py` reads `model_results.json` -> `data/figures/*.png`.

## Constraints & Assumptions
*   **Time Units**: All timestamps in milliseconds (ms).
*   **Spike Sorting**: Metadata fields (`snr`, `isolation_distance`) are assumed to be present. If missing, `valid_spike_sorting` is set to `False` and the pipeline halts the causal claim.
*   **Missing Data**: Rows with missing `spike_timestamps` or `reward_magnitude` are dropped.
*   **Zero-Reward Trials**: Included in analysis but flagged if `reward_magnitude` is 0.

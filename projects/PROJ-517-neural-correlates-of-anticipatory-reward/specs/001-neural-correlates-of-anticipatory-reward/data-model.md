# Data Model: Neural Correlates of Anticipatory Reward Processing in Vocal Learning

## Overview
This document defines the data structures for the ingestion, processing, and analysis pipeline. It ensures traceability from raw spike data to final statistical reports. The model aligns with `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml`.

## Input Schema (contracts/dataset.schema.yaml)
*Refer to `contracts/dataset.schema.yaml` for the formal YAML definition.*

The pipeline ingests data in a flat-row format to support streaming and efficient processing.

### Fields
| Field | Type | Unit | Description | Constraints |
|:--- |:--- |:--- |:--- |:--- |
| `trial_id` | string | - | Unique identifier for each trial. | Non-empty, unique per session. |
| `neuron_id` | string | - | Identifier for the recorded neuron. | Non-empty. |
| `spike_time_ms` | float | ms | Timestamp of a single spike event. | Sorted ascending within a trial/neuron context. |
| `cue_time_ms` | float | ms | Timestamp of cue presentation. | Must be < `reward_time_ms`. |
| `reward_time_ms` | float | ms | Timestamp of reward delivery. | Reference point (t=0) for analysis windows. |
| `reward_magnitude` | float | arbitrary units | Magnitude of reward delivered. | >= 0. |
| `snr` | float | dB | Signal-to-Noise Ratio from spike sorting. | >= 0. Rejection threshold: <= 3. |
| `isolation_distance` | float | dimensionless | Isolation distance metric from spike sorting. | >= 0. Rejection threshold: <= 20. |

## Derived Fields (Ingestion Stage)
These fields are calculated during the `code/ingestion.py` phase (T012, T012b) and appended to the unified dataset.

| Field | Type | Unit | Description | Calculation Logic |
|:--- |:--- |:--- |:--- |:--- |
| `spike_count` | int | count | Number of spikes in the anticipatory window. | Count where `reward_time_ms - 500 <= spike_time_ms <= reward_time_ms`. |
| `cue_delay` | float | ms | Time difference between cue and reward. | `reward_time_ms - cue_time_ms`. |
| `firing_rate` | float | spikes/sec | Normalized firing rate in the window. | `spike_count / 0.5` (window is 500ms). |
| `confounded` | bool | - | Flag for short cue-reward delays. | `True` if `cue_delay < 500`. |
| `valid_spike_sorting` | bool | - | Flag for quality control. | `True` if `snr > 3` AND `isolation_distance > 20`. |

## Output Schema (contracts/output.schema.yaml)
*Refer to `contracts/output.schema.yaml` for the formal YAML definition.*

The final unified DataFrame (T014) contains the following columns for modeling:

| Field | Type | Description |
|:--- |:--- |:--- |
| `trial_id` | string | Original trial ID. |
| `neuron_id` | string | Original neuron ID. |
| `spike_count` | int | Count of spikes in [-500ms, 0ms] window. |
| `reward_magnitude` | float | Normalized reward magnitude. |
| `cue_delay` | float | Time difference (cue to reward) in ms. |
| `firing_rate` | float | Calculated firing rate (spikes/sec). |
| `confounded` | bool | Flag for short delays. |
| `valid_spike_sorting` | bool | Quality control flag. |

### Reports
1. **Validation Report (JSON)**: `data/processed/validation_report.json`
 * Contains ingestion metrics: `ingestion_rows_total`, `ingestion_rows_valid`, `ingestion_rows_dropped`, `validated_sample_size`, `confounded_trial_count`, `flagged_trial_ids`.
2. **Spike Sorting Report (Markdown)**: `data/processed/spike_sorting_validation_report.md`
 * Contains counts of neurons passing/failing SNR/isolation thresholds.
3. **Summary Statistics (Text)**: `data/processed/summary_report.txt`
 * Contains GLM coefficients, p-values, MDES, CV scores.

## Data Flow

1. **Raw Ingestion**: `data/raw/*.csv` -> `ingestion.py` -> `data/processed/unified_data.csv`.
2. **Validation**: `ingestion.py` checks `snr`/`isolation_distance` -> `spike_sorting_validation_report.md`.
3. **Modeling**: `modeling.py` reads `unified_data.csv` -> `data/processed/model_results.json`.
4. **Visualization**: `visualization.py` reads `model_results.json` -> `data/figures/*.png`.

## Constraints & Assumptions
* **Time Units**: All timestamps and delays in milliseconds (ms).
* **Spike Sorting**: Metadata fields (`snr`, `isolation_distance`) are mandatory. If missing, `state/claim_status.json` is set to `REJECTED`.
* **Missing Data**: Rows with missing `spike_time_ms`, `cue_time_ms`, or `reward_time_ms` are dropped.
* **Zero-Reward Trials**: Included in analysis but handled explicitly in validation.
* **Streaming**: The flat-row format (one spike per row) is designed for `datasets.load_dataset(..., streaming=True)` to handle large neurophysiology datasets without loading full arrays into RAM.
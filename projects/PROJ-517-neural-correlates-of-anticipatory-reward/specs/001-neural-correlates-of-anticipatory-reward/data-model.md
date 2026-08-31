# Data Model: Neural Correlates of Anticipatory Reward Processing

## Entities

### Trial
- trial_id: str (unique identifier)
- neuron_id: str (recorded neuron identifier)
- cue_timestamps: List[float] (timestamps of cue presentations in seconds)
- reward_timestamp: float (timestamp of reward delivery in seconds)
- reward_magnitude: float (magnitude of reward, continuous variable)
- spike_timestamps: List[float] (timestamps of detected spikes in seconds)

### Neuron
- neuron_id: str (unique identifier)
- brain_region: str (e.g., "NAcc", "VTA")
- spike_sorting_metadata: Dict (SNR, isolation_distance, etc.)

### SpikeTrain
- neuron_id: str (foreign key to Neuron)
- trial_id: str (foreign key to Trial)
- spike_timestamps: List[float] (spike times relative to trial start)
- spike_count: int (number of spikes in analysis window)

## Relationships

- One Trial has one Neuron
- One Trial has one SpikeTrain
- One Neuron can have multiple Trials
- One Neuron can have multiple SpikeTrains

## Data Flow

1. Raw Data (CSV/Neurodata) -> Ingestion Pipeline
2. Ingestion -> Validation -> Unified DataFrame
3. Unified DataFrame -> Statistical Modeling
4. Model Results -> Visualization
5. All Metrics -> Summary Report

## Data Quality Requirements

- Minimum 30 trials per reward magnitude level
- Cue-reward delay >= 500ms (flag if <500ms)
- SNR > 3 for spike sorting acceptance
- Isolation Distance > 20 for spike sorting acceptance
- Handle zero-reward trials as valid
- Filter silent neurons (0 spikes across all trials)

## Output Data Structures

### Unified DataFrame Columns
- trial_id: str
- neuron_id: str
- spike_count: int
- reward_magnitude: float
- timestamp_relative_to_reward: float

### Validation Report (JSON)
- ingestion_rows_total: int
- ingestion_rows_valid: int
- ingestion_rows_dropped: int
- validation_status: str (PASS/FAIL/WARN)
- flags: List[str] (validation issues)

### Model Results (JSON)
- coefficient: float
- p_value: float
- model_family: str (Poisson/NegativeBinomial)
- dispersion: float
- mdes_80_power: float
- cv_score_mean: float
- cv_score_std: float
- neuron_count: int
- bonferroni_corrected_p: float

# Data Model Specification

## Overview
This document defines the core data structures used throughout the pipeline for representing participants, structural connectomes, and avalanche records. All data is stored in `data/processed` or `data/results` in JSON, CSV, or NumPy formats.

## Core Entities

### Participant
Represents a single subject in the study.
- `subject_id`: Unique identifier (string).
- `source`: Data source (e.g., "OpenNeuro_ds004230", "Simulation").
- `qc_status`: Pass/Fail status from quality control.
- `eeg_path`: Path to processed EEG time-series (if available).
- `connectome_path`: Path to structural adjacency matrix.

### StructuralConnectome
Represents the weighted adjacency matrix of the brain network.
- `subject_id`: Reference to Participant.
- `matrix`: 2D NumPy array (N x N) of connection weights.
- `parcellation`: Name of the parcellation scheme (e.g., "HCP-MMP1.0").
- `checksum`: SHA-256 hash of the matrix file for integrity.

### AvalancheRecord
Represents a single neural avalanche event.
- `subject_id`: Reference to Participant.
- `size`: Number of active channels/time steps.
- `duration`: Duration in time steps.
- `timestamp`: Start time of the avalanche.
- `channels`: List of involved channel indices.

## File Formats

### `data/processed/simulation_metadata.json`
Contains parameters for synthetic data generation.
```json
{
 "seed": 42,
 "wilson_cowan_params": {
 "connection_strength": 0.5,
 "time_constant": 10.0
 },
 "checksum": "sha256_hash"
}
```

### `data/processed/avalanche_metrics.csv`
Aggregated metrics for all participants.
Columns: `subject_id`, `avg_size`, `avg_duration`, `power_law_exponent`, `p_value`.

### `data/results/correlation_report.csv`
Statistical association results.
Columns: `metric_name`, `avalanche_metric`, `rho`, `p_value`, `corrected_p_value`.

## Data Flow
1. **Raw**: `data/raw/` (Downloaded dMRI/EEG).
2. **Processed**: `data/processed/` (Connectomes, Cleaned EEG, Metrics).
3. **Results**: `data/results/` (Final statistical reports, plots).

## Integrity & Versioning
- All processed files have associated SHA-256 checksums.
- `data/processed/data_status.json` tracks the pipeline path (Real vs. Simulation).
- `state/projects/...yaml` tracks project state and versioning.

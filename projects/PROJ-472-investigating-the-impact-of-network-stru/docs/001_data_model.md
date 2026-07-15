# Data Model Specification

This document defines the core data structures used in the `llmXive` pipeline for investigating the impact of network structure on neural avalanche dynamics.

## Overview

The pipeline processes structural connectomes (dMRI) and neural activity time-series (EEG/Simulation) to derive network metrics and avalanche statistics. The data flow is:
1. **Raw**: dMRI tractography (`.tck`), EEG recordings (`.edf`/`.bdf`).
2. **Processed**: Adjacency matrices (`.npy`), filtered time-series (`.csv`).
3. **Results**: Metrics (`.csv`), fitting parameters, correlation reports.

## Core Entities

### 1. Participant
Represents a single subject in the study.

| Field | Type | Description |
|:--- |:--- |:--- |
| `id` | `str` | Unique identifier (e.g., "sub-001") |
| `age` | `Optional[int]` | Age in years |
| `sex` | `Optional[str]` | Biological sex (M/F) |
| `group` | `str` | Experimental group (e.g., "Control", "Patient") |

**Source**: `code/data/models.py` -> `Participant` dataclass.

### 2. StructuralConnectome
Represents the weighted adjacency matrix derived from dMRI tractography.

| Field | Type | Description |
|:--- |:--- |:--- |
| `participant_id` | `str` | Link to Participant |
| `matrix` | `np.ndarray` | N x N weighted adjacency matrix (N=90 or N=114) |
| `parcellation` | `str` | Name of the atlas used (e.g., "HCP-MMP1.0") |
| `threshold` | `float` | Optional threshold applied |
| `file_path` | `Path` | Path to stored `.npy` file |

**Source**: `code/data/models.py` -> `StructuralConnectome` dataclass.

### 3. AvalancheRecord
Represents a single detected neural avalanche event.

| Field | Type | Description |
|:--- |:--- |:--- |
| `participant_id` | `str` | Link to Participant |
| `start_time` | `float` | Start time in seconds |
| `end_time` | `float` | End time in seconds |
| `size` | `int` | Total number of active channels/events |
| `duration` | `float` | Duration in seconds |
| `channels` | `List[int]` | List of channel indices involved |

**Source**: `code/data/models.py` -> `AvalancheRecord` dataclass.

## Data Storage Locations

All paths are relative to the project root.

- **Raw Data**: `data/raw/`
 - `dMRI/`: Tractography files (`.tck`)
 - `EEG/`: Raw recordings (`.edf`, `.bdf`)
- **Processed Data**: `data/processed/`
 - `connectomes/`: Adjacency matrices (`.npy`)
 - `eeg_cleaned/`: Filtered time-series (`.csv`)
 - `simulation_metadata.json`: Wilson-Cowan parameters and seeds used.
- **Results**: `data/results/`
 - `metrics.csv`: Structural and avalanche metrics.
 - `correlation_report.csv`: Statistical associations.
 - `null_result_report.md`: Protocol report if N < 10.

## File Formats

### Adjacency Matrix (`.npy`)
- Format: NumPy binary.
- Shape: `(N, N)` where N is the number of parcels.
- Content: Float64 weights representing streamline count or density.

### Time-Series (`.csv`)
- Format: Comma-separated values.
- Columns: `time`, `channel_0`, `channel_1`,..., `channel_N`.
- Sampling Rate: 250 Hz (downsampled from original).

### Simulation Metadata (`.json`)
- Format: JSON.
- Keys: `seed`, `wilson_cowan_params` (dict), `timestamp`, `subject_id`.
- Example:
 ```json
 {
 "subject_id": "sub-001",
 "seed": 42,
 "wilson_cowan_params": {
 "tau_e": 1.0,
 "tau_i": 0.5,
 "sigma": 0.1
 }
 }
 ```

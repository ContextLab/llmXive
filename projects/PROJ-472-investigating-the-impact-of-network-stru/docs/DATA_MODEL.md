# Data Model Specification

This document describes the core data structures used in the llmXive pipeline for investigating the impact of network structure on neural avalanche dynamics.

## Overview

The project utilizes three primary data entities:
1. `Participant`: Represents a subject in the study, linking structural and functional data.
2. `StructuralConnectome`: Represents the structural connectivity matrix derived from dMRI.
3. `AvalancheRecord`: Represents a detected neural avalanche event from EEG data.

## Entity Definitions

### Participant

The `Participant` class encapsulates metadata and file paths for a single study subject.

**Location**: `code/data/models.py`

**Attributes**:
- `subject_id` (str): Unique identifier for the participant (e.g., "sub-001").
- `age` (Optional[int]): Age of the participant in years.
- `sex` (Optional[str]): Biological sex of the participant.
- `raw_dwi_path` (Optional[Path]): Path to the raw diffusion MRI data (`.nii.gz`).
- `connectome_path` (Optional[Path]): Path to the processed adjacency matrix (`.csv` or `.npy`).
- `eeg_path` (Optional[Path]): Path to the simulated or recorded EEG time-series (`.fif` or `.csv`).
- `qc_status` (Optional[Dict]): Quality control metrics (SNR, connectivity status).

**Usage Example**:
```python
from data.models import Participant

p = Participant(subject_id="sub-001", age=25, sex="M")
p.qc_status = {"snr": 12.5, "is_connected": True}
```

### StructuralConnectome

The `StructuralConnectome` class represents the weighted adjacency matrix of the brain network.

**Location**: `code/data/models.py`

**Attributes**:
- `subject_id` (str): Link to the `Participant`.
- `matrix` (np.ndarray): 2D numpy array representing the connectivity weights (N x N).
- `parcel_names` (List[str]): List of region names corresponding to matrix indices.
- `parcellation_scheme` (str): Name of the atlas used (e.g., "HCP-MMP1.0").
- `threshold` (Optional[float]): The threshold applied to the matrix (if any).

**Methods**:
- `to_networkx()`: Converts the matrix to a `networkx.Graph` object.
- `get_degree_centrality()`: Returns a 1D array of degree centralities.

**Usage Example**:
```python
from data.models import StructuralConnectome
import numpy as np

matrix = np.array([[0, 0.5], [0.5, 0]])
conn = StructuralConnectome(
 subject_id="sub-001",
 matrix=matrix,
 parcel_names=["Frontal", "Parietal"],
 parcellation_scheme="HCP-MMP1.0"
)
G = conn.to_networkx()
```

### AvalancheRecord

The `AvalancheRecord` class stores details about a single detected neural avalanche.

**Location**: `code/data/models.py`

**Attributes**:
- `subject_id` (str): Link to the `Participant`.
- `start_time` (float): Start time of the avalanche in seconds.
- `end_time` (float): End time of the avalanche in seconds.
- `size` (int): Total number of active time bins or events in the avalanche.
- `duration` (float): Duration of the avalanche in seconds.
- `amplitude` (float): Peak amplitude of the avalanche.
- `channels_involved` (List[int]): Indices of channels that participated.

**Usage Example**:
```python
from data.models import AvalancheRecord

record = AvalancheRecord(
 subject_id="sub-001",
 start_time=10.5,
 end_time=11.2,
 size=15,
 duration=0.7,
 amplitude=2.3,
 channels_involved=[0, 1, 4]
)
```

## Data Flow

1. **Ingestion**: Raw dMRI data is loaded into `Participant` objects via `code/data/download.py`.
2. **Processing**: `preprocess_dMRI.py` generates `StructuralConnectome` objects.
3. **Simulation**: `simulate_EEG.py` generates time-series data associated with `Participant`.
4. **Analysis**: `code/analysis/avalanches.py` processes EEG signals to produce `AvalancheRecord` lists.
5. **Storage**: All artifacts are serialized to `data/processed/` and indexed in the central store.

## File Formats

- **Connectomes**: Saved as CSV (dense matrix) with headers as parcel names.
- **EEG**: Saved as `.fif` (MNE-Python format) or CSV (time x channels).
- **Avalanches**: Aggregated results stored in `data/results/avalanches.csv`.

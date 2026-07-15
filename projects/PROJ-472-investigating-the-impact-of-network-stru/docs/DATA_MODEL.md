# Data Model Specification

This document defines the core data entities used throughout the Network Structure & Neural Avalanche Dynamics research pipeline.

## Overview

The pipeline processes structural connectomes and simulated EEG data to compute network metrics and avalanche statistics. The data model ensures consistency across the download, preprocessing, simulation, analysis, and reporting stages.

## Core Entities

### Participant

Represents a single subject in the study.

**Location**: `code/data/models.py`

```python
@dataclass
class Participant:
 subject_id: str
 qc_passed: bool = False
 metadata: Dict[str, Any] = field(default_factory=dict)
```

**Fields**:
- `subject_id` (str): Unique identifier (e.g., "sub-001", "sub-002")
- `qc_passed` (bool): Whether the participant passed quality control checks
- `metadata` (Dict): Additional subject information (age, sex, etc.)

**Usage**:
```python
from data.models import Participant

participant = Participant(subject_id="sub-001", metadata={"age": 25})
```

---

### StructuralConnectome

Represents the structural brain network derived from diffusion MRI tractography.

**Location**: `code/data/models.py`

```python
@dataclass
class StructuralConnectome:
 subject_id: str
 adjacency_matrix: np.ndarray
 node_labels: List[str]
 source_file: Optional[str] = None
```

**Fields**:
- `subject_id` (str): Link to the participant
- `adjacency_matrix` (np.ndarray): N x N weighted adjacency matrix
- `node_labels` (List[str]): Names of brain regions (e.g., HCP-MMP1.0 parcels)
- `source_file` (str, optional): Path to the original tractography file

**Usage**:
```python
from data.models import StructuralConnectome
import numpy as np

matrix = np.random.rand(100, 100)
labels = [f"Region_{i}" for i in range(100)]
connectome = StructuralConnectome(subject_id="sub-001", adjacency_matrix=matrix, node_labels=labels)
```

**Storage**: Saved as `.npy` files in `data/processed/connectomes/`

---

### AvalancheRecord

Represents a detected neural avalanche event from the simulated EEG time-series.

**Location**: `code/data/models.py`

```python
@dataclass
class AvalancheRecord:
 subject_id: str
 start_time: float
 end_time: float
 size: float
 duration: int
 power_law_fit: Optional[Dict[str, float]] = None
```

**Fields**:
- `subject_id` (str): Link to the participant
- `start_time` (float): Start timestamp of the avalanche
- `end_time` (float): End timestamp of the avalanche
- `size` (float): Total activity (sum of amplitudes during the event)
- `duration` (int): Duration in time steps
- `power_law_fit` (Dict, optional): Fitted power-law parameters (exponent, xmin)

**Usage**:
```python
from data.models import AvalancheRecord

record = AvalancheRecord(
 subject_id="sub-001",
 start_time=0.5,
 end_time=1.2,
 size=15.4,
 duration=70
)
```

**Storage**: Aggregated into CSVs in `data/results/avalanche_metrics.csv`

---

## Data Flow

1. **Download**: Raw dMRI data (`bvec`, `bval`, `dwi.nii.gz`) fetched from OpenNeuro.
2. **Preprocessing**: Tractography (`.tck`) converted to `StructuralConnectome` (adjacency matrix).
3. **Simulation**: `StructuralConnectome` used to generate simulated EEG time-series.
4. **QC**: `Participant` marked as `qc_passed` based on graph connectivity and SNR.
5. **Analysis**: Simulated EEG processed to extract `AvalancheRecord` events.
6. **Metrics**: Network metrics computed from `StructuralConnectome`.
7. **Export**: All metrics aggregated into participant-level CSVs.

## File Formats

### Connectome Storage
- **Format**: NumPy `.npy`
- **Path**: `data/processed/connectomes/{subject_id}_connectome.npy`
- **Structure**: 2D array (N_nodes x N_nodes)

### EEG Time-Series
- **Format**: CSV
- **Path**: `data/processed/eeg/{subject_id}_eeg.csv`
- **Columns**: `time`, `channel_0`, `channel_1`,...

### Avalanche Records
- **Format**: CSV
- **Path**: `data/results/avalanche_events.csv`
- **Columns**: `subject_id`, `start_time`, `end_time`, `size`, `duration`, `exponent`

## Validation Rules

- **Connectome**: Must be symmetric (undirected graph) and non-negative weights.
- **EEG**: Must have consistent time steps across all channels.
- **Avalanche**: `start_time` < `end_time`, `size` > 0, `duration` > 0.
- **Participant**: `subject_id` must be unique and match across all data files.

## Integration Points

| Stage | Input Entity | Output Entity |
|-------|--------------|---------------|
| Download | - | Raw dMRI files |
| Preprocess | Raw dMRI | `StructuralConnectome` |
| Simulate | `StructuralConnectome` | Simulated EEG |
| QC | `StructuralConnectome`, EEG | `Participant` (with `qc_passed`) |
| Avalanches | Simulated EEG | `AvalancheRecord` |
| Metrics | `StructuralConnectome` | Network metrics (CSV) |
| Export | All | `correlation_report.csv` |

# Data Model Specification

This document defines the core data structures used throughout the `llmXive` pipeline. All data objects are defined in `code/data/models.py` using Python `dataclasses`.

## 1. Participant

Represents a single subject in the study cohort.

```python
@dataclass
class Participant:
 subject_id: str
 age: Optional[int] = None
 sex: Optional[str] = None
 # Links to processed data files
 connectome_path: Optional[Path] = None
 eeg_path: Optional[Path] = None
 qc_status: Optional[Dict] = None
```

### Attributes
- `subject_id`: Unique identifier (e.g., "sub-001").
- `age`: Age in years (optional).
- `sex`: Biological sex (optional).
- `connectome_path`: Path to the saved structural adjacency matrix (`.npy` or `.csv`).
- `eeg_path`: Path to the saved EEG time-series (`.fif` or `.csv`).
- `qc_status`: Dictionary containing quality control flags (e.g., `{"ica_channels_removed": 5, "graph_connected": True}`).

## 2. StructuralConnectome

Represents the structural connectivity matrix derived from dMRI tractography.

```python
@dataclass
class StructuralConnectome:
 subject_id: str
 matrix: np.ndarray
 parcel_scheme: str
 file_path: Path
 # Metadata
 num_nodes: int = field(init=False)
 density: Optional[float] = None
```

### Attributes
- `subject_id`: Link to the `Participant`.
- `matrix`: 2D NumPy array (N x N) representing connection strengths (weights).
- `parcel_scheme`: Name of the parcellation used (e.g., "HCP-MMP1.0").
- `file_path`: Absolute path to the stored file.
- `num_nodes`: Derived attribute (shape[0]).
- `density`: Proportion of non-zero edges.

### Methods
- `to_networkx()`: Converts the matrix to a NetworkX graph object for analysis.

## 3. AvalancheRecord

Represents a single detected neural avalanche event.

```python
@dataclass
class AvalancheRecord:
 subject_id: str
 start_time: float
 end_time: float
 size: int
 duration: float
 channels_involved: List[int]
 # Derived
 intensity: float = field(init=False)
```

### Attributes
- `subject_id`: Link to the `Participant`.
- `start_time`: Timestamp of avalanche onset (seconds).
- `end_time`: Timestamp of avalanche offset (seconds).
- `size`: Total number of active channels during the event.
- `duration`: `end_time - start_time` (seconds).
- `channels_involved`: List of channel indices that were active.
- `intensity`: `size / duration`.

## Data Flow & Storage

1. **Raw Data**: Stored in `data/raw/`.
2. **Processed Data**:
 - Structural matrices: `data/processed/connectomes/{subject_id}.npy`
 - EEG time-series: `data/processed/eeg/{subject_id}.csv`
 - QC Status: `data/processed/data_status.json`
3. **Results**:
 - Metrics: `data/results/metrics.csv`
 - Avalanche Fits: `data/results/fitting_results.json`
 - Correlation Report: `data/results/correlation_report.csv`

## Integrity & Validation

- **Checksums**: All processed files are tracked in `data/checksums.json` to ensure reproducibility.
- **QC Rules**:
 - Participants with >30% channels removed (ICA) are excluded.
 - Disconnected structural graphs are flagged or excluded.
 - Simulated signals must fall within physiological variance ranges.

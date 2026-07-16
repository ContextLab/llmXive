# Data Model Specification

## 1. Overview
This document defines the data structures used to represent participants, structural connectomes, and avalanche records within the `llmXive` pipeline for Project PROJ-472.

## 2. Core Entities

### 2.1 Participant
Represents a single subject in the study.
```python
@dataclass
class Participant:
 subject_id: str
 age: Optional[int] = None
 sex: Optional[str] = None
 qc_status: str = "pending" # 'passed', 'failed'
 data_root: Optional[Path] = None
```

### 2.2 StructuralConnectome
Represents the weighted adjacency matrix derived from dMRI.
```python
@dataclass
class StructuralConnectome:
 participant_id: str
 matrix: np.ndarray # Shape: (N_regions, N_regions)
 regions: List[str]
 method: str = "HCP-MMP1.0"
 path: Optional[Path] = None
```

### 2.3 AvalancheRecord
Represents a single detected neural avalanche event.
```python
@dataclass
class AvalancheRecord:
 participant_id: str
 start_time: float
 duration: float # In time bins
 size: int # Number of active channels/events
 channels_involved: List[int]
 amplitude: float
```

## 3. Derived Metrics
- **Structural Metrics**: Degree, Clustering, Rich-Club (stored in `data/processed/metrics.csv`).
- **Avalanche Metrics**: Power-law exponent (alpha), goodness-of-fit (p-value), size distribution (stored in `data/processed/avalanche_metrics.csv`).

## 4. Storage Format
- **Raw Data**: BIDS format in `data/raw/`.
- **Processed Data**: CSV and NumPy `.npy` files in `data/processed/`.
- **Results**: Aggregated CSVs and JSON reports in `data/results/`.

## 5. Integrity Constraints
- All files must have valid SHA-256 checksums recorded in `data/raw/checksums.json`.
- Participants with `qc_status == 'failed'` must be excluded from downstream analysis.

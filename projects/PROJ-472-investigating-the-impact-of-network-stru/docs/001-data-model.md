# Data Model Specification

## Overview
This document describes the core data entities used in the llmXive automated science pipeline for investigating network structure impact on neural avalanche dynamics.

## Core Entities

### Participant
Represents a single subject in the study.

```python
@dataclass
class Participant:
 participant_id: str
 age: Optional[int] = None
 sex: Optional[str] = None
 # Metadata for data provenance
 data_source: Optional[str] = None # 'real' or 'simulated'
 qc_status: Optional[str] = None # 'passed', 'failed', 'pending'
```

**Usage**:
- Instantiated during data loading (real or simulated)
- Used as primary key for all downstream data associations
- QC status updated after quality control checks (T012)

### StructuralConnectome
Represents the structural connectivity matrix derived from dMRI tractography.

```python
@dataclass
class StructuralConnectome:
 participant_id: str
 matrix: np.ndarray # Shape: (N_parcels, N_parcels)
 parcel_scheme: str # e.g., "HCP-MMP1.0"
 file_path: Path # Path to stored.npy or.csv
 checksum: str # SHA-256 of the matrix file
```

**Processing Pipeline**:
1. Raw tractography (`.tck`) downloaded (T009)
2. Converted to adjacency matrix via MRtrix3 `tck2connectome` (T010)
3. Stored in `data/processed/connectomes/` (T013)

**Constraints**:
- Matrix must be symmetric
- Diagonal elements must be zero
- Values represent streamline counts or weighted connectivity

### AvalancheRecord
Represents a single neural avalanche event detected in EEG data.

```python
@dataclass
class AvalancheRecord:
 participant_id: str
 start_time: float # Seconds from recording start
 end_time: float
 channels_involved: List[str]
 size: int # Number of active channels
 duration: float # Seconds
 amplitude_max: float # Peak z-score amplitude
```

**Detection Logic**:
- Input: Z-score normalized EEG time series
- Threshold: 75th percentile of global amplitude distribution
- Contiguity: Spatially and temporally connected active channels
- Output: List of `AvalancheRecord` per participant

## Data Flow

1. **Raw Data**: `data/raw/` (dMRI `.tck`, EEG `.edf`/`.bdf`)
2. **Processed Data**: `data/processed/` (connectome matrices, cleaned EEG, avalanche records)
3. **Results**: `data/results/` (metrics, correlations, reports)

## Storage Format

- **Connectomes**: NumPy `.npy` files with metadata JSON sidecar
- **EEG Time Series**: Pandas HDF5 or `.feather` format
- **Avalanche Records**: JSON Lines (`.jsonl`) or Parquet
- **Metrics**: CSV with participant-level aggregates

## Versioning

Data artifacts are versioned via checksums stored in `data/checksums.json`.
Any modification to raw data triggers re-processing of dependent artifacts.

# Data Model: The Impact of Network Efficiency on Age-Related Changes in Resting-State EEG

## 1. Raw Data Schema

**Source**: TUH EEG Corpus (PhysioNet)
**Format**: EDF (European Data Format)
**Key Fields**:
- `subject_id`: Unique identifier (anonymized).
- `age`: Integer (years).
- `sex`: String (M/F).
- `cognitive_score`: Float (MMSE or MoCA, if available).
- `cognitive_instrument`: String (e.g., "MMSE", "MoCA").
- `file_path`: Path to local EDF.

## 2. Processed Data Schema

### A. Epochs (Intermediate)
**File**: `data/processed/epochs/{subject_id}.fif`
**Format**: MNE Epochs (HDF5-based)
**Attributes**:
- `info`: Channel info, montage (10-20).
- `events`: Time points of Time segments of a fixed duration.
- `data`: Shape (n_epochs, n_channels, n_times).

### B. Connectivity Matrices (Intermediate)
**File**: `data/processed/connectivity/{subject_id}_{band}.npy`
**Format**: NumPy Array (float64)
**Shape**: `(n_channels, n_channels)`
**Content**: Coherence values (The normalized parameter will range from a baseline minimum to a maximum limit.) between channel pairs **per frequency band**.

## 3. Results Schema

### A. Network Metrics (Primary Output)
**File**: `data/results/network_metrics.csv`
**Columns**:
1. `subject_id`: String (Anonymized ID).
2. `age`: Integer.
3. `sex`: String.
4. `cognitive_score`: Float (or `NaN` if missing).
5. `cognitive_instrument`: String (or `NaN`).
6. `global_efficiency`: Float (Harmonic mean of inverse shortest paths).
7. `local_efficiency`: Float (Average of local efficiencies of each node).
8. `path_length`: Float (Characteristic path length).
9. `clustering_coeff`: Float.
10. `modularity`: Float.
11. `trace_id`: String (SHA-256 hash of the run artifact).
12. `snr_flag`: Boolean (True if SNR < 10dB).
13. `frequency_band`: String (Alpha, Beta, Theta).

### B. Correlation Results
**File**: `data/results/correlation_results.csv`
**Columns**:
1. `metric_name`: String (e.g., "global_efficiency").
2. `outcome`: String ("age" or "cognitive_score").
3. `correlation_r`: Float.
4. `p_value`: Float.
5. `p_adjusted`: Float (FDR/Bonferroni corrected).
6. `method`: String ("Spearman" or "Partial").
7. `n_samples`: Integer.
8. `trace_id`: String.

### C. Exclusion Log (New)
**File**: `data/quality/exclusion_log.csv`
**Columns**:
1. `subject_id`: String.
2. `exclusion_reason`: String (e.g., "Invalid_Instrument", "Missing_Cognitive_Score").

## 4. Quality Control Schema

### A. Download Report
**File**: `data/quality/download_report.json`
**Structure**:
```json
{
  "total_downloaded": 1234,
  "adults_filtered": 1100,
  "with_cognitive_score": 450,
  "invalid_instruments": 12,
  "mdes_r": 0.25,
  "checksums": {
    "subject_001": "sha256_hash...",
    ...
  }
}
```

### B. Efficiency Check
**File**: `data/results/efficiency_check.json`
**Structure**:
```json
{
  "formula_verification": {
    "global_efficiency_check": "PASS",
    "local_efficiency_check": "PASS",
    "unit_test_graph_id": "synthetic_ring_6"
  },
  "timestamp": "2026-07-08T12:00:00Z"
}
```

## 5. Data Flow Diagram (Conceptual)

```mermaid
graph TD
    A[Raw EDF] -->|Download & Filter| B(Adults + Valid Metadata)
    B -->|Preprocess (ICA, Filter)| C[Cleaned Continuous]
    C -->|Epoch 10s| D[Epochs Object]
    D -->|Coherence per Band| E[Adjacency Matrix]
    E -->|Graph Metrics| F[Network Metrics CSV]
    F -->|Regression + FDR| G[Correlation Results CSV]
    G -->|Trace ID Inject| H[Final Results]
```
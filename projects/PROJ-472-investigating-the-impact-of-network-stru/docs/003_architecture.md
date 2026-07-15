# System Architecture

## High-Level Design

The system follows a modular, pipeline-based architecture designed for reproducibility and strict separation of concerns.

```
[Raw Data] -> [Ingestion & Preprocessing] -> [Processed Store] -> [Analysis] -> [Reporting]
```

## Module Responsibilities

### 1. Infrastructure (`code/utils/`, `code/config.py`)
- **`config.py`**: Centralized configuration (paths, seeds, Wilson-Cowan params).
- **`logger.py`**: Logging infrastructure and custom exception hierarchy.
- **`env_config.py`**: Environment variable management (`.env` loading).
- **`data_setup.py`**: Directory creation and checksum tracking.

### 2. Data Layer (`code/data/`)
- **`models.py`**: Dataclasses (`Participant`, `StructuralConnectome`, `AvalancheRecord`).
- **`download.py`**: Fetching real data from OpenNeuro (with fallback chain).
- **`preprocess_dMRI.py`**: Tractography -> Adjacency Matrix conversion.
- **`simulate_EEG.py`**: Wilson-Cowan simulation of neural activity.
- **`store.py`**: Unified interface for saving/loading processed artifacts.
- **`quality_control.py`**: QC checks (SNR, graph connectivity).

### 3. Analysis Layer (`code/analysis/`)
- **`metrics.py`**: Network topology metrics (Degree, Clustering, Rich-Club).
- **`avalanches.py`**: Spatiotemporal event detection.
- **`fitting.py`**: Power-law model fitting and comparison.
- **`stats.py`**: Correlation analysis, permutation tests, VIF diagnostics.
- **`sensitivity.py`**: Threshold sensitivity sweeps.
- **`report.py`**: Report generation and associational framing validation.

### 4. Orchestration (`code/main.py`)
- Parses arguments.
- Executes the pipeline stages in order.
- Handles the "Null Result Protocol" if N < 10.

## Data Flow Diagram

1. **Ingestion**:
 - `download.py` attempts `ds004230` -> `ds004503` -> Fail.
 - `preprocess_dMRI.py` converts `.tck` -> `.npy`.
 - `simulate_EEG.py` generates `.csv` (if real EEG missing).
2. **Storage**:
 - `store.py` saves matrices and time-series to `data/processed/`.
 - `simulation_metadata.json` is updated with seeds/params (T030).
3. **Computation**:
 - `metrics.py` reads `.npy` -> computes stats.
 - `avalanches.py` reads `.csv` -> detects events.
 - `fitting.py` fits power-laws to avalanche sizes.
4. **Association**:
 - `stats.py` correlates structural metrics with avalanche exponents.
 - `sensitivity.py` sweeps thresholds.
5. **Reporting**:
 - `report.py` generates final CSV/MD, validates framing.

## Concurrency & Parallelism

- **Parallel Tasks**: Tasks marked `[P]` in `tasks.md` can run independently.
 - Example: `metrics.py` and `avalanches.py` can run in parallel once data is stored.
- **Permutation Tests**: `stats.py` uses multiprocessing for the permutation loop (T027).

## Dependencies

- **Python**: 3.11+
- **Core**: `numpy`, `pandas`, `scipy`, `networkx`, `bctpy`, `mne`, `powerlaw`.
- **Utils**: `python-dotenv`, `tqdm`, `matplotlib`.

## Error Handling Strategy

- **Fail Loudly**: Data loaders raise `DataLoadError` if real data is missing; no synthetic fallback.
- **Graceful Degradation**: If a specific subject fails QC, it is excluded, and the pipeline continues.
- **Null Result Protocol**: If N < 10, the pipeline halts correlation analysis and generates a `null_result_report.md`.

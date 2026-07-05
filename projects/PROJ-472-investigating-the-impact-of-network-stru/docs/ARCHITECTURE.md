# System Architecture

## High-Level Design

The llmXive pipeline is designed as a sequence of independent, testable stages. Each stage corresponds to a User Story (US) and produces artifacts that feed into the next.

```
[Setup] -> [Foundational] -> [US1: Data Pipeline] -> [US2: Metrics] -> [US3: Stats]
```

## Module Structure

```
code/
├── config.py # Global configuration and hyperparameters
├── data/
│ ├── models.py # Data classes (Participant, Connectome, Avalanche)
│ ├── download.py # OpenNeuro data fetching
│ ├── preprocess_dMRI.py # Tractography to connectome conversion
│ ├── simulate_EEG.py # Wilson-Cowan EEG simulation
│ ├── quality_control.py # QC checks and reporting
│ └── store.py # Unified data storage/loading
├── analysis/
│ ├── metrics.py # NetworkX/BCTpy metrics
│ ├── avalanches.py # Avalanche detection logic
│ ├── fitting.py # Power-law model fitting
│ ├── stats.py # Correlations and permutation tests
│ ├── sensitivity.py # Threshold sweeps
│ ├── export_metrics.py # CSV export logic
│ └── report.py # Final report generation
├── utils/
│ ├── logger.py # Structured logging
│ ├── env_config.py #.env loading
│ └── data_setup.py # Checksum and directory management
└── main.py # Orchestration entry point
```

## Data Flow Diagram

1. **Raw Data**: OpenNeuro ds003813 (dMRI) -> `data/raw/`
2. **Processed Connectomes**: `data/processed/connectomes/` (Adjacency matrices)
3. **Simulated EEG**: `data/processed/eeg/` (Time-series)
4. **QC Reports**: `data/processed/qc/`
5. **Metrics**: `data/results/network_metrics.csv`
6. **Avalanches**: `data/results/avalanche_events.csv`
7. **Final Stats**: `data/results/correlation_report.csv`

## Dependency Management

Dependencies are pinned in `code/requirements.txt`. Key libraries:
- `mne`: EEG processing and simulation support.
- `networkx`, `bctpy`: Graph analysis.
- `powerlaw`: Statistical fitting.
- `pandas`, `numpy`: Data manipulation.
- `python-dotenv`: Environment configuration.

## Error Handling Strategy

- **Structured Logging**: All modules use `utils/logger.py` for consistent logging.
- **Fail Fast**: Critical errors (e.g., missing data) halt execution immediately.
- **QC Gates**: Data must pass QC (SNR, connectivity) before analysis proceeds.
- **Null Result Protocol**: If insufficient data remains after QC, the pipeline halts and generates a "Pipeline Validated" report.

## Scalability

- **Parallelism**: US1, US2, and US3 can run in parallel if data is pre-staged.
- **Multiprocessing**: Permutation tests in `stats.py` use `multiprocessing` to handle large N.
- **Memory**: Large matrices are processed in chunks where possible.

## Security & Privacy

- No PII is stored; only subject IDs and anonymous data.
- Environment variables (API keys) are loaded from `.env` and never committed.
- Data integrity verified via checksums in `utils/data_setup.py`.

## Future Extensibility

- **Real Data Integration**: Pipeline supports swapping simulated EEG for real recordings.
- **Additional Metrics**: `metrics.py` is designed for easy extension of new graph metrics.
- **Visualization**: `report.py` can be extended to generate interactive plots.

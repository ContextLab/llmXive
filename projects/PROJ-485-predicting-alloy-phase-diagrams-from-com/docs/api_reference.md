# API Reference

## `code/main.py`
The central orchestrator for the pipeline.

### Functions
- `run_pipeline()`: Executes the full workflow from ingestion to visualization.
- `run_data_ingestion()`: Loads raw data and generates checksums.
- `run_feature_generation()`: Computes compositional descriptors.
- `run_model_training()`: Trains the model and performs LOSO CV.
- `run_visualization()`: Generates plots and fidelity reports.
- `run_compliance_check()`: Validates state and artifact integrity.

## `code/ingest/load_data.py`
Handles data loading with streaming and validation.

### Functions
- `load_data()`: Main entry point for data loading.
- `stream_data()`: Streams large CSVs in chunks.
- `filter_missing_temperature()`: Excludes rows without temperature data.
- `update_state_with_checksum()`: Records SHA-256 hashes in state.

## `code/features/generate_descriptors.py`
Computes alloy descriptors.

### Functions
- `generate_descriptors()`: Calculates mean atomic radius, electronegativity variance, etc.
- `calculate_hume_rothery_concentration()`: Computes Hume-Rothery parameters.
- `validate_descriptors()`: Checks derived values against elemental properties.

## `code/models/train.py`
Model training and evaluation.

### Functions
- `run_training_pipeline()`: Orchestrates training, CV, and baseline comparison.
- `run_loso_cv()`: Performs Leave-One-System-Out cross-validation.
- `perform_power_analysis()`: Checks statistical power (target ≥ 0.8).
- `compare_with_baseline()`: Compares RF against null model (global mean).

## `code/viz/plot_phase_diagrams.py`
Visualization module.

### Functions
- `run_visualization()`: Generates phase diagrams for required systems.
- `calculate_mae()`: Computes Mean Absolute Error between predicted and experimental.
- `calculate_tcs()`: Computes Topological Consistency Score.
- `write_fidelity_report()`: Saves `fidelity_report.json`.

## `code/utils/`
Utility modules.

- `logging.py`: Structured JSON logging.
- `checksum.py`: SHA-256 file hashing.
- `error_codes.py`: Enum of error codes (e.g., `DATA_SOURCE_MISSING`, `INVALID_SCOPE`).
- `resource_monitor.py`: Tracks memory and execution time.

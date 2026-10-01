# PROJ-485: Predicting Alloy Phase Diagrams from Compositional Data

## Overview
This project implements an automated scientific pipeline to predict alloy phase diagrams using compositional data and machine learning. It ingests thermodynamic data from NIST-JANAF/SGTE sources (or verified local fallbacks), generates compositional descriptors, trains a Random Forest model with Leave-One-System-Out (LOSO) cross-validation, and visualizes the results against ground truth.

## Project Structure
```
.
├── code/ # Source code
│ ├── __init__.py
│ ├── main.py # Pipeline orchestrator
│ ├── ingest/ # Data ingestion
│ ├── features/ # Descriptor generation
│ ├── models/ # Model training & evaluation
│ ├── viz/ # Visualization
│ ├── utils/ # Utilities (logging, checksums, etc.)
│ └── config.yaml # Configuration
├── data/
│ ├── raw/ # Raw input data (e.g., elemental_properties.csv)
│ ├── processed/ # Processed descriptors
│ ├── artifacts/ # Model artifacts, plots, reports
│ └── logs/ # Pipeline logs
├── state/ # Pipeline state tracking
├── tests/ # Test suite
└── docs/ # Documentation
```

## Prerequisites
- Python 3.11+
- pip
- Required dependencies listed in `requirements.txt`

## Installation
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Ensure `code/config.yaml` is configured with valid data sources or local fallback paths.

## Running the Pipeline
Execute the main orchestrator:
```bash
python code/main.py
```

This runs the full pipeline:
1. **Data Ingestion**: Loads and validates raw data.
2. **Feature Generation**: Computes atomic radius, electronegativity, etc.
3. **Model Training**: Trains RF with LOSO CV, performs power analysis, and compares against null baseline.
4. **Visualization**: Generates phase diagram plots and fidelity reports.
5. **Compliance**: Verifies checksums and state management.

## Key Artifacts
- `data/processed/descriptors.csv`: Processed feature set.
- `data/artifacts/model.pkl`: Trained Random Forest model.
- `data/artifacts/baseline_comparison.json`: Model vs. null baseline metrics.
- `data/artifacts/fidelity_report.json`: Visual fidelity assessment (MAE, TCS).
- `data/artifacts/plots/*.png`: Phase diagram visualizations.
- `state/PROJ-485/state.yaml`: Pipeline execution state and artifact hashes.

## Configuration
Edit `code/config.yaml` to specify:
- `nist_janaf_url`: URL for NIST-JANAF data (if available).
- `sgte_url`: URL for SGTE data (if available).
- `local_fallback_path`: Path to a verified local CSV if external URLs are unavailable.
- `required_systems`: List of alloy systems to process (e.g., Cu-Zn, Al-Cu).

## Known Limitations
- **Data Availability**: The pipeline strictly requires real thermodynamic data. If external URLs are empty and no valid local fallback exists, the pipeline halts with `DATA_SOURCE_MISSING`.
- **Memory Constraints**: Large datasets are streamed. If memory usage exceeds 7GB, the pipeline halts with `RESOURCE_LIMIT_EXCEEDED`.
- **Extrapolation**: The model will not predict for elements outside the convex hull of the training set (FR-010).
- **Fidelity Threshold**: Visualizations for systems with MAE > 50K are marked as 'FAILED' but do not halt the pipeline.

## Testing
Run the test suite:
```bash
python -m pytest tests/ -v
```

## Compliance
This project adheres to the llmXive Constitution Principles:
- **Principle I**: Fail Loudly (no synthetic fallbacks).
- **Principle II**: Real Data Only (verified sources).
- **Principle III**: Data Integrity (SHA-256 checksums).
- **Principle V**: State Management (artifact tracking in `state/`).

## License
Proprietary / Internal Research Use.

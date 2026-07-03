# Quantifying the Influence of Network Topology on Thermal Conductivity in Amorphous Silicon

This project implements a research pipeline to investigate the relationship between the atomic network topology of amorphous silicon and its thermal conductivity. The pipeline ingests pre-equilibrated atomic configurations, constructs atomic graphs, extracts topological metrics, runs Green-Kubo simulations for ground-truth conductivity, trains a Graph Neural Network (GNN) on a topology-derived proxy, and performs statistical correlation analysis.

## Project Structure

```
.
├── code/ # Python source code
│ ├── config.py # Configuration management
│ ├── __init__.py # Logging infrastructure
│ ├── ingest/ # Data ingestion and graph construction
│ ├── simulation/ # Green-Kubo simulations and validation
│ ├── metrics/ # Topological metric extraction
│ ├── model/ # GNN training and feature importance
│ └── analysis/ # Statistical analysis (LMM, Pearson)
├── data/ # Data artifacts
│ ├── raw/ # Raw input data (XYZ files)
│ └── processed/ # Processed graphs, conductivities, model outputs
├── tests/ # Unit, integration, and contract tests
├── contracts/ # JSON schemas for data validation
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Prerequisites

- Python 3.11+
- pip
- LAMMPS (for Green-Kubo simulations, optional for analysis-only runs)

## Installation

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Pipeline Execution

The pipeline is designed to be run in stages. Ensure you have the necessary input data in `data/raw/` before starting.

### 1. Setup Directories (if not already done)
```bash
python code/setup_data_directories.py
python code/setup_test_directories.py
```

### 2. Data Ingestion & Graph Construction (User Story 1)
Loads XYZ files from `data/raw/`, builds atomic graphs with a 3.0 Å bond cutoff, and saves them to `data/processed/graphs/`.
```bash
python code/ingest/graph_builder.py
python code/ingest/sample_generator.py # If external data fetching is needed
python code/ingest/node_degree_stats_generator.py
```

### 3. Topological Metric Extraction & Simulation (User Story 2)
Computes topological metrics (degree, clustering, shortest-path) and runs Green-Kubo simulations (if LAMMPS is configured).
```bash
python code/metrics/topology_extractor.py
python code/simulation/green_kubo.py # Requires LAMMPS setup
python code/simulation/convergence_checker.py
python code/simulation/conductivity_validator.py
```

### 4. Model Training & Analysis (User Story 3)
Trains a GNN on a static scattering potential proxy, extracts feature importance, and performs statistical analysis.
```bash
python code/analysis/power_checker.py # Checks sample size N
python code/model/gnn.py
python code/model/trainer.py
python code/model/feature_importance.py
python code/analysis/lmm_analysis.py
python code/analysis/pearson_correlation.py
python code/analysis/correlation_significance.py
python code/analysis/final_results_aggregator.py
```

## Configuration

All configuration is managed via `code/config.py` and `code/simulation/config.yaml`. Key parameters include:
- Bond cutoff distance (default: 3.0 Å)
- Random seeds
- GNN hyperparameters
- Conductivity validation ranges
- Outlier exclusion flags

## Output Artifacts

- `data/processed/graphs/`: Serialized atomic graphs and node-degree statistics.
- `data/processed/conductivities/`: Thermal conductivity data and convergence reports.
- `data/processed/model_outputs/`: GNN weights, feature importance, correlation results (Pearson, LMM), and final aggregated analysis.
- `data/checksums.json`: Integrity checksums for all processed data.

## Testing

Run the test suite:
```bash
pytest tests/
```

Contract tests validate data schemas in `contracts/`.
```bash
pytest tests/contract/
```

## Notes

- **Sample Size**: The pipeline expects N ≥ 10 samples for statistical power (per spec). If N < 10, a warning is logged, but the pipeline proceeds with the available data (N ≥ 2) for proof-of-concept.
- **Green-Kubo**: Requires a valid LAMMPS installation and the Stillinger-Weber (SW) potential file.
- **Data Integrity**: All processed data includes checksums. Verify integrity using `data/checksums.json`.

## License

[Insert License Information Here]
# Quantifying the Influence of Network Topology on Thermal Conductivity in Amorphous Silicon

## Project Overview

This project investigates the relationship between local atomic network topology (connectivity) and macroscopic thermal conductivity in amorphous silicon (a-Si). By constructing atomic graphs from equilibrated configurations, extracting topological metrics (degree, clustering, shortest paths), and correlating these with thermal conductivity values derived from Green-Kubo simulations, we aim to quantify how structural motifs influence heat transport.

The pipeline is modular, consisting of distinct stages for data ingestion, graph construction, topological metric extraction, thermal conductivity simulation, machine learning (GNN) training, and statistical analysis (Pearson correlation and Linear Mixed-Effects Models).

## Prerequisites

- Python 3.11+
- LAMMPS (installed and accessible via `mpirun`)
- Required Python packages listed in `requirements.txt`

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

## Configuration

All configuration parameters (paths, seeds, hyperparameters, simulation settings) are managed via `code/config.py` and `code/simulation/config.yaml`. Ensure these files are updated with your local paths and specific experimental parameters before running the pipeline.

## Pipeline Execution

The pipeline is designed to run sequentially through the following stages. Each stage produces artifacts in the `data/` directory.

### 1. Data Ingestion & Graph Construction (User Story 1)

Ingests XYZ files of pre-equilibrated a-Si configurations and constructs atomic graphs using a bond cutoff distance (default: 3.0 Å).

```bash
python -m code.ingest.sample_generator
python -m code.ingest.graph_builder
python -m code.ingest.node_degree_stats_generator
```

**Outputs:**
- `data/processed/graphs/`: Serialized atomic graphs (pickle).
- `data/processed/graphs/node_degree_stats.json`: Global degree distribution statistics.
- `data/processed/graphs/excluded_samples.json`: List of samples excluded due to topological defects.

### 2. Topological Metric Extraction & Green-Kubo Simulation (User Story 2)

Computes topological metrics for each graph and runs LAMMPS Green-Kubo simulations to determine ground-truth thermal conductivity.

```bash
python -m code.metrics.topology_extractor
python -m code.simulation.green_kubo
python -m code.simulation.convergence_checker
python -m code.simulation.thermal_sample_saver
```

**Outputs:**
- `data/processed/conductivities/`: Serialized `ThermalSample` objects containing conductivity values and metadata.
- `data/processed/conductivities/convergence_status.json`: Convergence status for each sample.
- `data/processed/conductivities/convergence_report.json`: Validation of conductivity ranges.

### 3. GNN Training & Statistical Analysis (User Story 3)

Trains a Graph Neural Network to predict local heat flux, extracts feature importance via SHAP, and performs correlation analysis.

```bash
python -m code.analysis.power_checker
python -m code.model.trainer
python -m code.model.feature_importance
python -m code.analysis.pearson_correlation
python -m code.analysis.correlation_significance
python -m code.analysis.lmm_analysis
python -m code.analysis.final_results_aggregator
```

**Outputs:**
- `data/processed/model_outputs/shap_values.npy`: Feature importance values.
- `data/processed/model_outputs/correlation_pearson.json`: Raw Pearson correlation results.
- `data/processed/model_outputs/correlation_pearson_corrected.json`: Bonferroni-corrected results.
- `data/processed/model_outputs/lmm_results.json`: Linear Mixed-Effects model coefficients.
- `data/processed/model_outputs/final_results.json`: Aggregated findings.

### 4. Verification & Validation

Verify data integrity and pipeline execution.

```bash
# Verify checksums
python -m code.analysis.checksum_verifier

# Validate quickstart steps
python -m code.validation.quickstart_validator
```

## Testing

Run the full test suite to ensure correctness:

```bash
pytest tests/ -v
```

- **Contract Tests:** `tests/contract/` - Validates data schemas.
- **Unit Tests:** `tests/unit/` - Tests individual components.
- **Integration Tests:** `tests/integration/` - Tests end-to-end pipeline stages.

## Data Integrity

This project strictly adheres to real-data requirements. No synthetic data is generated for inputs. All data must be sourced from real simulations or verified datasets. If a real data source is unavailable, the pipeline halts with a clear error.

## License

[Insert License Information]

## Contact

[Insert Contact Information]
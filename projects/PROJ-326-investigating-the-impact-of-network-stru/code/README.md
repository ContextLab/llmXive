# Network Topology Energy Transfer Research

Automated science pipeline for investigating the impact of network structure on energy transfer in spin systems.

## Installation

This project requires Python 3.9 or higher. Follow these steps to set up your environment:

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-326-investigating-the-impact-of-network-stru
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 ```

3. **Activate the virtual environment**:
 - On Linux/macOS:
 ```bash
 source venv/bin/activate
 ```
 - On Windows (Command Prompt):
 ```cmd
 venv\Scripts\activate
 ```
 - On Windows (PowerShell):
 ```powershell
 venv\Scripts\Activate.ps1
 ```

4. **Install project dependencies**:
 Navigate to the `code/` directory and install the required packages:
 ```bash
 cd code
 pip install -r requirements.txt
 ```
 *Note: This installs `networkx`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `pandas`, `pytest`, `ruff`, `black`, `pyyaml`, `scikit-learn`, and `statsmodels`.*

5. **Install pre-commit hooks** (Optional but recommended):
 ```bash
 pre-commit install
 ```

6. **Verify installation**:
 Run the test suite to ensure all dependencies are correctly installed:
 ```bash
 pytest tests/
 ```

## Configuration

The project uses a global configuration file located at `code/config.yaml`. Before running any simulations or analysis, review and edit this file to set:

- **Global seeds**: For reproducible random number generation.
- **Topology targets**: Parameters for Erdős-Rényi, Watts-Strogatz, and Barabási-Albert graph generation.
- **Simulation parameters**: Ising model settings (temperature, coupling constants, time steps).
- **Output paths**: Directories for raw data, analysis results, and figures.

### Configuration File Structure (`config.yaml`)

The `config.yaml` file is a YAML-formatted document that controls the behavior of the entire pipeline. It is loaded by `code/src/utils/config.py` and validated against a schema.

#### Global Settings

- `global_seed`: (int) The base seed for all random number generators. If set, all downstream processes (graph generation, simulation, analysis) will derive their seeds from this value to ensure reproducibility.
- `output_paths`:
 - `raw_data`: (string) Directory for generated graph data (default: `data/raw/`).
 - `analysis_results`: (string) Directory for simulation and statistical results (default: `data/analysis/`).
 - `figures`: (string) Directory for generated plots (default: `figures/`).
 - `metadata`: (string) Directory for graph metadata (default: `data/metadata/`).

#### Topology Generation Settings

- `topology_targets`:
 - `erdos_renyi`:
 - `n_nodes`: (int) Number of nodes in the graph.
 - `edge_probability`: (float) Probability of edge creation ($p$).
 - `batch_size`: (int) Number of graphs to generate in a batch.
 - `watts_strogatz`:
 - `n_nodes`: (int) Number of nodes.
 - `k_neighbors`: (int) Each node is connected to $k$ nearest neighbors.
 - `rewiring_probability`: (float) Probability of rewiring an edge ($\beta$).
 - `target_clustering`: (float) Target clustering coefficient (used for retry logic).
 - `batch_size`: (int) Number of graphs to generate.
 - `barabasi_albert`:
 - `n_nodes`: (int) Number of nodes.
 - `m_edges`: (int) Number of edges to attach from a new node to existing nodes.
 - `batch_size`: (int) Number of graphs to generate.

#### Simulation Settings

- `simulation_params`:
 - `temperature`: (float) Temperature $T$ for the Ising model.
 - `coupling_constant`: (float) Spin-spin coupling constant $J$.
 - `time_steps`: (int) Number of simulation steps to run.
 - `initial_state`: (string) Method for initializing spins (`random`, `all_up`, `all_down`).
 - `divergence_threshold`: (float) Threshold for detecting numerical instability.

#### Analysis Settings

- `analysis_params`:
 - `regression`:
 - `model_type`: (string) Type of regression to fit (`linear`, `polynomial`, `robust`).
 - `polynomial_degree`: (int) Degree for polynomial regression (if applicable).
 - `anova`:
 - `correction_method`: (string) Multiple comparison correction method (`bonferroni`, `bh`, `none`).
 - `sensitivity`:
 - `clustering_thresholds`: (list of float) List of clustering coefficients to test.

### Example `config.yaml`

```yaml
global_seed: 42

output_paths:
 raw_data: data/raw/
 analysis_results: data/analysis/
 figures: figures/
 metadata: data/metadata/

topology_targets:
 erdos_renyi:
 n_nodes: 100
 edge_probability: 0.05
 batch_size: 20
 watts_strogatz:
 n_nodes: 100
 k_neighbors: 4
 rewiring_probability: 0.1
 target_clustering: 0.6
 batch_size: 20
 barabasi_albert:
 n_nodes: 100
 m_edges: 3
 batch_size: 20

simulation_params:
 temperature: 2.0
 coupling_constant: 1.0
 time_steps: 100
 initial_state: random
 divergence_threshold: 1e6

analysis_params:
 regression:
 model_type: linear
 polynomial_degree: 2
 anova:
 correction_method: bonferroni
 sensitivity:
 clustering_thresholds: [0.1, 0.3, 0.5, 0.7, 0.9]
```

### Modifying Configuration

- **Reproducibility**: To reproduce a specific run, set `global_seed` to the value recorded in `data/run_log.json` for that run.
- **Scaling**: Increase `batch_size` in `topology_targets` to generate larger datasets. Ensure `data/` directory has sufficient disk space.
- **Simulation Stability**: If simulations diverge, lower `temperature` or reduce `time_steps`. Adjust `divergence_threshold` if false positives occur.
- **Analysis Sensitivity**: Modify `clustering_thresholds` in `analysis_params` to explore different regimes of network clustering.

## Usage

All commands below should be executed from the `code/` directory unless otherwise noted.

### Generate Synthetic Networks
Generate batches of connected graphs with controlled topological properties:
```bash
python src/generators/batch_runner.py --config config.yaml
```
This script outputs graph data to `data/raw/` and metadata to `data/metadata/`.

### Aggregate Batches
Combine generated batches into a global dataset:
```bash
python src/generators/aggregate_batch.py --config config.yaml
```

### Run Simulations
Execute the simplified Ising spin-flip dynamics on generated networks:
```bash
python src/simulation/run_simulation.py --config config.yaml
```
Simulation results (diffusion rates, energy profiles) are saved to `data/analysis/simulation_results.json`.

### Run Analysis
Perform statistical analysis, regression, ANOVA, and generate figures:
```bash
python src/analysis/run_analysis.py --config config.yaml
```
This pipeline generates:
- `data/analysis/final_results.json`: Aggregated statistical findings.
- `data/analysis/power_analysis_report.json`: Statistical power validation.
- `figures/`: High-resolution plots (scatter, heatmaps, boxplots).

### Validate Results
Run the batch validation script to ensure data integrity and thresholds:
```bash
python scripts/validate_batch.py
```

### Utility Scripts
- **Inject Seed**: Manually inject a specific random seed into the run log for reproducibility testing:
 ```bash
 python scripts/inject_seed.py --seed 42
 ```
- **Test Logging**: Verify the logging infrastructure is working correctly:
 ```bash
 python scripts/test_logging_demo.py
 ```

### Setup Directories
Initialize the project directory structure if not already present:
```bash
python setup_directories.py
```

## Code Quality

Maintain code standards using the following commands (run from `code/`):

- **Format code**:
 ```bash
 black src/ tests/
 ```
- **Lint code**:
 ```bash
 ruff check src/ tests/
 flake8 src/ tests/
 ```
- **Run tests**:
 ```bash
 pytest tests/ -v --cov=src
 ```

## Project Structure

```
code/
├── src/
│ ├── generators/ # Network generation algorithms (ER, SW, BA)
│ ├── simulation/ # Spin dynamics simulation and metrics
│ ├── analysis/ # Statistical analysis, plotting, reporting
│ └── utils/ # Logging, I/O, configuration, reproducibility
├── tests/ # Unit and integration tests
├── scripts/ # Helper scripts (seed injection, validation)
├── config.yaml # Global configuration
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Reproducibility

To ensure reproducibility:
- All random seeds are logged in `data/run_log.json` upon execution.
- Use the `scripts/inject_seed.py` utility to inject specific seeds into the log for reruns.
- Verify reproducibility by running `python src/utils/reproducibility.py --verify`.

## License

Research code - see LICENSE file for details.
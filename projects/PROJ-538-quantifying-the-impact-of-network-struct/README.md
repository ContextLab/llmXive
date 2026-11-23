# Quantifying the Impact of Network Structure on Heat Transport in Disordered Alloys

## Project Overview

This project investigates the relationship between atomic-scale network topology and thermal conductivity in disordered alloys, specifically focusing on Cu-Ni and Au-Ag systems. By constructing defect networks from molecular dynamics (MD) snapshots and correlating topological metrics with thermal conductivity, we aim to quantify how network structure influences heat transport.

## Key Features

- **Data Ingestion**: Supports both real data from OpenKim/Materials Cloud APIs and synthetic data generation using Lennard-Jones potentials.
- **Defect Network Construction**: Builds graph representations where nodes are atomic sites and edges connect nearest-neighbor atoms of mismatched species using Voronoi tessellation.
- **Topological Metric Extraction**: Computes clustering coefficients, mean degree, degree distribution moments, and percolation thresholds.
- **Statistical Correlation**: Performs Pearson and Spearman correlation analysis with Bonferroni correction, post-hoc power analysis, and sensitivity analysis.
- **Visualization**: Generates scatter plots with regression lines and correlation heatmaps at 300 DPI.

## Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager

### Setup

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Project Structure

```
.
├── code/ # Core implementation modules
│ ├── config.py # Configuration management
│ ├── ingest.py # Data ingestion and graph construction
│ ├── synthetic.py # Synthetic data generation
│ ├── metrics.py # Topological metric calculation
│ ├── stats.py # Statistical analysis
│ ├── viz.py # Visualization engine
│ ├── models.py # Pydantic data models
│ ├── utils.py # Utility functions and error handling
│ ├── interfaces.py # Abstract interfaces
│ ├── main.py # Pipeline orchestrator
│ └──... # Other utility scripts
├── data/ # Data storage
│ ├── raw/ # Raw input data
│ ├── processed/ # Processed data and results
│ └── contracts/ # JSON Schema contracts
├── tests/ # Test suite
│ └── unit/ # Unit tests
├── docs/ # Documentation
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Usage

### Running the Pipeline

The main pipeline can be executed via `code/main.py`:

```bash
python -m code.main
```

This will:
1. Perform a data audit to check for real data availability
2. Ingest data (real or synthetic)
3. Construct defect networks
4. Extract topological metrics
5. Perform statistical correlation analysis
6. Generate visualizations
7. Output results to `data/processed/`

### Configuration

Configuration is managed through `code/config.py`. Key settings include:
- `RunMode`: Select between `REAL` and `SYNTHETIC` data modes
- Data paths and output directories
- Logging verbosity

### Synthetic Data Generation

If real data is unavailable, the pipeline automatically switches to synthetic mode, generating statistically independent snapshots using Lennard-Jones potentials:
- Cu-Ni: epsilon=0.104 eV, sigma=2.56 Å
- Au-Ag: epsilon=0.103 eV, sigma=2.89 Å
- N=50 snapshots with unique random seeds (0-49)

## Output Files

The pipeline generates several output files in `data/processed/`:
- `raw_snapshots.parquet`: Ingested atomic snapshots
- `defect_graphs.json`: Constructed defect networks
- `metrics.json`: Topological metrics for each graph
- `correlation_results.json`: Correlation analysis results
- `power_analysis_report.json`: Post-hoc power analysis
- `sensitivity_report.csv`: Sensitivity analysis results
- `correlation_heatmap.png`: Correlation heatmap visualization
- `scatter_plots/`: Individual scatter plots for each metric

## Testing

Run the test suite with pytest:

```bash
pytest tests/ -v --cov=code
```

## Error Handling

The system implements robust error handling for:
- `DataAvailabilityError`: Raised when real data cannot be fetched
- `VoronoiFailure`: Raised when Voronoi tessellation fails

These errors are logged to `data/audit_log.json` with specific error codes.

## Dependencies

See `requirements.txt` for the complete list of dependencies, including:
- `pandas`, `numpy`, `scipy`: Data processing and scientific computing
- `networkx`: Graph construction and analysis
- `scikit-learn`, `statsmodels`: Statistical analysis
- `matplotlib`, `seaborn`: Visualization
- `pydantic`: Data validation
- `ase`, `phonopy`: Materials simulation
- `pymatgen`: Materials analysis

## License

[Insert license information here]

## Contributing

[Insert contributing guidelines here]

## Acknowledgments

This research is part of the llmXive automated science pipeline initiative.

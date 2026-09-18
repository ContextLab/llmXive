# Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns

## Project Overview

This project investigates the relationship between structural brain network topology (derived from diffusion MRI) and dynamic functional brain activity patterns (derived from fMRI). The study employs a rigorous Leave-One-Out (LOO) K-Means clustering approach to ensure statistical independence between structural and functional metric calculations.

## Research Question

Do topological properties of structural brain networks derived from diffusion MRI predict the prevalence, stability, and switching speed of recurrent activity patterns in spontaneous brain activity?

## Key Features

- **Structural Graph Metrics**: Computation of global efficiency, average clustering coefficient, and modularity from dMRI tractography data.
- **Dynamic Functional Metrics**: Extraction of dwell times and state visitation frequencies using sliding-window correlations and LOO K-Means clustering.
- **Statistical Analysis**: Correlation analysis between structural and dynamic metrics with Benjamini-Hochberg FDR correction.
- **Robustness Checks**: Sensitivity analysis for window length and density threshold variations.
- **Associational Framing**: All reports explicitly frame findings as associational rather than causal.

## Project Structure

```
PROJ-128-investigating-the-influence-of-network-t/
├── code/
│ ├── preprocess/
│ │ ├── __init__.py
│ │ ├── loader.py # HCP data loading utilities
│ │ ├── structural.py # Graph metric calculation
│ │ └── functional.py # Sliding-window & state extraction
│ ├── analysis/
│ │ ├── correlation.py # Statistical testing & FDR correction
│ │ └── robustness.py # Sensitivity analysis
│ ├── reports/
│ │ ├── generate_report.py # Final report generation
│ │ ├── audit_associational_language.py
│ │ └── validate_report.py
│ ├── config.py # Configuration parameters
│ ├── main.py # Main pipeline orchestrator
│ └── utils/
│ └── cpu_optimization.py
├── data/
│ ├── raw/ # Raw HCP data (downloaded)
│ ├── processed/ # Intermediate & final metrics
│ └── logs/ # Exclusion & runtime logs
├── contracts/
│ ├── dataset.schema.yaml # Input data schema
│ └── output.schema.yaml # Output data schema
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── docs/
│ └── README.md # This documentation
├── requirements.txt # Python dependencies
├── pyproject.toml # Tool configuration
└── README.md # Root README
```

## Prerequisites

- Python 3.9+
- CPU-only execution environment (no GPU required)
- ~14 GB disk space for data processing
- ~7 GB RAM for processing

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-128-investigating-the-influence-of-network-t
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

## Data Source

This project uses the **Human Connectome Project (HCP)** data available via OpenNeuro. The pipeline automatically downloads the required dMRI and fMRI data for the specified cohort.

- **Source**: OpenNeuro (HCP 1200 Subjects Release)
- **Data Types**: dMRI (tractography), fMRI (resting-state)
- **Access**: Publicly available, no authentication required

## Usage

### Quick Start

Run the full pipeline:

```bash
python code/main.py
```

This will:
1. Download HCP data (if not already present)
2. Compute structural graph metrics for each subject
3. Extract dynamic functional states using LOO K-Means
4. Calculate correlation between structural and dynamic metrics
5. Perform robustness analysis
6. Generate the final report

### Individual Components

- **Structural Metrics**: `python code/preprocess/structural.py`
- **Functional Metrics**: `python code/preprocess/functional.py`
- **Correlation Analysis**: `python code/analysis/correlation.py`
- **Robustness Analysis**: `python code/analysis/robustness.py`
- **Report Generation**: `python code/reports/generate_report.py`

### Validation

Validate the pipeline output:

```bash
python code/validate_quickstart.py
```

## Configuration

Key parameters are defined in `code/config.py`:

- `WINDOW_LENGTH`: Sliding window length (default: 30 TRs)
- `WINDOW_STEP`: Step size between windows (default: 1 TR)
- `K_MEANS_K`: Number of K-Means clusters (default: 5)
- `DENSITY_THRESHOLD_BASELINE`: Structural graph density threshold (default: None)
- `DENSITY_THRESHOLD_VARIATION`: Density variation for sensitivity analysis (default: 0.05)

## Output Files

The pipeline generates the following outputs in the `data/processed/` directory:

- `structural_metrics.csv`: Per-subject structural graph metrics
- `dynamic_metrics.csv`: Per-subject dynamic functional metrics
- `state_assignments.csv`: State sequences for each subject
- `correlation_results.csv`: Correlation coefficients, p-values, and FDR corrections
- `sensitivity_comparison.csv`: Sensitivity analysis results
- `final_report.json`: Comprehensive summary of all findings

## Testing

Run unit tests:

```bash
python -m pytest tests/unit/ -v
```

Run integration tests:

```bash
python -m pytest tests/integration/ -v
```

## Methodological Notes

### Leave-One-Out (LOO) K-Means

To ensure statistical independence, this project employs a Leave-One-Out K-Means strategy:
1. For each subject, K-Means centroids are computed using data from all *other* subjects (N-1).
2. The excluded subject's data is then assigned to these LOO-generated centroids.
3. This prevents data leakage and ensures unbiased metric estimation.

### Associational Framing

All reports and analyses explicitly frame findings as **associational** rather than causal. The study investigates correlations between structural topology and functional dynamics without implying directional causality.

### CPU-Only Execution

The pipeline is optimized for CPU execution with no GPU dependencies. Memory usage is monitored and optimized for environments with ~7 GB RAM.

## License

This project is licensed under the MIT License.

## Acknowledgments

- **Data Source**: Human Connectome Project (HCP), WU-Minn Consortium
- **Platform**: OpenNeuro for data distribution
- **Tools**: NetworkX, scikit-learn, nilearn, pandas, numpy, scipy

## Contact

For questions or contributions, please open an issue in the repository.

# Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns

## Overview

This project investigates whether topological properties of structural brain networks (derived from diffusion MRI) predict the prevalence, stability, and switching speed of recurrent activity patterns (derived from functional MRI). The analysis employs a rigorous Leave-One-Out (LOO) K-Means clustering strategy to ensure statistical independence between training and assignment phases.

## Research Question

Do topological properties of structural brain networks derived from diffusion MRI predict the prevalence, stability, and switching speed of recurrent activity patterns?

## Methodological Framework

### Data Sources
- **Structural Connectivity**: Diffusion MRI (dMRI) data from the HCP (Human Connectome Project) OpenNeuro dataset.
- **Functional Connectivity**: Resting-state fMRI (rs-fMRI) data from the same HCP cohort.

### Key Pipeline Stages
1. **Preprocessing**:
 - Structural: Graph metric calculation (global efficiency, clustering coefficient, modularity) using NetworkX.
 - Functional: Sliding-window correlation (30 TR window, 1 TR step) followed by LOO K-Means state extraction.
2. **Leave-One-Out (LOO) Strategy**:
 - For each subject, centroids are generated using data from all *other* subjects (N-1).
 - This ensures that the state assignment for a subject is independent of its own data, preventing circularity.
3. **Correlation Analysis**:
 - Statistical testing (Pearson/Spearman) between structural metrics and dynamic functional metrics.
 - Benjamini-Hochberg FDR correction applied to control for multiple comparisons.
4. **Robustness Checks**:
 - Sensitivity analysis on window length (30 TR vs. 20 TR).
 - Sensitivity analysis on structural density thresholds (±5% variation).

### Associational Framing
All results are framed as "associational" or "correlational" findings. The pipeline does not claim causal inference. Language in the final report explicitly avoids causal terminology (e.g., "predicts" is interpreted as "statistically associated with" in the context of the report).

## Directory Structure

```
.
├── code/ # Implementation modules
│ ├── analysis/ # Correlation and robustness analysis
│ ├── preprocess/ # Data loading and metric calculation
│ ├── reports/ # Report generation and validation
│ ├── utils/ # CPU optimization utilities
│ ├── config.py # Global configuration
│ ├── main.py # Main pipeline orchestrator
│ └── setup_data_structure.py
├── data/ # Data storage
│ ├── raw/ # Raw HCP data (downloaded)
│ ├── processed/ # Processed metrics and state assignments
│ └── logs/ # Exclusion logs and execution logs
├── tests/ # Unit and integration tests
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── docs/ # Documentation
│ └── README.md # This file
├── contracts/ # Data schemas
├── requirements.txt # Python dependencies
└── pyproject.toml # Project configuration (linting, formatting)
```

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-128-investigating-the-influence-of-network-t
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### Running the Full Pipeline

The main entry point is `code/main.py`. It orchestrates the entire pipeline:

```bash
python code/main.py
```

This will:
1. Load HCP data from `data/raw/`.
2. Compute structural graph metrics.
3. Perform LOO K-Means state extraction and calculate dynamic metrics.
4. Aggregate results into CSV files in `data/processed/`.
5. Log exclusions to `data/logs/exclusion_log.json`.

### Running Specific Analyses

- **Correlation Analysis**:
 ```bash
 python code/analysis/generate_correlation_results.py
 ```

- **Robustness/Sensitivity Analysis**:
 ```bash
 python code/analysis/robustness.py
 ```

- **Report Generation**:
 ```bash
 python code/reports/generate_report.py
 ```

- **Validation**:
 ```bash
 python code/validate_quickstart.py
 ```

### Configuration

Global parameters are defined in `code/config.py`:
- `WINDOW_LENGTH = 30` (in TRs)
- `WINDOW_STEP = 1` (in TRs)
- `K_MEANS_K = 5`
- `DENSITY_THRESHOLD_BASELINE = None`
- `DENSITY_THRESHOLD_VARIATION = 0.05`

## Output Artifacts

- **`data/processed/structural_metrics.csv`**: Per-subject structural graph metrics.
- **`data/processed/dynamic_metrics.csv`**: Per-subject dynamic functional metrics (dwell time, visited states).
- **`data/processed/correlation_results.csv`**: Correlation coefficients (r), p-values, and FDR-corrected flags.
- **`data/processed/sensitivity_comparison.csv`**: Absolute differences in correlation coefficients for sensitivity analyses.
- **`data/logs/exclusion_log.json`**: Log of subjects excluded due to convergence failure or sparsity.
- **`data/reports/final_report.json`**: Comprehensive summary of findings with associational framing.

## Testing

Run the test suite:

```bash
pytest tests/
```

- **Unit Tests**: `tests/unit/`
- **Integration Tests**: `tests/integration/`

## Contributing

When adding new features:
1. Ensure the code adheres to the CPU-only constraint.
2. Maintain the "associational" language framing.
3. Update the `contracts/` schemas if data structures change.
4. Add tests for new functionality.

## License

[Insert License Information Here]

## Acknowledgments

Data provided by the Human Connectome Project, WU-Minn Consortium (Principal Investigators: David Van Essen and Kamil Ugurbil; 1U54MH091657) funded by the 16 NIH Institutes and Centers that support the NIH Blueprint for Neuroscience Research; and the McDonnell Center for Systems Neuroscience at Washington University.

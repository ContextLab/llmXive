# Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns

## Overview

This project investigates whether topological properties of structural brain networks (derived from diffusion MRI) predict the prevalence, stability, and switching speed of recurrent activity patterns (derived from dynamic functional connectivity in fMRI).

## Project Structure

```
.
├── code/ # Source code
│ ├── analysis/ # Correlation and robustness analysis
│ ├── preprocess/ # Data loading and metric calculation
│ ├── reports/ # Report generation and validation
│ ├── utils/ # CPU optimization utilities
│ ├── config.py # Configuration and paths
│ ├── main.py # Main pipeline entry point
│ └── validate_quickstart.py
├── data/ # Data storage
│ ├── raw/ # Raw HCP data (downloaded)
│ ├── processed/ # Computed metrics (CSVs)
│ └── logs/ # Exclusion logs
├── contracts/ # Schema definitions
│ ├── dataset.schema.yaml
│ └── output.schema.yaml
├── tests/ # Test suite
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── docs/ # Documentation
│ └── README.md
├── requirements.txt # Python dependencies
└── quickstart.md # Reproducibility guide
```

## Prerequisites

- Python 3.9+
- CPU-only environment (no GPU required)
- ~7 GB RAM, ~14 GB disk space for processing [UNRESOLVED-CLAIM: c_083f2d9e — status=not_enough_info]
- Internet access to download HCP data from OpenNeuro

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-128-investigating-the-influence-of-network-t
 ```

2. Create a virtual environment and install dependencies:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```

## Quickstart

Run the full pipeline:

```bash
python code/main.py
```

This will:
1. Download HCP data (if not present)
2. Compute structural graph metrics (global efficiency, clustering, modularity)
3. Compute dynamic functional metrics (dwell time, visited states) using LOO k-means
4. Perform structure-function correlation analysis with FDR correction
5. Run sensitivity analyses (20 TR vs 30 TR window, density threshold variation)
6. Generate final report with "associational" framing

Outputs:
- `data/processed/structural_metrics.csv`
- `data/processed/dynamic_metrics.csv`
- `data/processed/correlation_results.csv`
- `data/logs/exclusion_log.json`
- `data/reports/final_report.json`

## Validation

Validate the pipeline reproducibility:

```bash
python code/validate_quickstart.py
```

Audit reports for "associational" language compliance:

```bash
python code/reports/audit_associational_language.py
```

Validate report against schema:

```bash
python code/reports/validate_report.py
```

## Testing

Run unit tests:

```bash
python -m pytest tests/unit/ -v
```

Run integration tests:

```bash
python -m pytest tests/integration/ -v
```

## Configuration

Edit `code/config.py` to modify:
- Sliding window length (default: 30 TR)
- Sensitivity check window (default: 20 TR)
- k-means clusters (default: k=5)
- Density thresholds
- Statistical alpha levels

## Methodology

### Structural Metrics
- Graph construction from dMRI tractography
- Global efficiency, average clustering coefficient, modularity
- Sparsity filter: exclude networks with sparsity > 90%

### Dynamic Functional Metrics
- Sliding window correlation (30 TR window, 1 TR step)
- Leave-One-Out (LOO) k-means clustering (k=5) to prevent circular correlation
- Metrics: number of visited states, mean dwell time

### Correlation Analysis
- Normality testing (Shapiro-Wilk) to select Pearson vs Spearman
- Benjamini-Hochberg FDR correction (q=0.05)
- Explicit "associational" framing (no causal claims)

### Sensitivity Analysis
- Window length: 30 TR (baseline) vs 20 TR (sensitivity)
- Density threshold: ±5% variation
- Report absolute difference in correlation coefficients

## Data Source

HCP 1200 Subjects dataset from OpenNeuro (ds000224). [UNRESOLVED-CLAIM: c_a2f95cef — status=not_enough_info]
Real data is downloaded at runtime; no synthetic data is used.

## Constraints

- CPU-only execution (no GPU)
- Memory efficient processing (streaming for large datasets)
- Strict subject isolation in LOO clustering
- No fabricated or placeholder data

## License

[Insert License]

## Contributing

[Insert Contribution Guidelines]

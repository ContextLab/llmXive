# Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns

## Project Status
**Status**: Completed (MVP + Robustness Analysis)
**Version**: 1.0.0

## Quick Start

### Prerequisites
- Python 3.8+
- Access to HCP OpenNeuro data (downloaded to `data/raw/`)

### Installation
```bash
pip install -r requirements.txt
```

### Running the Pipeline
```bash
python code/main.py
```

### Validating Results
```bash
python code/validate_quickstart.py
```

## What This Project Does

This project analyzes the relationship between structural brain connectivity (from dMRI) and dynamic functional connectivity (from fMRI). It uses a **Leave-One-Out (LOO)** K-Means clustering approach to ensure that the functional states assigned to a subject are independent of that subject's own data, thereby avoiding circularity.

Key outputs include:
- Structural graph metrics (efficiency, clustering, modularity).
- Dynamic functional metrics (dwell time, state transitions).
- Correlation analysis with FDR correction.
- Robustness checks on window length and density thresholds.

## Documentation

- **[Architecture Overview](docs/ARCHITECTURE.md)**: High-level design and component breakdown.
- **[Implementation Process](docs/PROCESS.md)**: Step-by-step guide to the development workflow.
- **[User Guide](docs/README.md)**: Detailed usage instructions and output descriptions.

## Key Methodological Notes

- **LOO K-Means**: Centroids are generated from N-1 subjects, ensuring independence for the Nth subject's state assignment.
- **Associational Framing**: All results are presented as correlations, not causal predictions.
- **CPU-Only**: The pipeline is optimized for CPU execution; no GPU acceleration is used.

## License

[Insert License Information Here]

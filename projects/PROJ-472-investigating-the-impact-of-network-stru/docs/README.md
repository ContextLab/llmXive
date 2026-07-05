# llmXive: Network Structure & Neural Avalanche Dynamics

## Project Overview

This project investigates the relationship between structural brain network properties (derived from dMRI) and neural avalanche dynamics (derived from EEG). Due to data availability constraints, this implementation utilizes a simulation approach where synthetic EEG data is generated from structural connectomes using Wilson-Cowan equations.

## Architecture

The pipeline follows a modular design:
1. **Data Ingestion**: Download and preprocess dMRI data.
2. **Simulation**: Generate synthetic EEG based on structural graphs.
3. **Analysis**: Compute network metrics and detect avalanches.
4. **Statistics**: Test associations and robustness.

## Quick Start

### Prerequisites

- Python 3.11+
- MRtrix3 (for dMRI preprocessing)
- MNE-Python
- NetworkX, BCTpy, powerlaw

### Installation

```bash
pip install -r code/requirements.txt
```

### Running the Pipeline

Execute the main orchestration script:

```bash
python code/main.py --config config.yaml
```

This will:
1. Download dMRI data (if not present).
2. Preprocess connectomes.
3. Simulate EEG.
4. Compute metrics and avalanches.
5. Run statistical analysis.
6. Generate a final report.

## Documentation

- [Data Model](DATA_MODEL.md): Detailed description of core entities.
- [API Usage](API_USAGE.md): Code examples for all major modules.
- [Configuration](../code/config.py): Hyperparameters and path settings.

## Output

Results are stored in the `data/results/` directory:
- `network_metrics.csv`: Structural graph metrics.
- `avalanche_events.csv`: Detected avalanche parameters.
- `powerlaw_fit.csv`: Model fitting results.
- `correlation_report.csv`: Statistical associations.
- `sensitivity_analysis.csv`: Threshold robustness results.

## License

MIT License

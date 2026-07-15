# Quickstart Guide

Get up and running with the `llmXive` pipeline in 5 steps.

## Prerequisites

- Python 3.11+
- pip
- Access to OpenNeuro (optional, for real data probe)

## 1. Setup Environment

Clone the repository and install dependencies:

```bash
pip install -r code/requirements.txt
```

Ensure the `.env` file is configured (if using custom paths):

```bash
#.env
DATA_ROOT=/path/to/data
SIMULATION_SEED=42
```

## 2. Run the Full Pipeline (Simulation Path)

Since real EEG is often unavailable, the pipeline defaults to simulation.

```bash
python code/main.py --mode simulation
```

This command will:
1. Attempt to download dMRI (and fail if not found, triggering fallback or simulation-only mode).
2. Generate synthetic EEG using Wilson-Cowan dynamics.
3. Compute network metrics.
4. Detect avalanches and fit power-laws.
5. Run statistical correlations.
6. Generate the final report.

## 3. Inspect Results

Check the `data/results/` directory:

- `metrics.csv`: Network and avalanche metrics per subject.
- `fitting_results.json`: Power-law fit parameters.
- `correlation_report.csv`: Statistical associations.
- `report.md`: Human-readable summary.

## 4. Run Tests

Verify the installation:

```bash
pytest tests/ -v
```

## 5. Customization

- **Change Thresholds**: Edit `code/analysis/sensitivity.py` (default: `[0.70, 0.75, 0.80]`).
- **Modify Simulation**: Edit `code/config.py` -> `SIMULATION_PARAMS`.
- **Add Subjects**: Place new connectome files in `data/processed/connectomes/`.

## Troubleshooting

- **`DataLoadError`**: Expected if real data is missing. The pipeline automatically switches to simulation.
- **`RuntimeError` (Causal Language)**: If the report generator finds words like "causes", it will halt. Rephrase findings in `code/analysis/report.py` to be associational.
- **Memory Error**: If processing large connectomes, ensure `data/processed` is on a fast drive or increase swap space.

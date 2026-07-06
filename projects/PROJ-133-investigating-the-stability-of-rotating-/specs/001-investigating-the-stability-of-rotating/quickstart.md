# Quickstart: Investigating the Stability of Rotating Bose-Einstein Condensates with Dipolar Interactions

## Prerequisites

- Python 3.11+
- `pip` or `poetry`
- A standard CPU environment (no GPU required).

## Installation

1.  **Clone the repository** (assuming the project structure is in place).
2.  **Navigate to the code directory**:
    ```bash
    cd projects/PROJ-133-investigating-the-stability-of-rotating-/code
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins versions for `numpy`, `scipy`, `matplotlib`, `pandas`, `pytest`, and `numba`.*

## Running a Single Simulation

To run a single simulation for validation (e.g., Ω=0.5, ε_dd=0.5, N=10⁴):

```bash
python -m simulation.runner --N 10000 --Omega 0.5 --epsilon_dd 0.5 --seed 42 --output-dir ../../data/raw
```

This will generate `.npy` files for density and phase snapshots and a log file.

## Running the Full Grid Scan

To execute the full parameter grid (60 points × 5 repeats):

```bash
python -m simulation.runner --grid-config ../../specs/001-gene-regulation/grid_config.json --repeats 5 --output-dir ../../data/raw
```

*Note: This command is designed to run within the 6-hour CI limit. If it exceeds the limit, the `grid_config.json` can be modified to reduce the grid resolution.*

## Analyzing Results

After simulations are complete, run the analysis pipeline:

```bash
python -m analysis.metrics --input-dir ../../data/raw --output-file ../../data/processed/metrics.csv
python -m statistics.aggregators --input-file ../../data/processed/metrics.csv --output-file ../../data/aggregated/results.json
```

## Visualizing the Phase Diagram

Generate the final phase map and statistical plots:

```bash
python -m viz.plotter --input-file ../../data/aggregated/results.json --output-dir ../../docs/figures
```

## Testing

Run the unit and contract tests:

```bash
pytest tests/
```

## Troubleshooting

- **Numerical Instability**: If the simulation crashes (NaN values), check the `crash_time` in the log. This indicates an unstable regime; the run is automatically classified as unstable.
- **Memory Error**: If memory usage exceeds limits, reduce the grid size in `grid_config.json` to 128×128.
- **Timeout**: If the full grid scan exceeds 6 hours, reduce the number of repeats to 3 for the initial run, or reduce the grid resolution.

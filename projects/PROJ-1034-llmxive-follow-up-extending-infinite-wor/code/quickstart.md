# Quickstart Guide

This guide provides the commands to run the simulation pipeline and analysis.

## Prerequisites

- Python 3.8+
- Install dependencies: `pip install -r requirements.txt`

## Running the Simulation

The simulation can be run with specific parameters. The CLI now supports `--agent`, `--seed`, and `--mode` flags.

### Run a single simulation (Baseline)

```bash
python -m src.cli.run_simulation --agent ca_eco_director --steps 2000 --seed 42
```

### Run a parameter sweep

```bash
python -m src.cli.run_simulation --mode sweep --steps 2000 --seed 42
```

## Validating Results

After running the simulation, validate the metrics to ensure data integrity and correct flags.

```bash
python -m src.analysis.validate_metrics --path data/raw
```

## Expected Outputs

- `data/raw/baseline_partial.parquet`: The simulation log (if time-bound or partial).
- `data/raw/baseline_partial_status.json`: Status log containing the 'Time-Bound' flag.
- `logs/simulation.log`: Detailed execution logs.

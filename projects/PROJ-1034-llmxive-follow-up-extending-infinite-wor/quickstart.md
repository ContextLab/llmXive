# Quickstart Guide

## Prerequisites

- Python 3.9+
- pip

## Installation

```bash
pip install -r requirements.txt
```

## Running a Simulation

```bash
python src/cli/run_simulation.py --config src/sim/config_schema.yaml --steps 100 --seed 42
```

## Running a Parameter Sweep

```bash
python src/cli/run_sweep.py --config src/sim/config_schema.yaml
```

## Analysis

```bash
python src/analysis/lmm_runner.py --input data/processed/metrics.csv
```
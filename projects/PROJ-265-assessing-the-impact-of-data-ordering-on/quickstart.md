# Quick Start Guide

## Prerequisites

- Python 3.11 or higher
- pip package manager

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Simulation

To run the full simulation batch:

```bash
python code/runner.py --full
```

To run a single simulation:

```bash
python code/runner.py --phi 0.8 --n 100
```

## Expected Output

After running the full simulation:

- `results/simulation_logs.json` - Raw simulation results
- `results/coverage_metrics.csv` - Aggregated metrics
- `results/sensitivity_analysis.md` - Sensitivity report
- `results/summary_report.md` - Summary report
- `results/stratified_report.md` - Stratified analysis

## Verification

{{claim:c_2cfa5ada}}
Shuffled baselines should maintain coverage near 0.95. [UNRESOLVED-CLAIM: c_d974f58a — status=not_enough_info]
{{claim:c_e01dcd96}}
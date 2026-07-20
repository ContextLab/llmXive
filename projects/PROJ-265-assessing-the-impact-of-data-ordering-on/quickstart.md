# Quickstart Guide: Assessing the Impact of Data Ordering on Bootstrapping

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

## Installation

1. Clone the repository (or navigate to the project root).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Simulation

The project provides a single entry point for running the full synthetic simulation.

### Full Simulation (Synthetic Only)

This command runs the complete batch of simulations for $\phi \in [0.0, 0.9]$ and $N \in \{50, 100, 200\}$ with 1000 trials per configuration.

```bash
python code/runner.py --full
```

### Custom Configuration

You can run specific configurations using the following flags:

```bash
# Run for a specific phi and sample size
python code/runner.py --phi 0.8 --n 100 --trials 500

# Run with a specific number of bootstrap resamples
python code/runner.py --full --resamples 2000
```

## Expected Output

Upon successful completion of `python code/runner.py --full`:

1. **Log File**: `results/simulation_logs.json` will be created containing detailed results for every $\phi, N$ combination.
2. **Metrics CSV**: The simulation logs are processed by `code/generate_metrics_csv.py` (run separately if not auto-triggered) to create `results/coverage_metrics.csv`.
3. **Reports**:
 - `results/summary_report.md`
 - `results/sensitivity_analysis.md`

The `simulation_logs.json` file will contain entries with keys:
- `phi`: float
- `n`: int
- `ordered_coverage`: float
- `shuffled_coverage`: float
- `diff`: float
- `p_value`: float
- `condition`: "paired"

## Verification

To verify reproducibility, run the command twice with the same seed (default is deterministic via `config.py`):

```bash
python code/runner.py --full
md5sum results/simulation_logs.json
python code/runner.py --full
md5sum results/simulation_logs.json
```

The checksums should match.

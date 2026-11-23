# Quickstart Guide: EvoPolicyGym Follow-up Pipeline

This guide walks you through running a single evolutionary experiment using the `main.py` CLI entry point.

## Prerequisites

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

## Running the Full Pipeline

To execute the full pipeline (shift analysis -> evolution -> stats), use:

```bash
python code/main.py --run-evolution --runs 5 --seeds 42 --conditions baseline counterfactual
```

This will:
1. Generate dynamic shift environments (if not already present)
2. Run evolutionary agents on baseline and counterfactual conditions
3. Parse policies and write results to `data/evolution_results.csv`
4. Run statistical analysis and write results to `data/stats_results.json`
5. Aggregate final results into `data/final_results.csv`

## Running Individual Stages

### Shift Sensitivity Analysis Only
```bash
python code/main.py --run-shift-analysis
```

### Evolution Pipeline Only
```bash
python code/main.py --run-evolution --runs 5 --seeds 42
```

### Statistical Analysis Only
```bash
python code/main.py --run-stats
```

## Output Files

- `data/evolution_results.csv`: Raw metrics from each evolutionary run
- `data/stats_results.json`: Statistical analysis results (p-values, effect sizes)
- `data/final_results.csv`: Aggregated final results with all metrics
- `data/discovered_envs.json`: List of discovered environments from EvoPolicyGym registry
- `data/shift_validation.log`: Log of shift validation failures
- `data/fallbacks.log`: Log of explanation generation fallbacks

## Custom Configuration

You can customize the run by specifying:
- `--seeds`: List of random seeds (default: [42])
- `--runs`: Number of runs per seed (default: 5)
- `--envs`: Specific environment IDs to test (default: all discovered)
- `--conditions`: Conditions to run (default: baseline, counterfactual)

Example with custom seeds and environments:
```bash
python code/main.py --run-evolution --seeds 42 123 456 --runs 3 --envs CartPole-v1 MountainCar-v0
```

## Troubleshooting

If you encounter errors about missing data files:
- Ensure you've run the shift analysis first (`--run-shift-analysis`)
- Check that `data/evolution_results.csv` exists before running stats analysis
- Verify that EvoPolicyGym is properly installed and registered
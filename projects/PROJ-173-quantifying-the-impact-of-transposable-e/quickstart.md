# Quick Start Guide

## Prerequisites
- Python 3.9+
- pip

## Installation
1. Clone the repository
2. Install dependencies:
 ```bash
 make install
 ```

## Running the Pipeline
1. Generate mock data:
 ```bash
 python code/data_generator.py
 ```
2. Run the full analysis pipeline:
 ```bash
 python code/run_pipeline.py
 ```

## Output
Results will be written to `data/results/`:
- `association_results.csv`: TE-gene association statistics
- `population_structure_control_metrics.csv`: R² reduction metrics
- `null_distribution_plot.png`: Permutation test visualization

## Testing
Run all tests:
```bash
make test
```

## Formatting and Linting
```bash
make format
make lint
```
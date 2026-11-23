# Exploring the Impact of Data Imputation Methods on Causal Inference

This project investigates how different data imputation methods affect causal inference accuracy when data is Missing Not At Random (MNAR).

## Quick Start

### Prerequisites

- Python 3.11+
- Install dependencies: `pip install -r code/requirements.txt`

### Running the Full Pipeline

```bash
# 1. Run simulations
python code/run_simulation.py --runs 200 --beta-sweep 0.0,0.2,0.5,0.8,1.0

# 2. Run analysis
python code/analysis.py --validate-schema --input data/results/simulation_summary.csv
python code/analysis.py --run-stats --input data/results/simulation_summary.csv

# 3. Generate visualizations (unified script)
python code/visualization.py --plot bias_vs_beta --input data/results/simulation_summary.csv --output docs/paper/figures/bias_vs_beta.png
python code/visualization.py --plot coverage_vs_beta --input data/results/simulation_summary.csv --output docs/paper/figures/coverage_vs_beta.png
python code/visualization.py --plot bias_distributions --input data/results/simulation_summary.csv --output docs/paper/figures/bias_distributions.png

# 4. Power analysis
python code/analysis.py --run-power --input data/results/simulation_summary.csv
```

### Visualization Script (Primary Entry Point for Plots)

The `code/visualization.py` script is the **unified CLI** for all plot generation. It replaces deprecated references to separate plotting scripts.

```bash
# Available plots:
python code/visualization.py --plot bias_vs_beta --input <csv> --output <png>
python code/visualization.py --plot coverage_vs_beta --input <csv> --output <png>
python code/visualization.py --plot bias_distributions --input <csv> --output <png>
```

## Project Structure

See `docs/paper/notes.md` for detailed file structure and methodology.

## Key Files

- `code/run_simulation.py`: Main simulation executor
- `code/analysis.py`: Statistical analysis and schema validation
- `code/visualization.py`: Unified visualization CLI (T047/T042)
- `docs/paper/notes.md`: Detailed research notes and documentation

## License

Research project - all rights reserved.
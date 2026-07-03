# PROJ-483: Evaluating the Robustness of Common Statistical Tests to Non-Independence

This project investigates how common statistical tests (t-test, ANOVA, Chi-squared) perform when the assumption of independence is violated in real-world public datasets.

## Structure
- `src/`: Source code for data loading, dependency injection, simulation, and metrics.
- `data/`: Raw and processed datasets, manifests, and checksums.
- `results/`: Simulation outputs, aggregated statistics, and visualizations.
- `tests/`: Unit and integration tests.
- `contracts/`: JSON/YAML schemas for configuration validation.
- `docs/`: Documentation.

## Setup
1. Ensure Python 3.10+ is installed.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the pipeline: `python src/main.py`

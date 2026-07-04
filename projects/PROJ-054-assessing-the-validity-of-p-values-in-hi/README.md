# PROJ-054: Assessing the Validity of p-Values in High-Dimensional Data

## Project Structure

- `code/`: Source code for the research pipeline
 - `utils/`: Utilities for simulation, regularization, and exceptions
 - `generate_data/`: Synthetic data generation modules
 - `run_tests/`: Hypothesis test execution modules
 - `analyze_pvalues/`: P-value analysis and visualization modules
- `data/`: Generated datasets and analysis results
 - `synthetic/`: Raw synthetic datasets
 - `synthetic/trajectories/`: P-value trajectories per iteration
 - `results/`: Aggregated analysis results (JSON, CSV)
- `tests/`: Test suite
 - `unit/`: Unit tests
 - `integration/`: Integration tests
- `docs/`: Documentation
- `specs/`: Feature specifications and design documents

## Quick Start

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Run the simulation pipeline:
 ```bash
 python code/run_simulation.py
 ```

3. View results in `data/results/`

## License
Research use only.

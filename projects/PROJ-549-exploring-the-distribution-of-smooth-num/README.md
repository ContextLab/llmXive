# PROJ-549: Exploring the Distribution of Smooth Numbers in Short Intervals

## Project Structure

This project follows the standard llmXive research pipeline structure:

- `code/`: Python source modules for sieve generation, smoothness checking, and statistical analysis.
- `data/`: Output artifacts including prime lists, density measurements, and model fit results.
- `tests/`: Unit and integration tests for the research pipeline.
- `state/`: Checkpoint files for resuming long-running computations.

## Setup

1. Ensure Python 3.11+ is installed.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Run the pipeline via `python code/main.py`.

## Execution Order

1. **T012**: Generate primes up to $10^9$ (`data/primes_1e9.csv`).
2. **T013**: Validate the prime list.
3. **T023**: Compute density measurements across the parameter grid.
4. **T029**: Perform statistical analysis and visualization.

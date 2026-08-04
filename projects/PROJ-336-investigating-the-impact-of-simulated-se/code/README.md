# PROJ-336: Investigating the Impact of Simulated Sensory Deprivation on Resting-State Brain Network Dynamics

## Project Structure

This project follows a standard Python research pipeline structure:

- `src/`: Source code for data acquisition, preprocessing, analysis, and visualization.
- `tests/`: Unit and integration tests.
- `data/`: Storage for downloaded raw data and processed intermediate files.
- `results/`: Final outputs including CSVs, plots, and reports.
- `specs/`: Design documents and specifications.

## Setup

1. Ensure Python 3.11+ is installed.
2. Run `bash code_setup.sh` to initialize the directory structure (if not already done).
3. Install dependencies: `pip install -r requirements.txt` (once created in T002).

## Execution

Run the main pipeline:
```bash
python main.py
```
# PROJ-062: Quantifying the Impact of Code Ownership on Software Quality

## Overview
This project analyzes the relationship between code ownership (concentration of commits by developers) and software quality metrics (bugs, complexity, churn).

## Project Structure
- `code/`: Python implementation scripts and utilities.
- `data/`:
 - `raw/`: Raw data from GitHub (cloned repos, API dumps).
 - `intermediate/`: Processed ownership data, bug metadata, and calculated metrics.
 - `results/`: Final statistical summaries and visualizations.
- `tests/`: Unit, integration, and contract tests.
- `specs/`: Design documents and data schemas.
- `logs/`: Pipeline execution logs.
- `state/`: Versioning artifacts and hashes.

## Getting Started
1. Ensure Python 3.8+ is installed.
2. Install dependencies: `pip install -r code/requirements.txt` (after T002).
3. Run the setup script (if not already run): `python code/setup_project.py`.
4. Follow the `quickstart.md` for the pipeline execution flow.

## Execution Constraints
- Max RAM: 7 GB
- Max Disk: 14 GB (log rotation)
- No GPU acceleration.
- Real data only from GitHub.

## Status
Phase 1 (Setup) - T001 Complete.
# PROJ-041: Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic

## Project Setup

This project uses a standardized directory structure for data science and machine learning research.

### Directory Structure

- `code/`: Source code for the project
 - `data/`: Data ingestion and preprocessing scripts
 - `models/`: Model definitions and training scripts
 - `analysis/`: Statistical analysis and attribution scripts
 - `utils/`: Utility functions (seeding, memory monitoring, etc.)
- `data/`: Data storage
 - `raw/`: Raw downloaded datasets
 - `processed/`: Preprocessed and subsampled graphs
 - `results/`: Model outputs, metrics, and statistical reports
- `tests/`: Test suites
 - `integration/`: Integration tests
 - `unit/`: Unit tests

### Quick Start

1. Ensure the directory structure exists:
 ```bash
 python code/scripts/setup_directories.py
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Run tests:
 ```bash
 pytest tests/
 ```

### Task T001: Project Directory Structure

This task creates the foundational directory structure required for the project.
Run `python code/scripts/setup_directories.py` to initialize all required folders.
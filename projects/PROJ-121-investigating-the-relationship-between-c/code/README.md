# Cosmic Ray Anisotropy Solar-Cycle Modulation

## Project Structure
- `code/src/`: Source code for analysis
- `code/data/`: Raw, processed, and result data
- `code/tests/`: Unit and integration tests
- `code/scripts/`: Utility scripts

## Setup
1. Install dependencies: `pip install -r code/requirements.txt`
2. Run setup: `python code/scripts/setup_directories.py`

## Execution
- Full pipeline: `./code/run_all.sh`
- Correlation analysis: `python code/analyze_correlation.py`
- Generate report: `./code/make_report.sh`

## Requirements
- Python 3.11+
- No CUDA/GPU dependencies

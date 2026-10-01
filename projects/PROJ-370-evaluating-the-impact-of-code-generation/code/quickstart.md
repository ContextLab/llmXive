# Quickstart Guide

## Prerequisites
- Python 3.9+
- pip
- git

## Setup
1. Clone the repository
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Project Structure
- `code/` - Source code
 - `src/` - Main source modules
 - `tests/` - Test suite
 - `config/` - Configuration files
 - `contracts/` - JSON schema contracts
- `data/` - Data directories
 - `raw/` - Raw extracted data
 - `derived/` - Processed data
 - `annotations/` - Human annotations
- `results/` - Final reports and metrics
- `logs/` - Pipeline logs

## Running the Pipeline
1. Extract PR data:
 ```bash
 python code/src/extraction/fetch_prs.py
 python code/src/extraction/preprocess.py
 ```
2. Run detection:
 ```bash
 python code/src/detection/detect_llm_code.py
 python code/src/inference/run_inference.py
 ```
3. Analyze results:
 ```bash
 python code/src/analysis/align.py
 python code/src/analysis/metrics.py
 python code/src/analysis/stats.py
 python code/src/reporting/generate_report.py
 ```

## Testing
Run the test suite:
```bash
pytest code/tests/ -v
```

## Configuration
Edit `code/config/settings.py` to configure:
- Target repositories
- Hyperparameters
- Paths and random seeds

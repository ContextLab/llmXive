# Quickstart Guide: llmXive Follow-up

## Prerequisites
- Python 3.9+
- Git
- Docker (for sandboxed execution)

## 1. Setup Directory Structure
Before running any analysis, ensure the project directory structure exists.

```bash
# Navigate to the project root
cd projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/

# Run the setup script to create directories
python code/setup_directories.py
```

This will create:
- `data/raw/`: For raw dataset downloads
- `data/processed/`: For processed data splits and results
- `code/src/`: Source code for the pipeline
- `code/tests/`: Unit and integration tests
- `code/notebooks/`: Jupyter notebooks for exploration
- `paper/`: Drafts and reports
- `state/`: Project state files
- `contracts/`: API contracts

## 2. Install Dependencies
```bash
cd code
pip install -r requirements.txt
```

## 3. Configure Environment
Copy `.env.example` to `.env` and set your model paths (e.g., CodeLlama-1.3b for CPU).
```bash
cp.env.example.env
# Edit.env with your configuration
```

## 4. Run Data Loading
Fetch and process the HumanEval and MBPP datasets.
```bash
python code/src/data_loader.py
```

## 5. Run Analysis Pipeline
Once data is loaded, run the entropy and inference pipelines.
```bash
# Run entropy extraction
python code/src/entropy.py

# Run iterative inference
python code/src/inference.py

# Run analysis (correlation, router training)
python code/src/analysis.py
```

## 6. Validate Results
Check `data/processed/` for output files:
- `entropy_results.csv`
- `convergence_results.csv`
- `router_results.csv`
- `robustness_report.json`

## 7. Run Tests
```bash
cd code
pytest tests/
```
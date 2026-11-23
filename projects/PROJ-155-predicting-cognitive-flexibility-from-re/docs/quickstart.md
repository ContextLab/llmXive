# Quickstart Guide

## Prerequisites
- Python 3.11+
- `pip` and `venv`

## Setup
1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
4. Set your HCP API token:
 ```bash
 export HCP_API_TOKEN="your_token_here"
 ```

## Project Initialization
Run the setup script to create the required directory structure:
```bash
python code/setup_structure.py
```
**Verification**:
```bash
tree code/
# Should show: code/, code/data/, code/features/, code/analysis/, code/utils/
```

## Running the Pipeline
Once data is downloaded and structure is set, run the main pipeline:
```bash
python code/main.py
```

## Output Artifacts
- `data/processed/final_results.csv`: Final merged results.
- `data/results/regression_summary.json`: Regression statistics.
- `data/processed/exclusion_log.csv`: Log of excluded subjects.

# Quickstart Guide

## Environment Setup

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-332-quantifying-the-impact-of-magnetic-field
 ```

2. Create and activate a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Execution Commands

### Run the Full Pipeline

The main entry point is `code/main.py`. It accepts a list of DIII-D discharge IDs:

```bash
python code/main.py --discharges 123456,123457,123458
```

Or set the environment variable:
```bash
export DIII_D_DISCHARGES="123456,123457,123458"
python code/main.py
```

### Run Specific Tasks

- **Data Retrieval**:
 ```bash
 python code/data/retrieval.py
 ```

- **Metrics Calculation**:
 ```bash
 python code/analysis/run_metrics.py
 ```

- **Correlation Analysis**:
 ```bash
 python code/analysis/correlation.py
 ```

### Run Tests

```bash
pytest tests/ -v
```

### Check Directory Structure

Run the setup script to ensure all directories exist:
```bash
python code/setup_project.py
```

## Output Artifacts

After running the pipeline, check the following outputs:

- `data/processed/unified_analysis.csv`: Unified dataset
- `outputs/summary_report.json`: Final statistical report
- `outputs/topology_vs_confinement.png`: Diagnostic scatter plot

## Troubleshooting

- If MDSplus connection fails, check network connectivity and ensure the DIII-D archive is accessible.
- If the pipeline fails due to insufficient discharges, ensure at least 5 valid discharges are provided.

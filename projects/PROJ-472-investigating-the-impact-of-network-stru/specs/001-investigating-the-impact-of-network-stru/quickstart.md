# Quickstart: Investigating the Impact of Network Structure on Neural Avalanche Dynamics

## Prerequisites

- Python 3.11+
- pip / virtualenv
- Access to the verified HuggingFace datasets (no API key required for public datasets).

## Installation

1. **Clone the repository** (or create the project structure).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` will pin versions of `mne`, `networkx`, `powerlaw`, `scikit-learn`, `pandas`, `numpy`, `huggingface_hub`.*

## Running the Pipeline

### Step 1: Download Data
The pipeline will attempt to download data from the verified sources.
```bash
python code/main.py --action download --subset 10
```
*Note: `--subset` limits the number of subjects to download for testing (default: all available).*

### Step 2: Preprocess Data
This step runs dMRI connectivity extraction and EEG cleaning.
```bash
python code/main.py --action preprocess
```

### Step 3: Compute Metrics
Calculates network metrics and avalanche statistics.
```bash
python code/main.py --action metrics
```

### Step 4: Statistical Analysis
Runs correlations, permutation tests, and sensitivity analysis.
```bash
python code/main.py --action analysis
```

### Step 5: Generate Report
Outputs the final CSV and a summary JSON.
```bash
python code/main.py --action report
```

## Verification

To verify the pipeline:
```bash
pytest tests/ -v
```
This runs unit tests on metric computation and integration tests on the full pipeline (with a small synthetic dataset if real data is unavailable).

## Troubleshooting

- **Memory Error**: Reduce the `--subset` size. The pipeline is designed for moderate RAM requirements.
- **No Matched Subjects**: If the report states "No Matched Subjects Found", the pipeline has validated successfully, but the specific dataset constraint (matched dMRI+EEG) was not met in the verified sources.
- **Power-Law Convergence**: If many subjects fail power-law fitting, check the EEG signal quality or the threshold settings.

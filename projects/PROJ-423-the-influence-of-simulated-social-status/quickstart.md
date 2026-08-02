# Quickstart Guide: The Influence of Simulated Social Status on Risk-Taking Behavior

This guide provides step-by-step instructions to set up the environment, run the simulation or meta-analysis pipeline, perform adaptive regression analysis, and generate the final report.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- git (for cloning the repository)

## 1. Environment Setup

### Clone the Repository
```bash
git clone <repository-url>
cd PROJ-423-the-influence-of-simulated-social-status
```

### Create and Activate Virtual Environment
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### Install Dependencies
Install all required packages listed in `code/requirements.txt`:
```bash
pip install -r code/requirements.txt
```

## 2. Configuration

### Verify Simulation Parameters
Ensure that `code/simulation_parameters.json` exists and contains verified effect sizes and sample size N. If missing, run the Phase 0 tasks first:
```bash
python code/verify_citations.py --sources "Smith et al. 2020,Jones et al. 2019"
python code/power_analysis.py
```

### Set Data Source
Choose between synthetic simulation or real meta-analysis data by setting the `DATA_SOURCE` environment variable:
```bash
export DATA_SOURCE=simulation # or 'meta' for meta-analysis
```

## 3. Running the Pipeline

### Step 1: Generate or Fetch Data
Run the data generation or meta-analysis script:
```bash
python code/simulate.py
# OR
python code/meta_analysis.py
```
This will produce `data/raw/synthetic_data.csv` (or equivalent meta-analysis data).

### Step 2: Preprocess Data
Clean and preprocess the raw data:
```bash
python code/preprocess.py
```
This generates:
- `data/processed/cleaned_data.csv`
- `data/processed/structure_config.json` (specifies between/within-subjects design)

### Step 3: Run Adaptive Regression Analysis
Fit the appropriate model based on the detected data structure:
```bash
python code/analysis.py
```
This produces:
- Model coefficients, p-values, VIFs
- Sensitivity analysis results
- Post-hoc comparisons

### Step 4: Generate Final Report
Create the HTML/PDF summary report with forest plots:
```bash
python code/report.py
```
Output: `reports/analysis_report.html` and `reports/analysis_report.pdf`

## 4. Validation and Testing

### Run Unit Tests
```bash
pytest tests/unit/
```

### Run Contract Tests
```bash
pytest tests/contract/
```

### Verify Data Integrity
Check checksums for raw data files:
```bash
python code/utils.py --verify-checksums
```

## 5. Common Issues

### Missing Dependencies
If you encounter import errors, ensure all packages from `code/requirements.txt` are installed:
```bash
pip install -r code/requirements.txt
```

### Data Source Not Found
If `DATA_SOURCE=meta` fails, verify that the dataset ID in `code/meta_analysis.py` is valid and accessible. The script will fail loudly without synthetic fallback.

### Model Fitting Errors
If the adaptive model fails to converge, check the data structure in `data/processed/structure_config.json` and ensure sufficient sample size N.

## 6. Output Artifacts

After successful execution, you should have:
- `data/raw/` - Raw synthetic or meta-analysis data
- `data/processed/` - Cleaned data and structure configuration
- `reports/` - Final analysis report (HTML/PDF) and forest plots
- `state/` - Verification and decision logs

## 7. Next Steps

- Review the generated report for statistical significance and effect sizes
- Conduct sensitivity analyses by adjusting outlier thresholds in configuration
- Extend the pipeline with additional user stories as defined in `tasks.md`
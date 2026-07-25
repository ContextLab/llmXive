# Quickstart: The Influence of Simulated Social Validation on Neural Responses to Novel Information

## Prerequisites
- Python 3.11+
- Git
- Access to GitHub Actions (or local virtualenv for testing)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-496-the-influence-of-simulated-social-valida
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### Step 1: Dataset Search & Eligibility Check
Run the search script to identify eligible datasets.
```bash
python code/search.py
```
- **Output**: `data/raw/dataset_catalog.csv` and `data/results/negative_finding_report.pdf` (if no dataset found).
- **Note**: If the report is generated, the pipeline stops here. No further steps are valid.

### Step 2: Preprocessing (If Dataset Found)
If a dataset is eligible, run the preprocessing pipeline.
```bash
python code/preprocess.py --dataset-id <ID>
```
- **Output**: `data/processed/p300_metrics.csv`.
- **QC Check**: The script will log participants excluded due to low trial count or high artifact rate.

### Step 3: Statistical Analysis
Run the LMM and sensitivity analysis.
```bash
python code/analyze.py
```
- **Output**: `data/results/model_summary.csv`, `data/results/sensitivity_sweep.csv`, and plots.

### Step 4: Generate Report
Generate the final PDF/HTML report.
```bash
python code/report.py
```
- **Output**: `data/results/final_report.pdf`, `data/results/final_report.html`.

## Verification

1. **Check Data Integrity**:
   ```bash
   sha256sum data/processed/p300_metrics.csv
   # Compare with checksum in state/artifact_hashes.yaml
   ```
2. **Run Tests**:
   ```bash
   pytest tests/
   ```
3. **Validate Schema**:
   Ensure `data/processed/p300_metrics.csv` matches `contracts/p300_measure.schema.yaml`.

## Troubleshooting

- **Error: "No eligible datasets found"**: This is expected if the verified dataset list does not contain the required data. Review `data/results/negative_finding_report.pdf` for details.
- **Error: "Model did not converge"**: Check `data/results/model_summary.csv` for convergence flags. May indicate insufficient data or collinearity.
- **Error: "Memory Limit"**: If processing fails on CI, ensure `streaming=True` is used in `code/preprocess.py`.

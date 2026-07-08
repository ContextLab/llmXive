# Quickstart: Exploring the Correlation Between Molecular Complexity and Degradation Rates in Pharmaceuticals

## 1. Prerequisites
- Python 3.11+
- pip / virtualenv
- Git

## 2. Environment Setup
```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-071-exploring-the-correlation-between-molecu

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Data Download
Run the ingestion script to fetch and cache datasets.
```bash
python code/ingest.py
```
*Note: This script will download data from the verified HuggingFace URLs. If degradation data is missing, it will log a warning.*

## 4. Run the Pipeline
Execute the full analysis pipeline:
```bash
python code/analysis.py
```
This script performs:
1.  Descriptor calculation (RDKit)
2.  Data standardization (Unit conversion)
3.  Correlation and Regression analysis
4.  Visualization generation

## 5. Generate Report
```bash
python code/report.py
```
Output: `docs/reports/analysis_report.md`

## 6. Validation
Run the test suite to verify correctness:
```bash
pytest tests/
```

## 7. Troubleshooting
- **Memory Error**: If the dataset is too large, the script will automatically sample [deferred] of the data.
- **RDKit Errors**: Check `logs/descriptor_errors.log` for molecules that failed calculation.
- **Missing Data**: If no degradation data is found, the report will indicate a "Data Insufficiency" status.

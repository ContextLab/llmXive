# Quickstart: Predicting the Glass Forming Region of Metallic Glass Alloys via Machine Learning

## Prerequisites

- Python 3.11+
- `pip` and `venv`
- Access to GitHub Actions (for CI) or local CPU-only environment

## Installation

1. Clone the repository and navigate to the project directory:
 ```bash
 cd projects/PROJ-396-predicting-the-glass-forming-region-of-m
 ```

2. Create a virtual environment and install dependencies:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```

3. Verify dependencies:
 ```bash
 python -c "import sklearn, pandas, numpy; print('Dependencies OK')"
 ```

## Data Setup

1. **Download Dataset**:
 - If using Zenodo GFA-DB (), place raw CSV in `data/raw/`.
 - If using Materials Project, download composition data to `data/raw/`.
 - *Note: If no verified dataset is available, the pipeline will generate a Synthetic Fallback for code testing only.*

2. **Compute Checksum**:
 ```bash
 sha256sum data/raw/*.csv > data/metadata/checksums.txt
 ```

## Running the Pipeline

1. **Ingest and Compute Descriptors**:
 ```bash
 python code/data_ingestion.py --input data/raw/ --output data/processed/descriptors.csv
 ```
 *Note: This step handles chunked processing and fallback to synthetic data if source is missing.*

2. **Train Models**:
 ```bash
 python code/model_training.py --input data/processed/descriptors.csv --output results/models/
 ```
 *Note: This step performs family assignment, cross-system split (or fallback), and permutation tests.*

3. **Run Validation**:
 ```bash
 python code/validation.py --models results/models/ --output results/validation/
 ```
 *Note: This step computes VIF, threshold sensitivity, and checks power status.*

4. **Generate Reports**:
 ```bash
 python code/generate_report.py --validation results/validation/ --output results/reports/
 ```

## Testing

Run unit and integration tests:
```bash
pytest tests/ -v --cov=code
```

Run contract tests:
```bash
pytest tests/contract/ -v
```

## Expected Outputs

- `data/processed/descriptors.csv`: Computed thermodynamic descriptors.
- `results/models/*.pkl`: Trained model artifacts.
- `results/validation/*.json`: VIF scores, threshold sensitivity tables, permutation test results.
- `results/reports/*.json`: Final performance and validation reports (with power status and provenance notes).
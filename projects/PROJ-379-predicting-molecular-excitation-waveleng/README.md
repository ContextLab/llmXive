# Predicting Molecular Excitation Wavelengths with Graph Neural Networks

This project implements an automated pipeline to predict molecular excitation wavelengths (λmax) from SMILES strings using Graph Neural Networks (GNNs). The pipeline ingests real UV-Vis spectral data, processes molecular graphs, trains models, and evaluates performance against scientific success criteria.

## Project Structure

```
projects/PROJ-379-predicting-molecular-excitation-waveleng/
├── code/ # Python implementation modules
├── data/
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Cleaned and split data
├── tests/ # Test suites
├── docs/ # Documentation
├── state/ # Artifact state tracking
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Quickstart

### 1. Environment Setup

Create and activate a Python virtual environment:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Data Fetching

The pipeline fetches real UV-Vis data from PubChem or SDBS. If these primary sources fail, it attempts to load from the Hugging Face dataset `zjunlp/UV-Vis-ML`.

Run the ingestion script:

```bash
python code/ingest.py
```

This will:
- Fetch raw data from primary sources (PubChem/SDBS)
- Validate the presence of `lambda_max_exp` column
- Parse SMILES and validate with RDKit
- Save cleaned data to `data/processed/cleaned.csv`

**Note**: The pipeline will fail loudly if real data cannot be fetched. No synthetic data fallbacks are permitted.

### 3. Running the Pipeline End-to-End

Execute the full pipeline in order:

```bash
# 1. Ingest and clean data
python code/ingest.py

# 2. Validate data
python code/validate_data.py

# 3. Generate scaffold splits
python code/split.py

# 4. Merge data with splits
python code/merge_split.py

# 5. Train models
python code/train.py

# 6. Evaluate results
python code/evaluate.py

# 7. Perform collinearity checks
python code/collinearity_check.py

# 8. Generate explanations
python code/explain.py

# 9. Run sensitivity analysis
python code/sensitivity.py

# 10. Aggregate final results
python code/analyze_results.py
```

### 4. Verifying Results

After running the pipeline, check the following artifacts:

- `data/processed/cleaned.csv`: Cleaned molecule data
- `data/processed/split_indices.json`: Train/val/test split indices
- `data/processed/train_val_test.csv`: Merged dataset with splits
- `model.pt`: Trained GNN model
- `data/processed/metrics_partial.json`: Evaluation metrics
- `data/processed/metrics.json`: Final aggregated results

The `metrics.json` file contains the success criteria status:
- `sc001_status`: "PASS" if MAE < 30 nm and p < 0.05, otherwise "FAIL"
- `power_status`: Whether test set size meets n ≥ 50 requirement

### 5. Running Tests

Run the test suite:

```bash
pytest tests/ -v
```

### 6. Linting and Formatting

Format code with Black:

```bash
python code/cleanup_linter.py --format
```

Check for linting errors:

```bash
python code/cleanup_linter.py --lint
```

## Success Criteria

- **SC-001**: Model achieves MAE < 30 nm with statistical significance (p < 0.05)
- **SC-002**: Pipeline completes within 6 hours on CPU-only hardware
- **SC-003**: Test set size n ≥ 50 for adequate statistical power
- **SC-004**: Sensitivity analysis performed across MAE thresholds (20, 30, 40, 50, 60 nm)

## Data Sources

- **Primary**: PubChem (via `pubchempy`) and SDBS (via official FTP)
- **Secondary**: Hugging Face dataset `zjunlp/UV-Vis-ML`
- **Validation**: All data sources are verified for `lambda_max_exp` column presence

## License

This project is part of the llmXive automated science pipeline.
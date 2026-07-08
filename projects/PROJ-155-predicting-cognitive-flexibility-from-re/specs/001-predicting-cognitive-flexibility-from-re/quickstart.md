# Quickstart: Predicting Cognitive Flexibility from Resting‑State Functional Connectivity Variability

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to GitHub Actions (for CI execution) or a local environment with sufficient RAM.
- **Verified Data Access**: Ensure the HCP large-scale subject release is accessible via the verified URLs. If not, the pipeline will halt.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd <project-dir>
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

### 1. Data Ingestion & Preprocessing
Run the data download and preprocessing script. This will attempt to fetch data from the verified sources and perform parcellation.
```bash
python code/main.py --stage download_preprocess
```
*Note: If the verified URLs do not contain the required raw fMRI data, this step will log a "Data Gap" error and halt execution. No synthetic data will be generated.*

### 2. Feature Extraction
Compute sliding-window connectivity metrics and PCA reduction.
```bash
python code/main.py --stage features
```

### 3. Statistical Analysis
Run the regression and permutation test.
```bash
python code/main.py --stage analysis
```

### 4. Validation
Run contract tests to ensure data integrity.
```bash
pytest tests/test_contracts.py
```

## Output

- **Exclusion Log**: `data/processed/exclusion_log.csv` (Subject counts, SC-001).
- **Final Results**: `data/processed/final_results.csv` (Subject-level results, FR-007).
- **Regression Summary**: `data/results/regression_summary.json` (P-value, Significance, SC-003, SC-004).
- **Plots**: `data/results/variability_vs_flexibility.png`

## Troubleshooting

- **Memory Error**: Reduce batch size in `code/config.py` (e.g., `BATCH_SIZE = 20`).
- **Missing Data**: Check logs in `data/logs/download.log` to see if verified URLs were invalid. If so, the project has halted.
- **Runtime Error**: If permutation test is too slow, set `PERMUTATIONS = 5000` in `code/config.py`.

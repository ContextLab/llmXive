# Quickstart: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local environment for testing)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-367-the-influence-of-algorithmic-recommendat
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

### 1. Data Fetching
Fetch the OULAD dataset (or a verified subset):
```bash
python code/data_fetcher.py
```
*Output*: `data/raw/validated_oulad.parquet` (or `.csv`)

### 2. Preprocessing
Calculate diversity scores, merge categories, and derive baseline vectors:
```bash
python code/preprocessing.py
```
*Output*: `data/processed/cleaned_data.parquet`, `data/processed/diversity_scores.json`

### 3. Modeling
Fit the weighted regression and calculate propensity scores:
```bash
python code/modeling.py
```
*Output*: `data/processed/model_results.csv`

### 4. Robustness Analysis
Run permutation tests and sensitivity analysis:
```bash
python code/robustness.py
```
*Output*: `data/processed/sensitivity_analysis.csv`, `data/processed/permutation_test_results.json`

### 5. Full Orchestration
Run the entire pipeline end-to-end:
```bash
python code/main.py
```

## Testing

Run unit tests:
```bash
pytest tests/unit/ -v
```

Run integration tests:
```bash
pytest tests/integration/ -v
```

Run contract tests (schema validation):
```bash
pytest tests/contract/ -v
```

## Expected Outputs

- `data/processed/diversity_scores.json`: Contains entropy scores for each session.
- `data/processed/model_results.csv`: Contains regression coefficients, p-values, and weights.
- `data/processed/sensitivity_analysis.csv`: Contains results for thresholds {0.01, 0.05, 0.1}.
- `docs/reports/analysis_report.md`: Final summary of findings (associational only).

## Troubleshooting

- **Missing Columns**: If `DataSchemaError` is raised, ensure the input dataset has `recommended_categories` and `enrolled_categories` (or mapped equivalents).
- **Small Sample**: If N < 30, the pipeline automatically switches to GLS. Check logs for the methodological change.
- **Extreme Weights**: If weights > 10x median, a warning is logged, and the effective sample size is reported.
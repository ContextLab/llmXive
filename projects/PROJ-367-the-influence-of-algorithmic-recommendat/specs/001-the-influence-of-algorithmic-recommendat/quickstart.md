# Quickstart: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to the verified Hugging Face datasets (or a local mock dataset).

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

### 1. Data Ingestion & Processing
Run the main script to ingest data, calculate diversity scores, and perform PSW.

```bash
python code/main.py --data <path-to-data> --output data/processed/results.json
```

- If `--data` is not provided, the script will attempt to load the verified Hugging Face datasets.
- If no verified dataset matches the schema, a synthetic dataset is generated for demonstration (with a fixed seed).

### 2. Robustness Analysis
The robustness analysis (Outcome Permutation Test and sensitivity sweep) is triggered automatically if the main pipeline succeeds.

```bash
python code/main.py --robustness
```

### 3. Unit Tests
Run the test suite to verify entropy calculations and pipeline logic.

```bash
pytest tests/
```

## Output

- `data/processed/results.json`: Contains the main regression results, weights, E-values, and diagnostics.
- `data/processed/sensitivity_analysis.csv`: Results of the threshold sweep.
- `data/processed/permutation_test.json`: Null distribution and p-value from the Outcome Permutation Test.
- `docs/reports/final_report.md`: A human-readable summary of the findings (generated automatically).

## Troubleshooting

- **DataSchemaError**: Raised if the input dataset lacks `recommended_categories` or `enrolled_categories`. Check the dataset schema.
- **VIF Warning**: If VIF > 5.0, the model flags collinearity. Review the `Baseline_Interest_Vector` construction.
- **Small Sample**: If unique users < 30, the model switches to GLS. Check the log for the methodological change.
- **Synthetic Data Warning**: If no verified real-world dataset is found, the pipeline will generate synthetic data. The results are a methodological demonstration, not an empirical finding about real-world behavior.

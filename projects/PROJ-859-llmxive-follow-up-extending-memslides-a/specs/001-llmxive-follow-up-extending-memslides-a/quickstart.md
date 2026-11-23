# Quickstart: llmXive Follow-up: Trace Compressibility Analysis

## Prerequisites

- Python 3.11+
- `pip` or `poetry`
- Access to a Linux environment (GitHub Actions runner or local Linux machine)

## Installation

1. **Clone the repository** and navigate to the project directory.
   ```bash
   git clone <repo-url>
   cd projects/PROJ-859-llmxive-follow-up-extending-memslides-a
   ```

2. **Install dependencies**.
   ```bash
   pip install -r requirements.txt
   # OR if using poetry
   poetry install
   ```

   *Note*: `requirements.txt` will be located at `code/requirements.txt`.

3. **Verify environment**.
   ```bash
   python -c "import sklearn; import pandas; import statsmodels; print('Environment OK')"
   ```

## Running the Pipeline

The pipeline is executed via the main entry point `code/main.py`.

### 1. Generate Synthetic Data
Generates [deferred] multi-turn revision sessions (Training and Held-Out sets).
```bash
python code/main.py --task generate --output data/raw/traces --seed 42 --count [deferred]
```

### 2. Validate Trace Integrity
Verifies `data/raw/logs/trace_integrity.log` exists and is valid.
```bash
python code/main.py --task validate_integrity --input data/raw/traces
```

### 3. Extract Metrics
Computes structural metrics for all generated traces.
```bash
python code/main.py --task extract --input data/raw/traces --output data/processed/metrics.csv
```

### 4. Train Rule Induction Model
Trains the Decision Tree model on the Training Set.
```bash
python code/main.py --task train --input data/processed/metrics.csv --split training --output data/processed/rules/model.json
```

### 5. Benchmark Agents
Runs the baseline and compressed agents on the Held-Out Set.
```bash
python code/main.py --task benchmark --rules data/processed/rules/model.json --test-set data/held_out/ --output data/processed/results/summary.json
```

### 6. Run Correlation Analysis
Performs Multiple Linear Regression on the Held-Out Set results.
```bash
python code/main.py --task analyze --input data/processed/results/summary.json --metrics data/processed/metrics.csv --output data/processed/statistical_analysis_results.json
```

### 7. Run Sensitivity Analysis
Sweeps the compression threshold.
```bash
python code/main.py --task sensitivity --rules data/processed/rules/model.json --output data/processed/sensitivity_report.json
```

### 8. Feasibility Gate
Measures runtime and memory usage.
```bash
python code/main.py --task feasibility --output data/processed/feasibility_report.json
```

### 9. Generate Final Report
Executes the fully implemented `code/evaluation/final_report_generator.py` to compile all artifacts into `data/processed/final_report.md`.
```bash
python code/main.py --task report --input data/processed/ --output data/processed/final_report.md
```

## Testing

Run the unit and integration tests to verify the implementation.
```bash
pytest tests/
```

## Troubleshooting

- **Memory Error**: If the dataset is too large, reduce `--count` in the generation step or enable streaming in `generator.py`.
- **Missing Data**: Ensure `data/raw/traces/` exists before running `extract`.
- **Schema Validation**: If `final_report_generator.py` fails, check that all intermediate files match the schemas in `contracts/`.
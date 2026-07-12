# Quickstart: llmXive follow-up: extending "Intern-Atlas"

## Prerequisites
- Python 3.11+
- `pip`
- Access to `intern-atlas-snapshot.graphml` and `retraction-watch-dump.csv` (must be placed in `data/raw/` for scientific analysis).

## Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Data Preparation
1. **CRITICAL**: Ensure `data/raw/intern-atlas-snapshot.graphml` exists for scientific analysis. If missing, the pipeline will **automatically generate synthetic data** for code validation only.
2. **CRITICAL**: Ensure `data/raw/retraction-watch-dump.csv` exists for scientific analysis. If missing, the pipeline will **automatically generate synthetic labels** for code validation only.
3. Run the extraction script:
   ```bash
   python code/data/extract_intern_atlas.py
   python code/data/merge_retractions.py
   python code/data/compute_features.py
   ```
   *Output*: `data/processed/features_2010_2018.csv`.

## Running the Analysis
1. Train models:
   ```bash
   python code/models/train_baseline.py
   python code/models/train_topological.py
   ```
2. Run robustness tests:
   ```bash
   python code/analysis/robustness_tests.py
   python code/analysis/sensitivity_analysis.py
   ```
3. View results:
   - Check `data/processed/model_results.json`.
   - Check `data/processed/plots/` for visualizations.

## Testing
```bash
pytest tests/
```
*Note: Unit tests use synthetic data to validate pipeline logic. Scientific analysis requires real data.*

## Troubleshooting
- **"Primary dataset not found"**: The Intern-Atlas graph is not in the verified dataset list. The pipeline will **automatically generate synthetic data** for code validation. **Scientific analysis aborted.**
- **"No retraction data found"**: The Retraction Watch database is missing. The pipeline will **automatically generate synthetic labels**. **Scientific analysis aborted.**
- **Memory Error**: Reduce the sample size in `code/utils/constants.py` or ensure the graph is filtered to 2010-2018 before processing.
- **Edge Type Error**: Check that `intern-atlas-snapshot.graphml` contains valid edge types (not LLM-inferred or retraction-linked).
- **"Validation set has too few positive cases"**: The stratified split failed to find enough retractions. The pipeline will report a limitation or abort.
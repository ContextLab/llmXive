# Quickstart Guide: Social Media Consumption and Cognitive Flexibility Pipeline

This guide provides step-by-step instructions to run the full analysis pipeline for the project: **The Impact of Social Media Consumption Patterns on Cognitive Flexibility**.

## Prerequisites

- Python 3.9+
- `pip` package manager
- Internet connection (to fetch real dataset)
- ~14 GB disk space (for raw and processed data)

## 1. Setup Environment

Navigate to the project root:

```bash
cd projects/PROJ-453-the-impact-of-social-media-consumption-p
```

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r code/requirements.txt
```

## 2. Verify Directory Structure

Ensure the following directories exist. If not, run the setup script:

```bash
python code/setup_directories.py
```

Expected structure:
- `data/raw/`
- `data/processed/`
- `code/`
- `results/models/`
- `results/figures/`
- `tests/`
- `contracts/`
- `logs/`

## 3. Data Feasibility Check (Phase 0)

Before downloading large datasets, verify that the required variables exist in the source.

```bash
python code/00_feasibility_check.py
```

**Expected Output:**
- `logs/feasibility_report.txt`: Confirmation of URL accessibility.
- `logs/schema_validation.log`: Confirmation that `switching_index` and `cognitive_flexibility_score` (or proxies) are present.
- If variables are missing, the script will exit with a "Data Gap" error.

## 4. Data Ingestion (User Story 1)

Download and process the raw data. This step handles HILDA, ESS, and AddHealth fallbacks.

```bash
python code/01_ingest.py
```

**Outputs:**
- `data/raw/`: Raw dataset files.
- `logs/ingest.log`: Detailed ingestion logs.

## 5. Variable Engineering (User Story 1)

Compute derived variables (e.g., `switching_index`) and clean the data.

```bash
python code/02_engineer.py
```

**Outputs:**
- `data/processed/participants_cleaned.csv`: The final analysis-ready dataset.
- `data/instrument_sources.yaml`: Documentation of variable sources.
- `logs/engineer.log`: Exclusion counts and processing details.

## 6. Associational Analysis & Model Fitting (User Story 2)

Fit the OLS regression model, calculate VIFs, and perform sensitivity analysis.

```bash
python code/03_model.py
```

**Outputs:**
- `results/models/regression_summary.json`: Coefficients, p-values, VIF scores, and diagnostics.
- `results/models/residualized_model.json`: (If collinearity > 0.7) Secondary model results.
- `results/sensitivity_comparison.csv`: Robustness check across operationalizations.
- `logs/collinearity_check.log`: Warning if mathematical coupling is detected.
- `logs/memory_profile.log`: Peak memory usage during model fitting.

**Note:** The pipeline automatically validates the output against `contracts/output.schema.yaml` and scans for forbidden causal language. If causal terms are detected, the run will fail.

## 7. Visualization (User Story 3)

Generate publication-ready plots and the final report.

```bash
python code/04_visualize.py
```

**Outputs:**
- `results/figures/regression_plot.png`
- `results/figures/stratified_plot.png`
- `results/figures/sensitivity_table.png`
- `results/final_report.json`: Merged model summary and textual interpretation.

## 8. Running Tests

To verify the pipeline integrity:

```bash
pytest tests/ -v
```

Key test files:
- `tests/contract/test_dataset_schema.py`: Validates data against schema.
- `tests/unit/test_vif.py`: Verifies VIF calculation.
- `tests/unit/test_causal_language.py`: Ensures no causal language leaks.

## Troubleshooting

- **Data Gap Error**: If `00_feasibility_check.py` fails, the required variables are not in the target dataset. The project cannot proceed without valid data.
- **Memory Errors**: If the dataset is too large, ensure `streaming=True` is used in `01_ingest.py` (implemented via `datasets.load_dataset`).
- **Collinearity Warning**: If `switching_index` and `total_screen_time` are highly correlated (>0.7), the pipeline automatically switches to a residualized model. Check `results/models/residualized_model.json` for these results.

## Citation

When using results from this pipeline, please reference the `data/instrument_sources.yaml` for specific survey citations and validation sources.
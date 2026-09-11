# Quick Start Guide: Predicting Plant Root Architecture from Soil Nutrient Profiles

This guide provides the steps to set up the environment, run the data ingestion pipeline, train the predictive models, and generate the final sensitivity analysis report.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Access to the internet (for downloading data and packages)

## 1. Setup Directory Structure

The project requires a specific directory structure for data, code, and artifacts. Run the setup script to create these directories automatically.

```bash
cd code
python setup_dirs.py
```

This will create:
- `data/` (raw, processed, logs)
- `code/`
- `tests/`
- `artifacts/`
- `figures/`

## 2. Install Dependencies

Install the required Python packages using the provided `requirements.txt` file.

```bash
pip install -r code/requirements.txt
```

## 3. Configure Environment

Ensure the `.env` file is present in the project root (or `code/` depending on configuration).
If not present, run:

```bash
python code/setup_env.py
```

This creates a default `.env` file. Verify that any required API keys (if applicable for data sources) are set.

## 4. Run Data Ingestion Pipeline (User Story 1)

Execute the ingestion pipeline to fetch soil data, load trait data, merge them, and validate the dataset.

```bash
# Set run mode (production or test)
export RUN_MODE=production

# Step 1: Load and process soil data
python code/ingestion/soil_data.py

# Step 2: Load and validate trait data
python code/ingestion/trait_data.py

# Step 3: Merge datasets
python code/ingestion/merge.py

# Step 4: Validate data quality
python code/ingestion/validation.py

# Step 5: Generate exclusion summaries
python code/ingestion/generate_outputs.py
```

**Note**: In `production` mode, the pipeline will fail if real data cannot be fetched. In `test` mode, it will use synthetic data for structural validation.

## 5. Train Predictive Models (User Story 2)

Train the Random Forest models using Leave-One-Species-Out (LOSO) cross-validation.

```bash
# Train Model A (Soil-Only) and Model B (Soil+Species)
python code/modeling/train.py

# Calculate baseline metrics
python code/modeling/baseline.py

# Run permutation tests
python code/modeling/train.py --permutation

# Validate SC-002 compliance
python code/modeling/sc002_validator.py

# Generate final metrics JSON
python code/modeling/generate_metrics.py

# Generate feature importance plots
python code/modeling/generate_feature_plot.py
```

## 6. Perform Sensitivity Analysis (User Story 3)

Analyze the stability of feature importance rankings across different p-value thresholds.

```bash
python code/modeling/sensitivity.py
```

This generates the `artifacts/sensitivity_report.md` containing the threshold stability table and justification.

## 7. Verify Outputs

After running the full pipeline, verify that the following artifacts exist:

- `data/processed/merged_dataset.csv`
- `artifacts/model_metrics.json`
- `artifacts/feature_importance.csv`
- `figures/feature_importance.png`
- `artifacts/sensitivity_report.md`

## Troubleshooting

- **Data Fetch Errors**: If the pipeline fails in production mode, check your internet connection and the availability of the data sources listed in `specs/001-predict-root-architecture/research.md`.
- **Import Errors**: Ensure all dependencies are installed and the Python path includes the `code/` directory.
- **Checksum Failures**: If checksum verification fails, re-run `code/ingestion/soil_data.py` to regenerate the data and checksum files.

## Research & Citations

For detailed information on the data sources, significance levels, and methodology, refer to:
- `specs/001-predict-root-architecture/research.md`
- `artifacts/sensitivity_report.md`

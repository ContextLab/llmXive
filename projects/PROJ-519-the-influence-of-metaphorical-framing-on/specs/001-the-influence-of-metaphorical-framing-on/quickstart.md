# Quickstart: The Influence of Metaphorical Framing on Attitudes Towards Mental Health Treatment

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to a GitHub Actions runner (or local machine for development)

## Installation

1. **Clone the repository** and navigate to the project directory.
   ```bash
   git clone <repo-url>
   cd projects/PROJ-519-the-influence-of-metaphorical-framing-on
   ```

2. **Create a virtual environment** and install dependencies.
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

The pipeline consists of three main stages: Data Generation/Simulation, Analysis, and Visualization.

### Step 1: Generate/Simulate Data
Run the simulation script to generate experimental data and the fallback discourse corpus.
```bash
python code/src/data_ingestion.py --mode simulate --seed 42
```
*Output*: `data/processed/experimental_data.csv`, `data/processed/discourse_data.csv`.

### Step 2: Run Statistical Analysis
Execute the statistical modeling scripts.
```bash
# Run ANOVA on experimental data
python code/src/statistical_modeling.py --analysis anova --input data/processed/experimental_data.csv

# Run Robust Regression on discourse data (includes stress test)
python code/src/statistical_modeling.py --analysis regression --input data/processed/discourse_data.csv
```
*Output*: `data/derived/anova_results.json`, `data/derived/regression_results.json`.

### Step 3: Generate Visualizations
Create the required plots.
```bash
python code/src/visualization.py --type anova --output data/derived/figures/
python code/src/visualization.py --type regression --output data/derived/figures/
```
*Output*: `data/derived/figures/anova_bar_chart.png`, `data/derived/figures/regression_scatter.png`.

## Verification

Run the test suite to ensure all components work as expected.
```bash
pytest code/tests/ -v
```

## Troubleshooting

- **Memory Error**: If processing the discourse data fails, ensure the `--sample-size` flag is used to limit the dataset size.
- **Missing Dependencies**: Re-run `pip install -r code/requirements.txt` if `ModuleNotFoundError` occurs.
- **Data Checksum Mismatch**: If `state/...yaml` reports a checksum mismatch, re-run the data generation step to ensure consistency.
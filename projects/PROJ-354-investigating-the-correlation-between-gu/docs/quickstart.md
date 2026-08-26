# Quickstart Guide: Gut Microbiome-Cognitive Correlation Study

This guide provides step-by-step instructions to run the entire analysis pipeline
from raw data download to final report generation.

## Prerequisites

- Python 3.10+
- UK Biobank Access Token (set in environment or `.env` file)
- Sufficient disk space (~20GB for raw and processed data)
- RAM: 7GB+ (streaming enabled for larger datasets)

## 1. Setup Environment

```bash
# Clone repository
git clone <repo-url>
cd PROJ-354-investigating-the-correlation-between-gu

# Install dependencies
pip install -r requirements.txt

# Configure credentials
# Option A: Create.env file
echo "UK_BIOBANK_TOKEN=your_token_here" >.env

# Option B: Set environment variable
export UK_BIOBANK_TOKEN="your_token_here"
```

## 2. Run the Pipeline

The pipeline is designed to be run sequentially. You can execute the full
validation script which runs all steps and verifies outputs.

```bash
# Run the full validation pipeline (T035)
python code/validate_quickstart.py
```

Alternatively, run individual stages manually:

### Step 2.1: Download Data
Fetches raw microbiome and cognitive data from UK Biobank.
```bash
python code/download.py
```
*Outputs*: `data/raw/microbiome_raw.parquet`, `data/raw/cognitive_raw.parquet`

### Step 2.2: Preprocess Data
Filters cohort, handles zeros, and applies ILR transformation.
```bash
python code/preprocess.py
```
*Outputs*: `data/processed/ilr_coordinates.parquet`, `data/processed/cohort_retention_log.json`

### Step 2.3: Statistical Analysis
Fits Lasso/Ridge models and applies Benjamini-Hochberg correction.
```bash
python code/analysis.py
```
*Outputs*: `results/associations/main_effects.parquet`, `results/associations/interaction_effects.parquet`

### Step 2.4: Visualization
Generates Manhattan plots and sensitivity reports.
```bash
python code/visualize.py
```
*Outputs*: `results/plots/manhattan_plot.png`, `results/sensitivity/threshold_sweep_report.json`

## 3. Verify Results

After completion, check the validation report:
```bash
cat results/validation_quickstart_report.json
```

Expected outputs:
- `results/associations/main_effects.parquet`: Contains taxon-cognitive associations.
- `results/plots/manhattan_plot.png`: Visual summary of significant taxa.
- `results/validation_quickstart_report.json`: End-to-end validation status.

## Troubleshooting

- **Missing Token**: Ensure `UK_BIOBANK_TOKEN` is set in `.env` or environment.
- **Memory Errors**: The pipeline uses streaming by default. If issues persist, reduce batch size in `config.py`.
- **Zero Replacement**: Ensure `zCompositions` is installed if zero-replacement fails.

## Next Steps

- Review `results/sensitivity/over_control_report.json` for bias analysis.
- Check `results/sensitivity/model_selection_report.json` for Lasso vs Ridge comparison.
- Explore `results/validation/instrument_citation_report.md` for instrument validation details.

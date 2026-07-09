# Quickstart: Predicting Plant Drought Tolerance from RSA Data

## Prerequisites

- Python 3.11+
- pip
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-464-predicting-plant-drought-tolerance-from-
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

The pipeline is executed via a single entry point script.

1. **Run the full pipeline**:
   ```bash
   python code/run_pipeline.py
   ```
   This script will:
   - Download data from verified sources (MGB3, TRY).
   - Extract RSA metrics.
   - Merge and clean data.
   - Run PCA, PGLS/PVR, Regression, and Classification.
   - Perform sensitivity analysis.
   - Generate reports in `results/reports/`.

2. **Run specific modules** (for debugging):
   ```bash
   # Extract RSA metrics only
   python code/extract_rsa.py --input data/raw/mgb3.parquet --output data/derived/rsametrics.csv

   # Run statistical analysis
   python code/analysis.py --input data/derived/merged_data.csv --output results/analysis_results.json
   ```

## Verifying Results

1. **Check Data Integrity**:
   ```bash
   python tests/contract/test_schemas.py
   ```
   This validates that all output CSVs match the defined schemas in `contracts/`.

2. **Review Reports**:
   Open `results/reports/final_report.md` for the complete analysis, including correlation matrices, model performance, and sensitivity curves.

## Troubleshooting

- **Memory Error**: If you encounter a MemoryError, ensure you are not running other heavy processes. The pipeline is designed for moderate RAM requirements.; if the dataset is too large, it will automatically sample.
- **Phylogenetic Tree Fetch Failed**: If the PGLS tree fetch fails, the pipeline will automatically switch to PVR. Check `results/logs/pipeline.log` for details.
- **No Species Overlap**: If the pipeline halts with "No species overlap," verify that the MGB3 and TRY datasets contain matching species names.

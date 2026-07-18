# Quickstart Guide: Molecular Complexity vs. Degradation Rates

This guide walks you through setting up and running the full pipeline to explore the correlation between molecular complexity and degradation rates in FDA-approved pharmaceuticals.

## Prerequisites

- Python 3.9+
- pip (Python package manager)
- Access to the HuggingFace datasets library (for fetching FDA drug data)

## Installation

1. **Clone the repository** (if not already done):
 ```bash
 git clone <repository-url>
 cd PROJ-071-exploring-the-correlation-between-molecu
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 The `requirements.txt` includes:
 - `rdkit`: For molecular descriptor calculation
 - `pandas`, `numpy`: For data manipulation
 - `scikit-learn`: For regression modeling
 - `matplotlib`, `seaborn`: For visualization
 - `pyyaml`, `requests`, `datasets`: For configuration and data fetching

## Data Setup

The pipeline requires a specific directory structure. Run the setup script to create it:

```bash
python code/setup_data.py
```

This creates:
- `data/raw/`: For raw downloaded data
- `data/processed/`: For cleaned and merged datasets
- `data/output_schema.yaml`: Defines the expected output format

## Running the Pipeline

The pipeline is executed in three main stages, corresponding to the User Stories. You can run them individually or all at once.

### Stage 1: Data Ingestion & Descriptor Calculation (US1)

Fetches FDA-approved drug structures, validates degradation data availability, and calculates molecular descriptors.

```bash
python code/ingest.py
```

**Outputs**:
- `data/processed/merged_drugs.csv`: Combined structural and degradation data.
- `data/checksums.txt`: Integrity checksums for the dataset.
- `data/errors.log`: Logs of any molecules with invalid SMILES or valence issues.
- `data_insufficiency_report.md`: Generated if data availability checks fail (N < 30).

### Stage 2: Standardization & Correlation Analysis (US2)

Standardizes degradation units (half-lives), normalizes for temperature/pH if possible, and performs statistical analysis.

```bash
python code/standardize.py
python code/analysis.py
```

**Outputs**:
- `data/processed/analysis_results.json`: Contains correlation matrices, regression coefficients, p-values, and R² scores.
- `data/processed/sensitivity_analysis.json`: Results of threshold sensitivity sweeps.

### Stage 3: Visualization & Reporting (US3)

Generates diagnostic plots and a comprehensive reproducibility report.

```bash
python code/viz.py
python code/report.py
```

**Outputs**:
- `data/outputs/scatter_tpsa_vs_half_life.png`: Scatter plots with regression lines.
- `data/outputs/residuals.png`, `data/outputs/qq_plot.png`: Residual diagnostic plots.
- `results_report.md`: Final report summarizing methodology, results, and reproducibility metadata (package versions, dataset hashes).

## Verifying Results

To ensure all outputs were generated correctly and match the expected schema:

```bash
python code/verify_outputs.py
```

This script checks for the existence and non-zero size of all required files listed in `data/output_schema.yaml`.

## Troubleshooting

- **Missing Data**: If the pipeline stops with a `DataIngestionError`, check `data_insufficiency_report.md` to see if the degradation data was missing or insufficient (N < 30).
- **Valence Errors**: Molecules with non-standard valence are skipped and logged to `data/errors.log`. Review this file if many molecules are excluded.
- **Missing Dependencies**: Ensure all packages in `requirements.txt` are installed. The pipeline relies heavily on `rdkit` and `scikit-learn`.
- **Logging**: Detailed logs are written to `logs/pipeline.log` (configured in `code/logging_config.py`). Check this file for stack traces on unexpected failures.

## Next Steps

- **Explore the Code**: The modular design allows you to inspect `code/descriptors.py`, `code/analysis.py`, and `code/viz.py` to understand the specific algorithms used.
- **Customize**: Modify `data/output_schema.yaml` or the analysis parameters in `code/analysis.py` to test different hypotheses.
- **Contribute**: See `CONTRIBUTING.md` for guidelines on adding new user stories or improving existing ones.

# Quickstart: Investigating the Correlation Between Gut Microbiome Composition and Sleep Architecture

## Prerequisites

- Python 3.11+
- A dataset containing metagenomic counts and sleep metrics (CSV/TSV).
- (Optional) A HuggingFace account if using a gated dataset.

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Data Preparation

Place your dataset in `data/raw/`. The file must be a CSV or TSV with the following columns:
- `subject_id` (unique identifier)
- One or more columns for microbial taxa (e.g., `Bacteroides`, `Firmicutes`)
- One or more columns for sleep metrics (e.g., `REM_duration`, `SWS_duration`)

*Note: If you do not have a real dataset, the system can generate synthetic data for testing using the `--synthetic` flag.*

## Running the Pipeline

### Full Analysis (Real or Synthetic Data)

```bash
python code/main.py --input data/raw/your_dataset.csv --output data/results/
```

### Synthetic Data Mode (Testing Only)

```bash
python code/main.py --synthetic --output data/results/synthetic_test/
```

### Validation Only

```bash
python code/main.py --validate-only --input data/raw/your_dataset.csv
```

## Output

The pipeline will generate the following artifacts in `data/results/`:
- `correlation_results.csv`: Full list of correlations with adjusted p-values.
- `diagnostics.json`: Collinearity, VIF, and power analysis results.
- `report.md`: Human-readable summary with associational framing.
- `validation_report.json`: Success/failure status of data ingestion.

## Troubleshooting

- **Dataset-variable fit check failed**: Ensure all required columns (taxa and sleep metrics) are present in the input file.
- **Underpowered**: The sample size is too small to detect the expected effect size (r ≥ 0.3). Consider collecting more data or acknowledging the limitation in the report.
- **Perfect Multicollinearity**: Two or more taxa are linearly dependent. The system will flag these and exclude them from VIF calculation.

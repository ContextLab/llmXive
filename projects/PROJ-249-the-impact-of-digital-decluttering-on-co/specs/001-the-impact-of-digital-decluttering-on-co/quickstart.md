# Quickstart: The Impact of Digital Decluttering on Cognitive Performance and Well-being

## Prerequisites

-   Python 3.11+
-   `pip` or `venv`
-   Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-249-the-impact-of-digital-decluttering-on-co
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

### 1. Data Validation (FR-009, FR-010)
Run the validation script to check raw data integrity.
```bash
python code/validation/validate_raw_data.py --input data/raw/ --output data/processed/
```

### 2. Compliance Logging (FR-002)
Aggregate daily logs and calculate compliance scores.
```bash
python code/analysis/aggregate_compliance.py --input data/processed/compliance_logs.csv --output data/processed/compliance_summary.csv
```

### 3. Statistical Analysis (FR-005, FR-006, FR-007, FR-008)
Run the main analysis script.
```bash
python code/analysis/run_statistics.py --input data/processed/measurement_records.csv --output results/
```
*This script performs bootstrapping (10k resamples), calculates Cohen's d, and applies Holm-Bonferroni correction. It uses bootstrapping as the primary method regardless of normality.*

### 4. Visualization
Generate plots from the results.
```bash
python code/viz/generate_plots.py --input results/statistical_summary.json --output results/plots/
```

## Testing

Run the test suite to verify scoring logic and data contracts.
```bash
pytest tests/ -v
```

## Troubleshooting

-   **Missing Dependencies**: Ensure you are using Python 3.11.
-   **Data Validation Errors**: Check `data/processed/validation_report.csv` for flagged records (e.g., SART RT < 100ms).
-   **Bootstrapping Failure**: If the script fails to converge, check for empty groups in the data. The script will automatically fallback to Wilcoxon signed-rank in this specific case.
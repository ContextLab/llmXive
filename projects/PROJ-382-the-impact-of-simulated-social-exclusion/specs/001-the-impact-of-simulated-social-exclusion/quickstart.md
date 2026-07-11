# Quickstart: The Impact of Simulated Social Exclusion on Subsequent Prosocial Behavior

## Prerequisites
-   Python 3.11+
-   `pip`
-   Access to the internet (for OSF/HuggingFace download)

## Installation

1.  **Clone the repository** (or navigate to the project directory).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r projects/PROJ-382-the-impact-of-simulated-social-exclusion/code/requirements.txt
    ```

## Running the Pipeline

The pipeline is orchestrated via `main.py`. It handles ingestion, validation, analysis, and reporting.

```bash
cd projects/PROJ-382-the-impact-of-simulated-social-exclusion/code/
python main.py
```

### Configuration
The pipeline expects a configuration file `config.yaml` (generated or provided) containing the list of OSF URLs. If not provided, it defaults to the verified list and triggers the keyword search (FR-001.5).

## Output Artifacts

Upon successful completion, the following files are generated in `data/processed/`:
-   `standardized.csv`: Cleaned, unified dataset.
-   `results.csv`: Individual dataset analysis results.
-   `meta_analysis.json`: Pooled effect sizes and confidence intervals.
-   `sensitivity_report.json`: Stability metrics across link/distribution sweeps.
-   `power_report.txt`: Statistical power assessment.

## Troubleshooting

-   **"Insufficient Data"**: If fewer than 3 valid datasets are found, the script exits with code 1. Check the logs for skipped datasets.
-   **Model Convergence**: If ZIG fails, the script attempts Hurdle, then Logistic. Check `results.csv` for `model_type` fallbacks.
-   **RAM Error**: The pipeline processes datasets sequentially. If memory errors occur, reduce the batch size in `config.yaml` (if applicable) or ensure no other heavy processes are running.

# Quickstart: Predicting Alloy Phase Diagrams

## Prerequisites

- Python 3.11+
- Access to the verified SGTE dataset URL (internet required for initial download).
- GitHub Actions Free Tier (for CI execution).

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
    *Note: `requirements.txt` pins versions for reproducibility (Principle I).*

## Running the Pipeline

The pipeline is executed via the main entry point:

```bash
python code/main.py
```

### Steps Executed:
1.  **Data Ingestion**: Downloads/loads SGTE data, validates schema, filters for binary systems.
2.  **Descriptor Generation**: Computes atomic radius, electronegativity, VEC, etc.
3.  **Power Analysis**: Checks sample size sufficiency. Halts if `INSUFFICIENT_POWER`.
4.  **Model Training**: Performs LOSO Cross-Validation with Random Forest.
5.  **Evaluation**: Calculates MAE, R², and compares to null baseline.
6.  **Visualization**: Generates phase diagram plots for representative systems.

## Output Artifacts

Upon successful completion, the following artifacts are generated in `artifacts/`:

- `model.pkl`: Trained Random Forest model.
- `metrics.json`: Detailed performance metrics per fold.
- `phase_diagram_*.png`: Visual comparisons of predicted vs. experimental boundaries.
- `power_analysis.json`: Statistical power justification.

## Troubleshooting

- **Error: `INVALID_DATA_SCHEMA`**: The dataset lacks required columns (temperature, composition). Check `data/raw/sgte_final.parquet`.
- **Error: `INSUFFICIENT_POWER`**: The dataset is too small for statistical significance.
- **Error: `API_RATE_LIMIT_EXCEEDED`**: Network failure after 3 retries. Ensure internet connectivity or use local fallback CSV.
- **Error: `LOW_DATA_DENSITY`**: A specific system has < 5 data points or high error variance.

# Quickstart: Memory Load‑Adaptive Text Presentation

## Prerequisites

- Python +
- Git
- Access to a GitHub Actions runner (or local environment with GB+ RAM)

## Installation

1.  **Clone the repository** (if applicable) or navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # venv\Scripts\activate   # Windows
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` will pin `statsmodels`, `pandas`, `numpy`, `scipy`, `pyarrow`, `openneuro-py`.*

## Data Setup

The pipeline downloads data programmatically. Ensure you have an internet connection.

1.  **Run the data download script**:
    ```bash
    python code/main.py --step download
    ```
    This will fetch the `ds004041` parquet file from the verified HuggingFace source and store it in `data/raw/`. It will also generate a checksum in `data/metadata.yaml`.

2.  **Verify data integrity**:
    Check `data/metadata.yaml` for the recorded checksum.

## Execution

Run the full pipeline:

```bash
python code/main.py --step full
```

This executes:
1.  **Preprocessing**: Filters, baseline correction, blink removal.
2.  **CLI Calculation**: Z-scores and thresholding.
3.  **Aggregation**: Computes `proportion_high_load` (High Load Exposure).
4.  **Analysis**: Fits LME, runs permutation test, sensitivity analysis.
5.  **Reporting**: Writes results to `results/`.

## Output

- `results/model_summary.csv`: Contains β coefficients, CIs, and p-values for the LME model.
- `results/permutation_pvalue.csv`: Empirical p-value from a large-scale permutation test.
- `results/sensitivity_analysis.csv`: Results for thresholds 0.5, 0.7 SD.

## Testing

Run the test suite:

```bash
pytest tests/
```

This validates:
- CLI calculation logic against known synthetic data.
- Aggregation logic (high load -> proportion).
- Statistical output format.
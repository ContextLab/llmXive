# Quickstart: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Prerequisites

- Python 3.11+
- `pip`
- Access to a terminal with internet connectivity (for data extraction).

## Installation

1.  **Clone the repository** and navigate to the project directory.
    ```bash
    git clone <repo-url>
    cd projects/PROJ-420-predicting-the-effect-of-alloying-on-the
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
    *Note: `requirements.txt` will include `pandas`, `scikit-learn`, `numpy`, `requests`, `pyyaml`, `joblib`.*

## Data Extraction (Manual Step)

*Note: The automated script will attempt to fetch data. If the public APIs are restricted, you may need to download a sample dataset manually and place it in `data/raw`.*

1.  Run the extraction script:
    ```bash
    python code/data_extraction.py
    ```
    This will attempt to query Materials Project and NIST.
    - **Success**: `data/raw/raw_data.json` (or similar) is created.
    - **Failure**: An error message is printed. Check the "Verified datasets" status.

## Running the Pipeline

Execute the full pipeline (Cleaning, Modeling, Analysis) with a single command:

```bash
python code/data_cleaning.py && python code/modeling.py && python code/analysis.py
```

Alternatively, run the master script if provided:
```bash
python code/run_pipeline.py
```

## Expected Outputs

After successful execution, the following files will be generated in `data/processed/`:

- `cleaned_records.parquet`: The filtered and normalized dataset.
- `ilr_features.parquet`: The ILR-transformed features.
- `model_metrics.json`: Contains `cv_mae`, `test_mae`, and `random_seed`.
- `diagnostics.json`: Contains VIF scores for each element.
- `feature_importance.json`: Ranked list of alloying elements.

## Verification

1.  **Check Data Integrity**:
    ```bash
    python -c "import pandas as pd; df = pd.read_parquet('data/processed/cleaned_records.parquet'); print(f'Rows: {len(df)}'); print(df.head())"
    ```
2.  **Verify Associational Framing**:
    Open `docs/results.md` (or the generated report) and ensure the text "associational (not causal)" appears in the conclusion.

## Troubleshooting

- **Error: "No data found"**: The public APIs for Materials Project or NIST may not have returned the specific aluminum alloy data with Poisson's ratio. Check the logs in `data/raw/` for the raw response.
- **Error: "Sum of elements < 0.95"**: This is expected behavior. The script excludes incomplete entries.
- **Memory Error**: Unlikely with this dataset size, but ensure no other heavy processes are running.

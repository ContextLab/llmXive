# Quickstart: Predicting Yield Strength of BCC Alloys

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to the MPEA database (DOI: 10.1038/s41597-020-00768-9) or a verified BCC dataset.

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-525-predicting-the-yield-strength-of-bcc-all
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Download Data**:
    - Manually download the MPEA database (or verified BCC dataset) and place it in `data/raw/mpea_raw.csv`.
    - Ensure the file contains columns: `system_id`, `elemental_composition`, `yield_strength`, `crystal_structure`.
    - Run the checksum verification (if provided):
      ```bash
      python code/utils.py --verify data/raw/mpea_raw.csv
      ```

## Running the Pipeline

Execute the full pipeline from data ingestion to model evaluation:

```bash
python code/main.py
```

### Expected Output

- `data/processed/filtered_bcc.csv`: Cleaned dataset.
- `data/processed/descriptors.csv`: Feature-engineered dataset.
- `data/processed/model_results.json`: Performance metrics and confidence intervals.
- `data/logs/rejected_entries.log`: List of excluded alloys and reasons.

## Testing

Run the unit tests to verify feature engineering accuracy:

```bash
pytest tests/unit/test_feature_engineering.py -v
```

Run the integration test to verify the full pipeline:

```bash
pytest tests/integration/test_pipeline.py -v
```

## Troubleshooting

- **Error: "DATA_SCARCITY: Insufficient BCC alloys (N < 80)"**: The filtered dataset has fewer than 80 entries. Verify the source data or the filtering logic.
- **Error: "Missing Element Reference"**: An element in the composition is not found in the periodic table reference. Check for typos in the data.
- **Error: "Math Domain Error"**: A mixing entropy calculation encountered a log of zero. The script will log the alloy ID and assign 0.0 or NaN.

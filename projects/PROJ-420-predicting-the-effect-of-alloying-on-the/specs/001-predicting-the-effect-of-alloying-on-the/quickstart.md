# Quickstart: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Prerequisites

- Python 3.11+
- `git`
- `pip`
- Access to the internet (to download OpenML dataset).

## Installation

1. **Clone the repository** (if applicable) or navigate to the project directory.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Data Preparation

1. **Run the download script**:
   ```bash
   python code/data/download.py
   ```
   - This script fetches an OpenML dataset.
   - It validates the schema and saves the raw data to `data/raw/`.
   - If the dataset is missing required fields, it will raise a `DataNotFoundError`.

2. **Verify data integrity**:
   ```bash
   python code/data/clean.py --check-only
   ```
   - This runs unit checks, filters the data, and checks for independence.
   - It outputs the count of valid records.

## Running the Pipeline

To execute the full analysis (Download → Clean → Train → Evaluate):

```bash
python code/main.py
```

This will:
1. Download raw data from OpenML 42347.
2. Filter and normalize the data (including independence check).
3. Apply ILR transformation.
4. Train the Random Forest model.
5. Compute cross-validation and test-set MAE.
6. Generate feature importance rankings (via Perturbation Analysis).
7. Save results to `results/metrics.json` and `results/feature_importance.json`.
8. Log peak memory usage and validate quickstart commands.

## Expected Output

- `data/processed/alloys_clean.parquet`: The filtered and normalized dataset.
- `models/rf_model.pkl`: The trained Random Forest model.
- `results/metrics.json`: Contains CV MAE, Test MAE, sample size, and memory usage.
- `results/feature_importance.json`: Ranked list of alloying elements with null model threshold and basis sensitivity flag.

## Troubleshooting

- **Error: DataNotFoundError**: The required dataset (OpenML 42347) is not found or does not contain the required fields. Please check `research.md` for the current data availability status.
- **Error: UnitMismatch**: The dataset contains elastic constants in inconsistent units. The script should handle this, but manual inspection of `data/raw/` may be required.
- **Error: SampleSizeLow**: The dataset contains a limited number of records. The model will train but results should be interpreted with caution.
- **Error: MemoryLimit**: Peak memory usage exceeded a significant threshold. The script should log this; if it occurs, reduce the dataset size or model complexity.

# Quickstart: Investigating the Relationship Between Stellar Flare Frequency and Exoplanet Atmospheric Retention

## Prerequisites

- Python 3.11+
- `pip`
- Internet access (for API calls)

## Installation

1. **Clone the repository** (or navigate to the project directory).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Execution

Run the full pipeline:

```bash
python code/main.py
```

This script will:
1. Fetch data from MAST and NASA Exoplanet Archive (with retry logic).
2. Filter and merge datasets.
3. Compute XUV flux and mass loss rates.
4. Perform partial Spearman correlation.
5. Generate plots and save results to `data/results/`.

## Verification

1. **Check Data**: Ensure `data/processed/filtered_m_dwarfs.csv` exists and has rows.
2. **Check Physics**: Run the unit test to verify mass loss formula:
   ```bash
   pytest tests/test_physics.py -v
   ```
3. **Check Results**: View `data/results/correlation_stats.json` for the correlation coefficient and p-value.

## Troubleshooting

- **API Rate Limits**: The script automatically implements exponential backoff. If it fails after 3 attempts, check your network or the API status.
- **Missing Data**: If no M-dwarfs with $\ge$10 flares are found, the script will log a warning and exit gracefully.
- **Memory**: The pipeline is optimized for < 7 GB RAM. If you encounter memory errors, reduce the dataset size in `code/config.py`.

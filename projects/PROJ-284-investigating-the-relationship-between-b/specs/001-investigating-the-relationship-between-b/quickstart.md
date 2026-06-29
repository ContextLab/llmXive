# Quickstart: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Sensorimotor Performance

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- HCP API credentials (optional, for raw data download; otherwise, the pipeline uses verified ICA-FIX parquet fallbacks).

## Installation

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r code/requirements.txt
   ```
3. (Optional) Set HCP credentials:
   ```bash
   export HCP_USERNAME="your_username"
   export HCP_PASSWORD="your_password"
   ```

## Running the Pipeline

### 1. Download and Preprocess Data (Fallback)
```bash
python code/main.py --step download_preprocess --subjects 50
```
*Note: The pipeline will prioritize verified preprocessed (ICA-FIX) data. Raw preprocessing is only attempted if ICA-FIX data is unavailable for a subject.*

### 2. Extract Network Metrics
```bash
python code/main.py --step extract_metrics
```

### 3. Run Correlation Analysis (with PCA/MANOVA and CI)
```bash
python code/main.py --step analyze
```

### 4. Generate Visualizations and Report
```bash
python code/main.py --step viz_report
```

## Output

- **Plots**: `output/plots/` (Scatter plots, network diagrams)
- **Results**: `output/results/correlations.csv`, `output/results/confidence_intervals.json`
- **Report**: `output/report/summary.md` (Includes Limitation Statement on proxy measure)

## Troubleshooting

- **Memory Error**: The pipeline automatically reduces batch size. If it fails, manually set `--batch-size 2` in the command.
- **Missing Data**: Subjects with missing behavioral data are skipped and logged.
- **API Errors**: If HCP API returns 403, the pipeline retries 3 times with exponential backoff before falling back to ICA-FIX parquet data.
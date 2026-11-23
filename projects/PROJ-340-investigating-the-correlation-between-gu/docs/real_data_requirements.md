# Real Data Requirements

## Overview
This project is designed to analyze **real** gut microbiome and sleep architecture data. Synthetic data is strictly for local validation and is **not** permitted for final results.

## Data Source Configuration
Data sources must be configured in `data/config/real_data_sources.yaml`.

### Required Fields
- `name`: Unique identifier for the dataset.
- `type`: Format (e.g., `csv`, `tsv`, `parquet`).
- `url`: Direct download link to the raw data file.
- `checksum`: SHA256 hash of the file (optional but recommended).

### Example Configuration
```yaml
sources:
 - name: "GutSleep_Cohort_2024"
 type: "csv"
 url: ""
 checksum: "sha256:a1b2c3d4..."
```

## Data Schema
The input data must contain the following columns (defined in `data/config/required_variables.yaml`):

### Predictors (Microbiome)
- Taxa abundance columns (e.g., `Bacteroides`, `Firmicutes`, etc.).
- Must be numeric.
- Must be compositional (sums to 1 or 100%).

### Outcomes (Sleep)
- Sleep metric columns (e.g., `rem_duration`, `sws_duration`, `sleep_efficiency`).
- Must be numeric.

## Fetching Mechanism
- The pipeline uses `code/ingest.py` to fetch data.
- If the URL is invalid or the file cannot be downloaded, the pipeline halts with `RealDataFetchError`.
- **No fallback**: The system will not generate synthetic data if the real fetch fails.

## Privacy & Ethics
- Ensure the dataset is publicly available or you have necessary permissions.
- Do not include PII (Personally Identifiable Information) in the dataset.
- Verify that the dataset's usage complies with its license.

## Troubleshooting Data Fetches
- **Error: 404 Not Found**: Check the URL in `real_data_sources.yaml`.
- **Error: SSL Certificate**: Ensure your environment has valid SSL certificates.
- **Error: Timeout**: Increase the timeout in `code/ingest.py` or use a faster connection.

# Quickstart: Investigating the Potential Benefits of Ecotourism in Regenerating Deforested Areas

## Prerequisites

- **Python**: 3.11+
- **USGS EarthExplorer Account**: Required for API access.
- **Dependencies**: Install from `code/requirements.txt`.

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-555-investigating-the-potential-benefits-of-/

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Configuration

1.  **USGS Credentials**: Set environment variables or create `code/.env`:
    ```bash
    USGS_USERNAME=your_username
    USGS_PASSWORD=your_password
    ```
2.  **Site List**: Ensure `data/ecotourism/site_list.csv` exists with the target coordinates.
    - **CRITICAL**: This file must include `designation_date` and `economic_source` columns.
    - **CRITICAL**: A corresponding `data/ecotourism/metadata.json` file must exist, containing `source_name`, `retrieval_date`, and `preprocessing_steps` for each site's economic data. **The pipeline will fail at the validation step if these are missing or if a site lacks a verified source.**

## Running the Pipeline

The pipeline is executed via the main entry point:

```bash
python code/main.py
```

### Steps Performed
1.  **Validate**: Checks `site_list.csv` and `metadata.json` for required citations and dates. **Excludes sites without verified sources.**
2.  **Download**: Fetches Landsat data for multiple sites (chunked).
3.  **Process**: Calculates NDVI, masks clouds, aligns climate data.
4.  **Detect**: Identifies deforestation events (NDVI drop ≥0.30).
5.  **Temporal Check**: Flags sites where designation occurred after deforestation.
6.  **Model**: Fits HNLMM, LMM, or HLM.
7.  **Sensitivity**: Sweeps revenue thresholds and proxy variables.
8.  **Report**: Generates `data/processed/final_report.csv` and plots.

## Validation

Run the test suite to verify the pipeline logic:

```bash
pytest tests/
```

### Expected Output
- `data/processed/ndvi_timeseries.parquet`
- `data/processed/events.csv`
- `data/processed/final_report.csv`
- Console output with model coefficients and sensitivity table.

## Troubleshooting

- **Memory Error**: The pipeline uses chunked processing. If you encounter OOM, reduce the `CHUNK_SIZE` in `code/config.py`.
- **API Auth Failed**: Verify USGS credentials in `.env`.
- **No Convergence**: Check `data/processed/events.csv` for `R_Squared` < 0.95. These sites will fall back to linear models or HLM.
- **Missing Metadata**: If the pipeline fails at startup, ensure `data/ecotourism/metadata.json` contains the required fields (`source_name`, `retrieval_date`, `preprocessing_steps`) for every site in `site_list.csv`.

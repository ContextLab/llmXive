# Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

## Project Overview

This project investigates the statistical relationship between solar wind composition (specifically ion ratios such as O/Fe, He/H, and C/O) and geomagnetic activity indices (Dst and Kp). The pipeline ingests data from ACE/WIND and NOAA sources, aligns temporal resolutions, derives coupling functions, performs multivariate regression analysis, and validates statistical significance through permutation tests.

## ⚠️ Critical Data Availability Notice

**Current Data Status: Synthetic**

Due to the unavailability of verified, programmatically-accessible real-world ACE SWICS (Solar Wind Ion Composition Spectrometer) and NOAA Dst/Kp archives within the execution environment, **all data currently processed by this pipeline is synthetic**.

- The ingestion modules (`code/ingestion/download_ace.py`, `code/ingestion/download_noaa.py`) are implemented to attempt real data fetches from CDAWeb and NOAA.
- **If these real fetches fail** (which is the current state), the pipeline automatically triggers the synthetic data generator (`code/ingestion/generate_synthetic_data.py`).
- **All output artifacts generated in this run are explicitly labeled as 'synthetic'**.
- **Scientific hypothesis testing is NOT possible with the current synthetic data.** The pipeline is currently in a validation state, ensuring the data processing, alignment, regression, and statistical testing logic functions correctly.
- When real data becomes available (e.g., via direct download or updated API access), the synthetic fallback can be disabled, and the pipeline will produce real scientific results.

**Action Required**: To transition to real data analysis, the user must:
1. Ensure network access to CDAWeb (ACE data) and NOAA (Dst/Kp indices) is available.
2. Verify authentication or API keys if required.
3. Update the configuration in `code/config.py` to point to the correct data paths or enable the real fetch mode.
4. Re-run the pipeline. The `main.py` script will automatically label outputs as 'real' or 'synthetic' based on the source.

## Project Structure

```
projects/PROJ-505-exploring-the-statistical-relationship-b/
├── code/
│ ├── __init__.py
│ ├── config.py # Configuration (paths, seeds, flags)
│ ├── main.py # Entry point for the full pipeline
│ ├── ingestion/
│ │ ├── __init__.py
│ │ ├── generate_synthetic_data.py # Synthetic data generator (fallback)
│ │ ├── download_ace.py # ACE SWICS data fetcher
│ │ ├── download_noaa.py # NOAA Dst/Kp fetcher
│ │ └── align.py # Temporal alignment and merging
│ ├── analysis/
│ │ ├── __init__.py
│ │ ├── coupling_functions.py # Derive Akasofu epsilon, Newell, etc.
│ │ ├── regression.py # Multivariate linear regression
│ │ ├── cross_validation.py # 5-fold cross-validation
│ │ ├── permutation_test.py # Block permutation significance test
│ │ └── sensitivity.py # Sensitivity analysis & FDR correction
│ └── utils/
│ ├── __init__.py
│ ├── io.py # Parquet/CSV I/O and checksums
│ ├── logging.py # Logging infrastructure
│ └── mkdirs.py # Directory creation utilities
├── data/
│ ├── raw/ # Raw downloaded data (if available)
│ ├── processed/ # Aligned, hourly median data
│ └── artifacts/ # Model results, JSON/CSV summaries
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
└── README.md
```

## Prerequisites

- Python 3.9+
- `pip` and `virtualenv` (recommended)
- Network access to CDAWeb and NOAA (for real data)

## Installation

1. Clone the repository and navigate to the project directory.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### Running the Full Pipeline

Execute the main script to run the entire pipeline from ingestion to final reporting:

```bash
python code/main.py
```

This will:
1. Attempt to download real ACE and NOAA data.
2. Fall back to synthetic data generation if real data is unavailable.
3. Align data to a regular hourly grid.
4. Compute coupling functions.
5. Run regression analysis (baseline vs. full model).
6. Perform cross-validation.
7. Execute block permutation tests for significance.
8. Run sensitivity analysis with FDR correction.
9. Generate summary artifacts in `data/artifacts/`.

### Running Individual Modules

- **Ingestion**:
 ```bash
 python code/ingestion/download_ace.py
 python code/ingestion/download_noaa.py
 python code/ingestion/align.py
 ```
- **Analysis**:
 ```bash
 python code/analysis/coupling_functions.py
 python code/analysis/regression.py
 python code/analysis/cross_validation.py
 python code/analysis/permutation_test.py
 python code/analysis/sensitivity.py
 ```

### Running Tests

```bash
pytest tests/ -v
```

## Output Artifacts

All results are saved to `data/artifacts/`:

- `regression_results.json`: Coefficients, p-values, VIF, and model metrics.
- `cross_validation_results.json`: Out-of-sample R² and ΔR².
- `permutation_results.json`: Null distributions and p-values.
- `sensitivity_results.json`: Threshold sweep and FDR-corrected significance.
- `summary_report.json`: Aggregated results with data source labeling ('real' or 'synthetic').

## Configuration

Edit `code/config.py` to adjust:
- `STUDY_START_DATE` / `STUDY_END_DATE`: Time range for analysis.
- `REAL_DATA_MODE`: Set to `True` to force real data fetch (will fail if unavailable).
- `SEED`: Random seed for reproducibility (used in synthetic generation).

## Limitations & Future Work

- **Data Source**: Currently relies on synthetic data due to API/Network constraints. Real data integration is a priority for Phase 2.
- **Instrument Transitions**: ACE SWICS vs. SWICS-2 calibration offsets are handled by treating them as separate cohorts if offsets are unavailable.
- **Memory**: The alignment step includes a memory check (>6GB warning). Chunked processing for larger datasets is planned for future iterations.

## License

[Insert License Here]

## Contributing

Contributions are welcome. Please ensure all tests pass and new features are accompanied by appropriate unit/integration tests.
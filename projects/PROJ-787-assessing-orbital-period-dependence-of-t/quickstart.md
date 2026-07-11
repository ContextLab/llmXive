# Quickstart Guide: Assessing Orbital Period Dependence of the Exoplanet Radius Gap

This guide provides step-by-step instructions to set up the environment, download the required astronomical data (Kepler DR25 and KIC), merge them, and run the full analysis pipeline.

## Prerequisites

- Python 3.9+
- pip
- A Unix-like environment (Linux/macOS) or WSL on Windows

## 1. Setup Environment and Install Dependencies

Create a virtual environment and install the required packages:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 2. Initialize Directory Structure

Ensure the required data directories exist:

```bash
python code/setup_data_dirs.py
```

This creates:
- `data/raw/` for downloaded raw data
- `data/processed/` for intermediate and final results
- `code/ingest/`, `code/analysis/`, etc. if not already present

## 3. Download Raw Data (Kepler DR25 & KIC)

The pipeline requires two major datasets from the MAST archive:

### 3.1 Download Kepler DR25 Planet Table

```bash
python code/ingest/download_dr25.py
```

- **Output**: `data/raw/dr25_raw.csv`
- **Description**: Fetches the Kepler DR25 Planet Table (MAST Product ID: `kplr_dr25_planet`) using `astroquery.mast` with automatic retry logic.

### 3.2 Download Kepler Input Catalog (KIC)

```bash
python code/ingest/download_kic.py
```

- **Output**: `data/raw/kic_raw.csv`
- **Description**: Fetches the Kepler Input Catalog (MAST Product ID: `kic_v2`) containing stellar parameters (e.g., effective temperature, radius) needed for filtering.

### 3.3 Merge Catalogs

Combine the DR25 planet data with KIC stellar parameters:

```bash
python code/ingest/merge_catalogs.py
```

- **Input**: `data/raw/dr25_raw.csv`, `data/raw/kic_raw.csv`
- **Output**: `data/processed/merged_catalog.csv` (intermediate)
- **Description**: Merges the two datasets on the KIC ID, enriching planet records with stellar effective temperature and radius.

## 4. Preprocess and Filter Data

Filter the merged catalog to include only high-confidence planets with precise measurements:

```bash
python code/ingest/preprocess.py
```

**Filtering Criteria**:
- Radius uncertainty < 20%
- Orbital period uncertainty < 1%
- Stellar effective temperature must be present

**Outputs**:
- `data/processed/filtered_planets.csv`: Planets meeting the criteria
- `data/processed/deduped_planets.csv`: Duplicates resolved (keeping lowest radius uncertainty)

## 5. Run the Full Analysis Pipeline

Execute the complete pipeline (binning, GMM fitting, regression, theory comparison):

```bash
python code/main.py
```

This script:
1. Loads the deduplicated planet data
2. Bins planets by orbital period (log-spaced)
3. Fits Gaussian Mixture Models to find the radius gap in each bin
4. Performs Errors-in-Variables regression to determine the gap's period dependence
5. Compares results against photoevaporation and core-powered mass loss theories
6. Generates validation reports and final results

**Outputs**:
- `data/processed/binned_planets.csv`
- `data/processed/gap_locations.csv`
- `data/processed/synthetic_validation.json`
- `paper/results.md`

## 6. Verify Results

Check the final results and validation status:

```bash
cat paper/results.md
cat data/processed/synthetic_validation.json
```

## Troubleshooting

- **API Timeouts**: The download scripts include exponential backoff retry logic. If downloads fail repeatedly, check your internet connection or MAST service status.
- **Missing Stellar Parameters**: Planets without effective temperature in KIC are automatically excluded during preprocessing.
- **Unimodal Distributions**: Some period bins may not show a clear bimodal distribution; these are flagged as "unresolved" in `gap_locations.csv`.

## Next Steps

- Explore the `paper/results.md` for the statistical comparison of theories.
- Run `python code/validation/synthetic_recovery.py` to validate the pipeline's recovery of known ground-truth slopes.
- Customize binning or GMM parameters in `code/analysis/` scripts for sensitivity analysis.
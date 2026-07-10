# Quickstart: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

## Prerequisites

- Python 3.11 or higher
- `git`
- ~10 GB of free disk space (for data and dependencies)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Data Setup

1. **Download the Pantheon+ dataset**:
   - Navigate to the official repository: https://github.com/PantheonPlusSH0ES/DataRelease
   - Download the `Pantheon+_SH0ES.dat` file (or the latest CSV equivalent).
   - Place the file in `data/raw/`.
   - Verify the checksum (if provided) against the `data/` metadata.

2. **Verify data integrity**:
   ```bash
   python code/ingestion.py --verify-only
   ```

## Running the Analysis

Execute the full pipeline:

```bash
python code/analysis.py
```

This will:
1. Ingest and filter the Pantheon+ data.
2. Calculate residuals.
3. Project to HEALPix and compute spherical harmonics.
4. Run a large number of rotation simulations.
5. Calculate p-values and generate the final report.

## Output

- **Processed Data**: `data/processed/`
  - `residuals.csv`: Filtered supernova data with residuals.
  - `healpix_map.fits`: HEALPix projection.
  - `simulation_results.csv`: Null distribution data.
- **Reports**: `data/reports/final_report.txt`
  - Contains the observed dipole/quadrupole amplitudes, p-values, and significance conclusion.

## Validation

To validate the implementation against a known signal:

```bash
python code/analysis.py --synthetic --inject-dipole 0.05
```

This will run the analysis on a synthetic dataset with an injected dipole of a representative magnitude and verify that the extracted amplitude matches within statistical error.

## Troubleshooting

- **Memory Error**: If you encounter memory issues, reduce the simulation count in `code/simulations.py` (e.g., `N=1000`).
- **Missing Data**: If the script reports missing RA/Dec, check the raw data file for formatting issues.
- **Runtime Error**: Ensure you are using Python 3.11+ and that all dependencies are installed correctly.

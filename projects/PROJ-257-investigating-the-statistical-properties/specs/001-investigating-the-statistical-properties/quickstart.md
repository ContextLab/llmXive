# Quickstart: Statistical Properties of Simulated Black Hole Mergers

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Internet access (for Zenodo downloads)

## Installation

1. Clone the repository and navigate to the project directory.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install pandas numpy scipy matplotlib requests pyyaml pytest
   ```

## Running the Pipeline

The pipeline is orchestrated by `src/main.py`.

1. **Download & Preprocess**:
   ```bash
   python src/main.py --phase download_preprocess
   ```
   This step attempts to download GWTC-1/2 data. If unavailable, it generates synthetic data.

2. **Run Analysis**:
   ```bash
   python src/main.py --phase analyze
   ```
   Computes KDEs, KS tests, sensitivity analysis, and power analysis.

3. **Generate Report**:
   ```bash
   python src/main.py --phase visualize
   ```
   Generates PNG plots and a summary report in `data/artifacts/`.

## Verification

To verify the pipeline:
1. Check `data/processed/` for CSVs with ≥100 events.
2. Check `data/artifacts/` for `ks_results.json` and `plots/`.
3. Run unit tests:
   ```bash
   pytest tests/unit/
   ```

## Troubleshooting

- **Zenodo 404**: If the download fails after 3 retries, check the Zenodo DOI status. The pipeline will exit with an error.
- **Memory Errors**: Reduce the number of synthetic events if running on a machine with <4GB RAM (though the default is optimized for 7GB).

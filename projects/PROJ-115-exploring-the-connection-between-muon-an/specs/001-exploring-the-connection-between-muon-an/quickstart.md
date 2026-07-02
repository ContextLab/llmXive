# Quickstart: Exploring the Connection Between Muon Anomalous Magnetic Dipole Moment and Dark Matter Interactions

## Prerequisites

- Python 3.11+
- pip

## Installation

1. Clone the repository and navigate to the project directory.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Scan

1. **Generate Lookup Tables** (Pre-computation):
   ```bash
   python code/scan/generate_tables.py
   ```
   This creates `data/processed/relic_lookup.csv`.

2. **Run the Parameter Scan**:
   ```bash
   python code/scan/run_scan.py
   ```
   This executes the grid scan, applies constraints, and outputs:
   - `data/processed/viable_points.csv`
   - `data/processed/viable_region.png`
   - `logs/scan.log`

3. **Validation**:
   - Validate $\Delta a_\mu$ implementation:
     ```bash
     python code/validation/validate_delta_a.py
     ```
   - Validate Relic Density (Sommerfeld):
     ```bash
     python code/validation/validate_relic_density.py
     ```

4. **Generate Report**:
   ```bash
   python code/reporting/make_report.py
   ```
   This produces `g2_dm_report.pdf`.

## Expected Outputs

- **viable_points.csv**: List of parameter points satisfying all constraints.
- **viable_region.png**: 2D contour plot of $m_V$ vs $g$.
- **g2_dm_report.pdf**: Comprehensive PDF report with plots, tables, and reproducibility info.

## Troubleshooting

- **Runtime Error**: Ensure you are on a 2-core CPU environment (GitHub Actions). If running locally, limit threads.
- **Data Missing**: If LEP data fails to download, check network or verify the URL in `code/config.py`.
- **Overflow**: If couplings $g \ge 1$ are attempted, the script will cap them and log a warning.

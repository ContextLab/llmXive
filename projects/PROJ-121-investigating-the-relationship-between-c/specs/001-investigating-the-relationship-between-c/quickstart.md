# Quickstart: Cosmic Ray Anisotropy Solar‑Cycle Modulation

## Prerequisites

- Python 3.11+
- `git`
- Internet connectivity (for data downloads)

## Installation

```bash
# Clone repository
git clone <repo-url>
cd <repo-root>

# Install dependencies
pip install -r requirements.txt
```

## Running the Pipeline

### Full End-to-End Execution

```bash
# Default 27-day bin size
./src/cli/run_all.sh

# Custom bin size (e.g., 14 days)
./src/cli/run_all.sh --bin-size 14
```

### Step-by-Step Execution

1. **Download Data**:
   ```bash
   python src/data/download.py
   ```
   - Downloads IceCube, Auger (if available), and NOAA data.
   - Verifies checksums; retries with exponential back-off on failure.
   - Logs warnings if Auger data is unavailable.

2. **Preprocess & Generate Maps**:
   ```bash
   python src/data/preprocess.py --bin-size 27
   ```
   - Bins events into intervals (~ for 27-day bins).
   - Generates HEALPix Nside maps.
   - Applies data sampling if dataset > 7GB RAM.
   - Fits spherical harmonics; exports CSV.

3. **Statistical Analysis**:
   ```bash
   python src/analysis/correlation.py
   ```
   - Runs Lomb-Scargle (with resolution warnings), data-driven block bootstrap, phase-sensitive correlation.
   - Applies Bonferroni correction; outputs correlation results.
   - Uses phase randomization of both series for FAP.

4. **Generate Report**:
   ```bash
   ./src/report/make_report.sh
   ```
   - Creates plots (PNG/SVG) with resolution warnings.
   - Compiles LaTeX report (`report.pdf`) with programmatically generated hypothesis statement.

## Output Files

- `data/results/dipole_timeseries.csv`: Anisotropy metrics per interval (multiple rows).
- `data/results/correlation_results.csv`: Statistical correlation metrics.
- `output/plots/`: Time-series, periodograms (with resolution warnings), heatmaps.
- `output/report.pdf`: Final LaTeX report.

## Troubleshooting

- **Missing Data**: Check logs for download errors; verify internet connectivity. Auger data may be unavailable; logs will indicate "Auger data not found".
- **Runtime Exceeded**: Reduce resamples in `correlation.py` (e.g., a lower count instead of [deferred]).
- **Data Volume**: If the dataset is too large, the pipeline will automatically sample a representative subset to fit in 7GB RAM.
- **Auger Unavailable**: Logs will indicate "Auger data not found"; analysis proceeds with IceCube only.

## Verification

- Run `./src/cli/run_all.sh` on a fresh runner.
- Verify `dipole_timeseries.csv` has ≥128 rows ([deferred] of ~135 expected).
- Confirm `report.pdf` compiles without errors and includes "Resolution Warning" for the 11-year cycle.

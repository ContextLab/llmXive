# Quickstart: Cosmic Ray Anisotropy Solar‑Cycle Modulation

## Prerequisites

- Python 3.11+
- `git`, `make`, `pdflatex` (TeX Live)
- Internet access (for data download)

## Installation

1. **Clone and Setup**
   ```bash
   git clone <repo>
   cd projects/PROJ-121-investigating-the-relationship-between-c
   python -m venv venv
   source venv/bin/activate
   pip install -r code/requirements.txt
   ```

2. **Verify Dependencies**
   ```bash
   python -c "import healpy, scipy, astropy; print('OK')"
   ```

## Running the Pipeline

### Full End-to-End
```bash
bash code/run_all.sh
```
- Downloads IceCube/Auger data (solar cycle 24–25) and solar proxies from official portals.
- Validates temporal coverage; flags partial data.
- Computes relative anisotropy (correcting for acceptance).
- Bins events (default duration), computes dipole/quadrupole.
- Runs Lomb-Scargle, bootstrap, shuffle tests (shuffling solar proxy).
- Generates `reports/report.pdf` and `data/results/correlation_results.json`.

### Custom Bin Size
```bash
bash code/run_all.sh --bin-size 14
```
- Options: varying intervals including approximately one week, two weeks, four weeks, and two months.

### Blind Validation Only
```bash
python code/src/validation.py
```
- Runs synthetic test; outputs FPR and Power metrics.

## Output Files

| File | Description |
|------|-------------|
| `data/processed/anisotropy_timeseries.csv` | Relative dipole amplitude/phase per interval |
| `data/results/correlation_results.json` | Statistical test results |
| `reports/report.pdf` | LaTeX report with figures |
| `code/requirements.txt` | Pinned dependencies |

## Troubleshooting

- **Download fails**: Check internet; script retries a limited number of times.
- **Partial coverage**: Pipeline logs warning; proceeds with available data.
- **LaTeX error**: Ensure `pdflatex` installed; run `make_report.sh` locally.
- **Memory error**: Reduce bin size or skip one detector.

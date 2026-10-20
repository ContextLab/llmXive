# Quickstart: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

## Prerequisites
- Python 3.11 or newer
- Git
- ~Sufficient free disk space (on the order of several gigabytes) for dataset and intermediate files

## Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r requirements.txt
```

## Data Setup

1. **Obtain Pantheon+**  
   - Visit the official Pantheon+ repository (https://github.com/PantheonPlusSH0ES/DataRelease).  
   - Download the file `Pantheon+_SH0ES.dat` (or the latest CSV equivalent).  
   - Place the file in `data/raw/`.  
2. **Verify integrity** (the SHA‑256 hash is recorded in `data/raw/manifest.json`):
   ```bash
   python code/ingestion.py --verify-only
   ```

## Run the Full Analysis

```bash
python code/analysis.py
```

The script performs the following automatically:
1. Ingests and filters the Pantheon+ data, writes `residuals.csv`.  
2. Projects residuals onto a HEALPix grid (`healpix_map.fits`).  
3. Computes dipole and quadrupole amplitudes.  
4. Generates isotropic mock catalogs via random rotations, monitors convergence, and writes `simulation_results.csv`.  
5. Calculates p‑values and writes `final_report.txt` and `analysis_result.json`.

## Outputs

- `data/processed/residuals.csv` – cleaned supernova table with residuals.  
- `data/processed/healpix_map.fits` – HEALPix map of mean residuals.  
- `data/processed/simulation_results.csv` – dipole/quadrupole amplitudes from each mock catalog.  
- `data/reports/final_report.txt` – human‑readable summary of the dipole/quadrupole amplitudes, p‑values, and significance flag.  
- `analysis_result.json` – machine‑readable result validated against `contracts/analysis_result.schema.yaml`.

## Validation (Synthetic Test)

To confirm the pipeline can recover a known signal:

```bash
python code/analysis.py --synthetic --inject-dipole 0.04
```

This creates a synthetic supernova sample with an injected dipole of 0.04 mag, runs the full pipeline, and prints the recovered amplitude and p‑value.

## Troubleshooting

- **MemoryError** – Reduce the number of simulations by editing `code/simulations.py` (`MAX_SIMULATIONS = 2000`).  
- **Missing columns** – Ensure the raw Pantheon+ file contains the required columns (`RA`, `DEC`, `z`, `mu`, `muerr`).  
- **Runtime > 6 h** – The script automatically stops the simulation loop once the convergence criterion (Δmean < 0.001 mag over last 1 000 sims) is met; you can also lower `MAX_SIMULATIONS` manually.

---

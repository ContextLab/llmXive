# Quickstart: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

## Prerequisites
- Python 3.11 or newer
- Git
- ~sufficient free disk space (for the Pantheon+ release and intermediate files)

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

```bash
# Download Pantheon+ (open‑source GitHub release)
python code/download_pantheon.py   # writes data/raw/pantheon_plus.dat and records SHA‑256
# Verify checksum (optional)
python code/download_pantheon.py --verify-only
```

> **Note:** The Pantheon+ repository URL is **not** a verified citation under Constitution Principle II. When a Zenodo‑mirrored DOI becomes available it should replace the GitHub URL to achieve full compliance.

## Step 0 – Power‑Analysis (optional but recommended)

```bash
python code/power_analysis.py
# Produces data/processed/power_analysis_results.csv
```

> **Note:** The power‑analysis routine uses each supernova’s individual uncertainty plus a small systematic term (σ_sys = 0.02 mag) and streams the dataset to stay within the 7 GB RAM limit.

## Run the Full Analysis

```bash
python code/analysis.py
```

The script will automatically:

1. Ingest the Pantheon+ data, filter invalid rows, and compute residuals (`residuals.csv`).  
2. Project residuals onto a HEALPix grid (`healpix_map.fits`).  
3. Estimate dipole and quadrupole amplitudes (weighted‑least‑squares + pseudo‑Cℓ).  
4. Generate isotropic mock catalogs via mask‑aware random rotations, stopping when convergence criteria (≥ 5 000 sims, mean change < 0.001 mag, p‑value CI width ≤ 0.01) are met.  
5. Compute p‑values, write `final_report.txt`, and produce `analysis_result.json`.

## Outputs

- `data/processed/residuals.csv` – cleaned supernova table with residuals.  
- `data/processed/healpix_map.fits` – HEALPix map of mean residuals.  
- `data/processed/simulation_results.csv` – dipole/quadrupole amplitudes from each mock catalog.  
- `data/processed/power_analysis_results.csv` – (optional) detectable dipole amplitude and assumptions.  
- `data/reports/final_report.txt` – human‑readable summary, validated against `final_report.schema.yaml`.  
- `data/reports/analysis_result.json` – machine‑readable result, validated against `analysis_result.schema.yaml`.

## Validation (Synthetic Test)

```bash
python code/analysis.py --synthetic --inject-dipole 0.04
```

Creates a synthetic supernova sample with an injected dipole of modest magnitude, runs the full pipeline, and prints the recovered amplitude and p‑value.

## Troubleshooting

- **MemoryError** – Reduce `MAX_SIMULATIONS` in `code/simulations.py` (default a high default value (e.g., on the order of thousands)).  
- **Missing columns** – Ensure the raw Pantheon+ file includes `RA`, `DEC`, `z`, `mu`, `mu_err`.  
- **Runtime > 6 h** – The simulation loop stops automatically once the dipole mean changes by < 0.001 mag over the last 1 000 sims **and** the p‑value confidence‑interval width ≤ 0.01; you can also lower `MAX_SIMULATIONS` manually.  

---  
*End of Quickstart*===
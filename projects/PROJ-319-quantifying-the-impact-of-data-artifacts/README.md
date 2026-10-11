# Quantifying the Impact of Data Artifacts on Planetary Nebula Morphology

**Project ID:** PROJ‑319
**Branch:** `001-quantify-artifact-bias`
**Created:** 2026‑06‑25

## Overview

This repository implements a computational pipeline to assess how common imaging artifacts—specifically Gaussian detector noise and pixel saturation—bias the measurement of morphological parameters (ellipticity and asymmetry) in planetary nebulae.

The workflow:
1. **Synthetic Data Generation** – Produce 50 synthetic, flux‑calibrated planetary nebula images with known ground‑truth ellipticity and asymmetry.
2. **Artifact Injection** – Systematically inject Gaussian noise (σ = 0.01, 0.05, 0.10 × median signal) and apply saturation clipping (0 %–50 % in 5 % steps).
3. **Metric Measurement** – Compute ellipticity (second‑order moments) and asymmetry (Conselice 2003) for each artifact‑augmented image.
4. **Statistical Analysis** – Perform linear/polynomial regression of bias versus artifact intensity, applying Bonferroni correction for multiple testing.
5. **Calibration & Validation** – Derive correction functions, validate on a held‑out synthetic subset, and evaluate on a small real HST validation set.
6. **Reproducibility** – Log random seeds, artifact parameters, software versions, and generate a run manifest with checksums.

The pipeline is fully automated via a single CLI entry point and is designed to run on CPU‑only runners (e.g., GitHub Actions free tier). All results are written to the `data/processed/` directory and documented in accompanying markdown reports.

## Quick‑start

The following instructions assume a POSIX‑compatible shell (Linux/macOS/WSL).

```bash
# 1. Clone the repository
git clone <repository-url>
cd PROJ-319-quantifying-the-impact-of-data-artifacts

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Run the full pipeline
python code/main.py --run-all
```

The command above will:
- Generate synthetic FITS images in `data/synthetic/`.
- Produce ground‑truth metadata `data/synthetic/gt_metadata.json`.
- Run noise and saturation sweeps, writing `noise_sweep_data.csv` and `saturation_sweep.csv` to `data/processed/`.
- Perform regressions, saving `noise_stats.csv`, `saturation_stats.csv`, and the calibration model `calibration_functions.json`.
- Validate the models on a held‑out subset and output `validation_results.csv`.
- Create a reproducibility manifest `data/processed/run_manifest.json` and log files under `logs/`.

### Running Individual Stages

```bash
# Generate synthetic data only
python code/main.py --mode generate --n-images 50

# Inject artifacts and measure metrics
python code/main.py --mode process

# Fit calibration models
python code/main.py --mode calibrate

# Validate calibration functions
python code/main.py --mode validate

# Verify pipeline state (checks required files)
python code/main.py --mode verify
```

## Directory Structure

```
.
├─ code/ # Source modules
│ ├─ synthetic/ # Synthetic image generation & artifact injection
│ ├─ metrics/ # Ellipticity & asymmetry calculations
│ ├─ analysis/ # Statistics, regression, validation, power analysis
│ └─ io/ # FITS/JSON I/O utilities and run manifest
├─ data/
│ ├─ synthetic/ # Generated FITS images + gt_metadata.json
│ ├─ processed/ # Sweep CSVs, regression outputs, manifests
│ └─ validation/ # Real HST images and validation results
├─ logs/ # Log files (research.log, verification.log, etc.)
├─ tests/ # Unit, contract, and integration tests
├─ docs/ # Reports and documentation
├─ requirements.txt # Pinned dependencies
└─ README.md # This file
```

## Reproducibility

- All random seeds are fixed (`RANDOM_SEED = 42`).
- Every artifact is written with a SHA‑256 checksum; the manifest (`run_manifest.json`) records git commit, environment info, and artifact parameters.
- To reproduce a specific run, checkout the commit hash from the manifest and rerun the pipeline with the same configuration.

## License

This project is released under the MIT License. See the `LICENSE` file for details.
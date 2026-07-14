# Quickstart Guide: Reconstructing Early Universe Phase Transitions from CMB B-Mode Polarization

This guide provides step-by-step instructions to set up the environment, download real observational data, run the full analysis pipeline, and visualize results.

## Prerequisites

- Python 3.11+
- pip (Python package manager)
- 2 CPU cores, 7GB RAM (minimum)
- Internet connection for initial data download

## 1. Environment Setup

Clone the repository and install dependencies:

```bash
cd projects/PROJ-499-reconstructing-early-universe-phase-tran
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Data Ingestion and Preprocessing (User Story 1)

Download Planck 2015 SMICA B-mode maps and BICEP/Keck spectra, apply masks, and compute power spectra.

```bash
python code/data_ingestion.py
```

**Output Files**:
- `data/raw/planck_smica_bmode.fits`
- `data/raw/bicep_keck_spectrum.json`
- `data/derived/planck_masked_bmode.fits`
- `data/derived/bb_spectrum.json`
- `data/hashes.json` (SHA-256 checksums)

**CLI Flags**:
- `--planck-id`: Override default Planck map ID (default: `PLK_2015_SMICA`)
- `--bicep-url`: Override BICEP/Keck data URL
- `--mask-threshold`: Masking threshold (default: `0.70` sky coverage minimum)
- `--nside`: HEALPix resolution (default: `64`)

## 3. Theoretical Model Generation and Fitting (User Story 2)

Generate theoretical spectra for Inflation ($r$), Phase Transition ($E_{PT}$), and Null models, then perform Nested Sampling inference.

```bash
python code/model_generation.py
python code/inference.py
```

**Output Files**:
- `data/derived/theoretical_spectra.json`
- `data/derived/inference_results.json`
- `data/derived/posterior_samples.h5`

**CLI Flags**:
- `--r-range`: Comma-separated $r$ grid (default: `0.001,0.01,0.1`)
- `--e-pt-range`: Comma-separated $E_{PT}$ grid in GeV (default: `1e14,1e15,1e16`)
- `--n-live`: Number of live points for Nested Sampling (default: `50`)
- `--max-steps`: Maximum sampling steps (default: `1000`)
- `--convergence-threshold`: Evidence stability threshold (default: `0.1`)

## 4. Model Comparison and Statistical Validation (User Story 3)

Compute Bayes factors, compare models, and validate sky-split consistency.

```bash
python code/model_comparison.py
python code/validation.py
```

**Output Files**:
- `data/derived/model_comparison_results.json`
- `data/derived/sky_split_validation.json`
- `figures/bayes_factor_table.pdf`
- `figures/posterior_distributions.pdf`

**CLI Flags**:
- `--bayes-threshold`: Decision threshold for Bayes factor (default: `10.0`)
- `--precision`: Decimal precision for Bayes factor reporting (default: `2`)
- `--split-direction`: Sky split axis (`north-south`, `east-west`) (default: `north-south`)

## 5. Visualization

Generate all plots (posteriors, Bayes factors, spectrum comparisons).

```bash
python code/plotting.py
```

**Output Files**:
- `figures/posterior_1d_inflation.pdf`
- `figures/posterior_1d_phase_transition.pdf`
- `figures/posterior_2d_joint.pdf`
- `figures/bayes_factor_table.pdf`
- `figures/spectrum_comparison.pdf`

**CLI Flags**:
- `--dpi`: Plot resolution (default: `300`)
- `--format`: Output format (`pdf`, `png`) (default: `pdf`)
- `--no-show`: Disable interactive display (for headless execution)

## 6. Full Pipeline Execution

Run the entire analysis chain end-to-end:

```bash
bash scripts/run_full_pipeline.sh
```

This script executes:
1. Data ingestion and preprocessing
2. Theoretical model generation
3. Nested sampling inference
4. Model comparison and Bayes factor computation
5. Sky-split validation
6. All visualizations

**Expected Runtime**: ~2 hours on CPU (Nside=64, 1000 steps)

## 7. Validation and Testing

Run unit and integration tests:

```bash
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/contract/ -v
```

Run synthetic validation to verify pipeline correctness:

```bash
python code/synthetic_data.py
python code/validation.py --mode synthetic
```

## Troubleshooting

### Data Download Fails
- Check internet connection
- Verify `data/raw/` directory exists and is writable
- Ensure `requirements.txt` includes `requests==2.31.0`

### Nested Sampling Non-Convergence
- Increase `--max-steps` or `--n-live`
- Check `data/derived/inference_results.json` for `converged` flag
- Try different `--r-range` or `--e-pt-range` bounds

### Memory Errors
- Reduce `--nside` (e.g., `32` instead of `64`)
- Ensure CPU-only mode (no GPU acceleration)

### Sky Coverage Too Low
- Verify `--mask-threshold` is set correctly (default: `0.70`)
- Check `data/derived/planck_masked_bmode.fits` for mask integrity

## Configuration

Edit `code/config.py` to modify:
- Random seed for reproducibility
- Default data URLs
- HEALPix resolution
- CPU core limits

## License

This project is released under the MIT License.
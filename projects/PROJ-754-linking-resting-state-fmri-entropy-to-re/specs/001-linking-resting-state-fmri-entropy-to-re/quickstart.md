# Quickstart: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

## Prerequisites

- Python 3.11+
- `pip`
- Access to the HCP OpenAccess S3 bucket (credentials set as environment variables `HCP_USERNAME` and `HCP_PASSWORD`).

## Installation

1. Clone the repository and navigate to the project directory.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/code/requirements.txt
   ```

## Running the Pipeline

The pipeline is executed via the main script. It handles download (Plan B), preprocessing, entropy calculation, statistical modeling, power simulation, runtime measurement, and reporting.

```bash
python projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/code/main.py
```

### Configuration (`code/config.py`)

| Parameter | Default | Description |
| --- | --- | --- |
| `SUBSET_SIZE` | 200 | Number of subjects to download (fits CI disk limits; **must not exceed 200** per FR‑001). |
| `PERMUTATIONS` | 5000 | Number of label‑shuffled permutations for FWE. |
| `ENTROPY_R_VALUES` | `[0.1, 0.15, 0.2]` | Tolerance parameters for multiscale entropy. |
| `FD_THRESHOLD` | 0.2 | Mean framewise displacement cutoff (mm). |
| `POWER_SIMULATIONS` | 1000 | Number of Monte‑Carlo power simulations. |
| `POWER_EFFECT_SIZE` | 0.3 | Target Cohen's d for the entropy‑DSRT relationship. |
| `SMOOTHNESS_FWHM_MAX` | 8.0 | Maximum allowed smoothness (mm) before TFCE fallback. |
| `RANDOM_SEED` | 42 | Global seed for reproducibility. |

## What the Pipeline Does

1. **Dataset verification** – Checks that the HCP 4 mm parcellated time series and DSRT scores are reachable. If verification fails, the script exits with a clear error (see Phase 0 in `plan.md`).
2. **Quality control** – Excludes subjects with mean FD ≥ 0.2 mm or missing DSRT scores; records exclusions in `subject_qc.csv`.
3. **Resampling validation** – Performs Pearson correlation and KS‑test validation of the 4 mm resampling against literature benchmarks; falls back to 2 mm data if validation fails.
4. **Entropy computation** – Generates per‑scale and averaged entropy matrices.
5. **Noise‑variance covariate** – Derives and includes `noise_variance` in all models; also computes partial correlation with DSRT.
6. **Statistical modeling** – Parcel‑wise linear regression with VIF check, permutation‑based FWE, and TFCE fallback after empirical smoothness validation.
7. **Power simulation** – Estimates statistical power; the final PDF reports the estimate and notes any shortfall.
8. **Runtime measurement** – Writes `output/runtime_log.json` with total and permutation‑specific wall‑clock time and peak RAM usage.
9. **Reporting** – Produces `output/report.pdf` and `output/association_map.nii.gz`.

## Troubleshooting

- **Memory Error**: Reduce `SUBSET_SIZE` (cannot go below 200 due to FR‑001) or ensure garbage collection (`gc.collect()`) is called.
- **Timeout**: Reduce `PERMUTATIONS` to 1000 for quick testing; the full run uses 5000.
- **Credential Issues**: Verify that `HCP_USERNAME` and `HCP_PASSWORD` are correctly exported in the CI environment. The pipeline will abort with a clear error if they are missing.
- **Resampling Validation Failure**: The script will automatically fall back to the original 2 mm data and note the change in `report.pdf`.
- **Power Below Target**: The report will state the estimated power; no automatic abort occurs to respect FR‑001.

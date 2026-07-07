# Quickstart Guide: Exoplanetary Atmosphere Characterization

This guide walks you through running the full pipeline to characterize exoplanetary atmospheres, from data acquisition to statistical analysis.

## 1. Environment Setup

Ensure you are in the project root directory:
```bash
cd projects/PROJ-554-characterization-of-exoplanetary-atmosph
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Verify directory structure (created by T001a/T006b):
```bash
ls -d code/ data/ tests/ results/
```

## 2. Run the Pipeline

Execute the tasks in order. Each script writes its output to the `data/` or `results/` directory.

### Step 1: Download Data (User Story 1)
Fetches transmission spectra and metadata from the NASA Exoplanet Archive.
```bash
python code/download.py
```
**Expected Output**:
- `data/raw/`: Spectrum files.
- `data/processed/metadata.csv`: Contains columns `planet_name`, `equilibrium_temperature`, `metallicity`, `snr`, `resolution`, `category`.

*Note: If the sample size is < 30 or > 45, a warning is logged, but the process continues.*

### Step 2: Atmospheric Retrieval (User Story 2)
Runs `petitRADTRANS` to derive water vapor mixing ratios.
```bash
python code/retrieval.py
```
**Expected Output**:
- `data/processed/retrieval_results.csv`: Contains `log10_water_abundance`, `uncertainty`, `censored_flag`.

### Step 3: Statistical Analysis (User Story 3)
Computes Kendall's tau (censored), Tobit regression, and detection limits.
```bash
python code/analysis.py
```
**Expected Output**:
- `data/processed/analysis_results.json`: Correlation coefficients, p-values, model fit statistics.
- `data/processed/detection_limits.csv`: Detection limits per spectrum.

### Step 4: Visualization
Generates plots for review.
```bash
python code/plots.py
```
**Expected Output**:
- `results/plots/instrumental_noise_vs_signal.png`: SNR distribution and thresholds.

## 3. Verify Results

Check the generated files:
```bash
cat data/processed/analysis_results.json
ls results/plots/
```

Ensure `metadata.csv` has non-null values for critical columns (Temperature, Metallicity, SNR, Resolution).

## 4. Troubleshooting

- **Missing Dependencies**: If `petitRADTRANS` fails to import, ensure `requirements.txt` was installed correctly.
- **API Errors**: Check `code/config.py` for correct path settings and internet connectivity.
- **Censored Data Warnings**: If many spectra are flagged as censored, check the SNR distribution in `data/processed/metadata.csv`.

## 5. Next Steps

- Review `results/quality_report.md` for statistical power analysis.
- Examine `results/plots/` for visual validation of noise thresholds.
- Run `python -m pytest tests/` to validate contract and integration tests.

# Quickstart: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

## Prerequisites
- Python 3.11+
- Git
- Access to the `data/raw/` directory containing particle tracking CSVs (or the synthetic test data generator).

## Installation

1. **Clone and Setup**:
   ```bash
   git clone <repo-url>
   cd projects/001-validity-equipartition-granular
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Prepare Data**:
   - **Option A (Synthetic)**: Run `python code/tests/generate_synthetic_data.py` to create a valid test dataset in `data/raw/`.
   - **Option B (Real)**: Place your `particle_tracking.csv` and `driving_log.csv` in `data/raw/`. Ensure they match the schema in `contracts/dataset.schema.yaml`.

## Running the Pipeline

### 1. Ingestion and Energy Calculation
```bash
python code/main.py --step ingestion --sample-ratio 0.1
```
- `--sample-ratio`: Fraction of data to process (default 1.0). Set to 0.1 to fit in memory on CI.
- Output: `data/derived/energy_samples.csv`.

### 2. Statistical Analysis
```bash
python code/main.py --step stats --alpha 0.01
```
- Runs Lilliefors-corrected KS tests and Chi-squared tests.
- Applies Benjamini-Hochberg correction.
- Output: `artifacts/stats_results.json`.

### 3. Sensitivity Analysis
```bash
python code/main.py --step sensitivity --thresholds 0.01,0.05,0.10
```
- Sweeps thresholds and reports robustness.
- Output: `artifacts/sensitivity_report.json`.

### 4. Regression Analysis
```bash
python code/main.py --step regression
```
- Fits linear models on Excess Kurtosis and Energy Ratios.
- Output: `artifacts/regression_results.json`.

### 5. Full Run (End-to-End)
```bash
python code/main.py --full-run --sample-ratio 0.1
```

## Testing
Run unit tests to verify energy formulas and statistical logic:
```bash
pytest tests/ -v
```

## Troubleshooting
- **Memory Error**: Reduce `--sample-ratio` (e.g., 0.01).
- **Missing Columns**: Check `data/raw/` CSV headers. The pipeline expects `z` and `theta`. If missing, the run will flag the dataset as incomplete for full analysis.
- **Underpowered**: If the dataset is too small (N < 1000 per bin), the pipeline will issue a warning and skip hypothesis testing, outputting only descriptive statistics.
- **No Data**: If `data/raw/` is empty, run `python code/tests/generate_synthetic_data.py` to create a test dataset.

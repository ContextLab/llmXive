# User Guide

This guide provides step-by-step instructions for using the Equivalence Principle testing pipeline.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Configuration](#configuration)
3. [Running the Pipeline](#running-the-pipeline)
4. [Understanding the Outputs](#understanding-the-outputs)
5. [Troubleshooting](#troubleshooting)
6. [Advanced Usage](#advanced-usage)

---

## Getting Started

### Prerequisites

Ensure you have the following installed:
- Python 3.9 or higher
- pip (Python package manager)
- Git (for cloning the repository)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd PROJ-752-testing-the-equivalence-principle-with-s
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. Verify installation:
```bash
python code/scripts/validate_quickstart.py
```

---

## Configuration

The pipeline is configured via `config.yaml`. Here is a breakdown of the key sections:

### Paths Configuration

```yaml
paths:
 data_raw: data/raw
 data_processed: data/processed
 data_results: data/results
 docs: docs
```

These define where raw data, processed data, and results are stored.

### Benchmark Values

```yaml
benchmark_values:
 etvos_limit: 1.0e-13
 citation: "DOI:10.xxxx/xxxxx"
```

- `etvos_limit`: The state-of-the-art precision target (must be populated by T048.0d)
- `citation`: DOI or URL of the benchmark paper

**Important:** If `etvos_limit` is missing, the pipeline will log a warning and set `precision_goal_met = False`.

### Hyperparameters

```yaml
hyperparams:
 residual_threshold_cm: 2.0
 min_arc_length_days: 30
 convergence_tolerance: 1e-8
 geopotential_models: ["GGM05C", "EGM2008", "GOCO"]
```

- `residual_threshold_cm`: Maximum allowed residual (cm)
- `min_arc_length_days`: Minimum arc length for a satellite to be included
- `convergence_tolerance`: Solver convergence tolerance
- `geopotential_models`: List of models for sensitivity analysis

---

## Running the Pipeline

### Full Pipeline Execution

Run the entire pipeline:

```bash
python code/cli/main.py --config config.yaml
```

This will:
1. Fetch SLR data from ILRS
2. Preprocess and clean the data
3. Run separate and joint fits
4. Compute Eötvös parameter
5. Perform sensitivity analysis
6. Generate final report

### Stage-Specific Execution

#### Data Ingestion

```bash
python code/scripts/run_ingestion_pipeline.py
```

#### Preprocessing

```bash
python -c "from data.preprocessing import main; main()"
```

#### Eötvös Analysis

```bash
python -c "from analysis.eotvos import main; main()"
```

#### Validation

```bash
python -c "from analysis.validation import main; main()"
```

### Monitoring Progress

The pipeline logs progress to:
- Console (INFO level)
- `data/logs/pipeline.log` (DEBUG level)

Example log output:
```
[2024-01-15 10:30:45] INFO: Starting data ingestion for LAGEOS-1
[2024-01-15 10:31:12] INFO: Fetched 123,456 observations
[2024-01-15 10:31:15] WARNING: Etalon-2 data unavailable (403)
[2024-01-15 10:31:15] INFO: Proceeding with available satellites
```

---

## Understanding the Outputs

### Data Artifacts

#### `data/processed/cleaned_slr_data.csv`
Contains preprocessed SLR observations with columns:
- `timestamp`: Observation time (ISO format)
- `range`: Range in meters
- `satellite_id`: Satellite identifier
- `station_id`: Station identifier
- `residual`: Residual in meters
- `quality_flag`: Quality indicator

#### `data/processed/excluded_satellites.json`
List of satellites excluded due to insufficient arc length:
```json
{
 "excluded": ["Etalon-2"],
 "reasons": {
 "Etalon-2": "Arc length < 30 days"
 }
}
```

### Results Artifacts

#### `data/results/orbit_solutions.json`
Contains orbit solutions for each satellite:
```json
{
 "LAGEOS-1": {
 "orbital_elements": {...},
 "chi2": 1234.56,
 "covariance_matrix": [[...]],
 "state": [x, y, z]
 },
 "LAGEOS-2": {...}
}
```

#### `data/results/eotvos_metrics.json`
Final Eötvös parameter results:
```json
{
 "eta_value": 1.23e-14,
 "confidence_interval": [0.98e-14, 1.48e-14],
 "p_value": 0.032,
 "sensitivity_sweep_data": {
 "GGM05C": 1.23e-14,
 "EGM2008": 1.25e-14,
 "GOCO": 1.22e-14
 }
}
```

#### `data/results/sensitivity_analysis.png`
Visualization of Eötvös parameter variation across geopotential models.

#### `data/results/feasibility_gap_report.json`
Reports on data availability:
```json
{
 "status": "Incomplete",
 "missing_satellites": ["Etalon-2"],
 "errors": {
 "Etalon-2": "HTTP 403 Forbidden"
 }
}
```

### Diagnostic Report

The final diagnostic report (`docs/diagnostic_report.md`) includes:
- Δχ² (chi-squared improvement)
- F-statistic and p-value
- Eötvös parameter with 95% CI
- Benchmark comparison (Pass/Fail)
- Data completeness status

---

## Troubleshooting

### Common Issues

#### Issue: "Benchmark value missing"
**Symptom:** Warning logged, `precision_goal_met = False`

**Solution:**
1. Complete research task T048.0d
2. Update `config.yaml` with `benchmark_values.etvos_limit`
3. Re-run the pipeline

#### Issue: "Memory limit exceeded"
**Symptom:** Pipeline exits with error: `CRITICAL: Memory limit (6GB) exceeded. Current RSS: 6500MB`

**Solution:**
- Reduce the time span of data processed (e.g., use a subset of years)
- Run on a machine with more RAM
- Check for memory leaks in the code

#### Issue: "Solver did not converge"
**Symptom:** Warning logged, best-fit result used

**Solution:**
- Check initial guess (TLE data may be outdated)
- Relax convergence tolerance in `config.yaml`
- Verify data quality (outliers may cause divergence)

#### Issue: "Data unavailable for satellite"
**Symptom:** Warning logged, satellite excluded from analysis

**Solution:**
- Check `data/feasibility_gap_report.json` for error details
- Verify ILRS archive URL
- Proceed with available satellites (pipeline continues)

#### Issue: "ImportError: No module named X"
**Symptom:** Python cannot find a required module

**Solution:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check `PYTHONPATH` includes the `code/` directory
- Verify the module exists in the expected location

### Debugging Tips

1. **Enable verbose logging:**
```bash
python code/cli/main.py --config config.yaml --log-level DEBUG
```

2. **Run a single stage:**
```bash
python -c "from data.preprocessing import main; main()"
```

3. **Check intermediate outputs:**
Inspect files in `data/processed/` and `data/results/` after each stage.

4. **Validate configuration:**
```bash
python -c "from config import get_config; print(get_config())"
```

---

## Advanced Usage

### Custom Geopotential Models

To add a new geopotential model:
1. Add the model name to `config.yaml`:
```yaml
hyperparams:
 geopotential_models: ["GGM05C", "EGM2008", "GOCO", "MY_MODEL"]
```
2. Implement the model in `code/models/dynamics.py`
3. Ensure the model coefficients are available

### Parallel Processing

The sensitivity analysis can be parallelized:
```python
from multiprocessing import Pool
from analysis.validation import run_sensitivity_per_model

models = ["GGM05C", "EGM2008", "GOCO"]
with Pool(len(models)) as p:
 results = p.map(run_sensitivity_per_model, [(m, data) for m in models])
```

### Custom Satellite Metadata

To add a new satellite:
1. Update `data/satellite_metadata.yaml`:
```yaml
MY_SATELLITE:
 mass_kg: 400.0
 cross_sectional_area_m2: 1.5
 reflectivity: 0.8
```
2. Add the satellite ID to `data/verified_datasets.yaml`
3. Include it in the satellite list for ingestion

### Batch Processing

To process multiple time periods:
```bash
for year in 2020 2021 2022; do
 python code/cli/main.py --config config.yaml --year $year
done
```

### Exporting Results

Results can be exported to various formats:
```python
import pandas as pd
from analysis.eotvos import run_eotvos_analysis

result = run_eotvos_analysis(...)
df = pd.DataFrame([result.__dict__])
df.to_csv("eotvos_results.csv", index=False)
```

---

## Support

For additional support:
- Review the [API Reference](api_reference.md)
- Check the [Implementation Notes](implementation_notes.md)
- Open an issue in the project repository
- Consult the scientific literature on SLR and WEP tests

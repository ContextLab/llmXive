# Quickstart: Bird Migration and Climate Analysis

## Prerequisites

- Python 3.11+  
- Git  
- At least **10 GB** free disk space (for raw data, synthetic generation, and processing).  

## Installation

```bash
# 1. Clone the repository (or navigate to the project root)
git clone <repository-url>
cd <repo-root>

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies (pinned versions)
pip install -r requirements.txt
```

## Running the Pipeline

The pipeline supports two mutually exclusive modes:

### 1. Synthetic‑Data Mode (default, CI testing)

```bash
python -m src.cli.run_pipeline --mode synthetic --seed 42
```

- Generates `data/raw/synthetic_ebird.csv` and `data/raw/synthetic_climate.parquet` that conform to `contracts/dataset.schema.yaml`.  
- Executes the full preprocessing → modeling → permutation testing → trajectory analysis workflow.  
- **No scientific conclusions** are drawn; this run only validates that the code works and that all contract tests pass.

### 2. Real‑Data Mode (scientific analysis)

```bash
python -m src.cli.run_pipeline --mode real
```

- **Requires** the official eBird Basic Dataset (2020‑2024) at `data/raw/ebird/ebird_2020_2024.csv` and NOAA/PRISM climate data at `data/raw/climate/prism_2020_2024.parquet`.  
- The pipeline will abort with a clear error if either file is missing.  
- When present, the full analysis (preprocessing, Unified Spatial Model fitting, full 10,000‑shuffle permutation tests, route‑shift analysis) is executed and results are written to `data/processed/`.

## Validation

- **Contract tests**:  

```bash
pytest tests/contract/test_schemas.py
```

- **CI runtime check** (GitHub Actions free tier):  

```bash
# In .github/workflows/ci.yml the job `validate_quickstart` runs:
pytest tests/integration/test_quickstart.py
```

  The job asserts total runtime < 4 h and that all contract tests succeed.

## Expected Output Files

- `data/processed/phenology_metrics.csv` – aggregated phenology with `sample_weight`.  
- `data/processed/model_results.parquet` – GAMM coefficients, p‑values, convergence flags, GP metadata.  
- `data/processed/trajectory_shifts.parquet` – route‑shift statistics and 95 % confidence intervals.  
- `logs/pipeline.log` – detailed execution log (including any “insufficient data” markings, convergence warnings, Moran’s I diagnostics, and early‑stop flags).

## Troubleshooting

- **MemoryError**: Ensure at least 6 GB RAM is available; the pipeline uses chunked I/O.  
- **Convergence Warning**: Some species may fail to converge; they are logged and skipped.  
- **Missing Real Data**: If you intend to run real‑data mode, place the required files under `data/raw/ebird/` and `data/raw/climate/`. The pipeline will automatically detect them.  
- **Synthetic vs Real Mode Confusion**: The `--mode` flag is required; omitting it defaults to `synthetic`.  

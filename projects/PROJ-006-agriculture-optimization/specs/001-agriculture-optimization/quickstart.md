# Quickstart: Climate-Smart Agricultural Practices for Food Security

**Date**: 2025-07-04 | **Spec**: `specs/agriculture-20250704-001/spec.md`

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Docker (optional, for containerized execution)
- Git for version control

## Installation

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd agriculture-20250704-001
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
python src/cli/validate.py --check-all
```

## Data Download

### Step 5: Download Climate and Soil Data

```bash
python src/data/collectors/climate_collector.py --output data/raw/climate.parquet --include-soil
```

> This collector downloads CHIRPS rainfall data and ISRIC SoilGrids data via their respective APIs.

### Step 6: Download Crop Production Statistics

```bash
python src/data/collectors/crop_statistics_collector.py --source faostat --output data/raw/crop_stats.csv
```

> This collector downloads FAOSTAT crop production statistics via the FAO API.

### Step 7: Download Remote Sensing (if available)

```bash
python src/data/collectors/remote_sensing_collector.py --dataset modis --output data/remote-sensing/
```

> This collector downloads NASA MODIS MOD13Q1 data via NASA Earthdata API. **Important**: Requires Earthdata account registration at https://urs.earthdata.nasa.gov. Account approval typically takes 1-2 business days. Rate limits: established daily request thresholds for MODIS data. Set NASA_EARTHDATA_USERNAME and NASA_EARTHDATA_PASSWORD environment variables before running. If Earthdata access is delayed, the pipeline will proceed with available datasets and flag MODIS data as unavailable in provenance logs.

### Step 8: Download Household Survey Data

```bash
python src/data/collectors/survey_collector.py --output data/raw/survey.csv
```

> This collector downloads household survey data from local partner collection system.

## Run Pipeline

### Step 9: Execute Full Pipeline

```bash
python src/cli/run_pipeline.py
```

### Step 10: Validate Outputs

```bash
python scripts/validate_quickstart.py
```

## Expected Outputs

| Output | Location | Description |
|--------|----------|-------------|
| Dataset schema validation | contracts/dataset.schema.yaml | Input data contract |
| Output schema validation | contracts/output.schema.yaml | Analysis results contract |
| Farm survey schema validation | contracts/farm_survey.schema.yaml | Survey data contract |
| Climate risk assessment | data/processed/climate_risk.parquet | Risk model outputs |
| Yield predictions | data/processed/crop_yield.parquet | Yield model outputs |
| GIS maps | data/processed/maps/ | Spatial visualizations |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Dependency installation fails | Ensure pip is updated: `pip install --upgrade pip` |
| Climate data download timeout | Retry with `--max-retries 3` flag |
| Schema validation errors | Check data/raw/ files match contracts/ specifications |
| Missing soil data | Note: Soil data is optional; analysis proceeds with coverage tracking |
| NASA Earthdata authentication | Register at https://urs.earthdata.nasa.gov and set NASA_EARTHDATA_USERNAME/NASA_EARTHDATA_PASSWORD env vars. Allow 1-2 business days for approval. |
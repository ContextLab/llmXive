# Usage Guide

This guide details how to execute the pipeline, configure it, and interpret outputs.

## Quick Start

### 1. Environment Setup

Ensure you are in the project root and the virtual environment is active:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Initialize Directories

The pipeline requires specific directory structures. Run:

```bash
python code/setup_directories.py
python code/setup_subdirectories.py
```

This creates:
- `data/raw/`
- `data/processed/`
- `data/logs/`
- `state/`

### 3. Run the Simulation Pipeline

The pipeline is designed to run end-to-end. Execute the following commands in order:

```bash
# Step 1: Generate Synthetic Data
python code/data/simulation_mfq.py
python code/data/simulation_stories.py

# Step 2: Ingest and Merge
python code/data/ingest.py

# Step 3: Preprocess (Salience Mapping)
python code/data/preprocess.py

# Step 4: Bayesian Analysis
python code/models/bayesian.py

# Step 5: Regression Analysis
python code/models/regression.py

# Step 6: Validation
python code/analysis/validation.py

# Step 7: Report Generation
python code/reports/generate_report.py
```

## Configuration

### `code/config.py`

Key configuration variables:

- `RUN_MODE`: Set to `'simulation'` for synthetic data or `'real'` for actual data.
- `RANDOM_SEED`: Integer for reproducibility (default: 42).
- `DATA_DIR`: Base path for data artifacts.
- `OUTPUT_DIR`: Base path for results.

To change the mode to real data (future phase):
```python
# In code/config.py
RUN_MODE = "real"
```

## Output Artifacts

Upon successful completion, the following files are generated:

| File Path | Description |
|-----------|-------------|
| `data/processed/merged_data.csv` | Combined MFQ, Story, and VR log data |
| `data/processed/preprocessed_data.csv` | Salience-mapped dataset |
| `data/logs/pipeline.log` | Detailed execution logs |
| `state/pipeline_state.yaml` | Checksums and status of all artifacts |
| `reports/validation_report.json` | Quantitative validation metrics |
| `reports/final_report.md` | Human-readable summary of findings |

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed (`pip install -r requirements.txt`).
2. **Missing Directories**: Run `setup_directories.py` and `setup_subdirectories.py`.
3. **Convergence Failures**: The Bayesian model may fail to converge on small datasets. Check `data/logs/pipeline.log` for warnings.
4. **Schema Validation Errors**: Ensure input data matches the schema in `code/utils/schema.py`.

### Logging

All critical events are logged to `data/logs/pipeline.log`. Exclusion reasons and VR mapping logs are also captured here.

```bash
tail -f data/logs/pipeline.log
```

## Advanced Usage

### Running Specific Modules

You can run individual modules for debugging or partial re-runs:

```bash
# Only regenerate MFQ data
python code/data/simulation_mfq.py

# Only run model comparison
python code/analysis/model_comparison.py
```

### Real Data Ingestion (Future Phase)

When real data becomes available, the pipeline supports fetching via:

```bash
python code/data/ingest_real.py
```

This script is configured to fetch from OSF or HuggingFace as defined in `code/data/ingest_real.py`. Currently, it defaults to simulation mode if no real source is configured.

# Quickstart Guide: Investigating the Role of Microglial Morphology

This guide provides the commands to run the full pipeline end-to-end.

## Prerequisites

- Python 3.11+
- Install dependencies: `pip install -r code/requirements.txt`

## Execution Modes

### 1. Generate Synthetic Data (Validation Only)

Use this mode to validate the pipeline logic without real data.
This runs T007 (synthetic data generation) and then T018 (output metrics).

```bash
python code/run_t018_output.py --mode synthetic
```

**Expected Output**: `data/processed/morphological_metrics.csv`

### 2. Run Full Pipeline (Real Data)

Use this mode for the actual research analysis.
**Prerequisite**: Ensure T013-T017 (morphometry pipeline) has run and produced
`data/intermediates/processed_morphology.csv`.

```bash
python code/run_t018_output.py --mode real
```

**Expected Output**: `data/processed/morphological_metrics.csv`

## Running the Full Research Pipeline

To run the entire research pipeline from ingestion to validation:

1. **Ingest & Process (T012a-T017)**:
 (This step is assumed to be run separately or via the main pipeline script if available)
 ```bash
 # Example: Run morphometry pipeline (placeholder for the actual command)
 python code/morphometry.py --run-pipeline
 ```

2. **Output Metrics (T018)**:
 ```bash
 python code/run_t018_output.py --mode real
 ```

3. **Analysis (T023-T029)**:
 ```bash
 python code/analysis.py --run-full
 ```

4. **Validation (T033-T036)**:
 ```bash
 python code/validation_report.py --run-full
 ```

## Troubleshooting

- **Missing Intermediate Data**: If T018 fails with "FileNotFoundError", ensure the morphometry pipeline (T013-T017) has completed successfully.
- **Synthetic Data Path**: Use `--mode synthetic` for quick validation without real data.
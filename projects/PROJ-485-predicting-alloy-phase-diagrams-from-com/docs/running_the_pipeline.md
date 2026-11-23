# Running the Pipeline

## Quick Start
1. **Configure**: Update `code/config.yaml` with your data sources.
2. **Run**:
 ```bash
 python code/main.py
 ```
3. **Check Outputs**: Artifacts will be in `data/artifacts/`.

## Step-by-Step Execution

### 1. Data Ingestion
- **Input**: `data/raw/` or URLs from config.
- **Output**: `data/processed/descriptors.csv`.
- **Logs**: `data/logs/pipeline.log`.
- **Note**: If no real data source is available, the pipeline halts.

### 2. Feature Generation
- **Input**: `data/processed/descriptors.csv` (raw data + elemental props).
- **Output**: Updated descriptors with calculated features.
- **Validation**: Ensures derived values are within expected ranges.

### 3. Model Training
- **Input**: Processed descriptors.
- **Process**:
 - LOSO Cross-Validation.
 - Power Analysis (halts if power < 0.8).
 - Null Baseline Comparison.
- **Output**: `data/artifacts/model.pkl`, `baseline_comparison.json`.

### 4. Visualization
- **Input**: Model + Processed Data.
- **Process**:
 - Filter complex systems (e.g., Fe-C).
 - Generate plots (solid = experimental, dashed = predicted).
 - Calculate MAE and TCS.
- **Output**: `data/artifacts/plots/*.png`, `fidelity_report.json`.

### 5. Compliance Check
- **Process**: Verifies checksums and state consistency.
- **Output**: Updates `state/PROJ-485/state.yaml`.

## Troubleshooting
- **`DATA_SOURCE_MISSING`**: Check `code/config.yaml` for valid URLs or local paths.
- **`INSUFFICIENT_POWER`**: Increase dataset size or relax power threshold (not recommended).
- **`RESOURCE_LIMIT_EXCEEDED`**: Reduce data volume or optimize streaming chunks.

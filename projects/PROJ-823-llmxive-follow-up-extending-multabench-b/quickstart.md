# llmXive Follow-up: Extending MulTaBench - Quick Start Guide

## Prerequisites

- Python 3.10+
- pip
- Access to MulTaBench data (see `data/README.md` for acquisition steps)

## Installation

```bash
# Clone and navigate to project
cd PROJ-823-llmxive-follow-up-extending-multabench-b

# Install dependencies
pip install -r requirements.txt
```

## Data Setup

1. Follow instructions in `data/README.md` to acquire MulTaBench data
2. Place `multabench_baselines.csv` in `data/raw/`
3. Verify data integrity:
 ```bash
 python code/pipelines/fetch_baselines.py
 ```

## Pipeline Execution

### Step 1: Generate Baseline Embeddings (US1)
```bash
python code/pipelines/run_baseline.py --seed 42 --additional-seeds 123,456,789,1011 --batch-size 8
```

### Step 2: Train Conditioned Models (US2)
```bash
python code/pipelines/run_conditioned.py --seed 42 --epochs 15
```

### Step 3: Run Statistical Analysis (US3)
```bash
python code/pipelines/run_analysis.py
```

### Step 4: Full Set Validation (Optional, T024g)
```bash
python code/pipelines/full_set_validation.py --timeout 21600
```

### Step 5: Generate Final Summary
```bash
python code/pipelines/generate_final_summary.py
```

## Output Artifacts

All artifacts will be generated in the following directories:
- `data/processed/`: Processed data files
- `data/artifacts/`: Analysis results and reports
- `state/projects/`: Pipeline state tracking

Key deliverables:
- `data/processed/metadata_stats_summary.csv`
- `data/processed/normalized_tabular_features.parquet`
- `data/artifacts/gpu_tuned_baselines.csv`
- `data/artifacts/data_availability_gap_report.json`
- `data/artifacts/data_integrity_report.json`
- `data/artifacts/correlation_report_{run_id}.json`
- `FINAL_RESEARCH_SUMMARY.md`

## Troubleshooting

### Memory Issues
If you encounter OOM errors, reduce batch size:
```bash
python code/pipelines/run_baseline.py --batch-size 4
```

### Missing Data
Ensure all required files are present:
```bash
python code/pipelines/verify_real_data_sources.py
```

### Validation Failures
Run pre-flight checks:
```bash
python code/pipelines/final_execution_gate.py
```

## Notes

- All tasks run on CPU only (no GPU required)
- Random seed 42 is used for primary experiments
- Sensitivity analysis uses seeds [123, 456, 789, 1011]
- Full pipeline execution should complete within 6 hours on standard hardware
# Quickstart: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

## Prerequisites

- Python 3.11+
- pip
- Git
- Sufficient disk space for data storage and processing requirements will be allocated.
- Internet access (for dataset downloads)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-533-evaluating-the-impact-of-data-transforma
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### Full Pipeline (End-to-End)

```bash
python code/main_pipeline.py
```

This executes:
1. Dataset download (FR-001)
2. Filtering (FR-002)
3. Transformation (FR-003)
4. Type I error simulation (FR-004)
5. Power simulation (FR-005, FR-006)
6. Aggregation & reporting (FR-007–FR-009)

### Individual Steps

- **Download datasets**:
  ```bash
  python code/download_datasets.py
  ```
- **Filter datasets**:
  ```bash
  python code/filter_datasets.py
  ```
- **Apply transformations**:
  ```bash
  python code/apply_transformations.py
  ```
- **Run Type I error simulation**:
  ```bash
  python code/simulate_null.py
  ```
- **Run power simulation**:
  ```bash
  python code/simulate_power.py
  ```
- **Aggregate results**:
  ```bash
  python code/aggregate_results.py
  ```

## Output Locations

- **Raw data**: `data/raw/`
- **Filtered data**: `data/processed/filtered/`
- **Transformed data**: `data/processed/transformations/`
- **Type I error results**: `results/type1_error/`
- **Power results**: `results/power/`
- **Aggregated tables**: `results/aggregated/summary.csv`
- **Plots**: `results/aggregated/` (matplotlib/seaborn bar plots)
- **Logs**: `logs/` (exclusions, transformation failures, checkpoints)

## Verification

1. **Check dataset count**:
   ```bash
   python -c "import pandas as pd; df = pd.read_csv('data/datasets.csv'); print(f'Included datasets: {df[df.included].shape[0]}')"
   ```
   Expected: ≥50 datasets with `included=True`.

2. **Verify checksums**:
   ```bash
   python code/utils/checksums.py --verify
   ```

3. **Reproduce a single dataset**:
   ```bash
   python code/main_pipeline.py --dataset-id uci_har --skip-download
   ```

## Troubleshooting

- **Transformation fails**: Check `logs/transformation_errors.log` for variable-specific interventions.
- **Runtime exceeds 6 hours**: Ensure checkpointing is enabled; reduce iterations if necessary.
- **Memory error**: Stream data; process one dataset at a time.
- **Missing datasets**: Verify internet connectivity; check `data/datasets.csv` for excluded entries.

## Next Steps

- Review `results/aggregated/summary.csv` for mean Type I error and power.
- Inspect bar plots in `results/aggregated/` for visual comparison.
- Read `paper/` draft for interpretation of results.

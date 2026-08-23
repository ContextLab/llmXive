# Usage Examples

This document provides practical examples of using the PROJ-340 pipeline.

## Example 1: Running with Synthetic Data (Testing)

To verify the pipeline logic without real data:

```bash
# 1. Generate synthetic data
python code/generate_synthetic_data.py --output data/raw/synthetic_test_data.csv

# 2. Run the pipeline
python code/main.py \
 --input data/raw/synthetic_test_data.csv \
 --output data/results/ \
 --mode synthetic
```

**Expected Output**:
- `data/results/report_draft.md`
- `data/results/correlation_results.csv`
- `data/results/power_analysis_report.json`

## Example 2: Running with Real Data

1. **Configure Data Source**:
 Edit `data/config/real_data_sources.yaml`:
 ```yaml
 sources:
 - name: "Public Sleep Microbiome Dataset"
 url: ""
 type: "csv"
 verified: true
 ```

2. **Run Pipeline**:
 ```bash
 python code/main.py \
 --input data/raw/real_data.csv \
 --output data/results/ \
 --mode real
 ```

3. **Verify Outputs**:
 ```bash
 cat data/results/report_draft.md
 cat data/results/causal_scan_report.json
 ```

## Example 3: Running Specific Stages

### Ingestion Only
```bash
python code/ingest.py \
 --input data/raw/real_data.csv \
 --output data/processed/ \
 --validate-only
```

### Analysis Only
```bash
python code/run_analysis_with_fdr.py \
 --input data/processed/filtered_data.parquet \
 --output data/results/
```

### Diagnostics Only
```bash
python code/diagnostics.py \
 --input data/processed/filtered_data.parquet \
 --output data/results/
```

## Example 4: Verifying Integrity

After running the pipeline, verify that all artifacts are intact:

```bash
python scripts/verify_integrity.py
```

This compares file checksums against the state file `state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml`.

## Example 5: Custom Configuration

To change the timeout or other parameters:

```bash
python code/main.py \
 --input data/raw/real_data.csv \
 --output data/results/ \
 --mode real \
 --timeout 7200 # 2 hours
```

## Example 6: Debugging

To enable debug logging:

```bash
python code/main.py \
 --input data/raw/real_data.csv \
 --output data/results/ \
 --mode real \
 --log-level DEBUG
```

Logs will be written to `logs/debug.log`.

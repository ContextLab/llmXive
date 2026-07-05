# Quickstart Guide

## Prerequisites

- Python 3.9+
- 7GB+ RAM
- Internet connection (for data download)

## Installation

```bash
cd projects/PROJ-421-assessing-the-impact-of-data-resolution-
pip install -r code/requirements.txt
```

## Running the Pipeline

1. **Initialize**:
 ```bash
 python code/setup_dirs.py
 ```

2. **Download Data**:
 ```bash
 python code/data_ingestion.py
 ```

3. **Generate Resolutions**:
 ```bash
 python code/resampling.py
 ```

4. **Analyze**:
 ```bash
 python code/analysis.py
 ```

5. **Report**:
 ```bash
 python code/generate_final_report.py
 ```

## Expected Output

- `data/results/power_results.csv`
- `data/results/threshold_report.txt`
- `data/results/final_report.md`
- `figures/power_curve.png`

## Verification

- Check `data/results/threshold_report.txt` for the identified threshold (expected: 240m).
- Verify `data/results/final_report.md` contains Type II error delta and sensitivity analysis.

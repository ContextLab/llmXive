# Quickstart: Statistical Analysis of Flight Delay Distributions

## Prerequisites

- Python 3.11+
- pip
- Sufficient RAM available (streaming enabled)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-105-statistical-analysis-of-publicly-availab
 ```

2. **Create and activate a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### Run the Full Pipeline

Execute the main script to download, clean, fit models, and run diagnostics:

```bash
python code/main.py --year 2022
```

**Arguments**:
- `--year`: Target year for BTS data (default: 2022).
- `--source`: Specify data source (default: `official_bts`).

### Run the Summary & Subset Generation (T003)

After the preprocessing step has produced `data/processed/cleaned_delays.csv`,
generate the retention summary, zero‑inflation subset, and analysis set:

```bash
python code/t003_summary.py
```

This script creates:
- `data/results/summary.json` – contains `retention_rate`, `total_records`, `valid_records`.
- `data/processed/cleaned_delays_no_zero.csv` – records with `total_delay == 0` removed.
- `data/processed/analysis_set.csv` – excludes rows where `is_data_error == True`.

The pipeline aborts with a `PipelineError` if the retention rate falls below 95 %.

### Output

Upon successful completion, the following artifacts will be generated in `data/results/`:
- `model_comparison.json`: Ranking of distributions.
- `tail_index_estimate.json`: Heavy‑tail diagnostic results.
- `component_comparison.json`: Comparison of sum vs components.
- `tail_ks.json`: Tail goodness‑of‑fit test.
- `summary.json`: Retention summary (produced by T003).

## Verification

1. Check that `data/processed/cleaned_delays.csv` exists.
2. Verify `data/results/summary.json` contains the required keys and `retention_rate >= 0.95`.
3. Confirm `data/processed/cleaned_delays_no_zero.csv` and `data/processed/analysis_set.csv` are present.
4. Verify `data/results/model_comparison.json` contains entries for all 5 models. [UNRESOLVED-CLAIM: c_3712309e — status=not_enough_info]
5. Confirm `data/results/tail_index_estimate.json` reports a finite `estimated_alpha` and stability status.

## Troubleshooting

- **Memory Error**: If the pipeline fails with "Memory limit exceeded", the full year dataset exceeds the 7 GB RAM constraint even with streaming. The pipeline will exit with a non‑zero code.
- **No Data Found**: If the specified year is not available in the official BTS source, the script will exit with "No valid delay records found".
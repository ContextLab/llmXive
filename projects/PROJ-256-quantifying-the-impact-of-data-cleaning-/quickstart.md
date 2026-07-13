# Quickstart Guide: Quantifying the Impact of Data Cleaning on Statistical Inference

## Prerequisites
- Python 3.11+
- `requirements.txt` dependencies installed

## Setup
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. (Optional) Configure environment variables in `.env`:
 ```
 DATASET_URLS=...
 OUTPUT_PATH=data/processed
 RANDOM_SEED=42
 BOOTSTRAP_ITERATIONS=1000
 LOG_LEVEL=INFO
 ```

## Running the Pipeline
Execute the full analysis pipeline using the main entry point:
```bash
python code/main.py
```

This will:
1. Download datasets (T011)
2. Run baseline analysis (T012, T013)
3. Apply cleaning strategies (T017-T021, T022)
4. Re-analyze cleaned variants (T023)
5. Generate reports and visualizations (T030-T041)

## Verifying Outputs
Ensure the following files are generated in `data/processed/`:
- `baseline_metrics.json`
- `cleaned_metrics.json`
- `null_fpr_metrics.json`
- `comparison_report.json`
- `final_report.md`

Visualizations will be saved in `figures/`:
- `forest_plot.png`
- `ci_heatmap.png`

## Running Individual Tasks
You can also run individual tasks directly:
```bash
python code/t011_download_datasets.py
python code/t023_reanalyze_cleaned_variants.py
#... etc
```

## Troubleshooting
- If `python code/main.py` fails, check the logs for the specific script that failed.
- Ensure `data/raw/` is writable and `data/processed/` exists.
- Verify network connectivity for dataset downloads.
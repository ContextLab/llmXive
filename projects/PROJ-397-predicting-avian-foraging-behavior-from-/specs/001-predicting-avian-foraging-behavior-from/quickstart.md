# Quickstart: Predicting Avian Foraging Guilds

## Prerequisites

- Python 3.11+
- `pip`
- ~15 GB free disk space
- Internet connection (for dataset download)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd <project-dir>
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/requirements.txt
   ```

## Running the Pipeline

The pipeline is orchestrated via a shell script to ensure correct ordering (Download -> Process -> Train -> Evaluate -> Visualize).

### Step 1: Download Data
```bash
python projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/data/download_ebd.py
python projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/data/download_nlcd.py
```
*Output*: Raw files in `data/raw/`. Checksums recorded in `data/metadata.yaml`.

### Step 2: Process & Aggregate
```bash
python projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/data/merge_and_buffer.py
python projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/data/preprocess.py
python projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/data/aggregate.py
```
*Output*: `data/processed/merged_observations.csv` and `data/processed/species_profiles.csv`.

### Step 3: Train & Evaluate
```bash
python projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/models/train.py
python projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/models/evaluate.py
```
*Output*: Model artifacts, metrics JSON, permutation p-values.

### Step 4: Visualize
```bash
python projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/viz/plot_confusion.py
python projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/viz/plot_importance.py
python projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/viz/map_habitat.py
```
*Output*: PNG/GeoJSON files in `docs/results/`.

### Step 5: Full Run (One Command)
```bash
bash projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/run_pipeline.sh
```

### Step 6: Review Results (SSoT)
Open the final analysis notebook to review all metrics, plots, and logs:
```bash
jupyter notebook projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/notebooks/01_analysis.ipynb
```

## Validation

To verify the data contract:
```bash
pytest projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/tests/test_data_contract.py
```

To verify metric calculations:
```bash
pytest projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/tests/test_metrics.py
```

## Troubleshooting

- **Memory Error**: The script automatically filters to top 25 species. If still failing, check `preprocess.py` for chunking logic.
- **Missing NLCD Data**: If many points are dropped, the coordinates may be outside the US or the NLCD tile. Check logs in `data/processed/logs/`.
- **Guild Missing**: If a top 25 species lacks a guild label, it will be dropped. Check `code/data/guilds.yaml` and update if necessary.
- **EBD Download Timeout**: If the official EBD download fails, the script will automatically switch to the S3 fallback mirror.
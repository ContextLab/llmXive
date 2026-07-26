# Quickstart: Exploring the Correlation Between Musical Preference and Personality Traits

These steps assume a fresh GitHub Actions runner or a local Linux/macOS environment with Python 3.11.

## 1. Clone the repository
```bash
git clone
cd PROJ-049-music-personality
```

## 2. Set up the environment
```bash
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

## 3. Generate (or download) the data
```bash
# Attempt to download the official OpenML BFI‑2 and Last.fm archives.
# If the download fails (as on the CI runner), the script falls back
# to synthetic generation and writes the result to
# data/processed/synthetic_data.csv.
python code/download_data.py --output data/processed/merged_dataset.csv --seed 42
```
*If an open dataset that satisfies the required columns becomes available, replace the above command with `python code/download_data.py` pointing to that source.*

## 4. Run the full analysis pipeline
```bash
python code/run_pipeline.py \
 --input data/processed/merged_dataset.csv \
 --out-dir results/
```
This script sequentially calls:
- `preprocess.py`
- `genre_lookup.py`
- `analysis.py`
- `postprocess.py`
- `visualize.py`
- `report.py`

## 5. Inspect the outputs
```bash
# Correlation heatmap
display results/correlation_heatmap.png

# Full results table
head -n 20 results/results_report.csv
```

## 6. Run the test suite (optional)
```bash
pytest -vv
```

All random seeds are fixed (`seed=42`) to guarantee reproducibility.


# Quickstart: Assessing the Predictive Power of Plant Functional Traits for Species Distribution Models

## Prerequisites
- Python 3.11+
- 15 GB free disk space (for raw rasters and processed data).
- Network access to download WorldClim and TRY data; GBIF data is fetched via the API.

## Installation

```bash
cd projects/PROJ-478-assessing-the-predictive-power-of-plant-/code/
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Verify Dependencies

```bash
python -c "import sklearn, pandas, geopandas, rasterio; print('All dependencies OK')"
```

## Running the Pipeline

The pipeline is executed via the CLI and performs data download, cleaning, modeling, and analysis in one go.

```bash
# Full analysis (global Asteraceae)
python src/cli/main.py --config config.yaml

# Only data preprocessing
python src/cli/main.py --step preprocess --config config.yaml

# Only statistical analysis (requires pre‑computed results)
python src/cli/main.py --step analyze --config config.yaml
```

## Output Artifacts

- `data/processed/cleaned_occurrences.csv`: Spatially thinned occurrence data (global scope).
- `data/processed/traits.csv`: Validated trait data with `is_verified` flag.
- `results/metrics_per_fold.json`: AUC/TSS for every LOSO fold.
- `results/final_report.json`: Aggregated t‑test results, corrected p‑values, effect sizes.
- `results/sensitivity_table.csv`: Performance across thresholds {0.01, 0.02, 0.05}.

## Troubleshooting

- **Memory Error**: Reduce `max_depth` in `config.yaml` or increase `background_points` limit.
- **No Records**: If a species has < 100 records after thinning, it will be skipped and logged.
- **Missing Traits**: Species with missing traits are excluded from the trait‑augmented analysis; unverified traits are flagged in `traits.csv` but retained.

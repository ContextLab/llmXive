# Quickstart Guide

## Setup

1. Ensure you are in the project root directory.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Run the configuration setup to ensure directories exist:
 ```bash
 python code/config.py
 ```

## Data Ingestion

Run the data ingestion pipeline to download and parse Lichess games:
```bash
python code/src/main.py
```

This will:
1. Download a subset of games from Lichess (via HuggingFace or direct DB).
2. Parse PGN files to extract features.
3. Validate against schema contracts.
4. Save processed data to `data/processed/games.parquet`.

## Modeling

After data ingestion, run the modeling pipeline:
```bash
python code/src/models/fit.py
```

This will:
1. Fit Gaussian GLM and Ridge Regression models.
2. Apply FDR correction.
3. Save metrics to `data/results/model_metrics.json`.

## Validation

Run cross-validation and generate diagnostic plots:
```bash
python code/src/models/validate.py
```

## Testing

Run all tests:
```bash
pytest code/tests/
```

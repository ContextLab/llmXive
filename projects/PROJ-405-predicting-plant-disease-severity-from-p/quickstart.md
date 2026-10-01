# Quickstart: Plant Disease Severity Prediction Pipeline

## Prerequisites
- Python 3.11+
- pip (package installer)
- Git

## Setup
1. Clone the repository and navigate to the project root.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Ensure environment variables are set (optional for API keys, but recommended):
 ```bash
 export OPEN_METEO_API_KEY="your_key_here"
 ```

## Running the Pipeline
The full pipeline consists of three stages: Data Ingestion, Modeling, and Visualization.

### 1. Data Ingestion (US1)
Downloads PlantVillage images, extracts features, and links weather data.
```bash
python code/main.py --mode full --stage data
```
*Output*: `data/processed/unified_analysis.csv`

### 2. Modeling (US2)
Trains baseline and augmented models, runs permutation test.
```bash
python code/main.py --mode full --stage model
```
*Output*: `artifacts/models/`, `artifacts/results.json`

### 3. Visualization (US3)
Generates Partial Dependence Plots and sensitivity analysis.
```bash
python code/main.py --mode full --stage visual
```
*Output*: `artifacts/figures/pdp_*.png`, `artifacts/visualization_results.json`

### Full Run
To run the entire pipeline end-to-end:
```bash
python code/main.py --mode full
```

## Verification
Check the `state/projects/PROJ-405-predicting-plant-disease-severity-from-p.yaml` file to verify artifact hashes match the generated outputs.

## Reproduction
To reproduce results, ensure the seed in `code/config.py` is set to `42` and run the full pipeline.

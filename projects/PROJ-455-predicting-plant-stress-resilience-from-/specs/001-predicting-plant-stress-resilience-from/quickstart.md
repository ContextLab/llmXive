# Quickstart: Predicting Plant Stress Resilience

## Prerequisites
- Python 3.11+
- `pip`
- Access to a GitHub Actions runner (or local environment with 7GB+ RAM).

## Installation

1. **Clone the repository** and navigate to the project directory.
   ```bash
   cd projects/PROJ-455-predicting-plant-stress-resilience-from-/
   ```

2. **Create a virtual environment** and install dependencies.
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Verify dataset availability**.
   - *Note*: As per `research.md`, no verified plant metabolomic datasets are currently available in the provided list. The pipeline will generate **synthetic data** for demonstration.
   - To use real data, update `data/raw/` with a valid dataset that meets the pairing criteria (pre-stress + post-stress $\ge 7$ days).

## Running the Pipeline

### 1. Data Ingestion & Preprocessing
Generates a cleaned dataset (or uses synthetic data if none found).
```bash
python code/data/ingest.py --source synthetic --output data/processed/cleaned.parquet
python code/data/preprocess.py --input data/processed/cleaned.parquet --output data/processed/preprocessed.parquet
```

### 2. Model Training & Validation
Trains RF and SVM models, performs cross-validation and permutation testing.
```bash
python code/models/train.py --input data/processed/preprocessed.parquet --output data/results/model_results.json
python code/models/validate.py --input data/results/model_results.json --permutations 1000
```

### 3. Biological Validation
Maps metabolites to KEGG and checks pathway enrichment.
```bash
python code/analysis/pathway.py --input data/results/model_results.json --output data/results/biological_validation.json
```

### 4. Full Pipeline
Run the entire workflow end-to-end.
```bash
python code/main.py
```

## Expected Outputs
- `data/processed/preprocessed.parquet`: Normalized, imputed dataset.
- `data/results/model_results.json`: Performance metrics and feature importance.
- `data/results/biological_validation.json`: Pathway alignment results.

## Troubleshooting
- **Memory Error**: Ensure the dataset is subsampled or the machine has $\ge 7$GB RAM.
- **Missing Data > 10%**: The pipeline will reject the dataset. Check `data/raw/` for data quality.
- **No KEGG Mapping**: Ensure `biopython` is installed and internet access is available for KEGG queries.

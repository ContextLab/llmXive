# Quickstart: 001-predict-plant-disease-resistance

## Prerequisites

- Python 3.11+
- Docker (for `fastp`/`bcftools` environment)
- `pip` and `venv`
- Access to NCBI SRA and MetaboLights (for data retrieval)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-259-predicting-plant-disease-resistance-from
   ```

2. **Set up the environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r code/requirements.txt
   ```

3. **Prepare Data**:
   - Create `data_manifest.yaml` in `data/` with valid NCBI/MetaboLights accession numbers.
   - Example `data_manifest.yaml`:
     ```yaml
     datasets:
       - accession: "SRP123456"
         type: "genomic"
         source: "NCBI SRA"
       - accession: "MTB12345"
         type: "metabolomic"
         source: "MetaboLights"
     ```

## Running the Pipeline

Execute the main pipeline script:
```bash
python code/main.py --mode full
```

### Options
- `--mode full`: Runs download, preprocess, train, and validate.
- `--mode train`: Runs training only (requires preprocessed data).
- `--mode validate`: Runs external validation only.

### Output
- `data/processed/feature_table.csv`: Aligned features.
- `code/output/results.json`: Performance metrics.
- `code/output/biomarkers.csv`: Top 50 SNPs and metabolites.

## Validation

Run tests to ensure contract compliance:
```bash
pytest tests/contract/test_schemas.py
```

## Troubleshooting

- **Error: Insufficient data modalities**: Ensure `data_manifest.yaml` contains paired accession numbers.
- **Error: Power deficiency**: Dataset must have ≥100 paired samples.
- **Error: Memory limit**: Reduce dataset size or increase RAM (not supported on free-tier).

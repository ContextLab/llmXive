# Quick Start Guide

Get up and running with the antibiotic resistance prediction pipeline in under 15 minutes. [UNRESOLVED-CLAIM: c_574a7b30 — status=not_enough_info]

## Step 1: Environment Setup (3 minutes)

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt

# Verify installation
python code/verify_env.py
```

## Step 2: Create Directory Structure (1 minute)

```bash
python code/setup_directories.py
```

This creates all necessary directories:
- `code/01_ingest/`, `code/02_process/`, etc.
- `data/raw/`, `data/processed/`, `data/models/`
- `tests/contract/`, `tests/unit/`

## Step 3: Configure the Pipeline (2 minutes)

Create `config.yaml` in the project root:

```yaml
MAX_ISOLATES: 100 # Start with a small subset for testing
RANDOM_SEED: 42
BIO_PROJECT_IDS:
 - PRJNA512231 # Example: E. coli collection
PATHS:
 RAW_DATA: data/raw
 PROCESSED_DATA: data/processed
 MODELS: data/models
 FIGURES: figures
```

## Step 4: Run the Full Pipeline

The canonical entry point for the pipeline is now **`code/main.py`**.

```bash
# Ingest data, run contract validation, train models, validate, and version
python code/main.py --stage full --n-isolates 1000 --bio_project PRJNA528852 --antibiotic ciprofloxacin
```

For quicker testing you can run individual stages:

```bash
# Only ingestion
python code/main.py --stage ingest --n-isolates 10 --bio_project PRJNA528852

# Only training (requires previous ingestion)
python code/main.py --stage train --antibiotic ciprofloxacin

# Validation only
python code/main.py --stage validate --antibiotic ciprofloxacin --permutations 1000

# Generate figures
python code/main.py --stage viz --antibiotic ciprofloxacin
```

## Step 5: Verify Outputs (2 minutes)

```bash
ls -la data/processed/feature_matrix.csv
ls -la data/models/
ls -la data/processed/permutation_results.json
ls -la data/processed/sensitivity_sweep.csv
ls -la figures/
```

You should see:
- `feature_matrix.csv` with genomic features and phenotype columns
- Model pickle files under `data/models/`
- `metrics.json`, `permutation_results.json`, `sensitivity_sweep.csv`
- ROC/PR/feature importance plots in `figures/`

## Step 6: Versioning (Optional)

After a successful run you can manually update the project state:

```bash
python code/utils/hash_artifacts.py
```

This computes SHA256 hashes for all artifacts and writes them to
`state/projects/PROJ-027-predicting-antibiotic-resistance-evoluti.yaml`.

## Troubleshooting

### NCBI Rate Limiting
If you encounter rate limits, add delays between requests or reduce `MAX_ISOLATES`.

### Missing Dependencies
Ensure system tools are installed:
```bash
# Ubuntu/Debian
sudo apt-get install snippy ariba

# macOS
brew install snippy ariba
```

### Memory Issues
Reduce `MAX_ISOLATES` in `config.yaml` or use streaming mode for large datasets.

### Phylogeny Generation Fails
Ensure sufficient SNP diversity in your dataset. If all sequences are identical, the tree cannot be inferred. [UNRESOLVED-CLAIM: c_a05af2af — status=not_enough_info]

## Next Steps

- Review `docs/README.md` for detailed pipeline documentation
- Check `tests/contract/` for schema validation requirements
- Examine `code/utils/config.py` for configuration options
- Read `specs/001-predict-antibiotic-resistance-evoluti/` for project specifications

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review error logs in the `logs/` directory
3. Examine test failures with `pytest -v`
4. Consult the project specification documents
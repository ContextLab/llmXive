# Quick Start Guide

Get up and running with the antibiotic resistance prediction pipeline in under 15 minutes.

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

## Step 4: Run a Test Subset (5 minutes)

For a quick validation, run with a small subset:

```bash
# Download a small subset of sequences
python code/01_ingest/download_ncbi.py --max-isolates 10

# Process metadata
python code/01_ingest/ingest_metadata.py

# Build feature matrix (with mock SNP/gene data for testing)
python code/02_process/build_feature_matrix.py --test-mode

# Generate phylogeny
python code/02_process/generate_phylogeny.py

# Train and evaluate models
python code/03_model/mechanism_blind_filter.py
python code/03_model/split_data.py
python code/03_model/train_models.py
python code/03_model/evaluate.py

# Generate plots
python code/05_viz/generate_plots.py
```

## Step 5: Verify Outputs (2 minutes)

Check that all expected files were created:

```bash
ls -la data/processed/feature_matrix.csv
ls -la data/processed/phylogeny_tree.newick
ls -la figures/
```

You should see:
- `feature_matrix.csv` with columns: `isolate_id`, gene presence columns, `snp_counts`, `cnv_counts`, `resistance_phenotype`
- `phylogeny_tree.newick` in Newick format
- ROC curve and feature importance plots in `figures/`

## Step 6: Run Full Pipeline (Optional)

Once the test subset works, run the full pipeline:

```bash
python code/main_reproducible.py
```

This executes all stages and verifies artifact checksums.

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
Ensure sufficient SNP diversity in your dataset. If all sequences are identical, the tree cannot be inferred.

## Next Steps

- Review `docs/README.md` for detailed pipeline documentation
- Check `tests/contract/` for schema validation requirements
- Examine `code/utils/config.py` for configuration options
- Read `specs/001-predicting-antibiotic-resistance-evoluti/` for project specifications

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review error logs in the `logs/` directory
3. Examine test failures with `pytest -v`
4. Consult the project specification documents

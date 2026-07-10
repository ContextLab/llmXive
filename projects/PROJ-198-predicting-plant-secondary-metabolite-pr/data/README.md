# Data Directory Structure

This directory contains all data files for the llmXive project.

## Directory Structure

```
data/
├── raw/ # Raw, unprocessed data files
│ ├── mock_genomes.json # Mock genome data for CI testing
│ ├── mock_metabolites.csv # Mock metabolite data for CI testing
│ └── mock_anti_smash.json # Mock antiSMASH results for CI testing
├── processed/ # Processed and aligned datasets
│ └── aligned_dataset.csv # Final aligned dataset for modeling
└── checksums.txt # File checksums for data integrity
```

## CI Mode vs Research Mode

### CI Mode (`CI_MODE=true`)
- Uses mock data files in `data/raw/`
- No API calls to external services
- Fast, reproducible testing
- Ideal for continuous integration and development

### Research Mode (`CI_MODE=false`)
- Fetches real data from NCBI RefSeq and MetaboLights APIs
- Requires valid API keys in `.env` file
- Slower, but produces real research results
- Used for actual scientific analysis

## Mock Data Files

The mock data files are minimal, curated datasets used for testing:
- `mock_genomes.json`: Genome assembly metadata for a few species
- `mock_metabolites.csv`: Metabolite abundance tables
- `mock_anti_smash.json`: Pre-computed BGC feature counts

These files are sufficient to test the pipeline logic without requiring API access.

## Data Integrity

File checksums are maintained in `checksums.txt` to ensure data integrity.
Use the `utils/data_hygiene.py` module to verify checksums.

## Adding New Data

1. Place raw data in `data/raw/`
2. Run the download pipeline to process data
3. Processed outputs go to `data/processed/`
4. Update checksums using `utils/data_hygiene.py`
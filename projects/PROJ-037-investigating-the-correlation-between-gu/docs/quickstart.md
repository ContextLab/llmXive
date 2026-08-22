# Quickstart Guide: Gut Microbiome and Circadian Rhythm Study

## Overview

This project investigates the correlation between gut microbiome composition and circadian rhythm disruption using data from the American Gut Project and Open Humans.

## Prerequisites

- Python 3.8+
- pip
- 8GB+ RAM
- 10GB+ disk space

## Setup

1. Clone the repository and navigate to the project directory:
```bash
cd projects/PROJ-037-investigating-the-correlation-between-gu
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Data Download

The pipeline expects the following data files to be present:

- `data/raw/agp_16s.biom` - American Gut Project 16S rRNA data
- `data/raw/agp_metadata.csv` - AGP participant metadata
- `data/raw/open_humans_sleep.csv` - Open Humans sleep metadata

These files must be manually downloaded from their respective sources before running the pipeline.

## Running the Pipeline

Execute the full analysis pipeline:

```bash
python code/main.py
```

This will:
1. Ingest and merge data
2. Calculate diversity metrics
3. Perform correlation analysis
4. Run validation and sensitivity analysis
5. Generate visualizations
6. Create final report

## Output Files

After successful execution, the following files will be generated:

- `data/processed/cohort_merged.csv` - Cleaned, merged cohort
- `data/outputs/correlation_results.csv` - Statistical results
- `data/outputs/heatmap.png` - Taxa-sleep association heatmap
- `data/outputs/pcoa_sleep_quality.png` - PCoA ordination plot
- `data/outputs/sensitivity_report.csv` - Sensitivity analysis results
- `data/outputs/validation_status.json` - Bootstrap validation results
- `docs/research_report.md` - Final research report

## Individual Scripts

You can also run individual steps:

```bash
# Data ingestion
python code/ingestion.py

# Diversity analysis
python code/diversity.py

# Correlation analysis
python code/analysis.py

# Visualization
python code/viz.py

# Validation
python code/validation.py

# Report generation
python code/report.py
```

## Troubleshooting

- **Missing data files**: Ensure all required raw data files are present in `data/raw/`
- **Memory errors**: Reduce sample size or increase available RAM
- **Import errors**: Verify virtual environment is activated and dependencies installed
- **No matching participants**: Check that participant IDs match between datasets

## Notes

- All findings are associational; no causal claims are made
- Sample size limitations are documented in the final report
- Bootstrap confidence intervals including zero are accepted as valid negative results

# Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

**Project ID**: PROJ-355

## Overview
This project investigates the relationship between impurity clustering at grain boundaries and segregation energy in polycrystalline materials.
We utilize bulk configurations from Materials Project (MP) and OQMD, construct grain boundary supercells, compute clustering descriptors (RDF, pair correlation, Voronoi), and simulate segregation energies.

## Directory Structure
- `code/`: Source code for data pipeline, modeling, and analysis.
- `data/raw/`: Raw downloaded structures (MP/OQMD) and potential files.
- `data/processed/`: Processed descriptors, energies, and intermediate artifacts.
- `results/`: Final model metrics, reports, and visualizations.
- `tests/`: Unit and integration tests.
- `contracts/`: JSON schemas for data validation.

## Prerequisites
- Python 3.9+
- Required packages listed in `requirements.txt`.

## Execution Instructions
To run the full pipeline:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Configure linting/formatting
python code/run_linting_setup.py

# 3. Run the main pipeline
python code/main.py
```

## Data Availability
The pipeline requires access to MP/OQMD bulk structures. If these are unavailable, the pipeline will log `[DATA_UNAVAILABLE]` and exit gracefully, checking for a local backup in `data/raw/backup/`.

## License
[Insert License Here]
# Predicting Avian Foraging Behavior from Public eBird Data and Land Cover Maps

## Project Overview

This project aims to predict avian foraging guilds using public eBird occurrence data and NLCD 2019 land cover maps. The pipeline extracts records for top species, merges them with land cover data within 100m buffers, and trains a Random Forest classifier to predict foraging guilds.

## Directory Structure

```
code/
├── data/
│ ├── raw/ # Raw downloaded data (EBD, NLCD)
│ ├── processed/ # Processed and merged datasets
│ └── metadata/ # Metadata and provenance records
├── models/ # Trained models and evaluation results
├── viz/ # Visualization scripts and outputs
├── notebooks/ # Jupyter notebooks for analysis
├── utils/ # Utility modules (config, provenance)
├── tests/ # Unit and integration tests
├── docs/ # Documentation and reports
└── contracts/ # Data schema contracts
```

## Quick Start

1. **Initialize Directories**:
 ```bash
 python code/setup_directories.py
 ```

2. **Install Dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

3. **Run the Pipeline**:
 ```bash
 bash code/run_pipeline.sh
 ```

## Data Sources

- **eBird Basic Dataset (EBD)**: Downloaded from S3 bucket `s3://ebird-data/ebd_release/`
- **NLCD 2019 Land Cover**: Downloaded from USGS EarthExplorer
- **Birds of the World**: Used for foraging guild mapping

## License

This project is for research purposes only. Please refer to the data sources' terms of use.

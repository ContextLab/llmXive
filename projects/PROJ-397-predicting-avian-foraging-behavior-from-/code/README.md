# Predicting Avian Foraging Guilds from Public eBird Data and Land Cover Maps

## Overview
This project implements a machine learning pipeline to predict avian foraging guilds using eBird observation data and NLCD land cover maps. The pipeline extracts, merges, and analyzes data to train a Random Forest classifier.

## Project Structure
- `code/`: Source code for data processing, model training, and visualization
- `data/`: Raw and processed data artifacts
- `models/`: Trained models and metrics
- `viz/`: Visualization scripts and outputs
- `notebooks/`: Jupyter notebooks for analysis
- `utils/`: Utility modules for configuration and provenance
- `tests/`: Unit and integration tests

## Prerequisites
- Python 3.8+
- Dependencies listed in `requirements.txt`

## Installation
```bash
cd code
pip install -r requirements.txt
```

## Running the Pipeline
Execute the full pipeline using the orchestration script:
```bash
./run_pipeline.sh
```

## Data Sources
- eBird Basic Dataset (EBD) from S3
- NLCD 2019 Land Cover from USGS
- Foraging Guild labels from verified static source

## License
MIT License

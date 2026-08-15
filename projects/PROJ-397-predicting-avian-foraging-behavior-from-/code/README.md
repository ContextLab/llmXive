# Predicting Avian Foraging Behavior from Public eBird Data and Land Cover Maps

## Project Overview
This project implements a machine learning pipeline to predict avian foraging guilds using public eBird observation data and NLCD land cover maps. The goal is to understand the relationship between habitat composition and foraging behavior across bird species.

## Structure
- `code/`: Source code for the pipeline
 - `data/`: Data download, processing, and aggregation scripts
 - `models/`: Model training and evaluation scripts
 - `viz/`: Visualization and reporting scripts
 - `utils/`: Utility functions and configuration
 - `tests/`: Unit and integration tests
- `data/`: Raw and processed data files
- `docs/`: Documentation and results
- `specs/`: Feature specifications and design documents

## Prerequisites
- Python 3.8+
- Required packages listed in `requirements.txt`

## Quick Start
1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
2. Run the full pipeline:
 ```bash
 bash run_pipeline.sh
 ```

## Data Sources
- eBird Basic Dataset (EBD) from Cornell Lab of Ornithology
- NLCD 2019 Land Cover data from USGS
- Birds of the World foraging guild data from Cornell Lab of Ornithology

## License
This project is for research purposes only. Please refer to the original data sources for their respective licenses and usage terms.

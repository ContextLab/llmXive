# Predicting Avian Foraging Behavior from Public eBird Data and Land Cover Maps

**Project ID**: PROJ-397

## Overview
This project implements a pipeline to predict avian foraging guilds using eBird observation data merged with NLCD 2019 land cover data.

## Prerequisites
- Python 3.11.x
- pip

## Installation
1. Clone the repository.
2. Navigate to the `code/` directory.
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage
Run the full pipeline using the orchestration script:
```bash
bash run_pipeline.sh
```

Alternatively, run individual steps:
```bash
python data/download_ebd.py
python data/download_nlcd.py
#... etc
```

## Project Structure
- `data/`: Data download and processing scripts
- `models/`: Model training and evaluation scripts
- `viz/`: Visualization scripts
- `utils/`: Utility functions
- `tests/`: Unit and integration tests
- `notebooks/`: Jupyter notebooks for analysis

## License
[Insert License]

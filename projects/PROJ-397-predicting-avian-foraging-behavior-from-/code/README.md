# Predicting Avian Foraging Behavior from Public eBird Data and Land Cover Maps

## Overview
This project implements a pipeline to predict avian foraging guilds using public eBird observation data and NLCD land cover maps.

## Prerequisites
- Python 3.11+
- pip

## Installation
1. Clone the repository.
2. Navigate to the code directory:
 ```bash
 cd projects/PROJ-397-predicting-avian-foraging-behavior-from-/code
 ```
3. Create a virtual environment and activate it:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
4. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Data
The pipeline automatically downloads required data (eBird EBD, NLCD 2019, Guild Mapping) when executed.
Ensure you have sufficient disk space (approx. 15GB for raw data + processed outputs).

## Running the Pipeline
Execute the full pipeline using the provided shell script:
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
- `data/`: Scripts for downloading, filtering, and merging data.
- `models/`: Scripts for training and evaluating the Random Forest classifier.
- `viz/`: Scripts for generating visualizations (confusion matrix, feature importance, habitat maps).
- `utils/`: Utility functions for configuration and provenance.
- `tests/`: Unit tests for data contracts and metrics.

## License
MIT License
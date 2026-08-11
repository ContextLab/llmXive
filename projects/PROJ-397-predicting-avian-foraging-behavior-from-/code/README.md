# Predicting Avian Foraging Behavior from Public eBird Data and Land Cover Maps

## Project Overview
This project implements a machine learning pipeline to predict avian foraging guilds based on land cover data derived from eBird observations and NLCD land cover maps.

## Prerequisites
- Python 3.11.x
- pip

## Installation
1. Clone the repository.
2. Navigate to the `code` directory:
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

## Running the Pipeline
Execute the full pipeline using the provided shell script:
```bash
bash run_pipeline.sh
```

Alternatively, run individual steps manually:
```bash
python data/download_ebd.py
python data/download_nlcd.py
python data/fetch_guild_mapping.py
python data/filter_top_25.py
python data/merge_and_buffer.py
python data/aggregate.py
python data/extract_top_species.py
python models/train.py
python models/evaluate.py
python viz/plot_confusion.py
python viz/plot_importance.py
python viz/map_habitat.py
```

## Project Structure
- `data/`: Scripts for downloading and processing data.
- `models/`: Scripts for training and evaluating ML models.
- `viz/`: Scripts for generating visualizations.
- `utils/`: Utility functions for configuration and provenance.
- `tests/`: Unit tests for various components.
- `notebooks/`: Jupyter notebooks for analysis.

## Data Sources
- **eBird EBD**: Downloaded from the official eBird S3 bucket.
- **NLCD 2019**: Downloaded from USGS EarthExplorer.
- **Foraging Guilds**: Retrieved from the Cornell Lab of Ornithology.

## License
[Insert License Information Here]
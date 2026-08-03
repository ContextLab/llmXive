# Predicting Avian Foraging Guilds from Public eBird Data and Land Cover Maps

**Project ID**: PROJ-397

## Overview

This project implements a machine learning pipeline to predict avian foraging guilds based on land cover data derived from eBird observations and NLCD (National Land Cover Database) 2019. The pipeline processes raw observational data, merges it with spatial land cover information, trains a Random Forest classifier, and evaluates performance using a rigorous Across-Species Permutation Test.

## Prerequisites

- **Python**: Version 3.11.x is required.
- **System Dependencies**: Ensure `gdal` and `proj` libraries are installed on your system (required by `geopandas` and `rasterio`).
 - Ubuntu/Debian: `sudo apt-get install libgdal-dev libproj-dev`
 - macOS (Homebrew): `brew install gdal proj`
 - Windows: Install via Conda or ensure GDAL is in your PATH.

## Installation

1. **Clone the repository** and navigate to the project directory:
 ```bash
 git clone <repository-url>
 cd projects/PROJ-397-predicting-avian-foraging-behavior-from-/code
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### Running the Full Pipeline

Execute the orchestration script to run the entire workflow from data download to visualization:

```bash
bash run_pipeline.sh
```

This script performs the following steps:
1. Downloads eBird EBD data.
2. Downloads NLCD 2019 land cover data.
3. Fetches foraging guild mappings.
4. Filters data for top 25 species.
5. Merges data and calculates 100m buffer land cover proportions.
6. Filters for statistical power (≥50 observations per species).
7. Aggregates data into species profiles.
8. Trains a Random Forest classifier.
9. Evaluates the model and runs the permutation test.
10. Generates visualizations and reports.

### Running Individual Scripts

You can also run specific steps of the pipeline manually:

- **Data Download**:
 ```bash
 python data/download_ebd.py
 python data/download_nlcd.py
 python data/fetch_guild_mapping.py
 ```

- **Data Processing**:
 ```bash
 python data/fetch_top_25.py
 python data/merge_and_buffer.py
 python data/aggregate.py
 python data/extract_top_species.py
 ```

- **Modeling**:
 ```bash
 python models/train.py
 python models/evaluate.py
 ```

- **Visualization**:
 ```bash
 python viz/plot_confusion.py
 python viz/plot_importance.py
 python viz/map_habitat.py
 ```

## Project Structure

```text
code/
├── data/ # Data processing scripts
│ ├── download_ebd.py
│ ├── download_nlcd.py
│ ├── fetch_guild_mapping.py
│ ├── fetch_top_25.py
│ ├── merge_and_buffer.py
│ ├── aggregate.py
│ └── extract_top_species.py
├── models/ # Machine learning scripts
│ ├── train.py
│ └── evaluate.py
├── viz/ # Visualization scripts
│ ├── plot_confusion.py
│ ├── plot_importance.py
│ └── map_habitat.py
├── utils/ # Utility modules
│ ├── config.py
│ └── provenance.py
├── tests/ # Unit tests
├── notebooks/ # Jupyter notebooks for analysis
├── data/ # Data directories (created at runtime)
│ ├── raw/
│ ├── processed/
│ └── metadata.yaml
├── models/ # Saved models
├── viz/ # Output figures
├── docs/ # Documentation and reports
├── requirements.txt # Python dependencies
├── run_pipeline.sh # Orchestration script
└── README.md
```

## Data Sources

- **eBird Basic Dataset (EBD)**: Downloaded from the Cornell Lab of Ornithology eBird website.
- **NLCD 2019**: Downloaded from the USGS EarthExplorer.
- **Foraging Guild Mapping**: Retrieved from the Cornell Lab of Ornithology (Birds of the World).

## License

This project is licensed under the MIT License.

## Contact

For questions or issues, please open an issue in the repository.
# Predicting Avian Migration Patterns from Publicly Available eBird Data

This project implements an automated science pipeline to predict the first-arrival dates of the American Robin (*Setophaga ruticilla*) in the Lake Powell region using eBird observation data and MODIS environmental data.

## Project Structure

```
.
├── code/ # Source code
│ ├── __init__.py # Logger setup and utilities
│ ├── config.py # Configuration, paths, and checksums
│ ├── data_loader.py # Data ingestion (eBird, MODIS)
│ ├── data_models.py # Data classes (GridCellObservation, etc.)
│ ├── preprocessing.py # Aggregation, first-arrival derivation, feature engineering
│ ├── model_training.py # XGBoost training, SHAP analysis, bootstrap validation
│ └── visualization.py # Map generation
├── data/ # Data directories
│ ├── raw/ # Raw downloaded data and checksums
│ ├── processed/ # Derived datasets (first arrival, features)
│ └── outputs/ # Plots, metrics, reports
├── tests/ # Test suite
│ ├── contract/ # Schema validation tests
│ └── integration/ # End-to-end pipeline tests
├── README.md # This file
└── requirements.txt # Python dependencies
```

## Prerequisites

- Python 3.9+
- pip

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

4. (Optional) Install development tools:
 ```bash
 pip install ruff black pytest
 ```

## Configuration

All configuration is managed in `code/config.py`. Key settings include:
- **Random Seed**: Fixed at 42 for reproducibility.
- **Lake Powell Bounding Box**: Defined by latitude/longitude coordinates.
- **Data Paths**: `data/raw`, `data/processed`, `data/outputs`.
- **Hyperparameters**: Default values for XGBoost and preprocessing.

Modify `code/config.py` if you need to change the region or experimental parameters.

## Usage

### Running the Full Pipeline

Execute the main pipeline script to run the data loading, processing, modeling, and validation steps:

```bash
python code/main.py
```

*Note: `main.py` is not explicitly listed in the task API surface but is the standard entry point implied by the pipeline structure. If it does not exist, run the modules sequentially as described below.*

### Step-by-Step Execution

1. **Data Loading**:
 ```bash
 python code/data_loader.py
 ```
 Downloads eBird and MODIS data to `data/raw/` and verifies checksums.

2. **Preprocessing**:
 ```bash
 python code/preprocessing.py
 ```
 Aggregates data, calculates first-arrival dates with sensitivity sweep, and prepares features. Output: `data/processed/first_arrival_sweep.csv`.

3. **Model Training**:
 ```bash
 python code/model_training.py
 ```
 Trains the XGBoost model, performs SHAP analysis, and runs bootstrap resampling. Outputs: `data/outputs/shap_summary.png`, `data/outputs/permutation_importance.csv`, `data/processed/metrics.json`.

4. **Visualization**:
 ```bash
 python code/visualization.py
 ```
 Generates the regional arrival map. Output: `data/outputs/lake_powell_arrival_map.png`.

### Running Tests

```bash
pytest tests/ -v
```

### Linting and Formatting

```bash
ruff check.
black --check.
```

## Data Sources

- **eBird**: Downloaded via the `datasets` library or verified URL for *Setophaga ruticilla* (2015–2023).
- **MODIS**: Temperature (MOD11A2) and NDVI (MOD13Q1) data, resampled to 0.5° grid.

## Outputs

- `data/processed/first_arrival_sweep.csv`: First-arrival dates for thresholds {3, 5, 10}.
- `data/outputs/shap_summary.png`: Beeswarm plot of feature importance.
- `data/outputs/lake_powell_arrival_map.png`: Spatial visualization of predicted arrival.
- `data/processed/metrics.json`: Model performance metrics and bootstrap confidence intervals.

## License

[Insert License Here]

# Investigating the Relationship Between Stellar Flare Frequency and Exoplanet Atmospheric Retention

This project implements an automated science pipeline to investigate the correlation between stellar flare activity (specifically cumulative XUV flux) and the atmospheric retention of orbiting exoplanets around M-dwarf stars.

## Prerequisites

- Python 3.9+
- pip
- A UNIX-like environment (Linux/macOS) is recommended for path handling, though Windows is supported.

## Installation

1. **Clone the repository** (if applicable) or navigate to the project root.

2. **Create and activate a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

 The `requirements.txt` file pins specific versions for reproducibility, including:
 - `astroquery`: For querying MAST and NASA Exoplanet Archive.
 - `pandas`, `numpy`, `scipy`: For data manipulation and statistical analysis.
 - `pingouin`: For partial correlation analysis.
 - `matplotlib`: For visualization.
 - `pytest`: For testing.

## Project Structure

```text
.
├── code/ # Source code modules
│ ├── config.py # Physical constants and API configuration
│ ├── data_ingestion.py # API fetching and data merging
│ ├── physics.py # Mass loss and retention calculations
│ ├── analysis.py # Statistical correlation
│ ├── visualization.py # Plot generation
│ └──...
├── data/
│ ├── raw/ # Raw downloads from APIs
│ ├── processed/ # Merged, filtered, and derived datasets
│ ├── results/ # Final JSON results and plots
│ └── logs/ # API provenance logs
├── tests/ # Unit tests
├── contracts/ # Schema definitions
├── requirements.txt
└── README.md
```

## Execution

The pipeline is designed to run in three sequential stages. Ensure you have a stable internet connection for the first stage.

### Stage 1: Data Ingestion (User Story 1)
Fetches stellar flare catalogs from MAST (TESS) and exoplanet parameters from the NASA Exoplanet Archive, merges them, and filters for M-dwarfs.

```bash
python code/data_ingestion.py
```
**Output**: `data/processed/merged_filtered.csv`

### Stage 2: Physics Modeling (User Story 2)
Calculates cumulative XUV flux, atmospheric mass loss rates, and retention fractions using the energy-limited escape model.

```bash
python code/physics.py
```
**Output**: `data/processed/derived_physics.csv`

### Stage 3: Analysis & Visualization (User Story 3)
Performs partial Spearman rank correlation (controlling for mass and semi-major axis) and generates visualizations.

```bash
python code/analysis.py
python code/visualization.py
```
**Outputs**:
- `data/results/correlation_results.json` (Includes ρ_partial, p-value, and sensitivity analysis)
- `data/results/flux_vs_retention.png`

### Running the Full Pipeline
You can execute the entire workflow sequentially by running the scripts in order:
```bash
python code/data_ingestion.py && python code/physics.py && python code/analysis.py && python code/visualization.py
```

## Testing

Run the unit test suite using `pytest`:
```bash
pytest tests/ -v
```

## Configuration

Physical constants, API retry parameters, and default thresholds (e.g., efficiency η, initial atmosphere mass) are defined in `code/config.py`. Modify this file to adjust model parameters or API endpoints if necessary.

## Dependencies

See `requirements.txt` for the full list of dependencies and pinned versions.

## License

This research pipeline is provided for scientific investigation purposes.
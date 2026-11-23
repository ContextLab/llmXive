# Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

This project implements a reproducible pipeline to analyze the relationship between OpenStreetMap (OSM) derived urban features and Land Surface Temperature (LST) to study Urban Heat Island (UHI) effects.

## Prerequisites

- Python 3.9+
- pip
- System dependencies: `gdal`, `proj`, `geos` (via `apt`, `brew`, or `conda`)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-125-statistical-analysis-of-openstreetmap-da
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

4. **Configure environment variables**:
 Create a `.env` file in the project root based on `.env.example`:
 ```bash
 cp.env.example.env
 ```
 Edit `.env` to include your API keys:
 - `OVERPASS_API_KEY`: Your Overpass API key (if required by your endpoint)
 - `AWS_ACCESS_KEY` / `AWS_SECRET_KEY`: For satellite data access (if using AWS)

## Project Structure

```
.
├── code/ # Source code
│ ├── config.py # Configuration and environment management
│ ├── ingest.py # Data ingestion (OSM, Satellite, Socioeconomic)
│ ├── eda.py # Exploratory Data Analysis
│ ├── modeling.py # Spatial regression modeling
│ ├── utils/ # Utility modules (logging, memory, env)
│ ├── models/ # Data models and schemas
│ └── scripts/ # Helper scripts (setup, validation, profiling)
├── data/ # Data storage (excluded from git)
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Aligned rasters and intermediate data
│ └── results/ # Final outputs (metrics, reports, plots)
├── tests/ # Unit and integration tests
├── docs/ # Documentation
├── requirements.txt # Python dependencies
├──.env.example # Template for environment variables
└── README.md # This file
```

## CLI Usage Examples

The pipeline is executed via Python scripts located in `code/` and `code/scripts/`.

### 1. Setup Project Directories
Creates the necessary directory structure (`data/raw`, `data/processed`, etc.).
```bash
python code/scripts/setup_dirs.py
```

### 2. Ingest Data
Downloads OSM vector data and satellite thermal imagery for a specific city (e.g., New York City) and generates aligned rasters.
```bash
python code/ingest.py --city "New York City"
```
*Note: Requires valid API keys in `.env`.*

### 3. Run Exploratory Data Analysis (EDA)
Computes correlation matrices, spatial autocorrelation (Moran's I), and variograms.
```bash
python code/eda.py --city "New York City"
```
Outputs:
- `data/results/correlation_matrix.csv`
- `data/results/spatial_stats.json`
- `data/results/eda_report.md`
- `data/results/eda_plots.png`

### 4. Run Spatial Modeling Pipeline
Fits OLS, SAR, and GWR models with spatial cross-validation.
```bash
python code/modeling.py --city "New York City"
```
Outputs:
- `data/results/metrics.csv`
- `data/results/sensitivity_report.md`

### 5. Validate Quickstart
Verifies that the pipeline runs end-to-end and produces expected outputs.
```bash
python code/scripts/validate_quickstart.py
```

### 6. Profile Memory Usage
Analyzes memory consumption of ingestion and modeling scripts.
```bash
python code/scripts/run_memory_profile.py
```

## Configuration

Edit `code/config.py` to adjust:
- `CITIES`: Dictionary of city definitions (bbox, CRS).
- `MAX_BLOCKS`: Maximum number of spatial blocks for sampling.
- `MEMORY_LIMIT_MB`: Memory safety threshold (default: 6000 MB).
- `GWR_BANDWIDTHS`: List of bandwidths for GWR sensitivity analysis.

## Testing

Run the test suite using `pytest`:
```bash
pytest tests/ -v
```

## Contributing

1. Create a feature branch.
2. Implement changes and ensure tests pass.
3. Run linting: `python code/scripts/run_linting.py`.
4. Submit a pull request.

## License

[Insert License Information Here]
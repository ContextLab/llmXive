# Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

A research pipeline to analyze Urban Heat Island (UHI) effects using OpenStreetMap (OSM)
vector data and satellite thermal imagery (MODIS/Landsat). This project implements
spatial regression models, exploratory data analysis, and proxy validity testing.

## Prerequisites

- Python 3.9+
- pip
- Required system libraries: GDAL, GEOS (via `geos` or `proj` packages)
- API Keys: Overpass API (no key required, but rate limits apply), AWS (optional for satellite data)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. Create a virtual environment and activate it:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

4. Configure environment variables:
 ```bash
 cp.env.example.env
 # Edit.env to add your API keys if necessary
 ```

## Project Structure

```
.
├── code/ # Source code
│ ├── config.py # Configuration and constants
│ ├── ingest.py # OSM and satellite data ingestion
│ ├── eda.py # Exploratory spatial analysis
│ ├── modeling.py # Spatial regression models
│ ├── metrics_exporter.py # Metrics export utilities
│ ├── proxy_validity.py # Proxy validity analysis
│ ├── sensitivity_report.py # Sensitivity analysis report generation
│ ├── fetch_literature_bounds.py # Fetch literature bounds
│ ├── stack_output.py # Aligned raster stack creation
│ ├── visualizations.py # Visualization utilities
│ ├── setup_dirs.py # Directory setup script
│ ├── models/ # Data models
│ │ ├── base.py
│ │ ├── city_boundary.py
│ │ ├── raster_covariate.py
│ │ └── temperature_raster.py
│ └── utils/ # Utility modules
│ ├── logging.py
│ ├── memory.py
│ └── env_manager.py
├── data/ # Data directories
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed/aligned data
│ └── results/ # Analysis results and reports
├── tests/ # Test suite
├── docs/ # Documentation
├── requirements.txt # Python dependencies
├──.env.example # Environment variable template
└── README.md # This file
```

## CLI Usage Examples

### 1. Setup Project Directories
Initializes the required directory structure (`data/raw`, `data/processed`, `data/results`, etc.).
```bash
python code/setup_dirs.py
```

### 2. Ingest Data (OSM + Satellite)
Downloads OSM vector data and satellite thermal imagery for a specified city,
aligns them to a common CRS, and creates a raster stack.
```bash
python code/ingest.py --city "New York" --output-dir data/processed --crs EPSG:3857
```
*Options:*
- `--city`: City name (must match definitions in `code/config.py`)
- `--output-dir`: Output directory for processed data
- `--crs`: Target CRS (default: EPSG:3857)

### 3. Run Exploratory Data Analysis (EDA)
Computes correlation matrices, Moran's I, and variograms, then generates a summary report.
```bash
python code/eda.py --input-dir data/processed --output-dir data/results
```
*Options:*
- `--input-dir`: Directory containing aligned GeoTIFFs
- `--output-dir`: Directory for EDA results (CSV, JSON, MD)

### 4. Run Spatial Modeling Pipeline
Fits OLS, SAR, and GWR models, performs spatial cross-validation, and applies FDR correction.
```bash
python code/modeling.py --input-dir data/processed --output-dir data/results --max-blocks 100
```
*Options:*
- `--input-dir`: Directory containing aligned raster data
- `--output-dir`: Directory for model results
- `--max-blocks`: Maximum number of spatial blocks for sampling (default: 100)
- `--seed`: Random seed for reproducibility (default: 42)

### 5. Fetch Literature Bounds
Retrieves literature-derived upper bounds for OSM-only UHI models.
```bash
python code/fetch_literature_bounds.py --output data/literature_bounds.json
```

### 6. Calculate Proxy Validity Gap
Computes the "Unexplained Variance Gap" between literature bounds and observed model performance.
```bash
python code/proxy_validity.py --literature data/literature_bounds.json --metrics data/results/metrics.csv --output data/results/metrics.csv
```

### 7. Generate Sensitivity Report
Visualizes GWR bandwidth sweep results and stability metrics.
```bash
python code/sensitivity_report.py --input data/results/gwr_bandwidth_sweep.json --output data/results/sensitivity_report.md
```

### 8. Export Metrics to CSV
Consolidates cross-validation, FDR, proxy gap, and sensitivity metrics into a single CSV.
```bash
python code/metrics_exporter.py --input-dir data/results --output data/results/metrics.csv
```

## Configuration

Edit `code/config.py` to customize:
- City boundaries (lat/lon boxes)
- CRS settings (EPSG codes)
- `MAX_BLOCKS` (default: 100) for memory safety
- Default paths and timeouts

## Memory Safety

The pipeline respects a 7GB RAM limit by:
- Using spatial block sampling (`MAX_BLOCKS=100` by default)
- Automatically degrading to OLS if memory constraints are exceeded
- Estimating array sizes before allocation

## License

MIT License - See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request
# Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

This project implements a pipeline to ingest OpenStreetMap (OSM) and satellite thermal data,
perform exploratory spatial analysis, and fit spatial regression models to study Urban Heat Island (UHI) effects.

## Prerequisites

- Python 3.9+
- pip (Python package manager)
- A valid Overpass API key (optional for small queries, recommended for production use)
- AWS credentials (optional, for satellite data retrieval if using AWS sources)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd statistical-analysis-of-openstreetmap-data
 ```

2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

4. Configure environment variables:
 - Copy `.env.example` to `.env`:
 ```bash
 cp.env.example.env
 ```
 - Edit `.env` and add your API keys:
 ```
 OVERPASS_API_KEY=your_overpass_key_here
 AWS_ACCESS_KEY_ID=your_aws_key
 AWS_SECRET_ACCESS_KEY=your_aws_secret
 ```

## Project Structure

```
.
├── code/ # Source code
│ ├── config.py # Configuration and path constants
│ ├── ingest.py # Data ingestion (OSM, Satellite)
│ ├── eda.py # Exploratory Data Analysis
│ ├── modeling.py # Spatial regression models
│ ├── utils/ # Utility modules (logging, memory, env)
│ └──...
├── data/ # Data directories
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Aligned raster stacks
│ └── results/ # Analysis outputs (metrics, reports)
├── tests/ # Test suite
├── specs/ # Feature specifications
├── requirements.txt # Python dependencies
└── README.md # This file
```

## CLI Usage

The pipeline is composed of several scripts. Each script can be run independently.

### 1. Setup Project Directories
Creates the necessary directory structure.
```bash
python code/setup_project.py
```

### 2. Ingest Data (OSM & Satellite)
Downloads OSM vector data and satellite thermal imagery, then aligns them to a common raster grid.
```bash
python code/ingest.py --city "New York"
```
*Output*: Aligned GeoTIFFs in `data/processed/` and metadata in `data/metadata.json`.

### 3. Exploratory Data Analysis (EDA)
Computes correlation matrices, spatial autocorrelation (Moran's I), and variograms.
```bash
python code/eda.py
```
*Output*: `data/results/correlation_matrix.csv`, `data/results/spatial_stats.json`, `data/results/eda_report.md`.

### 4. Fetch Literature Bounds
Retrieves upper-bound R² values from literature for proxy validity checks.
```bash
python code/fetch_literature_bounds.py
```
*Output*: `data/literature_bounds.json`.

### 5. Run Spatial Modeling Pipeline
Fits OLS, SAR, and GWR models with spatial cross-validation and sensitivity analysis.
```bash
python code/modeling.py
```
*Output*: Model coefficients, cross-validation metrics, and sensitivity reports in `data/results/`.

### 6. Export Metrics
Consolidates all metrics into a single CSV file.
```bash
python code/metrics_exporter.py
```
*Output*: `data/results/metrics.csv`.

### 7. Generate Reports
- **EDA Report**: `python code/reports/eda_report_generator.py`
- **Sensitivity Report**: `python code/sensitivity_report.py`

## Configuration

Edit `code/config.py` to modify:
- `MAX_BLOCKS`: Maximum number of spatial blocks for sampling (default: 100).
- `CITY_BOUNDS`: Default city boundaries.
- `CRS`: Coordinate Reference System settings.

## Testing

Run the test suite using pytest:
```bash
pytest tests/ -v
```

## License

[Insert License Information Here]
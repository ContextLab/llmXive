# Quickstart Guide: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

This guide provides step-by-step instructions to set up and run the llmXive automated science pipeline for analyzing Urban Heat Island (UHI) effects using OpenStreetMap (OSM) data and satellite thermal imagery.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- A text editor or IDE
- API keys for Overpass API (optional, for high-volume usage) and AWS (if using satellite data from AWS)

## Step 1: Clone and Setup the Project

1. Clone the repository (if not already done):
 ```bash
 git clone <repository-url>
 cd <project-directory>
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

4. Set up environment variables:
 - Copy `.env.example` to `.env`:
 ```bash
 cp.env.example.env
 ```
 - Edit `.env` and add your API keys:
 ```
 OVERPASS_API_KEY=your_overpass_api_key_here
 AWS_ACCESS_KEY_ID=your_aws_access_key
 AWS_SECRET_ACCESS_KEY=your_aws_secret_key
 ```
 *Note: Overpass API keys are optional but recommended for high-volume requests.*

## Step 2: Project Directory Structure

The project uses the following directory structure:

```
<project-root>/
├── code/ # Source code
│ ├── config.py # Configuration settings
│ ├── ingest.py # Data ingestion from OSM and satellite sources
│ ├── eda.py # Exploratory data analysis
│ ├── modeling.py # Spatial regression modeling
│ ├── metrics_exporter.py# Metrics export utilities
│ ├── proxy_validity.py # Proxy validity analysis
│ ├── sensitivity_report.py# Sensitivity analysis reporting
│ ├── fetch_literature_bounds.py# Literature bounds fetching
│ ├── stack_output.py # Aligned raster stack creation
│ ├── visualizations.py # Visualization utilities
│ ├── models/ # Data models (CityBoundary, RasterCovariate, TemperatureRaster)
│ └── utils/ # Utility modules (logging, memory management, environment)
├── data/ # Data storage
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed and aligned rasters
│ ├── results/ # Analysis results (metrics, reports)
│ └── literature_bounds.json# Literature-derived upper bounds
├── tests/ # Test suite
├── docs/ # Documentation
├── requirements.txt # Python dependencies
├──.env.example # Environment variable template
└── README.md # Project overview
```

## Step 3: Configure the Project

Edit `code/config.py` to customize settings:

- **City Definitions**: Add or modify city boundaries (e.g., New York City, Los Angeles).
- **CRS Settings**: Choose between EPSG:3857 (Web Mercator) or local UTM projections.
- **MAX_BLOCKS**: Set the maximum number of spatial blocks for memory safety (default: 100).
- **Output Paths**: Verify paths for `data/processed/`, `data/results/`, etc.

Example city configuration in `code/config.py`:
```python
CITIES = {
 "nyc": {
 "name": "New York City",
 "bbox": (-74.2591, 40.4774, -73.7004, 40.9176), # (min_lon, min_lat, max_lon, max_lat)
 "crs": "EPSG:3857"
 },
 # Add more cities as needed
}
```

## Step 4: Run the Data Ingestion Pipeline (User Story 1)

This step downloads OSM vector data and satellite thermal imagery, then aligns them into a common raster stack.

```bash
cd code
python ingest.py --city nyc
```

**What this does**:
- Downloads buildings, land-use, trees, and roads from OpenStreetMap via the Overpass API.
- Fetches MODIS/Landsat thermal data for the specified city.
- Reprojects all layers to a common CRS (e.g., EPSG:3857).
- Resamples rasters to a standardized 30m resolution.
- Outputs aligned GeoTIFFs to `data/processed/`.
- Generates `data/metadata.json` with fetch timestamps and checksums.

**Expected outputs**:
- `data/processed/nyc_temperature.tif`
- `data/processed/nyc_buildings.tif`
- `data/processed/nyc_landuse.tif`
- `data/processed/nyc_trees.tif`
- `data/processed/nyc_roads.tif`
- `data/metadata.json`

**Troubleshooting**:
- **Rate Limiting**: If Overpass API requests are throttled, the script will automatically retry with exponential backoff.
- **Missing Data**: If >10% of pixels are missing, a WARNING is logged. The pipeline proceeds if ≤10% is missing.
- **CRS Mismatch**: Ensure all input rasters are reprojected to the same CRS as defined in `config.py`.

## Step 5: Run Exploratory Spatial Analysis (User Story 2)

Perform EDA to quantify relationships between OSM-derived features and temperature.

```bash
cd code
python eda.py --city nyc
```

**What this does**:
- Calculates Pearson/Spearman correlation matrices between covariates and temperature.
- Computes Moran's I for spatial autocorrelation of temperature.
- Generates variograms for the target variable.
- Outputs statistics to `data/results/`.

**Expected outputs**:
- `data/results/correlation_matrix.csv`
- `data/results/spatial_stats.json`
- `data/results/eda_report.md`
- Optional: `figures/correlation_heatmap.png`, `figures/variogram_plot.png` (if matplotlib is available)

## Step 6: Run Spatial Regression Modeling (User Story 3)

Fit spatial regression models (OLS, GWR, SAR) with spatial cross-validation.

```bash
cd code
python modeling.py --city nyc
```

**What this does**:
- Samples spatial blocks (default: 100 blocks of 1km x 1km) for memory safety.
- Fits OLS with spatially robust standard errors (HAC).
- Fits SAR (Spatial Lag/Error) models if memory constraints allow.
- Fits GWR (Geographically Weighted Regression) with bandwidth sweep.
- Performs k-fold spatial cross-validation (default: k=5).
- Applies permutation-based FDR correction for multiple comparisons.
- Calculates "Unexplained Variance Gap" against literature bounds.

**Expected outputs**:
- `data/results/metrics.csv` (contains RMSE, MAE, R², adjusted p-values, proxy gap)
- `data/results/sensitivity_report.md` (GWR bandwidth stability analysis)
- Model artifacts saved to `data/results/models/` (if enabled)

**Memory Safety**:
- The pipeline enforces a 7GB RAM limit via `MAX_BLOCKS` (default: 100).
- If memory constraints are exceeded, the pipeline degrades to OLS with HAC and logs `model_type: "OLS_DEGRADED"`.

## Step 7: Review Results

All analysis results are stored in `data/results/`:

- **`metrics.csv`**: Aggregated performance metrics (RMSE, MAE, R²), adjusted p-values, and proxy validity gap.
- **`eda_report.md`**: Summary of EDA findings, including correlation strengths and spatial autocorrelation.
- **`sensitivity_report.md`**: GWR bandwidth sweep results and stability analysis.
- **`spatial_stats.json`**: Moran's I, variogram parameters, and other spatial statistics.

## Step 8: Run Tests (Optional)

Execute the test suite to verify pipeline integrity:

```bash
pytest tests/
```

**Test coverage**:
- Unit tests for Overpass API query construction (`tests/unit/test_ingest.py`).
- Unit tests for raster reprojection and resampling (`tests/unit/test_ingest.py`).
- Unit tests for Moran's I and variogram calculations (`tests/unit/test_eda.py`).
- Integration tests for end-to-end ingestion and modeling pipelines (`tests/integration/`).

## Step 9: Customize and Extend

- **Add New Cities**: Edit `code/config.py` to include additional city boundaries.
- **Adjust Resolution**: Modify resampling parameters in `code/ingest.py` (default: 30m).
- **Change Models**: Edit `code/modeling.py` to include additional regression models or adjust cross-validation folds.
- **Extend EDA**: Add new visualizations in `code/visualizations.py`.

## Troubleshooting Common Issues

- **API Key Errors**: Ensure `.env` contains valid API keys for Overpass and AWS.
- **Memory Errors**: Reduce `MAX_BLOCKS` in `code/config.py` or increase system RAM.
- **Missing Dependencies**: Re-run `pip install -r requirements.txt` to ensure all packages are installed.
- **CRS Mismatches**: Verify that all input rasters share the same CRS as defined in `config.py`.

## Next Steps

- **Literature Review**: Compare your results against the bounds in `data/literature_bounds.json`.
- **Policy Recommendations**: Use findings to inform urban planning strategies for mitigating UHI effects.
- **Contribute**: Submit improvements or bug fixes to the project repository.

## Support

For issues or questions, please refer to the [README.md](../README.md) or open an issue in the project repository.

---

**Version**: 1.0
**Last Updated**: 2024
**Project**: PROJ-125-statistical-analysis-of-openstreetmap-da
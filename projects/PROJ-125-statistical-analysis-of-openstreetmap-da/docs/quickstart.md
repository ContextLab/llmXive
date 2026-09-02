# Quickstart Guide: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

This guide provides step-by-step instructions to set up and run the Urban Heat Island analysis pipeline.

## Prerequisites

- Python 3.9+
- pip (Python package manager)
- Git
- Access to the Overpass API (optional, for OSM data download)
- AWS credentials (optional, for satellite data access)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Set up environment variables**:
 - Copy `.env.example` to `.env`:
 ```bash
 cp.env.example.env
 ```
 - Edit `.env` and add your API keys:
 ```
 OVERPASS_API_KEY=your_overpass_api_key
 AWS_ACCESS_KEY=your_aws_access_key
 AWS_SECRET_KEY=your_aws_secret_key
 ```

## Project Structure

```
.
├── code/ # Source code
│ ├── ingest.py # Data ingestion module
│ ├── eda.py # Exploratory data analysis module
│ ├── modeling.py # Spatial regression modeling module
│ ├── config.py # Configuration settings
│ ├── utils/ # Utility functions
│ └── scripts/ # Helper scripts
├── data/ # Data directories
│ ├── raw/ # Raw data (not tracked in Git)
│ ├── processed/ # Processed data
│ └── results/ # Analysis results
├── docs/ # Documentation
├── tests/ # Test suites
├── requirements.txt # Python dependencies
└── README.md # Project overview
```

## Running the Pipeline

### Step 1: Data Ingestion

Download and process OpenStreetMap and satellite data:

```bash
python code/ingest.py --city "New York"
```

This will:
- Fetch OSM vector data (buildings, land-use, trees, roads)
- Download satellite thermal data (MODIS/Landsat)
- Rasterize and align all layers to a common CRS
- Output aligned GeoTIFFs to `data/processed/`

### Step 2: Exploratory Data Analysis

Perform EDA to understand relationships between features and temperature:

```bash
python code/eda.py --city "New York"
```

This will:
- Compute correlation matrices
- Calculate spatial autocorrelation (Moran's I)
- Generate variograms
- Output results to `data/results/`

### Step 3: Spatial Regression Modeling

Fit spatial regression models and evaluate performance:

```bash
python code/modeling.py --city "New York"
```

This will:
- Fit OLS, SAR, and GWR models
- Perform spatial cross-validation
- Apply multiple-comparison correction
- Generate sensitivity reports
- Output metrics to `data/results/metrics.csv`

## Validation

Validate the pipeline setup and documentation:

```bash
python code/scripts/validate_quickstart.py
```

This script checks:
- Existence of `docs/quickstart.md`
- Validity of installation steps
- Presence of main scripts
- Correctness of output paths

## Troubleshooting

### Common Issues

1. **Missing API Keys**:
 - Ensure `.env` file is configured with valid keys.
 - Run `python code/config.py` to validate environment variables.

2. **Memory Errors**:
 - The pipeline includes memory safety checks. If data exceeds RAM limits, it will automatically sample or degrade to OLS-only mode.
 - Adjust `MAX_BLOCKS` in `config.py` if needed.

3. **Overpass API Rate Limits**:
 - The ingestion module includes exponential backoff for rate limiting.
 - Consider using a local cache for repeated runs.

### Getting Help

- Check the `logs/` directory for detailed error messages.
- Review the `docs/` folder for additional documentation.
- Open an issue on the project repository for support.

## Next Steps

- Customize the analysis for your city of interest.
- Extend the pipeline with additional covariates or models.
- Share your findings and contribute to the project!

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

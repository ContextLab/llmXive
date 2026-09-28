# Assessing the Impact of Data Resolution on Statistical Power in Publicly Available Spatial Datasets

## Project Overview
This research project investigates how data resolution affects statistical power in spatial datasets, using National Land Cover Database (NLCD) data for Colorado as a case study. The project analyzes the relationship between spatial resolution and the ability to detect spatial autocorrelation patterns.

## Research Question
How does modulating the resolution of publicly available spatial datasets impact the statistical power to detect spatial autocorrelation?

## Methodology

### Data Source
- **Dataset**: NLCD 2019 Land Cover (30m resolution)
- **Region**: Colorado, USA
- **Source**: HuggingFace (verified URL)

### Analysis Pipeline
1. **Data Ingestion**: Download and validate NLCD 30m data
2. **Resolution Aggregation**: Generate coarser resolutions (60m, 120m, 240m, 480m) using nearest-neighbor resampling
3. **Binary Transformation**: Create binary indicator maps (Forest vs. Others)
4. **Spatial Autocorrelation**: Calculate Moran's I statistics
5. **Null Distribution**: Generate 1,000 random permutations for H0
6. **Alternative Simulation**: Use Gibbs Sampler with calibrated λ for H1 (1,000 simulations)
7. **Power Calculation**: Compute rejection rate of H1 simulations
8. **Threshold Identification**: Find resolution where power < 0.80
9. **Sensitivity Analysis**: ±10% sweep around inflection point

### Key Metrics
- **Moran's I**: Measure of spatial autocorrelation
- **p-value**: Significance of spatial pattern
- **Statistical Power**: Probability of correctly rejecting H0 when H1 is true
- **Type II Error**: 1 - power (false negative rate)

## Project Structure
```
PROJ-421-assessing-the-impact-of-data-resolution-/
├── code/
│ ├── analysis.py # Core spatial analysis
│ ├── calibration.py # Lambda estimation
│ ├── config.py # Configuration settings
│ ├── data_ingestion.py # Data download
│ ├── models.py # Data models
│ ├── resampling.py # Resolution aggregation
│ ├── utils.py # Utilities
│ ├── visualization.py # Plotting and reporting
│ └──... (additional modules)
├── data/
│ ├── raw/ # Original NLCD data
│ ├── derived/ # Resampled rasters
│ └── results/ # Analysis outputs
├── tests/
│ └── unit/ # Unit tests
└── docs/
 └── IMPLEMENTATION_GUIDE.md
```

## Quick Start

### Prerequisites
- Python 3.8+
- pip
- 7GB+ RAM (for full dataset processing)

### Installation
```bash
# Clone repository
git clone <repository-url>
cd PROJ-421-assessing-the-impact-of-data-resolution-

# Install dependencies
pip install -r code/requirements.txt
```

### Running the Pipeline
```bash
# 1. Setup directories
python code/setup_dirs.py

# 2. Calibrate lambda parameter
python code/calibration.py

# 3. Download data
python code/data_ingestion.py

# 4. Generate coarser resolutions
python code/resampling.py

# 5. Run analysis
python code/analysis.py

# 6. Generate visualizations and reports
python code/visualization.py
python code/generate_final_report.py
```

### Running Tests
```bash
pytest tests/unit/
```

## Key Findings
- Statistical power decreases as resolution becomes coarser
- Threshold identified where power drops below 0.80
- Sensitivity analysis confirms threshold stability within one resolution step
- Type II error increases significantly at lower resolutions

## Outputs
- `data/results/power_results.csv`: Statistical metrics for each resolution
- `data/results/threshold_report.txt`: Resolution threshold where power < 0.80
- `data/results/final_report.md`: Comprehensive analysis report
- `data/results/sensitivity_report.txt`: Sensitivity analysis results
- `figures/power_curve.png`: Power vs. Resolution visualization

## Dependencies
- rasterio
- geopandas
- pysal
- numpy
- scipy
- matplotlib
- pandas
- libpysal
- datasets (HuggingFace)

## License
This project is for research purposes. NLCD data is subject to USGS licensing terms.

## Citation
If you use this code or findings in your research, please cite:
```
[Project Name]: Assessing the Impact of Data Resolution on Statistical Power in Publicly Available Spatial Datasets
```

## Contact
For questions or issues, please open an issue in the repository.

## Acknowledgments
- USGS/National Land Cover Database for data
- HuggingFace for dataset hosting
- PySAL team for spatial analysis tools

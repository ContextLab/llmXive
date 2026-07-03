# Quantifying the Effects of Dark Matter Halo Shapes on Galaxy Formation

## Project Overview
This project analyzes the correlation between dark matter halo shapes (triaxiality, axial ratios) and galaxy formation properties using data from the TNG-100 simulation.

## Hardware Constraints & Feasibility Note
**Important**: Due to hardware constraints (7GB RAM), this pipeline implements **chunked processing and sampling**. This is a documented deviation from the "every FoF halo" requirement specified in FR-001, as per SC-005 feasibility constraints.

- The pipeline processes data in configurable chunks to stay within memory limits.
- Statistical analysis may use representative sampling for large-scale correlations.
- All output artifacts include metadata flags indicating the use of sampling/chunking.

## Setup
1. Ensure Python 3.11 is installed.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Run the pipeline:
 ```bash
 python code/main.py
 ```

## Output
Processed data will be written to `data/processed/`:
- `halo_shapes.csv`: Axial ratios and triaxiality metrics.
- `statistical_results.csv`: Correlation and regression results.
- `sensitivity_report.csv`: Robustness analysis.

## License
Research project for automated science pipeline validation.
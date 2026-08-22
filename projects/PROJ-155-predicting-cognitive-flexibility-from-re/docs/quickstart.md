# Quick Start Guide

This guide provides instructions for setting up and running the **Predicting Cognitive Flexibility from Resting-State Functional Connectivity Variability** pipeline.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- HCP Connectome API Token (see [Data Access](#data-access))

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

## Configuration

### HCP API Token

To access the HCP data, you must obtain an API token from the [Human Connectome Project](https://db.humanconnectome.org/).

1. Log in to the HCP database.
2. Go to **Account Settings** > **API Access**.
3. Generate a token and export it as an environment variable:
 ```bash
 export HCP_API_TOKEN="your_token_here"
 ```
 *Note: On Windows, use `set HCP_API_TOKEN=your_token_here`.*

### Project Configuration

The project uses a central configuration file located at `code/config.py`. Key parameters include:
- **Window size**: 60 seconds (as per FR-003)
- **Step size**: 1 second
- **FD Threshold**: 0.2mm
- **Random Seed**: 42

## Running the Pipeline

The pipeline is executed via the main entry point `code/main.py`.

### Full Pipeline Execution

To run the entire pipeline (Data Ingestion → Preprocessing → Feature Extraction → Analysis):

```bash
python -m code.main
```

This will:
1. Download HCP data (if not present).
2. Preprocess fMRI data and apply the Schaefer atlas.
3. Merge with behavioral data (NIH Toolbox DCCS scores).
4. Filter subjects based on motion (Mean FD > 0.2).
5. Compute dynamic connectivity metrics (sliding window correlations, edge SD, entropy).
6. Run statistical analysis (regression, permutation tests).
7. Generate final results and visualizations.

### Running Specific Stages

You can run individual stages by invoking specific modules directly:

- **Data Download**:
 ```bash
 python -m code.data.download
 ```
- **Preprocessing**:
 ```bash
 python -m code.data.preprocess
 ```
- **Connectivity Metrics**:
 ```bash
 python -m code.features.connectivity
 ```
- **Regression Analysis**:
 ```bash
 python -m code.analysis.regression
 ```

## Output Files

All outputs are generated in the `data/` directory:

- **Raw Data**: `data/raw/` (Downloaded NIfTI and CSV files)
- **Processed Data**:
 - `data/processed/exclusion_log.csv`: Log of excluded subjects.
 - `data/processed/metrics.csv`: Subject-level variability metrics.
 - `data/processed/final_results.csv`: Final merged results with regression coefficients.
- **Results**:
 - `data/results/regression_summary.json`: Aggregated statistical results.
 - `data/results/variability_vs_flexibility.png`: Regression plot.

## Verification

To verify the pipeline execution:

1. Check `data/processed/final_results.csv` for the presence of required columns:
 `Subject_ID`, `Variability_Metric`, `Flexibility_Score`, `Age`, `Sex`, `Mean_FD`, `Total_Scan_Time`, `Predicted_Score`, `Residual`, `Beta_Variability`, `SE_Variability`, `P_Value`.
2. Ensure `data/results/regression_summary.json` contains the `pro_processed` success rate metric.
3. Run the test suite:
 ```bash
 pytest tests/
 ```

## Troubleshooting

- **Data Access Errors**: Ensure `HCP_API_TOKEN` is set correctly and you have permission to access the HCP_1200_Subjects project.
- **Memory Errors**: The pipeline is optimized for <7GB RAM. If errors persist, check `code/features/batch_processor.py` for batch size adjustments.
- **Missing Dependencies**: Re-run `pip install -r requirements.txt` to ensure all packages are installed.

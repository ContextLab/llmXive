# Predicting Personal Sleep Quality from Resting-State fMRI Connectivity

This project implements an automated science pipeline to predict sleep quality scores from functional connectivity data derived from the Human Connectome Project (HCP) 1200 Subjects Release.

## Prerequisites

- **Python**: 3.9 or higher
- **Operating System**: Linux (Ubuntu recommended) or macOS. Windows support is limited due to dependency on `nilearn` and `nibabel`.
- **Disk Space**: ~50GB for raw and processed data.
- **RAM**: Minimum 8GB (16GB recommended for full pipeline execution).

## Environment Setup

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install --upgrade pip
 pip install -r requirements.txt
 ```

 *Note: Ensure `nilearn`, `nibabel`, `scikit-learn`, and `networkx` are installed. If you encounter compilation errors for `nibabel` or `numpy`, ensure you have build tools installed (e.g., `build-essential` on Ubuntu).*

4. **Verify installation**:
 ```bash
 python -c "import nilearn; import nibabel; import numpy; print('Dependencies OK')"
 ```

## Quickstart

The pipeline is orchestrated via `code/main.py`. It handles data download, preprocessing, feature engineering, modeling, and interpretation.

### 1. Run the Full Pipeline

Execute the following command from the project root:

```bash
python code/main.py
```

This script will:
1. **Download Data**: Fetches HCP minimally preprocessed CIFTI files and behavioral data from the HCP server (requires internet access).
2. **Filter Subjects**: Identifies subjects with valid Sleep Scores and excludes those with excessive motion (>0.3mm FD).
3. **Preprocess**: Applies Schaefer parcellation, nuisance regression, and band-pass filtering.
4. **Feature Engineering**: Computes pairwise Pearson correlations and Fisher-z transforms.
5. **Modeling**: Trains an ElasticNet model with nested cross-validation.
6. **Evaluation**: Performs permutation tests and bootstrap resampling.
7. **Interpretation**: Generates a brain surface plot of predictive connections.

### 2. Output Artifacts

Upon successful completion, results will be available in the `data/` directory:

- `data/raw/behavioral/hcp1200_behavioral_data.csv`: Raw behavioral data.
- `data/processed/`: Contains `.npy` files for connectivity vectors and model predictions.
- `data/results/ResultReport.json`: Comprehensive report with metrics, p-values, confidence intervals, and sensitivity analysis.
- `data/results/brain_connectome.svg`: Visualization of top predictive edges.
- `data/logs/pipeline_run.json`: Structured JSON logs of the pipeline execution.

### 3. Running Specific Stages

If you wish to run specific components independently (after the foundation is established):

- **Data Download & Filtering**:
 ```bash
 python code/data/download_hcp.py
 ```
- **Preprocessing & Feature Engineering**:
 ```bash
 python code/data/preprocess.py
 python code/data/feature_engineering.py
 ```
- **Model Training**:
 ```bash
 python code/modeling/train.py
 ```
- **Evaluation**:
 ```bash
 python code/modeling/evaluate.py
 ```
- **Interpretation**:
 ```bash
 python code/modeling/interpret.py
 ```

## Project Structure

```text
.
├── code/
│ ├── __init__.py
│ ├── config.py # Configuration and paths
│ ├── main.py # Pipeline orchestration
│ ├── data/
│ │ ├── __init__.py
│ │ ├── download_hcp.py # Data fetching and filtering
│ │ ├── preprocess.py # Signal processing
│ │ └── feature_engineering.py # Connectivity computation
│ ├── modeling/
│ │ ├── __init__.py
│ │ ├── train.py # Model training
│ │ ├── evaluate.py # Validation and metrics
│ │ ├── interpret.py # Feature importance visualization
│ │ ├── report_generator.py # Result aggregation
│ │ └── validate_plot.py # SVG validation
│ └── utils/
│ ├── __init__.py
│ ├── logging.py # Structured logging
│ └── metrics.py # Statistical utilities
├── data/
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Intermediate features and predictions
│ ├── results/ # Final reports and figures
│ └── logs/ # Execution logs
├── tests/ # Unit, integration, and contract tests
├── requirements.txt # Python dependencies
└── README.md
```

## Configuration

Default parameters (e.g., variance threshold, PCA retention, subject subset size) are defined in `code/config.py`. To modify these:

1. Open `code/config.py`.
2. Adjust the constants (e.g., `VARIANCE_THRESHOLD`, `PCA_RETENTION`).
3. Re-run the pipeline.

## Troubleshooting

- **Memory Errors**: If the pipeline crashes due to RAM limits, reduce the `SUBSET_SIZE` in `code/config.py` or run on a machine with more memory.
- **HCP Download Failures**: Ensure you have a valid HCP account and are authenticated. Check network connectivity.
- **Import Errors**: Ensure the virtual environment is activated and `requirements.txt` was installed without errors.

## License

This project is for research purposes. Data usage is subject to the HCP Terms and Conditions.
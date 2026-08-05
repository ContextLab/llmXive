# Neural Correlates of Error Monitoring During Simulated Navigation

**Project ID**: PROJ-530-neural-correlates-of-error-monitoring-du

This project implements a pipeline to analyze the relationship between error monitoring signals (specifically the Medial Frontal Negativity, MFN) and error magnitude during simulated navigation tasks.

## Prerequisites

- Python 3.11+
- pip (package installer)
- System dependencies for MNE-Python (e.g., `libsndfile` on Linux)

## Installation

1. Clone the repository and navigate to the project root:
 ```bash
 cd projects/PROJ-530-neural-correlates-of-error-monitoring-du
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

## Dependencies

The project relies on the following core libraries (see `requirements.txt` for pinned versions):

- **Data Processing**: `mne`, `numpy`, `pandas`, `scipy`
- **Statistical Modeling**: `statsmodels`, `pingouin`, `pymer4`, `pygam`
- **Visualization**: `matplotlib`, `seaborn`
- **Utilities**: `pyyaml`, `psutil`, `pytest`

## Project Structure

```text
projects/PROJ-530-neural-correlates-of-error-monitoring-du/
├── code/ # Source code modules
│ ├── __init__.py
│ ├── analysis.py # Statistical modeling & validation
│ ├── config_loader.py # Configuration management
│ ├── download.py # Data acquisition
│ ├── logging_config.py # Logging infrastructure
│ ├── preprocess.py # EEG preprocessing & feature extraction
│ ├── setup_directories.py
│ ├── utils.py # Utility functions (seeding, etc.)
│ ├── viz.py # Visualization generation
│ └── linting_config.py
├── data/
│ ├── raw/ # Raw downloaded data (Zenodo)
│ └── processed/ # Preprocessed epochs and features
├── results/
│ ├── models/ # Saved model artifacts
│ ├── figures/ # Generated plots
│ └── diagnostics/ # Validation reports and feasibility metrics
├── tests/ # Unit and integration tests
├── requirements.txt # Python dependencies
└── README.md
```

## Execution Instructions

The pipeline is designed to run sequentially through download, preprocessing, analysis, and visualization steps.

### 1. Setup Directories
Ensure the required directory structure exists:
```bash
python code/setup_directories.py
```

### 2. Download Data
Fetch the Navigation Error Corpus from the configured source (Zenodo).
*Note: If the real source is unavailable, the script will fail loudly as per project constraints.*
```bash
python code/download.py
```

### 3. Preprocess EEG Data
Apply filters, run ICA for artifact removal, and extract MFN features.
```bash
python code/preprocess.py
```

### 4. Run Analysis
Fit the Linear Mixed-Effects model, perform sensitivity analysis, and generate validation reports.
```bash
python code/analysis.py
```

### 5. Generate Visualizations
Create scatter plots and sensitivity analysis figures.
```bash
python code/viz.py
```

### Full Pipeline Run
To execute the entire pipeline in one go (for local testing or CI):
```bash
python code/download.py && python code/preprocess.py && python code/analysis.py && python code/viz.py
```

## Testing

Run the test suite using `pytest`:
```bash
pytest tests/ -v
```

Specific test modules:
- `tests/test_preprocess.py`: Unit tests for angular deviation and MFN extraction.
- `tests/test_analysis.py`: Unit tests for VIF calculation and Bonferroni correction.
- `tests/test_integration.py`: Integration tests for the full pipeline on a subset.

## Configuration

Project configuration is managed via `config.yaml` (if present) or defaults defined in `code/config_loader.py`. Ensure `data/preprocessing.yaml` is populated after running the preprocessing step to track filter and ICA parameters.

## License

This project is part of the llmXive automated science pipeline.

## Contact

For issues related to the pipeline implementation, refer to the project documentation or the `specs/` directory.

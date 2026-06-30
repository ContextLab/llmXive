# PROJ-518: Investigating the Relationship Between Brain Network Dynamics and Creative Problem Solving

## Overview
This project implements a pipeline to analyze the relationship between dynamic brain network flexibility and creative problem-solving abilities using fMRI data. It computes network metrics, performs statistical regression, and generates diagnostic visualizations.

## Project Structure
```
.
├── code/ # Source code
│ ├── analysis/ # Core analysis logic (connectivity, dynamics, statistics)
│ ├── data/ # Data loading and preprocessing
│ ├── scripts/ # Execution scripts
│ ├── utils/ # Logging, versioning, config
│ ├── viz/ # Visualization utilities
│ ├── config.py
│ ├── errors.py
│ └── main.py
├── data/
│ ├── raw/ # Raw fMRI and behavioral data
│ ├── interim/ # Intermediate analysis results
│ └── processed/ # Preprocessed data
├── docs/
│ └── outputs/ # Final reports and figures
├── tests/ # Unit and integration tests
├── requirements.txt
└── README.md
```

## Installation
1. Clone the repository.
2. Create a virtual environment: `python -m venv venv && source venv/bin/activate` (or `venv\Scripts\activate` on Windows).
3. Install dependencies: `pip install -r requirements.txt`.

## Usage
Run the main pipeline:
```bash
python code/main.py
```

Run specific scripts:
- Save analysis results: `python code/scripts/save_analysis_results.py`
- Verify sensitivity: `python code/scripts/verify_sensitivity.py`

## Generated Artifacts
The pipeline produces the following files upon successful execution:

### Data Artifacts (in `data/interim/`)
- `permutation_results.csv`: Results from the permutation-based significance testing, including empirical p-values.
- `sensitivity_summary.csv`: Summary of sensitivity analysis across different window lengths (20, 30, 40), containing correlation coefficients and p-values.

### Output Documents & Figures (in `docs/outputs/`)
- `flexibility_vs_creativity.png`: Scatter plot of network flexibility vs. creativity scores with a regression line and confidence band.
- `model_residuals.png`: Residuals-vs-fitted plot for the regression model diagnostics.
- `model_qq.png`: Q-Q plot for residual normality check.

## Testing
Run the test suite:
```bash
pytest tests/
```

## Configuration
Edit `code/config.py` to adjust parameters such as window sizes, step lengths, and file paths. Environment variables can be used to override defaults via `.env`.

## License
[Insert License Information]

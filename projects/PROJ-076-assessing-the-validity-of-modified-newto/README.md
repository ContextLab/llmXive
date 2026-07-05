# PROJ-076: Assessing the Validity of Modified Newtonian Dynamics with Galaxy Rotation Curves

This project implements an automated science pipeline to assess the validity of Modified Newtonian Dynamics (MOND)
by comparing it against the standard NFW dark matter halo model using SPARC galaxy rotation curve data.

## Project Structure

```
.
├── code/ # Source code
│ ├── __init__.py # Package initialization
│ ├── config.py # Configuration management
│ ├── utils.py # Utility functions
│ ├── download.py # Data download utilities
│ ├── preprocess.py # Data preprocessing
│ ├── models/ # Physical models (MOND, NFW)
│ ├── fit.py # Model fitting engine
│ ├── metrics.py # Goodness-of-fit metrics
│ ├── residuals.py # Residual analysis
│ └── sensitivity.py # Sensitivity analysis
├── data/ # Data files
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed and filtered data
│ └── metadata.yaml # Project metadata
├── results/ # Analysis results
├── tests/ # Test suite
├── state/ # Pipeline state files
└── specs/ # Feature specifications
```

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Verify installation:
 ```bash
 python -c "import mond_pipeline; print('Setup complete!')"
 ```

## Usage

The pipeline executes in phases:

1. **Data Acquisition**: Download and preprocess SPARC data
2. **Model Fitting**: Fit MOND and NFW models to each galaxy
3. **Statistical Analysis**: Compare models using residuals and hypothesis testing

Run the main pipeline:
```bash
python code/main.py # (to be implemented in future tasks)
```

## Running Tests

```bash
pytest tests/ -v
```

## License

This project is for research purposes. See LICENSE for details.

# Quantifying the Impact of Data Artifacts on Planetary Nebula Morphology

This project investigates how common data artifacts (noise, saturation) bias the measurement of planetary nebula morphology parameters (ellipticity, asymmetry). Using synthetic data with known ground truth, we quantify these biases and derive calibration functions to correct them.

## Project Structure

```
.
├── code/ # Source code
│ ├── analysis/ # Statistical analysis, regression, validation
│ ├── io/ # I/O utilities (loading, saving, manifests)
│ ├── metrics/ # Ellipticity and asymmetry calculations
│ ├── synthetic/ # Data generation and artifact injection
│ ├── config.py # Configuration and project paths
│ ├── main.py # CLI entry point
│ └── setup_*.py # Project setup scripts
├── data/ # Data artifacts
│ ├── raw/ # Raw input data (e.g., HST images)
│ ├── synthetic/ # Generated synthetic nebulae
│ ├── processed/ # Processed data, metrics, sweep results
│ └── validation/ # Validation data and reports
├── docs/ # Documentation
│ ├── decisions/ # Architecture and design decisions
│ └── reports/ # Final research reports
├── logs/ # Execution logs
├── tests/ # Test suite
│ ├── unit/ # Unit tests
│ ├── contract/ # Contract tests
│ └── integration/ # Integration tests
├──.gitignore
├── README.md
├── quickstart.md
├── research.md
└── requirements.txt
```

## Quickstart

1. **Environment Setup**:
 ```bash
 python -m venv venv
 source venv/bin/activate
 pip install -r requirements.txt
 ```

2. **Project Initialization**:
 ```bash
 python code/setup_dirs.py
 python code/setup_linting.py
 ```

3. **Run the Full Pipeline**:
 ```bash
 python code/main.py --run-all
 ```

 This executes:
 - **US1**: Noise injection and ellipticity bias analysis
 - **US2**: Saturation injection and asymmetry bias analysis
 - **US3**: Calibration model fitting and validation

4. **View Results**:
 - Processed data: `data/processed/`
 - Validation reports: `data/validation/`
 - Final report: `docs/reports/001-final-bias-analysis.md`
 - Logs: `logs/research.log`

## User Stories

- **US1**: Evaluate noise-induced bias on ellipticity.
- **US2**: Quantify saturation-induced bias on asymmetry.
- **US3**: Derive calibration functions to correct bias.

## Key Artifacts

- `data/synthetic/gt_metadata.json`: Ground truth for synthetic images.
- `data/processed/noise_sweep_data.csv`: Noise bias measurements.
- `data/processed/saturation_sweep.csv`: Saturation bias measurements.
- `data/processed/calibration_functions.json`: Derived correction models.
- `data/processed/run_manifest.json`: Reproducibility audit trail.

## Configuration

See `code/config.py` for pinned seeds, paths, and artifact parameters:
- Noise levels: `{0.01, 0.05, 0.10}`
- Saturation range: `0.0` to `0.5` in `0.05` increments.

## Testing

Run tests with:
```bash
pytest tests/ -v
```

## License

This project is part of the llmXive automated science pipeline.

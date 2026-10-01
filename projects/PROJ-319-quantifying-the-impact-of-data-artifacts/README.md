# Quantifying the Impact of Data Artifacts on Planetary Nebula Morphology

This project quantifies how data artifacts (noise and saturation) bias measurements of planetary nebula morphology (ellipticity and asymmetry). It uses synthetic data with known ground truth to derive calibration functions that correct for these biases.

## Project Structure

```
.
├── code/ # Source code
│ ├── analysis/ # Statistical analysis and regression
│ ├── io/ # I/O utilities (loading/saving)
│ ├── metrics/ # Morphology metrics (ellipticity, asymmetry)
│ ├── synthetic/ # Synthetic data generation and artifact injection
│ ├── config.py # Configuration and project root
│ └── main.py # CLI entry point
├── data/ # Data artifacts
│ ├── raw/ # Raw input data (if any)
│ ├── synthetic/ # Generated synthetic nebulae
│ ├── processed/ # Processed data, metrics, and statistics
│ ├── validation/ # Real HST validation data
│ └── validation_results/ # Validation outputs
├── tests/ # Test suite
│ ├── unit/ # Unit tests
│ ├── contract/ # Contract tests
│ └── integration/ # Integration tests
├── docs/ # Documentation
│ ├── decisions/ # Architecture decisions
│ └── reports/ # Final research reports
├── logs/ # Execution logs
├── requirements.txt # Python dependencies
├── quickstart.md # Quick start guide
└── research.md # Research findings
```

## Quick Start

1. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

2. **Run the Full Pipeline**:
 ```bash
 python code/main.py --run-all
 ```
 This command:
 - Generates synthetic planetary nebulae with known ground truth.
 - Injects noise and saturation artifacts.
 - Measures ellipticity and asymmetry.
 - Computes bias and fits calibration models.
 - Validates results and generates reports.

3. **Run Specific Modes**:
 ```bash
 # Generate synthetic data
 python code/main.py --mode generate --n-images 50 --output data/synthetic

 # Process artifacts (noise/saturation sweeps)
 python code/main.py --mode process --input data/synthetic --output data/processed

 # Calibrate models
 python code/main.py --mode calibrate --input data/processed/metrics.csv --output data/processed/models.json

 # Validate results
 python code/main.py --mode validate --input data/processed/models.json --test-set data/synthetic/validation --output data/processed/validation_results.csv

 # Verify pipeline state
 python code/main.py --mode verify --output logs/verification.log
 ```

## Key Artifacts

- **Synthetic Data**: `data/synthetic/synth_*.fits` and `data/synthetic/gt_metadata.json`
- **Bias Data**: `data/processed/noise_sweep_data.csv`, `data/processed/saturation_sweep.csv`
- **Statistics**: `data/processed/noise_stats.csv`, `data/processed/saturation_stats.csv`
- **Calibration**: `data/processed/calibration_functions.json`
- **Reports**: `docs/reports/001-final-bias-analysis.md`, `data/validation/power_analysis_report.md`

## Configuration

Edit `code/config.py` to adjust:
- Random seeds
- Default paths
- Artifact parameters (noise levels, saturation range)

## Testing

Run the test suite:
```bash
pytest tests/
```

## License

This project is for research purposes.

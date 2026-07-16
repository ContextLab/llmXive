# Quick Start Guide

## Prerequisites
- Python 3.9+
- `pip` for dependency management.
- Access to `data/raw` (OpenNeuro datasets) or network connectivity to download them.

## Installation
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```
3. Set up environment variables (optional):
 ```bash
 cp.env.example.env
 # Edit.env with necessary paths/secrets
 ```

## Running the Pipeline
The main entry point is `code/main.py`. It orchestrates the entire workflow from data acquisition to statistical reporting.

```bash
cd code
python main.py
```

### Execution Flow
1. **Data Setup**: Checks `data/raw` and downloads `ds004230` if missing (streaming).
2. **Preprocessing**: Converts dMRI to connectomes. Attempts EEG download (`ds004231`).
3. **Simulation**: If EEG download fails, runs Wilson-Cowan simulation.
4. **QC**: Filters subjects based on connectivity and signal quality.
5. **Metrics**: Computes structural and avalanche metrics.
6. **Analysis**: Runs correlations and permutation tests.
7. **Reporting**: Generates `correlation_report.csv` or `null_result_report.md`.

## Output Artifacts
- `data/processed/avalanche_metrics.csv`: Per-subject avalanche statistics.
- `data/results/correlation_report.csv`: Statistical associations (if N >= 10).
- `data/results/null_result_report.md`: Null result protocol report (if N < 10).
- `figures/sensitivity_sweep.png`: Stability of results across thresholds.

## Troubleshooting
- **Data Download Failures**: Ensure network connectivity. The pipeline will fail loudly if `ds004230` is unavailable.
- **OOM Errors**: The pipeline uses streaming for large datasets. If issues persist, increase RAM or reduce batch size in `config.py`.
- **Power-Law Convergence**: If fitting fails for a subject, that subject is excluded from correlation analysis (logged in `fitting_report.json`).

## Validation
Run the validation tasks to ensure integrity:
```bash
python main.py --validate-correlation-path
python main.py --validate-null-path
```

## Documentation Location
All documentation resides in `specs/001-investigating-the-impact-of-network-stru/`.
- `research.md`: Research plan and methodology.
- `data-model.md`: Data structures and formats.
- `quickstart.md`: This guide.
# Quickstart Guide

## Getting Started in 5 Minutes

### 1. Clone and Install

```bash
cd projects/PROJ-504-evaluating-the-impact-of-variable-select/
pip install -r requirements.txt
```

### 2. Validate Environment

```bash
python code/quickstart_validator.py
```

This checks:
- Directory structure exists
- Required files are present
- Imports work correctly
- Simulation results integrity (if data exists)

### 3. Run a Mini Pipeline (Pilot)

```bash
python code/verify.py
```

This runs a small-scale simulation to:
- Verify runtime is acceptable (< 5.5 hours for full run)
- Validate CI width constraints
- Generate `simulations_per_condition` count

### 4. Execute Full Pipeline

```bash
# Download datasets and generate simulations
python code/data/pipeline.py

# Run selection methods and calculate power
python code/analysis/metrics.py

# Perform statistical comparisons
python code/analysis/comparators.py

# Generate visualizations
python code/viz/plots.py
```

### 5. View Results

- **Simulation Data**: `data/processed/simulation_results.csv`
- **Plots**: `results/plots/`
- **Final Report**: `results/final_report.md`
- **Sensitivity Analysis**: `results/sensitivity_report.csv`

## Common Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/unit/test_downloader.py -v

# Check code style
black code/ --check
flake8 code/

# Monitor resource usage
python code/utils/watchdog.py --monitor
```

## Configuration

Edit `code/config.py` to change:

```python
# Random seed for reproducibility
seed = 42

# OpenML dataset IDs
openml_ids = [123, 456, 789,...] # 10 datasets

# SNR levels
snr_levels = [0.5, 1.0, 2.0, 5.0]

# Sparsity levels
sparsity_levels = [0.0, 0.2, 0.4]

# Significance threshold
alpha = 0.05
```

## Troubleshooting

### API Timeout
- Retries are automatic with exponential backoff
- Check internet connection
- Verify OpenML API status

### Memory Error
- Reduce `simulations_per_condition`
- Check system RAM availability
- Run with smaller dataset subset

### Runtime Exceeded
- Check `watchdog.py` logs
- Verify early stopping is enabled
- Reduce number of datasets or SNR levels

## Next Steps

1. Read `docs/analysis_protocol.md` for detailed methodology
2. Review `docs/reproducibility_guide.md` for verification steps
3. Explore `results/final_report.md` for findings
4. Run `pytest tests/ -v` to validate implementation

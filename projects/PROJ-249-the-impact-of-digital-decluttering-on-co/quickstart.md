# Quick Start Guide

This guide walks you through setting up and running the Digital Decluttering research pipeline.

## 1. Environment Setup

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

### Installation Steps

1. **Clone the Repository**
 ```bash
 git clone <repository-url>
 cd PROJ-249-the-impact-of-digital-decluttering-on-co
 ```

2. **Install Dependencies**
 ```bash
 pip install -r requirements.txt
 ```

3. **Verify Setup**
 ```bash
 python -c "import code; print('Environment ready')"
 ```

## 2. Data Generation (Validation Mode)

For initial testing, generate synthetic baseline data to validate the pipeline.

```bash
# Generate synthetic baseline data
python code/pipeline/collect_baseline.py
```

**Expected Output**:
- `data/raw/synthetic_baseline.csv`: Contains baseline metrics for simulated participants.

**Verification**:
```bash
head data/raw/synthetic_baseline.csv
# Should show columns: participant_id, metric_type, value, timestamp
```

## 3. Instrument Validation

Ensure scoring functions work correctly against synthetic data.

```bash
python code/validation/validate_instruments.py
```

**Expected Output**:
- Console logs showing validation status for SART, Ospan, PSS-10, and PANAS.
- `results/validation_report.json`: Detailed validation results.

## 4. Compliance Logging

Process and aggregate compliance logs.

```bash
# Parse logs
python code/compliance/parse_logs.py

# Aggregate scores
python code/pipeline/aggregate_compliance.py
```

**Expected Output**:
- `data/processed/compliance_scores.csv`: Daily and weekly compliance metrics.

## 5. Statistical Analysis

Run the full analysis pipeline.

```bash
# Merge data
python code/pipeline/merge_data.py

# Calculate change scores
python code/analysis/change_scores.py

# Run bootstrap analysis
python code/analysis/bootstrap_ci.py

# Apply corrections
python code/analysis/holm_bonferroni.py

# Calculate effect sizes
python code/analysis/effect_sizes.py

# Generate statistical summary
python code/analysis/statistical_summary.py
```

**Expected Output**:
- `results/statistical_summary.json`: Aggregated statistical results.

## 6. Reporting

Generate the final research report.

```bash
python code/report/generate_report.py
```

**Expected Output**:
- `results/final_report.md`: Comprehensive research report.
- `results/power_analysis.json`: Power simulation results.
- `results/sensitivity_analysis_report.md`: Sensitivity analysis.

## 7. Visualization

Generate plots for the results.

```bash
python code/viz/generate_plots.py
```

**Expected Output**:
- `figures/`: Directory containing boxplots and distribution charts.

## 8. Running Tests

Verify the implementation with the test suite.

```bash
pytest tests/ -v
```

## Troubleshooting

- **Missing Data Files**: Ensure you ran `collect_baseline.py` first.
- **Import Errors**: Verify `requirements.txt` is installed and paths are correct.
- **Permission Errors**: Check write permissions for `data/` and `results/` directories.

## Next Steps

- Replace synthetic data with real participant data.
- Customize analysis parameters in `code/config/env_config.py`.
- Extend compliance rules in `code/compliance/rules_engine.py`.

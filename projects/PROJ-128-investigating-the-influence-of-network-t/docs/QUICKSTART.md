# Quick Start Guide

This guide provides step-by-step instructions to get the pipeline running and validated.

## Prerequisites

- Python 3.9 or higher
- pip package manager
- At least 14GB free disk space (for data) [UNRESOLVED-CLAIM: c_0fd20fda — status=not_enough_info]
- ~7GB RAM available [UNRESOLVED-CLAIM: c_0b9cbca7 — status=not_enough_info]
- Internet connection (for initial data download)

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd PROJ-128-investigating-the-influence-of-network-t

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Verify Installation

```bash
# Check all dependencies are installed
python -c "import nilearn, networkx, sklearn, pandas, numpy, scipy, statsmodels, yaml; print('✓ All dependencies installed')"

# Verify directory structure
python code/setup_data_structure.py
```

Expected output:
```
✓ Created directory: data/raw
✓ Created directory: data/processed
✓ Created directory: data/logs
✓ Created directory: contracts
✓ Schema files created
```

## Step 3: Run the Pipeline

```bash
# Execute the main pipeline
python code/main.py
```

### What Happens:

1. **Data Download**: Downloads HCP data from OpenNeuro (if not already present)
2. **Preprocessing**:
 - Structural: Calculates graph metrics (efficiency, clustering, modularity)
 - Functional: Computes sliding-window correlations and LOO K-Means states
3. **Analysis**: Correlates structural and dynamic metrics with FDR correction
4. **Robustness**: Performs sensitivity analysis (window length, density threshold)
5. **Reporting**: Generates final report with associational language audit

### Expected Duration:

- Data download: 30-60 minutes (depending on network) [UNRESOLVED-CLAIM: c_69bccf63 — status=not_enough_info]
- Processing: 1-2 hours (single subject) to 10+ hours (full cohort) [UNRESOLVED-CLAIM: c_fc863359 — status=not_enough_info]
- Analysis: 5-10 minutes [UNRESOLVED-CLAIM: c_5a93b798 — status=not_enough_info]

## Step 4: Validate Outputs

```bash
# Run validation script
python code/validate_quickstart.py
```

### Validation Checks:

- ✓ `data/processed/structural_metrics.csv` exists and is valid
- ✓ `data/processed/dynamic_metrics.csv` exists and is valid
- ✓ `data/processed/correlation_results.csv` exists and is valid
- ✓ `data/processed/sensitivity_comparison.csv` exists and is valid
- ✓ `data/reports/final_report.json` passes schema validation
- ✓ No placeholder or synthetic data detected

### Sample Output:

```
[VALIDATION] Checking required files...
✓ data/processed/structural_metrics.csv (2.3 MB) [UNRESOLVED-CLAIM: c_049e5a0e — status=not_enough_info]
✓ data/processed/dynamic_metrics.csv (1.8 MB) [UNRESOLVED-CLAIM: c_c2c3fb2f — status=not_enough_info]
✓ data/processed/correlation_results.csv (0.5 MB) [UNRESOLVED-CLAIM: c_e810f74a — status=not_enough_info]
✓ data/processed/sensitivity_comparison.csv (0.2 MB) [UNRESOLVED-CLAIM: c_837c939b — status=not_enough_info]
✓ data/reports/final_report.json (1.1 MB) [UNRESOLVED-CLAIM: c_7ce80310 — status=not_enough_info]

[VALIDATION] Schema validation...
✓ structural_metrics.csv: All required columns present
✓ dynamic_metrics.csv: All required columns present
✓ correlation_results.csv: r, p, FDR columns present
✓ final_report.json: All mandatory fields present

[VALIDATION] Data integrity check...
✓ No synthetic/fake data detected
✓ All values within expected ranges

[SUCCESS] Pipeline validation complete!
```

## Step 5: Explore Results

### Key Output Files:

1. **Structural Metrics**: `data/processed/structural_metrics.csv`
 - Columns: subject_id, global_efficiency, clustering_coefficient, modularity

2. **Dynamic Metrics**: `data/processed/dynamic_metrics.csv`
 - Columns: subject_id, dwell_time, visited_states, state_transitions

3. **Correlation Results**: `data/processed/correlation_results.csv`
 - Columns: metric_pair, r_value, p_value, fdr_significant

4. **Sensitivity Analysis**: `data/processed/sensitivity_comparison.csv`
 - Columns: metric_pair, baseline_r, sensitivity_r, absolute_difference

5. **Final Report**: `data/reports/final_report.json`
 - Contains summary statistics, correlation matrix, sensitivity metrics, exclusion log

### Example Analysis:

```python
import pandas as pd

# Load correlation results
corr = pd.read_csv('data/processed/correlation_results.csv')

# View significant findings (FDR-corrected)
significant = corr[corr['fdr_significant'] == True]
print(significant)

# Load sensitivity analysis
sens = pd.read_csv('data/processed/sensitivity_comparison.csv')
print(f"Max absolute difference: {sens['absolute_difference'].max():.4f}")
```

## Troubleshooting

### Issue: Data download fails

**Solution**:
- Check internet connection
- Verify OpenNeuro API access
- Increase timeout in `code/preprocess/loader.py` if needed

### Issue: Out of memory

**Solution**:
- Reduce batch size in `code/config.py`
- Use `code/main_optimized.py` for memory-efficient processing
- Process subjects sequentially instead of in parallel

### Issue: Convergence failure

**Solution**:
- Check exclusion log: `data/logs/exclusion_log.json`
- Adjust K-means parameters (k, max_iter) in `code/config.py`
- Verify data quality (sparsity >90% may cause exclusion [UNRESOLVED-CLAIM: c_ea1927ab — status=not_enough_info])

### Issue: No significant findings after FDR

**Solution**:
- This is valid; the report should explicitly state this (T028)
- Review correlation strength and sample size
- Check for data quality issues

## Next Steps

1. **Read Documentation**: Explore `docs/ARCHITECTURE.md` for system design
2. **Run Tests**: Execute `pytest tests/` for validation
3. **Contribute**: See `docs/CONTRIBUTING.md` for guidelines
4. **Customize**: Adjust parameters in `code/config.py` for your needs

## Support

For issues or questions:
- Check existing issues on GitHub
- Open a new issue with detailed description
- Review `docs/CONTRIBUTING.md` for contribution guidelines

## License

[Insert License Information]

---

**Note**: This pipeline is designed for **CPU-only** execution. Ensure your environment does not attempt GPU acceleration.

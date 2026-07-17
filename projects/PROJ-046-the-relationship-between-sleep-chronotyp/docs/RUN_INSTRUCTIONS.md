# Detailed Run Instructions

## Prerequisites Check
Before running, ensure:
1. R 4.3+ is installed: `R --version`
2. Python 3.9+ is installed: `python --version`
3. `renv` is initialized: `ls -la renv.lock` (should exist after running setup script)

## Step-by-Step Execution

### 1. Environment Setup
```bash
# Install R packages and initialize renv
python code/00_setup_r_env.py
```
*Wait for "R environment initialized successfully" message.*

### 2. Data Preparation
Ensure `data/raw/merged_data.csv` exists and contains the required columns.
```bash
head data/raw/merged_data.csv
```

### 3. Execution Sequence
Run the following commands sequentially. **Do not skip steps.**

```bash
# Ingestion
echo "Running Ingestion..."
Rscript code/01_ingest.R

# Classification
echo "Running Classification..."
Rscript code/02_classify.R

# Exclusion Check (Critical Gate)
echo "Checking Exclusion Rates..."
Rscript code/02.5_aggregate_exclusions.R
# If this script exits with non-zero, the pipeline has stopped due to >20% exclusions.

# Reliability
echo "Calculating Reliability..."
Rscript code/02.6_reliability.R

# Analysis
echo "Running ANCOVA..."
Rscript code/03_analysis.R
# This step may abort if VIF > 2.

# Report Generation
echo "Generating Report..."
python code/04_render_report.py

# Validation
echo "Validating Report..."
python code/05_validate_report.py
```

### 4. Output Verification
- Check `reports/chronotype_moral_analysis.html` exists.
- Check `data/derived/ancova_results.csv` for p-values < 0.01.
- Review `logs/pipeline.log` for any warnings.

## CI/CD Integration
For CI runners (2 CPU, 7GB RAM):
```bash
# Set environment variables for CI
export CI_RUN=true

# Run validation
python code/07_verify_ci_compatibility.py
python code/06_validate_quickstart.py

# Run full pipeline (if data is available in CI)
#... (execution sequence as above)
```

## Troubleshooting Common Errors
- **"R not found"**: Add R to your PATH.
- **"Missing columns"**: Verify `data/raw/merged_data.csv` headers match the spec.
- **"VIF > 2"**: Check for multicollinearity in covariates; consider removing redundant variables.
- **"renv not initialized"**: Re-run `00_setup_r_env.py`.

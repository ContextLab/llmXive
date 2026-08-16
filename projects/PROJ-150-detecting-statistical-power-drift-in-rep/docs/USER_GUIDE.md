# User Guide: Statistical Power Drift Analysis

## Quick Start

This guide walks you through running the statistical power drift analysis pipeline.

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Step 1: Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd PROJ-150-detecting-statistical-power-drift-in-rep

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Run the Pipeline

Execute the main script to run the full analysis:

```bash
python code/main.py
```

This command will:
1. Download the OSF Reproducibility Project dataset.
2. Validate and preprocess the data.
3. Fit the Linear Mixed-Effects Model.
4. Perform robustness checks (permutation tests).
5. Generate visualizations and summary reports.

### Step 3: Review Results

After completion, check the `results/` directory for:
- `lmm_final_summary.json`: Statistical summary of the drift analysis.
- `power_drift_scatter.png`: Visualization of power drift over time.
- `permutation_pvalue.json`: Results from the non-parametric validation.

## Understanding the Output

### LMM Summary (`lmm_final_summary.json`)

```json
{
 "slope_year": -0.002,
 "se_year": 0.001,
 "ci_lower": -0.004,
 "ci_upper": 0.000,
 "p_value_lrt": 0.032,
 "chi2_statistic": 4.56,
 "df_diff": 1
}
```

- **slope_year**: The estimated change in statistical power per year.
- **p_value_lrt**: The p-value from the Likelihood-Ratio Test. A value < 0.05 indicates significant drift.

### Visualization

The `power_drift_scatter.png` plot shows:
- **X-axis**: Publication year.
- **Y-axis**: Residual power (power after accounting for effect size and sample size).
- **Trend line**: The fitted drift slope. A downward slope indicates decreasing power over time.

## Troubleshooting

### Data Download Fails

Ensure you have an active internet connection and that the Hugging Face Hub is accessible. The script will fail loudly if the data cannot be fetched.

### Model Convergence Warnings

If the LMM fails to converge, the pipeline will attempt to re-fit with reduced random effects. Check the logs for specific warnings about excluded factors.

### Memory Issues

The permutation test (10,000 iterations) may require significant memory. If you encounter memory errors, the script will automatically fall back to 1,000 iterations and flag the result as "approximate".

## Advanced Usage

### Running Individual Steps

You can run specific steps of the pipeline independently:

```bash
# Preprocess data only
python code/preprocess.py

# Fit model and generate summary only
python code/compute_trends.py

# Generate visualizations only
python code/visualize.py
```

### Customizing Parameters

To modify the number of permutations or alpha thresholds, edit the `code/robustness.py` file and adjust the `N_PERMUTATIONS` and `ALPHA_THRESHOLDS` constants.

## Support

For issues or questions, please refer to the project's issue tracker or consult the methodology documentation at `docs/METHODOLOGY_LMM.md`.
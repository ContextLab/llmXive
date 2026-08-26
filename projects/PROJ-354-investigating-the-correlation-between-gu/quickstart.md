# Quick Start Guide

## Prerequisites

- Python 3.10 or higher
- UK Biobank access credentials (token)
- Minimum 7GB RAM, 14GB disk space
- pip and virtualenv

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-354-investigating-the-correlation-between-gu
 ```

2. **Create virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Configure UK Biobank token**:
 - Option 1: Set environment variable
 ```bash
 export UK_BIOBANK_TOKEN="your_token_here"
 ```
 - Option 2: Create `.env` file in project root
 ```
 UK_BIOBANK_TOKEN=your_token_here
 ```
 - Option 3: Use keyring (recommended for security)
 ```bash
 python -c "from code.utils.credentials import set_token_to_keyring; set_token_to_keyring('your_token_here')"
 ```

5. **Verify installation**:
 ```bash
 python -c "import code.config; print('Configuration loaded successfully')"
 ```

## Execution Pipeline

The pipeline consists of three main phases:

### Phase 1: Power Analysis (Validation Gate)

Run power analysis to validate methodology before processing real data:

```bash
python code/power_analysis.py
```

**Expected Output**: `results/validation/power_analysis_report.json`

**Gate Criteria**: Calculated power must be >= 0.8 to proceed.

### Phase 2: Data Download

Download UK Biobank microbiome and cognitive data:

```bash
python code/download.py
```

**Expected Outputs**:
- `data/raw/microbiome_raw.parquet`
- `data/raw/cognitive_raw.parquet`

**Note**: This step may take several hours depending on network speed.

### Phase 3: Preprocessing

Process raw data with zero-replacement and ILR transformation:

```bash
python code/preprocess.py
```

**Expected Outputs**:
- `data/processed/zero_replaced_counts.parquet`
- `data/processed/ilr_coordinates.parquet`
- `data/processed/cohort_with_age_groups.parquet`
- `data/processed/cohort_retention_log.json`

### Phase 4: Statistical Analysis

Run association analysis with confounder control:

```bash
python code/analysis.py
```

**Expected Outputs**:
- `results/associations/main_effects_lasso.parquet`
- `results/associations/main_effects_ridge.parquet`
- `results/associations/main_effects.parquet`
- `results/associations/interaction_effects.parquet`
- `results/sensitivity/over_control_report.json`
- `results/sensitivity/threshold_sweep_report.json`
- `results/sensitivity/interaction_comparison_report.json`
- `results/sensitivity/model_selection_report.json`

### Phase 5: Visualization

Generate Manhattan-style plots and other visualizations:

```bash
python code/visualize.py
```

**Expected Output**:
- `results/plots/manhattan_plot.png`

## Complete Pipeline Execution

To run the entire pipeline in sequence:

```bash
# 1. Power analysis (validation gate)
python code/power_analysis.py

# 2. Download data
python code/download.py

# 3. Preprocess data
python code/preprocess.py

# 4. Run analysis
python code/analysis.py

# 5. Generate visualizations
python code/visualize.py
```

## Validation

### Run Tests

Execute unit tests to verify implementation:

```bash
pytest tests/ -v
```

### Check Data Integrity

Validate downloaded and processed data:

```bash
python -c "from code.utils.hygiene import validate_data_integrity; validate_data_integrity()"
```

## Troubleshooting

### Memory Issues

If encountering memory errors:
- Ensure you have at least 7GB available RAM
- Check that streaming is enabled in configuration
- Reduce batch size in `code/config.py`

### UK Biobank Token Errors

If token authentication fails:
- Verify token is correctly set in environment or keyring
- Check token expiration date
- Regenerate token from UK Biobank portal

### Missing Dependencies

If import errors occur:
```bash
pip install -r requirements.txt --upgrade
```

## Output Interpretation

### Power Analysis Report

- `calculated_power`: Statistical power of the study design
- `required_sample_size`: Minimum sample size needed for 80% power
- `pass`: Boolean indicating if power gate is satisfied (>= 0.8)

### Association Results

- `beta`: Effect size estimate
- `p_value`: Raw p-value
- `adj_p_value`: Benjamini-Hochberg corrected p-value
- `causality_claim`: Always `false` (observational study)

### Sensitivity Analysis

- `over_control_report`: Comparison of full vs. reduced models
- `threshold_sweep_report`: Association counts at different p-value thresholds
- `interaction_comparison_report`: Age-interaction vs. main effects comparison
- `model_selection_report`: Lasso vs. Ridge model comparison

## Next Steps

1. Review results in `results/` directory
2. Examine `results/plots/manhattan_plot.png` for significant associations
3. Read `results/sensitivity/` reports for robustness checks
4. Consult `docs/api_reference.md` for detailed API documentation
5. Refer to `docs/README.md` for project overview and methodology details

# Quick Start Guide

This guide provides step-by-step instructions to run the chess Elo rating prediction pipeline.

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Internet connection (for downloading Lichess data)

## Step 1: Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd <project-directory>

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import pandas, numpy, sklearn, statsmodels, chess; print('Environment ready')"
```

## Step 2: Create Directory Structure

The project structure is created automatically, but you can verify:

```bash
python code/src/setup_structure.py
```

This creates:
- `data/raw/` - Raw downloaded PGN files
- `data/processed/` - Processed datasets
- `data/results/` - Model outputs and reports
- `specs/contracts/` - Data schemas
- `tests/unit/`, `tests/contract/`, `tests/integration/` - Test directories

## Step 3: Download and Parse Data

```bash
python code/src/data/parse.py
```

This script will:
1. Verify dataset URL reachability
2. Sample games to check for required metadata
3. Parse PGN files and extract features
4. Save processed data to `data/processed/games.parquet`

**Expected Output**:
- Console logs showing progress
- `data/processed/games.parquet` containing game records with columns:
 - `game_id`, `white_rating`, `black_rating`, `eco_code`
 - `avg_move_time_white`, `avg_move_time_black`
 - `material_imbalance_move5`, `outcome`
 - `elo_expected_prob`, `outcome_deviation`

## Step 4: Process and Calculate Metrics

```bash
python code/src/data/process.py
```

This calculates:
- Expected Elo probabilities using the formula: `P = 1 / (1 + 10^((R2-R1)/400))`
- Outcome deviations: `(actual_result - expected_probability)`
- Applies probability capping for numerical stability

**Expected Output**:
- Updated `data/processed/games.parquet` with calculated metrics
- Validation against `game_record.schema.yaml`

## Step 5: Fit Statistical Models

```bash
python code/src/models/fit.py
```

This fits:
- Gaussian GLM (Gaussian family)
- Ridge Regression
- Maps ECO codes to opening families
- Applies Benjamini-Hochberg FDR correction

**Expected Output**:
- Model coefficients and statistics
- `data/results/model_metrics.json` with:
 - `model_type`, `coefficients`, `p_values`
 - `r_squared`, `aic`, `cross_validation_scores`

## Step 6: Validate Models

```bash
python code/src/models/validate.py
```

This performs:
- 5-fold cross-validation
- Calculates R² and MSE variance across folds
- Checks for model instability (SC-003 threshold: std_dev_r2 < 0.05)

**Expected Output**:
- Cross-validation results in `data/results/model_metrics.json`
- Console output with validation metrics
- RuntimeError if model instability detected

## Step 7: Generate Reports and Visualizations

```bash
python code/src/reports/generate_plots.py
```

This creates:
- Residual plots
- Predicted vs. actual scatterplots
- Feature importance rankings
- Diagnostic report summary

**Expected Output**:
- PNG plots in `data/results/`:
 - `residuals.png`
 - `predicted_vs_actual.png`
 - `feature_importance.png`
- `data/results/diagnostics.json` with summary statistics

## Step 8: Run Sensitivity Analysis

```bash
python code/src/reports/sensitivity.py
```

This performs:
- Threshold sweep analysis
- Jaccard index calculation for significant predictors
- Sensitivity report generation

**Expected Output**:
- `data/results/sensitivity_report.json`

## Step 9: Validate All Contracts

```bash
python code/src/validation/validate_contracts.py
```

This validates:
- All processed datasets against their schemas
- Ensures data integrity throughout the pipeline

**Expected Output**:
- Console output with validation results
- SchemaValidationError if any contract fails

## Step 10: Run Tests

```bash
# Run all tests
pytest code/tests/ -v

# Run specific test suites
pytest code/tests/unit/ -v # Unit tests
pytest code/tests/contract/ -v # Contract tests
pytest code/tests/integration/ -v # Integration tests
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**:
 ```bash
 pip install -r requirements.txt --upgrade
 ```

2. **Data Download Failures**:
 - Check internet connection
 - Verify Lichess API is accessible
 - The script includes exponential backoff retry logic

3. **Model Instability Error**:
 - If you see "SC-003 Threshold Exceeded: Model instability detected",
 the model has high variance across folds. Consider:
 - Increasing dataset size
 - Adjusting regularization parameters
 - Checking for data quality issues

4. **Schema Validation Errors**:
 - Ensure all required columns are present
 - Check for null values in critical fields
 - Verify data types match schema definitions

### Performance Tips

- For large datasets, the pipeline includes sampling logic
- Monitor RAM usage (target: < 7GB)
- Use `--sample` flag if available for testing with smaller subsets

## Next Steps

- Review generated plots and diagnostic reports
- Analyze model coefficients and p-values
- Explore feature importance rankings
- Conduct additional sensitivity analyses
- Consider extending the model with additional features

## Support

For issues or questions:
- Check the `README.md` for detailed documentation
- Review the `specs/` directory for design documents
- Examine test files in `tests/` for usage examples
- Consult the project's issue tracker
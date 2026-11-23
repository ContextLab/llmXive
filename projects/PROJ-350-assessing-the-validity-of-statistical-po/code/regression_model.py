"""
Regression modeling module for T032.

Implements multiple linear regression using statsmodels.OLS to identify
predictors of Power Gap (field, effect_size_domain), explicitly excluding
sample_size_category to avoid mathematical coupling.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import VarianceInflationFactor

from regression import load_power_gap_data, preprocess_for_regression
from power_analysis_guardrail import load_power_analysis, filter_valid_records

logger = logging.getLogger(__name__)

class RegressionModelError(Exception):
    """Custom exception for regression modeling errors."""
    pass

def load_preprocessed_data() -> pd.DataFrame:
    """
    Load and preprocess data for regression.
    
    Returns:
        DataFrame with power_gap as target and predictors (field, effect_size_domain).
    
    Raises:
        RegressionModelError: If data cannot be loaded or preprocessed.
    """
    try:
        # Load power analysis data
        power_data = load_power_analysis()
        if power_data is None:
            raise RegressionModelError("Failed to load power analysis data")
        
        # Filter valid records (ensure minimum sample size)
        valid_records = filter_valid_records(power_data)
        if len(valid_records) < 30:
            raise RegressionModelError(
                f"Insufficient valid records: {len(valid_records)} < 30"
            )
        
        # Preprocess for regression
        df = preprocess_for_regression(valid_records)
        
        # Verify sample_size_category is excluded
        if 'sample_size_category' in df.columns:
            raise RegressionModelError(
                "sample_size_category must be excluded from regression predictors"
            )
        
        logger.info(f"Loaded {len(df)} records for regression")
        return df
    except Exception as e:
        raise RegressionModelError(f"Data loading/preprocessing failed: {e}")

def build_regression_model(df: pd.DataFrame) -> Tuple[sm.OLS, pd.DataFrame]:
    """
    Build multiple linear regression model with power_gap as target.
    
    Predictors: field (dummies), effect_size_domain (dummies)
    Excluded: sample_size_category (to avoid mathematical coupling)
    
    Args:
        df: Preprocessed DataFrame with power_gap and predictors.
    
    Returns:
        Tuple of (fitted OLS model, results summary DataFrame)
    
    Raises:
        RegressionModelError: If model fitting fails.
    """
    try:
        # Define target and features
        target_col = 'power_gap'
        if target_col not in df.columns:
            raise RegressionModelError(f"Target column '{target_col}' not found")
        
        # Identify predictor columns (exclude target and non-predictor columns)
        exclude_cols = ['study_id', 'power_gap']
        predictor_cols = [col for col in df.columns if col not in exclude_cols]
        
        # Explicitly verify sample_size_category is not in predictors
        if 'sample_size_category' in predictor_cols:
            raise RegressionModelError(
                "sample_size_category must be excluded from regression predictors"
            )
        
        logger.info(f"Using predictors: {predictor_cols}")
        
        # Prepare features (X) and target (y)
        X = df[predictor_cols]
        y = df[target_col]
        
        # Add constant for intercept
        X = sm.add_constant(X)
        
        # Fit OLS model
        model = sm.OLS(y, X)
        results = model.fit()
        
        # Create results summary DataFrame
        results_df = pd.DataFrame({
            'predictor': results.params.index,
            'coefficient': results.params.values,
            'std_error': results.std_errors.values,
            't_statistic': results.tvalues.values,
            'p_value': results.pvalues.values,
            'significant': results.pvalues.values < 0.05
        })
        
        logger.info(f"Model fitted: R² = {results.rsquared:.4f}")
        return results, results_df
    except Exception as e:
        raise RegressionModelError(f"Model fitting failed: {e}")

def run_regression_analysis() -> Dict[str, Any]:
    """
    Main function to run regression analysis.
    
    Returns:
        Dictionary containing model results, diagnostics, and metadata.
    
    Raises:
        RegressionModelError: If any step fails.
    """
    # Load and preprocess data
    df = load_preprocessed_data()
    
    # Build and fit model
    results, results_df = build_regression_model(df)
    
    # Prepare output
    output = {
        'metadata': {
            'model_type': 'OLS',
            'target': 'power_gap',
            'predictors': [col for col in results_df['predictor'] if col != 'const'],
            'excluded_predictors': ['sample_size_category'],
            'n_obs': results.nobs,
            'r_squared': float(results.rsquared),
            'adj_r_squared': float(results.rsquared_adj),
            'f_statistic': float(results.f_pvalue),
            'timestamp': str(pd.Timestamp.now())
        },
        'coefficients': results_df.to_dict(orient='records'),
        'model_summary': results.summary().as_html()
    }
    
    logger.info("Regression analysis completed successfully")
    return output

def write_results(output: Dict[str, Any], output_path: Path) -> None:
    """
    Write regression results to JSON file.
    
    Args:
        output: Results dictionary from run_regression_analysis.
        output_path: Path to output file.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        logger.info(f"Results written to {output_path}")
    except Exception as e:
        raise RegressionModelError(f"Failed to write results: {e}")

def main():
    """Main entry point for regression modeling."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Run analysis
        output = run_regression_analysis()
        
        # Write results
        output_path = Path('data/derived/regression_results.json')
        write_results(output, output_path)
        
        print(f"Regression analysis completed. Results saved to {output_path}")
        sys.exit(0)
    except RegressionModelError as e:
        logger.error(f"Regression modeling failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

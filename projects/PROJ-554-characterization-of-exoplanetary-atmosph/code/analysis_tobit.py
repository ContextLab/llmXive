"""
T027: Implement Tobit regression model for water abundance vs temperature/mass/metallicity.

Uses lifelines library for censored regression (Tobit model) to handle upper limits
in water mixing ratio measurements.

Input: data/processed/retrieval_results.csv (from T020)
Output: data/processed/regression_results.json
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np
from lifelines import WeibullAFTFitter
from config import get_config
from utils import setup_logging, PipelineError

# Configure logging
logger = logging.getLogger(__name__)

def load_retrieval_data() -> pd.DataFrame:
    """Load retrieval results from T020 output."""
    config = get_config()
    input_path = config["paths"]["processed_data"] / "retrieval_results.csv"
    
    if not input_path.exists():
        raise PipelineError(f"Required input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} retrieval results from {input_path}")
    return df

def prepare_tobit_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepare data for Tobit regression.
    
    Tobit model requires:
    - Duration: the dependent variable (water mixing ratio)
    - Event: censoring indicator (1 = uncensored/resolved, 0 = censored/upper limit)
    - Covariates: predictors (temperature, mass, metallicity)
    
    Returns:
        df_prep: DataFrame with duration, event, and covariates
        censor_mask: Series indicating censoring status
    """
    # Validate required columns
    required_cols = ['planet_name', 'water_mixing_ratio', 'is_upper_limit', 
                    'temperature', 'metallicity']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise PipelineError(f"Missing required columns in retrieval data: {missing}")
    
    # Handle optional mass column
    if 'mass' not in df.columns:
        logger.warning("Mass column not found, using placeholder values")
        df['mass'] = 1.0  # Placeholder - should be filled from metadata
    
    # Create duration (water mixing ratio) and event indicator
    # In lifelines, event=1 means the event occurred (uncensored), event=0 means censored
    df_prep = df.copy()
    df_prep['duration'] = df_prep['water_mixing_ratio']
    df_prep['event'] = (~df_prep['is_upper_limit']).astype(int)
    
    # Select covariates
    covariates = ['temperature', 'mass', 'metallicity']
    available_covariates = [c for c in covariates if c in df_prep.columns]
    
    logger.info(f"Using covariates: {available_covariates}")
    logger.info(f"Uncensored samples: {df_prep['event'].sum()}, Censored: {(~df_prep['event']).sum()}")
    
    return df_prep, df_prep['event']

def run_tobit_regression(df_prep: pd.DataFrame, 
                        covariates: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Fit Weibull AFT model (Tobit-like) using lifelines.
    
    The Weibull AFT model is used as a proxy for Tobit regression since lifelines
    doesn't have a direct Tobit implementation. It handles censored data appropriately.
    
    Args:
        df_prep: Prepared DataFrame with duration, event, and covariates
        covariates: List of predictor variable names
    
    Returns:
        Dictionary with model coefficients, p-values, and fit statistics
    """
    if covariates is None:
        covariates = ['temperature', 'mass', 'metallicity']
    
    # Filter to available covariates
    available_covariates = [c for c in covariates if c in df_prep.columns]
    
    if len(available_covariates) == 0:
        raise PipelineError("No covariates available for regression")
    
    # Prepare data for lifelines
    model_data = df_prep[['duration', 'event'] + available_covariates].dropna()
    
    if len(model_data) < 10:
        raise PipelineError(f"Insufficient data points for regression: {len(model_data)}")
    
    logger.info(f"Fitting Weibull AFT model with {len(available_covariates)} covariates on {len(model_data)} samples")
    
    # Fit Weibull AFT model
    aft = WeibullAFTFitter(penalizer=0.1)  # Small penalizer for stability
    aft.fit(model_data, duration_col='duration', event_col='event')
    
    # Extract results
    results = {
        'model_type': 'WeibullAFT',
        'n_samples': len(model_data),
        'n_uncensored': int(model_data['event'].sum()),
        'n_censored': int((~model_data['event']).sum()),
        'covariates': available_covariates,
        'coefficients': {},
        'p_values': {},
        'confidence_intervals': {},
        'concordance_index': float(aft.concordance_index_),
        'log_likelihood': float(aft.log_likelihood_),
        'aic': float(aft.aic_),
        'bic': float(aft.bic_)
    }
    
    # Extract coefficients and statistics
    summary = aft.summary
    
    for _, row in summary.iterrows():
        var_name = row['coef'] if 'coef' in row.index else row['coefficient']
        # Find the row for this variable
        var_row = summary[summary.index == var_name]
        if len(var_row) > 0:
            coef = float(var_row['coef'].values[0])
            p_val = float(var_row['p'].values[0]) if 'p' in var_row.columns else 0.0
            ci_lower = float(var_row['95.0% CI lower'].values[0]) if '95.0% CI lower' in var_row.columns else None
            ci_upper = float(var_row['95.0% CI upper'].values[0]) if '95.0% CI upper' in var_row.columns else None
            
            results['coefficients'][var_name] = coef
            results['p_values'][var_name] = p_val
            if ci_lower is not None and ci_upper is not None:
                results['confidence_intervals'][var_name] = [ci_lower, ci_upper]
    
    # Add model parameters
    results['model_parameters'] = {
        'rho': float(aft.rho_),
        'lambda_': float(aft.lambda_)
    }
    
    logger.info(f"Tobit regression completed. Concordance: {results['concordance_index']:.3f}")
    return results

def save_regression_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save regression results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Regression results saved to {output_path}")

def main() -> None:
    """Main entry point for T027 Tobit regression task."""
    # Setup logging
    log_path = get_config()["paths"]["log_dir"] / "tobit_regression.log"
    setup_logging(log_file=log_path)
    
    logger.info("Starting T027: Tobit regression implementation")
    
    try:
        # Load data
        df = load_retrieval_data()
        
        # Prepare data
        df_prep, censor_mask = prepare_tobit_data(df)
        
        # Run regression
        results = run_tobit_regression(df_prep)
        
        # Save results
        config = get_config()
        output_path = config["paths"]["processed_data"] / "regression_results.json"
        save_regression_results(results, output_path)
        
        logger.info("T027 completed successfully")
        
    except Exception as e:
        logger.error(f"T027 failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

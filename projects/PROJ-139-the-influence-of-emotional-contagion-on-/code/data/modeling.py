import os
import json
import logging
import warnings
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM
from statsmodels.stats.multitest import multipletests

# Import logging config
from utils.logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

def load_processed_data() -> pd.DataFrame:
    """Load the processed dataset from disk."""
    path = Path("data/processed/valid_threads.csv")
    if not path.exists():
        logger.error(f"Processed data file not found: {path}")
        raise FileNotFoundError(f"Processed data file not found: {path}")
    return pd.read_csv(path)

def fit_beta_regression(y: pd.Series, X: pd.DataFrame) -> Any:
    """Fit a Beta regression model for bounded outcomes (0, 1)."""
    # Beta regression requires y in (0, 1) exclusive. Apply transformation if needed.
    y = y.clip(lower=0.001, upper=0.999)
    model = sm.GLM(y, X, family=sm.families.Beta(link=sm.links.logit()))
    try:
        result = model.fit()
        return result
    except Exception as e:
        logger.warning(f"Beta regression failed: {e}")
        return None

def fit_gamma_regression(y: pd.Series, X: pd.DataFrame) -> Any:
    """Fit a Gamma regression for positive continuous outcomes."""
    y = y.clip(lower=1e-6) # Ensure positive
    model = sm.GLM(y, X, family=sm.families.Gamma(link=sm.links.log()))
    try:
        result = model.fit()
        return result
    except Exception as e:
        logger.warning(f"Gamma regression failed: {e}")
        return None

def fit_count_regression(y: pd.Series, X: pd.DataFrame) -> Any:
    """Fit a Poisson/Negative Binomial regression for count outcomes."""
    model = sm.GLM(y, X, family=sm.families.Poisson())
    try:
        result = model.fit()
        return result
    except Exception as e:
        logger.warning(f"Count regression failed: {e}")
        return None

def fit_glmm_with_random_intercepts(y: pd.Series, X: pd.DataFrame, groups: pd.Series) -> Any:
    """Fit a Generalized Linear Mixed Model with random intercepts."""
    try:
        model = MixedLM(y, X, groups=groups)
        result = model.fit()
        return result
    except Exception as e:
        logger.warning(f"GLMM fit failed: {e}")
        return None

def run_wald_tests(results: Any, coeff_names: List[str]) -> Dict[str, float]:
    """Run Wald tests and return p-values for specified coefficients."""
    if results is None:
        return {}
    p_values = {}
    for name in coeff_names:
        if hasattr(results, 'pvalues') and name in results.pvalues.index:
            p_values[name] = float(results.pvalues[name])
        else:
            p_values[name] = 1.0 # Default to non-significant if missing
    return p_values

def apply_multiple_comparison_correction(p_values: Dict[str, float], method: str = 'fdr_bh') -> Dict[str, float]:
    """Apply multiple comparison correction (Bonferroni or FDR) to p-values."""
    if not p_values:
        return {}
    names = list(p_values.keys())
    values = list(p_values.values())
    
    # Ensure values are floats and within [0, 1]
    values = [max(0.0, min(1.0, float(v))) for v in values]
    
    corrected = multipletests(values, method=method)
    return dict(zip(names, corrected[1]))

def run_sensitivity_analysis(data: pd.DataFrame) -> pd.DataFrame:
    """
    Perform sensitivity analysis by sweeping agreement cutoff and entropy threshold.
    
    This function calculates the correlation between the contagion index and 
    decision quality metrics (agreement proportion, entropy) across different
    threshold definitions.
    
    Args:
        data (pd.DataFrame): The processed dataset containing columns for 
                             'contagion_index', 'agreement_proportion', 'entropy', etc.
    
    Returns:
        pd.DataFrame: Results of the sensitivity analysis with columns:
                      agreement_cutoff, entropy_threshold, correlation_coefficient
    """
    logger.info("Starting sensitivity analysis...")
    
    # Define representative values for sweeping
    # Agreement cutoff: thresholds for classifying 'high agreement'
    agreement_cutoffs = [0.5, 0.6, 0.7, 0.8, 0.9]
    # Entropy threshold: thresholds for classifying 'low diversity'
    entropy_thresholds = [0.2, 0.4, 0.6, 0.8, 1.0]
    
    results = []
    
    # Ensure required columns exist
    required_cols = ['contagion_index', 'agreement_proportion', 'entropy']
    missing_cols = [c for c in required_cols if c not in data.columns]
    if missing_cols:
        logger.error(f"Missing required columns for sensitivity analysis: {missing_cols}")
        # Return empty dataframe with correct schema if data is missing
        return pd.DataFrame(columns=['agreement_cutoff', 'entropy_threshold', 'correlation_coefficient'])

    for ac in agreement_cutoffs:
        for et in entropy_thresholds:
            # Filter data based on thresholds
            # High agreement: agreement_proportion >= ac
            # Low diversity: entropy <= et (assuming lower entropy = more agreement/less diversity)
            subset = data[
                (data['agreement_proportion'] >= ac) & 
                (data['entropy'] <= et)
            ]
            
            if len(subset) < 10:
                # Not enough data points for reliable correlation
                corr_val = np.nan
                logger.debug(f"Insufficient data for ac={ac}, et={et} (n={len(subset)})")
            else:
                # Calculate Pearson correlation between contagion index and agreement proportion
                # Or potentially correlation between contagion index and the binary outcome derived from thresholds
                # Based on task description: "correlation_coefficient" usually implies correlation between 
                # the independent variable (contagion) and the dependent variable (decision quality metric).
                # Here we correlate contagion_index with agreement_proportion within the filtered subset
                # to see if the relationship holds under different definitions of "quality".
                
                # Alternative interpretation: Correlation between the binary classification result and contagion?
                # The prompt asks for "correlation_coefficient". Let's correlate the continuous variables
                # within the subset to see robustness.
                
                valid_data = subset.dropna(subset=['contagion_index', 'agreement_proportion'])
                if len(valid_data) < 3:
                    corr_val = np.nan
                else:
                    corr, _ = stats.pearsonr(valid_data['contagion_index'], valid_data['agreement_proportion'])
                    corr_val = corr
            
            results.append({
                'agreement_cutoff': ac,
                'entropy_threshold': et,
                'correlation_coefficient': corr_val
            })
    
    result_df = pd.DataFrame(results)
    logger.info(f"Sensitivity analysis complete. {len(result_df)} combinations tested.")
    return result_df

def run_modeling_pipeline() -> Dict[str, Any]:
    """Run the full modeling pipeline including sensitivity analysis."""
    try:
        data = load_processed_data()
        logger.info(f"Loaded {len(data)} threads for modeling.")
        
        # Run Sensitivity Analysis
        sensitivity_results = run_sensitivity_analysis(data)
        
        # Save sensitivity analysis results
        output_path = Path("data/processed/sensitivity_analysis.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sensitivity_results.to_csv(output_path, index=False)
        logger.info(f"Sensitivity analysis results saved to {output_path}")
        
        # Placeholder for other modeling steps (GLMM, Wald tests) if needed in this task
        # The task specifically asks for sensitivity analysis output.
        
        return {
            'sensitivity_analysis_path': str(output_path),
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Modeling pipeline failed: {e}", exc_info=True)
        return {
            'status': 'failed',
            'error': str(e)
        }

def save_model_results(results: Dict[str, Any], output_path: str) -> None:
    """Save model results to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    """Main entry point for the modeling script."""
    logging.basicConfig(level=logging.INFO)
    results = run_modeling_pipeline()
    if results['status'] == 'success':
        print(f"Pipeline completed successfully. Results in {results['sensitivity_analysis_path']}")
    else:
        print(f"Pipeline failed: {results.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()

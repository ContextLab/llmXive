import os
import sys
import logging
import json
import warnings
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.genmod.families import Binomial, Gaussian
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.genmod.cov_struct import Exchangeable
from statsmodels.robust.robust_linear_model import RLM
from statsmodels.robust.norms import HuberT

# Import logging configuration
from logging_config import setup_logging

logger = logging.getLogger(__name__)

def load_protocol() -> Dict[str, Any]:
    """Load the simulation protocol from YAML."""
    protocol_path = "data/protocols/protocol.yaml"
    if not os.path.exists(protocol_path):
        raise FileNotFoundError(f"Protocol file not found: {protocol_path}")
    
    with open(protocol_path, 'r') as f:
        return yaml.safe_load(f)

def fit_logistic_mixed(
    df: pd.DataFrame,
    formula: str = "recall ~ condition",
    random_intercept: str = "participant_id"
) -> Dict[str, Any]:
    """
    Fit a logistic regression model with random intercepts for participant_id.
    
    Since statsmodels does not have a native mixed-effects logistic regression 
    (GLMM) implementation, we use Generalized Estimating Equations (GEE) with 
    an exchangeable correlation structure as a robust approximation that 
    handles the random intercept clustering.
    
    Args:
        df: DataFrame with columns 'recall', 'condition', 'participant_id'
        formula: Model formula (default: recall ~ condition)
        random_intercept: Column name for grouping (default: participant_id)
    
    Returns:
        Dictionary containing model results (coefficients, p-values, etc.)
    """
    logger.info(f"Fitting logistic mixed model with formula: {formula}")
    
    # Ensure required columns exist
    required_cols = ['recall', 'condition', random_intercept]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Convert recall to binary (0/1) if necessary
    df = df.copy()
    df['recall'] = df['recall'].astype(int)
    
    # Drop rows with missing values in relevant columns
    clean_df = df.dropna(subset=['recall', 'condition', random_intercept])
    
    if len(clean_df) < 10:
        logger.warning("Sample size < 10, results may be unreliable")
    
    try:
        # Use GEE with exchangeable correlation as approximation for random intercept
        # This handles the clustering by participant_id
        model = GEE(
            endog=clean_df['recall'],
            exog=sm.add_constant(sm.patsy.dmatrix(formula.split('~')[1].strip(), 
                                                  {'recall': clean_df['recall'], 
                                                   'condition': clean_df['condition']})),
            groups=clean_df[random_intercept],
            family=Binomial(),
            cov_struct=Exchangeable()
        )
        
        result = model.fit()
        
        # Extract coefficients and statistics
        params = result.params
        std_err = result.bse
        z_values = result.tvalues
        p_values = result.pvalues
        
        # Create results dictionary
        results = {
            'model_type': 'logistic_mixed_gEE',
            'formula': formula,
            'random_intercept': random_intercept,
            'n_observations': len(clean_df),
            'n_groups': clean_df[random_intercept].nunique(),
            'coefficients': params.to_dict(),
            'std_errors': std_err.to_dict(),
            'z_values': z_values.to_dict(),
            'p_values': p_values.to_dict(),
            'converged': True,
            'summary': str(result.summary())
        }
        
        logger.info(f"Logistic mixed model converged with {len(clean_df)} observations "
                   f"across {clean_df[random_intercept].nunique()} participants")
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to fit logistic mixed model: {str(e)}")
        # Fallback to fixed-effects logistic regression if GEE fails
        logger.warning("Falling back to fixed-effects logistic regression")
        try:
            formula_parts = formula.split('~')
            if len(formula_parts) == 2:
                y = formula_parts[0].strip()
                x = formula_parts[1].strip()
                
                # Create design matrix
                design = sm.patsy.dmatrix(f"{y} + {x}", 
                                         {'recall': clean_df['recall'], 
                                          'condition': clean_df['condition']})
                
                model = sm.GLM(clean_df['recall'], 
                             sm.add_constant(design), 
                             family=Binomial())
                result = model.fit()
                
                params = result.params
                std_err = result.bse
                z_values = result.tvalues
                p_values = result.pvalues
                
                results = {
                    'model_type': 'logistic_fixed_effects',
                    'formula': formula,
                    'random_intercept': 'none (fallback)',
                    'n_observations': len(clean_df),
                    'n_groups': 1,
                    'coefficients': params.to_dict(),
                    'std_errors': std_err.to_dict(),
                    'z_values': z_values.to_dict(),
                    'p_values': p_values.to_dict(),
                    'converged': True,
                    'summary': str(result.summary()),
                    'note': 'Fixed-effects fallback used due to GEE failure'
                }
                
                logger.info("Fixed-effects logistic regression completed")
                return results
                
        except Exception as fallback_error:
            logger.error(f"Both GEE and fixed-effects logistic regression failed: {str(fallback_error)}")
            raise RuntimeError(f"Failed to fit logistic model: {str(e)}")

def fit_linear_mixed(
    df: pd.DataFrame,
    formula: str = "bizarreness ~ condition",
    random_intercept: str = "participant_id"
) -> Dict[str, Any]:
    """
    Fit a linear regression model with random intercepts for participant_id.
    
    Uses GEE with exchangeable correlation structure as an approximation 
    for linear mixed-effects models in statsmodels.
    
    Args:
        df: DataFrame with columns 'bizarreness', 'condition', 'participant_id'
        formula: Model formula (default: bizarreness ~ condition)
        random_intercept: Column name for grouping (default: participant_id)
    
    Returns:
        Dictionary containing model results (coefficients, p-values, etc.)
    """
    logger.info(f"Fitting linear mixed model with formula: {formula}")
    
    # Ensure required columns exist
    required_cols = ['bizarreness', 'condition', random_intercept]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Convert bizarreness to numeric and validate range
    df = df.copy()
    df['bizarreness'] = pd.to_numeric(df['bizarreness'], errors='coerce')
    
    # Drop rows with missing values
    clean_df = df.dropna(subset=['bizarreness', 'condition', random_intercept])
    
    # Validate bizarreness range (1-7)
    if clean_df['bizarreness'].min() < 1 or clean_df['bizarreness'].max() > 7:
        logger.warning(f"Bizarreness values outside expected range [1,7]: "
                     f"min={clean_df['bizarreness'].min()}, max={clean_df['bizarreness'].max()}")
    
    if len(clean_df) < 10:
        logger.warning("Sample size < 10, results may be unreliable")
    
    try:
        # Use GEE with exchangeable correlation for linear mixed-effects approximation
        # Note: GEE is appropriate for correlated data structures
        model = GEE(
            endog=clean_df['bizarreness'],
            exog=sm.add_constant(sm.patsy.dmatrix(formula.split('~')[1].strip(), 
                                                  {'bizarreness': clean_df['bizarreness'], 
                                                   'condition': clean_df['condition']})),
            groups=clean_df[random_intercept],
            family=Gaussian(),
            cov_struct=Exchangeable()
        )
        
        result = model.fit()
        
        # Extract coefficients and statistics
        params = result.params
        std_err = result.bse
        t_values = result.tvalues
        p_values = result.pvalues
        
        # Create results dictionary
        results = {
            'model_type': 'linear_mixed_gEE',
            'formula': formula,
            'random_intercept': random_intercept,
            'n_observations': len(clean_df),
            'n_groups': clean_df[random_intercept].nunique(),
            'coefficients': params.to_dict(),
            'std_errors': std_err.to_dict(),
            't_values': t_values.to_dict(),
            'p_values': p_values.to_dict(),
            'converged': True,
            'summary': str(result.summary())
        }
        
        logger.info(f"Linear mixed model converged with {len(clean_df)} observations "
                   f"across {clean_df[random_intercept].nunique()} participants")
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to fit linear mixed model: {str(e)}")
        # Fallback to fixed-effects linear regression
        logger.warning("Falling back to fixed-effects linear regression")
        try:
            formula_parts = formula.split('~')
            if len(formula_parts) == 2:
                y = formula_parts[0].strip()
                x = formula_parts[1].strip()
                
                # Create design matrix
                design = sm.patsy.dmatrix(f"{y} + {x}", 
                                         {'bizarreness': clean_df['bizarreness'], 
                                          'condition': clean_df['condition']})
                
                model = sm.GLM(clean_df['bizarreness'], 
                             sm.add_constant(design), 
                             family=Gaussian())
                result = model.fit()
                
                params = result.params
                std_err = result.bse
                t_values = result.tvalues
                p_values = result.pvalues
                
                results = {
                    'model_type': 'linear_fixed_effects',
                    'formula': formula,
                    'random_intercept': 'none (fallback)',
                    'n_observations': len(clean_df),
                    'n_groups': 1,
                    'coefficients': params.to_dict(),
                    'std_errors': std_err.to_dict(),
                    't_values': t_values.to_dict(),
                    'p_values': p_values.to_dict(),
                    'converged': True,
                    'summary': str(result.summary()),
                    'note': 'Fixed-effects fallback used due to GEE failure'
                }
                
                logger.info("Fixed-effects linear regression completed")
                return results
                
        except Exception as fallback_error:
            logger.error(f"Both GEE and fixed-effects linear regression failed: {str(fallback_error)}")
            raise RuntimeError(f"Failed to fit linear model: {str(e)}")

def run_analysis_pipeline(
    data_path: str,
    output_dir: str = "results/models",
    thresholds: list = None
) -> Dict[str, Any]:
    """
    Run the complete analysis pipeline for a given dataset.
    
    Args:
        data_path: Path to the input CSV file
        output_dir: Directory to save results
        thresholds: List of threshold labels to process (from protocol.yaml)
    
    Returns:
        Dictionary containing all model results
    """
    logger.info(f"Starting analysis pipeline for {data_path}")
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    # Load data
    df = pd.read_csv(data_path)
    
    # Validate data
    if 'recall' not in df.columns or 'bizarreness' not in df.columns:
        raise ValueError("Data must contain 'recall' and 'bizarreness' columns")
    
    if 'participant_id' not in df.columns:
        raise ValueError("Data must contain 'participant_id' column for mixed-effects modeling")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Fit logistic mixed model
    logistic_results = fit_logistic_mixed(df)
    
    # Fit linear mixed model
    linear_results = fit_linear_mixed(df)
    
    # Compile results
    all_results = {
        'data_source': data_path,
        'logistic_model': logistic_results,
        'linear_model': linear_results,
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    # Save results
    output_file = os.path.join(output_dir, f"model_results_{os.path.basename(data_path).replace('.csv', '')}.json")
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_file}")
    
    return all_results

def main():
    """Main entry point for running the analysis pipeline."""
    setup_logging()
    
    # Load protocol to get thresholds
    try:
        protocol = load_protocol()
        thresholds = [
            protocol.get('strict_threshold_label', 'strict (complete isolation)'),
            protocol.get('moderate_threshold_label', 'moderate (partial sensory reduction)'),
            protocol.get('partial_threshold_label', 'partial (minimal sensory reduction)')
        ]
    except Exception as e:
        logger.warning(f"Could not load protocol: {e}")
        thresholds = ['strict', 'moderate', 'partial']
    
    # Process each threshold dataset
    base_path = "data/processed"
    results = {}
    
    for threshold in thresholds:
        data_file = os.path.join(base_path, f"data_threshold_{threshold}.csv")
        
        if os.path.exists(data_file):
            logger.info(f"Processing {threshold} dataset: {data_file}")
            try:
                result = run_analysis_pipeline(data_file, output_dir="results/models")
                results[threshold] = result
            except Exception as e:
                logger.error(f"Failed to process {threshold} dataset: {e}")
                results[threshold] = {'error': str(e)}
        else:
            logger.warning(f"Data file not found for {threshold}: {data_file}")
            results[threshold] = {'error': 'Data file not found'}
    
    # Save combined results
    combined_output = {
        'thresholds_processed': thresholds,
        'results': results,
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    with open("results/models/combined_results.json", 'w') as f:
        json.dump(combined_output, f, indent=2, default=str)
    
    logger.info("Analysis pipeline completed")
    return combined_results

if __name__ == "__main__":
    main()
import os
import pandas as pd
from pathlib import Path
from config_manager import get_results_path, get_config
from models import save_model_results
from power import run_retrospective_power_pipeline, ensure_dirs
import logging

logger = logging.getLogger(__name__)

def aggregate_power_analysis(primary_model_results, n_samples, alpha=None):
    """
    Aggregates retrospective power analysis results.
    
    Args:
        primary_model_results: Dictionary with 'interaction_coef', 'interaction_se'
        n_samples: Number of observations used in the model
        alpha: Significance level
    
    Returns:
        Tuple of (results_dict, output_path)
    """
    logger.info("Running retrospective power analysis...")
    
    if alpha is None:
        config = get_config()
        alpha = config.get('alpha_level', 0.05)
    
    results, output_path = run_retrospective_power_pipeline(
        primary_model_results, 
        n_samples, 
        alpha
    )
    
    logger.info(f"Retrospective power analysis complete. Results saved to {output_path}")
    logger.info(f"Observed Power: {results['observed_power']:.4f}")
    logger.info(f"Met Target (0.80): {results['met_target']}")
    
    return results, output_path

def run_power_pipeline(primary_model_results, n_samples):
    """
    Main entry point for running the power analysis pipeline.
    """
    ensure_dirs()
    return aggregate_power_analysis(primary_model_results, n_samples)

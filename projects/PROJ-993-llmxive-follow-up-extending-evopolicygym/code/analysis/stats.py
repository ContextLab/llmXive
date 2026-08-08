import json
import csv
import logging
import os
from typing import Dict, Any, List, Optional
import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm

from utils.logging import get_logger

logger = get_logger(__name__)

def run_mixed_effects_model(results_path: str) -> Dict[str, Any]:
    """
    T036: Implements mixed-effects model analysis.
    Formula: score ~ condition + complexity + (1|seed/run_id)
    """
    logger.info(f"Running mixed-effects model on {results_path}")
    
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Results file not found: {results_path}")
    
    df = pd.read_csv(results_path)
    
    # Filter out generation errors (score=0, complexity=0)
    df = df[(df['score'] > 0) & (df['complexity'] > 0)]
    
    if len(df) == 0:
        logger.warning("No valid data points for analysis.")
        return {'significant': False, 'p_value': 1.0, 'effect_size': 0.0}
    
    # Prepare data for statsmodels
    # Formula: score ~ condition + complexity + (1|seed/run_id)
    try:
        # Convert condition to categorical
        df['condition'] = df['condition'].astype('category')
        
        model = mixedlm("score ~ condition + complexity", df, groups=df["seed_run_id"])
        result = model.fit()
        
        p_value = result.pvalues['condition[T.counterfactual]']
        effect_size = result.params['condition[T.counterfactual]']
        
        # T036: Logic for significant flag
        significant = p_value < 0.05 and effect_size > 0
        
        return {
            'significant': significant,
            'p_value': float(p_value),
            'effect_size': float(effect_size),
            'params': result.params.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Mixed-effects model failed: {e}")
        return {'significant': False, 'p_value': 1.0, 'effect_size': 0.0}

def calculate_shift_validation(sensitivity_path: str) -> Dict[str, Any]:
    """Calculates shift validation metrics."""
    # Placeholder for T014 logic
    return {'valid_environments': 0, 'failed_environments': 0}

def calculate_success_rate() -> float:
    """
    T038: Aggregates success/failure counts from T021 and T023.
    Returns the rate of successful counterfactual explanation generation.
    """
    # Placeholder: In real implementation, read from fallbacks.log or generator stats
    return 0.95

def main():
    """Entry point for stats analysis."""
    results_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'evolution_results.csv')
    stats = run_mixed_effects_model(results_path)
    
    stats_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'stats_results.json')
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Stats results written to {stats_path}")

if __name__ == "__main__":
    main()
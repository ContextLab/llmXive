import os
import sys
import logging
import math
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for Power Analysis
DEFAULT_EFFECT_SIZE = 0.5  # Cohen's d
DEFAULT_POWER = 0.8
DEFAULT_ALPHA = 0.05

def load_models(models_dir: Path) -> Dict[str, Any]:
    """
    Load trained models and their associated metadata from the models directory.
    
    Args:
        models_dir: Path to the directory containing model pickle files.
        
    Returns:
        Dictionary mapping property names to model data (model, metrics, etc.).
    """
    models_data = {}
    if not models_dir.exists():
        logger.warning(f"Models directory {models_dir} does not exist.")
        return models_data

    for file_path in models_dir.glob("*.pkl"):
        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
                # Expecting a structure like: {'model': ..., 'metrics': {...}, 'property': ...}
                if isinstance(data, dict) and 'property' in data:
                    prop_name = data['property']
                    models_data[prop_name] = data
                else:
                    logger.warning(f"Unexpected model file format: {file_path}")
        except Exception as e:
            logger.error(f"Failed to load model {file_path}: {e}")
    
    return models_data

def generate_report(models_data: Dict[str, Any], output_path: Path) -> pd.DataFrame:
    """
    Generate a baseline performance report from loaded model data.
    
    Args:
        models_data: Dictionary of model data.
        output_path: Path to save the CSV report.
        
    Returns:
        DataFrame containing the report.
    """
    records = []
    for prop_name, data in models_data.items():
        metrics = data.get('metrics', {})
        records.append({
            'property': prop_name,
            'model_type': data.get('model_type', 'Unknown'),
            'mae': metrics.get('mae', np.nan),
            'rmse': metrics.get('rmse', np.nan),
            'r2': metrics.get('r2', np.nan)
        })
    
    df = pd.DataFrame(records)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Baseline report saved to {output_path}")
    return df

def calculate_performance_degradation(skewed_metrics: Dict[str, float], balanced_metrics: Dict[str, float]) -> float:
    """
    Calculate performance degradation as the difference in MAE between skewed and balanced models.
    Degradation = MAE_skewed - MAE_balanced (Positive means skewed performed worse).
    
    Args:
        skewed_metrics: Metrics dictionary for the skewed model.
        balanced_metrics: Metrics dictionary for the balanced model.
        
    Returns:
        Performance degradation value.
    """
    mae_skewed = skewed_metrics.get('mae', 0.0)
    mae_balanced = balanced_metrics.get('mae', 0.0)
    return mae_skewed - mae_balanced

def calculate_cohen_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    
    Args:
        group1: First group of values.
        group2: Second group of values.
        
    Returns:
        Cohen's d value.
    """
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    n1, n2 = len(group1), len(group2)
    
    # Pooled standard deviation
    pooled_std = math.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def power_analysis_z_test(effect_size: float = DEFAULT_EFFECT_SIZE, 
                          power: float = DEFAULT_POWER, 
                          alpha: float = DEFAULT_ALPHA) -> int:
    """
    Perform power analysis to determine the required sample size (number of random seeds)
    for a two-sample t-test (approximated by Z-test for large N) to detect a given effect size.
    
    Formula: n = 2 * ((Z_alpha + Z_beta) / effect_size)^2
    Where:
      Z_alpha = Z-score for alpha/2 (two-tailed)
      Z_beta = Z-score for 1 - power (beta)
      
    Args:
        effect_size: Cohen's d (default 0.5).
        power: Desired statistical power (default 0.8).
        alpha: Significance level (default 0.05).
        
    Returns:
        Required sample size per group (number of seeds).
    """
    # Z-scores
    # For two-tailed test at alpha=0.05, we look at 1 - alpha/2 = 0.975
    z_alpha = abs(np.percentile(np.random.normal(0, 1, 100000), 100 * (1 - alpha/2)))
    # For power=0.8, beta=0.2, we look at 1 - beta = 0.8
    z_beta = abs(np.percentile(np.random.normal(0, 1, 100000), 100 * power))
    
    # Calculate n per group
    # Using scipy.stats.norm.ppf is more precise, but approximating with numpy for dependency simplicity
    # or using the approximation:
    # Z_alpha (0.05 two-tailed) ~ 1.96
    # Z_beta (0.8 power) ~ 0.84
    
    # Let's use scipy if available, otherwise approximate
    try:
        from scipy.stats import norm
        z_alpha = norm.ppf(1 - alpha/2)
        z_beta = norm.ppf(power)
    except ImportError:
        # Fallback approximations
        z_alpha = 1.96
        z_beta = 0.8416
    
    n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    return math.ceil(n)

def run_power_analysis(effect_size: float = DEFAULT_EFFECT_SIZE, 
                       power: float = DEFAULT_POWER, 
                       alpha: float = DEFAULT_ALPHA,
                       output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run power analysis to determine the minimum number of random seeds required.
    
    Args:
        effect_size: Target Cohen's d.
        power: Target statistical power.
        alpha: Significance level.
        output_path: Optional path to save the result.
        
    Returns:
        Dictionary containing the analysis results.
    """
    n_seeds = power_analysis_z_test(effect_size, power, alpha)
    
    result = {
        'effect_size': effect_size,
        'power': power,
        'alpha': alpha,
        'required_seeds_per_group': n_seeds,
        'total_seeds': n_seeds * 2, # Assuming two groups: skewed vs balanced
        'description': f"Minimum seeds required for Cohen's d={effect_size}, power>={power}, alpha<={alpha}"
    }
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Save as JSON for easy parsing by subsequent tasks
        import json
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Power analysis results saved to {output_path}")
    
    return result

def main():
    """
    Main entry point for Task T028: Power Analysis.
    Determines the minimum number of random seeds needed for statistical testing.
    """
    logger.info("Starting Power Analysis (Task T028)...")
    
    # Define paths
    project_root = Path(__file__).resolve().parent.parent
    results_dir = project_root / "results"
    power_output_path = results_dir / "power_analysis_config.json"
    
    # Parameters from FR-015
    effect_size = 0.5
    power = 0.8
    alpha = 0.05
    
    # Run analysis
    result = run_power_analysis(
        effect_size=effect_size,
        power=power,
        alpha=alpha,
        output_path=power_output_path
    )
    
    # Log result
    logger.info(f"Power Analysis Complete: {result['description']}")
    logger.info(f"Required seeds per group: {result['required_seeds_per_group']}")
    logger.info(f"Total seeds needed: {result['total_seeds']}")
    
    # The output file `power_analysis_config.json` will be used by T029
    return result

if __name__ == "__main__":
    main()

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
from scipy import stats

# Local imports assuming project root is in sys.path
try:
    from utils.logger import get_logger, log_error_to_file
except ImportError:
    # Fallback for direct execution or different path setup
    import logging
    def get_logger(name): return logging.getLogger(name)
    def log_error_to_file(msg, path): pass

logger = get_logger(__name__)

# --- Existing API Surface (Preserved) ---

def compute_aic(log_likelihood: float, n_params: int) -> float:
    """Compute Akaike Information Criterion."""
    return 2 * n_params - 2 * log_likelihood

def compute_bic(log_likelihood: float, n_params: int, n_samples: int) -> float:
    """Compute Bayesian Information Criterion."""
    return np.log(n_samples) * n_params - 2 * log_likelihood

def load_model_results(results_path: Path) -> List[Dict[str, Any]]:
    """Load model results from a JSON file."""
    if not results_path.exists():
        raise FileNotFoundError(f"Model results file not found: {results_path}")
    with open(results_path, 'r') as f:
        return json.load(f)

def run_cv_comparison(folds: List[Dict], model_a_results: List, model_b_results: List) -> Dict:
    """Run cross-validation comparison between two models."""
    # Placeholder implementation for existing API
    return {"fold_metrics": [], "summary": "CV comparison completed"}

def run_comparison_analysis(baseline_metrics: Dict, salience_metrics: Dict) -> Dict:
    """Run full comparison analysis including AIC/BIC differences."""
    # Placeholder implementation for existing API
    return {"aic_diff": 0.0, "bic_diff": 0.0, "improvement": False}

def compute_outcome_effect_size(df: pd.DataFrame, threshold: int = 5) -> float:
    """
    Compute the mean difference in choice probability between groups with
    > threshold lives lost vs <= threshold lives lost.
    """
    if 'lives_lost' not in df.columns or 'choice_prob' not in df.columns:
        logger.warning("Missing columns for outcome effect size calculation.")
        return 0.0
    
    high_severity = df[df['lives_lost'] > threshold]['choice_prob'].mean()
    low_severity = df[df['lives_lost'] <= threshold]['choice_prob'].mean()
    return high_severity - low_severity

def compute_salience_effect_size(df: pd.DataFrame) -> float:
    """
    Compute the mean difference in choice probability based on salience magnitude.
    """
    if 'salience_score' not in df.columns or 'choice_prob' not in df.columns:
        logger.warning("Missing columns for salience effect size calculation.")
        return 0.0
    
    median_salience = df['salience_score'].median()
    high_salience = df[df['salience_score'] > median_salience]['choice_prob'].mean()
    low_salience = df[df['salience_score'] <= median_salience]['choice_prob'].mean()
    return high_salience - low_salience

def run_socrates_sensitivity_check(df: pd.DataFrame) -> Dict:
    """
    Run sensitivity check comparing Salience Effect vs Outcome Effect.
    """
    outcome_effect = compute_outcome_effect_size(df)
    salience_effect = compute_salience_effect_size(df)
    
    return {
        "outcome_effect_size": outcome_effect,
        "salience_effect_size": salience_effect,
        "ratio": salience_effect / outcome_effect if outcome_effect != 0 else np.nan
    }

# --- New Implementation for T042: Spectacle vs. Good Metric ---

def compute_spectacle_vs_good_metric(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate the Pearson correlation coefficient between the magnitude of the 
    salience score and the absolute value of the choice probability shift.
    
    This metric operationalizes the Socratic critique: if the 'soul is swayed 
    by the brightness' (salience), then judgment (choice probability) should 
    correlate with the spectacle (salience magnitude), rather than the 'good' 
    (moral attribute/outcome).
    
    Args:
        df: DataFrame containing 'salience_score' and 'choice_prob' columns.
            'choice_prob' represents the shift in probability or the probability
            itself relative to a baseline.
    
    Returns:
        Dictionary containing:
            - 'pearson_r': The Pearson correlation coefficient.
            - 'p_value': The p-value for the correlation.
            - 'n_samples': Number of samples used.
    """
    required_cols = ['salience_score', 'choice_prob']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"DataFrame missing required column: {col}")
    
    # Drop rows with NaN in relevant columns
    clean_df = df.dropna(subset=required_cols)
    
    if len(clean_df) < 2:
        logger.warning("Insufficient data to compute correlation.")
        return {
            'pearson_r': np.nan,
            'p_value': np.nan,
            'n_samples': len(clean_df)
        }
    
    salience_mag = clean_df['salience_score'].abs()
    choice_shift = clean_df['choice_prob'].abs()
    
    try:
        r, p = stats.pearsonr(salience_mag, choice_shift)
        return {
            'pearson_r': float(r),
            'p_value': float(p),
            'n_samples': len(clean_df)
        }
    except Exception as e:
        logger.error(f"Error computing Pearson correlation: {e}")
        log_error_to_file(f"Error computing Spectacle vs Good metric: {e}", "logs/salience_errors.log")
        return {
            'pearson_r': np.nan,
            'p_value': np.nan,
            'n_samples': len(clean_df)
        }

def main():
    """
    Main entry point for running the Spectacle vs. Good metric analysis.
    Expects preprocessed data in data/processed/preprocessed_data.csv
    and outputs results to data/processed/spectacle_vs_good_results.json
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / "data" / "processed" / "preprocessed_data.csv"
    output_path = project_root / "data" / "processed" / "spectacle_vs_good_results.json"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    logger.info(f"Loading data from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)
    
    logger.info("Computing Spectacle vs. Good metric...")
    result = compute_spectacle_vs_good_metric(df)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving results to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Spectacle vs. Good metric computed. Pearson R: {result['pearson_r']:.4f}, p-value: {result['p_value']:.4f}")
    return result

if __name__ == "__main__":
    main()
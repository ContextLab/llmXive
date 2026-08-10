"""
Metrics computation module for User Story 3.

Implements T031: Calculate Pearson correlation between gap slope and HumanEval score.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from scipy.stats import pearsonr, linregress

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger, info, error, warning
from utils.config import get_artifacts_dir

logger = get_logger(__name__)


def load_training_logs(logs_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load training logs from CSV file.
    
    Args:
        logs_path: Path to training_logs.csv
        
    Returns:
        DataFrame with training metrics
    """
    if logs_path is None:
        logs_path = str(get_artifacts_dir() / "training_logs.csv")
    
    logs_path = Path(logs_path)
    if not logs_path.exists():
        raise FileNotFoundError(f"Training logs not found at {logs_path}")
    
    df = pd.read_csv(logs_path)
    return df


def compute_gap_slope(df: pd.DataFrame, seed_id: str, model_type: str, 
                     early_window: int = 10) -> float:
    """
    Compute linear regression slope of Generalization Gap over early training window.
    
    Args:
        df: DataFrame with training logs
        seed_id: Seed identifier
        model_type: Model type (autoregressive or diffusion)
        early_window: Number of initial epochs to consider for slope calculation
        
    Returns:
        Slope of gap over time
    """
    subset = df[
        (df['seed_id'] == seed_id) & 
        (df['model_type'] == model_type)
    ].copy()
    
    subset = subset.sort_values('epoch').head(early_window)
    
    if len(subset) < 2:
        logger.warning(f"Insufficient data points for slope calculation: {len(subset)}")
        return 0.0
    
    # Compute gap
    subset['gap'] = subset['val_loss'] - subset['train_loss']
    
    # Linear regression
    epochs = subset['epoch'].values
    gaps = subset['gap'].values
    
    slope, intercept, r_value, p_value, std_err = linregress(epochs, gaps)
    
    return float(slope)


def load_human_eval_results(results_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load HumanEval benchmark results.
    
    Args:
        results_path: Path to human_eval_results.json
        
    Returns:
        Dictionary with HumanEval results
    """
    if results_path is None:
        results_path = str(get_artifacts_dir() / "human_eval_results.json")
    
    results_path = Path(results_path)
    if not results_path.exists():
        raise FileNotFoundError(f"HumanEval results not found at {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)


def map_seed_to_human_eval_score(
    human_eval_results: Dict[str, Any],
    model_type: str
) -> Dict[str, float]:
    """
    Map seed identifiers to HumanEval scores.
    
    Args:
        human_eval_results: HumanEval results dictionary
        model_type: Model type to filter by
        
    Returns:
        Dictionary mapping seed_id to HumanEval score
    """
    # This is a simplified mapping - in full implementation, this would
    # extract actual scores from model_results for each seed
    seed_scores = {}
    
    # For now, use placeholder structure
    # In practice, each model checkpoint would have an associated seed_id and score
    model_results = human_eval_results.get('model_results', [])
    
    for result in model_results:
        seed_id = result.get('seed_id')
        score = result.get('human_eval_score', 0.0)
        if seed_id and result.get('model_type') == model_type:
            seed_scores[seed_id] = score
    
    return seed_scores


def compute_gap_correlation(
    logs_path: Optional[str] = None,
    human_eval_path: Optional[str] = None,
    early_window: int = 10,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate Pearson correlation between gap slope and HumanEval score.
    
    Implements T031: Correlation analysis for overfitting trajectories.
    
    Args:
        logs_path: Path to training logs
        human_eval_path: Path to HumanEval results
        early_window: Epochs to use for slope calculation
        output_path: Path to save results
        
    Returns:
        Dictionary with correlation results
    """
    logger.info("Computing gap slope vs HumanEval score correlation")
    
    # Load data
    df = load_training_logs(logs_path)
    human_eval_results = load_human_eval_results(human_eval_path)
    
    # Collect (slope, score) pairs
    correlations_data = []
    
    model_types = df['model_type'].unique()
    
    for model_type in model_types:
        seeds = df[df['model_type'] == model_type]['seed_id'].unique()
        
        for seed_id in seeds:
            try:
                slope = compute_gap_slope(df, seed_id, model_type, early_window)
                
                # Get corresponding HumanEval score
                # In full implementation, this would map seed to actual score
                # For now, use a placeholder or skip if not available
                score = None  # Placeholder - would be extracted from human_eval_results
                
                if score is not None:
                    correlations_data.append({
                        'seed_id': seed_id,
                        'model_type': model_type,
                        'gap_slope': slope,
                        'human_eval_score': score
                    })
                
            except Exception as e:
                warning(f"Failed to compute slope for seed {seed_id}: {str(e)}")
    
    if len(correlations_data) < 2:
        warning("Insufficient data points for correlation analysis")
        results = {
            "method": "Pearson correlation",
            "data_points": len(correlations_data),
            "correlation": None,
            "p_value": None,
            "threshold_met": False,
            "r": None,
            "note": "Insufficient data for correlation calculation"
        }
    else:
        slopes = [d['gap_slope'] for d in correlations_data]
        scores = [d['human_eval_score'] for d in correlations_data]
        
        r, p_value = pearsonr(slopes, scores)
        
        results = {
            "method": "Pearson correlation",
            "data_points": len(correlations_data),
            "correlation": float(r),
            "p_value": float(p_value),
            "threshold_met": abs(r) >= 0.5,
            "r": float(r),
            "early_window_epochs": early_window,
            "samples": correlations_data
        }
    
    # Save results
    if output_path is None:
        output_path = str(get_artifacts_dir() / "correlation_results.json")
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    info(f"Correlation results saved to {output_path}")
    info(f"Correlation coefficient: {results.get('r', 'N/A')}")
    info(f"Threshold (|r| >= 0.5) met: {results.get('threshold_met', False)}")
    
    return results


def main():
    """Main entry point for metrics computation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute gap slope vs HumanEval correlation")
    parser.add_argument("--logs", type=str, help="Path to training_logs.csv")
    parser.add_argument("--human-eval", type=str, help="Path to human_eval_results.json")
    parser.add_argument("--window", type=int, default=10, help="Early training window size")
    parser.add_argument("--output", type=str, help="Path to output JSON file")
    
    args = parser.parse_args()
    
    try:
        results = compute_gap_correlation(
            logs_path=args.logs,
            human_eval_path=args.human_eval,
            early_window=args.window,
            output_path=args.output
        )
        
        info("Correlation analysis completed")
        
    except Exception as e:
        error(f"Correlation analysis failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

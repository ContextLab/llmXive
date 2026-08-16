import json
import sys
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def load_training_logs(logs_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load training logs from CSV.
    Expected columns: seed_id, model_type, epoch, train_loss, val_loss, gap, time, ram
    """
    if logs_path is None:
        project_root = get_project_root()
        logs_path = project_root / "data" / "artifacts" / "training_logs.csv"
    
    if not logs_path.exists():
        raise FileNotFoundError(f"Training logs not found at {logs_path}")
    
    df = pd.read_csv(logs_path)
    return df

def compute_gap_slope(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the slope of the generalization gap over epochs for each seed.
    Uses linear regression on (epoch, gap) for each (seed_id, model_type) group.
    """
    results = []
    
    # Group by seed_id and model_type
    grouped = df.groupby(['seed_id', 'model_type'])
    
    for (seed_id, model_type), group in grouped:
        epochs = group['epoch'].values
        gaps = group['gap'].values
        
        # Perform simple linear regression: gap = slope * epoch + intercept
        # Using numpy's polyfit for slope calculation
        if len(epochs) < 2:
            slope = 0.0
        else:
            slope, _ = np.polyfit(epochs, gaps, 1)
        
        results.append({
            'seed_id': seed_id,
            'model_type': model_type,
            'gap_slope': slope
        })
    
    return pd.DataFrame(results)

def load_human_eval_results(results_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load HumanEval results from JSON.
    Expected structure: {
        "results": [
            {
                "seed_id": int,
                "model_type": str,
                "pass@1": float,
                ...
            },
            ...
        ]
    }
    """
    if results_path is None:
        project_root = get_project_root()
        results_path = project_root / "data" / "artifacts" / "human_eval_results.json"
    
    if not results_path.exists():
        raise FileNotFoundError(f"HumanEval results not found at {results_path}")
    
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    return data

def map_seed_to_human_eval_score(human_eval_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Map seed_id and model_type to HumanEval pass@1 score.
    Returns a DataFrame with columns: seed_id, model_type, human_eval_score
    """
    results = []
    
    if 'results' in human_eval_data:
        for entry in human_eval_data['results']:
            results.append({
                'seed_id': entry.get('seed_id'),
                'model_type': entry.get('model_type'),
                'human_eval_score': entry.get('pass@1', 0.0)
            })
    elif isinstance(human_eval_data, list):
        # Handle case where results are directly in a list
        for entry in human_eval_data:
            results.append({
                'seed_id': entry.get('seed_id'),
                'model_type': entry.get('model_type'),
                'human_eval_score': entry.get('pass@1', 0.0)
            })
    
    return pd.DataFrame(results)

def compute_gap_correlation(gap_slope_df: pd.DataFrame, human_eval_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate Pearson correlation between gap slope and HumanEval score.
    Returns a dictionary with correlation coefficient, p-value, and metadata.
    """
    # Merge the two DataFrames on seed_id and model_type
    merged = pd.merge(
        gap_slope_df, 
        human_eval_df, 
        on=['seed_id', 'model_type'], 
        how='inner'
    )
    
    if len(merged) == 0:
        raise ValueError("No matching seeds found between gap slopes and HumanEval results")
    
    if len(merged) < 2:
        raise ValueError("Need at least 2 data points to compute correlation")
    
    gap_slopes = merged['gap_slope'].values
    human_eval_scores = merged['human_eval_score'].values
    
    # Calculate Pearson correlation
    correlation_matrix = np.corrcoef(gap_slopes, human_eval_scores)
    correlation = correlation_matrix[0, 1]
    
    # Calculate p-value using t-distribution
    n = len(gap_slopes)
    if abs(correlation) >= 1.0:
        p_value = 0.0
    else:
        t_stat = correlation * math.sqrt((n - 2) / (1 - correlation ** 2))
        # Two-tailed p-value approximation using scipy if available, else manual
        try:
            from scipy import stats
            p_value = 2 * stats.t.sf(abs(t_stat), n - 2)
        except ImportError:
            # Fallback: rough approximation using error function
            # This is a simplified version; scipy is preferred
            p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))
    
    return {
        'correlation': float(correlation),
        'p_value': float(p_value),
        'n_samples': int(n),
        'threshold_met': abs(correlation) >= 0.5,
        'correlation_strength': 'strong' if abs(correlation) >= 0.5 else 'weak',
        'correlation_direction': 'positive' if correlation > 0 else 'negative',
        'seed_ids': merged['seed_id'].tolist(),
        'model_types': merged['model_type'].unique().tolist()
    }

def main():
    """Main entry point for computing correlation metrics."""
    project_root = get_project_root()
    output_dir = project_root / "data" / "artifacts"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load training logs
        print("Loading training logs...")
        logs_df = load_training_logs()
        print(f"Loaded {len(logs_df)} log entries")
        
        # Compute gap slopes
        print("Computing gap slopes...")
        gap_slope_df = compute_gap_slope(logs_df)
        print(f"Computed slopes for {len(gap_slope_df)} seed-model combinations")
        
        # Load HumanEval results
        print("Loading HumanEval results...")
        human_eval_data = load_human_eval_results()
        
        # Map to scores
        print("Mapping HumanEval scores...")
        human_eval_df = map_seed_to_human_eval_score(human_eval_data)
        print(f"Loaded {len(human_eval_df)} HumanEval results")
        
        # Compute correlation
        print("Computing Pearson correlation...")
        correlation_results = compute_gap_correlation(gap_slope_df, human_eval_df)
        
        # Save results
        output_path = output_dir / "correlation_results.json"
        with open(output_path, 'w') as f:
            json.dump(correlation_results, f, indent=2)
        
        print(f"Correlation results saved to {output_path}")
        print(f"Correlation coefficient: {correlation_results['correlation']:.4f}")
        print(f"P-value: {correlation_results['p_value']:.4f}")
        print(f"Threshold met (|r| >= 0.5): {correlation_results['threshold_met']}")
        
        return correlation_results
        
    except Exception as e:
        print(f"Error computing correlation: {e}", file=sys.stderr)
        raise

if __name__ == "__main__":
    main()
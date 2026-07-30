import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from statsmodels.stats.effect_size import CohensD

# Add project root to path to allow relative imports if run as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import TIMEOUT_SECONDS

logger = get_logger(__name__)

def load_results_csv(filepath: Path) -> pd.DataFrame:
    """Load the merged results CSV."""
    if not filepath.exists():
        raise FileNotFoundError(f"Results file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    
    required_cols = ['task_id', 'method', 'time_to_pivot', 'success', 'failure_type']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in results CSV: {missing_cols}")
    
    if df.empty:
        raise ValueError("Results CSV is empty")
    
    return df

def extract_paired_differences(df: pd.DataFrame) -> Dict[str, np.ndarray]:
    """
    Extract paired differences (Baseline - RuleEngine) for Time-to-Pivot.
    
    The data must be paired by task_id. We assume the merged results.csv
    contains both methods for the same task_id.
    """
    # Pivot to get one row per task_id with columns for each method
    pivot_df = df.pivot(index='task_id', columns='method', values='time_to_pivot')
    
    # Ensure both methods exist
    if 'Baseline' not in pivot_df.columns or 'RuleEngine' not in pivot_df.columns:
        raise ValueError("Merged results must contain both 'Baseline' and 'RuleEngine' methods")
    
    baseline_times = pivot_df['Baseline'].dropna().values
    rule_engine_times = pivot_df['RuleEngine'].dropna().values
    
    # Ensure alignment by dropping NaNs in both
    # Re-pivot to ensure alignment
    valid_ids = pivot_df.index[pivot_df['Baseline'].notna() & pivot_df['RuleEngine'].notna()]
    baseline_aligned = pivot_df.loc[valid_ids, 'Baseline'].values
    rule_engine_aligned = pivot_df.loc[valid_ids, 'RuleEngine'].values
    
    if len(baseline_aligned) == 0:
        raise ValueError("No paired observations found between Baseline and RuleEngine")
    
    # Difference: Baseline - RuleEngine (positive means RuleEngine is faster)
    differences = baseline_aligned - rule_engine_aligned
    
    return {
        'baseline': baseline_aligned,
        'rule_engine': rule_engine_aligned,
        'differences': differences,
        'n_pairs': len(differences)
    }

def calculate_cohens_d(differences: np.ndarray) -> Dict[str, float]:
    """
    Calculate Cohen's d for the paired differences.
    
    For paired data, Cohen's d is calculated as:
    d = mean(differences) / std(differences)
    
    This is sometimes referred to as d_z (Cohen's d for dependent samples).
    """
    mean_diff = np.mean(differences)
    std_diff = np.std(differences, ddof=1)  # Sample standard deviation
    
    if std_diff == 0:
        logger.warning("Standard deviation of differences is zero. Effect size is undefined (infinity).")
        return {
            'cohens_d': float('inf') if mean_diff > 0 else float('-inf') if mean_diff < 0 else 0.0,
            'mean_difference': float(mean_diff),
            'std_difference': 0.0
        }
    
    cohens_d = mean_diff / std_diff
    
    return {
        'cohens_d': float(cohens_d),
        'mean_difference': float(mean_diff),
        'std_difference': float(std_diff)
    }

def calculate_effect_size(results_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Main function to calculate effect size for Time-to-Pivot differences.
    
    Args:
        results_path: Path to data/derived/results.csv
        output_path: Path to write data/derived/effect_size_results.json
    
    Returns:
        Dictionary containing effect size results
    """
    log_stage_start("Calculate Effect Size", str(results_path))
    
    try:
        # Load data
        logger.info(f"Loading results from {results_path}")
        df = load_results_csv(results_path)
        
        # Extract paired differences
        logger.info("Extracting paired differences (Baseline - RuleEngine)")
        paired_data = extract_paired_differences(df)
        
        logger.info(f"Found {paired_data['n_pairs']} paired observations")
        
        # Calculate Cohen's d
        logger.info("Calculating Cohen's d for paired differences")
        effect_size_metrics = calculate_cohens_d(paired_data['differences'])
        
        # Interpret effect size
        d = effect_size_metrics['cohens_d']
        if abs(d) < 0.2:
            interpretation = "negligible"
        elif abs(d) < 0.5:
            interpretation = "small"
        elif abs(d) < 0.8:
            interpretation = "medium"
        else:
            interpretation = "large"
        
        # Compile results
        results = {
            'n_pairs': paired_data['n_pairs'],
            'mean_difference_seconds': effect_size_metrics['mean_difference'],
            'std_difference_seconds': effect_size_metrics['std_difference'],
            'cohens_d': effect_size_metrics['cohens_d'],
            'effect_size_interpretation': interpretation,
            'direction': "RuleEngine faster" if effect_size_metrics['mean_difference'] > 0 else "Baseline faster" if effect_size_metrics['mean_difference'] < 0 else "No difference",
            'methodology': "Paired Cohen's d (d_z) calculated on Time-to-Pivot differences (Baseline - RuleEngine)",
            'notes': [
                "Positive effect size indicates RuleEngine is faster on average.",
                "Negative effect size indicates Baseline is faster on average.",
                "Effect size magnitude: negligible (<0.2), small (0.2-0.5), medium (0.5-0.8), large (>0.8)."
            ]
        }
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write results
        logger.info(f"Writing effect size results to {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Effect size calculation complete. Cohen's d = {results['cohens_d']:.4f} ({interpretation})")
        log_stage_end("Calculate Effect Size", "Success")
        
        return results
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        log_stage_end("Calculate Effect Size", "Failed - File not found")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        log_stage_end("Calculate Effect Size", "Failed - Data validation error")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        log_stage_end("Calculate Effect Size", "Failed - Unexpected error")
        raise

def main():
    """Entry point for the effect size calculation script."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    results_path = project_root / "data" / "derived" / "results.csv"
    output_path = project_root / "data" / "derived" / "effect_size_results.json"
    
    try:
        results = calculate_effect_size(results_path, output_path)
        print(f"Effect size calculation successful. Output written to: {output_path}")
        print(f"Cohen's d: {results['cohens_d']:.4f} ({results['effect_size_interpretation']})")
        print(f"Direction: {results['direction']}")
        sys.exit(0)
    except Exception as e:
        print(f"Effect size calculation failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
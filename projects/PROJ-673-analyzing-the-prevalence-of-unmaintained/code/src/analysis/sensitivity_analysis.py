import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from src.config.settings import get_config

logger = logging.getLogger(__name__)

def load_dependencies_data(input_path: str) -> pd.DataFrame:
    """Load the dependencies dataset from CSV."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return pd.read_csv(path)

def calculate_unmaintained_proportion(df: pd.DataFrame, threshold_days: int) -> float:
    """
    Calculate the proportion of dependencies considered 'unmaintained'
    based on the age_in_days threshold.
    
    A dependency is unmaintained if age_in_days > threshold_days.
    Rows with null age_in_days are excluded from this specific calculation.
    """
    valid_mask = df['age_in_days'].notna()
    if valid_mask.sum() == 0:
        return 0.0
    
    valid_df = df[valid_mask]
    unmaintained_count = (valid_df['age_in_days'] > threshold_days).sum()
    return unmaintained_count / len(valid_df)

def run_sensitivity_analysis(
    input_path: str,
    output_path: str,
    threshold_range: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Run sensitivity analysis for the 'unmaintained' threshold.
    
    Args:
        input_path: Path to the input CSV (dependencies_raw.csv).
        output_path: Path to write the JSON results.
        threshold_range: List of thresholds to sweep. If None, uses config 
                         default (180 ± 90 -> 90 to 270).
    
    Returns:
        Dictionary with sensitivity analysis results.
    """
    logger.info(f"Loading data from {input_path}")
    df = load_dependencies_data(input_path)
    
    # Determine threshold range from config or use default
    if threshold_range is None:
        config = get_config()
        base = getattr(config, 'UNMAINTAINED_THRESHOLD_BASE', 180)
        delta = getattr(config, 'UNMAINTAINED_THRESHOLD_DELTA', 90)
        # Generate range: base - delta to base + delta
        threshold_range = list(range(base - delta, base + delta + 1, 10))
    
    logger.info(f"Running sensitivity sweep over thresholds: {threshold_range}")
    
    results = []
    for threshold in threshold_range:
        proportion = calculate_unmaintained_proportion(df, threshold)
        
        # Robustness score: How stable is the proportion?
        # We define robustness as 1 - |derivative| (normalized).
        # Since we are sweeping, we calculate the change from the previous point.
        # If this is the first point, robustness is 1.0.
        if len(results) == 0:
            robustness = 1.0
        else:
            prev_prop = results[-1]['unmaintained_proportion']
            diff = abs(proportion - prev_prop)
            # Normalize by max possible change (1.0)
            robustness = max(0.0, 1.0 - (diff * 10)) # Scale factor for visibility
        
        results.append({
            'threshold': threshold,
            'unmaintained_proportion': round(proportion, 4),
            'robustness_score': round(robustness, 4)
        })
    
    output_data = {
        'threshold_sweep': results,
        'base_threshold': threshold_range[len(threshold_range)//2] if threshold_range else 180,
        'total_dependencies_analyzed': len(df)
    }
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing results to {output_path}")
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    return output_data

def main():
    """Entry point for the sensitivity analysis script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run sensitivity analysis for unmaintained threshold.')
    parser.add_argument('--input', type=str, required=True, help='Path to input CSV')
    parser.add_argument('--output', type=str, required=True, help='Path to output JSON')
    parser.add_argument('--config-base', type=int, default=180, help='Base threshold days')
    parser.add_argument('--config-delta', type=int, default=90, help='Delta for threshold sweep')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Construct range based on args
        start = args.config_base - args.config_delta
        end = args.config_base + args.config_delta
        threshold_range = list(range(start, end + 1, 10))
        
        result = run_sensitivity_analysis(
            input_path=args.input,
            output_path=args.output,
            threshold_range=threshold_range
        )
        
        print(f"Sensitivity analysis complete. Results written to {args.output}")
        print(f"Found {len(result['threshold_sweep'])} threshold points.")
        
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        raise

if __name__ == '__main__':
    main()

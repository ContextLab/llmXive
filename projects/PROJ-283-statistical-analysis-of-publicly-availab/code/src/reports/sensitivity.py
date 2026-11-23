"""
Sensitivity Analysis Module for Threshold Sweep and Jaccard Index Calculation.

Implements SC-004: Threshold sweep analysis over specific p-value thresholds.
Calculates pairwise Jaccard indices to measure stability of significant predictors.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Set, Optional
from pathlib import Path
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default thresholds from Spec SC-004
DEFAULT_THRESHOLDS = [0.005, 0.01, 0.05]

def get_significant_predictors(
    p_values: pd.Series, 
    threshold: float
) -> Set[str]:
    """
    Get the set of predictors with corrected p-value < threshold.
    
    Args:
        p_values: Series of corrected p-values indexed by predictor name.
        threshold: The p-value threshold.
        
    Returns:
        Set of predictor names considered significant at this threshold.
        
    Note:
        Predictors with NaN p-values are excluded from the set.
    """
    if p_values is None or p_values.empty:
        return set()
    
    # Drop NaN values as per requirement
    valid_series = p_values.dropna()
    
    # Filter for significance
    significant = set(valid_series[valid_series < threshold].index.tolist())
    return significant

def calculate_jaccard_index(set_a: Set[str], set_b: Set[str]) -> float:
    """
    Calculate the Jaccard index between two sets.
    
    Jaccard Index = |A ∩ B| / |A ∪ B|
    
    Args:
        set_a: First set of elements.
        set_b: Second set of elements.
        
    Returns:
        Jaccard index as a float between 0.0 and 1.0.
        
    Edge Case:
        If both sets are empty, returns 0.0 to prevent division by zero.
        If the union is empty (both empty), returns 0.0.
    """
    if not set_a and not set_b:
        return 0.0
    
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    
    if union == 0:
        return 0.0
        
    return intersection / union

def perform_threshold_sweep(
    p_values: pd.Series, 
    thresholds: Optional[List[float]] = None
) -> Dict[float, Dict]:
    """
    Perform a threshold sweep over specified p-value thresholds.
    
    For each threshold, calculates:
    - The set of significant predictors.
    - The count of significant predictors.
    
    Args:
        p_values: Series of corrected p-values.
        thresholds: List of thresholds to sweep (defaults to SC-004 set).
        
    Returns:
        Dictionary mapping threshold -> {
            'significant_predictors': list of names,
            'count': int
        }
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS
        
    results = {}
    
    for threshold in thresholds:
        significant_set = get_significant_predictors(p_values, threshold)
        results[threshold] = {
            'significant_predictors': sorted(list(significant_set)),
            'count': len(significant_set)
        }
        logger.info(f"Threshold {threshold}: {len(significant_set)} significant predictors")
        
    return results

def calculate_pairwise_jaccard(
    p_values: pd.Series,
    thresholds: Optional[List[float]] = None
) -> Dict[Tuple[float, float], float]:
    """
    Calculate pairwise Jaccard indices for all pairs of thresholds.
    
    Args:
        p_values: Series of corrected p-values.
        thresholds: List of thresholds to compare.
        
    Returns:
        Dictionary mapping (threshold_a, threshold_b) -> Jaccard index.
        
    Edge Case:
        If a threshold yields an empty set, Jaccard with any other set is 0.0.
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS
        
    # Perform sweep to get sets
    sweep_results = perform_threshold_sweep(p_values, thresholds)
    
    pairwise_jaccards = {}
    
    # Iterate over all unique pairs
    for i in range(len(thresholds)):
        for j in range(i + 1, len(thresholds)):
            t1 = thresholds[i]
            t2 = thresholds[j]
            
            set1 = set(sweep_results[t1]['significant_predictors'])
            set2 = set(sweep_results[t2]['significant_predictors'])
            
            jaccard = calculate_jaccard_index(set1, set2)
            pairwise_jaccards[(t1, t2)] = jaccard
            
            logger.info(f"Jaccard({t1}, {t2}) = {jaccard:.4f}")
            
    return pairwise_jaccards

def generate_sensitivity_report(
    p_values: pd.Series,
    thresholds: Optional[List[float]] = None,
    output_path: Optional[Path] = None
) -> Dict:
    """
    Generate the full sensitivity analysis report.
    
    This includes:
    - Threshold sweep results (counts and sets).
    - Delta calculation (variation in counts between steps).
    - Pairwise Jaccard indices.
    
    Args:
        p_values: Series of corrected p-values.
        thresholds: List of thresholds to analyze.
        output_path: Path to save the JSON report (optional).
        
    Returns:
        Dictionary containing the full analysis results.
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS
        
    # Sort thresholds for consistent delta calculation
    sorted_thresholds = sorted(thresholds)
    
    # 1. Perform Threshold Sweep
    sweep_data = perform_threshold_sweep(p_values, sorted_thresholds)
    
    # 2. Calculate Deltas (variation in number of significant predictors)
    deltas = []
    counts = [sweep_data[t]['count'] for t in sorted_thresholds]
    
    for k in range(1, len(counts)):
        delta = counts[k] - counts[k-1]
        deltas.append({
            'from_threshold': sorted_thresholds[k-1],
            'to_threshold': sorted_thresholds[k],
            'delta_count': delta
        })
        
    # 3. Calculate Pairwise Jaccard Indices
    pairwise_jaccards = calculate_pairwise_jaccard(p_values, sorted_thresholds)
    
    # Format pairwise results for JSON
    pairwise_results = [
        {
            'threshold_a': k[0],
            'threshold_b': k[1],
            'jaccard_index': v
        }
        for k, v in sorted(pairwise_jaccards.items())
    ]
    
    # 4. Compile Final Report
    report = {
        'thresholds_analyzed': sorted_thresholds,
        'sweep_results': {str(k): v for k, v in sweep_data.items()},
        'delta_variation': deltas,
        'pairwise_jaccard_indices': pairwise_results
    }
    
    # Save to file if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Sensitivity report saved to {output_path}")
        
    return report

def run_sensitivity_analysis(
    model_metrics_path: Path,
    output_path: Path,
    thresholds: Optional[List[float]] = None
) -> Dict:
    """
    Main entry point to run sensitivity analysis on saved model metrics.
    
    Reads corrected p-values from the model metrics file and generates
    the sensitivity analysis report.
    
    Args:
        model_metrics_path: Path to the model_metrics.json file.
        output_path: Path to save the sensitivity_analysis.json file.
        thresholds: Optional custom thresholds.
        
    Returns:
        The sensitivity analysis report dictionary.
        
    Raises:
        FileNotFoundError: If model_metrics_path does not exist.
        ValueError: If p-values are missing or malformed.
    """
    if not model_metrics_path.exists():
        raise FileNotFoundError(f"Model metrics file not found: {model_metrics_path}")
        
    # Load model metrics
    with open(model_metrics_path, 'r') as f:
        metrics = json.load(f)
        
    # Extract p-values. The structure depends on T024/T027 output.
    # Assuming 'corrected_p_values' is a dict or list of dicts with 'predictor' and 'p_value'.
    # Based on T024 spec: Output is a DataFrame with 'original_p_value' and 'corrected_p_value'.
    # We need to construct a Series indexed by predictor name.
    
    p_values_dict = {}
    
    # Handle different possible structures from fit.py/metrics.py
    if 'corrected_p_values' in metrics:
        cpv_data = metrics['corrected_p_values']
        if isinstance(cpv_data, list):
            # List of dicts: [{'predictor': 'x1', 'corrected_p_value': 0.01}, ...]
            for item in cpv_data:
                name = item.get('predictor') or item.get('feature')
                val = item.get('corrected_p_value') or item.get('p_value')
                if name is not None and val is not None:
                    p_values_dict[name] = val
        elif isinstance(cpv_data, dict):
            # Dict: {'x1': 0.01, 'x2': 0.05}
            p_values_dict = cpv_data
            
    if not p_values_dict:
        raise ValueError("Could not extract corrected p-values from model metrics.")
        
    p_values_series = pd.Series(p_values_dict)
    
    # Run the analysis
    report = generate_sensitivity_report(
        p_values_series,
        thresholds=thresholds,
        output_path=output_path
    )
    
    return report

def main():
    """
    CLI entry point for sensitivity analysis.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on model metrics.")
    parser.add_argument(
        "--input", 
        type=Path, 
        default=Path("data/results/model_metrics.json"),
        help="Path to model_metrics.json"
    )
    parser.add_argument(
        "--output", 
        type=Path, 
        default=Path("data/results/sensitivity_analysis.json"),
        help="Path to save sensitivity_analysis.json"
    )
    parser.add_argument(
        "--thresholds",
        type=str,
        default="0.005,0.01,0.05",
        help="Comma-separated list of thresholds (default: 0.005,0.01,0.05)"
    )
    
    args = parser.parse_args()
    
    try:
        # Parse thresholds
        thresholds = [float(x.strip()) for x in args.thresholds.split(',')]
        
        logger.info(f"Running sensitivity analysis with thresholds: {thresholds}")
        logger.info(f"Input: {args.input}, Output: {args.output}")
        
        report = run_sensitivity_analysis(
            model_metrics_path=args.input,
            output_path=args.output,
            thresholds=thresholds
        )
        
        logger.info("Sensitivity analysis completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise SystemExit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        raise SystemExit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
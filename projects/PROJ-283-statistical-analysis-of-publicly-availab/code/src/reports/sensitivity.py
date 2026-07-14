"""
Sensitivity analysis for model threshold stability.

Implements threshold sweep analysis over a range of small p-value thresholds
to compute the Jaccard index of significant predictors (FR-010).
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Set
from pathlib import Path
import json
import logging
from src.config import ensure_directories

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_jaccard_index(set_a: Set[str], set_b: Set[str]) -> float:
    """
    Calculate the Jaccard index between two sets.
    J = |A ∩ B| / |A ∪ B|
    
    Args:
        set_a: First set of elements
        set_b: Second set of elements
        
    Returns:
        Jaccard index between 0.0 and 1.0
    """
    if not set_a and not set_b:
        return 1.0  # Both empty, perfect agreement
    
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    
    if union == 0:
        return 1.0
        
    return intersection / union

def get_significant_predictors(
    results_df: pd.DataFrame, 
    p_value_col: str, 
    threshold: float
) -> Set[str]:
    """
    Get the set of predictor names that are significant at the given threshold.
    
    Args:
        results_df: DataFrame containing model results with p-values
        p_value_col: Name of the column containing p-values
        threshold: P-value threshold for significance
        
    Returns:
        Set of predictor names with p-values below threshold
    """
    significant = results_df[results_df[p_value_col] < threshold]
    return set(significant.index) if 'index' in results_df.columns else set(significant[p_value_col].index)

def perform_threshold_sweep(
    model_results: pd.DataFrame,
    p_value_column: str = 'p_value',
    threshold_range: List[float] = None
) -> Dict:
    """
    Perform threshold sweep analysis to measure stability of significant predictors.
    
    Args:
        model_results: DataFrame with predictor names as index and p-values
        p_value_column: Column name containing p-values
        threshold_range: List of thresholds to sweep (defaults to 0.001 to 0.1)
        
    Returns:
        Dictionary containing sweep results with Jaccard indices
    """
    if threshold_range is None:
        threshold_range = [0.001, 0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1]
    
    # Sort thresholds to ensure sequential comparison
    threshold_range = sorted(threshold_range)
    
    results = {
        'thresholds': threshold_range,
        'significant_sets': [],
        'jaccard_indices': [],
        'pairwise_jaccards': []
    }
    
    significant_sets = []
    
    logger.info(f"Performing threshold sweep over {len(threshold_range)} thresholds")
    
    for i, threshold in enumerate(threshold_range):
        significant = get_significant_predictors(model_results, p_value_column, threshold)
        significant_sets.append(significant)
        
        logger.info(f"Threshold {threshold:.3f}: {len(significant)} significant predictors")
        
        # Calculate Jaccard index with previous threshold if available
        if i > 0:
            prev_set = significant_sets[i - 1]
            jaccard = calculate_jaccard_index(prev_set, significant)
            results['jaccard_indices'].append(jaccard)
            results['pairwise_jaccards'].append({
                'threshold_from': threshold_range[i - 1],
                'threshold_to': threshold,
                'jaccard_index': jaccard
            })
        else:
            results['jaccard_indices'].append(1.0)  # First threshold has no previous
    
    results['significant_sets'] = [list(s) for s in significant_sets]
    
    # Calculate overall stability metric (mean Jaccard index)
    if results['jaccard_indices']:
        results['mean_jaccard_index'] = float(np.mean(results['jaccard_indices']))
        results['std_jaccard_index'] = float(np.std(results['jaccard_indices']))
    else:
        results['mean_jaccard_index'] = 0.0
        results['std_jaccard_index'] = 0.0
        
    logger.info(f"Sweep complete. Mean Jaccard index: {results['mean_jaccard_index']:.4f}")
    
    return results

def generate_sensitivity_report(
    model_metrics_path: str,
    output_path: str,
    p_value_column: str = 'p_value',
    threshold_range: List[float] = None
) -> Dict:
    """
    Generate a comprehensive sensitivity analysis report.
    
    Args:
        model_metrics_path: Path to the model metrics JSON file
        output_path: Path to save the sensitivity report
        p_value_column: Column name containing p-values
        threshold_range: List of thresholds to sweep
        
    Returns:
        Dictionary containing the sensitivity analysis results
    """
    ensure_directories()
    
    logger.info(f"Loading model metrics from {model_metrics_path}")
    
    # Load model metrics
    with open(model_metrics_path, 'r') as f:
        model_metrics = json.load(f)
    
    # Convert coefficients and p-values to DataFrame
    # Assuming structure: {model_type: {model_name: {coefficients: {...}, p_values: {...}}}}
    report_data = {
        'analysis_type': 'threshold_sweep_sensitivity',
        'models_analyzed': [],
        'results': {}
    }
    
    for model_type, models in model_metrics.items():
        if not isinstance(models, dict):
            continue
            
        for model_name, model_data in models.items():
            if 'p_values' not in model_data or 'coefficients' not in model_data:
                logger.warning(f"Skipping {model_type}/{model_name}: missing p_values or coefficients")
                continue
                
            p_values = model_data['p_values']
            coefficients = model_data['coefficients']
            
            # Create DataFrame with p-values
            df = pd.DataFrame({
                'coefficient': coefficients,
                'p_value': p_values
            }, index=p_values.keys())
            
            logger.info(f"Analyzing {model_type}/{model_name} with {len(df)} predictors")
            
            # Perform threshold sweep
            sweep_results = perform_threshold_sweep(
                df, 
                p_value_column='p_value',
                threshold_range=threshold_range
            )
            
            report_data['models_analyzed'].append(f"{model_type}/{model_name}")
            report_data['results'][f"{model_type}_{model_name}"] = sweep_results
            
    # Save report
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2, default=str)
    
    logger.info(f"Sensitivity report saved to {output_path}")
    
    return report_data

def main():
    """Main entry point for sensitivity analysis."""
    # Define paths
    base_path = Path(__file__).parent.parent.parent
    metrics_path = base_path / "data" / "results" / "model_metrics.json"
    output_path = base_path / "data" / "results" / "sensitivity_analysis.json"
    
    # Define threshold range (small thresholds for p-values)
    threshold_range = [0.001, 0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1]
    
    if not metrics_path.exists():
        logger.error(f"Model metrics file not found at {metrics_path}")
        logger.error("Please run the modeling pipeline first to generate model_metrics.json")
        return 1
    
    try:
        report = generate_sensitivity_report(
            str(metrics_path),
            str(output_path),
            p_value_column='p_value',
            threshold_range=threshold_range
        )
        
        print(f"Sensitivity analysis complete.")
        print(f"Models analyzed: {', '.join(report['models_analyzed'])}")
        print(f"Report saved to: {output_path}")
        
        # Print summary
        for model_key, results in report['results'].items():
            print(f"\n{model_key}:")
            print(f"  Mean Jaccard Index: {results['mean_jaccard_index']:.4f} (+/- {results['std_jaccard_index']:.4f})")
            print(f"  Thresholds tested: {len(results['thresholds'])}")
            
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}")
        raise
        
    return 0

if __name__ == "__main__":
    exit(main())

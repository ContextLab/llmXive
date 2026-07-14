import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from utils import setup_logging, pin_random_seed
from config import Config, get_config

# Setup logger
logger = logging.getLogger(__name__)

def bin_dataset_size(n_rows: int) -> str:
    """
    Bin dataset size into categories:
    - 'small': n < 50
    - 'medium': 50 <= n <= 200
    - 'large': n > 200
    """
    if n_rows < 50:
        return 'small'
    elif n_rows <= 200:
        return 'medium'
    else:
        return 'large'

def load_baseline_metrics(filepath: str = None) -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if filepath is None:
        filepath = os.path.join('data', 'processed', 'baseline_metrics.json')
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Baseline metrics file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        return json.load(f)

def load_cleaned_metrics(filepath: str = None) -> Dict[str, Any]:
    """Load cleaned metrics from JSON file."""
    if filepath is None:
        filepath = os.path.join('data', 'processed', 'cleaned_metrics.json')
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cleaned metrics file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_p_value_shift(baseline_p: float, cleaned_p: float) -> float:
    """Calculate absolute difference between baseline and cleaned p-values."""
    return abs(cleaned_p - baseline_p)

def analyze_size_bin(
    datasets: List[Dict[str, Any]], 
    bin_name: str,
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze a specific size bin of datasets.
    
    Args:
        datasets: List of dataset entries with size info
        bin_name: Name of the bin (small, medium, large)
        baseline_metrics: Baseline metrics dictionary
        cleaned_metrics: Cleaned metrics dictionary
        
    Returns:
        Dictionary with analysis results for this bin
    """
    bin_datasets = [d for d in datasets if d.get('size_bin') == bin_name]
    
    result = {
        'bin': bin_name,
        'count': len(bin_datasets),
        'datasets': []
    }
    
    if len(bin_datasets) == 0:
        logger.warning(f"CONSTRAINT_VIOLATION: Bin '{bin_name}' is empty (0 datasets). Proceeding with empty bin.")
        return result
    
    if len(bin_datasets) < 1:
        logger.warning(f"Warning: Bin '{bin_name}' has <1 dataset ({len(bin_datasets)}). Results may be unstable.")
    
    for ds in bin_datasets:
        dataset_name = ds.get('dataset_name')
        dataset_size = ds.get('dataset_size')
        
        # Find corresponding baseline entry
        baseline_entry = None
        if 'datasets' in baseline_metrics:
            for b in baseline_metrics['datasets']:
                if b.get('dataset_name') == dataset_name:
                    baseline_entry = b
                    break
        
        # Find corresponding cleaned entries (could be multiple strategies)
        cleaned_entries = []
        if 'datasets' in cleaned_metrics:
            for c in cleaned_metrics['datasets']:
                if c.get('dataset_name') == dataset_name:
                    cleaned_entries.append(c)
        
        if baseline_entry and cleaned_entries:
            # Calculate p-value shifts for each cleaning strategy
            for cleaned_entry in cleaned_entries:
                strategy = cleaned_entry.get('strategy', 'unknown')
                
                # Extract p-values (assuming t-test on first variable)
                baseline_p = baseline_entry.get('t_test', {}).get('p_value')
                cleaned_p = cleaned_entry.get('t_test', {}).get('p_value')
                
                if baseline_p is not None and cleaned_p is not None:
                    p_shift = calculate_p_value_shift(baseline_p, cleaned_p)
                    
                    result['datasets'].append({
                        'dataset_name': dataset_name,
                        'dataset_size': dataset_size,
                        'strategy': strategy,
                        'baseline_p': baseline_p,
                        'cleaned_p': cleaned_p,
                        'p_value_shift': p_shift
                    })
        
    return result

def run_sensitivity_analysis(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any],
    output_path: str = None
) -> Dict[str, Any]:
    """
    Run sensitivity analysis across dataset size bins.
    
    Args:
        baseline_metrics: Baseline metrics dictionary
        cleaned_metrics: Cleaned metrics dictionary
        output_path: Path to save results (optional)
        
    Returns:
        Dictionary containing sensitivity analysis results
    """
    # Prepare output path
    if output_path is None:
        output_path = os.path.join('data', 'processed', 'size_sensitivity_analysis.json')
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Collect all datasets from baseline metrics
    all_datasets = []
    if 'datasets' in baseline_metrics:
        for ds in baseline_metrics['datasets']:
            dataset_name = ds.get('dataset_name')
            dataset_size = ds.get('dataset_size', 0)
            size_bin = bin_dataset_size(dataset_size)
            
            all_datasets.append({
                'dataset_name': dataset_name,
                'dataset_size': dataset_size,
                'size_bin': size_bin
            })
    
    # Analyze each bin
    bins = ['small', 'medium', 'large']
    bin_results = {}
    
    for bin_name in bins:
        bin_result = analyze_size_bin(
            all_datasets, 
            bin_name, 
            baseline_metrics, 
            cleaned_metrics
        )
        bin_results[bin_name] = bin_result
      
        # Log if bin has < 1 dataset
        if bin_result['count'] < 1:
            logger.warning(f"CONSTRAINT_VIOLATION: Bin '{bin_name}' has {bin_result['count']} datasets. Warning logged as per requirement.")
    
    # Compile final result
    sensitivity_result = {
        'timestamp': datetime.now().isoformat(),
        'analysis_type': 'dataset_size_sensitivity',
        'bins': bin_results,
        'summary': {
            'total_datasets': len(all_datasets),
            'bin_counts': {
                'small': bin_results['small']['count'],
                'medium': bin_results['medium']['count'],
                'large': bin_results['large']['count']
            }
        }
    }
    
    # Write to file
    with open(output_path, 'w') as f:
        json.dump(sensitivity_result, f, indent=2)
    
    logger.info(f"Size sensitivity analysis written to {output_path}")
    return sensitivity_result

def main():
    """Main entry point for dataset size sensitivity analysis."""
    setup_logging("INFO")
    pin_random_seed(42)
    
    logger.info("Starting T030: Dataset Size Sensitivity Analysis")
    
    try:
        # Load metrics
        baseline_metrics = load_baseline_metrics()
        cleaned_metrics = load_cleaned_metrics()
        
        logger.info(f"Loaded baseline metrics with {len(baseline_metrics.get('datasets', []))} datasets")
        logger.info(f"Loaded cleaned metrics with {len(cleaned_metrics.get('datasets', []))} datasets")
        
        # Run analysis
        output_path = os.path.join('data', 'processed', 'size_sensitivity_analysis.json')
        result = run_sensitivity_analysis(baseline_metrics, cleaned_metrics, output_path)
        
        logger.info("T030 completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        logger.error("Please ensure baseline_metrics.json and cleaned_metrics.json exist in data/processed/")
        return 1
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())

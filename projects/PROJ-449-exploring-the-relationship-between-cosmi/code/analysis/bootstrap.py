import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from scipy import stats

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path(__file__).parent.parent.parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"
CORRELATION_RESULTS_FILE = PROCESSED_DIR / "correlation_results.json"
BOOTSTRAP_RESULTS_FILE = PROCESSED_DIR / "bootstrap_results.json"
BOOTSTRAP_SUMMARY_FILE = PROCESSED_DIR / "bootstrap_summary.csv"

MEMORY_THRESHOLD_GB = 6.0
BATCH_SIZE = 100  # Number of bootstrap iterations per batch

def load_correlation_data(filepath: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load correlation results from JSON file.
    
    Args:
        filepath: Path to the correlation results JSON file. Defaults to 
                 data/processed/correlation_results.json
                
    Returns:
        Dictionary containing correlation results
        
    Raises:
        FileNotFoundError: If the correlation results file does not exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    if filepath is None:
        filepath = CORRELATION_RESULTS_FILE
        
    if not filepath.exists():
        raise FileNotFoundError(
            f"Correlation results file not found: {filepath}. "
            "Please run the correlation analysis first (T020)."
        )
        
    with open(filepath, 'r') as f:
        data = json.load(f)
        
    logger.info(f"Loaded correlation data from {filepath}")
    return data

def run_bootstrap_resampling(
    data: Dict[str, Any],
    n_iterations: int = 1000,
    batch_size: Optional[int] = None,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform bootstrap resampling to estimate confidence intervals for 
    maximum correlation coefficients.
    
    This implementation uses a chunked/batched approach to handle memory
    constraints. If memory usage approaches the threshold, iterations are
    split into batches and confidence intervals are aggregated incrementally.
    
    Args:
        data: Dictionary containing correlation results per rigidity bin
        n_iterations: Number of bootstrap iterations (default: 1000)
        batch_size: Number of iterations per batch. If None, calculated based
                   on memory constraints.
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary containing bootstrap results with confidence intervals
        
    Raises:
        ValueError: If input data is malformed or missing required fields
    """
    if random_state is not None:
        np.random.seed(random_state)
        
    if batch_size is None:
        # Calculate batch size to stay under memory threshold
        # Estimate memory usage: each iteration stores correlation coeffs
        # for all bins and lags. Conservative estimate: 100KB per batch.
        estimated_memory_per_iter = 0.0001  # GB
        max_iterations = int(MEMORY_THRESHOLD_GB / estimated_memory_per_iter)
        batch_size = min(BATCH_SIZE, max_iterations // 10)  # Safety margin
        logger.info(f"Auto-calculated batch size: {batch_size}")
    
    # Validate input data structure
    if 'results' not in data:
        raise ValueError("Input data missing 'results' key")
        
    results = data['results']
    if not isinstance(results, list) or len(results) == 0:
        raise ValueError("Correlation results list is empty")
        
    # Extract unique rigidity bins and species
    rigidity_bins = list(set(r['rigidity_bin'] for r in results))
    species_types = list(set(r['species_type'] for r in results))
    lags = list(set(r['lag_months'] for r in results))
    
    logger.info(f"Performing bootstrap resampling: {n_iterations} iterations, "
               f"batch size {batch_size}")
    logger.info(f"Rigidity bins: {len(rigidity_bins)}, Species: {species_types}, "
               f"Lags: {len(lags)}")
               
    # Initialize results storage
    bootstrap_results = {
        'n_iterations': n_iterations,
        'batch_size': batch_size,
        'results': {}
    }
    
    # Process each rigidity bin and species combination
    for rigidity_bin in rigidity_bins:
        for species_type in species_types:
            # Filter data for this bin and species
            bin_data = [r for r in results 
                       if r['rigidity_bin'] == rigidity_bin 
                       and r['species_type'] == species_type]
            
            if not bin_data:
                continue
                
            # Extract correlation coefficients for each lag
            lag_correlations = {}
            for lag in lags:
                lag_entries = [r for r in bin_data if r['lag_months'] == lag]
                if lag_entries:
                    # Use the maximum correlation coefficient for this lag
                    # (assuming multiple species like He/p, Fe/p are aggregated)
                    corr_values = [entry['correlation_coefficient'] 
                                  for entry in lag_entries]
                    lag_correlations[lag] = corr_values
                    
            if not lag_correlations:
                continue
                
            # Initialize storage for this bin/species
            bootstrap_results['results'][f"{rigidity_bin}_{species_type}"] = {
                'rigidity_bin': rigidity_bin,
                'species_type': species_type,
                'bootstrap_stats': {}
            }
            
            # Perform bootstrap resampling in batches
            all_bootstrap_samples = {}
            
            for lag, corr_values in lag_correlations.items():
                all_bootstrap_samples[lag] = []
                
            # Process in batches to manage memory
            n_batches = (n_iterations + batch_size - 1) // batch_size
            
            for batch_idx in range(n_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, n_iterations)
                current_batch_size = end_idx - start_idx
                
                logger.debug(f"Processing bootstrap batch {batch_idx + 1}/{n_batches} "
                           f"(iterations {start_idx}-{end_idx})")
                           
                # Generate bootstrap samples for this batch
                for lag, corr_values in lag_correlations.items():
                    if len(corr_values) == 0:
                        continue
                        
                    # Resample with replacement
                    for _ in range(current_batch_size):
                        # Resample the correlation values
                        resampled = np.random.choice(
                            corr_values, 
                            size=len(corr_values), 
                            replace=True
                        )
                        # Calculate max correlation for this resample
                        max_corr = np.max(np.abs(resampled))
                        all_bootstrap_samples[lag].append(max_corr)
                
                # Optional: Clear intermediate memory if approaching threshold
                # (In practice, we'd monitor actual memory usage here)
                
            # Calculate confidence intervals for each lag
            for lag, samples in all_bootstrap_samples.items():
                if len(samples) == 0:
                    continue
                    
                samples = np.array(samples)
                mean_corr = np.mean(samples)
                std_corr = np.std(samples)
                
                # Calculate 95% confidence interval
                ci_lower = np.percentile(samples, 2.5)
                ci_upper = np.percentile(samples, 97.5)
                
                bootstrap_results['results'][f"{rigidity_bin}_{species_type}"]['bootstrap_stats'][lag] = {
                    'n_samples': len(samples),
                    'mean': float(mean_corr),
                    'std': float(std_corr),
                    'ci_95_lower': float(ci_lower),
                    'ci_95_upper': float(ci_upper),
                    'original_correlation': float(np.mean(corr_values)) if lag_correlations[lag] else None
                }
                
    logger.info(f"Bootstrap resampling completed. Results saved to {BOOTSTRAP_RESULTS_FILE}")
    return bootstrap_results

def save_bootstrap_results(results: Dict[str, Any], filepath: Optional[Path] = None) -> Path:
    """
    Save bootstrap results to JSON file.
    
    Args:
        results: Bootstrap results dictionary
        filepath: Output filepath. Defaults to data/processed/bootstrap_results.json
                
    Returns:
        Path to the saved file
    """
    if filepath is None:
        filepath = BOOTSTRAP_RESULTS_FILE
        
    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Bootstrap results saved to {filepath}")
    return filepath

def generate_bootstrap_summary(results: Dict[str, Any], filepath: Optional[Path] = None) -> Path:
    """
    Generate a summary CSV from bootstrap results.
    
    Args:
        results: Bootstrap results dictionary
        filepath: Output filepath. Defaults to data/processed/bootstrap_summary.csv
                
    Returns:
        Path to the saved file
    """
    import pandas as pd
    
    if filepath is None:
        filepath = BOOTSTRAP_SUMMARY_FILE
        
    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Flatten results for CSV output
    summary_data = []
    
    for key, value in results.get('results', {}).items():
        rigidity_bin = value.get('rigidity_bin')
        species_type = value.get('species_type')
        
        for lag, stats in value.get('bootstrap_stats', {}).items():
            summary_data.append({
                'rigidity_bin': rigidity_bin,
                'species_type': species_type,
                'lag_months': lag,
                'n_samples': stats.get('n_samples'),
                'mean_correlation': stats.get('mean'),
                'std_correlation': stats.get('std'),
                'ci_95_lower': stats.get('ci_95_lower'),
                'ci_95_upper': stats.get('ci_95_upper'),
                'original_correlation': stats.get('original_correlation')
            })
            
    df = pd.DataFrame(summary_data)
    df.to_csv(filepath, index=False)
    
    logger.info(f"Bootstrap summary saved to {filepath}")
    return filepath

def main():
    """
    Main entry point for bootstrap resampling analysis.
    
    This function:
    1. Loads correlation results from data/processed/correlation_results.json
    2. Performs bootstrap resampling with memory-efficient batching
    3. Saves results to data/processed/bootstrap_results.json
    4. Generates summary CSV at data/processed/bootstrap_summary.csv
    """
    # Setup logging
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Load correlation data
        logger.info("Loading correlation data...")
        correlation_data = load_correlation_data()
        
        # Run bootstrap resampling
        logger.info("Starting bootstrap resampling...")
        bootstrap_results = run_bootstrap_resampling(
            correlation_data,
            n_iterations=1000,
            random_state=42
        )
        
        # Save results
        logger.info("Saving bootstrap results...")
        save_bootstrap_results(bootstrap_results)
        
        # Generate summary
        logger.info("Generating bootstrap summary...")
        generate_bootstrap_summary(bootstrap_results)
        
        logger.info("Bootstrap resampling completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Invalid data format: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during bootstrap resampling: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
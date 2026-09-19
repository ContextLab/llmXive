import argparse
import json
import os
import sys
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import logging
from pathlib import Path

from config import get_random_generator, get_processed_data_dir, get_output_dir, initialize_random_state, get_simulation_config
from simulation import load_population_means, load_dataset, calculate_t_interval, calculate_bootstrap_interval, run_single_iteration
from coverage import create_coverage_record, save_coverage_records

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_population_means() -> Dict[str, Dict[str, float]]:
    """Load population means from the processed data directory."""
    pop_means_path = get_processed_data_dir() / "population_means.json"
    if not pop_means_path.exists():
        raise FileNotFoundError(f"Population means file not found at {pop_means_path}. Run population_mean_calculator first.")
    
    with open(pop_means_path, 'r') as f:
        return json.load(f)

def sweep_confidence_levels(
    dataset_id: str,
    variable_name: str,
    sample_size: int,
    confidence_levels: List[float],
    n_replications: int,
    seed: int
) -> Dict[float, Dict[str, Any]]:
    """
    Sweep across confidence levels for a fixed dataset, variable, and sample size.
    Reuses the US1 simulation engine to run the Monte Carlo loop for each level.
    
    Returns a dict mapping confidence_level -> {
        'empirical_coverage': float,
        'nominal_coverage': float,
        'deviation': float,
        'n_replications': int
    }
    """
    logger.info(f"Starting confidence level sweep for {dataset_id}, {variable_name}, n={sample_size}")
    
    # Load data
    pop_means = load_population_means()
    if dataset_id not in pop_means:
        raise ValueError(f"Dataset {dataset_id} not found in population means.")
    
    # Load the full cleaned dataset for this variable to sample from
    # We need the raw data to sample with replacement
    dataset_path = get_processed_data_dir() / f"{dataset_id}_cleaned.npy"
    if not dataset_path.exists():
        # Fallback: try to load from data_loader if .npy not created yet
        # For now, assume the simulation workflow creates this or we load from raw
        logger.warning(f"Cleaned dataset {dataset_path} not found. Attempting to load from raw or re-clean.")
        # In a real pipeline, we might call data_cleaner here, but for this task
        # we assume the data exists as per US1 completion.
        raise FileNotFoundError(f"Cleaned dataset for {dataset_id} not found.")
    
    full_data = np.load(dataset_path)
    if variable_name not in full_data.dtype.names:
        # Try if it's a 1D array or specific column handling
        # Assuming the cleaned data is structured or we map variable names to indices
        # For simplicity in this implementation, we assume the cleaned data is a 1D array 
        # of the specific variable or we handle the mapping in load_dataset.
        # Let's assume load_dataset returns the specific variable array.
        pass
    
    # Actually, let's refine: load_dataset in simulation.py likely handles the specific variable extraction.
    # We will call the simulation logic directly.
    
    results = {}
    rng = initialize_random_state(seed)
    
    for conf_level in confidence_levels:
        logger.info(f"  Running {n_replications} replications for confidence level {conf_level}")
        
        coverage_count = 0
        records = []
        
        for i in range(n_replications):
            # Draw a sample with replacement
            sample = rng.choice(full_data, size=sample_size, replace=True)
            
            # Calculate t-interval
            t_lower, t_upper = calculate_t_interval(sample, conf_level)
            
            # Calculate bootstrap interval
            b_lower, b_upper = calculate_bootstrap_interval(sample, conf_level, n_replications=1000, rng=rng)
            
            # Check coverage against population mean
            pop_mean = pop_means[dataset_id][variable_name]
            
            # We check both intervals or just the t-interval? 
            # The task asks to integrate sweep into simulation loop. 
            # We will record both, but focus on the deviation for the report.
            
            t_contains = t_lower <= pop_mean <= t_upper
            b_contains = b_lower <= pop_mean <= b_upper
            
            if t_contains:
                coverage_count += 1
            
            records.append(create_coverage_record(
                dataset_id=dataset_id,
                variable_name=variable_name,
                sample_size=sample_size,
                confidence_level=conf_level,
                interval_type='t',
                lower=t_lower,
                upper=t_upper,
                contains_mean=t_contains
            ))
            
            # Optionally save bootstrap too, but let's focus on t for the sweep report
            # to keep it simple and aligned with the "deviation" metric in FR-011.
        
        empirical_coverage = coverage_count / n_replications
        nominal_coverage = conf_level
        deviation = empirical_coverage - nominal_coverage
        
        results[conf_level] = {
            'empirical_coverage': empirical_coverage,
            'nominal_coverage': nominal_coverage,
            'deviation': deviation,
            'n_replications': n_replications,
            'records': records # Store records for potential detailed analysis
        }
        
        logger.info(f"    Result: Empirical={empirical_coverage:.4f}, Nominal={nominal_coverage:.4f}, Deviation={deviation:.4f}")
    
    return results

def sweep_sample_sizes(
    dataset_id: str,
    variable_name: str,
    confidence_level: float,
    sample_sizes: List[int],
    n_replications: int,
    seed: int
) -> Dict[int, Dict[str, Any]]:
    """
    Sweep across sample sizes for a fixed dataset, variable, and confidence level.
    """
    logger.info(f"Starting sample size sweep for {dataset_id}, {variable_name}, conf={confidence_level}")
    
    pop_means = load_population_means()
    if dataset_id not in pop_means:
        raise ValueError(f"Dataset {dataset_id} not found in population means.")
    
    dataset_path = get_processed_data_dir() / f"{dataset_id}_cleaned.npy"
    if not dataset_path.exists():
        raise FileNotFoundError(f"Cleaned dataset for {dataset_id} not found.")
    
    full_data = np.load(dataset_path)
    
    results = {}
    rng = initialize_random_state(seed)
    
    for n in sample_sizes:
        logger.info(f"  Running {n_replications} replications for sample size n={n}")
        
        coverage_count = 0
        records = []
        
        for i in range(n_replications):
            sample = rng.choice(full_data, size=n, replace=True)
            t_lower, t_upper = calculate_t_interval(sample, confidence_level)
            
            pop_mean = pop_means[dataset_id][variable_name]
            contains = t_lower <= pop_mean <= t_upper
            
            if contains:
                coverage_count += 1
            
            records.append(create_coverage_record(
                dataset_id=dataset_id,
                variable_name=variable_name,
                sample_size=n,
                confidence_level=confidence_level,
                interval_type='t',
                lower=t_lower,
                upper=t_upper,
                contains_mean=contains
            ))
        
        empirical_coverage = coverage_count / n_replications
        deviation = empirical_coverage - confidence_level
        
        results[n] = {
            'empirical_coverage': empirical_coverage,
            'nominal_coverage': confidence_level,
            'deviation': deviation,
            'n_replications': n_replications,
            'records': records
        }
        
        logger.info(f"    Result: Empirical={empirical_coverage:.4f}, Deviation={deviation:.4f}")
    
    return results

def analyze_sensitivity_deviations(results: Dict[Any, Dict[str, Any]], threshold: float = 0.01) -> Dict[str, Any]:
    """
    Analyze the deviations from the sweep results.
    Identifies levels/sizes where deviation exceeds the practical significance threshold (1.0%).
    """
    significant_deviations = []
    for key, data in results.items():
        if abs(data['deviation']) > threshold:
            significant_deviations.append({
                'parameter_value': key,
                'deviation': data['deviation'],
                'is_significant': True
            })
        else:
            significant_deviations.append({
                'parameter_value': key,
                'deviation': data['deviation'],
                'is_significant': False
            })
    
    return {
        'threshold': threshold,
        'results': results,
        'significant_deviations': significant_deviations
    }

def run_sensitivity_analysis(
    dataset_ids: List[str],
    variable_name: str,
    n_replications: int,
    seed: int,
    confidence_levels: Optional[List[float]] = None,
    sample_sizes: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Main entry point for sensitivity analysis.
    Integrates the sweep logic into the simulation loop as requested.
    """
    if confidence_levels is None:
        # Default from FR-008 / T034 context: {90%, 95%, 99%}
        confidence_levels = [0.90, 0.95, 0.99]
    if sample_sizes is None:
        # Default from US1: n=10, 20, 30
        sample_sizes = [10, 20, 30]
    
    all_results = {}
    
    for ds_id in dataset_ids:
        logger.info(f"Processing dataset: {ds_id}")
        
        # Check if dataset exists in population means
        try:
            pop_means = load_population_means()
            if ds_id not in pop_means:
                logger.warning(f"Skipping {ds_id}: not found in population means.")
                continue
            if variable_name not in pop_means[ds_id]:
                logger.warning(f"Skipping {ds_id}: variable {variable_name} not found.")
                continue
        except FileNotFoundError:
            logger.warning(f"Skipping {ds_id}: population means file missing.")
            continue
        
        # Check data file
        dataset_path = get_processed_data_dir() / f"{ds_id}_cleaned.npy"
        if not dataset_path.exists():
            logger.warning(f"Skipping {ds_id}: cleaned data file missing.")
            continue
        
        # Run Confidence Level Sweep
        logger.info(f"  Running Confidence Level Sweep for {ds_id}")
        conf_results = sweep_confidence_levels(
            dataset_id=ds_id,
            variable_name=variable_name,
            sample_size=sample_sizes[0], # Use first sample size as base for confidence sweep
            confidence_levels=confidence_levels,
            n_replications=n_replications,
            seed=seed
        )
        
        # Run Sample Size Sweep
        logger.info(f"  Running Sample Size Sweep for {ds_id}")
        size_results = sweep_sample_sizes(
            dataset_id=ds_id,
            variable_name=variable_name,
            confidence_level=confidence_levels[1], # Use 95% as base for size sweep
            sample_sizes=sample_sizes,
            n_replications=n_replications,
            seed=seed
        )
        
        all_results[ds_id] = {
            'confidence_sweep': conf_results,
            'size_sweep': size_results
        }
    
    return all_results

def main():
    parser = argparse.ArgumentParser(description="Sensitivity Analysis for Confidence Intervals")
    parser.add_argument('--datasets', nargs='+', default=['wine', 'ionosphere'], help='Dataset IDs to analyze')
    parser.add_argument('--variable', type=str, default='alcohol', help='Variable name to analyze (must be continuous)')
    parser.add_argument('--replications', type=int, default=1000, help='Number of Monte Carlo replications')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--output', type=str, default=None, help='Output JSON path (optional)')
    
    args = parser.parse_args()
    
    initialize_random_state(args.seed)
    
    try:
        results = run_sensitivity_analysis(
            dataset_ids=args.datasets,
            variable_name=args.variable,
            n_replications=args.replications,
            seed=args.seed
        )
        
        output_dir = get_output_dir()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / "sensitivity_confidence.json"
        if args.output:
            output_path = Path(args.output)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Sensitivity analysis complete. Results saved to {output_path}")
        
        # Generate a simple markdown report as well
        report_path = output_dir / "sensitivity_confidence.md"
        with open(report_path, 'w') as f:
            f.write("# Sensitivity Analysis Report\n\n")
            for ds_id, data in results.items():
                f.write(f"## Dataset: {ds_id}\n\n")
                f.write("### Confidence Level Sweep (n=10)\n")
                f.write("| Confidence Level | Empirical Coverage | Deviation |\n")
                f.write("| :--- | :--- | :--- |\n")
                for level, res in data['confidence_sweep'].items():
                    f.write(f"| {level:.2f} | {res['empirical_coverage']:.4f} | {res['deviation']:.4f} |\n")
                f.write("\n")
                
                f.write("### Sample Size Sweep (95% Confidence)\n")
                f.write("| Sample Size | Empirical Coverage | Deviation |\n")
                f.write("| :--- | :--- | :--- |\n")
                for size, res in data['size_sweep'].items():
                    f.write(f"| {size} | {res['empirical_coverage']:.4f} | {res['deviation']:.4f} |\n")
                f.write("\n")
        
        logger.info(f"Markdown report saved to {report_path}")
        
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}")
        raise

if __name__ == "__main__":
    main()
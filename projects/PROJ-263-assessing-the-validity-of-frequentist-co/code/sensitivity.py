"""
Sensitivity Analysis Module for Frequentist Confidence Interval Assessment.

This module implements sensitivity analysis logic to test the robustness of
coverage rates across varying confidence thresholds and sample sizes.

Dependencies:
    - code/coverage.py (for coverage calculation and aggregation)
    - code/simulation.py (for Monte Carlo simulation engine)
    - data/processed/population_means.json (operational ground truth)

Usage:
    python code/sensitivity.py --config path/to/config.yaml
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

# Add parent directory to path for imports if running as script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coverage import (
    check_coverage,
    calculate_coverage_rate,
    create_coverage_record,
    aggregate_coverage_records,
    save_coverage_records,
    load_coverage_records
)
# Note: simulation.py skeleton exists (T005) but full implementation is pending.
# This module assumes simulation functions will be available when fully implemented.
try:
    from simulation import run_simulation_batch
except ImportError:
    # Placeholder for when simulation.py is fully implemented
    def run_simulation_batch(
        dataset: np.ndarray,
        sample_sizes: List[int],
        confidence_levels: List[float],
        n_replications: int,
        seed: int
    ) -> List[Dict[str, Any]]:
        """
        Placeholder for simulation batch runner.
        This will be implemented in T025.
        """
        raise NotImplementedError(
            "run_simulation_batch is not yet implemented. "
            "Please complete T025 (Main Monte Carlo loop) before running sensitivity analysis."
        )


def load_population_means(filepath: str) -> Dict[str, float]:
    """
    Load operational ground truth (population means) from processed data.

    Args:
        filepath: Path to population_means.json

    Returns:
        Dictionary mapping dataset_id -> variable_name -> mean value
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Population means file not found: {filepath}. "
            "Run T020 to generate population means first."
        )

    with open(filepath, 'r') as f:
        return json.load(f)


def sweep_confidence_levels(
    dataset_name: str,
    dataset_array: np.ndarray,
    sample_size: int,
    confidence_levels: List[float],
    n_replications: int,
    population_mean: float,
    seed: int
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by sweeping across confidence levels.

    Args:
        dataset_name: Identifier for the dataset
        dataset_array: Cleaned numeric data array
        sample_size: Fixed sample size for this sweep
        confidence_levels: List of confidence levels to test (e.g., [0.90, 0.95, 0.99])
        n_replications: Number of Monte Carlo replications per level
        population_mean: True population mean (operational ground truth)
        seed: Random seed for reproducibility

    Returns:
        Dictionary containing sensitivity results for each confidence level
    """
    results = {
        "dataset": dataset_name,
        "sample_size": sample_size,
        "sweep_type": "confidence_level",
        "results": []
    }

    for level in confidence_levels:
        # Run simulation for this confidence level
        # Note: This calls the simulation engine which will be fully implemented in T025
        try:
            # Simulate the sampling and interval construction
            # We need to manually implement the logic here since simulation.py is skeleton
            np.random.seed(seed)
            
            coverage_count = 0
            intervals = []
            
            for _ in range(n_replications):
                # Sample with replacement (approximates super-population)
                sample = np.random.choice(dataset_array, size=sample_size, replace=True)
                
                # Calculate t-interval
                sample_mean = np.mean(sample)
                sample_std = np.std(sample, ddof=1)
                
                if sample_size > 1 and sample_std > 0:
                    # t-interval using scipy.stats.t.ppf (as per FR-005)
                    from scipy import stats
                    t_crit = stats.t.ppf((1 + level) / 2, df=sample_size - 1)
                    margin = t_crit * (sample_std / np.sqrt(sample_size))
                    lower = sample_mean - margin
                    upper = sample_mean + margin
                    
                    # Check coverage
                    contains = check_coverage(lower, upper, population_mean)
                    if contains:
                        coverage_count += 1
                    
                    intervals.append({
                        "lower": float(lower),
                        "upper": float(upper),
                        "contains_mean": bool(contains)
                    })
                else:
                    # Degenerate case: skip or handle as non-coverage
                    pass
            
            coverage_rate = coverage_count / n_replications
            deviation = abs(coverage_rate - level)
            
            results["results"].append({
                "confidence_level": level,
                "empirical_coverage": float(coverage_rate),
                "nominal_coverage": level,
                "deviation": float(deviation),
                "is_practically_significant": deviation > 0.01,  # FR-011 threshold
                "n_replications": n_replications
            })
            
        except Exception as e:
            results["results"].append({
                "confidence_level": level,
                "error": str(e),
                "empirical_coverage": None,
                "nominal_coverage": level,
                "deviation": None,
                "is_practically_significant": None
            })

    return results


def sweep_sample_sizes(
    dataset_name: str,
    dataset_array: np.ndarray,
    confidence_level: float,
    sample_sizes: List[int],
    n_replications: int,
    population_mean: float,
    seed: int
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by sweeping across sample sizes.

    Args:
        dataset_name: Identifier for the dataset
        dataset_array: Cleaned numeric data array
        confidence_level: Fixed confidence level for this sweep
        sample_sizes: List of sample sizes to test (e.g., [10, 20, 30])
        n_replications: Number of Monte Carlo replications per size
        population_mean: True population mean (operational ground truth)
        seed: Random seed for reproducibility

    Returns:
        Dictionary containing sensitivity results for each sample size
    """
    results = {
        "dataset": dataset_name,
        "confidence_level": confidence_level,
        "sweep_type": "sample_size",
        "results": []
    }

    for n in sample_sizes:
        try:
            np.random.seed(seed + n)  # Different seed per sample size
            
            coverage_count = 0
            
            for _ in range(n_replications):
                # Sample with replacement
                sample = np.random.choice(dataset_array, size=n, replace=True)
                
                # Calculate t-interval
                sample_mean = np.mean(sample)
                sample_std = np.std(sample, ddof=1)
                
                if n > 1 and sample_std > 0:
                    from scipy import stats
                    t_crit = stats.t.ppf((1 + confidence_level) / 2, df=n - 1)
                    margin = t_crit * (sample_std / np.sqrt(n))
                    lower = sample_mean - margin
                    upper = sample_mean + margin
                    
                    contains = check_coverage(lower, upper, population_mean)
                    if contains:
                        coverage_count += 1
                else:
                    pass
            
            coverage_rate = coverage_count / n_replications
            deviation = abs(coverage_rate - confidence_level)
            
            results["results"].append({
                "sample_size": n,
                "empirical_coverage": float(coverage_rate),
                "nominal_coverage": confidence_level,
                "deviation": float(deviation),
                "is_practically_significant": deviation > 0.01,  # FR-011 threshold
                "n_replications": n_replications
            })
            
        except Exception as e:
            results["results"].append({
                "sample_size": n,
                "error": str(e),
                "empirical_coverage": None,
                "nominal_coverage": confidence_level,
                "deviation": None,
                "is_practically_significant": None
            })

    return results


def analyze_sensitivity_deviations(
    sensitivity_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze sensitivity results to identify patterns and instability.

    Args:
        sensitivity_results: Output from sweep_confidence_levels or sweep_sample_sizes

    Returns:
        Analysis summary with key findings
    """
    analysis = {
        "dataset": sensitivity_results.get("dataset"),
        "sweep_type": sensitivity_results.get("sweep_type"),
        "findings": [],
        "instability_detected": False,
        "max_deviation": 0.0,
        "practically_significant_count": 0
    }

    for result in sensitivity_results.get("results", []):
        if result.get("error"):
            continue

        deviation = result.get("deviation", 0)
        if deviation > analysis["max_deviation"]:
            analysis["max_deviation"] = deviation

        if result.get("is_practically_significant"):
            analysis["practically_significant_count"] += 1
            analysis["findings"].append(
                f"Practically significant deviation ({deviation:.4f}) at "
                f"{result.get('confidence_level') if sensitivity_results.get('sweep_type') == 'confidence_level' else 'n=' + str(result.get('sample_size'))}"
            )

    if analysis["practically_significant_count"] > 0:
        analysis["instability_detected"] = True

    return analysis


def run_sensitivity_analysis(
    config_path: str,
    output_dir: str = "outputs"
) -> None:
    """
    Main entry point for running sensitivity analysis.

    Args:
        config_path: Path to configuration file specifying datasets and parameters
        output_dir: Directory for output files
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = json.load(f)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Load population means
    pop_means_path = config.get("population_means_path", "data/processed/population_means.json")
    population_means = load_population_means(pop_means_path)

    # Load dataset (simulated for now, will be replaced with real data loader in T016-T018)
    # This is a placeholder until T016 (UCI downloader) and T017 (data loader) are complete
    dataset_name = config.get("dataset", "placeholder")
    dataset_path = config.get("dataset_path")
    
    if dataset_path and os.path.exists(dataset_path):
        # Load real data if available
        import pandas as pd
        df = pd.read_csv(dataset_path)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            dataset_array = df[numeric_cols[0]].values
        else:
            raise ValueError(f"No numeric columns found in {dataset_path}")
    else:
        # Placeholder data for skeleton functionality
        # In real execution, this will be replaced by T016-T018 data loading
        print(f"Warning: Dataset not found at {dataset_path}. Using placeholder data.")
        dataset_array = np.random.normal(loc=0, scale=1, size=1000)

    # Extract parameters from config
    sample_sizes = config.get("sample_sizes", [10, 20, 30])
    confidence_levels = config.get("confidence_levels", [0.90, 0.95, 0.99])
    n_replications = config.get("n_replications", 1000)
    seed = config.get("seed", 42)
    variable_name = config.get("variable", 0)  # Index or name of variable

    # Get population mean for this variable
    if dataset_name in population_means:
        if isinstance(population_means[dataset_name], dict):
            pop_mean = population_means[dataset_name].get(str(variable_name), 0.0)
        else:
            pop_mean = float(population_means[dataset_name])
    else:
        # Calculate from full dataset if not pre-computed (fallback)
        pop_mean = float(np.mean(dataset_array))
        print(f"Warning: Population mean not found for {dataset_name}. Calculated from data: {pop_mean}")

    # Run sensitivity sweeps
    all_results = []

    # Confidence level sweep
    if config.get("sweep_confidence", True):
        print(f"Running confidence level sweep for {dataset_name}...")
        conf_results = sweep_confidence_levels(
            dataset_name=dataset_name,
            dataset_array=dataset_array,
            sample_size=config.get("fixed_sample_size", sample_sizes[0]),
            confidence_levels=confidence_levels,
            n_replications=n_replications,
            population_mean=pop_mean,
            seed=seed
        )
        all_results.append(conf_results)
        
        # Analyze confidence sweep
        conf_analysis = analyze_sensitivity_deviations(conf_results)
        conf_results["analysis"] = conf_analysis

    # Sample size sweep
    if config.get("sweep_sample_size", True):
        print(f"Running sample size sweep for {dataset_name}...")
        size_results = sweep_sample_sizes(
            dataset_name=dataset_name,
            dataset_array=dataset_array,
            confidence_level=config.get("fixed_confidence_level", 0.95),
            sample_sizes=sample_sizes,
            n_replications=n_replications,
            population_mean=pop_mean,
            seed=seed
        )
        all_results.append(size_results)
        
        # Analyze size sweep
        size_analysis = analyze_sensitivity_deviations(size_results)
        size_results["analysis"] = size_analysis

    # Save results
    timestamp = config.get("timestamp", "unknown")
    output_file = os.path.join(
        output_dir, 
        f"sensitivity_analysis_{dataset_name}_{timestamp}.json"
    )
    
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"Sensitivity analysis results saved to: {output_file}")


def main():
    """Command-line interface for sensitivity analysis."""
    parser = argparse.ArgumentParser(
        description="Run sensitivity analysis for confidence interval coverage"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/sensitivity_config.json",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="outputs",
        help="Output directory for results"
    )
    
    args = parser.parse_args()
    
    try:
        run_sensitivity_analysis(args.config, args.output)
    except Exception as e:
        print(f"Error running sensitivity analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

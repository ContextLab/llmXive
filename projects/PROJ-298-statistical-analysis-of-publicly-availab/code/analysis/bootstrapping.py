"""
Bootstrapping module for calculating confidence intervals on Theil-Sen slopes.

Implements non-parametric bootstrapping to estimate 95% confidence intervals
for trend slopes calculated via Theil-Sen estimator.
"""
import os
import json
import math
import random
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

# Import from sibling modules as per API surface
from analysis.trends import theil_sen_slope, analyze_trends
from utils.state_manager import calculate_sha256, load_state, save_state, update_artifact_checksums


def bootstrap_theil_sen(
    monthly_frequencies: Dict[str, List[float]],
    timestamps: List[str],
    n_iterations: int = 1000,
    confidence_level: float = 0.95,
    random_seed: Optional[int] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate 95% confidence intervals for Theil-Sen slopes using bootstrapping.
    
    Args:
        monthly_frequencies: Dict mapping tag names to lists of monthly frequency values.
        timestamps: List of timestamp strings corresponding to the frequency data.
        n_iterations: Number of bootstrap iterations to perform.
        confidence_level: Confidence level for the interval (default 0.95).
        random_seed: Random seed for reproducibility.
        
    Returns:
        Dict mapping tag names to their confidence interval results containing:
            - point_estimate: The original Theil-Sen slope
            - ci_lower: Lower bound of the confidence interval
            - ci_upper: Upper bound of the confidence interval
            - bootstrap_mean: Mean of bootstrap slope distribution
            - bootstrap_std: Standard deviation of bootstrap slope distribution
    """
    if random_seed is not None:
        random.seed(random_seed)
        
    results = {}
    n_samples = len(timestamps)
    
    if n_samples < 2:
        raise ValueError("Need at least 2 data points for bootstrapping")
        
    for tag, frequencies in monthly_frequencies.items():
        if len(frequencies) != n_samples:
            raise ValueError(f"Frequency list length mismatch for tag {tag}")
            
        # Calculate original point estimate
        original_slope = theil_sen_slope(timestamps, frequencies)
        
        # Perform bootstrapping
        bootstrap_slopes = []
        for _ in range(n_iterations):
            # Resample with replacement
            indices = [random.randint(0, n_samples - 1) for _ in range(n_samples)]
            resampled_freqs = [frequencies[i] for i in indices]
            resampled_timestamps = [timestamps[i] for i in indices]
            
            # Calculate slope on resampled data
            try:
                slope = theil_sen_slope(resampled_timestamps, resampled_freqs)
                bootstrap_slopes.append(slope)
            except (ValueError, ZeroDivisionError):
                # Skip if slope calculation fails on resampled data
                continue
                
        if len(bootstrap_slopes) < 10:
            # Not enough valid bootstrap samples
            results[tag] = {
                "point_estimate": original_slope,
                "ci_lower": None,
                "ci_upper": None,
                "bootstrap_mean": None,
                "bootstrap_std": None,
                "bootstrap_samples": len(bootstrap_slopes),
                "status": "insufficient_bootstrap_samples"
            }
            continue
            
        # Calculate confidence interval
        alpha = 1 - confidence_level
        lower_idx = int(math.floor(alpha / 2 * len(bootstrap_slopes)))
        upper_idx = int(math.ceil((1 - alpha / 2) * len(bootstrap_slopes)))
        
        bootstrap_slopes.sort()
        ci_lower = bootstrap_slopes[lower_idx]
        ci_upper = bootstrap_slopes[upper_idx]
        bootstrap_mean = sum(bootstrap_slopes) / len(bootstrap_slopes)
        bootstrap_std = math.sqrt(sum((x - bootstrap_mean) ** 2 for x in bootstrap_slopes) / len(bootstrap_slopes))
        
        results[tag] = {
            "point_estimate": original_slope,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "bootstrap_mean": bootstrap_mean,
            "bootstrap_std": bootstrap_std,
            "bootstrap_samples": len(bootstrap_slopes),
            "status": "success"
        }
        
    return results


def load_processed_data(
    data_dir: Path,
    processed_filename: str = "processed_data.json"
) -> Tuple[Dict[str, List[float]], List[str]]:
    """
    Load processed monthly frequency data from JSON file.
    
    Args:
        data_dir: Path to the data directory.
        processed_filename: Name of the processed data file.
        
    Returns:
        Tuple of (monthly_frequencies dict, timestamps list)
    """
    file_path = data_dir / processed_filename
    if not file_path.exists():
        raise FileNotFoundError(f"Processed data file not found: {file_path}")
        
    with open(file_path, 'r') as f:
        data = json.load(f)
        
    monthly_frequencies = data.get("monthly_frequencies", {})
    timestamps = data.get("timestamps", [])
    
    return monthly_frequencies, timestamps


def save_confidence_intervals(
    results: Dict[str, Dict[str, Any]],
    output_dir: Path,
    output_filename: str = "confidence_interval.json"
) -> Path:
    """
    Save confidence interval results to JSON file.
    
    Args:
        results: Dict of confidence interval results.
        output_dir: Path to output directory.
        output_filename: Name of output file.
        
    Returns:
        Path to the saved file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_filename
    
    output_data = {
        "metadata": {
            "description": "95% confidence intervals for Theil-Sen trend slopes",
            "method": "bootstrapping",
            "confidence_level": 0.95,
            "generated_by": "code/analysis/bootstrapping.py"
        },
        "results": results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
        
    return output_path


def run_bootstrapping_analysis(
    data_dir: Path,
    output_dir: Path,
    n_iterations: int = 1000,
    random_seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run complete bootstrapping analysis pipeline.
    
    Args:
        data_dir: Path to data directory containing processed data.
        output_dir: Path to output directory for results.
        n_iterations: Number of bootstrap iterations.
        random_seed: Random seed for reproducibility.
        
    Returns:
        Summary dictionary of the analysis.
    """
    # Load processed data
    monthly_frequencies, timestamps = load_processed_data(data_dir)
    
    # Filter out tags with insufficient data
    valid_tags = {
        tag: freqs for tag, freqs in monthly_frequencies.items()
        if len(freqs) >= 12  # FR-003: minimum 12 months
    }
    
    if not valid_tags:
        raise ValueError("No valid tags with sufficient data for bootstrapping")
        
    # Run bootstrapping
    results = bootstrap_theil_sen(
        valid_tags,
        timestamps,
        n_iterations=n_iterations,
        random_seed=random_seed
    )
    
    # Save results
    output_path = save_confidence_intervals(results, output_dir)
    
    # Calculate summary statistics
    successful = sum(1 for r in results.values() if r["status"] == "success")
    total = len(results)
    
    summary = {
        "total_tags_analyzed": total,
        "successful_calculations": successful,
        "failed_calculations": total - successful,
        "output_file": str(output_path),
        "iterations": n_iterations,
        "confidence_level": 0.95
    }
    
    return summary


def main():
    """Main entry point for bootstrapping analysis."""
    # Determine paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    output_dir = project_root / "data" / "processed"
    
    print(f"Starting bootstrapping analysis...")
    print(f"Data directory: {data_dir}")
    print(f"Output directory: {output_dir}")
    
    try:
        summary = run_bootstrapping_analysis(
            data_dir=data_dir,
            output_dir=output_dir,
            n_iterations=1000,
            random_seed=42
        )
        
        print(f"\nBootstrapping analysis completed successfully!")
        print(f"Total tags analyzed: {summary['total_tags_analyzed']}")
        print(f"Successful calculations: {summary['successful_calculations']}")
        print(f"Output file: {summary['output_file']}")
        
        # Update state file with new artifact checksum
        state_file = project_root / "state" / "projects" / "PROJ-298-statistical-analysis-of-publicly-availab.yaml"
        if state_file.exists():
            update_artifact_checksums(state_file, [summary['output_file']])
            print(f"State file updated with new checksum.")
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure processed data exists in data/processed/processed_data.json")
        raise
    except Exception as e:
        print(f"Error during bootstrapping analysis: {e}")
        raise


if __name__ == "__main__":
    main()

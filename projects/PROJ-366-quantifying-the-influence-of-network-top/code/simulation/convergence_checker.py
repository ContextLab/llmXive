"""
Convergence detection logic for Green-Kubo thermal conductivity simulations.

This module implements the convergence check based on the relative change
in heat current autocorrelation (HCACF) in the final segment of the simulation.

Convergence criterion: relative change < 1% in the final segment.
"""

import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

# Import from existing API surface
from config import get_config, get_simulation_config

logger = logging.getLogger(__name__)

# Default convergence threshold (1%)
DEFAULT_CONVERGENCE_THRESHOLD = 0.01
DEFAULT_FINAL_SEGMENT_FRACTION = 0.2  # Use last 20% of data for convergence check


def calculate_hcacf_relative_change(hcacf_data: np.ndarray, 
                                   segment_fraction: float = DEFAULT_FINAL_SEGMENT_FRACTION) -> Tuple[float, float, float]:
    """
    Calculate the relative change in HCACF for the final segment of the data.
    
    Args:
        hcacf_data: Array of heat current autocorrelation values.
        segment_fraction: Fraction of the data to use for the final segment check.
        
    Returns:
        Tuple of (relative_change, mean_first_half, mean_second_half)
    """
    if len(hcacf_data) < 10:
        logger.warning("HCACF data too short (<10 points) for convergence check.")
        return float('inf'), 0.0, 0.0
    
    n_points = len(hcacf_data)
    segment_size = max(1, int(n_points * segment_fraction))
    
    # Split the final segment into two halves
    final_segment_start = n_points - segment_size
    first_half_end = final_segment_start + (segment_size // 2)
    second_half_start = first_half_end
    
    first_half = hcacf_data[final_segment_start:first_half_end]
    second_half = hcacf_data[second_half_start:n_points]
    
    # Calculate means (using absolute values to handle sign changes)
    mean_first = np.mean(np.abs(first_half))
    mean_second = np.mean(np.abs(second_half))
    
    # Avoid division by zero
    if mean_first < 1e-10:
        relative_change = float('inf') if mean_second > 1e-10 else 0.0
    else:
        relative_change = abs(mean_second - mean_first) / mean_first
    
    return relative_change, mean_first, mean_second


def check_convergence(hcacf_data: np.ndarray, 
                     threshold: float = DEFAULT_CONVERGENCE_THRESHOLD,
                     segment_fraction: float = DEFAULT_FINAL_SEGMENT_FRACTION) -> Dict[str, Any]:
    """
    Check if the HCACF has converged based on relative change in the final segment.
    
    Args:
        hcacf_data: Array of heat current autocorrelation values.
        threshold: Maximum allowed relative change for convergence (default 1%).
        segment_fraction: Fraction of data to use for final segment check.
        
    Returns:
        Dictionary with convergence status and metrics.
    """
    relative_change, mean_first, mean_second = calculate_hcacf_relative_change(
        hcacf_data, segment_fraction
    )
    
    is_converged = relative_change < threshold
    
    return {
        "converged": is_converged,
        "relative_change": float(relative_change),
        "threshold": threshold,
        "mean_first_half": float(mean_first),
        "mean_second_half": float(mean_second),
        "segment_fraction": segment_fraction,
        "total_points": len(hcacf_data),
        "segment_points": int(len(hcacf_data) * segment_fraction)
    }


def update_thermal_sample_metadata(sample_data: Dict[str, Any], 
                                  convergence_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a ThermalSample dictionary with convergence metadata.
    
    Args:
        sample_data: The ThermalSample dictionary to update.
        convergence_result: Dictionary containing convergence check results.
        
    Returns:
        Updated sample_data dictionary with convergence information.
    """
    if "metadata" not in sample_data:
        sample_data["metadata"] = {}
    
    sample_data["metadata"]["convergence"] = {
        "converged": convergence_result["converged"],
        "relative_change": convergence_result["relative_change"],
        "threshold": convergence_result["threshold"],
        "check_timestamp": None,  # Will be set by caller if needed
        "details": {
            "mean_first_half": convergence_result["mean_first_half"],
            "mean_second_half": convergence_result["mean_second_half"],
            "segment_fraction": convergence_result["segment_fraction"],
            "total_points": convergence_result["total_points"],
            "segment_points": convergence_result["segment_points"]
        }
    }
    
    # Also set top-level converged flag for easy access
    sample_data["converged"] = convergence_result["converged"]
    
    return sample_data


def process_convergence_for_sample(sample_path: Path, 
                                  output_dir: Path,
                                  threshold: Optional[float] = None) -> Dict[str, Any]:
    """
    Process a single ThermalSample file to check convergence and update metadata.
    
    Args:
        sample_path: Path to the pickle file containing the ThermalSample.
        output_dir: Directory to save the updated sample file.
        threshold: Optional custom convergence threshold.
        
    Returns:
        Dictionary with the update result.
    """
    config = get_simulation_config()
    if threshold is None:
        threshold = config.get("convergence_threshold", DEFAULT_CONVERGENCE_THRESHOLD)
    
    try:
        # Load the sample
        with open(sample_path, 'rb') as f:
            sample_data = pickle.load(f)
        
        # Extract HCACF data (assuming it's stored in the sample)
        hcacf_data = sample_data.get("hcacf_data")
        if hcacf_data is None:
            logger.warning(f"No HCACF data found in {sample_path}, skipping convergence check.")
            return {
                "sample_id": sample_data.get("sample_id", "unknown"),
                "status": "skipped",
                "reason": "No HCACF data found"
            }
        
        # Convert to numpy array if needed
        if not isinstance(hcac_data, np.ndarray):
            hcacf_data = np.array(hcac_data)
        
        # Check convergence
        convergence_result = check_convergence(hcac_data, threshold)
        
        # Update sample metadata
        updated_sample = update_thermal_sample_metadata(sample_data, convergence_result)
        
        # Save updated sample
        output_path = output_dir / sample_path.name
        with open(output_path, 'wb') as f:
            pickle.dump(updated_sample, f)
        
        logger.info(f"Convergence check for {sample_path.name}: "
                   f"converged={convergence_result['converged']}, "
                   f"relative_change={convergence_result['relative_change']:.4f}")
        
        return {
            "sample_id": sample_data.get("sample_id", "unknown"),
            "status": "completed",
            "converged": convergence_result["converged"],
            "relative_change": convergence_result["relative_change"],
            "output_path": str(output_path)
        }
        
    except Exception as e:
        logger.error(f"Error processing convergence for {sample_path}: {str(e)}")
        return {
            "sample_id": sample_path.stem,
            "status": "error",
            "error": str(e)
        }


def main():
    """
    Main entry point for convergence checking.
    
    Processes all ThermalSample files in the conductivities directory,
    checks convergence, and updates metadata.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Check convergence of thermal conductivity samples")
    parser.add_argument("--input-dir", type=str, default=None,
                      help="Input directory containing sample pickle files")
    parser.add_argument("--output-dir", type=str, default=None,
                      help="Output directory for updated sample files")
    parser.add_argument("--threshold", type=float, default=None,
                      help="Convergence threshold (default from config)")
    parser.add_argument("--sample-file", type=str, default=None,
                      help="Process a single sample file")
    
    args = parser.parse_args()
    
    config = get_config()
    paths = get_paths()
    
    input_dir = Path(args.input_dir) if args.input_dir else paths["processed_conductivities"]
    output_dir = Path(args.output_dir) if args.output_dir else input_dir
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    if args.sample_file:
        # Process single file
        sample_path = Path(args.sample_file)
        if not sample_path.exists():
            logger.error(f"Sample file not found: {sample_path}")
            return 1
        
        result = process_convergence_for_sample(sample_path, output_dir, args.threshold)
        results.append(result)
    else:
        # Process all files in directory
        sample_files = list(input_dir.glob("*.pkl")) + list(input_dir.glob("*.pickle"))
        
        if not sample_files:
            logger.warning(f"No sample files found in {input_dir}")
            return 0
        
        logger.info(f"Found {len(sample_files)} sample files to process")
        
        for sample_file in sample_files:
            result = process_convergence_for_sample(sample_file, output_dir, args.threshold)
            results.append(result)
    
    # Write summary report
    report_path = output_dir / "convergence_report.json"
    with open(report_path, 'w') as f:
        json.dump({
            "total_samples": len(results),
            "converged": sum(1 for r in results if r.get("converged") is True),
            "not_converged": sum(1 for r in results if r.get("converged") is False),
            "skipped": sum(1 for r in results if r.get("status") == "skipped"),
            "errors": sum(1 for r in results if r.get("status") == "error"),
            "results": results
        }, f, indent=2)
    
    logger.info(f"Convergence report saved to {report_path}")
    
    # Return non-zero if any samples failed convergence
    failed_count = sum(1 for r in results if r.get("converged") is False)
    return 1 if failed_count > 0 else 0


if __name__ == "__main__":
    exit(main())

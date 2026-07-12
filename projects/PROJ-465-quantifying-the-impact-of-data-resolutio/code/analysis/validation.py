"""
Validation module for injected data scenarios.

Implements US-2, Scenario 3: Validate that for injected data scenarios,
the calculated bias is effectively zero (< 1e-6).
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np

from code.config import DATA_DIR, RESULTS_DIR
from code.analysis.metrics import load_posterior_from_file, calculate_bias
from code.utils.logging_config import get_derivation_logger

logger = get_derivation_logger(__name__)


def validate_injection_bias(
    posterior_path: Path,
    injection_truth: Dict[str, float],
    tolerance: float = 1e-6
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that bias for injected data is effectively zero.
    
    This function loads a posterior distribution generated from injected data,
    calculates the bias against the known injection truth, and verifies that
    the bias is below the specified tolerance threshold.
    
    Args:
        posterior_path: Path to the posterior distribution file (HDF5 or JSON)
        injection_truth: Dictionary mapping parameter names to their true injected values
        tolerance: Maximum acceptable bias value (default: 1e-6)
        
    Returns:
        Tuple of (is_valid, details_dict) where:
            - is_valid: True if all biases are < tolerance
            - details_dict: Contains bias values, pass/fail status per parameter,
                            and overall validation result
    """
    if not posterior_path.exists():
        error_msg = f"Posterior file not found: {posterior_path}"
        logger.error(error_msg)
        return False, {
            "error": error_msg,
            "is_valid": False,
            "posterior_path": str(posterior_path)
        }
    
    try:
        posterior_data = load_posterior_from_file(posterior_path)
    except Exception as e:
        error_msg = f"Failed to load posterior from {posterior_path}: {str(e)}"
        logger.error(error_msg)
        return False, {
            "error": error_msg,
            "is_valid": False,
            "posterior_path": str(posterior_path)
        }
    
    # Extract posterior samples for comparison
    samples = posterior_data.get("samples", {})
    if not samples:
        error_msg = "No samples found in posterior data"
        logger.error(error_msg)
        return False, {
            "error": error_msg,
            "is_valid": False,
            "posterior_path": str(posterior_path)
        }
    
    # Calculate bias for each parameter present in injection truth
    bias_results = {}
    all_pass = True
    
    for param_name, true_value in injection_truth.items():
        if param_name not in samples:
            logger.warning(f"Parameter '{param_name}' not found in posterior samples")
            bias_results[param_name] = {
                "true_value": true_value,
                "bias": None,
                "passed": False,
                "reason": "parameter_missing"
            }
            all_pass = False
            continue
        
        # Calculate posterior mean for the parameter
        param_samples = np.array(samples[param_name])
        posterior_mean = np.mean(param_samples)
        
        # Calculate absolute bias
        bias = abs(posterior_mean - true_value)
        
        # Check against tolerance
        passed = bias < tolerance
        
        bias_results[param_name] = {
            "true_value": true_value,
            "posterior_mean": posterior_mean,
            "bias": bias,
            "tolerance": tolerance,
            "passed": passed
        }
        
        if not passed:
            all_pass = False
            logger.warning(
                f"Bias for '{param_name}' ({bias:.2e}) exceeds tolerance ({tolerance})"
            )
        else:
            logger.info(
                f"Bias for '{param_name}' ({bias:.2e}) within tolerance ({tolerance})"
            )
    
    result = {
        "is_valid": all_pass,
        "bias_results": bias_results,
        "posterior_path": str(posterior_path),
        "tolerance": tolerance
    }
    
    return all_pass, result


def run_injection_validation(
    event_id: str,
    resolution_config: str,
    tolerance: float = 1e-6
) -> Dict[str, Any]:
    """
    Run full injection validation for a specific event and resolution.
    
    This function locates the posterior file for a given event and resolution,
    retrieves the injection truth values (assumed to be stored in metadata or
    a separate truth file), and performs the bias validation.
    
    Args:
        event_id: Identifier for the gravitational wave event (e.g., 'GW150914')
        resolution_config: Resolution configuration string (e.g., '4096Hz_16bit')
        tolerance: Maximum acceptable bias value
        
    Returns:
        Dictionary containing validation results and metadata
    """
    logger.info(f"Running injection validation for {event_id} at {resolution_config}")
    
    # Construct expected posterior path
    posterior_dir = RESULTS_DIR / "posteriors" / event_id
    posterior_file = posterior_dir / f"{event_id}_{resolution_config}_posterior.hdf5"
    
    # For injected data, we assume truth values are stored in a companion file
    # or in the posterior metadata. Attempt to load from metadata first.
    try:
        posterior_data = load_posterior_from_file(posterior_file)
        injection_truth = posterior_data.get("injection_truth", {})
        
        if not injection_truth:
            # Try to load from companion truth file
            truth_file = posterior_dir / f"{event_id}_{resolution_config}_truth.json"
            if truth_file.exists():
                import json
                with open(truth_file, 'r') as f:
                    injection_truth = json.load(f)
            else:
                raise ValueError("No injection truth found for validation")
        
    except FileNotFoundError:
        error_msg = f"Posterior file not found: {posterior_file}"
        logger.error(error_msg)
        return {
            "status": "failed",
            "error": error_msg,
            "event_id": event_id,
            "resolution_config": resolution_config
        }
    except Exception as e:
        error_msg = f"Failed to retrieve injection truth: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "failed",
            "error": error_msg,
            "event_id": event_id,
            "resolution_config": resolution_config
        }
    
    # Perform validation
    is_valid, details = validate_injection_bias(
        posterior_file, 
        injection_truth, 
        tolerance
    )
    
    result = {
        "status": "passed" if is_valid else "failed",
        "event_id": event_id,
        "resolution_config": resolution_config,
        "tolerance": tolerance,
        "details": details
    }
    
    logger.info(
        f"Validation {result['status'].upper()} for {event_id} at {resolution_config}"
    )
    
    return result


def main():
    """
    Main entry point for injection validation script.
    
    This function runs validation on all available injected event post
      eriors and outputs a summary report.
    """
    logger.info("Starting injection validation for all events")
    
    # Define test cases - these would normally be discovered dynamically
    test_cases = [
        # Example: event_id, resolution_config
        ("GW150914", "4096Hz_32bit"),
        ("GW150914", "2048Hz_32bit"),
        ("GW150914", "1024Hz_32bit"),
        # Add more test cases as needed
    ]
    
    results = []
    passed_count = 0
    failed_count = 0
    error_count = 0
    
    for event_id, resolution_config in test_cases:
        result = run_injection_validation(event_id, resolution_config)
        results.append(result)
        
        if result["status"] == "passed":
            passed_count += 1
        elif result["status"] == "failed":
            failed_count += 1
        else:
            error_count += 1
    
    # Output summary
    summary = {
        "total_tests": len(test_cases),
        "passed": passed_count,
        "failed": failed_count,
        "errors": error_count,
        "results": results
    }
    
    logger.info(f"Validation complete: {passed_count} passed, {failed_count} failed, {error_count} errors")
    
    # Save results to file
    output_path = RESULTS_DIR / "metrics" / "injection_validation_summary.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Summary saved to {output_path}")
    
    return summary


if __name__ == "__main__":
    main()
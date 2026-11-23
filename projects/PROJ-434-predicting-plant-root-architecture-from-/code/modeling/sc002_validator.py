"""
T023: Execute/Validate SC-002 compliance.

Reads artifacts/permutation_distributions.json, calculates p-values,
enforces SC-002 (ΔR² ≥ 0.05 AND p < 0.05), and writes the status to
artifacts/sc002_status.json.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np

# Add project root to path to allow imports if run as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.exceptions import DataQualityError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_permutation_distributions(file_path: Path) -> Dict[str, Any]:
    """
    Load the permutation distributions JSON file.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        Dictionary containing the permutation distributions.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or invalid JSON.
        DataQualityError: If the data is insufficient or empty.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Permutation distributions file not found: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in permutation distributions file: {e}")
    
    if not data:
        raise DataQualityError("Permutation distributions file is empty.")
    
    # Validate structure expected from T022
    # Expected keys: 'model_a', 'model_b', etc., containing lists of R2 scores
    # Or a structure like: {'distributions': {'model_a': [...], 'model_b': [...]}}
    # We assume the structure from T022: {'model_a': [...], 'model_b': [...]} or similar
    # Let's be flexible but ensure we have data for at least one model
    
    has_data = False
    for key, value in data.items():
        if isinstance(value, list) and len(value) > 0:
            has_data = True
            break
        
        # Check nested structure if applicable
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, list) and len(sub_value) > 0:
                    has_data = True
                    break
    
    if not has_data:
        raise DataQualityError(
            "Permutation distributions file contains no valid data or insufficient iterations."
        )
    
    return data

def calculate_p_value(observed_score: float, null_distribution: List[float]) -> float:
    """
    Calculate the one-sided p-value for the observed score against the null distribution.
    
    p-value = (count(null_scores >= observed_score) + 1) / (N + 1)
    This is a standard permutation test p-value calculation.
    
    Args:
        observed_score: The observed R2 score.
        null_distribution: List of R2 scores from the null distribution (permuted).
        
    Returns:
        The calculated p-value.
    """
    if not null_distribution:
        raise ValueError("Null distribution is empty.")
    
    null_array = np.array(null_distribution)
    # Count how many permuted scores are greater than or equal to the observed score
    # (Assuming higher R2 is better, which is typical for R2)
    count_extreme = np.sum(null_array >= observed_score)
    n = len(null_array)
    
    # P-value calculation with continuity correction
    p_value = (count_extreme + 1) / (n + 1)
    return float(p_value)

def calculate_delta_r2(permuted_r2: float, baseline_r2: float) -> float:
    """
    Calculate the delta R2.
    
    Args:
        permuted_r2: The R2 score from the permuted model (or observed if comparing to baseline).
        baseline_r2: The baseline R2 score (e.g., mean prediction model).
        
    Returns:
        The delta R2 (observed - baseline).
    """
    return float(permuted_r2 - baseline_r2)

def validate_sc002(
    observed_r2: float,
    null_distribution: List[float],
    baseline_r2: float,
    delta_threshold: float = 0.05,
    p_threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Validate SC-002 compliance.
    
    SC-002 requires: ΔR² ≥ 0.05 AND p < 0.05
    
    Args:
        observed_r2: The observed R2 score from the real model.
        null_distribution: The list of R2 scores from the permutation test.
        baseline_r2: The baseline R2 score (mean prediction model).
        delta_threshold: Minimum required ΔR².
        p_threshold: Maximum allowed p-value.
        
    Returns:
        Dictionary with pass/fail status, reason, delta_r2, and p_value.
    """
    # Calculate delta R2
    delta_r2 = calculate_delta_r2(observed_r2, baseline_r2)
    
    # Calculate p-value
    p_value = calculate_p_value(observed_r2, null_distribution)
    
    # Check conditions
    passes_delta = delta_r2 >= delta_threshold
    passes_p = p_value < p_threshold
    
    passed = passes_delta and passes_p
    
    reason_parts = []
    if not passes_delta:
        reason_parts.append(f"ΔR² ({delta_r2:.4f}) < {delta_threshold}")
    if not passes_p:
        reason_parts.append(f"p-value ({p_value:.4f}) >= {p_threshold}")
    
    if passed:
        reason = "SC-002 criteria met: ΔR² >= 0.05 and p < 0.05"
    else:
        reason = "; ".join(reason_parts)
    
    return {
        "pass": passed,
        "reason": reason,
        "delta_r2": delta_r2,
        "p_value": p_value
    }

def main():
    """
    Main entry point for T023.
    """
    # Define paths
    artifacts_dir = project_root / "artifacts"
    input_file = artifacts_dir / "permutation_distributions.json"
    baseline_file = artifacts_dir / "baseline_metrics.json"
    output_file = artifacts_dir / "sc002_status.json"
    
    # Ensure artifacts directory exists
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading permutation distributions from {input_file}")
    try:
        perm_data = load_permutation_distributions(input_file)
    except (FileNotFoundError, ValueError, DataQualityError) as e:
        logger.error(f"Failed to load permutation distributions: {e}")
        # Write a failure status
        status = {
            "pass": False,
            "reason": f"Failed to load permutation data: {str(e)}",
            "delta_r2": 0.0,
            "p_value": 1.0
        }
        with open(output_file, 'w') as f:
            json.dump(status, f, indent=2)
        return
    
    logger.info(f"Loading baseline metrics from {baseline_file}")
    try:
        with open(baseline_file, 'r') as f:
            baseline_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Baseline metrics file not found: {baseline_file}")
        status = {
            "pass": False,
            "reason": f"Baseline metrics file not found: {baseline_file}",
            "delta_r2": 0.0,
            "p_value": 1.0
        }
        with open(output_file, 'w') as f:
            json.dump(status, f, indent=2)
        return
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in baseline metrics file: {e}")
        status = {
            "pass": False,
            "reason": f"Invalid JSON in baseline metrics: {e}",
            "delta_r2": 0.0,
            "p_value": 1.0
        }
        with open(output_file, 'w') as f:
            json.dump(status, f, indent=2)
        return
    
    # Extract baseline R2 (mean_baseline_r2)
    # Structure from T021: {"mean_baseline_r2": float, "per_fold_baseline_r2": [float]}
    mean_baseline_r2 = baseline_data.get("mean_baseline_r2")
    if mean_baseline_r2 is None:
        logger.error("mean_baseline_r2 not found in baseline_metrics.json")
        status = {
            "pass": False,
            "reason": "mean_baseline_r2 not found in baseline_metrics.json",
            "delta_r2": 0.0,
            "p_value": 1.0
        }
        with open(output_file, 'w') as f:
            json.dump(status, f, indent=2)
        return
    
    # We need to validate for at least one model (Model A or B)
    # Let's assume the structure of perm_data is:
    # {
    #   "model_a": {"observed_r2": float, "null_distribution": [float]},
    #   "model_b": {"observed_r2": float, "null_distribution": [float]}
    # }
    # Or potentially just lists if T022 output was simpler.
    # Given T022 description: "Write the distribution of R² scores to artifacts/permutation_distributions.json"
    # It likely contains the null distributions. We need the observed R2 too.
    # Let's assume T022 output includes observed R2 as well, or we read it from training logs.
    # However, T022 specifically says "Write the distribution of R² scores".
    # It's possible the observed R2 is stored separately or alongside.
    # Let's check for common keys.
    
    # Attempt to find observed R2 and null distributions for a model (e.g., Model A)
    # We'll look for keys that might indicate model results
    model_a_observed = None
    model_a_null = None
    model_b_observed = None
    model_b_null = None
    
    # Try to extract data for Model A and Model B
    # Heuristic: Look for keys containing 'model_a' or 'model_b'
    for key, value in perm_data.items():
        if 'model_a' in key.lower():
            if isinstance(value, dict):
                model_a_observed = value.get('observed_r2')
                model_a_null = value.get('null_distribution')
            elif isinstance(value, list):
                # If it's just a list, maybe it's the null distribution and observed is elsewhere?
                # This is ambiguous. Let's assume if it's a list, it's the null distribution.
                # But we need observed_r2.
                # For now, let's assume the structure is:
                # {'model_a': {'observed_r2': ..., 'null_distribution': ...}}
                pass
        if 'model_b' in key.lower():
            if isinstance(value, dict):
                model_b_observed = value.get('observed_r2')
                model_b_null = value.get('null_distribution')
            elif isinstance(value, list):
                pass
    
    # If the structure is flat (just lists), we might need to infer.
    # But T022 says "distribution of R² scores", implying the null distribution.
    # We need the observed R2. Let's assume it's stored in the same file under a different key.
    # If not found, we might need to read from training logs, but T023 says "Read and validate artifacts/permutation_distributions.json"
    # So we assume the observed R2 is in there.
    
    # Fallback: If we couldn't find structured data, try to interpret the JSON differently.
    # For example, maybe it's: {'model_a_null': [...], 'model_a_observed': ...}
    if model_a_observed is None and 'model_a_observed' in perm_data:
        model_a_observed = perm_data['model_a_observed']
        model_a_null = perm_data.get('model_a_null')
    if model_b_observed is None and 'model_b_observed' in perm_data:
        model_b_observed = perm_data['model_b_observed']
        model_b_null = perm_data.get('model_b_null')
    
    # If still not found, we might have to fail or look for a single model.
    # Let's try to use Model A if available, else Model B.
    target_model = None
    observed_r2 = None
    null_dist = None
    
    if model_a_observed is not None and model_a_null is not None:
        target_model = "Model A"
        observed_r2 = model_a_observed
        null_dist = model_a_null
    elif model_b_observed is not None and model_b_null is not None:
        target_model = "Model B"
        observed_r2 = model_b_observed
        null_dist = model_b_null
    else:
        # Try to find any observed_r2 and null_distribution in the data
        # This handles cases where the structure might be different
        for key, value in perm_data.items():
            if isinstance(value, dict):
                if 'observed_r2' in value and 'null_distribution' in value:
                    target_model = key
                    observed_r2 = value['observed_r2']
                    null_dist = value['null_distribution']
                    break
        
        if observed_r2 is None:
            logger.error("Could not find observed_r2 and null_distribution for any model in permutation_distributions.json")
            status = {
                "pass": False,
                "reason": "Could not find observed_r2 and null_distribution in permutation_distributions.json",
                "delta_r2": 0.0,
                "p_value": 1.0
            }
            with open(output_file, 'w') as f:
                json.dump(status, f, indent=2)
            return
    
    logger.info(f"Validating SC-002 for {target_model}")
    logger.info(f"  Observed R2: {observed_r2}")
    logger.info(f"  Baseline R2: {mean_baseline_r2}")
    logger.info(f"  Null distribution size: {len(null_dist)}")
    
    try:
        status = validate_sc002(
            observed_r2=observed_r2,
            null_distribution=null_dist,
            baseline_r2=mean_baseline_r2
        )
    except Exception as e:
        logger.error(f"Error during SC-002 validation: {e}")
        status = {
            "pass": False,
            "reason": f"Validation error: {str(e)}",
            "delta_r2": 0.0,
            "p_value": 1.0
        }
    
    # Write output
    with open(output_file, 'w') as f:
        json.dump(status, f, indent=2)
    
    logger.info(f"SC-002 validation result written to {output_file}")
    logger.info(f"  Pass: {status['pass']}")
    logger.info(f"  Reason: {status['reason']}")
    logger.info(f"  Delta R2: {status['delta_r2']}")
    logger.info(f"  P-value: {status['p_value']}")

if __name__ == "__main__":
    main()
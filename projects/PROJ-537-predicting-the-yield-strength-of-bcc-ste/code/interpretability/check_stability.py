"""
T039: Check stability of key DFT descriptors across 10 bootstrapped samples.

Implements FR-008 / SC-005: Check if std_dev of key DFT descriptors < 0.05
across the 10 bootstrapped samples and report `is_stable` boolean.

This script reads the results from T038 (bootstrap_stability.py) which
contains the standard deviations of feature importance across the 10
bootstrapped samples, and checks if the key DFT descriptors are stable.
"""
import os
import sys
import json
import logging
from pathlib import Path
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CONFIG
from utils.logging import get_logger

# Get logger
logger = get_logger(__name__)

# Define key DFT descriptors (these should match what was used in modeling)
# Based on the project context, these are likely:
# - shear_modulus_GPa
# - bulk_modulus_GPa
# - elastic_anisotropy
# - maybe others like c11, c12, c44 if they were used
KEY_DFT_DESCRIPTORS = [
    'shear_modulus_GPa',
    'bulk_modulus_GPa',
    'elastic_anisotropy'
]

STABILITY_THRESHOLD = 0.05

def load_bootstrap_results():
    """Load the bootstrap stability results from T038."""
    results_path = CONFIG.RESULTS_DIR / "bootstrap_stability_results.json"
    
    if not results_path.exists():
        logger.error(f"Bootstrap results file not found: {results_path}")
        raise FileNotFoundError(
            f"Bootstrap results file not found: {results_path}. "
            "Run T038 (bootstrap_stability.py) first."
        )
    
    with open(results_path, 'r') as f:
        return json.load(f)

def check_dft_stability(results):
    """
    Check if std_dev of key DFT descriptors < 0.05 across 10 bootstrapped samples.
    
    Args:
        results: Dictionary containing bootstrap stability results with
                'fixed_sample_bootstrap' key containing std_dev for each feature.
    
    Returns:
        dict: Stability check results including is_stable boolean and details.
    """
    if 'fixed_sample_bootstrap' not in results:
        logger.error("Fixed sample bootstrap results not found in bootstrap results.")
        raise KeyError(
            "Fixed sample bootstrap results not found. "
            "Run T038 (bootstrap_stability.py) first."
        )
    
    fixed_bootstrap = results['fixed_sample_bootstrap']
    feature_stds = fixed_bootstrap.get('feature_importance_std', {})
    
    logger.info(f"Checking stability for {len(KEY_DFT_DESCRIPTORS)} key DFT descriptors")
    logger.info(f"Stability threshold: {STABILITY_THRESHOLD}")
    
    stability_results = {
        'threshold': STABILITY_THRESHOLD,
        'key_dft_descriptors': KEY_DFT_DESCRIPTORS,
        'descriptor_stability': {},
        'all_stable': True,
        'details': []
    }
    
    for descriptor in KEY_DFT_DESCRIPTORS:
        if descriptor in feature_stds:
            std_val = feature_stds[descriptor]
            is_stable = std_val < STABILITY_THRESHOLD
            
            stability_results['descriptor_stability'][descriptor] = {
                'std_dev': float(std_val),
                'is_stable': is_stable,
                'threshold': STABILITY_THRESHOLD
            }
            
            status = "STABLE" if is_stable else "UNSTABLE"
            logger.info(f"  {descriptor}: std_dev={std_val:.4f} -> {status}")
            
            if not is_stable:
                stability_results['all_stable'] = False
                stability_results['details'].append(
                    f"Descriptor '{descriptor}' has std_dev={std_val:.4f} "
                    f"(threshold={STABILITY_THRESHOLD})"
                )
        else:
            logger.warning(f"Key DFT descriptor '{descriptor}' not found in feature importance results")
            stability_results['descriptor_stability'][descriptor] = {
                'std_dev': None,
                'is_stable': False,
                'threshold': STABILITY_THRESHOLD,
                'error': 'Not found in results'
            }
            stability_results['all_stable'] = False
            stability_results['details'].append(
                f"Descriptor '{descriptor}' not found in feature importance results"
            )
    
    return stability_results

def save_stability_check(results, stability_check):
    """Save the stability check results to the output file."""
    output_path = CONFIG.RESULTS_DIR / "stability_check.json"
    
    # Load existing results if present
    if output_path.exists():
        with open(output_path, 'r') as f:
            existing = json.load(f)
    else:
        existing = {}
    
    # Update with new stability check
    existing['stability_check'] = stability_check
    existing['is_stable'] = stability_check['all_stable']
    
    # Save updated results
    with open(output_path, 'w') as f:
        json.dump(existing, f, indent=2)
    
    logger.info(f"Stability check results saved to: {output_path}")
    return output_path

def main():
    """Main entry point for T039 stability check."""
    logger.info("Starting T039: Stability check for key DFT descriptors")
    
    try:
        # Load bootstrap results from T038
        bootstrap_results = load_bootstrap_results()
        
        # Check stability of key DFT descriptors
        stability_check = check_dft_stability(bootstrap_results)
        
        # Save results
        output_path = save_stability_check(bootstrap_results, stability_check)
        
        # Log final result
        if stability_check['all_stable']:
            logger.info("✓ All key DFT descriptors are STABLE (std_dev < 0.05)")
            print(f"SUCCESS: All key DFT descriptors are stable. Output: {output_path}")
        else:
            logger.warning("✗ Some key DFT descriptors are UNSTABLE (std_dev >= 0.05)")
            print(f"WARNING: Some descriptors are unstable. Details: {stability_check['details']}")
            print(f"Output: {output_path}")
        
        return stability_check['all_stable']
        
    except Exception as e:
        logger.error(f"Error during stability check: {e}", exc_info=True)
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
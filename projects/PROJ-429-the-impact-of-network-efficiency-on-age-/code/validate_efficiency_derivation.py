"""
Validate that network metrics were derived correctly using the reciprocal formula.

This script verifies that:
Global_Efficiency = 1.0 / Characteristic_Path_Length
Local_Efficiency = 1.0 / Local_Path_Length (or equivalent derivation)

It reads the generated network_metrics.csv and checks the mathematical relationship.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
TOLERANCE = 1e-6
METRICS_FILE = Path("data/results/network_metrics.csv")
OUTPUT_FILE = Path("data/results/efficiency_check.json")


def validate_efficiency_formulas(metrics_df: pd.DataFrame) -> dict:
    """
    Validate the efficiency formulas in the metrics dataframe.
    
    Args:
        metrics_df: DataFrame containing network metrics including
                   global_efficiency, local_efficiency, and path lengths.
    
    Returns:
        dict with verification results
    """
    results = {
        "formula_verified": False,
        "max_deviation": 0.0,
        "details": {}
    }
    
    # Check required columns
    required_cols = [
        "global_efficiency", "characteristic_path_length",
        "local_efficiency", "local_path_length"
    ]
    
    missing_cols = [col for col in required_cols if col not in metrics_df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        results["details"]["error"] = f"Missing columns: {missing_cols}"
        return results
    
    # Validate Global Efficiency = 1 / Characteristic Path Length
    global_eff = metrics_df["global_efficiency"].values
    char_path_len = metrics_df["characteristic_path_length"].values
    
    # Avoid division by zero
    valid_global_mask = (char_path_len != 0) & (~np.isnan(char_path_len)) & (~np.isnan(global_eff))
    
    if not np.any(valid_global_mask):
        logger.warning("No valid data points for global efficiency validation")
        results["details"]["global_efficiency"] = "No valid data points"
    else:
        # Calculate expected global efficiency
        expected_global_eff = 1.0 / char_path_len[valid_global_mask]
        actual_global_eff = global_eff[valid_global_mask]
        
        # Calculate deviation
        deviation_global = np.abs(expected_global_eff - actual_global_eff)
        max_dev_global = np.nanmax(deviation_global)
        
        results["details"]["global_efficiency"] = {
            "max_deviation": float(max_dev_global),
            "sample_count": int(np.sum(valid_global_mask)),
            "verified": bool(max_dev_global < TOLERANCE)
        }
    
    # Validate Local Efficiency = 1 / Local Path Length (or similar derivation)
    local_eff = metrics_df["local_efficiency"].values
    local_path_len = metrics_df["local_path_length"].values
    
    # Avoid division by zero
    valid_local_mask = (local_path_len != 0) & (~np.isnan(local_path_len)) & (~np.isnan(local_eff))
    
    if not np.any(valid_local_mask):
        logger.warning("No valid data points for local efficiency validation")
        results["details"]["local_efficiency"] = "No valid data points"
    else:
        # Calculate expected local efficiency
        expected_local_eff = 1.0 / local_path_len[valid_local_mask]
        actual_local_eff = local_eff[valid_local_mask]
        
        # Calculate deviation
        deviation_local = np.abs(expected_local_eff - actual_local_eff)
        max_dev_local = np.nanmax(deviation_local)
        
        results["details"]["local_efficiency"] = {
            "max_deviation": float(max_dev_local),
            "sample_count": int(np.sum(valid_local_mask)),
            "verified": bool(max_dev_local < TOLERANCE)
        }
    
    # Determine overall verification status
    global_verified = results["details"].get("global_efficiency", {}).get("verified", False)
    local_verified = results["details"].get("local_efficiency", {}).get("verified", False)
    
    # Calculate overall max deviation
    deviations = []
    if "global_efficiency" in results["details"] and "max_deviation" in results["details"]["global_efficiency"]:
        deviations.append(results["details"]["global_efficiency"]["max_deviation"])
    if "local_efficiency" in results["details"] and "max_deviation" in results["details"]["local_efficiency"]:
        deviations.append(results["details"]["local_efficiency"]["max_deviation"])
    
    if deviations:
        results["max_deviation"] = max(deviations)
        results["formula_verified"] = global_verified and local_verified
    else:
        results["max_deviation"] = 0.0
        results["formula_verified"] = False
    
    logger.info(f"Global Efficiency Verification: {'PASSED' if global_verified else 'FAILED'}")
    logger.info(f"Local Efficiency Verification: {'PASSED' if local_verified else 'FAILED'}")
    logger.info(f"Overall Max Deviation: {results['max_deviation']:.2e}")
    
    return results


def main():
    """Main function to run the validation."""
    logger.info("Starting efficiency formula validation...")
    
    # Check if metrics file exists
    if not METRICS_FILE.exists():
        logger.error(f"Metrics file not found: {METRICS_FILE}")
        results = {
            "formula_verified": False,
            "max_deviation": 0.0,
            "error": f"Metrics file not found: {METRICS_FILE}"
        }
    else:
        try:
            # Load metrics
            logger.info(f"Loading metrics from {METRICS_FILE}")
            metrics_df = pd.read_csv(METRICS_FILE)
            
            logger.info(f"Loaded {len(metrics_df)} records")
            logger.info(f"Columns: {list(metrics_df.columns)}")
            
            # Validate formulas
            results = validate_efficiency_formulas(metrics_df)
            
        except Exception as e:
            logger.error(f"Error processing metrics: {e}")
            results = {
                "formula_verified": False,
                "max_deviation": 0.0,
                "error": str(e)
            }
    
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Save results
    logger.info(f"Saving validation results to {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    logger.info("=" * 50)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Formula Verified: {results['formula_verified']}")
    logger.info(f"Max Deviation: {results['max_deviation']:.2e}")
    
    if "error" in results:
        logger.error(f"Error: {results['error']}")
    
    if results["formula_verified"] and results["max_deviation"] < TOLERANCE:
        logger.info("SUCCESS: All efficiency formulas verified correctly.")
        return 0
    else:
        logger.warning("WARNING: Formula verification failed or deviation exceeds tolerance.")
        return 1


if __name__ == "__main__":
    exit(main())

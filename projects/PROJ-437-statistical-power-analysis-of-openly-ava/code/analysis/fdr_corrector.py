import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy.stats import rankdata

class FDRCorrectionError(Exception):
    """Custom exception for FDR correction errors."""
    pass

def benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Applies the Benjamini-Hochberg procedure to control the False Discovery Rate (FDR).

    Args:
        p_values (List[float]): A list of p-values.
        alpha (float): The desired FDR level.

    Returns:
        List[float]: A list of adjusted p-values.
    """
    ranked_p_values = np.array(sorted(p_values))
    n = len(p_values)
    ranks = np.arange(1, n + 1)
    critical_values = (ranks / n) * alpha
    adjusted_p_values = np.zeros(n)
    for i in range(n - 1, -1, -1):
        adjusted_p_values[i] = min(ranked_p_values[i], critical_values[i])
    return list(adjusted_p_values)

def apply_fdr_to_power_curves(power_curves: List[Dict[str, Any]], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Applies FDR correction to a list of power curve results.

    Args:
        power_curves (List[Dict[str, Any]]): A list of dictionaries, each representing a power curve result.
        alpha (float): The desired FDR level.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries with corrected p-values.
    """
    corrected_power_curves = []
    for curve in power_curves:
        p_values = [result['p_value'] for result in curve['results']]
        adjusted_p_values = benjamini_hochberg(p_values, alpha)
        for i, result in enumerate(curve['results']):
            result['corrected_rate'] = curve['results'][i]['raw_rate']  # Initialize corrected_rate with raw_rate
            result['corrected_p_value'] = adjusted_p_values[i]
        corrected_power_curves.append(curve)
    return corrected_power_curves

def main():
    """
    Main function for testing the FDR correction.  Loads power curves, applies FDR, and saves the results.
    """
    try:
        # Load power curves from a JSON file
        with open("data/aggregated/power_curves.json", "r") as f:
            power_curves = json.load(f)

        # Apply FDR correction
        corrected_power_curves = apply_fdr_to_power_curves(power_curves)

        # Save the corrected power curves
        with open("data/aggregated/corrected_power_curves.json", "w") as f:
            json.dump(corrected_power_curves, f, indent=4)

        logging.info("FDR correction applied and saved to data/aggregated/corrected_power_curves.json")

    except FileNotFoundError:
        logging.error("Power curves file not found.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    main()
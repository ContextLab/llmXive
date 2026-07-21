"""
T027: Implement slope coefficient extraction for code size impact analysis.

Reads the LMER results from data/analysis_results.json, extracts the fixed effect
coefficient for 'code_size' (the slope), and appends it to the results under
the key 'code_size_slopes'.

Output: data/analysis_results.json updated with 'code_size_slopes'.
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Import shared utilities from existing project files
from analysis.simex_correction import load_analysis_results, save_analysis_results
from data.logging_config import get_logger

logger = get_logger(__name__)

def extract_code_size_slope(results: Dict[str, Any]) -> Optional[float]:
    """
    Extract the 'code_size' fixed effect coefficient from LMER results.
    
    Args:
        results: The full analysis results dictionary loaded from JSON.
    
    Returns:
        The slope coefficient for 'code_size' if found, else None.
    """
    lmer_data = results.get("lmer", {})
    
    # The LMER output structure typically contains 'coefficients' which is a dict
    # or list of dicts. We look for the row/entry where the predictor is 'code_size'.
    coefficients = lmer_data.get("coefficients")
    
    if not coefficients:
        logger.warning("No 'coefficients' found in LMER results.")
        return None

    # Handle case where coefficients might be a list of dicts (common in statsmodels)
    if isinstance(coefficients, list):
        for row in coefficients:
            if isinstance(row, dict):
                # Check various possible keys for the predictor name
                name = row.get("term") or row.get("variable") or row.get("param_name")
                if name and "code_size" in str(name).lower():
                    val = row.get("coef") or row.get("coefficient") or row.get("estimate")
                    if val is not None:
                        return float(val)
    
    # Handle case where coefficients is a dict mapping name -> value
    elif isinstance(coefficients, dict):
        # Direct lookup
        if "code_size" in coefficients:
            return float(coefficients["code_size"])
        
        # Case-insensitive search
        for k, v in coefficients.items():
            if "code_size" in str(k).lower():
                return float(v)

    logger.warning("Could not locate 'code_size' coefficient in LMER results.")
    return None

def run_slope_extraction() -> Dict[str, Any]:
    """
    Main logic to load results, extract slope, update dict, and save.
    
    Returns:
        The updated results dictionary.
    """
    logger.info("Starting slope coefficient extraction for code size impact.")
    
    # Load existing results
    results = load_analysis_results()
    
    if not results:
        logger.error("No analysis results found to extract slopes from.")
        return {}

    slope = extract_code_size_slope(results)
    
    if slope is not None:
        # Store in the specific key required by the task
        results["code_size_slopes"] = slope
        logger.info(f"Extracted code_size slope: {slope}")
    else:
        # If extraction fails, store None or a specific error flag
        # but ensure the key exists to satisfy the "append" requirement
        results["code_size_slopes"] = None
        logger.warning("Failed to extract code_size slope; setting to None.")

    # Save updated results
    save_analysis_results(results)
    
    logger.info("Slope extraction complete. Results saved to data/analysis_results.json.")
    return results

def main():
    """Entry point for the script."""
    try:
        run_slope_extraction()
    except Exception as e:
        logger.critical(f"Error during slope extraction: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
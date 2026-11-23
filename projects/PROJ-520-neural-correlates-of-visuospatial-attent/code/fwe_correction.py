"""
T029: Family-Wise Error (FWE) Correction for Univariate T-Tests.

Implements Bonferroni (or FDR) correction for specific hypothesis-driven comparisons:
- Alpha band: P3, Pz, P4
- Beta band: F3, Fz, F4

Reads uncorrected p-values from `data/processed/t_test_results.json` (produced by T028a).
Appends corrected results to `data/processed/feature_metadata.json`.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np

from logger import get_logger

# Define the specific hypothesis-driven comparisons
TARGET_COMPARISONS = [
    {"electrode": "P3", "band": "alpha"},
    {"electrode": "Pz", "band": "alpha"},
    {"electrode": "P4", "band": "alpha"},
    {"electrode": "F3", "band": "beta"},
    {"electrode": "Fz", "band": "beta"},
    {"electrode": "F4", "band": "beta"},
]

logger = get_logger(__name__)

def load_t_test_results(path: Path) -> Dict[str, Any]:
    """Load uncorrected t-test results."""
    if not path.exists():
        raise FileNotFoundError(
            f"Required input file missing: {path}. "
            "Ensure T028a has run successfully."
        )
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded t-test results from {path}")
    return data

def load_feature_metadata(path: Path) -> Dict[str, Any]:
    """Load existing feature metadata, initializing if necessary."""
    if not path.exists():
        raise FileNotFoundError(
            f"Required metadata file missing: {path}. "
            "Ensure T024a/T024b have run successfully."
        )
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded feature metadata from {path}")
    return data

def apply_bonferroni_correction(uncorrected_p: float, n_tests: int) -> float:
    """Apply Bonferroni correction."""
    corrected = min(uncorrected_p * n_tests, 1.0)
    return corrected

def apply_fdr_correction(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction.
    Returns list of corrected p-values corresponding to the input order.
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values with their original indices
    indexed_p = sorted(enumerate(p_values), key=lambda x: x[1])
    sorted_indices = [x[0] for x in indexed_p]
    sorted_p = [x[1] for x in indexed_p]
    
    corrected = [0.0] * n
    min_val = 1.0
    
    # Calculate BH corrected values (working backwards)
    for i in range(n - 1, -1, -1):
        rank = i + 1
        corrected_val = min(sorted_p[i] * n / rank, min_val)
        min_val = corrected_val
        corrected[sorted_indices[i]] = corrected_val
    
    # Ensure monotonicity (cumulative min from largest to smallest)
    # Actually, BH procedure ensures this if done correctly, but let's be safe
    # Re-sort to ensure non-decreasing order of corrected p-values
    # The standard BH implementation:
    # p_corrected[i] = min( (n/j) * p[j] for j >= i )
    
    # Let's re-implement strictly
    corrected = [0.0] * n
    running_min = 1.0
    for i in range(n - 1, -1, -1):
        val = sorted_p[i] * n / (i + 1)
        running_min = min(running_min, val)
        corrected[sorted_indices[i]] = running_min
    
    # Ensure values are <= 1.0
    corrected = [min(p, 1.0) for p in corrected]
    
    return corrected

def run_fwe_correction(
    t_test_path: Path, 
    metadata_path: Path, 
    output_path: Path,
    method: str = "bonferroni"
) -> Dict[str, Any]:
    """
    Run FWE correction on specific electrode-band pairs.
    
    Args:
        t_test_path: Path to t_test_results.json
        metadata_path: Path to feature_metadata.json
        output_path: Path to save updated feature_metadata.json
        method: "bonferroni" or "fdr"
    
    Returns:
        Dict containing the corrected results
    """
    # Load inputs
    t_test_data = load_t_test_results(t_test_path)
    metadata = load_feature_metadata(metadata_path)
    
    # Extract uncorrected p-values for target comparisons
    target_p_values = []
    results_list = []
    
    for comp in TARGET_COMPARISONS:
        electrode = comp["electrode"]
        band = comp["band"]
        key = f"{electrode}_{band}"
        
        # Handle potential key variations (e.g., "P3_alpha" vs "P3-alpha")
        if key not in t_test_data:
            # Try alternative formats
            alt_key = f"{electrode}-{band}"
            if alt_key in t_test_data:
                key = alt_key
            else:
                logger.warning(f"Key {key} not found in t-test results. Skipping.")
                continue
        
        entry = t_test_data[key]
        if "p_value" not in entry:
            logger.error(f"Missing 'p_value' in entry for {key}")
            continue
        
        p_val = entry["p_value"]
        target_p_values.append(p_val)
        
        results_list.append({
            "electrode": electrode,
            "band": band,
            "uncorrected_p": float(p_val),
            "t_statistic": entry.get("t_statistic"),
            "method": method
        })
    
    if not target_p_values:
        raise ValueError("No valid p-values found for target comparisons.")
    
    # Apply correction
    n_tests = len(target_p_values)
    corrected_p_values = []
    
    if method == "bonferroni":
        for p in target_p_values:
            corrected_p_values.append(apply_bonferroni_correction(p, n_tests))
    elif method == "fdr":
        corrected_p_values = apply_fdr_correction(target_p_values)
    else:
        raise ValueError(f"Unsupported correction method: {method}")
    
    # Update results with corrected values
    for i, result in enumerate(results_list):
        result["corrected_p"] = float(corrected_p_values[i])
    
    # Ensure the key exists in metadata
    if "fwe_corrected_p_values" not in metadata:
        metadata["fwe_corrected_p_values"] = []
    
    # Append new results (or replace if we want to keep it fresh)
    # Per task spec: "Append a list of objects"
    metadata["fwe_corrected_p_values"].extend(results_list)
    
    # Save updated metadata
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Saved FWE corrected p-values to {output_path}")
    
    return {
        "method": method,
        "n_tests": n_tests,
        "corrected_results": results_list
    }

def main():
    """Main entry point for T029."""
    base_dir = Path(__file__).resolve().parent.parent
    t_test_path = base_dir / "data" / "processed" / "t_test_results.json"
    metadata_path = base_dir / "data" / "processed" / "feature_metadata.json"
    output_path = base_dir / "data" / "processed" / "feature_metadata.json"
    
    logger.info("Starting T029: FWE Correction")
    
    try:
        # Run Bonferroni correction (default for strict control)
        result = run_fwe_correction(
            t_test_path=t_test_path,
            metadata_path=metadata_path,
            output_path=output_path,
            method="bonferroni"
        )
        
        logger.info(f"FWE Correction Complete: {result['n_tests']} tests corrected.")
        for r in result["corrected_results"]:
            logger.info(f"  {r['electrode']}_{r['band']}: "
                        f"uncorrected={r['uncorrected_p']:.4f}, "
                        f"corrected={r['corrected_p']:.4f}")
        
    except FileNotFoundError as e:
        logger.error(f"Required input file missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during FWE correction: {e}")
        raise

if __name__ == "__main__":
    main()

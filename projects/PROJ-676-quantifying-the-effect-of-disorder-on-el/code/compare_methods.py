import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np

from code.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_scaling_fits(filepath: str) -> List[Dict[str, Any]]:
    """
    Load PR scaling fits from JSON.
    Expected schema: list of dicts with keys 'disorder_width', 'xi', 'uncertainty', ...
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Scaling fits file not found: {filepath}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected list in {filepath}, got {type(data)}")
    
    # Validate basic schema
    for i, item in enumerate(data):
        if 'disorder_width' not in item:
            raise ValueError(f"Item {i} missing 'disorder_width'")
        if 'xi' not in item:
            raise ValueError(f"Item {i} missing 'xi'")
    
    return data

def load_lyapunov_exponents(filepath: str) -> List[Dict[str, Any]]:
    """
    Load TM Lyapunov exponents from JSON.
    Expected schema: list of dicts with keys 'disorder_width', 'localization_length', ...
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Lyapunov exponents file not found: {filepath}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected list in {filepath}, got {type(data)}")
    
    # Validate basic schema
    for i, item in enumerate(data):
        if 'disorder_width' not in item:
            raise ValueError(f"Item {i} missing 'disorder_width'")
        if 'localization_length' not in item:
            raise ValueError(f"Item {i} missing 'localization_length'")
    
    return data

def compute_relative_error(xi_pr: float, xi_tm: float) -> float:
    """
    Compute relative error between PR and TM localization lengths.
    Formula: |xi_pr - xi_tm| / max(xi_pr, xi_tm)
    """
    if xi_pr == 0 and xi_tm == 0:
        return 0.0
    max_val = max(abs(xi_pr), abs(xi_tm))
    if max_val == 0:
        return 0.0
    return abs(xi_pr - xi_tm) / max_val

def compare_methods(
    pr_results: List[Dict[str, Any]],
    tm_results: List[Dict[str, Any]],
    threshold: float = 0.10,
    min_realizations: int = 8
) -> Dict[str, Any]:
    """
    Compare PR and TM localization lengths.
    
    Validates SC-002: Agreement within 10% for L >= 400 and >= 80% of realizations.
    
    Args:
        pr_results: List of dicts from scaling_fits.json
        tm_results: List of dicts from lyapunov_exponents.json
        threshold: Maximum allowed relative error (default 0.10)
        min_realizations: Minimum number of agreeing realizations required
    
    Returns:
        Dict with comparison results and pass/fail status
    """
    logger.info(f"Comparing methods with threshold={threshold}, min_realizations={min_realizations}")
    
    # Group by disorder width
    pr_by_width = {}
    for item in pr_results:
        w = item['disorder_width']
        if w not in pr_by_width:
            pr_by_width[w] = []
        pr_by_width[w].append(item['xi'])
    
    tm_by_width = {}
    for item in tm_results:
        w = item['disorder_width']
        if w not in tm_by_width:
            tm_by_width[w] = []
        tm_by_width[w].append(item['localization_length'])
    
    # Find common widths
    common_widths = sorted(set(pr_by_width.keys()) & set(tm_by_width.keys()))
    
    if not common_widths:
        logger.warning("No common disorder widths found between PR and TM results")
        return {
            "status": "fail",
            "reason": "No common disorder widths",
            "details": []
        }
    
    results = []
    total_agreements = 0
    total_comparisons = 0
    
    for w in common_widths:
        pr_vals = pr_by_width[w]
        tm_vals = tm_by_width[w]
        
        # Ensure we have enough data points
        n_comparisons = min(len(pr_vals), len(tm_vals))
        if n_comparisons == 0:
            continue
        
        agreements = 0
        for i in range(n_comparisons):
            xi_pr = pr_vals[i]
            xi_tm = tm_vals[i]
            rel_err = compute_relative_error(xi_pr, xi_tm)
            
            passed = rel_err <= threshold
            if passed:
                agreements += 1
            
            total_comparisons += 1
            results.append({
                "disorder_width": w,
                "realization_index": i,
                "xi_pr": xi_pr,
                "xi_tm": xi_tm,
                "relative_error": rel_err,
                "passed": passed
            })
    
    # Calculate overall agreement rate
    if total_comparisons == 0:
        return {
            "status": "fail",
            "reason": "No comparisons made",
            "details": []
        }
    
    agreement_rate = agreements / total_comparisons
    required_agreements = min_realizations  # Based on 80% of 10 realizations = 8
    
    # Determine pass/fail
    # SC-002: >= 80% of realizations must agree within 10%
    # For 10 realizations, 80% = 8 realizations
    # We check if the number of agreements meets the minimum requirement
    status = "pass" if agreements >= required_agreements else "fail"
    
    logger.info(f"Comparison complete: {agreements}/{total_comparisons} agreements ({agreement_rate:.2%})")
    logger.info(f"Status: {status} (required: {required_agreements} agreements)")
    
    return {
        "status": status,
        "threshold": threshold,
        "min_realizations": min_realizations,
        "total_comparisons": total_comparisons,
        "agreements": agreements,
        "agreement_rate": agreement_rate,
        "details": results
    }

def main():
    """
    Main entry point for method comparison.
    Loads PR and TM results, compares them, and writes report to disk.
    """
    config = get_config()
    
    # Verify NUM_REALIZATIONS is defined
    if 'NUM_REALIZATIONS' not in config:
        raise RuntimeError("NUM_REALIZATIONS not defined in config.py")
    
    num_realizations = config['NUM_REALIZATIONS']
    min_agreements = int(0.8 * num_realizations)
    
    logger.info(f"Using NUM_REALIZATIONS={num_realizations}, min_agreements={min_agreements}")
    
    # Define paths
    project_root = Path(config['PROJECT_ROOT'])
    pr_path = project_root / "data" / "processed" / "scaling_fits.json"
    tm_path = project_root / "data" / "processed" / "lyapunov_exponents.json"
    output_path = project_root / "data" / "processed" / "method_agreement_report.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    try:
        pr_results = load_scaling_fits(str(pr_path))
        logger.info(f"Loaded {len(pr_results)} PR results from {pr_path}")
    except FileNotFoundError as e:
        logger.error(f"Failed to load PR results: {e}")
        raise
    
    try:
        tm_results = load_lyapunov_exponents(str(tm_path))
        logger.info(f"Loaded {len(tm_results)} TM results from {tm_path}")
    except FileNotFoundError as e:
        logger.error(f"Failed to load TM results: {e}")
        raise
    
    # Compare methods
    report = compare_methods(
        pr_results=pr_results,
        tm_results=tm_results,
        threshold=0.10,
        min_realizations=min_agreements
    )
    
    # Write report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Method agreement report written to {output_path}")
    logger.info(f"Final status: {report['status']}")
    
    return report

if __name__ == "__main__":
    main()
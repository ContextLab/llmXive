"""
code/analysis/correction.py
Implements Bonferroni correction for multiple comparisons.

Decision Logic:
1. Check N: Read N from data/processed/study_count.json. If N < 10, skip immediately.
2. Check k: If N >= 10, read k (distinct tract count) from data/derived/tract_count.json.
3. Execute ONLY if k >= 2 tracts AND N >= 10.
4. Output: data/derived/bonferroni_status.json
"""
import json
import math
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Determine the project root directory."""
    current = Path(__file__).resolve()
    if "code" in current.parts:
        return current.parents[1]
    return current.parent.parent

def load_study_count_from_json() -> int:
    """Load N from data/processed/study_count.json."""
    root = get_project_root()
    path = root / "data" / "processed" / "study_count.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing study count file: {path}. Run T014a first.")
    with open(path, "r") as f:
        data = json.load(f)
    return int(data.get("N", 0))

def load_tract_data_from_json() -> Dict[str, Any]:
    """
    Load tract count from data/derived/tract_count.json.
    Note: T008c (tract_counting) saves to data/derived/tract_count.json based on task description.
    """
    root = get_project_root()
    path = root / "data" / "derived" / "tract_count.json"
    if not path.exists():
        logger.warning(f"Tract count file not found: {path}. Returning empty dict.")
        return {}
    with open(path, "r") as f:
        return json.load(f)

def count_unique_tracts() -> int:
    """Count unique tracts (k) from tract_count.json."""
    data = load_tract_data_from_json()
    return int(data.get("k", 0))

def apply_bonferroni_correction(k: int, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction.
    Adjusted threshold = alpha / k
    """
    if k < 2:
        return {
            "bonferroni_applied": False,
            "reason": "k < 2, correction not needed",
            "adjusted_threshold": alpha,
            "limitations_note": "Limitations: Bonferroni correction is conservative due to potential non-independence of tract measurements."
        }

    adjusted_alpha = alpha / k
    return {
        "bonferroni_applied": True,
        "k": k,
        "original_alpha": alpha,
        "adjusted_threshold": adjusted_alpha,
        "limitations_note": "Limitations: Bonferroni correction is conservative due to potential non-independence of tract measurements."
    }

def run_correction_analysis() -> Dict[str, Any]:
    """
    Main entry point for correction analysis.
    Checks k and N, applies Bonferroni if eligible.
    """
    try:
        n = load_study_count_from_json()
    except FileNotFoundError as e:
        logger.error(f"Study count file missing: {e}")
        return {"status": "error", "reason": str(e), "bonferroni_applied": False}

    logger.info(f"Loaded study count N = {n}")

    # Gate Logic: If N < 10, skip immediately
    if n < 10:
        logger.warning("Bonferroni skipped: N < 10")
        return {
            "bonferroni_applied": False,
            "reason": "N < 10, meta-analysis skipped",
            "adjusted_threshold": 0.05,
            "limitations_note": "Limitations: Bonferroni correction is conservative due to potential non-independence of tract measurements."
        }

    k = count_unique_tracts()
    logger.info(f"Loaded tract count k = {k}")

    # Constraint: Execute ONLY if k >= 2 tracts AND N >= 10
    if k < 2:
        logger.warning("Bonferroni correction skipped: k < 2 or extraction failed")
        return apply_bonferroni_correction(k)

    return apply_bonferroni_correction(k)

def main():
    """CLI entry point."""
    result = run_correction_analysis()
    root = get_project_root()
    output_path = root / "data" / "derived" / "bonferroni_status.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Bonferroni status written to {output_path}")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
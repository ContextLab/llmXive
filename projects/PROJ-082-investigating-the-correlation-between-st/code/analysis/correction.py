"""
Multiple Comparisons Correction (Task T021).

Implements Standard Bonferroni Correction for the meta-analysis pipeline.

Logic:
1. Read N from study_count.json. If N < 10, skip correction.
2. Read k (number of distinct tracts) from tract_count.json.
3. If k >= 2 and N >= 10, compute adjusted alpha = 0.05 / k.
4. Read meta-analysis results from meta_results.json to extract p-values.
5. Apply Bonferroni correction to extracted p-values.
6. Write bonferroni_status.json with correction details.
7. Update results.json with adjusted p-values and metadata.

Output:
  - data/derived/bonferroni_status.json
  - data/derived/results.json (updated)
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

def get_project_root() -> Path:
    """Find the project root (parent of 'code' directory)."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if parent.name == "code":
            return parent.parent
    return current.parent

def load_json(path: Path) -> Optional[Dict]:
    """Load a JSON file, returning None if it doesn't exist."""
    if not path.exists():
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path: Path, data: Dict) -> None:
    """Save a dictionary to a JSON file, creating directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def apply_bonferroni_correction(p_values: List[float], k: int) -> tuple:
    """
    Apply Bonferroni correction to a list of p-values.

    Args:
        p_values: List of original p-values.
        k: Number of comparisons (tracts).

    Returns:
        Tuple of (adjusted_p_values, adjusted_alpha)
    """
    alpha = 0.05
    adjusted_alpha = alpha / k
    # Bonferroni: multiply p by k, cap at 1.0
    adjusted_p = [min(p * k, 1.0) for p in p_values]
    return adjusted_p, adjusted_alpha

def extract_p_values_from_meta_results(meta_results: Dict) -> List[float]:
    """
    Extract p-values from meta-analysis results.

    Looks for common p-value keys in the meta_results dictionary.
    """
    p_values = []
    # Check for pooled p-value from random-effects or fixed-effects model
    if "pooled_p_value" in meta_results:
        p_values.append(meta_results["pooled_p_value"])
    # Check for individual study p-values if available
    if "study_p_values" in meta_results:
        p_values.extend(meta_results["study_p_values"])
    # Check for heterogeneity test p-value (e.g., Q-test)
    if "heterogeneity_p_value" in meta_results:
        p_values.append(meta_results["heterogeneity_p_value"])
    # Check for Egger's test p-value
    if "egger_p_value" in meta_results:
        p_values.append(meta_results["egger_p_value"])

    return p_values

def main() -> int:
    """Main entry point for Bonferroni correction task."""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger("correction")
    project_root = get_project_root()

    # Define paths
    study_count_path = project_root / "data" / "processed" / "study_count.json"
    tract_count_path = project_root / "data" / "derived" / "tract_count.json"
    meta_results_path = project_root / "data" / "derived" / "meta_results.json"
    results_path = project_root / "data" / "derived" / "results.json"
    status_path = project_root / "data" / "derived" / "bonferroni_status.json"

    # Load study count
    study_count = load_json(study_count_path)
    if not study_count:
        logger.warning(f"study_count.json not found at {study_count_path}. Skipping correction.")
        save_json(status_path, {
            "bonferroni_applied": False,
            "reason": "study_count.json not found",
            "N": None
        })
        return 0

    N = study_count.get("N", 0)

    # Gate: Need at least 10 studies
    if N < 10:
        logger.info(f"N={N} < 10. Skipping Bonferroni correction due to insufficient studies.")
        save_json(status_path, {
            "bonferroni_applied": False,
            "reason": "Insufficient studies (N < 10)",
            "N": N
        })
        # Update results if it exists
        results = load_json(results_path) or {}
        results["bonferroni_applied"] = False
        save_json(results_path, results)
        return 0

    # Load tract count
    tract_count = load_json(tract_count_path)
    k = tract_count.get("k", 0) if tract_count else 0

    # Gate: Need at least 2 distinct tracts for multiple comparisons
    if k < 2:
        logger.info(f"Tract count k={k} < 2. Skipping correction (no multiple comparisons).")
        save_json(status_path, {
            "bonferroni_applied": False,
            "reason": "Insufficient tracts (k < 2)",
            "k": k,
            "N": N
        })
        results = load_json(results_path) or {}
        results["bonferroni_applied"] = False
        save_json(results_path, results)
        return 0

    # Load meta-analysis results to extract p-values
    meta_results = load_json(meta_results_path)
    if not meta_results:
        logger.warning(f"meta_results.json not found at {meta_results_path}. Cannot extract p-values.")
        save_json(status_path, {
            "bonferroni_applied": False,
            "reason": "meta_results.json not found",
            "k": k,
            "N": N
        })
        return 0

    # Extract p-values
    p_values = extract_p_values_from_meta_results(meta_results)

    if not p_values:
        logger.warning("No p-values found in meta_results.json. Skipping correction.")
        save_json(status_path, {
            "bonferroni_applied": False,
            "reason": "No p-values found in meta results",
            "k": k,
            "N": N
        })
        return 0

    logger.info(f"Found {len(p_values)} p-value(s). Applying Bonferroni correction (k={k}, N={N}).")

    # Apply correction
    adjusted_p_values, adjusted_alpha = apply_bonferroni_correction(p_values, k)

    # Prepare status output
    status = {
        "bonferroni_applied": True,
        "adjusted_threshold": adjusted_alpha,
        "original_alpha": 0.05,
        "k": k,
        "N": N,
        "num_comparisons": len(p_values),
        "original_p_values": p_values,
        "adjusted_p_values": adjusted_p_values
    }
    save_json(status_path, status)
    logger.info(f"Bonferroni status saved to {status_path}")

    # Update results.json
    results = load_json(results_path) or {}
    results["bonferroni_applied"] = True
    results["bonferroni_adjusted_threshold"] = adjusted_alpha
    results["bonferroni_original_alpha"] = 0.05
    results["bonferroni_k"] = k
    results["bonferroni_N"] = N

    # Store adjusted p-values
    if len(adjusted_p_values) == 1:
        results["adjusted_p_value"] = adjusted_p_values[0]
    else:
        results["adjusted_p_values"] = adjusted_p_values

    # Store original p-values for reference
    if len(p_values) == 1:
        results["original_p_value"] = p_values[0]
    else:
        results["original_p_values"] = p_values

    save_json(results_path, results)
    logger.info(f"Results updated with Bonferroni corrections at {results_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
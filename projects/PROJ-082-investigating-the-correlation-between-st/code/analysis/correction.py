"""
Multiple Comparisons Correction (Bonferroni) Implementation.

Task: T021
Reads gate_result.json to determine synthesis mode.
If quantitative mode is active, reads study counts and tract counts to compute
adjusted alpha and p-values.
Writes bonferroni_status.json and updates results.json.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def load_json(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(file_path: Path, data: Dict[str, Any]) -> None:
    """Save data to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def apply_bonferroni_correction(
    p_values: List[float],
    k: int,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Apply Bonferroni correction to a list of p-values.

    Args:
        p_values: List of raw p-values.
        k: Number of comparisons (distinct tracts).
        alpha: Significance level (default 0.05).

    Returns:
        Dictionary containing correction results.
    """
    if k <= 0:
        raise ValueError("Number of comparisons (k) must be positive.")

    alpha_adj = alpha / k
    p_adjusted = [min(p * k, 1.0) for p in p_values]

    return {
        "bonferroni_applied": True,
        "k": k,
        "alpha": alpha,
        "alpha_adj": alpha_adj,
        "p_adjusted": p_adjusted
    }

def extract_p_values_from_meta_results(meta_results: Dict[str, Any]) -> List[float]:
    """
    Extract p-values from meta-analysis results.
    Handles various possible structures in meta_results.
    """
    p_values = []

    # Case 1: Direct 'p_value' field
    if "p_value" in meta_results:
        val = meta_results["p_value"]
        if isinstance(val, (int, float)) and not (val is None or (isinstance(val, float) and val != val)):
            p_values.append(float(val))

    # Case 2: 'results' list
    if "results" in meta_results and isinstance(meta_results["results"], list):
        for item in meta_results["results"]:
            if isinstance(item, dict) and "p_value" in item:
                val = item["p_value"]
                if isinstance(val, (int, float)) and not (val is None or (isinstance(val, float) and val != val)):
                    p_values.append(float(val))

    # Case 3: 'effect_size' list
    if "effect_size" in meta_results and isinstance(meta_results["effect_size"], list):
        for item in meta_results["effect_size"]:
            if isinstance(item, dict) and "p_value" in item:
                val = item["p_value"]
                if isinstance(val, (int, float)) and not (val is None or (isinstance(val, float) and val != val)):
                    p_values.append(float(val))

    # Case 4: Nested 'p_value' in 'overall' or 'summary'
    for key in ["overall", "summary", "pooled"]:
        if key in meta_results and isinstance(meta_results[key], dict):
            if "p_value" in meta_results[key]:
                val = meta_results[key]["p_value"]
                if isinstance(val, (int, float)) and not (val is None or (isinstance(val, float) and val != val)):
                    p_values.append(float(val))

    return p_values

def run_correction() -> Dict[str, Any]:
    """
    Main logic for multiple comparisons correction.
    """
    project_root = get_project_root()
    data_derived = project_root / "data" / "derived"
    data_processed = project_root / "data" / "processed"

    # Paths
    gate_path = data_derived / "gate_result.json"
    study_count_path = data_processed / "study_count.json"
    tract_count_path = data_derived / "tract_count.json"
    meta_results_path = data_derived / "meta_results.json"
    results_path = data_derived / "results.json"
    output_path = data_derived / "bonferroni_status.json"

    # 1. Check Gate Result
    logger.info(f"Reading gate result from {gate_path}")
    try:
        gate_result = load_json(gate_path)
    except FileNotFoundError:
        logger.warning("Gate result file not found. Assuming narrative mode.")
        gate_result = {"status": "narrative_required", "reason": "Gate file missing"}

    status = gate_result.get("status", "narrative_required")

    if status == "narrative_required":
        logger.info("Narrative mode active. Skipping Bonferroni correction.")
        result = {
            "bonferroni_applied": False,
            "reason": "Narrative mode active"
        }
        save_json(output_path, result)
        return result

    # 2. Load Counts
    try:
        study_count_data = load_json(study_count_path)
        N = study_count_data.get("N", 0)
    except FileNotFoundError:
        logger.error(f"Study count file not found: {study_count_path}")
        N = 0

    try:
        tract_count_data = load_json(tract_count_path)
        k = tract_count_data.get("k", 0)
    except FileNotFoundError:
        logger.error(f"Tract count file not found: {tract_count_path}")
        k = 0

    logger.info(f"Study count (N): {N}, Tract count (k): {k}")

    # 3. Check Conditions
    # Condition: k >= 2 AND N >= 10
    if k < 2:
        logger.info(f"Skipping correction: k={k} < 2. (k must be >= 2)")
        result = {
            "bonferroni_applied": False,
            "reason": f"Insufficient tracts (k={k} < 2)"
        }
        save_json(output_path, result)
        return result

    if N < 10:
        logger.info(f"Skipping correction: N={N} < 10. (N must be >= 10)")
        result = {
            "bonferroni_applied": False,
            "reason": f"Insufficient studies (N={N} < 10)"
        }
        save_json(output_path, result)
        return result

    # 4. Extract P-values
    try:
        meta_results = load_json(meta_results_path)
    except FileNotFoundError:
        logger.warning(f"Meta results file not found: {meta_results_path}. Cannot extract p-values.")
        result = {
            "bonferroni_applied": False,
            "reason": "Meta results file missing"
        }
        save_json(output_path, result)
        return result

    p_values = extract_p_values_from_meta_results(meta_results)

    if not p_values:
        logger.warning("No valid p-values found in meta results.")
        result = {
            "bonferroni_applied": False,
            "reason": "No valid p-values found"
        }
        save_json(output_path, result)
        return result

    # 5. Apply Correction
    logger.info(f"Applying Bonferroni correction for k={k} comparisons.")
    correction_result = apply_bonferroni_correction(p_values, k)

    # 6. Update Results JSON
    if results_path.exists():
        try:
            current_results = load_json(results_path)
        except Exception as e:
            logger.warning(f"Could not load existing results.json: {e}. Creating new.")
            current_results = {}

        current_results["bonferroni_correction"] = correction_result
        save_json(results_path, current_results)
        logger.info(f"Updated {results_path} with correction results.")
    else:
        # If results.json doesn't exist, create it with the correction data
        # Note: This might be too minimal for a full results.json, but satisfies the requirement
        # to update it. A full pipeline should have populated results.json earlier.
        logger.warning(f"{results_path} not found. Creating minimal results.json with correction data.")
        save_json(results_path, {
            "bonferroni_correction": correction_result
        })

    # 7. Save Bonferroni Status
    save_json(output_path, correction_result)
    logger.info(f"Saved Bonferroni status to {output_path}")

    return correction_result

def main() -> None:
    """Entry point."""
    try:
        result = run_correction()
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error in correction pipeline: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
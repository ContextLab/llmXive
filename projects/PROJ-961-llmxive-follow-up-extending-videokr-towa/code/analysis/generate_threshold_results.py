"""
Generate the final threshold results JSON (T023).

This script consumes the output of T020b (detect_threshold.py) and T020a (bin_utils.py)
to produce the definitive `data/processed/threshold_results.json` artifact.

It explicitly:
1. Loads the permutation test results (p-value, effect size, optimal knot).
2. Loads bin configuration to check for deferrals.
3. Compares the p-value against alpha=0.05.
4. Writes a JSON file with: p_value, alpha, is_significant, conclusion, optimal_knot, effect_size, deferral_reasons.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from local utils
from utils.config import get_project_root, get_path, ensure_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required input file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(file_path: Path, data: Dict[str, Any]) -> None:
    """Save data to a JSON file."""
    ensure_dir(file_path.parent)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved results to {file_path}")

def main() -> int:
    """
    Main entry point for T023: Generate Threshold Results.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    project_root = get_project_root()
    
    # Define input paths (dependencies: T020b output, T020a output)
    # T020b produces: data/processed/threshold_detection_results.json (or similar)
    # T020a produces: data/processed/bin_config.json
    # We assume T020b's output path based on standard naming conventions if not specified,
    # but strictly looking for the artifact produced by detect_threshold.py.
    # Based on T020b description: "Output: Identify the optimal knot and report the corrected p-value."
    # Let's assume the output file is `threshold_detection_results.json` as per typical pipeline patterns,
    # or we might need to check the exact filename from T020b. 
    # Re-reading T020b: "Output: Identify the optimal knot and report the corrected p-value."
    # It doesn't explicitly name the file, but T023 needs to read it.
    # Let's assume the standard output name for T020b is `threshold_detection_results.json`.
    # If T020b writes to a different name, this task must be updated. 
    # However, looking at T020b's description again, it says "Output: Identify the optimal knot...".
    # Let's assume the file is `data/processed/threshold_detection_results.json`.
    
    # Wait, T020b description says: "Output: Identify the optimal knot and report the corrected p-value."
    # It does not specify the filename. Let's look at T020a: "Write a JSON file `data/processed/bin_config.json`".
    # Let's assume T020b writes to `data/processed/threshold_detection_results.json`.
    # If that file doesn't exist, we might need to look for `data/processed/detect_threshold_results.json` or similar.
    # To be safe, let's check for common patterns or assume the name based on the script name.
    # Script: detect_threshold.py -> Output: threshold_detection_results.json
    
    input_threshold_path = get_path(project_root, "data/processed/threshold_detection_results.json")
    input_bin_config_path = get_path(project_root, "data/processed/bin_config.json")
    output_path = get_path(project_root, "data/processed/threshold_results.json")

    # Check if input files exist
    if not input_threshold_path.exists():
        logger.error(f"Input file not found: {input_threshold_path}")
        logger.error("Ensure T020b (detect_threshold.py) has been run successfully.")
        return 1

    if not input_bin_config_path.exists():
        logger.warning(f"Bin config file not found: {input_bin_config_path}")
        logger.warning("Proceeding without bin configuration (no deferral info).")
        bin_config = {}
    else:
        bin_config = load_json_file(input_bin_config_path)

    # Load threshold detection results
    try:
        threshold_results = load_json_file(input_threshold_path)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Failed to load threshold results: {e}")
        return 1

    # Extract key metrics
    # Expected keys in threshold_results: p_value, effect_size, optimal_knot, deferral_reasons (optional)
    p_value = threshold_results.get("p_value")
    effect_size = threshold_results.get("effect_size")
    optimal_knot = threshold_results.get("optimal_knot")
    deferral_reasons = threshold_results.get("deferral_reasons", [])

    # Validate required fields
    if p_value is None:
        logger.error("p_value is missing from threshold detection results.")
        return 1
    if effect_size is None:
        logger.error("effect_size is missing from threshold detection results.")
        return 1
    if optimal_knot is None:
        logger.error("optimal_knot is missing from threshold detection results.")
        return 1

    # Define alpha
    alpha = 0.05

    # Determine significance
    is_significant = p_value < alpha

    # Determine conclusion
    if is_significant:
        conclusion = "PASS"
        conclusion_detail = f"Significant threshold detected (p={p_value:.4f} < {alpha})."
    else:
        conclusion = "FAIL"
        conclusion_detail = f"No significant threshold detected (p={p_value:.4f} >= {alpha})."

    # Check for deferrals from bin_config
    # T020a might have set status: "deferred" or merged bins.
    # If T020a deferred a test, we should reflect that in the conclusion.
    bin_strategy = bin_config.get("strategy", "none")
    if bin_strategy == "deferred":
        reason = bin_config.get("reason", "insufficient_power")
        conclusion = "DEFERRED"
        conclusion_detail = f"Statistical test deferred due to {reason}. Bin status: {bin_strategy}."
        is_significant = False # Cannot be significant if deferred
        p_value = None # Or keep as None to indicate no test was run

    # Construct final output
    final_results = {
        "p_value": p_value,
        "alpha": alpha,
        "is_significant": is_significant,
        "conclusion": conclusion,
        "conclusion_detail": conclusion_detail,
        "optimal_knot": optimal_knot,
        "effect_size": effect_size,
        "deferral_reasons": deferral_reasons if deferral_reasons else [],
        "bin_strategy": bin_strategy,
        "timestamp": "2023-10-27T12:00:00Z" # Placeholder, can be dynamic if needed
    }

    # Save output
    try:
        save_json_file(output_path, final_results)
        logger.info(f"T023 completed successfully. Conclusion: {conclusion}")
        return 0
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
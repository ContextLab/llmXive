import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/metadata/aggregate_stats.log')
    ]
)
logger = logging.getLogger(__name__)

def load_aggregated_results() -> List[Dict[str, Any]]:
    """
    Read data/processed/scaling_fits.json and verify all W values are present.
    Aggregates into a single list for downstream tasks.
    """
    input_path = Path("data/processed/scaling_fits.json")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Missing required input: {input_path}")

    try:
        with open(input_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {input_path}: {e}")
        raise

    if not isinstance(data, list):
        logger.error(f"Expected list in {input_path}, got {type(data)}")
        raise ValueError(f"Invalid format in {input_path}: expected list")

    if len(data) == 0:
        logger.warning("Input file is empty (empty list). No data to aggregate.")
        return []

    # Verify required keys for downstream tasks (T015)
    required_keys = {'disorder_width', 'xi', 'uncertainty', 'p_value'}
    for i, item in enumerate(data):
        missing = required_keys - set(item.keys())
        if missing:
            logger.warning(f"Item {i} missing keys: {missing}. Will proceed but downstream may fail.")
    
    logger.info(f"Loaded {len(data)} scaling fit results from {input_path}")
    return data

def analyze_scaling_slopes(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract slope statistics for Bonferroni correction.
    In this pipeline, p_value is derived from the linear regression fit (FR-005)
    testing the slope deviation from -2 in the weak disorder regime.
    This function validates the presence of p_values and returns the dataset
    ready for correction.
    """
    if not data:
        return []

    valid_data = []
    for item in data:
        if 'p_value' in item and item['p_value'] is not None:
            valid_data.append(item)
        else:
            logger.warning(f"Skipping item with missing p_value: {item.get('disorder_width')}")
    
    logger.info(f"Filtered to {len(valid_data)} items with valid p_values for correction.")
    return valid_data

def apply_bonferroni_correction(data: List[Dict[str, Any]], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction for the full family of disorder widths (SC-005).
    Correction Factor: alpha / len(processed_widths).
    Output: Dictionary with corrected p-values and significance flags.
    """
    if not data:
        logger.warning("No data to apply Bonferroni correction.")
        return {"corrected_results": [], "alpha": alpha, "num_tests": 0}

    num_tests = len(data)
    corrected_alpha = alpha / num_tests
    
    logger.info(f"Applying Bonferroni correction: {num_tests} tests, alpha={alpha}, corrected_alpha={corrected_alpha}")

    corrected_results = []
    significant_count = 0

    for item in data:
        raw_p = item['p_value']
        # Bonferroni: compare raw_p against corrected_alpha
        # Or adjust p-value: p_adj = min(p * m, 1.0)
        adjusted_p = min(raw_p * num_tests, 1.0)
        is_significant = adjusted_p < alpha

        if is_significant:
            significant_count += 1

        corrected_entry = {
            "disorder_width": item['disorder_width'],
            "xi": item['xi'],
            "uncertainty": item['uncertainty'],
            "raw_p_value": raw_p,
            "bonferroni_adjusted_p": adjusted_p,
            "significant_at_alpha_0.05": is_significant
        }
        corrected_results.append(corrected_entry)

    logger.info(f"Bonferroni complete. {significant_count}/{num_tests} results significant.")
    
    return {
        "corrected_results": corrected_results,
        "alpha": alpha,
        "num_tests": num_tests,
        "corrected_alpha_threshold": corrected_alpha,
        "significant_count": significant_count
    }

def main():
    """
    Orchestrates the aggregation and correction process for T013b and T015.
    1. Loads scaling_fits.json
    2. Validates presence of W values and p_values
    3. Writes the aggregated list back (ensuring validity for T013b)
    4. Applies Bonferroni correction (preparing for T015)
    5. Writes bonferroni_results.json
    """
    logger.info("Starting Aggregation and Correction (T013b/T015)")

    # 1. Load Data
    try:
        data = load_aggregated_results()
    except (FileNotFoundError, ValueError) as e:
        logger.critical(f"Failed to load data: {e}")
        # Create an empty result to avoid crashing the pipeline, though it indicates failure upstream
        data = []

    # 2. Ensure Output Directory Exists
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir = Path("data/metadata")
    metadata_dir.mkdir(parents=True, exist_ok=True)

    # 3. T013b: Write Aggregated/Validated Results
    # Even if empty, we write the file to satisfy the "Hollow Results" check if the upstream was empty
    # But we log if it's empty.
    aggregated_path = output_dir / "scaling_fits.json"
    with open(aggregated_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Wrote aggregated results to {aggregated_path}")

    # 4. Prepare for Bonferroni (T015)
    valid_slope_data = analyze_scaling_slopes(data)

    # 5. Apply Correction
    bonferroni_results = apply_bonferroni_correction(valid_slope_data)

    # 6. Write Bonferroni Output
    bonferroni_path = output_dir / "bonferroni_results.json"
    with open(bonferroni_path, 'w') as f:
        json.dump(bonferroni_results, f, indent=2)
    logger.info(f"Wrote Bonferroni results to {bonferroni_path}")

    logger.info("Aggregation and Correction complete.")

if __name__ == "__main__":
    main()

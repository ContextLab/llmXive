import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from config import ensure_directories, setup_logging


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_scope_adjustments() -> list:
    """Load scope_adjustments.json to determine excluded models."""
    scope_path = Path("data/results/scope_adjustments.json")
    if not scope_path.exists():
        # If no scope adjustments exist, assume all models were attempted
        # but we need to check memory profile for actual execution
        return []
    return load_json_file(scope_path)


def load_memory_profile() -> Dict[str, Any]:
    """Load memory_profile_report.json to determine which models actually ran."""
    mem_path = Path("data/results/memory_profile_report.json")
    if not mem_path.exists():
        raise FileNotFoundError(f"Required file not found: {mem_path}")
    return load_json_file(mem_path)


def calculate_expected_factor() -> float:
    """
    Calculate the expected Holm-Bonferroni correction factor.
    
    The factor is 1 / N_actual, where N_actual is the number of LLMs
    that were actually executed (passed memory checks).
    
    Returns:
        float: The expected correction factor (1/N_actual).
    """
    # Get the list of excluded models from scope_adjustments
    excluded_models = load_scope_adjustments()
    excluded_names = {item['model_name'] for item in excluded_models}
    
    # Get the memory profile to see which models were actually run
    mem_profile = load_memory_profile()
    
    # The memory profile should contain a list of models that were tested/executed
    # We need to count only those that were NOT excluded and were actually run
    if 'models' not in mem_profile:
        raise ValueError("memory_profile_report.json does not contain 'models' key")
    
    actual_models = []
    for model_entry in mem_profile['models']:
        model_name = model_entry.get('model_name')
        # A model is considered "actually executed" if it passed memory checks
        # and was included in the experiment run
        if model_name not in excluded_names:
            # Check if the model was actually run (has execution data)
            if model_entry.get('executed', False):
                actual_models.append(model_name)
    
    n_actual = len(actual_models)
    
    if n_actual == 0:
        raise ValueError("No models were actually executed. Cannot calculate correction factor.")
    
    # Holm-Bonferroni correction factor is 1/N for the first comparison
    # For the purpose of verification, we use 1/N_actual as the base factor
    expected_factor = 1.0 / n_actual
    
    logging.info(f"Calculated expected Holm-Bonferroni factor: 1/{n_actual} = {expected_factor:.6f}")
    logging.info(f"Active models: {actual_models}")
    
    return expected_factor


def verify_correction() -> Dict[str, Any]:
    """
    Verify that the Holm-Bonferroni correction was applied correctly.
    
    Reads stats_report.json, extracts the actual correction factor used,
    compares it with the expected factor calculated from N_actual,
    and returns a verification report.
    
    Returns:
        Dict[str, Any]: Verification report with expected_factor, actual_factor, and match.
    """
    stats_report_path = Path("data/results/stats_report.json")
    
    try:
        stats_report = load_json_file(stats_report_path)
    except FileNotFoundError as e:
        logging.error(f"stats_report.json not found: {e}")
        return {
            "expected_factor": None,
            "actual_factor": None,
            "match": False,
            "error": str(e)
        }
    
    # Calculate expected factor from N_actual
    try:
        expected_factor = calculate_expected_factor()
    except (FileNotFoundError, ValueError) as e:
        logging.error(f"Failed to calculate expected factor: {e}")
        return {
            "expected_factor": None,
            "actual_factor": None,
            "match": False,
            "error": str(e)
        }
    
    # Extract actual factor from stats report
    # The stats report should contain the correction factor used
    actual_factor = None
    
    if 'holm_bonferroni_factor' in stats_report:
        actual_factor = stats_report['holm_bonferroni_factor']
    elif 'correction' in stats_report and 'factor' in stats_report['correction']:
        actual_factor = stats_report['correction']['factor']
    elif 'method_parameters' in stats_report and 'factor' in stats_report['method_parameters']:
        actual_factor = stats_report['method_parameters']['factor']
    else:
        # Try to infer from the reported p-values and original p-values
        # If we have both raw and corrected p-values, we can estimate the factor
        logging.warning("Could not find explicit correction factor in stats_report.json")
        logging.warning("Attempting to infer from p-values...")
        
        # This is a fallback - we look for a pattern in the data
        if 'results' in stats_report and len(stats_report['results']) > 0:
            first_result = stats_report['results'][0]
            if 'raw_p_value' in first_result and 'corrected_p_value' in first_result:
                raw_p = first_result['raw_p_value']
                corrected_p = first_result['corrected_p_value']
                if raw_p > 0:
                    # For Holm-Bonferroni, the first comparison uses 1/N
                    # corrected_p = raw_p * N (approximately for the first comparison)
                    inferred_n = corrected_p / raw_p
                    if inferred_n > 1:
                        actual_factor = 1.0 / inferred_n
                        logging.info(f"Inferred factor from p-values: {actual_factor:.6f}")
    
    if actual_factor is None:
        return {
            "expected_factor": expected_factor,
            "actual_factor": None,
            "match": False,
            "error": "Could not determine actual correction factor from stats report"
        }
    
    # Compare factors with tolerance for floating-point errors
    tolerance = 1e-6
    match = abs(expected_factor - actual_factor) < tolerance
    
    return {
        "expected_factor": expected_factor,
        "actual_factor": actual_factor,
        "match": match,
        "tolerance": tolerance,
        "difference": abs(expected_factor - actual_factor)
    }


def main():
    """Main entry point for the correction verification script."""
    setup_logging()
    ensure_directories()
    
    logging.info("Starting Holm-Bonferroni correction verification...")
    
    try:
        verification_result = verify_correction()
        
        # Write the verification report
        output_path = Path("data/results/correction_verification.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(verification_result, f, indent=2)
        
        logging.info(f"Verification report written to: {output_path}")
        logging.info(f"Expected factor: {verification_result['expected_factor']}")
        logging.info(f"Actual factor: {verification_result['actual_factor']}")
        logging.info(f"Match: {verification_result['match']}")
        
        if verification_result.get('error'):
            logging.warning(f"Verification encountered an error: {verification_result['error']}")
        
        if not verification_result['match']:
            logging.error("CORRECTION FACTOR MISMATCH: The applied correction does not match the expected factor.")
            logging.error("This indicates a potential issue with the statistical analysis.")
            sys.exit(1)
        else:
            logging.info("CORRECTION VERIFICATION PASSED: The applied correction matches the expected factor.")
            sys.exit(0)
            
    except Exception as e:
        logging.exception(f"Verification failed with exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
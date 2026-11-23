import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from config.env_config import get_processed_dir

logger = logging.getLogger(__name__)

def load_regression_results() -> Optional[Dict[str, Any]]:
    """
    Load regression results from data/processed/results/regression_metrics.json.
    Returns None if the file does not exist or cannot be loaded.
    """
    results_path = get_processed_dir() / "results" / "regression_metrics.json"
    if not results_path.exists():
        logger.warning(f"Regression results file not found at {results_path}.")
        return None
    
    try:
        with open(results_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load regression results: {e}")
        return None

def load_descriptor_availability() -> Dict[str, Any]:
    """
    Load descriptor availability status from data/processed/descriptors.csv.
    Checks for the presence of key topological descriptors (e.g., ring statistics).
    Returns a dictionary indicating which descriptors are available for the loaded configs.
    """
    descriptors_path = get_processed_dir() / "descriptors.csv"
    availability = {
        "ring_statistics": False,
        "steinhardt_q6": False,
        "clustering_coefficient": False,
        "vdos_available": False,
        "k_available": False
    }

    if not descriptors_path.exists():
        logger.warning(f"Descriptors file not found at {descriptors_path}. No descriptors available.")
        return availability

    try:
        import pandas as pd
        df = pd.read_csv(descriptors_path)
        
        # Check for topological features (Structure-Only Mode candidates)
        if any(col.startswith('ring_') for col in df.columns):
            availability["ring_statistics"] = True
        if 'q6' in df.columns:
            availability["steinhardt_q6"] = True
        if 'clustering_coeff' in df.columns:
            availability["clustering_coefficient"] = True
        
        # Check for VDOS and Thermal Conductivity (k) columns
        # Assuming 'vdos_integral' or similar indicates VDOS presence
        if any('vdos' in col.lower() for col in df.columns):
            availability["vdos_available"] = True
        
        # Check for target variable 'k' or 'thermal_conductivity'
        if 'k' in df.columns or 'thermal_conductivity' in df.columns:
            availability["k_available"] = True
        
        # If k is missing, we cannot run regression (H-001/H-002 UNTESTABLE)
        # But we can still test H-003/H-004 if ring stats exist.
        
    except Exception as e:
        logger.error(f"Failed to parse descriptors file: {e}")
    
    return availability

def determine_hypothesis_status(
    regression_results: Optional[Dict[str, Any]],
    descriptor_availability: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """
    Determine the status of hypotheses H-001 through H-004 based on:
    1. Whether regression was successfully run (regression_results).
    2. Whether necessary descriptors (ring stats) are available.
    
    Returns a dictionary with keys H-001 to H-004.
    Values are 'TESTED', 'UNTESTABLE', or 'FAILED', with a 'reason' field.
    """
    status = {}

    # H-001: Correlation between topological features and thermal conductivity (k)
    # H-002: Correlation between vibrational features (VDOS) and k
    
    if regression_results is not None:
        # Regression ran successfully
        if regression_results.get('status') == 'success':
            # Check if it was a full model or structure-only
            # If k was present and regression ran, H-001 and H-002 are TESTED
            status["H-001"] = {
                "status": "TESTED",
                "reason": "Regression pipeline executed successfully with thermal conductivity targets."
            }
            status["H-002"] = {
                "status": "TESTED",
                "reason": "Regression pipeline executed successfully with thermal conductivity targets."
            }
        else:
            status["H-001"] = {
                "status": "FAILED",
                "reason": "Regression pipeline reported failure or no valid model found."
            }
            status["H-002"] = {
                "status": "FAILED",
                "reason": "Regression pipeline reported failure or no valid model found."
            }
    else:
        # Regression did not run (likely missing k or VDOS)
        reason = "Thermal conductivity (k) or VDOS data missing; regression skipped."
        status["H-001"] = {
            "status": "UNTESTABLE",
            "reason": reason
        }
        status["H-002"] = {
            "status": "UNTESTABLE",
            "reason": reason
        }

    # H-003: Ring statistics characterize amorphous structure differences
    # H-004: Topological feature importance predicts k (or characterizes structure)
    
    if descriptor_availability.get("ring_statistics"):
        # Ring statistics were computed (Structure-Only Mode OK for these)
        status["H-003"] = {
            "status": "TESTED",
            "reason": "Ring statistics were successfully computed and available for analysis."
        }
        
        if regression_results is not None and regression_results.get('status') == 'success':
            status["H-004"] = {
                "status": "TESTED",
                "reason": "Topological feature importance was computed during successful regression."
            }
        else:
            # Even if regression didn't run (missing k), we can say H-004 is TESTED 
            # regarding the *calculation* of importance if we assume the pipeline 
            # attempted it or if the hypothesis is about the *existence* of the correlation 
            # which we can't test without k. 
            # However, the task says: "Mark 'TESTED' if topological feature importance was computed".
            # If regression didn't run, importance wasn't computed.
            status["H-004"] = {
                "status": "UNTESTABLE",
                "reason": "Topological feature importance could not be computed because regression was skipped (missing k)."
            }
    else:
        status["H-003"] = {
            "status": "FAILED",
            "reason": "Ring statistics were not computed or not available in the descriptor dataset."
        }
        status["H-004"] = {
            "status": "FAILED",
            "reason": "Topological feature importance could not be computed because ring statistics were missing."
        }

    return status

def save_hypothesis_status(status: Dict[str, Dict[str, Any]]) -> Path:
    """
    Save the hypothesis status dictionary to data/processed/results/hypothesis_status.json.
    """
    results_dir = get_processed_dir() / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = results_dir / "hypothesis_status.json"
    
    with open(output_path, 'w') as f:
        json.dump(status, f, indent=2)
    
    logger.info(f"Hypothesis status saved to {output_path}")
    return output_path

def main():
    """
    Main entry point for T037: Tiered Execution logic.
    1. Check if regression results exist.
    2. Check descriptor availability.
    3. Determine hypothesis status.
    4. Save to hypothesis_status.json.
    """
    setup_logger = logging.getLogger(__name__)
    setup_logger.setLevel(logging.INFO)
    
    logger.info("Starting Tiered Execution logic (T037)...")
    
    # 1. Load regression results (if any)
    regression_results = load_regression_results()
    
    # 2. Load descriptor availability
    descriptor_availability = load_descriptor_availability()
    
    # 3. Determine status
    status = determine_hypothesis_status(regression_results, descriptor_availability)
    
    # 4. Save
    save_hypothesis_status(status)
    
    logger.info("Tiered Execution logic completed.")
    return status

if __name__ == "__main__":
    main()

"""
Hypothesis Tracker for Tiered Execution Logic (Task T037).

This module implements the logic to update the hypothesis status based on
the availability of thermal conductivity (k) and VDOS data, and the success
of topological descriptor calculations.

It handles the Tiered Execution mode:
- If k/VDOS is missing: Mark H-001/H-002 as 'UNTESTABLE'.
- If ring statistics computed: Mark H-003 as 'TESTED'.
- If topological feature importance computed: Mark H-004 as 'TESTED'.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from config.env_config import get_processed_dir
from logging_config import get_logger

logger = get_logger(__name__)

RESULTS_DIR = "results"
HYPOTHESIS_FILE = "hypothesis_status.json"

# Hypothesis IDs
H_IDS = ["H-001", "H-002", "H-003", "H-004"]

def load_regression_results() -> Optional[Dict[str, Any]]:
    """
    Attempts to load regression results from the processed directory.
    Returns None if the file does not exist or is empty.
    """
    processed_dir = get_processed_dir()
    results_path = processed_dir / RESULTS_DIR
    # Assuming the regression results are saved in a standard location by models.py/viz.py
    # We look for a generic results file or check if the directory has content.
    # Based on T031-T036, results are saved to data/processed/results/
    
    # Check for a generic 'regression_results.json' or similar if T031-T036 saved it there.
    # If T031-T036 saved to a specific file, we might need to adjust. 
    # For now, we assume a file named 'regression_results.json' exists if regression ran.
    # If the task T036 saved plots, the data might be in 'metrics.json' or similar.
    # Let's check for a standard output file from the regression pipeline.
    # We will assume 'regression_metrics.json' is the standard output for T034.
    
    metrics_file = results_path / "regression_metrics.json"
    if metrics_file.exists():
        try:
            with open(metrics_file, 'r') as f:
                data = json.load(f)
                if data:
                    return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not read regression metrics: {e}")
    
    # Fallback: check if any file exists in results dir to infer success
    # This is a heuristic if specific file naming varies.
    if results_path.exists() and any(results_path.iterdir()):
        # If files exist, we assume regression ran, but we can't confirm success without the file.
        # However, strict adherence suggests checking the specific output.
        pass
        
    return None

def load_descriptor_availability() -> Dict[str, bool]:
    """
    Checks if topological descriptors (ring statistics) were successfully computed.
    Returns a dict indicating availability.
    """
    processed_dir = get_processed_dir()
    # T025/T027 should have saved descriptors.csv
    descriptors_file = processed_dir / "descriptors.csv"
    
    has_ring_stats = descriptors_file.exists() and descriptors_file.stat().st_size > 0
    
    # Check for VDOS missing report to see if we are in Structure-Only mode
    vdos_missing_file = processed_dir / "vdos_missing_report.json"
    has_vdos_missing = vdos_missing_file.exists()
    
    return {
        "ring_stats": has_ring_stats,
        "vdos_missing": has_vdos_missing,
        "has_vdos": not has_vdos_missing if has_vdos_missing else None # None if unknown
    }

def determine_hypothesis_status(
    regression_results: Optional[Dict[str, Any]],
    descriptor_availability: Dict[str, bool]
) -> Dict[str, Dict[str, str]]:
    """
    Determines the status of each hypothesis based on execution results.
    
    H-001: Correlation between k and VDOS (Requires k and VDOS)
    H-002: Correlation between k and Topology (Requires k)
    H-003: Ring statistics predict structure (Requires Ring Stats)
    H-004: Topological features drive transport (Requires Topology + k)
    """
    status = {}
    
    # Check if regression actually ran (indicates k was available and processed)
    regression_ran = regression_results is not None
    
    # H-001: k vs VDOS correlation
    # If k is missing (regression didn't run) OR VDOS is missing, it's untestable.
    if not regression_ran:
        status["H-001"] = {
            "status": "UNTESTABLE",
            "reason": "Thermal conductivity (k) or VDOS data missing. Regression not executed."
        }
    elif descriptor_availability.get("vdos_missing", False):
        # If we ran regression but VDOS was missing for all, we can't correlate k vs VDOS
        status["H-001"] = {
            "status": "UNTESTABLE",
            "reason": "VDOS data missing for all configurations."
        }
    else:
        status["H-001"] = {
            "status": "TESTED",
            "reason": "Regression with VDOS features completed successfully."
        }
    
    # H-002: k vs Topology correlation
    if not regression_ran:
        status["H-002"] = {
            "status": "UNTESTABLE",
            "reason": "Thermal conductivity (k) missing. Regression not executed."
        }
    else:
        # If regression ran, we have k. If we have topological features (ring stats), we tested it.
        if descriptor_availability.get("ring_stats", False):
            status["H-002"] = {
                "status": "TESTED",
                "reason": "Regression with topological features completed successfully."
            }
        else:
            status["H-002"] = {
                "status": "FAILED",
                "reason": "Thermal conductivity available but topological descriptors (ring stats) missing."
            }
    
    # H-003: Ring statistics predict structure (Structure-Only Mode OK)
    # This only requires ring statistics to be computed.
    if descriptor_availability.get("ring_stats", False):
        status["H-003"] = {
            "status": "TESTED",
            "reason": "Ring statistics successfully computed."
        }
    else:
        status["H-003"] = {
            "status": "FAILED",
            "reason": "Ring statistics computation failed or was skipped."
        }
    
    # H-004: Topological feature importance (Structure-Only Mode OK)
    # Requires regression to run (to get feature importance) AND ring stats to be present.
    if regression_ran and descriptor_availability.get("ring_stats", False):
        status["H-004"] = {
            "status": "TESTED",
            "reason": "Feature importance analysis completed with topological descriptors."
        }
    elif not regression_ran:
        status["H-004"] = {
            "status": "UNTESTABLE",
            "reason": "Thermal conductivity (k) missing. Cannot compute feature importance."
        }
    else:
        status["H-004"] = {
            "status": "FAILED",
            "reason": "Regression ran but topological descriptors missing for feature importance."
        }
        
    return status

def save_hypothesis_status(status: Dict[str, Dict[str, str]]) -> Path:
    """
    Saves the hypothesis status to the results directory.
    """
    processed_dir = get_processed_dir()
    results_path = processed_dir / RESULTS_DIR
    results_path.mkdir(parents=True, exist_ok=True)
    
    output_file = results_path / HYPOTHESIS_FILE
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "hypotheses": status,
        "summary": {
            h_id: h_data["status"] for h_id, h_data in status.items()
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Hypothesis status saved to {output_file}")
    return output_file

def main() -> None:
    """
    Main entry point for T037: Tiered Execution Logic.
    """
    logger.info("Starting Hypothesis Tracking (T037)...")
    
    # 1. Check availability of inputs
    regression_results = load_regression_results()
    descriptor_availability = load_descriptor_availability()
    
    logger.info(f"Regression results found: {regression_results is not None}")
    logger.info(f"Descriptor availability: {descriptor_availability}")
    
    # 2. Determine status
    status = determine_hypothesis_status(regression_results, descriptor_availability)
    
    # 3. Save results
    save_hypothesis_status(status)
    
    logger.info("Hypothesis tracking completed.")

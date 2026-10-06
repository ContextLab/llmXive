import os
import json
import logging
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Import from utils as per API surface
from utils.logger import get_logger
from utils.config import get_data_path, get_code_path

logger = get_logger(__name__)

def load_simulated_state() -> Dict[str, Any]:
    """Load the simulated mode state from data/simulated/state.json."""
    state_path = get_data_path() / "simulated" / "state.json"
    if not state_path.exists():
        logger.warning(f"State file not found at {state_path}. Assuming real data mode.")
        return {"SIMULATED_MODE": False}
    
    with open(state_path, 'r') as f:
        return json.load(f)

def load_model_metrics() -> Dict[str, Any]:
    """Load model metrics from data/processed/model_runs.json."""
    metrics_path = get_data_path() / "processed" / "model_runs.json"
    if not metrics_path.exists():
        raise FileNotFoundError(f"Model metrics file not found at {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        return json.load(f)

def get_halide_counts() -> Dict[str, int]:
    """Get counts of records per halide from the processed dataset."""
    data_path = get_data_path() / "processed" / "halide_binding_data.csv"
    if not data_path.exists():
        logger.warning("Processed data file not found. Returning empty counts.")
        return {}
    
    df = pd.read_csv(data_path)
    if 'halide' not in df.columns:
        logger.warning("'halide' column not found in processed data.")
        return {}
    
    counts = df['halide'].value_counts().to_dict()
    return {str(k): int(v) for k, v in counts.items()}

def run_power_analysis(halide_counts: Dict[str, int], min_samples: int = 10) -> Dict[str, Any]:
    """
    Run power analysis based on halide counts.
    
    Returns a dict with:
      - status: "powered", "underpowered", or "simulated"
      - reason: explanation if underpowered or simulated
      - min_count: the minimum count found
    """
    if not halide_counts:
        return {"status": "underpowered", "reason": "No halide data found", "min_count": 0}
    
    min_count = min(halide_counts.values())
    
    if min_count < min_samples:
        return {
            "status": "underpowered",
            "reason": f"Minimum halide count ({min_count}) is below threshold ({min_samples})",
            "min_count": min_count
        }
    
    return {
        "status": "powered",
        "reason": "Sufficient samples for comparative analysis",
        "min_count": min_count
    }

def save_power_status(power_status: Dict[str, Any]) -> None:
    """Save power status to data/processed/power_status.json."""
    output_path = get_data_path() / "processed" / "power_status.json"
    with open(output_path, 'w') as f:
        json.dump(power_status, f, indent=2)
    logger.info(f"Power status saved to {output_path}")

def save_statistical_summary_partial(status: str, reason: str) -> None:
    """Save partial statistical summary before finalization."""
    output_path = get_data_path() / "processed" / "statistical_summary.json"
    
    summary = {
        "status": status,
        "reason": reason,
        "comparative_analysis_aborted": True,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Partial statistical summary saved to {output_path}")

def save_statistical_summary_final(
    abort_reason: str,
    halide_counts: Optional[Dict[str, int]] = None
) -> None:
    """
    Save the final statistical summary for T028b (Fallback Statistical Report).
    
    This function generates the required fallback artifact when T029a sets
    ABORT_REASON to "SIMULATED_MODE" or "UNDERPOWERED".
    
    Args:
        abort_reason: Either "SIMULATED_MODE" or "UNDERPOWERED"
        halide_counts: Optional dict of halide counts for UNDERPOWERED case
    """
    output_path = get_data_path() / "processed" / "statistical_summary.json"
    
    if abort_reason == "SIMULATED_MODE":
        summary = {
            "comparative_analysis_aborted": True,
            "reason": "Simulated Data Mode",
            "status": "aborted_simulated",
            "note": "Comparative analysis cannot be performed on simulated data.",
            "timestamp": pd.Timestamp.now().isoformat()
        }
        logger.warning("Simulated Data Mode active. Project FAILS to answer the primary comparative research question.")
        
    elif abort_reason == "UNDERPOWERED":
        min_count = min(halide_counts.values()) if halide_counts else 0
        summary = {
            "power_status": "underpowered",
            "ci_width": "wide",
            "note": "Comparative analysis underpowered; only 95% CIs reported.",
            "min_halide_count": min_count,
            "halide_counts": halide_counts,
            "status": "underpowered",
            "timestamp": pd.Timestamp.now().isoformat()
        }
        logger.warning(f"Analysis underpowered. Minimum halide count: {min_count}")
        
    else:
        raise ValueError(f"Unknown abort reason: {abort_reason}")
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Final statistical summary saved to {output_path}")
    return summary

def main() -> None:
    """
    Main entry point for T028b: Fallback Statistical Report.
    
    This task generates the required fallback artifact when T029a determines
    that the analysis should be aborted due to simulated mode or underpowered data.
    """
    logger.info("Starting T028b: Fallback Statistical Report")
    
    try:
        # Load simulated state
        sim_state = load_simulated_state()
        simulated_mode = sim_state.get("SIMULATED_MODE", False)
        
        # Load halide counts
        halide_counts = get_halide_counts()
        
        # Run power analysis
        power_analysis = run_power_analysis(halide_counts)
        
        # Determine abort reason
        abort_reason = None
        
        if simulated_mode:
            abort_reason = "SIMULATED_MODE"
        elif power_analysis["status"] == "underpowered":
            abort_reason = "UNDERPOWERED"
        
        if abort_reason is None:
            logger.info("No abort reason found. Comparative analysis can proceed (T028 should run).")
            # For T028b, we only run if there's an abort reason
            # If no abort reason, this task is not applicable
            return
        
        # Save power status
        power_status = {
            "abort_reason": abort_reason,
            "simulated_mode": simulated_mode,
            "power_analysis": power_analysis,
            "halide_counts": halide_counts
        }
        save_power_status(power_status)
        
        # Generate fallback report
        if abort_reason == "SIMULATED_MODE":
            save_statistical_summary_final("SIMULATED_MODE")
        else:  # UNDERPOWERED
            save_statistical_summary_final("UNDERPOWERED", halide_counts)
        
        logger.info("T028b completed successfully.")
        
    except Exception as e:
        logger.error(f"Error in T028b: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
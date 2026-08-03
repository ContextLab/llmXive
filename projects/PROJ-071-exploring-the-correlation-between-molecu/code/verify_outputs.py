"""
Verification script for T036: Save all plots to data/outputs/ and final report to results_report.md.
Verifies the existence and non-zero size of required plot files and the report file.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent

def get_data_path() -> Path:
    """Get the data directory."""
    return get_project_root() / "data"

def check_gate_status() -> dict:
    """Read and return the gate status from data/gate_status.json."""
    gate_path = get_data_path() / "gate_status.json"
    if not gate_path.exists():
        logger.warning(f"Gate status file not found: {gate_path}")
        return {"status": "UNKNOWN"}
    
    try:
        with open(gate_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse gate status JSON: {e}")
        return {"status": "UNKNOWN"}

def verify_plot_files(gate_passed: bool) -> bool:
    """
    Verify the existence and non-zero size of required plot files.
    
    Args:
        gate_passed: True if the data gate passed, False otherwise.
        
    Returns:
        True if verification passes, False otherwise.
    """
    outputs_dir = get_data_path() / "outputs"
    required_plots = [
        "scatter_tpsa_vs_half_life.png",
        "residuals.png",
        "qq_plot.png"
    ]
    
    if gate_passed:
        logger.info("Gate PASSED. Verifying that all required plot files exist and have non-zero size.")
        
        if not outputs_dir.exists():
            logger.error(f"Outputs directory does not exist: {outputs_dir}")
            return False
        
        all_valid = True
        for plot_name in required_plots:
            plot_path = outputs_dir / plot_name
            if not plot_path.exists():
                logger.error(f"Required plot file missing: {plot_path}")
                all_valid = False
            else:
                size = plot_path.stat().st_size
                if size == 0:
                    logger.error(f"Plot file exists but is empty (0 bytes): {plot_path}")
                    all_valid = False
                else:
                    logger.info(f"Plot file verified: {plot_path} ({size} bytes)")
        
        if all_valid:
            logger.info("All required plot files verified successfully.")
        else:
            logger.error("Some plot files are missing or empty.")
        
        return all_valid
    else:
        logger.info("Gate FAILED. Verifying that no plot files were generated (as per T032/T033).")
        
        if outputs_dir.exists():
            # Check if any of the required plots exist (they shouldn't)
            found_plots = []
            for plot_name in required_plots:
                plot_path = outputs_dir / plot_name
                if plot_path.exists():
                    found_plots.append(str(plot_path))
            
            if found_plots:
                logger.warning(f"Plot files found despite gate failure (expected none): {found_plots}")
                # This is a warning, not a failure, as the plots might be stale from a previous run
                # but the task logic says "verify no plot files are generated"
                # We'll treat this as a failure of the pipeline logic that generated them
                return False
            else:
                logger.info("No plot files found in outputs directory (as expected for gate failure).")
        else:
            logger.info("Outputs directory does not exist (as expected for gate failure).")
        
        return True

def verify_report(gate_passed: bool) -> bool:
    """
    Verify the existence of the final report file.
    
    Args:
        gate_passed: True if the data gate passed, False otherwise.
        
    Returns:
        True if verification passes, False otherwise.
    """
    project_root = get_project_root()
    
    if gate_passed:
        report_path = project_root / "results_report.md"
        expected_name = "results_report.md"
    else:
        report_path = project_root / "data" / "data_insufficiency_report.md"
        expected_name = "data_insufficiency_report.md"
    
    if not report_path.exists():
        logger.error(f"Required report file missing: {report_path}")
        return False
    
    size = report_path.stat().st_size
    if size == 0:
        logger.error(f"Report file exists but is empty (0 bytes): {report_path}")
        return False
    
    logger.info(f"Report file verified: {report_path} ({size} bytes)")
    return True

def main():
    """Main entry point for T036 verification."""
    logger.info("Starting T036 verification...")
    
    # Check gate status
    gate_status = check_gate_status()
    gate_passed = gate_status.get("status", "").upper() == "PASS"
    
    logger.info(f"Gate status: {'PASS' if gate_passed else 'FAIL'}")
    
    # Verify plots
    plots_ok = verify_plot_files(gate_passed)
    
    # Verify report
    report_ok = verify_report(gate_passed)
    
    # Final result
    if plots_ok and report_ok:
        logger.info("T036 verification PASSED: All required artifacts exist and are valid.")
        sys.exit(0)
    else:
        logger.error("T036 verification FAILED: Some required artifacts are missing or invalid.")
        sys.exit(1)

if __name__ == "__main__":
    main()
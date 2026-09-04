"""
Verification module for T036: Artifact existence and integrity check.
Verifies that the pipeline produced the required outputs based on the gate status.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import logging

# Add project root to path if not already present
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    return PROJECT_ROOT

def get_data_path() -> Path:
    return PROJECT_ROOT / "data"

def check_gate_status() -> dict:
    """Read the gate status from data/gate_status.json."""
    gate_file = get_data_path() / "gate_status.json"
    if not gate_file.exists():
        logger.error(f"Gate status file not found: {gate_file}")
        return {"status": "UNKNOWN", "reason": "File missing"}
    
    try:
        with open(gate_file, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in gate status file: {e}")
        return {"status": "UNKNOWN", "reason": "Invalid JSON"}

def verify_plot_files(gate_status: dict) -> bool:
    """
    Verify plot files based on gate status.
    - If PASS: Check that scatter_tpsa_vs_half_life.png, residuals.png, qq_plot.png exist and have size > 0.
    - If FAIL: Check that NO plot files exist in data/outputs/.
    """
    outputs_dir = get_data_path() / "outputs"
    required_plots = [
        "scatter_tpsa_vs_half_life.png",
        "residuals.png",
        "qq_plot.png"
    ]

    if gate_status.get("status") == "PASS":
        logger.info("Gate PASSED. Verifying existence of required plot files...")
        if not outputs_dir.exists():
            logger.error(f"Outputs directory does not exist: {outputs_dir}")
            return False

        all_good = True
        for plot_name in required_plots:
            plot_path = outputs_dir / plot_name
            if not plot_path.exists():
                logger.error(f"Required plot file missing: {plot_path}")
                all_good = False
            elif plot_path.stat().st_size == 0:
                logger.error(f"Plot file is empty (0 bytes): {plot_path}")
                all_good = False
            else:
                logger.info(f"Verified plot: {plot_name} ({plot_path.stat().st_size} bytes)")
        
        if all_good:
            logger.info("All required plots verified successfully.")
        return all_good

    elif gate_status.get("status") == "FAIL":
        logger.info("Gate FAILED. Verifying that NO plot files were generated...")
        if outputs_dir.exists():
            existing_plots = [p for p in outputs_dir.iterdir() if p.suffix == ".png"]
            if existing_plots:
                logger.error(f"Plot files found in outputs directory despite Gate FAIL: {[p.name for p in existing_plots]}")
                return False
            else:
                logger.info("No plot files found in outputs directory (correct behavior for Gate FAIL).")
                return True
        else:
            logger.info("Outputs directory does not exist (correct behavior for Gate FAIL).")
            return True

    else:
        logger.warning(f"Unknown gate status: {gate_status.get('status')}. Skipping plot verification.")
        return True

def verify_report(gate_status: dict) -> bool:
    """
    Verify the report file based on gate status.
    - If PASS: Check that results_report.md exists and is non-empty.
    - If FAIL: Check that data_insufficiency_report.md exists and is non-empty.
    """
    if gate_status.get("status") == "PASS":
        report_path = get_project_root() / "results_report.md"
        if not report_path.exists():
            logger.error(f"Report file missing: {report_path}")
            return False
        if report_path.stat().st_size == 0:
            logger.error(f"Report file is empty: {report_path}")
            return False
        
        # Verify content includes expected sections
        content = report_path.read_text()
        if "Methodology" not in content or "Results" not in content:
            logger.warning("Report file exists but may be missing mandatory sections.")
            # Not a hard fail for existence, but a warning
        
        logger.info(f"Verified report: results_report.md ({report_path.stat().st_size} bytes)")
        return True

    elif gate_status.get("status") == "FAIL":
        report_path = get_project_root() / "data" / "data_insufficiency_report.md"
        if not report_path.exists():
            logger.error(f"Insufficiency report file missing: {report_path}")
            return False
        if report_path.stat().st_size == 0:
            logger.error(f"Insufficiency report file is empty: {report_path}")
            return False

        content = report_path.read_text()
        if "Insufficient" not in content and "Insufficiency" not in content:
            logger.warning("Insufficiency report file exists but may not contain expected keywords.")
        
        logger.info(f"Verified insufficiency report: data_insufficiency_report.md ({report_path.stat().st_size} bytes)")
        return True

    else:
        logger.warning(f"Unknown gate status: {gate_status.get('status')}. Skipping report verification.")
        return True

def main():
    """Main entry point for T036 verification."""
    logger.info("Starting T036 Artifact Verification...")
    
    gate_status = check_gate_status()
    if gate_status.get("status") == "UNKNOWN":
        logger.error("Cannot proceed with verification due to unknown gate status.")
        sys.exit(1)

    plots_ok = verify_plot_files(gate_status)
    report_ok = verify_report(gate_status)

    if plots_ok and report_ok:
        logger.info("T036 Verification PASSED: All required artifacts are present and valid.")
        sys.exit(0)
    else:
        logger.error("T036 Verification FAILED: Some required artifacts are missing or invalid.")
        sys.exit(1)

if __name__ == '__main__':
    main()

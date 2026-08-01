"""Verification of final pipeline outputs for T036."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import logging

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

from logging_config import log_operation, get_logger

logger = get_logger("verify_outputs")

def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent

def get_data_path() -> Path:
    return get_project_root() / "data"

def check_gate_status() -> dict:
    """Read gate_status.json to determine if the data gate passed."""
    gate_path = get_data_path() / "gate_status.json"
    if not gate_path.exists():
        logger.log("gate_check", status="MISSING", path=str(gate_path))
        return {"status": "FAIL", "reason": "gate_status.json not found"}
    
    with open(gate_path, "r") as f:
        return json.load(f)

def verify_plot_files(gate_passed: bool) -> bool:
    """
    Verify existence and content of required plot files.
    - If gate passed: files must exist and have non-zero size.
    - If gate failed: files must exist, be non-zero, and contain "N/A" or "Insufficient" text.
    """
    outputs_dir = get_data_path() / "outputs"
    required_plots = [
        "scatter_tpsa_vs_half_life.png",
        "residuals.png",
        "qq_plot.png"
    ]

    all_ok = True
    for plot_name in required_plots:
        plot_path = outputs_dir / plot_name
        
        if not plot_path.exists():
            logger.log("verify_plot", file=plot_name, status="MISSING")
            all_ok = False
            continue

        size = plot_path.stat().st_size
        if size == 0:
            logger.log("verify_plot", file=plot_name, status="EMPTY")
            all_ok = False
            continue

        if gate_passed:
            # For PASS, just ensure non-zero (binary check is sufficient)
            logger.log("verify_plot", file=plot_name, status="OK", size=size)
        else:
            # For FAIL, we need to check if it's a placeholder.
            # Since PNGs are binary, we check for the "N/A" string in the raw bytes
            # (assuming the placeholder generator embeds text).
            try:
                content = plot_path.read_bytes()
                # Check for common placeholder markers
                if b"N/A" in content or b"Insufficient" in content or b"Data Insufficient" in content:
                    logger.log("verify_plot", file=plot_name, status="PLACEHOLDER_OK", size=size)
                else:
                    # If it's a real image but gate failed, that's a logic error in viz.py
                    # But we accept it if it's non-zero for now, or fail if strict.
                    # Task says: "verify each plot file contains the 'N/A' placeholder text"
                    logger.log("verify_plot", file=plot_name, status="MISSING_PLACEHOLDER_TEXT", size=size)
                    all_ok = False
            except Exception as e:
                logger.log("verify_plot", file=plot_name, status="READ_ERROR", error=str(e))
                all_ok = False

    return all_ok

def verify_report(gate_passed: bool) -> bool:
    """
    Verify existence and content of final report.
    - If gate passed: results_report.md must exist and be non-empty.
    - If gate failed: data_insufficiency_report.md must exist and contain "Insufficient".
    """
    project_root = get_project_root()
    
    if gate_passed:
        report_path = project_root / "results_report.md"
        expected_name = "results_report.md"
    else:
        report_path = project_root / "data" / "data_insufficiency_report.md"
        expected_name = "data_insufficiency_report.md"

    if not report_path.exists():
        logger.log("verify_report", file=expected_name, status="MISSING")
        return False

    size = report_path.stat().st_size
    if size == 0:
        logger.log("verify_report", file=expected_name, status="EMPTY")
        return False

    if not gate_passed:
        # Check for specific content
        content = report_path.read_text()
        if "Insufficient" not in content and "N/A" not in content:
            logger.log("verify_report", file=expected_name, status="MISSING_CONTENT")
            return False
    
    logger.log("verify_report", file=expected_name, status="OK", size=size)
    return True

def main():
    """Main entry point for T036 verification."""
    log_operation("T036_Verification_Start")
    
    gate = check_gate_status()
    gate_passed = gate.get("status") == "PASS"
    
    logger.log("Gate_Check", status=gate.get("status"), N=gate.get("N"))

    plots_ok = verify_plot_files(gate_passed)
    report_ok = verify_report(gate_passed)

    if plots_ok and report_ok:
        logger.log("T036_Verification_Complete", status="SUCCESS")
        print("T036 Verification: PASSED")
        sys.exit(0)
    else:
        logger.log("T036_Verification_Complete", status="FAILED")
        print("T036 Verification: FAILED - Missing or invalid artifacts")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
Verification script for T084: Report Compliance.

This script performs a manual review (automated check) of the final report
to ensure:
1. All FDR-corrected p-values are presented.
2. Partial dependence plots are included (files exist).
3. Collinearity condition number is discussed.

It exits with code 0 if all checks pass, or code 1 if any check fails.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Tuple, Any

# Ensure code directory is in path for imports if running from root
code_dir = Path(__file__).resolve().parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config.config import get_config
from analyze import get_project_root

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("verify_report_compliance")

def check_fdr_pvalues(report_path: Path, fdr_pvalues_path: Path) -> Tuple[bool, str]:
    """
    Checks if the report mentions FDR-corrected p-values and if the source file exists.
    """
    if not fdr_pvalues_path.exists():
        return False, f"FDR p-values file not found: {fdr_pvalues_path}"

    try:
        with open(fdr_pvalues_path, 'r') as f:
            data = json.load(f)
            if 'corrected_pvalues' not in data:
                return False, "FDR p-values file missing 'corrected_pvalues' key"
    except Exception as e:
        return False, f"Error reading FDR p-values file: {e}"

    if not report_path.exists():
        return False, f"Report file not found: {report_path}"

    with open(report_path, 'r') as f:
        content = f.read()

    # Check for presence of FDR discussion or data
    keywords = ["FDR", "Benjamini-Hochberg", "corrected p-value", "adjusted p-value"]
    found = any(kw.lower() in content.lower() for kw in keywords)

    if not found:
        return False, "Report does not appear to discuss FDR-corrected p-values."

    return True, "FDR-corrected p-values verification passed."

def check_partial_dependence_plots(report_path: Path, artifacts_dir: Path) -> Tuple[bool, str]:
    """
    Checks if the report mentions PDPs and if the plot files exist.
    """
    required_plots = [
        "pdp_radius_mismatch.png",
        "pdp_vec.png",
        "pdp_electronegativity.png"
    ]
    
    missing_plots = []
    for plot_name in required_plots:
        plot_path = artifacts_dir / "reports" / plot_name
        if not plot_path.exists():
            missing_plots.append(plot_name)

    if missing_plots:
        return False, f"Missing PDP plot files: {', '.join(missing_plots)}"

    if not report_path.exists():
        return False, f"Report file not found: {report_path}"

    with open(report_path, 'r') as f:
        content = f.read()

    # Check for mention of plots
    if "partial dependence" not in content.lower() and "pdp" not in content.lower():
        return False, "Report does not appear to discuss partial dependence plots."

    return True, "Partial dependence plots verification passed."

def check_collinearity_condition_number(report_path: Path, collinearity_log_path: Path) -> Tuple[bool, str]:
    """
    Checks if the report discusses collinearity and if the log file exists.
    """
    if not collinearity_log_path.exists():
        return False, f"Collinearity log file not found: {collinearity_log_path}"

    try:
        with open(collinearity_log_path, 'r') as f:
            data = json.load(f)
            if 'condition_number' not in data:
                return False, "Collinearity log missing 'condition_number' key"
    except Exception as e:
        return False, f"Error reading collinearity log: {e}"

    if not report_path.exists():
        return False, f"Report file not found: {report_path}"

    with open(report_path, 'r') as f:
        content = f.read()

    # Check for discussion of collinearity or condition number
    keywords = ["collinearity", "condition number", "multicollinearity"]
    found = any(kw.lower() in content.lower() for kw in keywords)

    if not found:
        return False, "Report does not appear to discuss collinearity or condition number."

    return True, "Collinearity condition number verification passed."

def main():
    logger.info("Starting T084 Report Compliance Verification...")
    
    project_root = get_project_root()
    artifacts_dir = project_root / "artifacts"
    reports_dir = artifacts_dir / "reports"
    processed_dir = project_root / "data" / "processed"

    report_path = reports_dir / "final_report.md"
    fdr_pvalues_path = processed_dir / "fdr_corrected_pvalues.json"
    collinearity_log_path = processed_dir / "collinearity_log.json"

    all_passed = True
    checks = [
        ("FDR Corrected P-Values", check_fdr_pvalues(report_path, fdr_pvalues_path)),
        ("Partial Dependence Plots", check_partial_dependence_plots(report_path, artifacts_dir)),
        ("Collinearity Condition Number", check_collinearity_condition_number(report_path, collinearity_log_path))
    ]

    for check_name, (passed, message) in checks:
        if passed:
            logger.info(f"[PASS] {check_name}: {message}")
        else:
            logger.error(f"[FAIL] {check_name}: {message}")
            all_passed = False

    if all_passed:
        logger.info("All compliance checks passed. Report is compliant.")
        sys.exit(0)
    else:
        logger.error("Compliance checks failed. Please review the report.")
        sys.exit(1)

if __name__ == "__main__":
    main()
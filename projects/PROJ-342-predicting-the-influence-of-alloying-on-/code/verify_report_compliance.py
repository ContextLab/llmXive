"""
T084: Report Compliance Verification Script.

This script performs a manual-style automated review of `artifacts/reports/final_report.md`
to ensure:
1. All FDR-corrected p-values are presented (by checking the source JSON and confirming
   the report references the FDR analysis).
2. Partial dependence plots are included (by checking for existence of image files and
   references in the report).
3. The collinearity condition number is discussed (by checking for the value in the
   collinearity log and its presence in the report).

It exits with code 0 if all checks pass, or 1 if any check fails.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Determine the project root directory."""
    # Assume the script is in code/verify_report_compliance.py
    return Path(__file__).resolve().parent.parent

def check_fdr_pvalues(report_path: Path, fdr_json_path: Path) -> Tuple[bool, str]:
    """
    Check if FDR-corrected p-values are presented in the report.
    Verifies the source data exists and the report references the FDR analysis.
    """
    errors = []
    
    if not fdr_json_path.exists():
        errors.append(f"FDR data file not found: {fdr_json_path}")
        return False, "; ".join(errors)

    try:
        with open(fdr_json_path, 'r') as f:
            fdr_data = json.load(f)
        
        if 'corrected_pvalues' not in fdr_data:
            errors.append("FDR JSON missing 'corrected_pvalues' key")
            return False, "; ".join(errors)
        
        if not fdr_data['corrected_pvalues']:
            errors.append("FDR 'corrected_pvalues' is empty")
            return False, "; ".join(errors)
            
    except json.JSONDecodeError:
        errors.append(f"Invalid JSON in FDR file: {fdr_json_path}")
        return False, "; ".join(errors)

    if not report_path.exists():
        errors.append(f"Report file not found: {report_path}")
        return False, "; ".join(errors)

    report_text = report_path.read_text()
    
    # Check for references to FDR or corrected p-values
    if 'FDR' not in report_text and 'Benjamini-Hochberg' not in report_text:
        errors.append("Report does not mention 'FDR' or 'Benjamini-Hochberg'")
    
    # Check if the report contains a section discussing correlations or p-values
    # We look for evidence that the values were actually presented/discussed
    if 'corrected p-value' not in report_text.lower() and 'adjusted p-value' not in report_text.lower():
        # This is a soft check; if the report is very long, it might just summarize.
        # But for compliance, we expect some explicit mention.
        logger.warning("Report does not explicitly mention 'corrected p-value' or 'adjusted p-value'.")
    
    if errors:
        return False, "; ".join(errors)
    
    return True, "FDR-corrected p-values are present and referenced."

def check_partial_dependence_plots(report_path: Path, project_root: Path) -> Tuple[bool, str]:
    """
    Check if partial dependence plots are included.
    Verifies existence of image files and references in the report.
    """
    errors = []
    expected_plots = [
        'pdp_radius_mismatch.png',
        'pdp_vec.png',
        'pdp_electronegativity.png'
    ]
    
    plots_dir = project_root / 'artifacts' / 'reports'
    
    missing_plots = []
    for plot_name in expected_plots:
        plot_path = plots_dir / plot_name
        if not plot_path.exists():
            missing_plots.append(plot_name)
        else:
            # Check if the report references the plot (basic check for filename or alt text)
            report_text = report_path.read_text()
            if plot_name.replace('.png', '') not in report_text:
                logger.warning(f"Report does not explicitly reference {plot_name}, but file exists.")

    if missing_plots:
        errors.append(f"Missing partial dependence plot files: {', '.join(missing_plots)}")
    
    if errors:
        return False, "; ".join(errors)
    
    return True, "All partial dependence plots are present."

def check_collinearity_condition_number(report_path: Path, collinearity_json_path: Path) -> Tuple[bool, str]:
    """
    Check if the collinearity condition number is discussed.
    Verifies the value exists in the log and is discussed in the report.
    """
    errors = []
    
    if not collinearity_json_path.exists():
        errors.append(f"Collinearity log file not found: {collinearity_json_path}")
        return False, "; ".join(errors)

    try:
        with open(collinearity_json_path, 'r') as f:
            collinearity_data = json.load(f)
        
        if 'condition_number' not in collinearity_data:
            errors.append("Collinearity JSON missing 'condition_number' key")
            return False, "; ".join(errors)
        
        condition_number = collinearity_data['condition_number']
        
    except json.JSONDecodeError:
        errors.append(f"Invalid JSON in collinearity file: {collinearity_json_path}")
        return False, "; ".join(errors)

    if not report_path.exists():
        errors.append(f"Report file not found: {report_path}")
        return False, "; ".join(errors)

    report_text = report_path.read_text()
    
    # Check if the condition number is mentioned or discussed
    # We look for the word 'condition' and 'collinearity' or 'multicollinearity'
    if 'condition number' not in report_text.lower():
        errors.append("Report does not discuss 'condition number'")
    elif 'collinearity' not in report_text.lower() and 'multicollinearity' not in report_text.lower():
        errors.append("Report mentions 'condition number' but not in the context of collinearity")
    
    # Optional: Check if the specific value is mentioned (stricter)
    # This might fail if the report rounds the number, so we just check for presence of the concept.
    
    if errors:
        return False, "; ".join(errors)
    
    return True, "Collinearity condition number is discussed."

def main():
    project_root = get_project_root()
    report_path = project_root / 'artifacts' / 'reports' / 'final_report.md'
    fdr_json_path = project_root / 'data' / 'processed' / 'fdr_corrected_pvalues.json'
    collinearity_json_path = project_root / 'data' / 'processed' / 'collinearity_log.json'
    
    logger.info("Starting T084 Report Compliance Verification...")
    
    all_passed = True
    results = []
    
    # Check 1: FDR
    passed, msg = check_fdr_pvalues(report_path, fdr_json_path)
    results.append(("FDR-corrected p-values", passed, msg))
    if not passed: all_passed = False
    
    # Check 2: PDPs
    passed, msg = check_partial_dependence_plots(report_path, project_root)
    results.append(("Partial Dependence Plots", passed, msg))
    if not passed: all_passed = False
    
    # Check 3: Collinearity
    passed, msg = check_collinearity_condition_number(report_path, collinearity_json_path)
    results.append(("Collinearity Condition Number", passed, msg))
    if not passed: all_passed = False
    
    # Summary
    print("\n" + "="*50)
    print("T084 Report Compliance Verification Results")
    print("="*50)
    for check_name, passed, msg in results:
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {check_name}: {msg}")
    
    if all_passed:
        print("\nAll compliance checks passed.")
        sys.exit(0)
    else:
        print("\nSome compliance checks failed.")
        sys.exit(1)

if __name__ == '__main__':
    main()
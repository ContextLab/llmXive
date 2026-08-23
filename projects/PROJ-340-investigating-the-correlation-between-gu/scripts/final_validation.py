"""
Final Statistical Validation Script for PROJ-340.

This script performs a final validation to ensure:
1. Statistical methods selected match the data distribution checks.
2. No causal language slipped through in the reports.

It parses:
- data/metadata/method_selection_log.json
- data/results/causal_scan_report.json

And outputs:
- data/results/final_validation_report.json
"""
import json
import os
import sys
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def load_json_file(file_path: Path) -> dict:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_method_selection(method_log: dict) -> dict:
    """
    Validate that method selection logic was consistent with data distribution.
    
    Checks:
    - If compositionality was detected, a compositional method (SparCC/SpiecEasi) should be selected.
    - If zero-inflation was high, a ZINB/Hurdle model should be selected.
    - If normal distribution, Pearson/Spearman should be selected.
    """
    issues = []
    warnings = []
    
    # Default to pass if log is empty but expected to be populated
    if not method_log:
        return {
            "status": "warning",
            "message": "Method selection log is empty. Cannot validate consistency.",
            "issues": [],
            "warnings": ["Empty method selection log"]
        }

    # Example validation logic based on expected schema
    # We assume the log contains a list of selections or a single selection object
    selections = method_log.get("selections", [method_log]) if isinstance(method_log.get("selections"), list) else [method_log]
    
    for selection in selections:
        distribution = selection.get("distribution_check", "unknown")
        method = selection.get("selected_method", "unknown")
        reason = selection.get("reason", "")
        
        # Rule 1: If compositionality detected, method should be compositional
        if "compositionality" in reason.lower() or selection.get("is_compositional", False):
            valid_compositional_methods = ["sparcc", "spieceasi", "clr_spearman", "clr_pearson"]
            if method.lower() not in valid_compositional_methods:
                issues.append(f"Compositionality detected but non-compositional method '{method}' selected.")
        
        # Rule 2: If zero-inflation high, method should be ZINB/Hurdle
        if "zero-inflation" in reason.lower() or selection.get("high_zero_inflation", False):
            valid_zinb_methods = ["zinb", "hurdle", "zeroinfl", "zero_inflated_negative_binomial"]
            if method.lower() not in valid_zinb_methods:
                # Allow Spearman/Pearson as fallback if explicitly noted, but flag it
                if method.lower() in ["spearman", "pearson"]:
                    warnings.append(f"High zero-inflation detected but correlation method '{method}' selected. Check if ZINB fallback logic was triggered.")
                else:
                    issues.append(f"High zero-inflation detected but non-ZINB method '{method}' selected.")
        
        # Rule 3: Normal distribution should use parametric methods
        if distribution == "normal" and "non-parametric" in reason.lower():
            warnings.append(f"Data is normal but non-parametric method selected. Check if robustness was preferred.")

    status = "failed" if issues else ("warning" if warnings else "passed")
    return {
        "status": status,
        "issues": issues,
        "warnings": warnings
    }

def validate_causal_language(causal_report: dict) -> dict:
    """
    Validate that no causal language slipped through.
    
    Checks the causal_scan_report to see if any violations were found.
    """
    if not causal_report:
        return {
            "status": "warning",
            "message": "Causal scan report is missing.",
            "violations": []
        }

    violations = causal_report.get("violations", [])
    total_scanned = causal_report.get("total_files_scanned", 0)
    
    if violations:
        return {
            "status": "failed",
            "message": f"Found {len(violations)} causal language violations.",
            "violations": violations
        }
    
    return {
        "status": "passed",
        "message": "No causal language violations found.",
        "files_scanned": total_scanned
    }

def main():
    # Define paths relative to project root
    metadata_dir = project_root / "data" / "metadata"
    results_dir = project_root / "data" / "results"
    
    method_log_path = metadata_dir / "method_selection_log.json"
    causal_report_path = results_dir / "causal_scan_report.json"
    output_path = results_dir / "final_validation_report.json"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "validation_timestamp": None,
        "method_selection_validation": {},
        "causal_language_validation": {},
        "overall_status": "pending",
        "summary": ""
    }

    try:
        from datetime import datetime
        report["validation_timestamp"] = datetime.now().isoformat()
    except ImportError:
        report["validation_timestamp"] = "unknown"

    # 1. Validate Method Selection
    print(f"Loading method selection log from {method_log_path}...")
    try:
        method_log = load_json_file(method_log_path)
        method_validation = validate_method_selection(method_log)
        report["method_selection_validation"] = method_validation
    except FileNotFoundError as e:
        report["method_selection_validation"] = {
            "status": "failed",
            "message": str(e)
        }
    except Exception as e:
        report["method_selection_validation"] = {
            "status": "failed",
            "message": f"Error parsing method log: {str(e)}"
        }

    # 2. Validate Causal Language
    print(f"Loading causal scan report from {causal_report_path}...")
    try:
        causal_report = load_json_file(causal_report_path)
        causal_validation = validate_causal_language(causal_report)
        report["causal_language_validation"] = causal_validation
    except FileNotFoundError as e:
        report["causal_language_validation"] = {
            "status": "failed",
            "message": str(e)
        }
    except Exception as e:
        report["causal_language_validation"] = {
            "status": "failed",
            "message": f"Error parsing causal report: {str(e)}"
        }

    # 3. Determine Overall Status
    method_status = report["method_selection_validation"].get("status", "failed")
    causal_status = report["causal_language_validation"].get("status", "failed")

    if method_status == "failed" or causal_status == "failed":
        report["overall_status"] = "failed"
        report["summary"] = "Validation FAILED. See specific sections for details."
    elif method_status == "warning" or causal_status == "warning":
        report["overall_status"] = "warning"
        report["summary"] = "Validation completed with warnings. Review details."
    else:
        report["overall_status"] = "passed"
        report["summary"] = "All validation checks PASSED."

    # Write output
    print(f"Writing final validation report to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"Final validation complete. Status: {report['overall_status']}")
    
    # Exit with error code if failed to support CI gating
    if report["overall_status"] == "failed":
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
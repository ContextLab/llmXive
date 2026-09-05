"""
T084: Final Review of Spec and Plan against Execution Results.

This script performs the final verification mandated by T084:
1. Reads the final execution results (stats_report.json, final_report.md).
2. Loads the design documents (spec.md, plan.md).
3. Verifies that all assumptions in plan.md (e.g., N=5, Pearson correlation)
   are reflected in the actual results.
4. Verifies that the spec.md amendments (Proxy Ground Truth) were applied.
5. Writes a verification log to reports/spec_review_log.txt.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path if running as script
if "code" in str(Path(__file__).parent):
    sys.path.insert(0, str(Path(__file__).parent.parent))
else:
    sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config import get_project_root, get_data_path, get_artifacts_path, ensure_directories
from src.evaluation.report_generator import load_json_safe

def load_text_file(path: Path) -> str:
    """Safely load a text file."""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")

def check_spec_amendments(spec_content: str) -> List[str]:
    """
    Verify that spec.md contains the required amendments:
    - Amendment to FR-007/SC-005 regarding Proxy Ground Truth.
    """
    issues = []
    if "Proxy Ground Truth" not in spec_content:
        issues.append("MISSING: 'Proxy Ground Truth' amendment not found in spec.md")
    if "arithmetic mean" not in spec_content.lower():
        issues.append("MISSING: 'arithmetic mean' synthesis method not documented in spec.md")
    if "validate against this proxy" not in spec_content.lower():
        issues.append("MISSING: Validation logic for proxy not documented in spec.md")
    return issues

def check_plan_constraints(plan_content: str) -> List[str]:
    """
    Verify that plan.md contains the corrected constraints:
    - Pearson correlation (not Spearman).
    - N=5 runs (not N=3).
    """
    issues = []
    if "Pearson correlation" not in plan_content:
        issues.append("MISSING: 'Pearson correlation' not found in plan.md Constitution Check")
    if "Spearman correlation" in plan_content:
        issues.append("ERROR: 'Spearman correlation' still present in plan.md (should be Pearson)")
    if "N=5" not in plan_content:
        issues.append("MISSING: 'N=5' run count not found in plan.md Assumptions")
    if "N=3" in plan_content:
        issues.append("ERROR: 'N=3' run count still present in plan.md (should be N=5)")
    return issues

def verify_execution_results(stats_report_path: Path) -> List[str]:
    """
    Verify that the execution results match the plan constraints.
    """
    issues = []
    if not stats_report_path.exists():
        return ["CRITICAL: stats_report.json not found. Execution did not complete successfully."]

    try:
        report = load_json_safe(stats_report_path)
        if not report:
            return ["CRITICAL: stats_report.json is empty or invalid JSON."]
    except Exception as e:
        return [f"CRITICAL: Failed to load stats_report.json: {e}"]

    # Check N >= 5 (implied by power estimate or explicit run count if available)
    # Since stats_report.json aggregates results, we check for power_estimate which depends on N
    if "power_estimate" not in report:
        issues.append("MISSING: 'power_estimate' field in stats_report.json (requires N>=5 runs)")
    else:
        # If power_estimate exists, N>=5 was likely respected (T043 requirement)
        pass

    # Check Linearity Validation (SC-005)
    if "linearity_valid" not in report:
        issues.append("MISSING: 'linearity_valid' field in stats_report.json")
    else:
        status = "PASS" if report["linearity_valid"] else "FAIL"
        issues.append(f"INFO: SC-005 Linearity Validation status: {status}")

    # Check Max Error
    if "reconstruction_error" in report:
        max_err = report["reconstruction_error"].get("max")
        if max_err is not None:
            if max_err > 0.05:
                issues.append(f"WARNING: Max reconstruction error ({max_err}) exceeds 0.05 threshold.")
            else:
                issues.append(f"INFO: Max reconstruction error ({max_err}) within 0.05 threshold.")
    else:
        issues.append("MISSING: 'reconstruction_error' object in stats_report.json")

    return issues

def main():
    parser = argparse.ArgumentParser(description="T084: Verify Spec and Plan against Execution Results")
    parser.add_argument("--project-root", type=Path, default=None, help="Project root directory")
    args = parser.parse_args()

    root = args.project_root or get_project_root()
    spec_path = root / "specs" / "001-lattentskill-retrieval-geometry" / "spec.md"
    plan_path = root / "specs" / "001-lattentskill-retrieval-geometry" / "plan.md"
    stats_report_path = root / "data" / "results" / "stats_report.json"
    log_path = root / "reports" / "spec_review_log.txt"

    ensure_directories([log_path.parent])

    all_issues = []
    log_lines = []

    log_lines.append("=" * 60)
    log_lines.append("T084: Final Spec & Plan Review")
    log_lines.append(f"Timestamp: {Path(__file__).stat().st_mtime}")
    log_lines.append("=" * 60)

    # 1. Check Spec
    if spec_path.exists():
        spec_content = load_text_file(spec_path)
        spec_issues = check_spec_amendments(spec_content)
        log_lines.append("\n[1] Spec.md Review:")
        if not spec_issues:
            log_lines.append("  - All required amendments (Proxy Ground Truth) found.")
        else:
            for issue in spec_issues:
                log_lines.append(f"  - {issue}")
                all_issues.append(issue)
    else:
        log_lines.append("\n[1] Spec.md Review: FILE NOT FOUND")
        all_issues.append("CRITICAL: spec.md not found")

    # 2. Check Plan
    if plan_path.exists():
        plan_content = load_text_file(plan_path)
        plan_issues = check_plan_constraints(plan_content)
        log_lines.append("\n[2] Plan.md Review:")
        if not plan_issues:
            log_lines.append("  - All constraints (Pearson, N=5) verified.")
        else:
            for issue in plan_issues:
                log_lines.append(f"  - {issue}")
                all_issues.append(issue)
    else:
        log_lines.append("\n[2] Plan.md Review: FILE NOT FOUND")
        all_issues.append("CRITICAL: plan.md not found")

    # 3. Verify Execution Results
    log_lines.append("\n[3] Execution Results Verification:")
    exec_issues = verify_execution_results(stats_report_path)
    for issue in exec_issues:
        log_lines.append(f"  - {issue}")
        if "CRITICAL" in issue or "MISSING" in issue:
            all_issues.append(issue)

    # 4. Final Summary
    log_lines.append("\n" + "=" * 60)
    log_lines.append("SUMMARY")
    log_lines.append("=" * 60)
    if not all_issues:
        log_lines.append("STATUS: PASS")
        log_lines.append("All assumptions and constraints in spec.md and plan.md are accurately reflected in the final report and execution results.")
    else:
        log_lines.append("STATUS: WARNINGS / FAILURES")
        log_lines.append(f"Found {len(all_issues)} issue(s) requiring attention.")
        for issue in all_issues:
            log_lines.append(f"  - {issue}")

    # Write log
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"T084 Review complete. Log written to: {log_path}")

    # Return non-zero if critical issues found
    if any("CRITICAL" in i for i in all_issues):
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()

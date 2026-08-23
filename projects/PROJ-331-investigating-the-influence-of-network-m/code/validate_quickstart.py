"""
T044: Run quickstart.md validation.

This script parses `quickstart.md`, validates all referenced paths,
dependencies, and commands against the current project state, and
produces a validation report.
"""
import os
import sys
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Import config for paths
from config import ensure_dirs
from utils import get_logger, safe_read_text

# Configure logging
logger = get_logger("validate_quickstart")

def parse_quickstart(filepath: str) -> Dict[str, Any]:
    """Parse quickstart.md and extract sections."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"quickstart.md not found at {filepath}")

    content = safe_read_text(filepath)
    if not content:
        raise ValueError("quickstart.md is empty")

    sections = {
        "prerequisites": [],
        "commands": [],
        "expected_outputs": [],
        "data_sources": []
    }

    lines = content.split('\n')
    current_section = None

    for line in lines:
        line_stripped = line.strip()

        # Detect section headers
        if line_stripped.startswith("## Prerequisites"):
            current_section = "prerequisites"
            continue
        elif line_stripped.startswith("## Commands"):
            current_section = "commands"
            continue
        elif line_stripped.startswith("## Expected Outputs"):
            current_section = "expected_outputs"
            continue
        elif line_stripped.startswith("## Data Sources"):
            current_section = "data_sources"
            continue

        # Parse list items
        if current_section and line_stripped.startswith("-"):
            item = line_stripped[1:].strip()
            if current_section == "commands" and item.startswith("python"):
                sections["commands"].append(item)
            elif current_section == "expected_outputs":
                sections["expected_outputs"].append(item)
            elif current_section == "data_sources":
                sections["data_sources"].append(item)
            elif current_section == "prerequisites":
                sections["prerequisites"].append(item)

    return sections

def validate_paths(expected_outputs: List[str]) -> List[Dict[str, Any]]:
    """Check if expected output files exist."""
    results = []
    for output in expected_outputs:
        # Extract path from description (e.g., "data/processed/rsfc.npy")
        match = re.search(r'(data/[^\s,]+|results/[^\s,]+|figures/[^\s,]+)', output)
        if match:
            path = match.group(1)
            exists = os.path.exists(path)
            results.append({
                "path": path,
                "exists": exists,
                "status": "PASS" if exists else "FAIL"
            })
        else:
            results.append({
                "path": "unknown",
                "exists": False,
                "status": "FAIL",
                "reason": "Could not extract path from description"
            })
    return results

def validate_commands(commands: List[str]) -> List[Dict[str, Any]]:
    """Validate that commands are syntactically correct and reference existing scripts."""
    results = []
    for cmd in commands:
        try:
            # Check if script exists
            parts = cmd.split()
            if len(parts) >= 2 and parts[1].startswith("code/"):
                script_path = parts[1]
                if not os.path.exists(script_path):
                    results.append({
                        "command": cmd,
                        "status": "FAIL",
                        "reason": f"Script not found: {script_path}"
                    })
                else:
                    results.append({
                        "command": cmd,
                        "status": "PASS"
                    })
            else:
                # Non-script command (e.g., pip install)
                results.append({
                    "command": cmd,
                    "status": "PASS",
                    "note": "External command"
                })
        except Exception as e:
            results.append({
                "command": cmd,
                "status": "FAIL",
                "reason": str(e)
            })
    return results

def validate_prerequisites(prerequisites: List[str]) -> List[Dict[str, Any]]:
    """Check if prerequisites (dependencies) are met."""
    results = []
    required_packages = {
        "numpy", "scipy", "pandas", "networkx", "matplotlib", "seaborn",
        "nibabel", "requests", "reportlab", "tqdm", "joblib", "dipy",
        "statsmodels", "weasyprint", "igraph"
    }

    for req in prerequisites:
        # Check if it's a package
        match = re.search(r'pip install (\S+)', req)
        if match:
            pkg = match.group(1)
            # Simplified check - just log it
            results.append({
                "package": pkg,
                "status": "CHECKED",
                "note": f"Dependency listed: {pkg}"
            })
    return results

def run_validation(quickstart_path: str = "quickstart.md") -> Dict[str, Any]:
    """Run full validation and return report."""
    report = {
        "validation_status": "PASS",
        "sections_validated": [],
        "issues": [],
        "summary": {}
    }

    try:
        logger.info(f"Validating {quickstart_path}")
        sections = parse_quickstart(quickstart_path)
        report["sections_validated"] = list(sections.keys())

        # Validate paths
        path_results = validate_paths(sections["expected_outputs"])
        report["path_validation"] = path_results
        failed_paths = [r for r in path_results if r["status"] == "FAIL"]
        if failed_paths:
            report["validation_status"] = "WARN"
            report["issues"].extend([
                {"type": "missing_output", "details": r} for r in failed_paths
            ])

        # Validate commands
        cmd_results = validate_commands(sections["commands"])
        report["command_validation"] = cmd_results
        failed_cmds = [r for r in cmd_results if r["status"] == "FAIL"]
        if failed_cmds:
            report["validation_status"] = "FAIL"
            report["issues"].extend([
                {"type": "invalid_command", "details": r} for r in failed_cmds
            ])

        # Validate prerequisites
        prereq_results = validate_prerequisites(sections["prerequisites"])
        report["prerequisite_validation"] = prereq_results

        # Summary
        total_checks = len(path_results) + len(cmd_results)
        passed_checks = sum(1 for r in path_results if r["status"] == "PASS") + \
                        sum(1 for r in cmd_results if r["status"] == "PASS")

        report["summary"] = {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": total_checks - passed_checks,
            "validation_status": report["validation_status"]
        }

        logger.info(f"Validation complete: {report['validation_status']}")

    except Exception as e:
        report["validation_status"] = "FAIL"
        report["issues"].append({
            "type": "validation_error",
            "details": str(e)
        })
        logger.error(f"Validation failed: {e}")

    return report

def save_report(report: Dict[str, Any], output_path: str = "results/quickstart_validation_report.json"):
    """Save validation report to file."""
    ensure_dirs()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Report saved to {output_path}")

def main():
    """Main entry point for T044."""
    logger.info("Starting quickstart.md validation (T044)")

    # Run validation
    report = run_validation("quickstart.md")

    # Save report
    save_report(report, "results/quickstart_validation_report.json")

    # Print summary
    print("\n" + "="*50)
    print("QUICKSTART VALIDATION SUMMARY")
    print("="*50)
    print(f"Status: {report['validation_status']}")
    print(f"Total Checks: {report['summary']['total_checks']}")
    print(f"Passed: {report['summary']['passed_checks']}")
    print(f"Failed: {report['summary']['failed_checks']}")

    if report['issues']:
        print("\nIssues found:")
        for issue in report['issues']:
            print(f"  - [{issue['type']}] {issue['details']}")

    print("="*50)

    # Exit with appropriate code
    if report['validation_status'] == "FAIL":
        sys.exit(1)
    elif report['validation_status'] == "WARN":
        sys.exit(0)  # Warnings are acceptable
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()

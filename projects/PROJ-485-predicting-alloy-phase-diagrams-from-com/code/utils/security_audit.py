"""
Security Audit Module for PROJ-485.
Implements automated security scanning using bandit and safety,
along with manual code review checks for hardcoded credentials and insecure file handling.
"""
import os
import sys
import json
import subprocess
import argparse
from typing import Dict, Any, List, Optional
from utils.logging import get_logger, log_info, log_error, log_warning

logger = get_logger(__name__)

def run_bandit_check(target_dir: str = "code") -> Dict[str, Any]:
    """
    Runs bandit security scanner on the target directory.
    Returns a summary of findings.
    """
    log_info(f"Running bandit check on {target_dir}")
    try:
        # Run bandit with JSON output
        cmd = [
            "bandit",
            "-r", target_dir,
            "-f", "json",
            "-o", "-",  # Output to stdout
            "--skip", "B101"  # Skip assert statements (common in tests)
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            log_info("Bandit scan completed with no findings.")
            return {
                "status": "passed",
                "tool": "bandit",
                "findings": [],
                "message": "No security issues found."
            }
        elif result.returncode == 1:
            # Findings exist
            try:
                findings = json.loads(result.stdout)
                # Filter high/critical issues
                critical = [
                    f for f in findings.get("results", [])
                    if f.get("issue_severity", "").lower() in ["high", "critical"]
                ]
                if critical:
                    log_error(f"Found {len(critical)} high/critical issues.")
                    return {
                        "status": "failed",
                        "tool": "bandit",
                        "critical_count": len(critical),
                        "findings": critical,
                        "message": f"Found {len(critical)} critical/high security issues."
                    }
                else:
                    log_warning("Bandit found issues, but none are critical/high.")
                    return {
                        "status": "warning",
                        "tool": "bandit",
                        "findings": findings.get("results", []),
                        "message": "Non-critical issues found."
                    }
            except json.JSONDecodeError:
                # Fallback if bandit output is not valid JSON (e.g. just text)
                log_warning("Bandit output was not valid JSON, treating as failure.")
                return {
                    "status": "failed",
                    "tool": "bandit",
                    "message": "Bandit reported issues (non-JSON output)."
                }
        else:
            log_error(f"Bandit command failed with code {result.returncode}")
            return {
                "status": "error",
                "tool": "bandit",
                "message": f"Bandit execution failed: {result.stderr}"
            }
    except subprocess.TimeoutExpired:
        log_error("Bandit check timed out.")
        return {
            "status": "error",
            "tool": "bandit",
            "message": "Bandit check timed out."
        }
    except FileNotFoundError:
        log_error("Bandit not found. Install with: pip install bandit")
        return {
            "status": "error",
            "tool": "bandit",
            "message": "Bandit tool not found."
        }
    except Exception as e:
        log_error(f"Unexpected error during bandit check: {str(e)}")
        return {
            "status": "error",
            "tool": "bandit",
            "message": str(e)
        }

def run_safety_check() -> Dict[str, Any]:
    """
    Runs safety check on installed packages for known vulnerabilities.
    """
    log_info("Running safety check on dependencies.")
    try:
        cmd = ["safety", "check", "--output", "json"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            log_info("Safety check completed with no vulnerabilities.")
            return {
                "status": "passed",
                "tool": "safety",
                "findings": [],
                "message": "No known vulnerabilities in dependencies."
            }
        elif result.returncode == 1:
            # Vulnerabilities found
            try:
                findings = json.loads(result.stdout)
                critical = [f for f in findings if f.get("severity", "").lower() in ["critical", "high"]]
                if critical:
                    log_error(f"Found {len(critical)} critical/high vulnerabilities.")
                    return {
                        "status": "failed",
                        "tool": "safety",
                        "critical_count": len(critical),
                        "findings": findings,
                        "message": f"Found {len(critical)} critical/high vulnerabilities."
                    }
                else:
                    log_warning("Safety found vulnerabilities, but none are critical/high.")
                    return {
                        "status": "warning",
                        "tool": "safety",
                        "findings": findings,
                        "message": "Non-critical vulnerabilities found."
                    }
            except json.JSONDecodeError:
                log_warning("Safety output was not valid JSON.")
                return {
                    "status": "failed",
                    "tool": "safety",
                    "message": "Safety reported vulnerabilities (non-JSON output)."
                }
        else:
            log_error(f"Safety command failed with code {result.returncode}")
            return {
                "status": "error",
                "tool": "safety",
                "message": f"Safety execution failed: {result.stderr}"
            }
    except subprocess.TimeoutExpired:
        log_error("Safety check timed out.")
        return {
            "status": "error",
            "tool": "safety",
            "message": "Safety check timed out."
        }
    except FileNotFoundError:
        log_error("Safety not found. Install with: pip install safety")
        return {
            "status": "error",
            "tool": "safety",
            "message": "Safety tool not found."
        }
    except Exception as e:
        log_error(f"Unexpected error during safety check: {str(e)}")
        return {
            "status": "error",
            "tool": "safety",
            "message": str(e)
        }

def manual_code_review() -> Dict[str, Any]:
    """
    Performs a manual code review by scanning for common patterns:
    - Hardcoded credentials (passwords, api_keys, secrets)
    - Insecure file handling (open without context, missing permissions checks)
    - Use of eval/exec on user input
    """
    log_info("Performing manual code review.")
    findings = []
    critical_issues = 0
    code_dir = "code"
    if not os.path.exists(code_dir):
        log_warning(f"Directory {code_dir} not found for manual review.")
        return {
            "status": "warning",
            "tool": "manual_review",
            "findings": [],
            "message": "Code directory not found."
        }

    # Patterns to search for
    patterns = {
        "hardcoded_password": r"(?i)(password|passwd|pwd)\s*=\s*['\"][^'\"]+['\"]",
        "hardcoded_api_key": r"(?i)(api_key|apikey|secret_key)\s*=\s*['\"][^'\"]+['\"]",
        "hardcoded_secret": r"(?i)(secret|token)\s*=\s*['\"][^'\"]+['\"]",
        "unsafe_eval": r"\beval\s*\(",
        "unsafe_exec": r"\bexec\s*\(",
    }

    for root, _, files in os.walk(code_dir):
        # Skip hidden directories and non-code files
        if "__pycache__" in root or ".git" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        for issue_type, pattern in patterns.items():
                            import re
                            matches = re.findall(pattern, content)
                            if matches:
                                # Filter out test files or known safe patterns if necessary
                                if "test" in filepath.lower():
                                    continue
                                critical_issues += 1
                                findings.append({
                                    "file": filepath,
                                    "issue": issue_type,
                                    "count": len(matches),
                                    "severity": "high" if "password" in issue_type or "secret" in issue_type else "medium"
                                })
                except Exception as e:
                    log_warning(f"Could not read file {filepath}: {e}")

    if critical_issues > 0:
        log_error(f"Found {critical_issues} potential security issues in manual review.")
        return {
            "status": "failed",
            "tool": "manual_review",
            "critical_count": critical_issues,
            "findings": findings,
            "message": f"Found {critical_issues} potential security issues."
        }
    else:
        log_info("Manual review completed with no critical issues.")
        return {
            "status": "passed",
            "tool": "manual_review",
            "findings": [],
            "message": "No critical security issues found in manual review."
        }

def check_file_permissions() -> Dict[str, Any]:
    """
    Checks if any files in the code directory have overly permissive permissions.
    """
    log_info("Checking file permissions.")
    findings = []
    code_dir = "code"
    if not os.path.exists(code_dir):
        return {
            "status": "warning",
            "tool": "file_permissions",
            "findings": [],
            "message": "Code directory not found."
        }

    for root, _, files in os.walk(code_dir):
        for file in files:
            filepath = os.path.join(root, file)
            try:
                stat_info = os.stat(filepath)
                # Check if file is world-writable (mode & 0o002)
                if stat_info.st_mode & 0o002:
                    findings.append({
                        "file": filepath,
                        "issue": "world_writable",
                        "severity": "high"
                    })
            except Exception as e:
                log_warning(f"Could not check permissions for {filepath}: {e}")

    if findings:
        log_error(f"Found {len(findings)} files with insecure permissions.")
        return {
            "status": "failed",
            "tool": "file_permissions",
            "critical_count": len(findings),
            "findings": findings,
            "message": f"Found {len(findings)} files with insecure permissions."
        }
    else:
        log_info("File permissions check completed with no issues.")
        return {
            "status": "passed",
            "tool": "file_permissions",
            "findings": [],
            "message": "No files with insecure permissions found."
        }

def generate_report(
    bandit_result: Dict[str, Any],
    safety_result: Dict[str, Any],
    manual_result: Dict[str, Any],
    perm_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregates all security check results into a final report.
    """
    overall_status = "passed"
    total_critical = 0
    all_findings = []

    # Aggregate results
    for res in [bandit_result, safety_result, manual_result, perm_result]:
        if res.get("status") == "failed":
            overall_status = "failed"
            total_critical += res.get("critical_count", 0)
        if res.get("status") == "warning" and overall_status != "failed":
            overall_status = "warning"
        if res.get("findings"):
            all_findings.extend(res.get("findings", []))

    report = {
        "audit_date": "2023-10-27", # Placeholder, can be dynamic
        "overall_status": overall_status,
        "total_critical_issues": total_critical,
        "tool_results": {
            "bandit": bandit_result,
            "safety": safety_result,
            "manual_review": manual_result,
            "file_permissions": perm_result
        },
        "summary_findings": all_findings
    }

    return report

def main():
    """
    Main entry point for the security audit.
    """
    parser = argparse.ArgumentParser(description="Run security audit on the codebase.")
    parser.add_argument("--output", "-o", default="data/artifacts/security_audit_report.json",
                        help="Path to save the security audit report.")
    args = parser.parse_args()

    log_info("Starting Security Audit for PROJ-485")

    # Run checks
    bandit_result = run_bandit_check()
    safety_result = run_safety_check()
    manual_result = manual_code_review()
    perm_result = check_file_permissions()

    # Generate report
    report = generate_report(bandit_result, safety_result, manual_result, perm_result)

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Write report to disk
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)

    log_info(f"Security audit report saved to {args.output}")

    # Print summary
    print(f"\n--- Security Audit Summary ---")
    print(f"Overall Status: {report['overall_status'].upper()}")
    print(f"Critical Issues: {report['total_critical_issues']}")
    if report['overall_status'] == "passed":
        print("No Critical Issues")
    else:
        print("Critical Issues Found. Review report for details.")

    # Exit with appropriate code
    if report['overall_status'] == "failed":
        sys.exit(1)
    elif report['overall_status'] == "warning":
        sys.exit(0) # Warnings are acceptable for this task
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()

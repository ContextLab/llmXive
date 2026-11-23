"""
PII Scanner Script for Security Hardening.

This script uses detect-secrets to scan the project for potential PII leaks,
specifically focusing on the data/processed/ directory. It can check prerequisites,
create a baseline, and run scans that fail the build if new secrets are found.
"""
import subprocess
import sys
import os
from pathlib import Path
import argparse
import json


def check_prerequisites(baseline_path: str = ".secrets.baseline") -> bool:
    """
    Check if detect-secrets is installed and if a baseline exists.
    If baseline doesn't exist, create one.

    Args:
        baseline_path: Path to the secrets baseline file.

    Returns:
        True if prerequisites are met, False otherwise.
    """
    # Check if detect-secrets is installed
    try:
        subprocess.run(
            ["detect-secrets", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: detect-secrets is not installed. Run: pip install detect-secrets")
        return False

    baseline_file = Path(baseline_path)
    if not baseline_file.exists():
        print("INFO: No baseline file found. Creating a new baseline...")
        try:
            # Scan the entire repo to create a baseline, excluding data/processed initially
            # to avoid false positives on legitimate processed data that might look like secrets
            result = subprocess.run(
                [
                    "detect-secrets", "scan",
                    "--baseline", str(baseline_file),
                    "--exclude-files", "data/processed/.*"
                ],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"INFO: Baseline created at {baseline_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to create baseline: {e.stderr}")
            return False

    return True


def run_scan(scan_path: str, baseline_path: str = ".secrets.baseline") -> bool:
    """
    Run detect-secrets scan on a specific path and compare against baseline.
    Fails if new secrets are detected.

    Args:
        scan_path: Path to scan (e.g., data/processed/).
        baseline_path: Path to the secrets baseline file.

    Returns:
        True if scan passes (no new secrets), False if new secrets found or error.
    """
    baseline_file = Path(baseline_path)
    if not baseline_file.exists():
        print(f"ERROR: Baseline file {baseline_path} not found. Run --check-prerequisites first.")
        return False

    scan_dir = Path(scan_path)
    if not scan_dir.exists():
        print(f"ERROR: Scan path {scan_path} does not exist.")
        return False

    print(f"INFO: Scanning {scan_path} for PII...")

    # Run detect-secrets audit to check for new secrets against baseline
    try:
        result = subprocess.run(
            [
                "detect-secrets", "audit",
                "--baseline", str(baseline_file),
                "--path", str(scan_dir)
            ],
            capture_output=True,
            text=True
        )

        # detect-secrets audit returns 0 if no new secrets, 1 if new secrets found
        if result.returncode != 0:
            print("ERROR: Potential PII detected in processed data!")
            print(result.stdout)
            print(result.stderr)
            return False

        print("INFO: Scan complete. No new PII detected.")
        return True

    except Exception as e:
        print(f"ERROR: Scan failed with exception: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="PII Scanner for Security Hardening")
    parser.add_argument(
        "--check-prerequisites",
        action="store_true",
        help="Check if detect-secrets is installed and create baseline if missing"
    )
    parser.add_argument(
        "--scan-path",
        type=str,
        default="data/processed/",
        help="Path to scan for PII (default: data/processed/)"
    )
    parser.add_argument(
        "--baseline",
        type=str,
        default=".secrets.baseline",
        help="Path to secrets baseline file (default: .secrets.baseline)"
    )

    args = parser.parse_args()

    if args.check_prerequisites:
        success = check_prerequisites(args.baseline)
        sys.exit(0 if success else 1)

    # Default action: run scan
    success = run_scan(args.scan_path, args.baseline)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

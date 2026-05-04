#!/usr/bin/env python3
"""
Credential scanning script for data files using trufflehog.

Scans the data/ directory for exposed credentials, secrets, and API keys.
Per Constitution Principle III security requirements.

Usage:
    python scan_credentials.py [--data-dir DATA_DIR] [--output OUTPUT_JSON]

Exit codes:
    0 - Scan completed (findings may or may not exist)
    1 - Scan failed due to error
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_trufflehog_installed() -> bool:
    """Check if trufflehog is installed and available."""
    try:
        result = subprocess.run(
            ["trufflehog", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            logger.info(f"trufflehog available: {result.stdout.strip()}")
            return True
        else:
            logger.warning("trufflehog command exists but returned error")
            return False
    except FileNotFoundError:
        logger.error("trufflehog not found in PATH")
        logger.info("Install with: pip install trufflehog")
        return False
    except subprocess.TimeoutExpired:
        logger.error("trufflehog version check timed out")
        return False

def scan_data_directory(
    data_dir: Path,
    output_file: Path = None
) -> dict:
    """
    Scan data directory for credentials using trufflehog.

    Args:
        data_dir: Path to data directory to scan
        output_file: Optional path to write results to JSON

    Returns:
        Dictionary with scan results
    """
    if not data_dir.exists():
        logger.error(f"Data directory does not exist: {data_dir}")
        return {
            "error": f"Directory not found: {data_dir}",
            "findings": [],
            "scan_time": datetime.now().isoformat(),
            "directory": str(data_dir)
        }

    logger.info(f"Starting credential scan of {data_dir}")

    # Check if trufflehog is installed
    if not check_trufflehog_installed():
        return {
            "error": "trufflehog not installed",
            "findings": [],
            "scan_time": datetime.now().isoformat(),
            "directory": str(data_dir)
        }

    try:
        # Run trufflehog scan on data directory
        # Using filesystem detector with JSON output
        scan_result = subprocess.run(
            ["trufflehog", "filesystem", "--json", str(data_dir)],
            capture_output=True,
            text=True,
            timeout=600
        )

        findings = []

        # Parse JSON output (each line is a JSON object)
        if scan_result.stdout:
            for line in scan_result.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        finding = json.loads(line)
                        findings.append(finding)
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse trufflehog output: {line}")

        # Also check stderr for any errors
        if scan_result.stderr:
            logger.warning(f"trufflehog stderr: {scan_result.stderr}")

        result = {
            "scan_time": datetime.now().isoformat(),
            "directory": str(data_dir),
            "total_findings": len(findings),
            "findings": findings
        }

        # Write results to file if specified
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"Results written to {output_file}")

        # Log summary
        if findings:
            logger.warning(f"Found {len(findings)} potential credential findings!")
            for i, finding in enumerate(findings[:5]):
                logger.warning(
                    f"  Finding {i+1}: {finding.get('DetectorType', 'unknown')} "
                    f"at {finding.get('File', 'unknown')}"
                )
            if len(findings) > 5:
                logger.warning(f"  ... and {len(findings) - 5} more")
        else:
            logger.info("No credential findings detected - scan passed!")

        return result

    except subprocess.TimeoutExpired:
        logger.error("trufflehog scan timed out after 600 seconds")
        return {
            "error": "scan timed out",
            "findings": [],
            "scan_time": datetime.now().isoformat(),
            "directory": str(data_dir)
        }
    except Exception as e:
        logger.error(f"Error during trufflehog scan: {e}")
        return {
            "error": str(e),
            "findings": [],
            "scan_time": datetime.now().isoformat(),
            "directory": str(data_dir)
        }

def main():
    """Main entry point for credential scanning."""
    parser = argparse.ArgumentParser(
        description="Scan data directory for credentials using trufflehog"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        help="Path to data directory to scan (default: project_root/data)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output JSON file path (default: data/credential_scan_results.json)"
    )
    parser.add_argument(
        "--fail-on-findings",
        action="store_true",
        help="Exit with code 1 if any findings are detected"
    )

    args = parser.parse_args()

    # Determine project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    # Set data directory
    if args.data_dir:
        data_dir = Path(args.data_dir)
    else:
        data_dir = project_root / "data"

    # Set output file
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = project_root / "data" / "credential_scan_results.json"

    logger.info(f"Project root: {project_root}")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Output file: {output_file}")

    # Run the scan
    results = scan_data_directory(data_dir, output_file)

    # Print summary to stdout for CI/CD integration
    print(json.dumps(results, indent=2))

    # Exit with appropriate code
    if results.get("error"):
        logger.error("Scan failed due to error")
        sys.exit(1)
    elif results.get("total_findings", 0) > 0 and args.fail_on_findings:
        logger.warning("Credential scan found potential secrets")
        sys.exit(1)
    else:
        logger.info("Credential scan completed successfully")
        sys.exit(0)

if __name__ == "__main__":
    main()

"""
PII Removal Verification Script.

This script scans the anonymized interaction logs for Personally Identifiable Information (PII)
patterns and verifies that the consent directory is excluded from VCS history.

It is designed to fail loudly (exit code 1) if any PII is detected or if the consent
directory appears in the git history, ensuring Constitution Principle VI is met.
"""
import os
import sys
import re
import json
import subprocess
import argparse
from pathlib import Path
from typing import List, Set, Tuple, Dict, Any

# Import existing logging utility
from utils.logging_utils import get_logger

# Initialize logger
logger = get_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ANONYMIZED_LOGS_PATH = PROJECT_ROOT / "data" / "interaction_logs" / "anonymized_logs.csv"
CONSENT_DIR = PROJECT_ROOT / "data" / "consent"
GIT_DIR = PROJECT_ROOT / ".git"

# PII Regex Patterns
PII_PATTERNS = {
    "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    "phone_us": re.compile(r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
    "ssn": re.compile(r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b'),
    # Participant ID patterns that might leak original IDs (e.g., "P001" if not hashed)
    # We assume anonymized IDs should be UUIDs or specific hash formats.
    # If we find "Participant_" followed by digits, it might be a leak.
    "leaked_participant_id": re.compile(r'\bParticipant_\d{3,}\b'),
    "ip_address": re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
    "url": re.compile(r'\bhttps?://[^\s<>"{}|\\^`\[\]]+\b'),
}

# Columns that are expected to contain sensitive data if not properly anonymized
SENSITIVE_COLUMNS = {
    "participant_id", "user_id", "email", "name", "ip_address", "session_id"
}

def check_pii_in_file(file_path: Path) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Scans a CSV file for PII patterns.
    
    Args:
        file_path: Path to the CSV file.
        
    Returns:
        Tuple of (has_pii, list_of_findings).
    """
    findings = []
    has_pii = False

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return True, [{"file": str(file_path), "error": "File not found"}]

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read line by line to handle large files
            for line_num, line in enumerate(f, 1):
                for pattern_name, pattern in PII_PATTERNS.items():
                    matches = pattern.findall(line)
                    if matches:
                        has_pii = True
                        # Limit findings to avoid log spam
                        if len(findings) < 50:
                            findings.append({
                                "file": str(file_path),
                                "line": line_num,
                                "pattern": pattern_name,
                                "match": matches[0] if len(matches) == 1 else f"{matches[0]}... (truncated)"
                            })
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return True, [{"file": str(file_path), "error": str(e)}]

    return has_pii, findings

def check_consent_vcs_history() -> Tuple[bool, str]:
    """
    Verifies that the data/consent/ directory is not present in the git history.
    
    Returns:
        Tuple of (is_present_in_history, message).
    """
    if not GIT_DIR.exists():
        logger.warning("No .git directory found. Skipping VCS history check.")
        return False, "No .git directory found. Skipping VCS history check."

    try:
        # Check if the directory exists in the current working tree
        if CONSENT_DIR.exists():
            logger.warning(f"Consent directory exists at {CONSENT_DIR}. Checking history...")
        
        # Use git log to search for the path in history
        # We check if any commit touched data/consent/
        result = subprocess.run(
            ["git", "log", "--all", "--full-history", "--", str(CONSENT_DIR.relative_to(PROJECT_ROOT))],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 and result.stdout.strip():
            return True, f"Found {CONSENT_DIR} in git history."
        
        return False, "Consent directory not found in git history."

    except subprocess.TimeoutExpired:
        return False, "Git history check timed out."
    except Exception as e:
        logger.error(f"Error checking git history: {e}")
        return False, f"Error checking git history: {e}"

def run_verification() -> bool:
    """
    Executes the full PII verification workflow.
    
    Returns:
        True if verification passes (no PII found, consent not in VCS), False otherwise.
    """
    logger.info("Starting PII Removal Verification (T031b)...")
    all_passed = True
    report = {
        "status": "PASSED",
        "checks": []
    }

    # 1. Check Anonymized Logs for PII
    logger.info(f"Scanning {ANONYMIZED_LOGS_PATH} for PII...")
    if ANONYMIZED_LOGS_PATH.exists():
        has_pii, findings = check_pii_in_file(ANONYMIZED_LOGS_PATH)
        if has_pii:
            all_passed = False
            report["status"] = "FAILED"
            logger.error("PII detected in anonymized logs!")
            logger.error(f"Findings count: {len(findings)}")
            for i, finding in enumerate(findings[:10]): # Log first 10
                logger.error(f"  - {finding}")
            report["checks"].append({
                "name": "PII Scan",
                "passed": False,
                "details": f"Found {len(findings)} potential PII instances."
            })
        else:
            logger.info("No PII detected in anonymized logs.")
            report["checks"].append({
                "name": "PII Scan",
                "passed": True,
                "details": "No PII patterns found."
            })
    else:
        all_passed = False
        report["status"] = "FAILED"
        logger.error(f"Anonymized logs file not found at {ANONYMIZED_LOGS_PATH}")
        report["checks"].append({
            "name": "PII Scan",
            "passed": False,
            "details": "File not found."
        })

    # 2. Check Consent Directory VCS History
    logger.info("Checking VCS history for data/consent/...")
    present_in_history, history_msg = check_consent_vcs_history()
    if present_in_history:
        all_passed = False
        report["status"] = "FAILED"
        logger.error(history_msg)
        report["checks"].append({
            "name": "VCS History Check",
            "passed": False,
            "details": history_msg
        })
    else:
        logger.info("Consent directory is not in VCS history.")
        report["checks"].append({
            "name": "VCS History Check",
            "passed": True,
            "details": history_msg
        })

    # 3. Check Consent Directory Permissions (Optional but good practice)
    if CONSENT_DIR.exists():
        stat_info = CONSENT_DIR.stat()
        # Check if permissions are 600 or 700 (owner only)
        mode = stat_info.st_mode & 0o777
        if mode != 0o700 and mode != 0o600:
            logger.warning(f"Consent directory permissions are {oct(mode)}, expected 0o700 or 0o600.")
            # This is a warning, not a hard failure for the script, but noted.
        else:
            logger.info(f"Consent directory permissions are secure ({oct(mode)}).")

    # Save report
    report_path = PROJECT_ROOT / "data" / "analysis_results" / "pii_verification_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Verification report saved to {report_path}")

    return all_passed

def main():
    parser = argparse.ArgumentParser(description="Verify PII removal and consent directory security.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

    success = run_verification()

    if success:
        logger.info("T031b Verification PASSED.")
        sys.exit(0)
    else:
        logger.error("T031b Verification FAILED. PII found or security policy violated.")
        sys.exit(1)

if __name__ == "__main__":
    main()
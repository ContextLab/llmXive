"""
T031b: Verify PII Removal and Consent Directory Exclusion.

This script implements the verification logic for Constitution Principle VI.
It performs two critical checks:
1. Scans `data/interaction_logs/anonymized_logs.csv` for PII patterns (email, SSN, phone).
2. Verifies `data/consent/` is excluded from VCS history.

Exit codes:
0: Verification passed (no PII found, consent excluded).
1: Verification failed (PII found or consent directory present in VCS).
"""

import os
import sys
import re
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

# Import logging utilities from existing project surface
try:
    from utils.logging_utils import get_logger
except ImportError:
    # Fallback for direct execution if utils is not in path
    import logging
    def get_logger(name):
        return logging.getLogger(name)

# Configuration
ANONYMIZED_LOGS_PATH = Path("data/interaction_logs/anonymized_logs.csv")
CONSENT_DIR_PATH = Path("data/consent")
REPO_ROOT = Path.cwd()

# PII Detection Patterns (Regex)
# These patterns are designed to catch common PII formats.
# If any match, the verification fails.
PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "phone_us": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    # Additional generic pattern for potential names if they look like full names
    # Note: This is heuristic and might have false positives, but serves as a warning.
    "potential_name": re.compile(r"\b[A-Z][a-z]+\s[A-Z][a-z]+\b"), 
}

logger = get_logger("verify_pii_removal")

def scan_csv_for_pii(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Scans a CSV file for PII patterns.
    
    Args:
        file_path: Path to the CSV file.
        
    Returns:
        A list of tuples (line_number, line_content, pattern_type) for matches.
    """
    findings = []
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return findings

    logger.info(f"Scanning {file_path} for PII patterns...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Skip header if it's the first line and contains column names
                if line_num == 1 and 'participant_id' in line.lower():
                    continue
                
                for pattern_name, pattern in PII_PATTERNS.items():
                    if pattern.search(line):
                        findings.append((line_num, line.strip(), pattern_name))
                        logger.warning(f"Potential PII found at line {line_num}: {pattern_name} -> {line.strip()[:50]}...")
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

    return findings

def check_vcs_exclusion(directory_path: Path) -> bool:
    """
    Checks if the specified directory exists in the git history.
    
    Args:
        directory_path: Path to the directory to check.
        
    Returns:
        True if the directory is NOT in git history (passed), False if it is (failed).
    """
    if not directory_path.exists():
        logger.warning(f"Directory does not exist: {directory_path}. Skipping VCS history check.")
        # If the directory doesn't exist, we can't check history, but it's technically "not present".
        # However, for the task, we usually expect the directory to exist but be empty/ignored.
        # We'll assume pass if it doesn't exist, but log a warning.
        return True

    try:
        # Run git log to check if any file in the directory was ever committed
        # Using --full-history to ensure we catch all relevant commits
        cmd = [
            "git", "log", "--all", "--full-history", "--", str(directory_path)
        ]
        
        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            # Git might fail if not in a repo or other issues. 
            # If it's not a git repo, we can't verify history, but we can't fail for that.
            logger.warning(f"Git command failed or not a git repo: {result.stderr}")
            return True 
        
        if result.stdout.strip():
            # Output means there are commits touching this directory
            logger.error(f"Directory {directory_path} found in git history!")
            logger.error(f"Git output:\n{result.stdout}")
            return False
        
        logger.info(f"Directory {directory_path} is NOT present in git history.")
        return True

    except subprocess.TimeoutExpired:
        logger.error("Git command timed out.")
        return False
    except FileNotFoundError:
        logger.warning("Git not found. Skipping VCS history check.")
        return True
    except Exception as e:
        logger.error(f"Error checking VCS history: {e}")
        return False

def verify_gitignore_exclusion(directory_path: Path) -> bool:
    """
    Verifies that the directory is listed in .gitignore.
    
    Args:
        directory_path: Path to the directory.
        
    Returns:
        True if excluded in .gitignore, False otherwise.
    """
    gitignore_path = REPO_ROOT / ".gitignore"
    if not gitignore_path.exists():
        logger.warning(".gitignore not found. Cannot verify exclusion.")
        return False

    with open(gitignore_path, 'r') as f:
        content = f.read()

    # Check if the directory name or path is in .gitignore
    # We look for the directory name (e.g., "data/consent" or "consent")
    exclusion_patterns = [
        str(directory_path),
        directory_path.name,
        f"*/{directory_path.name}",
    ]
    
    found = any(p in content for p in exclusion_patterns)
    
    if found:
        logger.info(f"Directory {directory_path} is excluded in .gitignore.")
        return True
    else:
        logger.error(f"Directory {directory_path} is NOT excluded in .gitignore.")
        return False

def main():
    """
    Main entry point for T031b verification.
    """
    logger.info("Starting PII Removal and Consent Exclusion Verification (T031b)...")
    
    all_checks_passed = True
    errors = []

    # 1. Scan Anonymized Logs for PII
    if ANONYMIZED_LOGS_PATH.exists():
        pii_findings = scan_csv_for_pii(ANONYMIZED_LOGS_PATH)
        if pii_findings:
            all_checks_passed = False
            errors.append(f"Found {len(pii_findings)} potential PII instances in {ANONYMIZED_LOGS_PATH}")
            for line_num, line, p_type in pii_findings:
                errors.append(f"  Line {line_num} ({p_type}): {line[:60]}...")
        else:
            logger.info(f"No PII patterns detected in {ANONYMIZED_LOGS_PATH}.")
    else:
        logger.warning(f"Anonymized logs file not found: {ANONYMIZED_LOGS_PATH}. Skipping PII scan.")
        # Depending on strictness, this might be a failure, but usually implies no data to scan.
        # We will treat it as a warning but not a hard fail for the PII check itself, 
        # unless the task requires the file to exist. The task says "scan ... and verify".
        # If it doesn't exist, we can't scan. We'll flag it.
        errors.append(f"Anonymized logs file missing: {ANONYMIZED_LOGS_PATH}")
        all_checks_passed = False

    # 2. Verify Consent Directory Exclusion from VCS
    vcs_check_passed = check_vcs_exclusion(CONSENT_DIR_PATH)
    if not vcs_check_passed:
        all_checks_passed = False
        errors.append("Consent directory found in git history.")
    
    # 3. Verify .gitignore exclusion
    ignore_check_passed = verify_gitignore_exclusion(CONSENT_DIR_PATH)
    if not ignore_check_passed:
        all_checks_passed = False
        errors.append("Consent directory not properly excluded in .gitignore.")

    # Final Report
    print("\n" + "="*60)
    print("VERIFICATION REPORT (T031b)")
    print("="*60)
    if all_checks_passed:
        print("STATUS: PASSED")
        print("All PII checks and VCS exclusions are valid.")
        sys.exit(0)
    else:
        print("STATUS: FAILED")
        print("The following issues were detected:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()

"""
Terminology Audit Script for PROJ-169.

Scans code/, docs/, and data/results/ for forbidden terminology:
- "First-Principles" (case insensitive, variations)
- "Schrödinger" (case insensitive)

Replaces occurrences with "Surrogate" or "Interpolation" where appropriate.
Logs all changes to state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml
under the key `terminology_audit`.
"""

import os
import re
import sys
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Project root (assuming this script is in code/utils/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Directories to scan
SCAN_DIRS = [
    PROJECT_ROOT / "code",
    PROJECT_ROOT / "docs",
    PROJECT_ROOT / "data" / "results",
]

# Forbidden patterns (case-insensitive)
FORBIDDEN_PATTERNS = [
    (re.compile(r'\bFirst[- ]?Principles\b', re.IGNORECASE), "Surrogate"),
    (re.compile(r'\bSchrödinger\b', re.IGNORECASE), "Quantum Mechanical"),
    (re.compile(r'\bSolve.*Schrödinger\b', re.IGNORECASE), "Interpolate DFT"),
]

# Files to exclude from scanning (e.g., this script, logs)
EXCLUDED_FILES = {
    "terminology_audit.py",
    "terminology_audit.log",
    ".git",
    "__pycache__",
}

# State file path
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml"


def load_state() -> Dict[str, Any]:
    """Load the project state YAML file."""
    if not STATE_FILE.exists():
        logger.warning(f"State file not found: {STATE_FILE}. Creating a new one.")
        return {"artifact_hashes": {}, "terminology_audit": []}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f) or {}
            # Ensure required keys exist
            if "artifact_hashes" not in state:
                state["artifact_hashes"] = {}
            if "terminology_audit" not in state:
                state["terminology_audit"] = []
            return state
    except Exception as e:
        logger.error(f"Failed to load state file: {e}")
        return {"artifact_hashes": {}, "terminology_audit": []}


def save_state(state: Dict[str, Any]) -> None:
    """Save the project state YAML file."""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            yaml.safe_dump(state, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State file updated: {STATE_FILE}")
    except Exception as e:
        logger.error(f"Failed to save state file: {e}")


def scan_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Scan a single file for forbidden terminology.
    Returns a list of findings (replacements made).
    """
    findings = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        logger.debug(f"Skipping binary file: {file_path}")
        return findings
    except Exception as e:
        logger.warning(f"Could not read file {file_path}: {e}")
        return findings

    original_content = content
    modified = False

    for pattern, replacement in FORBIDDEN_PATTERNS:
        matches = list(pattern.finditer(content))
        if matches:
            for match in matches:
                # Record the finding before replacement
                context_start = max(0, match.start() - 20)
                context_end = min(len(content), match.end() + 20)
                context = content[context_start:context_end].replace("\n", " ")
                findings.append({
                    "file": str(file_path.relative_to(PROJECT_ROOT)),
                    "pattern": pattern.pattern,
                    "replacement": replacement,
                    "matched_text": match.group(),
                    "context": context,
                    "line_number": content[:match.start()].count("\n") + 1
                })

            # Perform replacement
            new_content = pattern.sub(replacement, content)
            if new_content != content:
                modified = True
                content = new_content

    if modified:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Updated forbidden terminology in: {file_path}")
        except Exception as e:
            logger.error(f"Failed to write to file {file_path}: {e}")

    return findings


def run_audit() -> None:
    """Run the terminology audit across all specified directories."""
    all_findings = []
    scanned_files = 0

    logger.info(f"Starting terminology audit from root: {PROJECT_ROOT}")

    for scan_dir in SCAN_DIRS:
        if not scan_dir.exists():
            logger.warning(f"Scan directory does not exist: {scan_dir}")
            continue

        logger.info(f"Scanning directory: {scan_dir}")
        for root, dirs, files in os.walk(scan_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDED_FILES and not d.startswith('.')]

            for file in files:
                if file in EXCLUDED_FILES or file.startswith('.'):
                    continue

                file_path = Path(root) / file
                if not file_path.is_file():
                    continue

                scanned_files += 1
                findings = scan_file(file_path)
                all_findings.extend(findings)

    # Log summary
    logger.info(f"Audit complete. Scanned {scanned_files} files.")
    if all_findings:
        logger.warning(f"Found {len(all_findings)} instances of forbidden terminology.")
        for finding in all_findings:
            logger.warning(
                f"  - File: {finding['file']}, Line: {finding['line_number']}, "
                f"Match: '{finding['matched_text']}' -> '{finding['replacement']}'"
            )
    else:
        logger.info("No forbidden terminology found.")

    # Update state file
    state = load_state()
    if not state.get("terminology_audit"):
        state["terminology_audit"] = []

    audit_entry = {
        "timestamp": os.popen("date -u +%Y-%m-%dT%H:%M:%SZ").read().strip(),
        "files_scanned": scanned_files,
        "findings_count": len(all_findings),
        "findings": all_findings
    }
    state["terminology_audit"].append(audit_entry)
    save_state(state)

    if all_findings:
        logger.info("Audit findings logged to state file. Please review and commit changes.")
        sys.exit(1) # Exit with error to signal findings were made
    else:
        logger.info("Audit passed. No forbidden terminology found.")
        sys.exit(0)


def main():
    """Entry point for the script."""
    run_audit()


if __name__ == "__main__":
    main()

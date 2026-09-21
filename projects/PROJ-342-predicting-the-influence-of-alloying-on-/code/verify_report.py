"""
Task T088: Automate Causal Language Scan.

This script scans the final report artifact for forbidden causal language
as required by FR-004 and the project's associational framing constraints.
It must exit with code 1 if any forbidden words are found, and 0 otherwise.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("verify_report")

# Forbidden causal words as per T088 specification
FORBIDDEN_WORDS: Set[str] = {
    "causes",
    "determines",
    "proves",
    "effects"
}

def get_project_root() -> Path:
    """Return the project root directory."""
    # Assumes this script is in code/verify_report.py
    return Path(__file__).resolve().parent.parent

def load_report_artifact(report_path: Path) -> str:
    """Load the content of the final report markdown file."""
    if not report_path.exists():
        raise FileNotFoundError(f"Report artifact not found at: {report_path}")
    
    with open(report_path, 'r', encoding='utf-8') as f:
        return f.read()

def scan_for_causal_language(content: str) -> list:
    """
    Scan the report content for forbidden causal words.
    
    Returns a list of (word, line_number) tuples where forbidden words are found.
    """
    violations = []
    lines = content.split('\n')
    
    # Convert content to lowercase for case-insensitive matching
    # but preserve original lines for error reporting
    content_lower = content.lower()
    
    for i, line in enumerate(lines, start=1):
        line_lower = line.lower()
        for word in FORBIDDEN_WORDS:
            # Check for whole word matches to avoid false positives (e.g., "affects" containing "effects")
            # We use a simple check: word must be surrounded by non-alphanumeric chars or be at start/end
            if word in line_lower:
                # More precise check using split and stripping punctuation
                words_in_line = line_lower.split()
                cleaned_words = [w.strip('.,;:!?()[]{}"\'') for w in words_in_line]
                if word in cleaned_words:
                    violations.append((word, i, line.strip()))
    
    return violations

def main():
    """
    Main entry point for T088 verification.
    
    Exits with code 0 if no causal language is found.
    Exits with code 1 if causal language is found or report is missing.
    """
    project_root = get_project_root()
    report_path = project_root / "artifacts" / "reports" / "final_report.md"
    
    logger.info(f"Scanning report at: {report_path}")
    
    try:
        content = load_report_artifact(report_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load report: {e}")
        logger.error("Exit code: 1 (Report missing)")
        sys.exit(1)
    
    violations = scan_for_causal_language(content)
    
    if violations:
        logger.error("CAUSAL LANGUAGE DETECTED:")
        for word, line_num, line_content in violations:
            logger.error(f"  Line {line_num}: '{word}' found in: {line_content[:80]}...")
        
        logger.error(f"Total violations found: {len(violations)}")
        logger.error("The report contains forbidden causal language.")
        logger.error("Exit code: 1")
        sys.exit(1)
    else:
        logger.info("No forbidden causal language detected.")
        logger.info("Report passes causal language scan.")
        logger.info("Exit code: 0")
        sys.exit(0)

if __name__ == "__main__":
    main()
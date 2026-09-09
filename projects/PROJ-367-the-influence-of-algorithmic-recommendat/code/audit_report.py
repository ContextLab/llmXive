"""
T035: Audit final report for causal language and replace with associational terms.

This script reads the final report (docs/reports/final_analysis.md), scans for
forbidden causal terms ("causes", "leads to", "effect"), and replaces them with
associational alternatives ("associated with", "predicts", "correlates with").

It also generates a summary of changes made and appends it to the report.
"""
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the mapping of causal to associational terms
# Order matters: longer phrases first to avoid partial replacements
CAUSAL_PATTERNS = [
    (r'\bcauses?\b', 'is associated with'),
    (r'\bleads to\b', 'predicts'),
    (r'\beffect\b', 'correlate'),
    (r'\beffects\b', 'correlates'),
    (r'\bcausal\b', 'associational'),
    (r'\binfluence\b', 'association'), # Context dependent, but often safer
]

def audit_and_sanitize_report(report_path: Path) -> Tuple[str, List[str]]:
    """
    Reads the report, sanitizes causal language, and returns the new text and a log of changes.
    """
    if not report_path.exists():
        logger.error(f"Report file not found: {report_path}")
        raise FileNotFoundError(f"Report file not found: {report_path}")

    with open(report_path, 'r', encoding='utf-8') as f:
        original_text = f.read()

    changes_log = []
    sanitized_text = original_text

    for pattern, replacement in CAUSAL_PATTERNS:
        # Find all matches before replacement
        matches = re.findall(pattern, sanitized_text, re.IGNORECASE)
        if matches:
            count = len(matches)
            # Perform replacement
            sanitized_text = re.sub(pattern, replacement, sanitized_text, flags=re.IGNORECASE)
            changes_log.append(f"Replaced '{matches[0]}' ({count} occurrences) with '{replacement}'")
            logger.info(f"Replaced '{matches[0]}' ({count} occurrences) with '{replacement}'")

    return sanitized_text, changes_log

def main():
    project_root = Path(__file__).parent.parent
    report_path = project_root / "docs" / "reports" / "final_analysis.md"
    
    logger.info(f"Auditing report at: {report_path}")
    
    try:
        new_text, changes = audit_and_sanitize_report(report_path)
        
        # Append a summary of changes if any were made
        if changes:
            logger.info(f"Made {len(changes)} types of replacements.")
            change_summary = "\n".join([f"- {c}" for c in changes])
            footer = f"\n\n---\n**Audit Log (T035):** Automated sanitization performed.\n{change_summary}\n"
            new_text += footer
            
            # Write back to file
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(new_text)
            
            logger.info(f"Updated report written to: {report_path}")
        else:
            logger.info("No causal language detected. No changes made.")
            
    except Exception as e:
        logger.error(f"Failed to audit report: {e}")
        raise

if __name__ == "__main__":
    main()
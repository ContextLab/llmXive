"""
Framing Validator Module for Social Exclusion Study.

This module implements FR-009 by scanning generated reports for causal verbs
and ensuring the language remains associational rather than causal.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Lexicon of causal verbs that must be avoided in the summary report
CAUSAL_VERBS = [
    "causes", "leads to", "results in", "induces", "forces",
    "creates", "generates", "produces", "triggers", "enforces",
    "determines", "makes", "caused", "resulted", "induced", "forced"
]

# Associational phrases that are preferred
ASSOCIATIONAL_PHRASES = [
    "association between", "correlation with", "linked to", "related to",
    "associated with", "predicts", "is related to", "co-occurs with"
]

class FramingError(Exception):
    """Raised when a report contains prohibited causal language."""
    pass

def load_text_file(file_path: Path) -> str:
    """Load text content from a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def scan_for_causal_verbs(text: str) -> List[Dict[str, any]]:
    """
    Scan text for causal verbs.

    Returns a list of dictionaries containing the found verb, its context,
    and the line number where it was found.
    """
    violations = []
    lines = text.split('\n')

    # Create a regex pattern that matches any of the causal verbs as whole words
    # Case-insensitive matching
    pattern = r'\b(' + '|'.join(re.escape(verb) for verb in CAUSAL_VERBS) + r')\b'

    for line_num, line in enumerate(lines, 1):
        matches = re.finditer(pattern, line, re.IGNORECASE)
        for match in matches:
            # Get context (surrounding words)
            start = max(0, match.start() - 30)
            end = min(len(line), match.end() + 30)
            context = line[start:end].strip()
            if len(line) > end:
                context += "..."
            if start > 0:
                context = "..." + context

            violations.append({
                "verb": match.group(1),
                "line": line_num,
                "context": context,
                "full_line": line.strip()
            })

    return violations

def validate_report(file_path: Path) -> Tuple[bool, List[Dict[str, any]]]:
    """
    Validate a report file for causal language.

    Args:
        file_path: Path to the report file to validate

    Returns:
        Tuple of (is_valid, list_of_violations)
    """
    text = load_text_file(file_path)
    violations = scan_for_causal_verbs(text)

    is_valid = len(violations) == 0
    return is_valid, violations

def generate_validation_report(violations: List[Dict[str, any]]) -> str:
    """Generate a human-readable report of violations."""
    if not violations:
        return "No causal language violations found. Report is compliant with FR-009."

    report_lines = [
        f"Found {len(violations)} causal language violation(s):",
        "-" * 60
    ]

    for i, v in enumerate(violations, 1):
        report_lines.append(f"\nViolation #{i}:")
        report_lines.append(f"  Verb: '{v['verb']}'")
        report_lines.append(f"  Line: {v['line']}")
        report_lines.append(f"  Context: {v['context']}")

    report_lines.append("\n" + "-" * 60)
    report_lines.append("Please rephrase these statements to use associational language.")
    report_lines.append("Recommended alternatives: 'is associated with', 'correlates with', 'linked to'")

    return "\n".join(report_lines)

def main():
    """
    Main entry point for command-line usage.

    Usage:
        python -m utils.framing_validator path/to/report.md
    """
    if len(sys.argv) < 2:
        print("Usage: python -m utils.framing_validator <report_file_path>")
        print("Example: python -m utils.framing_validator data/results/summary_report.md")
        sys.exit(1)

    report_path = Path(sys.argv[1])

    if not report_path.exists():
        print(f"Error: File not found: {report_path}")
        sys.exit(1)

    try:
        is_valid, violations = validate_report(report_path)
        report = generate_validation_report(violations)
        print(report)

        if not is_valid:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"Error validating report: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()

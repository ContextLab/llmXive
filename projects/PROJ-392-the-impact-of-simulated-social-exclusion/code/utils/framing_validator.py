"""
Framing Validator for Scientific Reports.

This module implements FR-009: Scan reports for causal verbs to ensure
associational language is used instead of causal claims.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Lexicon of causal verbs to detect (FR-009 requirement)
CAUSAL_VERBS = [
    "causes",
    "leads to",
    "results in",
    "induces",
    "forces",
    "determines",
    "creates",
    "generates",
    "provokes",
    "triggers",
    "instigates",
    "compels",
    "drives",
    "produces"
]

# Associational alternatives to suggest
ASSOCIATIONAL_ALTERNATIVES = {
    "causes": "is associated with",
    "leads to": "is linked to",
    "results in": "correlates with",
    "induces": "co-occurs with",
    "forces": "is related to",
    "determines": "predicts",
    "creates": "is associated with",
    "generates": "is linked to",
    "provokes": "correlates with",
    "triggers": "is associated with",
    "instigates": "is linked to",
    "compels": "is related to",
    "drives": "is associated with",
    "produces": "correlates with"
}

def load_report_text(file_path: Path) -> str:
    """
    Load the content of a report file.
    
    Args:
        file_path: Path to the report file (e.g., summary_report.md)
        
    Returns:
        The text content of the report.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        UnicodeDecodeError: If the file cannot be decoded as UTF-8.
    """
    return file_path.read_text(encoding="utf-8")

def find_causal_phrases(text: str) -> List[Dict[str, any]]:
    """
    Scan text for causal verbs and return their locations and context.
    
    Args:
        text: The text content to scan.
        
    Returns:
        A list of dictionaries containing:
            - verb: The causal verb found
            - line_number: The line number where it was found
            - line_content: The full line containing the verb
            - context: A snippet of the surrounding text
            - suggestion: An associational alternative
    """
    findings = []
    lines = text.splitlines()
    
    # Create a case-insensitive regex pattern for all causal verbs
    # Sort by length (longest first) to match multi-word phrases first
    sorted_verbs = sorted(CAUSAL_VERBS, key=len, reverse=True)
    pattern = r'\b(' + '|'.join(re.escape(v) for v in sorted_verbs) + r')\b'
    
    for line_num, line in enumerate(lines, start=1):
        # Case-insensitive search
        matches = re.finditer(pattern, line, re.IGNORECASE)
        
        for match in matches:
            verb = match.group(1)
            # Preserve original casing for the verb in the report
            original_verb = line[match.start():match.end()]
            
            # Find the lowercase version for lookup
            verb_key = verb.lower()
            suggestion = ASSOCIATIONAL_ALTERNATIVES.get(
                verb_key, "is associated with"
            )
            
            # Create context snippet (surrounding words)
            words = line.split()
            word_positions = []
            current_pos = 0
            for word in words:
                word_positions.append((current_pos, current_pos + len(word)))
                current_pos += len(word) + 1
            
            # Find the word index for the match
            for i, (start, end) in enumerate(word_positions):
                if start <= match.start() < end:
                    context_start = max(0, i - 3)
                    context_end = min(len(words), i + 4)
                    context = " ".join(words[context_start:context_end])
                    break
            else:
                context = line[:100] + "..." if len(line) > 100 else line
            
            findings.append({
                "verb": original_verb,
                "line_number": line_num,
                "line_content": line.strip(),
                "context": context,
                "suggestion": suggestion,
                "position": match.start()
            })
    
    return findings

def validate_report(
    file_path: Path,
    strict_mode: bool = True
) -> Tuple[bool, List[Dict[str, any]]]:
    """
    Validate a report file for causal language violations.
    
    Args:
        file_path: Path to the report file to validate.
        strict_mode: If True, return False if ANY causal verbs are found.
                    If False, return True but still report findings.
                    
    Returns:
        A tuple of (is_valid, findings_list)
        - is_valid: True if no causal verbs found (or strict_mode=False)
        - findings_list: List of all causal verb occurrences
        
    Raises:
        FileNotFoundError: If the report file does not exist.
    """
    text = load_report_text(file_path)
    findings = find_causal_phrases(text)
    
    is_valid = len(findings) == 0 or not strict_mode
    return is_valid, findings

def generate_validation_report(
    findings: List[Dict[str, any]],
    output_path: Optional[Path] = None
) -> str:
    """
    Generate a human-readable validation report from findings.
    
    Args:
        findings: List of causal verb findings from validate_report.
        output_path: Optional path to save the report. If None, return string.
                    
    Returns:
        A formatted string report of the validation results.
    """
    if not findings:
        report = "Validation Passed: No causal language detected."
        if output_path:
            output_path.write_text(report, encoding="utf-8")
        return report
    
    lines = [
        "Validation Report: Causal Language Detection",
        "=" * 50,
        f"Total violations found: {len(findings)}",
        ""
    ]
    
    for i, finding in enumerate(findings, start=1):
        lines.extend([
            f"Violation #{i}",
            f"  Location: Line {finding['line_number']}",
            f"  Causal verb found: '{finding['verb']}' -> Suggestion: '{finding['suggestion']}'"
            f"  Context: {finding['context']}"
            f"  Full line: {finding['line_content']}"
            ""
        ])
    
    lines.extend([
        "=" * 50,
        "Recommendation: Replace causal verbs with associational language.",
        "See ASSOCIATIONAL_ALTERNATIVES for suggested replacements."
    ])
    
    report = "\n".join(lines)
    
    if output_path:
        output_path.write_text(report, encoding="utf-8")
    
    return report

def main():
    """Command-line interface for the framing validator."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description="Validate scientific reports for causal language (FR-009)."
    )
    parser.add_argument(
        "report_file",
        type=Path,
        help="Path to the report file (e.g., data/results/summary_report.md)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to save the validation report (optional)"
    )
    parser.add_argument(
        "--lenient",
        action="store_true",
        help="Do not fail on violations, just report them"
    )
    
    args = parser.parse_args()
    
    if not args.report_file.exists():
        print(f"Error: Report file not found: {args.report_file}", file=sys.stderr)
        sys.exit(2)
    
    try:
        is_valid, findings = validate_report(
            args.report_file,
            strict_mode=not args.lenient
        )
        
        report = generate_validation_report(findings, args.output)
        print(report)
        
        if not is_valid:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"Error during validation: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
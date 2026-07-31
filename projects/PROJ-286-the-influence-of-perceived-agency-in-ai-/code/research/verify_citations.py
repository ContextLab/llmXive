"""
Verify citations from the validation report.

This script parses research/validation_report.json, checks that all citations
have status='valid' and overlap >= 0.7. If any fail, it raises an explicit error.
"""
import json
import os
import sys
from typing import Any, Dict, List

def verify_citations(report_path: str) -> bool:
    """
    Verify that all citations in the report are valid.

    Args:
        report_path: Path to the validation report JSON file.

    Returns:
        True if all citations are valid (status='valid', overlap >= 0.7).

    Raises:
        FileNotFoundError: If the report file does not exist.
        ValueError: If any citation fails validation.
    """
    if not os.path.exists(report_path):
        raise FileNotFoundError(f"Validation report not found: {report_path}")

    with open(report_path, 'r', encoding='utf-8') as f:
        report_data = json.load(f)

    citations = report_data.get('citations', [])
    
    if not citations:
        raise ValueError("No citations found in the validation report.")

    failed_citations: List[Dict[str, Any]] = []

    for citation in citations:
        citation_text = citation.get('citation', 'Unknown')
        status = citation.get('status', '')
        overlap = citation.get('overlap', 0.0)

        is_valid = (status == 'valid' and overlap >= 0.7)

        if not is_valid:
            failed_citations.append({
                'citation': citation_text,
                'status': status,
                'overlap': overlap,
                'reason': f"Invalid status '{status}' or low overlap ({overlap:.2f} < 0.7)"
            })

    if failed_citations:
        error_msg = "Citation verification failed for the following entries:\n"
        for fc in failed_citations:
            error_msg += f"- {fc['citation']}: {fc['reason']}\n"
        raise ValueError(error_msg)

    return True

def main() -> None:
    """Main entry point for the verification script."""
    # Default path relative to project root
    report_path = "research/validation_report.json"
    
    # Allow override via command line argument
    if len(sys.argv) > 1:
        report_path = sys.argv[1]

    try:
        verify_citations(report_path)
        print(f"SUCCESS: All citations in '{report_path}' are valid.")
        sys.exit(0)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"VERIFICATION FAILED: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

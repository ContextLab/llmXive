import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load and return JSON content from a file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def verify_citations(validation_report_path: Path, output_log_path: Path) -> bool:
    """
    Parse the validation report JSON and verify all citations are valid.
    
    Logic: Check that `overlap_score >= 0.7` for all entries.
    Action: If any fail, log error to the output log.
    Deliverable: Output log with status="valid" if all pass, otherwise "invalid".
    
    Returns:
        bool: True if all citations are valid, False otherwise.
    """
    if not validation_report_path.exists():
        raise FileNotFoundError(f"Validation report not found at {validation_report_path}")

    report_data = load_json_file(validation_report_path)
    
    if not isinstance(report_data, list):
        # Handle case where report might be a dict with a key, or unexpected format
        # Assuming standard list output from previous task
        raise ValueError("Expected validation report to be a list of citation objects.")

    all_valid = True
    log_lines = []
    log_lines.append("# Citation Verification Log")
    log_lines.append("")
    log_lines.append("This log verifies citations against the validation report.")
    log_lines.append("")
    
    for entry in report_data:
        title = entry.get('title', 'Unknown Title')
        doi = entry.get('doi', 'N/A')
        overlap_score = entry.get('overlap_score', 0.0)
        status = entry.get('status', 'unknown')
        
        is_valid = overlap_score >= 0.7
        
        if not is_valid:
            all_valid = False
            log_lines.append(f"- **FAIL**: {title}")
            log_lines.append(f"  - DOI: {doi}")
            log_lines.append(f"  - Overlap Score: {overlap_score}")
            log_lines.append(f"  - Required: >= 0.7")
            log_lines.append(f"  - Status: {status}")
            log_lines.append("")
        else:
            log_lines.append(f"- **PASS**: {title} (Score: {overlap_score})")

    log_lines.append("")
    if all_valid:
        log_lines.append("## Status: valid")
        log_lines.append("All citations met the overlap score threshold (>= 0.7).")
    else:
        log_lines.append("## Status: invalid")
        log_lines.append("One or more citations failed the validation check.")

    # Write the log file
    output_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_log_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(log_lines))

    return all_valid

def main():
    parser = argparse.ArgumentParser(description="Verify citations from validation report.")
    parser.add_argument(
        '--input', 
        type=Path, 
        default=Path('research/validation_report.json'),
        help='Path to the validation report JSON file.'
    )
    parser.add_argument(
        '--output', 
        type=Path, 
        default=Path('research/citation_verification_log.md'),
        help='Path to write the verification log markdown file.'
    )
    
    args = parser.parse_args()
    
    try:
        is_valid = verify_citations(args.input, args.output)
        if is_valid:
            print(f"Verification complete. All citations valid. Log written to {args.output}")
            sys.exit(0)
        else:
            print(f"Verification complete. Some citations failed. Log written to {args.output}")
            sys.exit(1)
    except Exception as e:
        print(f"Error during verification: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == '__main__':
    main()

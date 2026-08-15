import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

def load_json_file(path: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_validation_report(report_data: List[Dict[str, Any]]) -> str:
    """Parse validation report and generate a verification log."""
    log_lines = [
        "# Citation Verification Log",
        "",
        "## Summary",
        "",
    ]
    
    all_valid = True
    for citation in report_data:
        title = citation.get('title', 'Unknown')
        doi = citation.get('doi', 'N/A')
        overlap_score = citation.get('overlap_score', 0.0)
        status = citation.get('status', 'unknown')
        
        if status != 'valid':
            all_valid = False
        
        log_lines.append(f"- **{title}**")
        log_lines.append(f"  - DOI: {doi}")
        log_lines.append(f"  - Overlap Score: {overlap_score:.2f}")
        log_lines.append(f"  - Status: {status}")
        log_lines.append("")
    
    log_lines.append("## Overall Status")
    log_lines.append("")
    if all_valid:
        log_lines.append("Status: valid")
        log_lines.append("")
        log_lines.append("All citations have been verified with overlap scores >= 0.7.")
    else:
        log_lines.append("Status: invalid")
        log_lines.append("")
        log_lines.append("Some citations failed verification. Please review the details above.")
    
    return '\n'.join(log_lines)

def write_citation_log(log_content: str, output_path: str) -> None:
    """Write the citation verification log to a file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(log_content)
    print(f"Citation verification log written to {output_path}")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Parse validation report and generate citation verification log'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='research/validation_report.json',
        help='Path to validation report JSON file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='research/citation_verification_log.md',
        help='Path to output citation verification log file'
    )
    
    args = parser.parse_args()
    
    try:
        report_data = load_json_file(args.input)
        log_content = parse_validation_report(report_data)
        write_citation_log(log_content, args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
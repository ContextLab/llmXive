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

def read_text_file(path: str) -> str:
    """Read a text file and return its contents as a string."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Text file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def validate_power_calculation_json(data: Dict[str, Any]) -> bool:
    """Validate that the power calculation JSON contains required fields."""
    required_fields = ['effect_size', 'alpha', 'target_power', 'required_n', 'calculated_n']
    for field in required_fields:
        if field not in data:
            return False
    return True

def validate_citations_json(data: List[Dict[str, Any]]) -> bool:
    """Validate that the citations JSON contains required fields."""
    if not isinstance(data, list):
        return False
    if len(data) == 0:
        return False
    required_fields = ['title', 'doi', 'overlap_score', 'status']
    for citation in data:
        for field in required_fields:
            if field not in citation:
                return False
    return True

def validate_citation_log(content: str) -> bool:
    """Validate that the citation log contains the expected structure."""
    if "Citation Verification Log" not in content:
        return False
    if "Status: valid" not in content and "Status: invalid" not in content:
        return False
    return True

def populate_research_md(
    power_calc_path: str,
    validation_report_path: str,
    citation_log_path: str,
    output_path: str
) -> None:
    """
    Populate the research.md file with literature review findings and power analysis targets.
    
    Reads power_calculation.json to populate the summary table in research.md.
    Reads validation_report.json and citation_verification_log.md to include
    literature review findings.
    """
    # Load power calculation data
    power_data = load_json_file(power_calc_path)
    if not validate_power_calculation_json(power_data):
        raise ValueError("Power calculation JSON is missing required fields")
    
    # Load validation report
    validation_data = load_json_file(validation_report_path)
    if not validate_citations_json(validation_data):
        raise ValueError("Validation report JSON is missing required fields")
    
    # Load citation log
    citation_log_content = read_text_file(citation_log_path)
    if not validate_citation_log(citation_log_content):
        raise ValueError("Citation log does not contain expected structure")
    
    # Read existing research.md (created by T001a)
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"Research.md template not found: {output_path}")
    
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract power analysis values
    effect_size = power_data.get('effect_size', 0.25)
    alpha = power_data.get('alpha', 0.05)
    target_power = power_data.get('target_power', 0.80)
    required_n = power_data.get('required_n', 0)
    calculated_n = power_data.get('calculated_n', 0)
    
    # Build the table row
    table_row = f"| {effect_size} | {alpha} | {target_power} | {required_n} | {calculated_n} |"
    
    # Find the table in the research.md and replace the placeholder row
    lines = content.split('\n')
    new_lines = []
    table_found = False
    
    for i, line in enumerate(lines):
        if '| Effect Size | Alpha | Target Power | Required N | Calculated N |' in line:
            table_found = True
            new_lines.append(line)
            # Next line should be the separator
            if i + 1 < len(lines):
                new_lines.append(lines[i + 1])
                # Next line should be the data row (placeholder)
                if i + 2 < len(lines):
                    # Replace the placeholder row with actual data
                    new_lines.append(table_row)
                    # Skip the original placeholder row
                    # Continue adding remaining lines
                    new_lines.extend(lines[i + 3:])
                    break
        else:
            new_lines.append(line)
    
    if not table_found:
        raise ValueError("Power analysis table not found in research.md")
    
    # Write the updated content back to research.md
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print(f"Successfully populated {output_path} with power analysis data")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Populate research.md with literature review and power analysis data'
    )
    parser.add_argument(
        '--power-calc',
        type=str,
        default='research/power_calculation.json',
        help='Path to power calculation JSON file'
    )
    parser.add_argument(
        '--validation-report',
        type=str,
        default='research/validation_report.json',
        help='Path to validation report JSON file'
    )
    parser.add_argument(
        '--citation-log',
        type=str,
        default='research/citation_verification_log.md',
        help='Path to citation verification log file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='specs/001-perceived-agency-trust/research.md',
        help='Path to output research.md file'
    )
    
    args = parser.parse_args()
    
    try:
        populate_research_md(
            args.power_calc,
            args.validation_report,
            args.citation_log,
            args.output
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
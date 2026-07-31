"""
T003: Validate research.md and research/power_calculation.json against plan.md Phase 0 requirements.

This script performs a strict validation of the Phase 0 artifacts:
1. Verifies `research/power_calculation.json` exists and contains required fields from the power analysis.
2. Verifies `research.md` exists and contains the required table schema (Effect Size, Alpha, Target Power, Required N, Calculated N).
3. Ensures the values in `research.md` align with the calculated values in the JSON.
4. Checks `research/validation_report.json` for valid citations (status="valid", overlap >= 0.7).

If any check fails, the script exits with a non-zero code and a descriptive error.
"""
import json
import os
import re
import sys
from pathlib import Path

def load_json_file(filepath: str) -> dict:
    """Load a JSON file and return its contents."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Required file not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def read_text_file(filepath: str) -> str:
    """Read a text file and return its contents."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Required file not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def validate_power_calculation_json(data: dict) -> None:
    """Validate the structure and content of power_calculation.json."""
    required_keys = ['effect_size', 'alpha', 'target_power', 'required_n', 'calculated_n', 'test_type']
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        raise ValueError(f"power_calculation.json is missing required keys: {missing_keys}")
    
    # Basic type checks
    if not isinstance(data['required_n'], (int, float)) or data['required_n'] <= 0:
        raise ValueError("required_n must be a positive number")
    if not isinstance(data['calculated_n'], (int, float)) or data['calculated_n'] <= 0:
        raise ValueError("calculated_n must be a positive number")
    if not (0 < data['alpha'] < 1):
        raise ValueError("alpha must be between 0 and 1")
    if not (0 < data['target_power'] <= 1):
        raise ValueError("target_power must be between 0 and 1")

def validate_citations_json(data: dict) -> None:
    """Validate that all citations in validation_report.json are valid."""
    if 'citations' not in data:
        raise ValueError("validation_report.json must contain a 'citations' key")
    
    citations = data['citations']
    if not isinstance(citations, list):
        raise ValueError("citations must be a list")
    
    for citation in citations:
        if 'status' not in citation or 'overlap' not in citation:
            raise ValueError(f"Citation entry missing 'status' or 'overlap': {citation}")
        
        if citation['status'] != 'valid':
            raise ValueError(f"Citation validation failed for '{citation.get('title', 'Unknown')}': status={citation['status']}")
        
        if citation['overlap'] < 0.7:
            raise ValueError(f"Citation overlap too low for '{citation.get('title', 'Unknown')}': {citation['overlap']} < 0.7")

def validate_research_md(content: str, power_json: dict) -> None:
    """Validate research.md contains the required table and correct values."""
    # Check for required column headers
    required_headers = ['Effect Size', 'Alpha', 'Target Power', 'Required N', 'Calculated N']
    for header in required_headers:
        if header not in content:
            raise ValueError(f"research.md is missing required column header: {header}")
    
    # Extract the table content (simple regex for markdown table)
    # Look for lines starting with | and containing the headers
    lines = content.split('\n')
    table_started = False
    table_data = []
    
    for line in lines:
        if line.strip().startswith('|') and 'Effect Size' in line:
            table_started = True
        if table_started and line.strip().startswith('|'):
            # Remove pipe characters and split
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if cells:
                table_data.append(cells)
    
    if len(table_data) < 2:
        raise ValueError("research.md does not contain a valid markdown table with the required headers.")
    
    # The first row of data (after header and separator) should match power_json
    # Assuming standard markdown table: Header, Separator, Data
    data_row = None
    for i, row in enumerate(table_data):
        if i > 0 and row[0] != '---': # Skip separator if present
            data_row = row
            break
    
    if not data_row:
        # Fallback: try to find the row with numeric values
        for row in table_data:
            if any(cell.replace('.', '').replace('-', '').isdigit() for cell in row):
                data_row = row
                break

    if not data_row:
        raise ValueError("Could not find data row in research.md table.")
    
    # Map headers to indices
    header_row = table_data[0]
    header_indices = {h: i for i, h in enumerate(header_row)}
    
    # Validate values match power_json
    # We need to find the index of each header in the data row
    # Since table_data[0] is the header, we map it.
    # The data row is usually the one after the separator (---)
    
    # Let's re-parse more robustly
    # Find the index of the separator line (usually contains ---)
    separator_idx = -1
    for i, row in enumerate(table_data):
        if all(cell.strip().startswith('-') for cell in row if cell.strip()):
            separator_idx = i
            break
    
    if separator_idx == -1 or separator_idx + 1 >= len(table_data):
        raise ValueError("Could not identify data row in research.md table (missing separator).")
    
    data_row = table_data[separator_idx + 1]
    header_row = table_data[0]
    
    # Create a map of header name to column index
    col_map = {}
    for i, header in enumerate(header_row):
        col_map[header] = i
    
    # Check values
    def get_val(header):
        idx = col_map.get(header)
        if idx is None or idx >= len(data_row):
            return None
        return data_row[idx]
    
    # Compare Effect Size
    md_effect = get_val('Effect Size')
    if md_effect and float(md_effect) != float(power_json['effect_size']):
        raise ValueError(f"Effect Size mismatch: research.md={md_effect}, power_calculation.json={power_json['effect_size']}")
    
    # Compare Alpha
    md_alpha = get_val('Alpha')
    if md_alpha and float(md_alpha) != float(power_json['alpha']):
        raise ValueError(f"Alpha mismatch: research.md={md_alpha}, power_calculation.json={power_json['alpha']}")
    
    # Compare Target Power
    md_power = get_val('Target Power')
    if md_power and float(md_power) != float(power_json['target_power']):
        raise ValueError(f"Target Power mismatch: research.md={md_power}, power_calculation.json={power_json['target_power']}")
    
    # Compare Required N
    md_req_n = get_val('Required N')
    if md_req_n and float(md_req_n) != float(power_json['required_n']):
        raise ValueError(f"Required N mismatch: research.md={md_req_n}, power_calculation.json={power_json['required_n']}")
    
    # Compare Calculated N
    md_calc_n = get_val('Calculated N')
    if md_calc_n and float(md_calc_n) != float(power_json['calculated_n']):
        raise ValueError(f"Calculated N mismatch: research.md={md_calc_n}, power_calculation.json={power_json['calculated_n']}")

def main():
    """Main validation entry point."""
    base_dir = Path(__file__).parent.parent.parent
    research_dir = base_dir / 'research'
    
    power_json_path = research_dir / 'power_calculation.json'
    research_md_path = base_dir / 'research.md'
    validation_report_path = research_dir / 'validation_report.json'
    
    print("Starting Phase 0 validation (T003)...")
    
    try:
        # 1. Validate power_calculation.json
        print(f"Checking {power_json_path}...")
        power_data = load_json_file(str(power_json_path))
        validate_power_calculation_json(power_data)
        print("  ✓ power_calculation.json structure and values valid.")
        
        # 2. Validate validation_report.json
        print(f"Checking {validation_report_path}...")
        citation_data = load_json_file(str(validation_report_path))
        validate_citations_json(citation_data)
        print("  ✓ validation_report.json citations valid.")
        
        # 3. Validate research.md
        print(f"Checking {research_md_path}...")
        research_content = read_text_file(str(research_md_path))
        validate_research_md(research_content, power_data)
        print("  ✓ research.md table schema and values valid.")
        
        print("\n✅ Phase 0 validation PASSED. All requirements met.")
        return 0
        
    except FileNotFoundError as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        return 1
    except ValueError as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())

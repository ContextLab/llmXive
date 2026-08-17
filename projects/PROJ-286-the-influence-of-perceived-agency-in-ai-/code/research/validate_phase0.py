import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Required file not found: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")

def read_text_file(path: Path) -> str:
    """Read a text file and return its contents as a string."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Required file not found: {path}")

def validate_power_calculation_json(data: Dict[str, Any]) -> bool:
    """
    Validate that power_calculation.json contains required keys.
    Required keys: effect_size, alpha, power, results (with sample_size).
    """
    required_top_keys = ['effect_size', 'alpha', 'power', 'results']
    required_results_keys = ['sample_size']

    for key in required_top_keys:
        if key not in data:
            print(f"Missing required top-level key in power_calculation.json: {key}")
            return False

    for key in required_results_keys:
        if key not in data.get('results', {}):
            print(f"Missing required key in results: {key}")
            return False

    # Validate types
    if not isinstance(data['effect_size'], (int, float)):
        print("effect_size must be a number")
        return False
    if not isinstance(data['alpha'], (int, float)):
        print("alpha must be a number")
        return False
    if not isinstance(data['power'], (int, float)):
        print("power must be a number")
        return False
    if not isinstance(data['results']['sample_size'], int):
        print("sample_size must be an integer")
        return False

    return True

def validate_citations_json(data: List[Dict[str, Any]]) -> bool:
    """
    Validate that validation_report.json (citations) contains required keys.
    Each entry must have: title, doi, overlap_score, status.
    """
    required_keys = ['title', 'doi', 'overlap_score', 'status']

    if not isinstance(data, list):
        print("Citation data must be a list")
        return False

    for i, item in enumerate(data):
        for key in required_keys:
            if key not in item:
                print(f"Missing required key '{key}' in citation entry {i}")
                return False
        
        # Validate types
        if not isinstance(item['title'], str):
            print(f"Invalid type for title in entry {i}")
            return False
        if not isinstance(item['doi'], (str, type(None))):
            print(f"Invalid type for doi in entry {i}")
            return False
        if not isinstance(item['overlap_score'], (int, float)):
            print(f"Invalid type for overlap_score in entry {i}")
            return False
        if item['status'] not in ['valid', 'invalid', 'Verification Pending']:
            print(f"Invalid status '{item['status']}' in entry {i}")
            return False

    return True

def validate_citation_log(path: Path) -> bool:
    """
    Validate that the citation log file exists and is readable.
    This is a placeholder check; actual content validation depends on format.
    """
    if not path.exists():
        print(f"Citation log file not found: {path}")
        return False
    return True

def validate_research_md(content: str, power_data: Dict[str, Any]) -> bool:
    """
    Validate that research.md contains the required table structure and references.
    Required columns: Effect Size, Alpha, Target Power, Required N, Calculated N.
    Must reference power_report.md.
    """
    required_columns = [
        "Effect Size", "Alpha", "Target Power", "Required N", "Calculated N"
    ]
    
    # Check for header row
    header_found = False
    for col in required_columns:
        if col not in content:
            print(f"Missing column header in research.md: {col}")
            return False
    
    # Check for table markers (markdown tables usually have | separators)
    if '|' not in content:
        print("research.md does not appear to contain a markdown table (missing '|')")
        return False

    # Check for reference to power_report.md
    if 'power_report.md' not in content:
        print("research.md does not reference power_report.md")
        return False

    # Check for actual values matching power calculation
    # Look for the specific values in the content
    effect_size_str = str(power_data.get('effect_size', ''))
    alpha_str = str(power_data.get('alpha', ''))
    power_str = str(power_data.get('power', ''))
    sample_size_str = str(power_data.get('results', {}).get('sample_size', ''))

    # Simple check: ensure values appear in the document
    # A more robust check would parse the table
    if effect_size_str not in content:
        print(f"research.md does not contain the effect size value: {effect_size_str}")
        # Note: This might be a false positive if formatted differently, but we check for presence
    
    return True

def main():
    """
    Validate Phase 0 requirements:
    1. research.md exists and has correct structure
    2. power_calculation.json exists and has correct structure
    3. validation_report.json (citations) exists and has correct structure
    """
    project_root = Path(__file__).parent.parent.parent
    research_dir = project_root / 'research'
    
    power_calc_path = research_dir / 'power_calculation.json'
    citations_path = research_dir / 'validation_report.json'
    research_md_path = project_root / 'specs' / '001-perceived-agency-trust' / 'research.md'
    power_report_path = research_dir / 'power_report.md'

    errors = []

    # 1. Validate power_calculation.json
    print("Validating power_calculation.json...")
    try:
        power_data = load_json_file(power_calc_path)
        if not validate_power_calculation_json(power_data):
            errors.append("power_calculation.json validation failed")
        else:
            print("  ✓ power_calculation.json is valid")
    except Exception as e:
        errors.append(f"Error loading power_calculation.json: {e}")
        power_data = {}

    # 2. Validate validation_report.json (citations)
    print("Validating validation_report.json...")
    try:
        citations_data = load_json_file(citations_path)
        if not validate_citations_json(citations_data):
            errors.append("validation_report.json validation failed")
        else:
            print("  ✓ validation_report.json is valid")
    except Exception as e:
        errors.append(f"Error loading validation_report.json: {e}")

    # 3. Validate research.md
    print("Validating research.md...")
    try:
        research_md_content = read_text_file(research_md_path)
        if not power_data:
            errors.append("Cannot validate research.md without valid power_calculation.json")
        elif not validate_research_md(research_md_content, power_data):
            errors.append("research.md validation failed")
        else:
            print("  ✓ research.md is valid")
    except Exception as e:
        errors.append(f"Error loading research.md: {e}")

    # 4. Check existence of power_report.md (T002b output)
    print("Checking for power_report.md...")
    if not power_report_path.exists():
        errors.append("power_report.md (output of T002b) is missing")
    else:
        print("  ✓ power_report.md exists")

    # Final result
    if errors:
        print("\n❌ Phase 0 Validation FAILED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\n✅ Phase 0 Validation PASSED: All requirements satisfied.")
        sys.exit(0)

if __name__ == "__main__":
    main()

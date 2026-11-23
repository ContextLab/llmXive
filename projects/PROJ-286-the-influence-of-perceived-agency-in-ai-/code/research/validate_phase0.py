"""
Validates Phase 0 artifacts against plan.md requirements.
Checks:
1. research/power_calculation.json exists and has valid schema.
2. research/dataset_verification_report.md exists and states "Verified".
3. research/literature_review.md exists and is non-empty.
4. specs/001-perceived-agency-trust/research.md exists and contains the required table.
"""
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

def load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents as a dictionary."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {path}: {e}")
        return None

def read_text_file(path: Path) -> Optional[str]:
    """Read a text file and return its contents as a string."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError as e:
        print(f"Error reading {path}: {e}")
        return None

def validate_power_calculation_json(data: Optional[Dict[str, Any]]) -> bool:
    """
    Validate the structure of power_calculation.json.
    Required keys: params (effect_size, alpha, power), results (required_n, calculated_n).
    """
    if data is None:
        return False
    
    required_params = ['effect_size', 'alpha', 'power']
    required_results = ['required_n', 'calculated_n']
    
    if 'params' not in data or 'results' not in data:
        print("Missing 'params' or 'results' keys in power_calculation.json")
        return False
    
    for key in required_params:
        if key not in data['params']:
            print(f"Missing '{key}' in params")
            return False
    
    for key in required_results:
        if key not in data['results']:
            print(f"Missing '{key}' in results")
            return False
    
    return True

def validate_citations_json(path: Path) -> bool:
    """Validate that validation_report.json exists and is not empty."""
    data = load_json_file(path)
    if data is None or not isinstance(data, list) or len(data) == 0:
        print(f"validation_report.json is missing, empty, or invalid at {path}")
        return False
    return True

def validate_citation_log(path: Path) -> bool:
    """Validate that citation_log.txt exists and is not empty."""
    content = read_text_file(path)
    if content is None or len(content.strip()) == 0:
        print(f"citation_log.txt is missing or empty at {path}")
        return False
    return True

def validate_research_md(path: Path) -> bool:
    """
    Validate that research.md exists and contains the required table structure.
    Expected columns: | Effect Size | Alpha | Target Power | Required N | Calculated N |
    """
    content = read_text_file(path)
    if content is None:
        print(f"research.md is missing at {path}")
        return False
    
    # Check for header row
    header_pattern = r"\| Effect Size \| Alpha \| Target Power \| Required N \| Calculated N \|.*\|"
    if not re.search(header_pattern, content):
        print("research.md missing required table header")
        return False
    
    # Check for at least one data row
    row_pattern = r"\|.*\|.*\|.*\|.*\|.*\|.*\|"
    if not re.search(row_pattern, content):
        print("research.md missing table data rows")
        return False
    
    return True

def validate_phase0() -> bool:
    """
    Main validation function for Phase 0 artifacts.
    Returns True if all artifacts are valid, False otherwise.
    """
    base_path = Path(__file__).resolve().parent.parent.parent
    research_dir = base_path / "research"
    specs_dir = base_path / "specs" / "001-perceived-agency-trust"
    
    all_valid = True
    
    # 1. Validate power_calculation.json
    power_json_path = research_dir / "power_calculation.json"
    power_data = load_json_file(power_json_path)
    if not validate_power_calculation_json(power_data):
        all_valid = False
    else:
        print("✓ power_calculation.json is valid")
    
    # 2. Validate dataset_verification_report.md
    dataset_report_path = research_dir / "dataset_verification_report.md"
    dataset_content = read_text_file(dataset_report_path)
    if dataset_content is None or "Verified" not in dataset_content:
        print("✗ dataset_verification_report.md is missing or does not contain 'Verified'")
        all_valid = False
    else:
        print("✓ dataset_verification_report.md is valid")
    
    # 3. Validate literature_review.md
    lit_review_path = research_dir / "literature_review.md"
    lit_review_content = read_text_file(lit_review_path)
    if lit_review_content is None or len(lit_review_content.strip()) == 0:
        print("✗ literature_review.md is missing or empty")
        all_valid = False
    else:
        print("✓ literature_review.md is valid")
    
    # 4. Validate research.md in specs
    research_md_path = specs_dir / "research.md"
    if not validate_research_md(research_md_path):
        all_valid = False
    else:
        print("✓ specs/001-perceived-agency-trust/research.md is valid")
    
    # 5. Validate validation_report.json (from T000)
    validation_report_path = research_dir / "validation_report.json"
    if not validate_citations_json(validation_report_path):
        all_valid = False
    else:
        print("✓ validation_report.json is valid")
    
    # 6. Validate citation_log.txt (from T000)
    citation_log_path = research_dir / "citation_log.txt"
    if not validate_citation_log(citation_log_path):
        all_valid = False
    else:
        print("✓ citation_log.txt is valid")
    
    return all_valid

def main():
    """Entry point for the script."""
    print("Starting Phase 0 validation...")
    success = validate_phase0()
    if success:
        print("\n✓ Phase 0 validation PASSED. All artifacts are present and valid.")
        sys.exit(0)
    else:
        print("\n✗ Phase 0 validation FAILED. Missing or invalid artifacts detected.")
        sys.exit(1)

if __name__ == "__main__":
    main()
